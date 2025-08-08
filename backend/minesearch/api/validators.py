"""
Author: rahn
Datum: 25.07.2025
Version: 1.0
Beschreibung: Zentrale Validation Layer für nachhaltige API-Architektur
"""

from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field, validator
from fastapi import HTTPException
import re
import logging

logger = logging.getLogger(__name__)

# =============================================================================
# BASE VALIDATION SCHEMAS
# =============================================================================

class BaseAPIRequest(BaseModel):
    """Basis-Schema für alle API-Requests"""
    
    class Config:
        str_strip_whitespace = True
        validate_assignment = True


class BaseAPIResponse(BaseModel):
    """Standardisiertes Response-Schema für alle API-Endpoints"""
    
    success: bool = Field(..., description="Erfolg-Status der Operation")
    data: Optional[Dict[str, Any]] = Field(None, description="Response-Daten bei Erfolg")
    error: Optional[str] = Field(None, description="Fehlermeldung bei Fehler")
    code: Optional[str] = Field(None, description="Spezifischer Error-Code")
    timestamp: str = Field(..., description="ISO-Timestamp der Response")
    request_id: Optional[str] = Field(None, description="Eindeutige Request-ID für Tracing")


# =============================================================================
# MINE SEARCH VALIDATION
# =============================================================================

class MineSearchValidator(BaseAPIRequest):
    """Validierung für Mine-Search-Requests"""
    
    mine_name: str = Field(
        ..., 
        min_length=2, 
        max_length=200,
        description="Name der Mine (2-200 Zeichen)"
    )
    country: Optional[str] = Field(
        None, 
        max_length=100,
        description="Land (max. 100 Zeichen)"
    )
    commodity: Optional[str] = Field(
        None, 
        max_length=100,
        description="Rohstoff (max. 100 Zeichen)"
    )
    region: Optional[str] = Field(
        None, 
        max_length=100,
        description="Region (max. 100 Zeichen)"
    )
    model_id: str = Field(
        ...,
        description="AI-Modell ID für die Suche"
    )
    
    @validator('mine_name')
    def validate_mine_name(cls, v):
        """Validiert Mine-Namen auf gefährliche Eingaben"""
        if not v or not v.strip():
            raise ValueError("Mine-Name darf nicht leer sein")
        
        # Blockiere potentiell gefährliche Zeichen
        dangerous_patterns = [
            r'<script.*?>',
            r'javascript:',
            r'on\w+\s*=',
            r'SELECT.*FROM',
            r'DROP\s+TABLE',
            r'INSERT\s+INTO'
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError(f"Ungültige Zeichen im Mine-Namen erkannt")
        
        return v.strip()
    
    @validator('model_id')
    def validate_model_id(cls, v):
        """Validiert Modell-IDs"""
        if not v or not v.strip():
            raise ValueError("Modell-ID darf nicht leer sein")
        
        # Erlaubte Modell-Präfixe
        valid_prefixes = ['openrouter:', 'perplexity:', 'anthropic:', 'openai:']
        
        if not any(v.startswith(prefix) for prefix in valid_prefixes):
            # Füge Default-Präfix hinzu wenn keiner vorhanden
            v = f"openrouter:{v}"
        
        return v


class MultiSearchValidator(BaseAPIRequest):
    """Validierung für Multi-Model-Search-Requests"""
    
    mine_name: str = Field(..., min_length=2, max_length=200)
    country: Optional[str] = Field(None, max_length=100)
    commodity: Optional[str] = Field(None, max_length=100)
    region: Optional[str] = Field(None, max_length=100)
    model_ids: List[str] = Field(
        ..., 
        min_items=1, 
        max_items=10,
        description="Liste der Modell-IDs (1-10 Modelle)"
    )
    
    @validator('model_ids')
    def validate_model_ids(cls, v):
        """Validiert Liste von Modell-IDs"""
        if not v:
            raise ValueError("Mindestens ein Modell muss angegeben werden")
        
        if len(v) > 10:
            raise ValueError("Maximal 10 Modelle pro Multi-Search erlaubt")
        
        # Validiere jede Modell-ID
        validated_ids = []
        for model_id in v:
            if not model_id or not model_id.strip():
                continue
            
            valid_prefixes = ['openrouter:', 'perplexity:', 'anthropic:', 'openai:']
            if not any(model_id.startswith(prefix) for prefix in valid_prefixes):
                model_id = f"openrouter:{model_id}"
            
            validated_ids.append(model_id)
        
        if not validated_ids:
            raise ValueError("Mindestens ein gültiges Modell muss angegeben werden")
        
        return validated_ids


# =============================================================================
# BATCH PROCESSING VALIDATION
# =============================================================================

class BatchMineItem(BaseModel):
    """Einzelne Mine für Batch-Processing"""
    
    mine_name: str = Field(..., min_length=2, max_length=200)
    country: Optional[str] = Field(None, max_length=100)
    commodity: Optional[str] = Field(None, max_length=100)
    region: Optional[str] = Field(None, max_length=100)


class BatchSearchValidator(BaseAPIRequest):
    """Validierung für Batch-Search-Requests"""
    
    mines: List[BatchMineItem] = Field(
        ...,
        min_items=1,
        max_items=100,
        description="Liste von Minen (1-100 Einträge)"
    )
    model_ids: List[str] = Field(
        ...,
        min_items=1,
        max_items=5,
        description="Liste der Modell-IDs (1-5 Modelle)"
    )
    parallel_limit: Optional[int] = Field(
        5,
        ge=1,
        le=20,
        description="Parallelitätslimit (1-20)"
    )
    
    @validator('mines')
    def validate_batch_size(cls, v):
        """Validiert Batch-Größe"""
        if len(v) > 100:
            raise ValueError("Batch-Größe überschreitet Maximum von 100 Minen")
        
        # Prüfe auf Duplikate
        seen_mines = set()
        for mine in v:
            key = f"{mine.mine_name}_{mine.country or ''}_{mine.commodity or ''}"
            if key in seen_mines:
                logger.warning(f"Duplikat erkannt in Batch: {mine.mine_name}")
            seen_mines.add(key)
        
        return v


# =============================================================================
# VALIDATION UTILITIES
# =============================================================================

class ValidationError(Exception):
    """Custom Validation Error"""
    
    def __init__(self, message: str, field: str = None, code: str = None):
        self.message = message
        self.field = field
        self.code = code or "VALIDATION_ERROR"
        super().__init__(self.message)


def validate_request(validator_class: BaseModel, data: Dict[str, Any]) -> BaseModel:
    """
    Zentrale Request-Validierung
    
    Args:
        validator_class: Pydantic-Modell für Validierung
        data: Request-Daten
        
    Returns:
        Validiertes Pydantic-Modell
        
    Raises:
        HTTPException: Bei Validierungsfehlern
    """
    try:
        return validator_class(**data)
    
    except ValueError as e:
        logger.error(f"[VALIDATION] Request validation failed: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": f"Validierungsfehler: {str(e)}",
                "code": "VALIDATION_ERROR",
                "field": getattr(e, 'field', None)
            }
        )
    
    except Exception as e:
        logger.error(f"[VALIDATION] Unexpected validation error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Interner Validierungsfehler",
                "code": "INTERNAL_VALIDATION_ERROR"
            }
        )


