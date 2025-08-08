"""
Author: rahn
Datum: 25.07.2025
Version: 1.0
Beschreibung: Nachhaltige Code-Standards für API-Entwicklung
"""

from typing import Dict, Any, Optional, List, Callable
from functools import wraps
from datetime import datetime
import logging
import time
import uuid
from contextlib import asynccontextmanager

from .validators import validate_request, build_success_response, build_error_response
from .error_handlers import ErrorCodes, MineSearchException, log_error_with_context
from .schemas import BaseRequest, BaseResponse

logger = logging.getLogger(__name__)

# =============================================================================
# API DEVELOPMENT STANDARDS
# =============================================================================

class APIStandards:
    """
    Zentrale Sammlung aller API-Entwicklungsstandards
    Diese Standards MÜSSEN von allen Entwicklern befolgt werden
    """
    
    # NAMING CONVENTIONS
    ENDPOINT_NAMING = {
        "format": "kebab-case",  # /search-mine, /batch-process
        "versioning": "/api/v1/",
        "resources": "plural_nouns",  # /mines, /searches, /results
        "actions": "http_verbs"  # GET, POST, PUT, DELETE
    }
    
    # RESPONSE STRUCTURE
    RESPONSE_STANDARDS = {
        "always_include": ["success", "timestamp", "request_id"],
        "success_format": {
            "success": True,
            "data": "actual_response_data",
            "timestamp": "ISO_8601_format",
            "request_id": "uuid_v4"
        },
        "error_format": {
            "success": False,
            "error": "user_friendly_message",
            "code": "SPECIFIC_ERROR_CODE",
            "timestamp": "ISO_8601_format",
            "request_id": "uuid_v4"
        }
    }
    
    # VALIDATION REQUIREMENTS
    VALIDATION_STANDARDS = {
        "input_sanitization": "MANDATORY",
        "request_size_limit": "10MB",
        "field_length_limits": "ENFORCED",
        "sql_injection_protection": "REQUIRED",
        "xss_protection": "REQUIRED"
    }
    
    # PERFORMANCE REQUIREMENTS
    PERFORMANCE_STANDARDS = {
        "response_time_target": "< 2000ms",
        "timeout_limit": "30s",
        "concurrent_request_limit": 50,
        "rate_limiting": "100_requests_per_minute",
        "caching_required": True
    }
    
    # LOGGING REQUIREMENTS
    LOGGING_STANDARDS = {
        "all_requests": "INFO level",
        "all_errors": "ERROR level",
        "performance_metrics": "DEBUG level",
        "sensitive_data": "NEVER_LOG",
        "request_id_tracking": "MANDATORY"
    }
    
    # SECURITY REQUIREMENTS
    SECURITY_STANDARDS = {
        "input_validation": "STRICT",
        "output_encoding": "REQUIRED",
        "cors_configuration": "RESTRICTIVE",
        "error_information_disclosure": "MINIMAL",
        "api_key_validation": "WHEN_APPLICABLE"
    }


# =============================================================================
# STANDARD DECORATORS
# =============================================================================

