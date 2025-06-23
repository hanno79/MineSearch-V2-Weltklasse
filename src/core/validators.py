"""
Author: rahn
Datum: 16.06.2025
Version: 1.0
Beschreibung: Validierungsfunktionen für Minendaten
"""

import re
from typing import Any, Dict, List, Optional, Union, Tuple
from datetime import datetime
from urllib.parse import urlparse

from .logger import get_logger


logger = get_logger(__name__)


class ValidationError(Exception):
    """Basis-Exception für Validierungsfehler"""
    pass


class DataValidator:
    """Hauptklasse für Datenvalidierung mit erweiterter Normalisierung"""
    
    # Währungscodes
    VALID_CURRENCIES = ['CAD', 'USD', 'EUR', 'GBP', 'AUD', 'CHF', 'JPY', 'CNY']
    
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
        self.errors = []
        self.warnings = []
    
    def validate_mine_data(self, data: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
        """Validiert kompletten Minendatensatz"""
        self.errors = []
        self.warnings = []
        
        # Pflichtfelder prüfen
        required_fields = ['name', 'betreiber', 'region']
        for field in required_fields:
            if field not in data or not data[field]:
                self.errors.append(f"Pflichtfeld '{field}' fehlt")
        
        # Feldspezifische Validierungen
        if 'name' in data:
            self._validate_name(data['name'])
        
        if 'koordinaten' in data:
            self._validate_coordinates(data['koordinaten'])
        
        if 'sanierungskosten' in data:
            self._validate_currency_amount(data['sanierungskosten'], 'sanierungskosten')
        
        if 'umweltkosten' in data:
            self._validate_currency_amount(data['umweltkosten'], 'umweltkosten')
        
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
    
    def _validate_coordinates(self, coords: Any, region: Optional[str] = None) -> Optional[Tuple[float, float]]:
        """Validiert und normalisiert Koordinaten"""
        lat, lon = None, None
        
        if isinstance(coords, str):
            # Verschiedene Koordinatenformate unterstützen
            patterns = [
                r'(-?\d+\.?\d*)[,\s]+(-?\d+\.?\d*)',  # Dezimal
                r'(\d+)°\s*(\d+)′\s*(\d+(?:\.\d+)?)″?\s*([NS])\s*[,;]?\s*(\d+)°\s*(\d+)′\s*(\d+(?:\.\d+)?)″?\s*([EW])',  # DMS
                r'latitude[:\s]*([-]?\d+\.?\d*)[,\s]+longitude[:\s]*([-]?\d+\.?\d*)'  # Mit Labels
            ]
            
            for pattern in patterns:
                match = re.search(pattern, coords, re.IGNORECASE)
                if match:
                    if len(match.groups()) == 2:
                        lat, lon = float(match.group(1)), float(match.group(2))
                    elif len(match.groups()) == 8:  # DMS Format
                        lat = self._dms_to_decimal(
                            int(match.group(1)), int(match.group(2)), 
                            float(match.group(3)), match.group(4)
                        )
                        lon = self._dms_to_decimal(
                            int(match.group(5)), int(match.group(6)), 
                            float(match.group(7)), match.group(8)
                        )
                    break
                    
            if lat is None:
                self.errors.append("Koordinaten im falschen Format")
                return None
                
        elif isinstance(coords, (list, tuple)) and len(coords) == 2:
            try:
                lat, lon = float(coords[0]), float(coords[1])
            except (ValueError, TypeError):
                self.errors.append("Koordinaten müssen Zahlen sein")
                return None
        elif isinstance(coords, dict) and 'latitude' in coords and 'longitude' in coords:
            try:
                lat = float(coords['latitude'])
                lon = float(coords['longitude'])
            except (ValueError, TypeError):
                self.errors.append("Latitude/Longitude müssen Zahlen sein")
                return None
        else:
            self.errors.append("Ungültiges Koordinatenformat")
            return None
        
        # Validiere Bereiche
        if lat is None or lon is None:
            self.errors.append("Koordinaten konnten nicht extrahiert werden")
            return None
            
        if not -90 <= lat <= 90:
            self.errors.append(f"Ungültige Latitude: {lat} (muss zwischen -90 und 90 liegen)")
            return None
        
        if not -180 <= lon <= 180:
            self.errors.append(f"Ungültige Longitude: {lon} (muss zwischen -180 und 180 liegen)")
            return None
        
        # Keine länderspezifische Validierung mehr - flexibel für alle Länder
            
        return (lat, lon)
    
    def _dms_to_decimal(self, degrees: int, minutes: int, seconds: float, direction: str) -> float:
        """Konvertiert Grad/Minuten/Sekunden zu Dezimalgrad"""
        decimal = degrees + minutes/60 + seconds/3600
        if direction in ['S', 'W']:
            decimal = -decimal
        return decimal
    
    def _validate_currency_amount(self, amount: Any, field_name: str) -> None:
        """Validiert Währungsbeträge"""
        if amount is None or amount == "nichts gefunden":
            return
        
        # String zu Zahl konvertieren
        if isinstance(amount, str):
            # Entferne Währungssymbole und Formatierung
            cleaned = re.sub(r'[^\d,.-]', '', amount)
            cleaned = cleaned.replace(',', '.')
            
            try:
                numeric_amount = float(cleaned)
            except ValueError:
                self.errors.append(f"{field_name}: Ungültiger Betrag '{amount}'")
                return
                
            # Prüfe auf Währungscode
            currency_match = re.search(r'\b(' + '|'.join(self.VALID_CURRENCIES) + r')\b', amount, re.IGNORECASE)
            if not currency_match:
                self.warnings.append(f"{field_name}: Keine Währung angegeben")
        
        elif isinstance(amount, (int, float)):
            numeric_amount = float(amount)
        else:
            self.errors.append(f"{field_name}: Muss Zahl oder Text sein")
            return
        
        # Validiere Betragshöhe
        if numeric_amount < 0:
            self.errors.append(f"{field_name}: Betrag darf nicht negativ sein")
        
        if numeric_amount > 10_000_000_000:  # 10 Milliarden
            self.warnings.append(f"{field_name}: Ungewöhnlich hoher Betrag ({numeric_amount:,.0f})")
    
    def normalize_currency_amount(self, amount: Any, target_currency: str = 'CAD') -> Optional[Dict[str, Any]]:
        """Normalisiert Währungsbeträge zu Zielwährung"""
        if amount is None or amount == "nichts gefunden":
            return None
            
        # Einfache Wechselkurse (sollten eigentlich dynamisch sein)
        exchange_rates = {
            'USD': {'CAD': 1.35, 'EUR': 0.92},
            'CAD': {'USD': 0.74, 'EUR': 0.68},
            'EUR': {'USD': 1.09, 'CAD': 1.47}
        }
        
        # Parse Betrag
        if isinstance(amount, str):
            # Extrahiere Zahl und Währung
            amount_match = re.search(r'([\d,]+(?:\.\d+)?)\s*(?:million|M)?\s*([A-Z]{3})?', amount, re.IGNORECASE)
            if not amount_match:
                return None
                
            value = float(amount_match.group(1).replace(',', ''))
            
            # Prüfe auf Millionen/Milliarden
            if 'million' in amount.lower() or ' M' in amount:
                value *= 1_000_000
            elif 'billion' in amount.lower() or ' B' in amount:
                value *= 1_000_000_000
                
            currency = amount_match.group(2) or 'CAD'  # Default CAD
            
        elif isinstance(amount, (int, float)):
            value = float(amount)
            currency = 'CAD'  # Default
        else:
            return None
            
        # Konvertiere zur Zielwährung
        if currency != target_currency and currency in exchange_rates:
            if target_currency in exchange_rates[currency]:
                value *= exchange_rates[currency][target_currency]
                
        return {
            'value': value,
            'currency': target_currency,
            'original_currency': currency,
            'formatted': f"${value:,.2f} {target_currency}"
        }
    
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
    
    def validate_search_result(self, result: Dict[str, Any]) -> bool:
        """Validiert einzelnes Suchergebnis"""
        required_fields = ['field_name', 'value', 'source', 'agent_name']
        
        for field in required_fields:
            if field not in result:
                logger.error(f"Suchergebnis fehlt Pflichtfeld: {field}")
                return False
        
        # Wert darf nicht leer sein
        if result['value'] is None or result['value'] == '':
            logger.warning(f"Leerer Wert für Feld: {result['field_name']}")
            return False
        
        return True
    
    def clean_numeric_value(self, value: Any) -> Optional[float]:
        """Bereinigt und konvertiert numerische Werte"""
        if value is None or value == "nichts gefunden":
            return None
        
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, str):
            # Entferne Währungssymbole, Leerzeichen, etc.
            cleaned = re.sub(r'[^\d,.-]', '', value)
            
            # Ersetze Komma durch Punkt
            cleaned = cleaned.replace(',', '.')
            
            try:
                return float(cleaned)
            except ValueError:
                logger.warning(f"Konnte Wert nicht zu Zahl konvertieren: '{value}'")
                return None
        
        return None
    
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
    
    def extract_currency(self, amount_str: str) -> Tuple[Optional[float], Optional[str]]:
        """Extrahiert Betrag und Währung aus String"""
        if not isinstance(amount_str, str):
            return None, None
        
        # Suche nach Währung
        currency = None
        for curr in self.VALID_CURRENCIES:
            if curr in amount_str.upper():
                currency = curr
                break
        
        # Extrahiere numerischen Wert
        amount = self.clean_numeric_value(amount_str)
        
        return amount, currency


# Singleton-Instanz
_validator = None


def get_validator() -> DataValidator:
    """Factory-Funktion für DataValidator"""
    global _validator
    if _validator is None:
        _validator = DataValidator()
    return _validator