"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Haupt-Datenvalidator für Mining-Daten
"""

import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from .base import ValidationError
from .field_validators import (
    LocationValidator,
    CoordinateValidator,
    DateValidator,
    URLValidator,
    EmailValidator
)
from .mining_validators import (
    CommodityValidator,
    MineStatusValidator,
    MineTypeValidator,
    ProductionValidator,
    FinancialValidator
)


class DataValidator:
    """Hauptklasse für Mining-Datenvalidierung"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        
        # Initialisiere Feld-Validatoren
        self.location_validator = LocationValidator()
        self.coordinate_validator = CoordinateValidator()
        self.commodity_validator = CommodityValidator()
        self.status_validator = MineStatusValidator()
        self.type_validator = MineTypeValidator()
        self.production_validator = ProductionValidator()
        self.financial_validator = FinancialValidator()
        self.date_validator = DateValidator()
        self.url_validator = URLValidator()
        self.email_validator = EmailValidator()
        
        # Validierungsergebnisse
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate_mine_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validiert komplette Minendaten"""
        self.errors = []
        self.warnings = []
        
        validated_data = {}
        
        # Name (Pflichtfeld)
        if 'name' in data:
            name = self._clean_string(data['name'])
            if name:
                validated_data['name'] = name
            else:
                self.errors.append("Minenname darf nicht leer sein")
        else:
            self.errors.append("Minenname fehlt")
        
        # Location (Pflichtfeld)
        if 'location' in data:
            is_valid, normalized, error = self.location_validator.validate_and_normalize(data['location'])
            if is_valid:
                validated_data['location'] = normalized
            else:
                self.errors.append(error)
        else:
            self.errors.append("Standort fehlt")
        
        # Coordinates (optional)
        if 'coordinates' in data and data['coordinates']:
            is_valid, normalized, error = self.coordinate_validator.validate_and_normalize(data['coordinates'])
            if is_valid:
                validated_data['coordinates'] = normalized
            else:
                self.warnings.append(f"Koordinaten: {error}")
        
        # Commodity (Pflichtfeld)
        if 'commodity' in data:
            is_valid, normalized, error = self.commodity_validator.validate_and_normalize(data['commodity'])
            if is_valid:
                validated_data['commodity'] = normalized
            else:
                self.errors.append(error)
        else:
            self.errors.append("Rohstoff fehlt")
        
        # Status (Pflichtfeld)
        if 'status' in data:
            is_valid, normalized, error = self.status_validator.validate_and_normalize(data['status'])
            if is_valid:
                validated_data['status'] = normalized
            else:
                self.errors.append(error)
        else:
            self.errors.append("Status fehlt")
        
        # Type (optional)
        if 'mine_type' in data and data['mine_type']:
            is_valid, normalized, error = self.type_validator.validate_and_normalize(data['mine_type'])
            if is_valid:
                validated_data['mine_type'] = normalized
            else:
                self.warnings.append(f"Minentyp: {error}")
        
        # Production (optional)
        if 'production' in data and data['production']:
            is_valid, normalized, error = self.production_validator.validate_and_normalize(data['production'])
            if is_valid:
                validated_data['production'] = normalized
            else:
                self.warnings.append(f"Produktion: {error}")
        
        # Financial data (optional)
        for field in ['revenue', 'investment', 'market_cap']:
            if field in data and data[field]:
                is_valid, normalized, error = self.financial_validator.validate_and_normalize(data[field])
                if is_valid:
                    validated_data[field] = normalized
                else:
                    self.warnings.append(f"{field}: {error}")
        
        # Dates (optional)
        for field in ['start_date', 'discovered_date', 'last_update']:
            if field in data and data[field]:
                is_valid, normalized, error = self.date_validator.validate_and_normalize(data[field])
                if is_valid:
                    validated_data[field] = normalized
                else:
                    self.warnings.append(f"{field}: {error}")
        
        # URLs (optional)
        for field in ['website', 'source_url', 'report_url']:
            if field in data and data[field]:
                is_valid, normalized, error = self.url_validator.validate_and_normalize(data[field])
                if is_valid:
                    validated_data[field] = normalized
                else:
                    self.warnings.append(f"{field}: {error}")
        
        # Weitere Felder ohne spezielle Validierung
        additional_fields = [
            'owner', 'operator', 'country', 'region', 'province',
            'description', 'notes', 'employees', 'depth', 'area',
            'reserves', 'resources', 'grade', 'recovery_rate',
            'processing_capacity', 'infrastructure'
        ]
        
        for field in additional_fields:
            if field in data and data[field]:
                validated_data[field] = self._clean_value(data[field])
        
        # Metadaten
        validated_data['validation_timestamp'] = datetime.now().isoformat()
        validated_data['validation_errors'] = self.errors
        validated_data['validation_warnings'] = self.warnings
        
        return validated_data
    
    def validate_search_result(self, result: Dict[str, Any]) -> bool:
        """Validiert ein einzelnes Suchergebnis"""
        # Minimal-Validierung für Suchergebnisse
        required_fields = ['title', 'url']
        
        for field in required_fields:
            if field not in result or not result[field]:
                self.logger.warning(f"Suchergebnis fehlt Pflichtfeld: {field}")
                return False
        
        # URL-Validierung
        is_valid, error = self.url_validator.validate(result['url'])
        if not is_valid:
            self.logger.warning(f"Ungültige URL in Suchergebnis: {error}")
            return False
        
        return True
    
    def bulk_validate(self, data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validiert eine Liste von Minendaten"""
        validated_list = []
        
        for idx, data in enumerate(data_list):
            try:
                validated = self.validate_mine_data(data)
                if not self.errors:
                    validated_list.append(validated)
                else:
                    self.logger.error(f"Validierung fehlgeschlagen für Eintrag {idx}: {self.errors}")
            except Exception as e:
                self.logger.error(f"Validierungsfehler bei Eintrag {idx}: {str(e)}")
        
        return validated_list
    
    def _clean_string(self, value: Any) -> str:
        """Bereinigt String-Werte"""
        if value is None:
            return ''
        
        # Konvertiere zu String
        value_str = str(value).strip()
        
        # Entferne mehrfache Leerzeichen
        import re
        value_str = re.sub(r'\s+', ' ', value_str)
        
        return value_str
    
    def _clean_value(self, value: Any) -> Any:
        """Bereinigt beliebige Werte"""
        if isinstance(value, str):
            return self._clean_string(value)
        elif isinstance(value, (list, tuple)):
            return [self._clean_value(v) for v in value]
        elif isinstance(value, dict):
            return {k: self._clean_value(v) for k, v in value.items()}
        else:
            return value
    
    def get_validation_report(self) -> Dict[str, Any]:
        """Gibt einen Validierungsbericht zurück"""
        return {
            'timestamp': datetime.now().isoformat(),
            'errors': self.errors,
            'warnings': self.warnings,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings),
            'is_valid': len(self.errors) == 0
        }
