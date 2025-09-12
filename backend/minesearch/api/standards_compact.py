"""
Compact API Standards
Kompakte Version der API Standards

Author: MineSearch Development Team
Date: 2025-01-11
"""

from typing import Dict, Any, Optional, List, Callable
from functools import wraps
from datetime import datetime
import logging
import time
import uuid
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class APIStandards:
    """Zentrale Sammlung aller API-Entwicklungsstandards"""

    @staticmethod
    def validate_request_data(data: Dict[str, Any], required_fields: List[str]) -> Dict[str, Any]:
        """Validiere Request-Daten"""
        try:
            validation_result = {
                'valid': True,
                'errors': [],
                'data': data
            }
            
            # Prüfe erforderliche Felder
            for field in required_fields:
                if field not in data:
                    validation_result['valid'] = False
                    validation_result['errors'].append(f"Required field missing: {field}")
            
            # Prüfe Datentypen
            if 'mine_name' in data and not isinstance(data['mine_name'], str):
                validation_result['valid'] = False
                validation_result['errors'].append("mine_name must be a string")
            
            if 'country' in data and not isinstance(data['country'], str):
                validation_result['valid'] = False
                validation_result['errors'].append("country must be a string")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Fehler bei Request-Validierung: {e}")
            return {
                'valid': False,
                'errors': [str(e)],
                'data': data
            }

    @staticmethod
    def build_success_response(data: Any, message: str = "Success") -> Dict[str, Any]:
        """Erstelle Erfolgs-Response"""
        return {
            'success': True,
            'message': message,
            'data': data,
            'timestamp': datetime.now().isoformat(),
            'request_id': str(uuid.uuid4())
        }

    @staticmethod
    def build_error_response(error: str, error_code: str = "GENERIC_ERROR", status_code: int = 400) -> Dict[str, Any]:
        """Erstelle Fehler-Response"""
        return {
            'success': False,
            'error': error,
            'error_code': error_code,
            'status_code': status_code,
            'timestamp': datetime.now().isoformat(),
            'request_id': str(uuid.uuid4())
        }

    @staticmethod
    def log_request(request_data: Dict[str, Any], endpoint: str):
        """Logge Request"""
        try:
            logger.info(f"Request to {endpoint}: {request_data}")
        except Exception as e:
            logger.error(f"Fehler beim Loggen des Requests: {e}")

    @staticmethod
    def log_response(response_data: Dict[str, Any], endpoint: str, duration: float):
        """Logge Response"""
        try:
            logger.info(f"Response from {endpoint} (duration: {duration:.2f}s): {response_data}")
        except Exception as e:
            logger.error(f"Fehler beim Loggen der Response: {e}")


