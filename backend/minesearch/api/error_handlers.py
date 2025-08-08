"""
Author: rahn
Datum: 25.07.2025
Version: 1.0
Beschreibung: Zentrale Error-Handler für nachhaltige API-Architektur
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
import logging
import traceback
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# =============================================================================
# ERROR CODES REGISTRY
# =============================================================================

class ErrorCodes:
    """Zentrale Registry für alle Error-Codes"""
    
    # Validation Errors (4xx)
    VALIDATION_ERROR = "VALIDATION_ERROR"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_FIELD_FORMAT = "INVALID_FIELD_FORMAT"
    FIELD_TOO_LONG = "FIELD_TOO_LONG"
    FIELD_TOO_SHORT = "FIELD_TOO_SHORT"
    INVALID_MODEL_ID = "INVALID_MODEL_ID"
    BATCH_SIZE_EXCEEDED = "BATCH_SIZE_EXCEEDED"
    
    # Authentication/Authorization Errors (4xx)
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    API_KEY_INVALID = "API_KEY_INVALID"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    
    # Resource Errors (4xx)
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    MINE_NOT_FOUND = "MINE_NOT_FOUND"
    MODEL_NOT_FOUND = "MODEL_NOT_FOUND"
    SOURCE_NOT_FOUND = "SOURCE_NOT_FOUND"
    
    # Business Logic Errors (422)
    SEARCH_FAILED = "SEARCH_FAILED"
    MODEL_UNAVAILABLE = "MODEL_UNAVAILABLE"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    COST_LIMIT_EXCEEDED = "COST_LIMIT_EXCEEDED"
    
    # System Errors (5xx)
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"
    MEMORY_ERROR = "MEMORY_ERROR"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"


# =============================================================================
# CUSTOM EXCEPTIONS
# =============================================================================

class MineSearchException(Exception):
    """Basis-Exception für MineSearch-spezifische Fehler"""
    
    def __init__(
        self, 
        message: str, 
        error_code: str = ErrorCodes.INTERNAL_SERVER_ERROR,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationException(MineSearchException):
    """Exception für Validierungsfehler"""
    
    def __init__(self, message: str, field: str = None, details: Dict[str, Any] = None):
        super().__init__(
            message=message,
            error_code=ErrorCodes.VALIDATION_ERROR,
            status_code=400,
            details=details or {}
        )
        if field:
            self.details['field'] = field


class ResourceNotFoundException(MineSearchException):
    """Exception für nicht gefundene Ressourcen"""
    
    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            message=f"{resource_type} mit ID '{resource_id}' nicht gefunden",
            error_code=ErrorCodes.RESOURCE_NOT_FOUND,
            status_code=404,
            details={'resource_type': resource_type, 'resource_id': resource_id}
        )


class BusinessLogicException(MineSearchException):
    """Exception für Business-Logic-Fehler"""
    
    def __init__(self, message: str, error_code: str = ErrorCodes.SEARCH_FAILED):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=422
        )


class ExternalServiceException(MineSearchException):
    """Exception für externe Service-Fehler"""
    
    def __init__(self, service_name: str, message: str):
        super().__init__(
            message=f"Fehler in externem Service '{service_name}': {message}",
            error_code=ErrorCodes.EXTERNAL_SERVICE_ERROR,
            status_code=503,
            details={'service_name': service_name}
        )


# =============================================================================
# ERROR RESPONSE BUILDER
# =============================================================================

def build_error_response(
    error_message: str,
    error_code: str,
    status_code: int = 500,
    request_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    request: Optional[Request] = None
) -> JSONResponse:
    """
    Erstellt standardisierte Error-Response
    
    Args:
        error_message: Benutzerfreundliche Fehlermeldung
        error_code: Spezifischer Error-Code
        status_code: HTTP-Status-Code
        request_id: Eindeutige Request-ID
        details: Zusätzliche Fehlerdetails
        request: FastAPI Request-Objekt
        
    Returns:
        Standardisierte JSONResponse
    """
    
    if not request_id:
        request_id = str(uuid.uuid4())
    
    response_data = {
        "success": False,
        "data": None,
        "error": error_message,
        "code": error_code,
        "timestamp": datetime.now().isoformat(),
        "request_id": request_id
    }
    
    # Zusätzliche Details nur in Development-Umgebung
    if details and logger.level <= logging.DEBUG:
        response_data["details"] = details
    
    # Request-Context hinzufügen für Debugging
    if request and logger.level <= logging.DEBUG:
        response_data["request_info"] = {
            "method": request.method,
            "url": str(request.url),
            "headers": dict(request.headers)
        }
    
    # Logge den Fehler
    log_level = logging.ERROR if status_code >= 500 else logging.WARNING
    logger.log(
        log_level,
        f"[ERROR-HANDLER] {error_code}: {error_message} (Request-ID: {request_id})",
        extra={"request_id": request_id, "error_code": error_code}
    )
    
    return JSONResponse(
        status_code=status_code,
        content=response_data
    )


# =============================================================================
# EXCEPTION HANDLERS
# =============================================================================

def setup_error_handlers(app: FastAPI):
    """
    Konfiguriert alle Error-Handler für die FastAPI-App
    
    Args:
        app: FastAPI-Instanz
    """
    
    @app.exception_handler(MineSearchException)
    async def minesearch_exception_handler(request: Request, exc: MineSearchException):
        """Handler für MineSearch-spezifische Exceptions"""
        
        return build_error_response(
            error_message=exc.message,
            error_code=exc.error_code,
            status_code=exc.status_code,
            details=exc.details,
            request=request
        )
    
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handler für Pydantic Validation Errors"""
        
        # Extrahiere erste Validation-Error für Benutzerfreundlichkeit
        first_error = exc.errors()[0] if exc.errors() else {}
        field = ".".join(str(loc) for loc in first_error.get('loc', []))
        message = first_error.get('msg', 'Validierungsfehler')
        
        return build_error_response(
            error_message=f"Validierungsfehler im Feld '{field}': {message}",
            error_code=ErrorCodes.VALIDATION_ERROR,
            status_code=422,
            details={
                "field": field,
                "validation_errors": exc.errors()
            },
            request=request
        )
    
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handler für FastAPI HTTPExceptions"""
        
        # Bestimme Error-Code basierend auf Status-Code
        error_code = ErrorCodes.INTERNAL_SERVER_ERROR
        if exc.status_code == 400:
            error_code = ErrorCodes.VALIDATION_ERROR
        elif exc.status_code == 401:
            error_code = ErrorCodes.UNAUTHORIZED
        elif exc.status_code == 403:
            error_code = ErrorCodes.FORBIDDEN
        elif exc.status_code == 404:
            error_code = ErrorCodes.RESOURCE_NOT_FOUND
        elif exc.status_code == 429:
            error_code = ErrorCodes.RATE_LIMIT_EXCEEDED
        
        return build_error_response(
            error_message=str(exc.detail),
            error_code=error_code,
            status_code=exc.status_code,
            request=request
        )
    
    
    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        """Handler für ValueError"""
        
        return build_error_response(
            error_message=f"Ungültiger Wert: {str(exc)}",
            error_code=ErrorCodes.VALIDATION_ERROR,
            status_code=400,
            request=request
        )
    
    
    @app.exception_handler(KeyError)
    async def key_error_handler(request: Request, exc: KeyError):
        """Handler für KeyError"""
        
        return build_error_response(
            error_message=f"Erforderliches Feld fehlt: {str(exc)}",
            error_code=ErrorCodes.MISSING_REQUIRED_FIELD,
            status_code=400,
            request=request
        )
    
    
    @app.exception_handler(TimeoutError)
    async def timeout_error_handler(request: Request, exc: TimeoutError):
        """Handler für Timeout-Errors"""
        
        return build_error_response(
            error_message="Request-Timeout: Die Anfrage dauerte zu lange",
            error_code=ErrorCodes.TIMEOUT_ERROR,
            status_code=504,
            request=request
        )
    
    
    @app.exception_handler(ConnectionError)
    async def connection_error_handler(request: Request, exc: ConnectionError):
        """Handler für Connection-Errors"""
        
        return build_error_response(
            error_message="Verbindungsfehler zu externem Service",
            error_code=ErrorCodes.EXTERNAL_SERVICE_ERROR,
            status_code=503,
            request=request
        )
    
    
    @app.exception_handler(MemoryError)
    async def memory_error_handler(request: Request, exc: MemoryError):
        """Handler für Memory-Errors"""
        
        return build_error_response(
            error_message="Unzureichender Speicher für Request-Verarbeitung",
            error_code=ErrorCodes.MEMORY_ERROR,
            status_code=507,
            request=request
        )
    
    
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        """Fallback-Handler für alle anderen Exceptions"""
        
        # Logge kompletten Stacktrace für interne Fehler
        logger.error(
            f"[ERROR-HANDLER] Unbehandelter Fehler: {type(exc).__name__}: {str(exc)}",
            extra={
                "exception_type": type(exc).__name__,
                "traceback": traceback.format_exc()
            }
        )
        
        return build_error_response(
            error_message="Unerwarteter Serverfehler aufgetreten",
            error_code=ErrorCodes.INTERNAL_SERVER_ERROR,
            status_code=500,
            details={
                "exception_type": type(exc).__name__
            } if logger.level <= logging.DEBUG else None,
            request=request
        )
    
    
    logger.info("[ERROR-HANDLERS] Alle Error-Handler erfolgreich konfiguriert")


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def log_error_with_context(
    error: Exception,
    context: Dict[str, Any],
    request_id: Optional[str] = None
):
    """
    Loggt Fehler mit zusätzlichem Kontext
    
    Args:
        error: Exception-Objekt
        context: Zusätzlicher Kontext
        request_id: Request-ID
    """
    
    logger.error(
        f"[ERROR-CONTEXT] {type(error).__name__}: {str(error)}",
        extra={
            "request_id": request_id,
            "context": context,
            "exception_type": type(error).__name__,
            "traceback": traceback.format_exc()
        }
    )


def create_error_context(
    operation: str,
    parameters: Dict[str, Any],
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Erstellt Error-Kontext für besseres Debugging
    
    Args:
        operation: Name der Operation
        parameters: Parameter der Operation
        user_id: Benutzer-ID
        
    Returns:
        Error-Kontext Dictionary
    """
    
    return {
        "operation": operation,
        "parameters": parameters,
        "user_id": user_id,
        "timestamp": datetime.now().isoformat()
    }