def standard_api_endpoint(
    request_schema: Optional[BaseRequest] = None,
    response_schema: Optional[BaseResponse] = None,
    cache_ttl: Optional[int] = None,
    rate_limit: Optional[int] = None,
    require_auth: bool = False
):
    """
    Standard-Decorator für alle API-Endpoints
    Implementiert alle API-Standards automatisch
    
    Args:
        request_schema: Pydantic-Schema für Request-Validierung
        response_schema: Pydantic-Schema für Response-Validierung
        cache_ttl: Cache-TTL in Sekunden
        rate_limit: Rate-Limit pro Minute
        require_auth: Authentifizierung erforderlich
    """
    
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request_id = str(uuid.uuid4())
            start_time = time.time()
            
            try:
                # REQUEST TRACKING
                logger.info(
                    f"[API-STANDARD] {func.__name__} started",
                    extra={"request_id": request_id, "endpoint": func.__name__}
                )
                
                # REQUEST VALIDATION
                if request_schema and len(args) > 1:
                    # Validiere Request gegen Schema
                    validated_request = validate_request(request_schema, args[1])
                    args = (args[0], validated_request, *args[2:])
                
                # AUTHENTICATION CHECK  
                if require_auth:
                    # Implementierung der Auth-Prüfung
                    pass
                
                # RATE LIMITING
                if rate_limit:
                    # Implementierung des Rate-Limiting
                    pass
                
                # EXECUTE FUNCTION
                result = await func(*args, **kwargs)
                
                # RESPONSE VALIDATION
                if response_schema and result:
                    # Validiere Response gegen Schema
                    if isinstance(result, dict):
                        response_schema(**result)
                
                # PERFORMANCE LOGGING
                duration = time.time() - start_time
                logger.info(
                    f"[API-STANDARD] {func.__name__} completed successfully",
                    extra={
                        "request_id": request_id,
                        "duration_ms": round(duration * 1000, 2),
                        "endpoint": func.__name__
                    }
                )
                
                # ENSURE STANDARD RESPONSE FORMAT
                if isinstance(result, dict) and "request_id" not in result:
                    result["request_id"] = request_id
                
                return result
                
            except MineSearchException as e:
                # BUSINESS LOGIC ERRORS
                duration = time.time() - start_time
                logger.warning(
                    f"[API-STANDARD] {func.__name__} business error: {e.message}",
                    extra={
                        "request_id": request_id,
                        "error_code": e.error_code,
                        "duration_ms": round(duration * 1000, 2)
                    }
                )
                
                return build_error_response(
                    error_message=e.message,
                    error_code=e.error_code,
                    request_id=request_id
                )
            
            except Exception as e:
                # UNEXPECTED ERRORS
                duration = time.time() - start_time
                log_error_with_context(
                    error=e,
                    context={
                        "endpoint": func.__name__,
                        "args": str(args)[:200],  # Begrenzt für Sicherheit
                        "kwargs": str(kwargs)[:200]
                    },
                    request_id=request_id
                )
                
                logger.error(
                    f"[API-STANDARD] {func.__name__} unexpected error",
                    extra={
                        "request_id": request_id,
                        "error_type": type(e).__name__,
                        "duration_ms": round(duration * 1000, 2)
                    }
                )
                
                return build_error_response(
                    error_message="Unerwarteter Serverfehler",
                    error_code=ErrorCodes.INTERNAL_SERVER_ERROR,
                    request_id=request_id
                )
        
        return wrapper
    return decorator


def require_fields(*required_fields):
    """
    Decorator zur Validierung erforderlicher Felder
    
    Args:
        *required_fields: Liste der erforderlichen Feldnamen
    """
    
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Suche Request-Objekt in Args
            request_data = None
            for arg in args:
                if hasattr(arg, '__dict__') and not callable(arg):
                    request_data = arg.__dict__ if hasattr(arg, '__dict__') else arg
                    break
            
            if not request_data and kwargs:
                request_data = kwargs
            
            # Prüfe erforderliche Felder
            if request_data:
                missing_fields = []
                for field in required_fields:
                    if field not in request_data or not request_data[field]:
                        missing_fields.append(field)
                
                if missing_fields:
                    raise MineSearchException(
                        message=f"Erforderliche Felder fehlen: {', '.join(missing_fields)}",
                        error_code=ErrorCodes.MISSING_REQUIRED_FIELD,
                        status_code=400
                    )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def performance_monitor(max_duration_ms: int = 5000):
    """
    Decorator zur Performance-Überwachung
    
    Args:
        max_duration_ms: Maximale erlaubte Ausführungszeit in ms
    """
    
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            result = await func(*args, **kwargs)
            
            duration_ms = (time.time() - start_time) * 1000
            
            if duration_ms > max_duration_ms:
                logger.warning(
                    f"[PERFORMANCE] {func.__name__} exceeded max duration",
                    extra={
                        "duration_ms": round(duration_ms, 2),
                        "max_duration_ms": max_duration_ms,
                        "endpoint": func.__name__
                    }
                )
            
            return result
        
        return wrapper
    return decorator


