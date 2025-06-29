"""
Author: rahn
Datum: 27.06.2025
Version: 1.0
Beschreibung: Basis-Klassen und Exception für Validierung
"""

from typing import Any, Dict, List, Tuple
from ..logger import get_logger

logger = get_logger(__name__)


class ValidationError(Exception):
    """Basis-Exception für Validierungsfehler"""
    pass


class BaseValidator:
    """Abstrakte Basisklasse für alle Validator"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def reset_errors(self):
        """Setzt Fehler und Warnungen zurück"""
        self.errors = []
        self.warnings = []


class DataValidator(BaseValidator):
    """Hauptklasse für Datenvalidierung - delegiert an Spezialvalidatoren"""
    
    def __init__(self):
        super().__init__()
        # Lazy loading der Spezialvalidatoren
        self._mine_validator = None
        self._api_validator = None
        self._currency_validator = None
        self._coordinate_validator = None
    
    @property
    def mine_validator(self):
        """Lazy Loading für MineValidator"""
        if self._mine_validator is None:
            from .mine_validators import MineValidator
            self._mine_validator = MineValidator()
        return self._mine_validator
    
    @property
    def api_validator(self):
        """Lazy Loading für APIValidator"""
        if self._api_validator is None:
            from .api_validators import APIValidator
            self._api_validator = APIValidator()
        return self._api_validator
    
    @property
    def currency_validator(self):
        """Lazy Loading für CurrencyValidator"""
        if self._currency_validator is None:
            from .currency_validators import CurrencyValidator
            self._currency_validator = CurrencyValidator()
        return self._currency_validator
    
    @property
    def coordinate_validator(self):
        """Lazy Loading für CoordinateValidator"""
        if self._coordinate_validator is None:
            from .coordinate_validators import CoordinateValidator
            self._coordinate_validator = CoordinateValidator()
        return self._coordinate_validator
    
    def validate_mine_data(self, data: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
        """Validiert kompletten Minendatensatz"""
        self.reset_errors()
        
        # Delegiere an MineValidator
        is_valid, errors, warnings = self.mine_validator.validate_mine_data(data)
        
        # Füge Fehler und Warnungen hinzu
        self.errors.extend(errors)
        self.warnings.extend(warnings)
        
        return is_valid, self.errors, self.warnings
    
    def validate_search_result(self, result: Dict[str, Any]) -> bool:
        """Validiert einzelnes Suchergebnis"""
        return self.api_validator.validate_search_result(result)
    
    def clean_numeric_value(self, value: Any):
        """Bereinigt und konvertiert numerische Werte"""
        return self.currency_validator.clean_numeric_value(value)
    
    def normalize_currency_amount(self, amount: Any, target_currency: str = 'CAD'):
        """Normalisiert Währungsbeträge zu Zielwährung"""
        return self.currency_validator.normalize_currency_amount(amount, target_currency)
    
    def extract_currency(self, amount_str: str):
        """Extrahiert Betrag und Währung aus String"""
        return self.currency_validator.extract_currency(amount_str)
    
    def normalize_status(self, status: str) -> str:
        """Normalisiert Minenstatus zu Standardwerten"""
        return self.mine_validator.normalize_status(status)
    
    def normalize_commodity(self, commodity: str) -> str:
        """Normalisiert Rohstoffnamen"""
        return self.mine_validator.normalize_commodity(commodity)


# Singleton-Instanz
_validator = None


def get_validator() -> DataValidator:
    """Factory-Funktion für DataValidator"""
    global _validator
    if _validator is None:
        _validator = DataValidator()
    return _validator