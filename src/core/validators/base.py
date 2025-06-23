"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Basis-Klassen für Validatoren
"""

from abc import ABC, abstractmethod
from typing import Any, Tuple, Optional
import logging


class ValidationError(Exception):
    """Basis-Exception für Validierungsfehler"""
    pass


class BaseValidator(ABC):
    """Abstrakte Basis-Klasse für alle Validatoren"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def validate(self, value: Any) -> Tuple[bool, Optional[str]]:
        """
        Validiert einen Wert
        
        Args:
            value: Zu validierender Wert
            
        Returns:
            Tuple (is_valid, error_message)
        """
        pass
    
    @abstractmethod
    def normalize(self, value: Any) -> Any:
        """
        Normalisiert einen Wert
        
        Args:
            value: Zu normalisierender Wert
            
        Returns:
            Normalisierter Wert
        """
        pass
    
    def validate_and_normalize(self, value: Any) -> Tuple[bool, Any, Optional[str]]:
        """
        Validiert und normalisiert einen Wert
        
        Returns:
            Tuple (is_valid, normalized_value, error_message)
        """
        is_valid, error = self.validate(value)
        
        if is_valid:
            try:
                normalized = self.normalize(value)
                return True, normalized, None
            except Exception as e:
                return False, value, f"Normalisierungsfehler: {str(e)}"
        else:
            return False, value, error
    
    def _clean_string(self, value: str) -> str:
        """Bereinigt einen String"""
        if not isinstance(value, str):
            return str(value)
        
        # Entferne führende/nachfolgende Leerzeichen
        cleaned = value.strip()
        
        # Reduziere mehrfache Leerzeichen
        import re
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        return cleaned