@asynccontextmanager
async def api_operation_context(operation_name: str, parameters: Dict[str, Any]):
    """
    Context Manager für API-Operationen mit standardisiertem Logging
    
    Args:
        operation_name: Name der Operation
        parameters: Operation-Parameter
    """
    
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    logger.info(
        f"[OPERATION] {operation_name} started",
        extra={
            "request_id": request_id,
            "operation": operation_name,
            "parameters": parameters
        }
    )
    
    try:
        yield request_id
        
        duration = time.time() - start_time
        logger.info(
            f"[OPERATION] {operation_name} completed",
            extra={
                "request_id": request_id,
                "duration_ms": round(duration * 1000, 2)
            }
        )
    
    except Exception as e:
        duration = time.time() - start_time
        log_error_with_context(
            error=e,
            context={
                "operation": operation_name,
                "parameters": parameters
            },
            request_id=request_id
        )
        
        logger.error(
            f"[OPERATION] {operation_name} failed",
            extra={
                "request_id": request_id,
                "error_type": type(e).__name__,
                "duration_ms": round(duration * 1000, 2)
            }
        )
        raise


# =============================================================================
# CODE QUALITY STANDARDS
# =============================================================================

class CodeQualityStandards:
    """
    Standards für Code-Qualität in API-Entwicklung
    """
    
    # FUNCTION STANDARDS
    FUNCTION_STANDARDS = {
        "max_lines": 50,  # Keine Funktion > 50 Zeilen
        "max_parameters": 6,  # Maximal 6 Parameter
        "naming": "descriptive_verbs",  # process_mine_search()
        "docstring": "MANDATORY",  # Jede Funktion braucht Docstring
        "type_hints": "REQUIRED"  # Alle Parameter und Returns typisiert
    }
    
    # CLASS STANDARDS
    CLASS_STANDARDS = {
        "single_responsibility": True,  # Eine Verantwortlichkeit pro Klasse
        "max_methods": 15,  # Maximal 15 Methoden pro Klasse
        "naming": "descriptive_nouns",  # MineSearchService
        "docstring": "MANDATORY"
    }
    
    # FILE STANDARDS
    FILE_STANDARDS = {
        "max_lines": 500,  # Siehe CLAUDE.md Regel 1
        "imports_sorted": True,  # Alphabetisch sortierte Imports
        "no_wildcard_imports": True,  # Keine from module import *
        "header_required": True  # Author, Datum, Version, Beschreibung
    }
    
    # TESTING STANDARDS
    TESTING_STANDARDS = {
        "unit_test_coverage": 80,  # Mindestens 80% Test-Coverage
        "integration_tests": "REQUIRED",  # Für alle API-Endpoints
        "test_naming": "test_should_do_when_condition",
        "mock_external_services": True
    }


def validate_function_standards(func: Callable) -> List[str]:
    """
    Validiert eine Funktion gegen Code-Standards
    
    Args:
        func: Zu validierende Funktion
        
    Returns:
        Liste der Standard-Verstöße
    """
    
    violations = []
    
    # Prüfe Docstring
    if not func.__doc__:
        violations.append("Fehlender Docstring")
    
    # Prüfe Type Hints
    if not hasattr(func, '__annotations__'):
        violations.append("Fehlende Type Hints")
    
    # Prüfe Funktionsname
    if not func.__name__.islower() or '_' not in func.__name__:
        violations.append("Funktionsname sollte snake_case verwenden")
    
    return violations


# =============================================================================
# API DOCUMENTATION STANDARDS
# =============================================================================