def api_endpoint(endpoint_name: str, required_fields: List[str] = None):
    """Decorator für API-Endpoints"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            request_id = str(uuid.uuid4())
            
            try:
                # Logge Request
                if required_fields:
                    APIStandards.log_request(kwargs, endpoint_name)
                
                # Validiere Request
                if required_fields:
                    validation = APIStandards.validate_request_data(kwargs, required_fields)
                    if not validation['valid']:
                        return APIStandards.build_error_response(
                            f"Validation failed: {', '.join(validation['errors'])}",
                            "VALIDATION_ERROR"
                        )
                
                # Führe Funktion aus
                result = await func(*args, **kwargs)
                
                # Logge Response
                duration = time.time() - start_time
                APIStandards.log_response(result, endpoint_name, duration)
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"Fehler in {endpoint_name}: {e}")
                
                return APIStandards.build_error_response(
                    str(e),
                    "INTERNAL_ERROR",
                    500
                )
        
        return wrapper
    return decorator


def rate_limit(max_requests: int = 100, window_seconds: int = 60):
    """Rate Limiting Decorator"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Simuliere Rate Limiting
            # In der Realität würde hier ein Redis oder ähnliches verwendet
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def cache_response(ttl_seconds: int = 300):
    """Response Caching Decorator"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Simuliere Caching
            # In der Realität würde hier ein Cache-System verwendet
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def authenticate(required_permissions: List[str] = None):
    """Authentication Decorator"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Simuliere Authentication
            # In der Realität würde hier echte Auth-Logik stehen
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def validate_schema(schema_class):
    """Schema Validation Decorator"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Simuliere Schema-Validierung
            # In der Realität würde hier Pydantic oder ähnliches verwendet
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


class ErrorCodes:
    """Standardisierte Fehlercodes"""
    
    # Allgemeine Fehler
    GENERIC_ERROR = "GENERIC_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    AUTHORIZATION_ERROR = "AUTHORIZATION_ERROR"
    
    # API-spezifische Fehler
    INVALID_REQUEST = "INVALID_REQUEST"
    MISSING_PARAMETERS = "MISSING_PARAMETERS"
    INVALID_PARAMETERS = "INVALID_PARAMETERS"
    
    # Datenbank-Fehler
    DATABASE_ERROR = "DATABASE_ERROR"
    CONNECTION_ERROR = "CONNECTION_ERROR"
    
    # Provider-Fehler
    PROVIDER_ERROR = "PROVIDER_ERROR"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    
    # Mining-spezifische Fehler
    MINE_NOT_FOUND = "MINE_NOT_FOUND"
    INVALID_MINE_DATA = "INVALID_MINE_DATA"
    EXTRACTION_FAILED = "EXTRACTION_FAILED"


class MineSearchException(Exception):
    """Basis-Exception für MineSearch"""
    
    def __init__(self, message: str, error_code: str = ErrorCodes.GENERIC_ERROR, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.timestamp = datetime.now().isoformat()


def log_error_with_context(error: Exception, context: Dict[str, Any] = None):
    """Logge Fehler mit Kontext"""
    try:
        error_info = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'timestamp': datetime.now().isoformat(),
            'context': context or {}
        }
        
        if isinstance(error, MineSearchException):
            error_info['error_code'] = error.error_code
            error_info['status_code'] = error.status_code
        
        logger.error(f"Error occurred: {error_info}")
        
    except Exception as e:
        logger.error(f"Fehler beim Loggen des Fehlers: {e}")


@asynccontextmanager
async def api_context(request_id: str = None, endpoint: str = None):
    """API-Kontext Manager"""
    if not request_id:
        request_id = str(uuid.uuid4())
    
    start_time = time.time()
    
    try:
        logger.info(f"Starting API request: {request_id} at {endpoint}")
        yield {
            'request_id': request_id,
            'endpoint': endpoint,
            'start_time': start_time
        }
    except Exception as e:
        logger.error(f"Error in API context: {e}")
        raise
    finally:
        duration = time.time() - start_time
        logger.info(f"Completed API request: {request_id} (duration: {duration:.2f}s)")


def get_request_metrics() -> Dict[str, Any]:
    """Hole Request-Metriken"""
    return {
        'total_requests': 0,  # Würde in der Realität aus der Datenbank kommen
        'successful_requests': 0,
        'failed_requests': 0,
        'average_response_time': 0.0,
        'timestamp': datetime.now().isoformat()
    }


def get_health_status() -> Dict[str, Any]:
    """Hole Gesundheitsstatus"""
    return {
        'status': 'healthy',
        'api_version': '1.0',
        'timestamp': datetime.now().isoformat(),
        'components': {
            'database': 'healthy',
            'providers': 'healthy',
            'cache': 'healthy'
        }
    }


__all__ = [
    "APIStandards",
    "api_endpoint",
    "rate_limit",
    "cache_response",
    "authenticate",
    "validate_schema",
    "ErrorCodes",
    "MineSearchException",
    "log_error_with_context",
    "api_context",
    "get_request_metrics",
    "get_health_status"
]
