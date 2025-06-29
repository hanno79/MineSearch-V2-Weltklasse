"""
Author: rahn
Datum: 27.06.2025
Version: 1.0
Beschreibung: Validierungen für Minendaten
"""

import re
from typing import Any, Dict, List, Tuple
from urllib.parse import urlparse
from .base import BaseValidator
from .coordinate_validators import CoordinateValidator
from .currency_validators import CurrencyValidator
from ..logger import get_logger

logger = get_logger(__name__)


class MineValidator(BaseValidator):
    """Validierung für Minendaten"""
    
    # Gültige Minenstatus
    VALID_MINE_STATUS = [
        'aktiv', 'active', 'in betrieb', 'operating',
        'inaktiv', 'inactive', 'geschlossen', 'closed',
        'stillgelegt', 'suspended', 'pausiert', 'on hold',
        'in entwicklung', 'development', 'exploration',
        'sanierung', 'rehabilitation', 'restauration'
    ]
    
    # Status-Normalisierung
    STATUS_NORMALIZATION = {
        'active': 'aktiv',
        'operating': 'aktiv',
        'in betrieb': 'aktiv',
        'producing': 'aktiv',
        'operational': 'aktiv',
        'inactive': 'inaktiv',
        'closed': 'inaktiv',
        'geschlossen': 'inaktiv',
        'shut down': 'inaktiv',
        'abandoned': 'inaktiv',
        'suspended': 'pausiert',
        'on hold': 'pausiert',
        'care and maintenance': 'pausiert',
        'development': 'entwicklung',
        'construction': 'entwicklung',
        'exploration': 'exploration'
    }
    
    # Gültige Minentypen
    VALID_MINE_TYPES = [
        'tagebau', 'open pit', 'surface',
        'untertagebau', 'underground', 'subsurface',
        'kombiniert', 'combined', 'hybrid',
        'alluvial', 'placer',
        'lösung', 'solution', 'in-situ'
    ]
    
    # Gültige Rohstoffe
    VALID_COMMODITIES = [
        'gold', 'or', 'silver', 'argent', 'copper', 'cuivre', 'kupfer',
        'zinc', 'lead', 'plomb', 'blei', 'nickel', 'cobalt', 'kobalt',
        'iron', 'fer', 'eisen', 'uranium', 'lithium', 'coal', 'charbon', 'kohle',
        'diamond', 'diamant', 'platinum', 'platin', 'palladium',
        'molybdenum', 'molybdän', 'tungsten', 'wolfram', 'tin', 'étain', 'zinn',
        'aluminium', 'aluminum', 'bauxite', 'chromium', 'chrome', 'chrom',
        'manganese', 'mangan', 'titanium', 'titan', 'vanadium', 'graphite', 'graphit',
        'rare earth', 'terres rares', 'seltene erden', 'phosphate', 'phosphat',
        'potash', 'potasse', 'kali', 'salt', 'sel', 'salz', 'limestone', 'calcaire', 'kalkstein'
    ]
    
    # Rohstofftypen mit Normalisierung
    COMMODITY_NORMALIZATION = {
        'gold': 'Gold', 'or': 'Gold',
        'silver': 'Silber', 'argent': 'Silber',
        'copper': 'Kupfer', 'cuivre': 'Kupfer',
        'nickel': 'Nickel',
        'iron': 'Eisen', 'fer': 'Eisen',
        'zinc': 'Zink',
        'lead': 'Blei', 'plomb': 'Blei',
        'diamond': 'Diamant', 'diamonds': 'Diamant',
        'coal': 'Kohle', 'charbon': 'Kohle',
        'uranium': 'Uran',
        'lithium': 'Lithium',
        'cobalt': 'Kobalt',
        'platinum': 'Platin',
        'rare earth': 'Seltene Erden', 'terres rares': 'Seltene Erden'
    }
    
    def __init__(self):
        super().__init__()
        self.coordinate_validator = CoordinateValidator()
        self.currency_validator = CurrencyValidator()
    
    def validate_mine_data(self, data: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
        """Validiert kompletten Minendatensatz"""
        self.reset_errors()
        
        # Pflichtfelder prüfen
        required_fields = ['name', 'betreiber', 'region']
        for field in required_fields:
            if field not in data or not data[field]:
                self.errors.append(f"Pflichtfeld '{field}' fehlt")
        
        # Feldspezifische Validierungen
        if 'name' in data:
            self._validate_name(data['name'])
        
        if 'koordinaten' in data:
            coords_result = self.coordinate_validator.validate_coordinates(data['koordinaten'])
            if coords_result is None:
                self.errors.extend(self.coordinate_validator.errors)
            self.warnings.extend(self.coordinate_validator.warnings)
        
        if 'sanierungskosten' in data:
            self.currency_validator.validate_currency_amount(data['sanierungskosten'], 'sanierungskosten')
            self.errors.extend(self.currency_validator.errors)
            self.warnings.extend(self.currency_validator.warnings)
            self.currency_validator.reset_errors()
        
        if 'umweltkosten' in data:
            self.currency_validator.validate_currency_amount(data['umweltkosten'], 'umweltkosten')
            self.errors.extend(self.currency_validator.errors)
            self.warnings.extend(self.currency_validator.warnings)
            self.currency_validator.reset_errors()
        
        if 'aktivitaetsstatus' in data:
            self._validate_status(data['aktivitaetsstatus'])
        
        if 'minentyp' in data:
            self._validate_mine_type(data['minentyp'])
        
        if 'rohstofftyp' in data:
            self._validate_commodities(data['rohstofftyp'])
        
        if 'website' in data:
            self._validate_url(data['website'])
        
        if 'flaeche' in data:
            self._validate_area(data['flaeche'])
        
        # Logische Validierungen
        self._validate_logical_consistency(data)
        
        is_valid = len(self.errors) == 0
        return is_valid, self.errors, self.warnings
    
    def _validate_name(self, name: Any) -> None:
        """Validiert Minennamen"""
        if not isinstance(name, str):
            self.errors.append(f"Minenname muss Text sein, ist aber: {type(name).__name__}")
            return
        
        if len(name) < 2:
            self.errors.append("Minenname zu kurz (min. 2 Zeichen)")
        
        if len(name) > 200:
            self.errors.append("Minenname zu lang (max. 200 Zeichen)")
        
        # Warnung bei verdächtigen Zeichen
        if re.search(r'[<>{}\\]', name):
            self.warnings.append("Minenname enthält ungewöhnliche Zeichen")
    
    def _validate_status(self, status: Any) -> None:
        """Validiert Minenstatus"""
        if not isinstance(status, str):
            self.errors.append(f"Status muss Text sein, ist aber: {type(status).__name__}")
            return
        
        status_lower = status.lower().strip()
        
        if not any(valid in status_lower for valid in self.VALID_MINE_STATUS):
            self.warnings.append(f"Unbekannter Minenstatus: '{status}'")
    
    def _validate_mine_type(self, mine_type: Any) -> None:
        """Validiert Minentyp"""
        if not isinstance(mine_type, str):
            self.errors.append(f"Minentyp muss Text sein, ist aber: {type(mine_type).__name__}")
            return
        
        type_lower = mine_type.lower().strip()
        
        if not any(valid in type_lower for valid in self.VALID_MINE_TYPES):
            self.warnings.append(f"Unbekannter Minentyp: '{mine_type}'")
    
    def _validate_commodities(self, commodities: Any) -> None:
        """Validiert Rohstofftypen"""
        if not isinstance(commodities, str):
            self.errors.append(f"Rohstofftyp muss Text sein, ist aber: {type(commodities).__name__}")
            return
        
        commodities_lower = commodities.lower()
        
        # Prüfe ob mindestens ein gültiger Rohstoff enthalten ist
        found_valid = False
        for commodity in self.VALID_COMMODITIES:
            if commodity in commodities_lower:
                found_valid = True
                break
        
        if not found_valid:
            self.warnings.append(f"Keine bekannten Rohstoffe erkannt in: '{commodities}'")
    
    def _validate_url(self, url: Any) -> None:
        """Validiert URLs"""
        if not isinstance(url, str):
            self.errors.append(f"URL muss Text sein, ist aber: {type(url).__name__}")
            return
        
        # Füge Protokoll hinzu wenn fehlt
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        try:
            result = urlparse(url)
            if not all([result.scheme, result.netloc]):
                self.errors.append(f"Ungültige URL: '{url}'")
            
            # Warnung bei unverschlüsselten URLs
            if result.scheme == 'http':
                self.warnings.append("URL verwendet unverschlüsseltes HTTP")
                
        except Exception as e:
            self.errors.append(f"URL-Parsing-Fehler: {str(e)}")
    
    def _validate_area(self, area: Any) -> None:
        """Validiert Flächenangaben"""
        if area is None or area == "nichts gefunden":
            return
        
        # Versuche Zahl zu extrahieren
        if isinstance(area, str):
            # Suche nach Zahlen
            numbers = re.findall(r'\d+\.?\d*', area)
            if not numbers:
                self.errors.append(f"Keine Zahl in Flächenangabe gefunden: '{area}'")
                return
            
            try:
                numeric_area = float(numbers[0])
            except ValueError:
                self.errors.append(f"Ungültige Flächenangabe: '{area}'")
                return
                
            # Prüfe auf Einheit
            if not re.search(r'(km²|km2|hectare|ha|m²|m2|acre)', area, re.IGNORECASE):
                self.warnings.append("Keine Flächeneinheit angegeben")
        
        elif isinstance(area, (int, float)):
            numeric_area = float(area)
            self.warnings.append("Flächenangabe ohne Einheit")
        else:
            self.errors.append(f"Fläche muss Zahl oder Text sein, ist aber: {type(area).__name__}")
            return
        
        # Validiere Größe
        if numeric_area <= 0:
            self.errors.append("Fläche muss größer als 0 sein")
        
        if numeric_area > 100000:  # Annahme: km²
            self.warnings.append(f"Ungewöhnlich große Fläche: {numeric_area}")
    
    def _validate_logical_consistency(self, data: Dict[str, Any]) -> None:
        """Prüft logische Konsistenz der Daten"""
        
        # Inaktive Mine sollte keine aktuellen Produktionsdaten haben
        if data.get('aktivitaetsstatus'):
            status = data['aktivitaetsstatus'].lower()
            if any(s in status for s in ['geschlossen', 'closed', 'inaktiv', 'stillgelegt']):
                if data.get('jahresproduktion') and data['jahresproduktion'] != "nichts gefunden":
                    self.warnings.append("Inaktive Mine hat Produktionsdaten")
        
        # Sanierungskosten sollten bei aktiven Minen vorhanden sein
        if data.get('aktivitaetsstatus'):
            status = data['aktivitaetsstatus'].lower()
            if any(s in status for s in ['aktiv', 'active', 'betrieb', 'operating']):
                if not data.get('sanierungskosten') or data['sanierungskosten'] == "nichts gefunden":
                    self.warnings.append("Aktive Mine ohne Sanierungskosten-Angabe")
    
    def normalize_status(self, status: str) -> str:
        """Normalisiert Minenstatus zu Standardwerten"""
        if not isinstance(status, str):
            return "unbekannt"
        
        status_lower = status.lower().strip()
        
        # Nutze STATUS_NORMALIZATION Dictionary
        for key, value in self.STATUS_NORMALIZATION.items():
            if key in status_lower:
                return value
                
        return "unbekannt"
    
    def normalize_commodity(self, commodity: str) -> str:
        """Normalisiert Rohstoffnamen"""
        if not isinstance(commodity, str):
            return commodity
            
        commodity_lower = commodity.lower().strip()
        
        # Sammle alle gefundenen Rohstoffe
        found_commodities = []
        
        for key, normalized in self.COMMODITY_NORMALIZATION.items():
            if key in commodity_lower:
                if normalized not in found_commodities:
                    found_commodities.append(normalized)
        
        if found_commodities:
            return ", ".join(found_commodities)
        else:
            return commodity