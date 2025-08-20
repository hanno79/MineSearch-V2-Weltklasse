"""
Author: rahn
Datum: 25.07.2025
Version: 1.0
Beschreibung: Comprehensive Request/Response Schema Validation für nachhaltige API-Architektur
"""

from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field, validator, root_validator
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)

# =============================================================================
# ENUMS & CONSTANTS
# =============================================================================

class SearchType(str, Enum):
    """Verfügbare Suchtypen"""
    SINGLE = "single"
    MULTI_MODEL = "multi_model"
    BATCH = "batch"
    SMART = "smart"
    ENHANCED = "enhanced"
    COMPREHENSIVE = "comprehensive"


class ModelProvider(str, Enum):
    """Verfügbare Modell-Provider"""
    OPENROUTER = "openrouter"
    PERPLEXITY = "perplexity"
    ANTHROPIC = "anthropic"
    OPENAI = "openai"


class HealthStatus(str, Enum):
    """Health-Check-Status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


# =============================================================================
# BASE SCHEMAS
# =============================================================================

class BaseRequest(BaseModel):
    """Basis-Schema für alle Requests"""
    
    class Config:
        str_strip_whitespace = True
        validate_assignment = True
        extra = "forbid"  # Verhindert zusätzliche Felder


class BaseResponse(BaseModel):
    """Basis-Schema für alle Responses"""
    
    success: bool = Field(..., description="Erfolg-Status der Operation")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response-Timestamp")
    request_id: Optional[str] = Field(None, description="Eindeutige Request-ID")
    
    class Config:
        extra = "allow"  # Erlaubt zusätzliche Felder in Responses


class PaginationRequest(BaseModel):
    """Schema für Pagination-Parameter"""
    
    page: int = Field(1, ge=1, le=1000, description="Seitennummer (1-1000)")
    limit: int = Field(25, ge=1, le=100, description="Anzahl Einträge pro Seite (1-100)")
    
    @property
    def offset(self) -> int:
        """Berechnet Offset für Datenbankabfragen"""
        return (self.page - 1) * self.limit


class PaginationResponse(BaseModel):
    """Schema für paginierte Responses"""
    
    page: int = Field(..., description="Aktuelle Seite")
    limit: int = Field(..., description="Einträge pro Seite")
    total_count: int = Field(..., description="Gesamtanzahl Einträge")
    total_pages: int = Field(..., description="Gesamtanzahl Seiten")
    has_next: bool = Field(..., description="Weitere Seiten verfügbar")
    has_previous: bool = Field(..., description="Vorherige Seiten verfügbar")


# =============================================================================
# MINE DATA SCHEMAS
# =============================================================================

class MineLocation(BaseModel):
    """Schema für Mine-Standortdaten"""
    
    country: Optional[str] = Field(None, max_length=100, description="Land")
    region: Optional[str] = Field(None, max_length=100, description="Region/Bundesstaat")
    coordinates: Optional[Dict[str, float]] = Field(None, description="GPS-Koordinaten")
    
    @validator('coordinates')
    def validate_coordinates(cls, v):
        """Validiert GPS-Koordinaten"""
        if v is None:
            return v
        
        required_keys = {'latitude', 'longitude'}
        if not required_keys.issubset(v.keys()):
            raise ValueError("Koordinaten müssen 'latitude' und 'longitude' enthalten")
        
        lat, lng = v['latitude'], v['longitude']
        if not (-90 <= lat <= 90):
            raise ValueError("Latitude muss zwischen -90 und 90 liegen")
        if not (-180 <= lng <= 180):
            raise ValueError("Longitude muss zwischen -180 und 180 liegen")
        
        return v


class MineProduction(BaseModel):
    """Schema für Mine-Produktionsdaten"""
    
    commodity: Optional[str] = Field(None, max_length=100, description="Hauptrohstoff")
    production_volume: Optional[str] = Field(None, description="Produktionsvolumen")
    production_unit: Optional[str] = Field(None, max_length=50, description="Einheit")
    year: Optional[int] = Field(None, ge=1800, le=2100, description="Produktionsjahr")


class MineOperational(BaseModel):
    """Schema für operative Mine-Daten"""
    
    status: Optional[str] = Field(None, max_length=50, description="Betriebsstatus")
    operator: Optional[str] = Field(None, max_length=200, description="Betreiber")
    owner: Optional[str] = Field(None, max_length=200, description="Eigentümer")
    start_year: Optional[int] = Field(None, ge=1800, le=2100, description="Betriebsbeginn")
    end_year: Optional[int] = Field(None, ge=1800, le=2100, description="Betriebsende")


class MineFinancial(BaseModel):
    """Schema für finanzielle Mine-Daten"""
    
    market_cap: Optional[str] = Field(None, description="Marktkapitalisierung")
    revenue: Optional[str] = Field(None, description="Umsatz")
    currency: Optional[str] = Field(None, max_length=10, description="Währung")


class ComprehensiveMineData(BaseModel):
    """Vollständiges Schema für alle Mine-Daten"""
    
    basic_info: Dict[str, Any] = Field(..., description="Grundinformationen")
    location: Optional[MineLocation] = Field(None, description="Standortdaten")
    production: Optional[MineProduction] = Field(None, description="Produktionsdaten")
    operational: Optional[MineOperational] = Field(None, description="Operative Daten")
    financial: Optional[MineFinancial] = Field(None, description="Finanzielle Daten")
    sources: List[str] = Field(default_factory=list, description="Datenquellen")
    extraction_metadata: Optional[Dict[str, Any]] = Field(None, description="Extraktions-Metadaten")


# =============================================================================
# SEARCH REQUEST SCHEMAS
# =============================================================================

class SingleSearchRequest(BaseRequest):
    """Schema für Einzel-Mine-Suche"""
    
    mine_name: str = Field(
        ..., 
        min_length=2, 
        max_length=200,
        description="Name der Mine (2-200 Zeichen)"
    )
    model_id: str = Field(..., description="AI-Modell ID")
    location: Optional[MineLocation] = Field(None, description="Standortfilter")
    commodity: Optional[str] = Field(None, max_length=100, description="Rohstofffilter")
    search_type: SearchType = Field(SearchType.SINGLE, description="Suchtyp")
    
    @validator('mine_name')
    def validate_mine_name(cls, v):
        """Validiert Mine-Namen"""
        if not v or not v.strip():
            raise ValueError("Mine-Name darf nicht leer sein")
        return v.strip()


class MultiModelSearchRequest(BaseRequest):
    """Schema für Multi-Modell-Suche"""
    
    mine_name: str = Field(..., min_length=2, max_length=200)
    model_ids: List[str] = Field(
        ..., 
        min_items=2, 
        max_items=100,  # PHASE 3: Erhöht für alle 55+ verfügbaren Modelle
        description="Liste der Modell-IDs (2-100 Modelle)"
    )
    location: Optional[MineLocation] = Field(None)
    commodity: Optional[str] = Field(None, max_length=100)
    comparison_enabled: bool = Field(True, description="Modell-Vergleich aktivieren")
    
    @validator('model_ids')
    def validate_model_ids(cls, v):
        """Validiert Modell-IDs Liste"""
        if len(set(v)) != len(v):
            raise ValueError("Duplikate in Modell-IDs nicht erlaubt")
        return v


class BatchMineEntry(BaseModel):
    """Einzelner Eintrag für Batch-Suche"""
    
    mine_name: str = Field(..., min_length=2, max_length=200)
    location: Optional[MineLocation] = Field(None)
    commodity: Optional[str] = Field(None, max_length=100)
    priority: int = Field(1, ge=1, le=5, description="Priorität (1=niedrig, 5=hoch)")


class BatchSearchRequest(BaseRequest):
    """Schema für Batch-Suche"""
    
    mines: List[BatchMineEntry] = Field(
        ...,
        min_items=1,
        max_items=100,
        description="Liste von Minen (1-100 Einträge)"
    )
    model_ids: List[str] = Field(
        ...,
        min_items=1,
        max_items=5,
        description="Modell-IDs für alle Minen"
    )
    parallel_limit: int = Field(
        5,
        ge=1,
        le=20,
        description="Parallelitätslimit (1-20)"
    )
    priority_processing: bool = Field(
        False,
        description="Prioritätsbasierte Verarbeitung"
    )
    
    @validator('mines')
    def validate_batch_mines(cls, v):
        """Validiert Batch-Minen auf Duplikate"""
        seen = set()
        for mine in v:
            key = f"{mine.mine_name}_{mine.location.country if mine.location else ''}"
            if key in seen:
                logger.warning(f"Duplikat in Batch erkannt: {mine.mine_name}")
            seen.add(key)
        return v


# =============================================================================
# SEARCH RESPONSE SCHEMAS  
# =============================================================================

class SearchMetadata(BaseModel):
    """Metadaten für Suchergebnisse"""
    
    search_duration: float = Field(..., description="Suchdauer in Sekunden")
    model_used: str = Field(..., description="Verwendetes Modell")
    provider: str = Field(..., description="Verwendeter Provider")
    token_usage: Optional[Dict[str, int]] = Field(None, description="Token-Verbrauch")
    cost_estimate: Optional[float] = Field(None, description="Geschätzte Kosten")
    confidence_score: Optional[float] = Field(None, ge=0, le=1, description="Vertrauenswert")
    data_completeness: Optional[float] = Field(None, ge=0, le=1, description="Datenvollständigkeit")


class SingleSearchResponse(BaseResponse):
    """Response für Einzel-Mine-Suche"""
    
    data: Optional[ComprehensiveMineData] = Field(None, description="Mine-Daten")
    error: Optional[str] = Field(None, description="Fehlermeldung")
    metadata: SearchMetadata = Field(..., description="Such-Metadaten")


class MultiModelSearchResponse(BaseResponse):
    """Response für Multi-Modell-Suche"""
    
    data: Optional[Dict[str, ComprehensiveMineData]] = Field(
        None, 
        description="Mine-Daten pro Modell"
    )
    comparison: Optional[Dict[str, Any]] = Field(
        None,
        description="Modell-Vergleichsdaten"
    )
    error: Optional[str] = Field(None, description="Fehlermeldung")
    metadata: Dict[str, SearchMetadata] = Field(
        ...,
        description="Metadaten pro Modell"
    )


class BatchSearchItem(BaseModel):
    """Einzelnes Ergebnis in Batch-Response"""
    
    mine_name: str = Field(..., description="Mine-Name")
    status: str = Field(..., description="Verarbeitungsstatus")
    data: Optional[ComprehensiveMineData] = Field(None, description="Mine-Daten")
    error: Optional[str] = Field(None, description="Fehlermeldung")
    metadata: SearchMetadata = Field(..., description="Such-Metadaten")


class BatchSearchResponse(BaseResponse):
    """Response für Batch-Suche"""
    
    results: List[BatchSearchItem] = Field(..., description="Batch-Ergebnisse")
    summary: Dict[str, Any] = Field(..., description="Batch-Zusammenfassung")
    total_processed: int = Field(..., description="Anzahl verarbeiteter Minen")
    successful: int = Field(..., description="Anzahl erfolgreicher Suchen")
    failed: int = Field(..., description="Anzahl fehlgeschlagener Suchen")


# =============================================================================
# STATISTICS & ANALYTICS SCHEMAS
# =============================================================================

class ModelPerformanceStats(BaseModel):
    """Modell-Performance-Statistiken"""
    
    model_id: str = Field(..., description="Modell-ID")
    total_requests: int = Field(..., description="Gesamtanzahl Anfragen")
    successful_requests: int = Field(..., description="Erfolgreiche Anfragen")
    success_rate: float = Field(..., ge=0, le=1, description="Erfolgsrate")
    avg_response_time: float = Field(..., description="Durchschnittliche Antwortzeit")
    avg_token_usage: Optional[float] = Field(None, description="Durchschnittlicher Token-Verbrauch")
    total_cost: Optional[float] = Field(None, description="Gesamtkosten")


class SystemHealthResponse(BaseResponse):
    """System-Health-Response"""
    
    status: HealthStatus = Field(..., description="Gesamtstatus")
    components: Dict[str, Dict[str, Any]] = Field(..., description="Komponenten-Status")
    uptime: float = Field(..., description="System-Uptime in Sekunden")
    version: str = Field(..., description="System-Version")
    last_check: datetime = Field(..., description="Letzter Health-Check")


# =============================================================================
# CONFIGURATION SCHEMAS
# =============================================================================

class ModelConfiguration(BaseModel):
    """Modell-Konfiguration"""
    
    model_id: str = Field(..., description="Modell-ID")
    provider: ModelProvider = Field(..., description="Provider")
    enabled: bool = Field(True, description="Modell aktiviert")
    cost_per_token: Optional[float] = Field(None, description="Kosten pro Token")
    max_tokens: Optional[int] = Field(None, description="Maximale Token-Anzahl")
    temperature: Optional[float] = Field(None, ge=0, le=2, description="Temperatur-Parameter")
    timeout: int = Field(30, ge=1, le=300, description="Timeout in Sekunden")


class SearchConfiguration(BaseModel):
    """Such-Konfiguration"""
    
    cache_enabled: bool = Field(True, description="Cache aktiviert")
    cache_ttl: int = Field(3600, ge=60, le=86400, description="Cache-TTL in Sekunden")
    max_concurrent_searches: int = Field(10, ge=1, le=50, description="Max. parallele Suchen")
    default_timeout: int = Field(30, ge=5, le=300, description="Standard-Timeout")
    retry_attempts: int = Field(3, ge=1, le=10, description="Wiederholungsversuche")
    cost_limit_per_hour: Optional[float] = Field(None, description="Kostenlimit pro Stunde")


# =============================================================================
# VALIDATION DECORATORS
# =============================================================================

def validate_request_schema(schema_class: BaseModel):
    """
    Decorator für Request-Schema-Validierung
    
    Args:
        schema_class: Pydantic-Schema-Klasse
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Implementierung würde hier Request validieren
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def validate_response_schema(schema_class: BaseModel):
    """
    Decorator für Response-Schema-Validierung
    
    Args:
        schema_class: Pydantic-Schema-Klasse
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            # Implementierung würde hier Response validieren
            return result
        return wrapper
    return decorator