"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Mining-spezifische Validatoren
"""

import re
from typing import Any, Tuple, Optional, Union, List
from decimal import Decimal, InvalidOperation

from .base import BaseValidator
from .constants import ValidatorConstants


class CommodityValidator(BaseValidator):
    """Validiert Rohstoff-Angaben"""
    
    def __init__(self):
        super().__init__()
        self.valid_commodities = set(c.lower() for c in ValidatorConstants.VALID_COMMODITIES)
        self.normalization = ValidatorConstants.COMMODITY_NORMALIZATION
    
    def validate(self, value: Any) -> Tuple[bool, Optional[str]]:
        """Validiert Rohstoff"""
        if not value:
            return False, "Rohstoff darf nicht leer sein"
        
        # Unterstütze Listen
        if isinstance(value, list):
            for commodity in value:
                is_valid, error = self._validate_single(commodity)
                if not is_valid:
                    return False, error
            return True, None
        
        return self._validate_single(value)
    
    def _validate_single(self, commodity: Any) -> Tuple[bool, Optional[str]]:
        """Validiert einzelnen Rohstoff"""
        if not commodity:
            return False, "Rohstoff darf nicht leer sein"
        
        commodity_str = str(commodity).strip().lower()
        
        # Prüfe gegen Liste
        if commodity_str in self.valid_commodities:
            return True, None
        
        # Prüfe Normalisierung
        if commodity_str in self.normalization:
            return True, None
        
        # Fuzzy-Match für zusammengesetzte Begriffe
        for valid in self.valid_commodities:
            if valid in commodity_str or commodity_str in valid:
                return True, None
        
        return False, f"Unbekannter Rohstoff: {commodity}"
    
    def normalize(self, value: Any) -> Union[str, List[str]]:
        """Normalisiert Rohstoff"""
        if isinstance(value, list):
            return [self._normalize_single(c) for c in value]
        
        return self._normalize_single(value)
    
    def _normalize_single(self, commodity: Any) -> str:
        """Normalisiert einzelnen Rohstoff"""
        commodity_str = str(commodity).strip().lower()
        
        # Nutze Normalisierungstabelle
        if commodity_str in self.normalization:
            return self.normalization[commodity_str]
        
        # Fuzzy-Match
        for key, normalized in self.normalization.items():
            if key in commodity_str:
                return normalized
        
        # Titel-Case als Fallback
        return commodity_str.title()


class MineStatusValidator(BaseValidator):
    """Validiert Minenstatus"""
    
    def __init__(self):
        super().__init__()
        self.valid_status = set(s.lower() for s in ValidatorConstants.VALID_MINE_STATUS)
        self.normalization = ValidatorConstants.STATUS_NORMALIZATION
    
    def validate(self, value: Any) -> Tuple[bool, Optional[str]]:
        """Validiert Status"""
        if not value:
            return False, "Status darf nicht leer sein"
        
        status_str = str(value).strip().lower()
        
        # Prüfe gegen Liste
        if status_str in self.valid_status:
            return True, None
        
        # Prüfe Normalisierung
        if status_str in self.normalization:
            return True, None
        
        # Partial Match
        for valid in self.valid_status:
            if valid in status_str or status_str in valid:
                return True, None
        
        return False, f"Ungültiger Minenstatus: {value}"
    
    def normalize(self, value: Any) -> str:
        """Normalisiert Status"""
        status_str = str(value).strip().lower()
        
        # Nutze Normalisierungstabelle
        if status_str in self.normalization:
            return self.normalization[status_str]
        
        # Partial Match
        for key, normalized in self.normalization.items():
            if key in status_str or status_str in key:
                return normalized
        
        # Standard-Fallback
        return 'unbekannt'


class MineTypeValidator(BaseValidator):
    """Validiert Minentyp"""
    
    def __init__(self):
        super().__init__()
        self.valid_types = set(t.lower() for t in ValidatorConstants.VALID_MINE_TYPES)
    
    def validate(self, value: Any) -> Tuple[bool, Optional[str]]:
        """Validiert Minentyp"""
        if not value:
            return True, None  # Typ ist optional
        
        type_str = str(value).strip().lower()
        
        # Exakte Übereinstimmung
        if type_str in self.valid_types:
            return True, None
        
        # Partial Match
        for valid in self.valid_types:
            if valid in type_str or type_str in valid:
                return True, None
        
        return False, f"Ungültiger Minentyp: {value}"
    
    def normalize(self, value: Any) -> Optional[str]:
        """Normalisiert Minentyp"""
        if not value:
            return None
        
        type_str = str(value).strip().lower()
        
        # Normalisierungstabelle
        type_map = {
            'open pit': 'Tagebau',
            'tagebau': 'Tagebau',
            'surface': 'Tagebau',
            'strip': 'Tagebau',
            'quarry': 'Steinbruch',
            'underground': 'Untertagebau',
            'untertagebau': 'Untertagebau',
            'subsurface': 'Untertagebau',
            'shaft': 'Untertagebau',
            'placer': 'Seifenbergbau',
            'alluvial': 'Seifenbergbau',
            'dredging': 'Baggerung',
            'solution': 'Laugung',
            'in-situ': 'In-Situ',
            'isl': 'In-Situ',
            'combined': 'Kombiniert',
            'hybrid': 'Kombiniert',
            'mixed': 'Kombiniert'
        }
        
        # Suche beste Übereinstimmung
        for key, normalized in type_map.items():
            if key in type_str:
                return normalized
        
        return type_str.title()


class ProductionValidator(BaseValidator):
    """Validiert Produktionsangaben"""
    
    def __init__(self):
        super().__init__()
        self.units = ValidatorConstants.PRODUCTION_UNITS
    
    def validate(self, value: Any) -> Tuple[bool, Optional[str]]:
        """Validiert Produktionsangabe"""
        if not value:
            return True, None  # Produktion ist optional
        
        value_str = str(value).strip()
        
        # Parse Zahl und Einheit
        match = re.match(r'^([\d,.\s]+)\s*([a-zA-Z/%]+)?', value_str)
        if not match:
            return False, "Ungültiges Produktionsformat"
        
        number_str = match.group(1).replace(',', '').replace(' ', '')
        unit_str = match.group(2) if match.group(2) else ''
        
        # Validiere Zahl
        try:
            number = float(number_str)
            if number < 0:
                return False, "Produktion kann nicht negativ sein"
        except ValueError:
            return False, f"Ungültige Zahl: {number_str}"
        
        # Validiere Einheit wenn vorhanden
        if unit_str:
            unit_lower = unit_str.lower()
            valid_unit = False
            
            for unit_type, units in self.units.items():
                if any(unit_lower == u.lower() or unit_lower in u.lower() for u in units):
                    valid_unit = True
                    break
            
            if not valid_unit:
                return False, f"Ungültige Einheit: {unit_str}"
        
        return True, None
    
    def normalize(self, value: Any) -> Optional[dict]:
        """Normalisiert Produktionsangabe"""
        if not value:
            return None
        
        value_str = str(value).strip()
        
        # Parse Zahl und Einheit
        match = re.match(r'^([\d,.\s]+)\s*([a-zA-Z/%]+)?', value_str)
        if not match:
            return None
        
        number_str = match.group(1).replace(',', '').replace(' ', '')
        unit_str = match.group(2) if match.group(2) else ''
        
        try:
            number = float(number_str)
        except ValueError:
            return None
        
        # Normalisiere Einheit
        normalized_unit = self._normalize_unit(unit_str) if unit_str else 'units'
        
        return {
            'value': number,
            'unit': normalized_unit,
            'display': f"{number:,.0f} {normalized_unit}"
        }
    
    def _normalize_unit(self, unit: str) -> str:
        """Normalisiert Produktionseinheit"""
        unit_lower = unit.lower()
        
        # Einheiten-Mapping
        unit_map = {
            't': 'tonnes',
            'mt': 'million tonnes',
            'kg': 'kg',
            'g': 'grams',
            'oz': 'ounces',
            'lbs': 'pounds',
            'm3': 'cubic meters',
            'l': 'liters',
            'bbl': 'barrels',
            'g/t': 'g/t',
            'oz/t': 'oz/t',
            'ppm': 'ppm',
            '%': 'percent'
        }
        
        # Exakte Übereinstimmung
        if unit_lower in unit_map:
            return unit_map[unit_lower]
        
        # Suche beste Übereinstimmung
        for abbr, full in unit_map.items():
            if abbr in unit_lower:
                return full
        
        return unit


class FinancialValidator(BaseValidator):
    """Validiert finanzielle Angaben"""
    
    def __init__(self):
        super().__init__()
        self.currencies = ValidatorConstants.VALID_CURRENCIES
    
    def validate(self, value: Any) -> Tuple[bool, Optional[str]]:
        """Validiert Finanzangabe"""
        if not value:
            return True, None  # Optional
        
        value_str = str(value).strip()
        
        # Parse Währung und Betrag
        currency_pattern = r'^([A-Z$€£¥]{1,3})?\s*([\d,.\s]+)\s*([MmBbKk](?:illion|illion)?)?'
        match = re.match(currency_pattern, value_str)
        
        if not match:
            return False, "Ungültiges Finanzformat"
        
        currency = match.group(1)
        amount_str = match.group(2).replace(',', '').replace(' ', '')
        multiplier = match.group(3)
        
        # Validiere Betrag
        try:
            amount = float(amount_str)
            if amount < 0:
                self.logger.warning(f"Negativer Betrag: {amount}")
        except ValueError:
            return False, f"Ungültiger Betrag: {amount_str}"
        
        # Validiere Währung wenn vorhanden
        if currency and currency not in ['$', '€', '£', '¥']:
            if currency.upper() not in self.currencies:
                return False, f"Ungültige Währung: {currency}"
        
        return True, None
    
    def normalize(self, value: Any) -> Optional[dict]:
        """Normalisiert Finanzangabe"""
        if not value:
            return None
        
        value_str = str(value).strip()
        
        # Parse
        currency_pattern = r'^([A-Z$€£¥]{1,3})?\s*([\d,.\s]+)\s*([MmBbKk](?:illion|illion)?)?'
        match = re.match(currency_pattern, value_str)
        
        if not match:
            return None
        
        currency = match.group(1) or 'USD'  # Default USD
        amount_str = match.group(2).replace(',', '').replace(' ', '')
        multiplier = match.group(3)
        
        try:
            amount = float(amount_str)
            
            # Multiplier anwenden
            if multiplier:
                mult_lower = multiplier.lower()
                if 'k' in mult_lower:
                    amount *= 1000
                elif 'm' in mult_lower:
                    amount *= 1_000_000
                elif 'b' in mult_lower:
                    amount *= 1_000_000_000
            
            # Währung normalisieren
            currency_map = {
                '$': 'USD',
                '€': 'EUR',
                '£': 'GBP',
                '¥': 'JPY'
            }
            
            normalized_currency = currency_map.get(currency, currency.upper())
            
            return {
                'amount': amount,
                'currency': normalized_currency,
                'display': f"{normalized_currency} {amount:,.2f}"
            }
            
        except ValueError:
            return None