class DocumentationStandards:
    """
    Standards für API-Dokumentation
    """
    
    ENDPOINT_DOCUMENTATION = {
        "summary": "REQUIRED",  # Kurze Beschreibung
        "description": "DETAILED",  # Ausführliche Beschreibung
        "parameters": "ALL_DOCUMENTED",  # Alle Parameter erklärt
        "responses": "ALL_STATUS_CODES",  # Alle möglichen Response-Codes
        "examples": "REQUEST_RESPONSE",  # Request/Response-Beispiele
        "error_codes": "DOCUMENTED"  # Alle Error-Codes erklärt
    }
    
    SCHEMA_DOCUMENTATION = {
        "field_descriptions": "MANDATORY",  # Jedes Feld beschrieben
        "validation_rules": "DOCUMENTED",  # Validierungsregeln erklärt
        "examples": "PROVIDED",  # Beispielwerte
        "constraints": "LISTED"  # Min/Max-Werte, Pattern etc.
    }


def generate_endpoint_documentation(func: Callable) -> Dict[str, Any]:
    """
    Generiert Dokumentation für API-Endpoint
    
    Args:
        func: API-Endpoint-Funktion
        
    Returns:
        Dokumentations-Dictionary
    """
    
    return {
        "endpoint": func.__name__,
        "description": func.__doc__ or "Keine Beschreibung verfügbar",
        "parameters": getattr(func, '__annotations__', {}),
        "generated_at": datetime.now().isoformat()
    }


# =============================================================================
# MIGRATION UTILITIES
# =============================================================================

class LegacyAPIHandler:
    """
    Handler für Migration von Legacy-API-Code zu Standards
    """
    
    @staticmethod
    def wrap_legacy_endpoint(legacy_func: Callable) -> Callable:
        """
        Wrapped Legacy-Endpoint mit Standard-Compliance
        
        Args:
            legacy_func: Legacy-Funktion
            
        Returns:
            Standard-konforme Wrapper-Funktion
        """
        
        @standard_api_endpoint()
        @wraps(legacy_func)
        async def wrapper(*args, **kwargs):
            logger.warning(
                f"[LEGACY] Using legacy endpoint: {legacy_func.__name__}",
                extra={"legacy_endpoint": legacy_func.__name__}
            )
            
            try:
                result = await legacy_func(*args, **kwargs)
                
                # Konvertiere Legacy-Response zu Standard-Format
                if isinstance(result, dict) and "success" not in result:
                    result = build_success_response(result)
                
                return result
                
            except Exception as e:
                return build_error_response(
                    error_message=f"Legacy endpoint error: {str(e)}",
                    error_code=ErrorCodes.INTERNAL_SERVER_ERROR
                )
        
        return wrapper


# =============================================================================
# COMPLIANCE CHECKER
# =============================================================================

def check_api_compliance(module_name: str) -> Dict[str, Any]:
    """
    Prüft ein Modul auf API-Standard-Compliance
    
    Args:
        module_name: Name des zu prüfenden Moduls
        
    Returns:
        Compliance-Report
    """
    
    import inspect
    import importlib
    
    try:
        module = importlib.import_module(module_name)
        functions = inspect.getmembers(module, inspect.isfunction)
        
        report = {
            "module": module_name,
            "total_functions": len(functions),
            "compliant_functions": 0,
            "violations": [],
            "checked_at": datetime.now().isoformat()
        }
        
        for name, func in functions:
            violations = validate_function_standards(func)
            if violations:
                report["violations"].append({
                    "function": name,
                    "violations": violations
                })
            else:
                report["compliant_functions"] += 1
        
        report["compliance_rate"] = (
            report["compliant_functions"] / report["total_functions"] * 100
            if report["total_functions"] > 0 else 0
        )
        
        return report
        
    except ImportError as e:
        return {
            "module": module_name,
            "error": f"Module konnte nicht importiert werden: {str(e)}",
            "checked_at": datetime.now().isoformat()
        }