def sanitize_string_input(value: str, max_length: int = 200) -> str:
    """
    Bereinigt String-Eingaben von potentiell gefährlichen Inhalten
    
    Args:
        value: Zu bereinigender String
        max_length: Maximale Länge
        
    Returns:
        Bereinigter String
    """
    if not value:
        return ""
    
    # Entferne gefährliche HTML/Script-Tags
    value = re.sub(r'<[^>]*>', '', value)
    
    # Entferne SQL-Injection-Pattern
    sql_patterns = [
        r"(\bSELECT\b|\bFROM\b|\bWHERE\b|\bDROP\b|\bINSERT\b|\bUPDATE\b|\bDELETE\b)",
        r"(\bUNION\b|\bOR\b\s+\d+\s*=\s*\d+|\bAND\b\s+\d+\s*=\s*\d+)",
        r"(--|\/\*|\*\/|;)"
    ]
    
    for pattern in sql_patterns:
        value = re.sub(pattern, '', value, flags=re.IGNORECASE)
    
    # Begrenze Länge
    if len(value) > max_length:
        value = value[:max_length]
    
    return value.strip()


# =============================================================================
# RESPONSE BUILDERS
# =============================================================================

def build_success_response(
    data: Dict[str, Any],
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Erstellt standardisierte Erfolgs-Response
    
    Args:
        data: Response-Daten
        request_id: Optional Request-ID
        
    Returns:
        Standardisierte Success-Response
    """
    from datetime import datetime
    
    return {
        "success": True,
        "data": data,
        "error": None,
        "code": None,
        "timestamp": datetime.now().isoformat(),
        "request_id": request_id
    }


def build_error_response(
    error_message: str,
    error_code: str = "GENERIC_ERROR",
    request_id: Optional[str] = None,
    status_code: int = 500
) -> Dict[str, Any]:
    """
    Erstellt standardisierte Error-Response
    
    Args:
        error_message: Fehlermeldung
        error_code: Spezifischer Error-Code
        request_id: Optional Request-ID
        status_code: HTTP-Status-Code
        
    Returns:
        Standardisierte Error-Response
    """
    from datetime import datetime
    
    return {
        "success": False,
        "data": None,
        "error": error_message,
        "code": error_code,
        "timestamp": datetime.now().isoformat(),
        "request_id": request_id
    }