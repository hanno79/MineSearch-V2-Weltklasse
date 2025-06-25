"""
Author: rahn
Datum: 23.06.2025
Version: 1.0
Beschreibung: Utility-Modul für sicheren Dictionary-Zugriff
"""

from typing import Any, Dict, List, Optional, Union
import logging

logger = logging.getLogger(__name__)


def safe_get(obj: Any, key: str, default: Any = None) -> Any:
    """
    Sicherer Dictionary-Zugriff mit Type-Checking.
    
    Args:
        obj: Das Objekt (sollte ein Dictionary sein)
        key: Der Schlüssel
        default: Standardwert falls Schlüssel nicht existiert oder obj kein dict ist
        
    Returns:
        Der Wert oder default
    """
    if isinstance(obj, dict):
        return obj.get(key, default)
    
    # Log wenn obj kein dict ist aber .get() erwartet wurde
    if obj is not None and not isinstance(obj, (str, int, float, bool, list)):
        logger.debug(f"safe_get called on non-dict object of type {type(obj).__name__}")
    
    return default


def safe_nested_get(obj: Any, *keys: str, default: Any = None) -> Any:
    """
    Sicherer verschachtelter Dictionary-Zugriff.
    
    Args:
        obj: Das Start-Objekt
        *keys: Die Schlüssel-Kette
        default: Standardwert falls ein Schlüssel nicht existiert
        
    Returns:
        Der Wert am Ende der Kette oder default
        
    Example:
        >>> data = {"user": {"name": "John", "age": 30}}
        >>> safe_nested_get(data, "user", "name")  # "John"
        >>> safe_nested_get(data, "user", "email", default="")  # ""
    """
    current = obj
    
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key)
        else:
            return default
            
    return current if current is not None else default


def ensure_dict(obj: Any, default: Optional[Dict] = None) -> Dict:
    """
    Stellt sicher dass ein Objekt ein Dictionary ist.
    
    Args:
        obj: Das zu prüfende Objekt
        default: Standard-Dictionary falls obj kein dict ist
        
    Returns:
        obj wenn es ein dict ist, sonst default oder {}
    """
    if isinstance(obj, dict):
        return obj
    
    if obj is not None:
        logger.debug(f"ensure_dict: Expected dict but got {type(obj).__name__}")
    
    return default if default is not None else {}


def ensure_list(obj: Any, default: Optional[List] = None) -> List:
    """
    Stellt sicher dass ein Objekt eine Liste ist.
    
    Args:
        obj: Das zu prüfende Objekt
        default: Standard-Liste falls obj keine Liste ist
        
    Returns:
        obj wenn es eine Liste ist, sonst default oder []
    """
    if isinstance(obj, list):
        return obj
    
    if obj is not None:
        logger.debug(f"ensure_list: Expected list but got {type(obj).__name__}")
    
    return default if default is not None else []


def safe_json_get(json_data: Any, path: str, default: Any = None) -> Any:
    """
    Sicherer Zugriff auf JSON-Daten mit Punkt-Notation.
    
    Args:
        json_data: Die JSON-Daten
        path: Der Pfad mit Punkt-Notation (z.B. "user.profile.name")
        default: Standardwert
        
    Returns:
        Der Wert oder default
        
    Example:
        >>> data = {"user": {"profile": {"name": "John"}}}
        >>> safe_json_get(data, "user.profile.name")  # "John"
        >>> safe_json_get(data, "user.email", "no@email.com")  # "no@email.com"
    """
    keys = path.split('.')
    return safe_nested_get(json_data, *keys, default=default)


def extract_value_safely(data: Any, field_mappings: Dict[str, str] = None) -> Dict[str, Any]:
    """
    Extrahiert Werte sicher aus verschiedenen Datenstrukturen.
    
    Args:
        data: Die Datenstruktur (dict, list, string, etc.)
        field_mappings: Optionale Feld-Mappings
        
    Returns:
        Ein Dictionary mit extrahierten Werten
    """
    result = {}
    
    if isinstance(data, dict):
        for key, value in data.items():
            # Mappe Feldnamen wenn Mappings vorhanden
            mapped_key = field_mappings.get(key, key) if field_mappings else key
            result[mapped_key] = value
            
    elif isinstance(data, list):
        # Bei Listen, extrahiere erstes Element wenn es ein dict ist
        if data and isinstance(data[0], dict):
            result = extract_value_safely(data[0], field_mappings)
            
    elif isinstance(data, str):
        # Bei Strings, versuche als "general_info" zu speichern
        result["general_info"] = data
        
    else:
        # Andere Typen als String konvertieren
        result["value"] = str(data) if data is not None else None
    
    return result


class SafeDictAccessMixin:
    """
    Mixin-Klasse die sicheren Dictionary-Zugriff für andere Klassen bereitstellt.
    """
    
    def _safe_get(self, obj: Any, key: str, default: Any = None) -> Any:
        """Wrapper für safe_get Funktion"""
        return safe_get(obj, key, default)
    
    def _safe_nested_get(self, obj: Any, *keys: str, default: Any = None) -> Any:
        """Wrapper für safe_nested_get Funktion"""
        return safe_nested_get(obj, *keys, default=default)
    
    def _ensure_dict(self, obj: Any, default: Optional[Dict] = None) -> Dict:
        """Wrapper für ensure_dict Funktion"""
        return ensure_dict(obj, default)
    
    def _ensure_list(self, obj: Any, default: Optional[List] = None) -> List:
        """Wrapper für ensure_list Funktion"""
        return ensure_list(obj, default)
    
    def _extract_safely(self, data: Any, field_mappings: Dict[str, str] = None) -> Dict[str, Any]:
        """Wrapper für extract_value_safely Funktion"""
        return extract_value_safely(data, field_mappings)