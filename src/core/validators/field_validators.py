"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Feld-spezifische Validatoren
"""

import re
from typing import Any, Tuple, Optional, Union
from datetime import datetime
from urllib.parse import urlparse

from .base import BaseValidator
from .constants import ValidatorConstants


class LocationValidator(BaseValidator):
    """Validiert Standort-Angaben"""
    
    def validate(self, value: Any) -> Tuple[bool, Optional[str]]:
        """Validiert Standort"""
        if not value:
            return False, "Standort darf nicht leer sein"
        
        value_str = str(value).strip()
        
        if len(value_str) < 2:
            return False, "Standort zu kurz"
        
        if len(value_str) > 500:
            return False, "Standort zu lang"
        
        # Prüfe auf verdächtige Zeichen
        if re.search(r'[<>{}|\[\]]', value_str):
            return False, "Ungültige Zeichen im Standort"
        
        return True, None
    
    def normalize(self, value: Any) -> str:
        """Normalisiert Standort"""
        cleaned = self._clean_string(str(value))
        
        # Titel-Case für Ortsnamen
        parts = cleaned.split(',')
        normalized_parts = []
        
        for part in parts:
            # Behalte Akronyme (z.B. USA, UK)
            if part.strip().isupper() and len(part.strip()) <= 4:
                normalized_parts.append(part.strip())
            else:
                # Titel-Case für normale Wörter
                words = part.strip().split()
                normalized_words = []
                for word in words:
                    if word.lower() in ['of', 'de', 'la', 'le', 'and']:
                        normalized_words.append(word.lower())
                    else:
                        normalized_words.append(word.title())
                normalized_parts.append(' '.join(normalized_words))
        
        return ', '.join(normalized_parts)


class CoordinateValidator(BaseValidator):
    """Validiert GPS-Koordinaten"""
    
    def validate(self, value: Any) -> Tuple[bool, Optional[str]]:
        """Validiert Koordinaten"""
        if not value:
            return True, None  # Koordinaten sind optional
        
        # Unterstütze verschiedene Formate
        if isinstance(value, (list, tuple)) and len(value) == 2:
            lat, lon = value
        elif isinstance(value, dict) and 'lat' in value and 'lon' in value:
            lat = value['lat']
            lon = value['lon']
        elif isinstance(value, str):
            # Versuche String zu parsen
            parts = re.split(r'[,\s]+', value.strip())
            if len(parts) == 2:
                try:
                    lat = float(parts[0])
                    lon = float(parts[1])
                except ValueError:
                    return False, "Ungültiges Koordinatenformat"
            else:
                return False, "Koordinaten müssen aus Latitude und Longitude bestehen"
        else:
            return False, "Ungültiges Koordinatenformat"
        
        # Validiere Bereiche
        try:
            lat_float = float(lat)
            lon_float = float(lon)
            
            if not -90 <= lat_float <= 90:
                return False, f"Latitude muss zwischen -90 und 90 liegen (ist: {lat_float})"
            
            if not -180 <= lon_float <= 180:
                return False, f"Longitude muss zwischen -180 und 180 liegen (ist: {lon_float})"
            
            return True, None
            
        except (ValueError, TypeError):
            return False, "Koordinaten müssen numerisch sein"
    
    def normalize(self, value: Any) -> Optional[dict]:
        """Normalisiert Koordinaten zu Dict"""
        if not value:
            return None
        
        is_valid, error = self.validate(value)
        if not is_valid:
            return None
        
        # Parse zu lat/lon
        if isinstance(value, (list, tuple)) and len(value) == 2:
            lat, lon = value
        elif isinstance(value, dict) and 'lat' in value and 'lon' in value:
            lat = value['lat']
            lon = value['lon']
        elif isinstance(value, str):
            parts = re.split(r'[,\s]+', value.strip())
            lat = float(parts[0])
            lon = float(parts[1])
        else:
            return None
        
        return {
            'lat': round(float(lat), 6),
            'lon': round(float(lon), 6)
        }


class DateValidator(BaseValidator):
    """Validiert Datumsangaben"""
    
    # Unterstützte Formate
    DATE_FORMATS = [
        '%Y-%m-%d',
        '%d.%m.%Y',
        '%d/%m/%Y',
        '%m/%d/%Y',
        '%Y/%m/%d',
        '%d-%m-%Y',
        '%Y-%m-%d %H:%M:%S',
        '%d.%m.%Y %H:%M:%S',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%SZ',
        '%Y-%m-%dT%H:%M:%S.%f',
        '%Y-%m-%dT%H:%M:%S.%fZ'
    ]
    
    def validate(self, value: Any) -> Tuple[bool, Optional[str]]:
        """Validiert Datum"""
        if not value:
            return True, None  # Datum ist optional
        
        if isinstance(value, datetime):
            return True, None
        
        if isinstance(value, str):
            # Versuche verschiedene Formate
            for date_format in self.DATE_FORMATS:
                try:
                    datetime.strptime(value.strip(), date_format)
                    return True, None
                except ValueError:
                    continue
            
            return False, "Ungültiges Datumsformat"
        
        return False, "Datum muss String oder datetime sein"
    
    def normalize(self, value: Any) -> Optional[str]:
        """Normalisiert Datum zu ISO-Format"""
        if not value:
            return None
        
        if isinstance(value, datetime):
            return value.isoformat()
        
        if isinstance(value, str):
            # Parse und konvertiere zu ISO
            for date_format in self.DATE_FORMATS:
                try:
                    dt = datetime.strptime(value.strip(), date_format)
                    return dt.isoformat()
                except ValueError:
                    continue
        
        return None


class URLValidator(BaseValidator):
    """Validiert URLs"""
    
    def validate(self, value: Any) -> Tuple[bool, Optional[str]]:
        """Validiert URL"""
        if not value:
            return True, None  # URL ist optional
        
        if not isinstance(value, str):
            return False, "URL muss ein String sein"
        
        value = value.strip()
        
        # Einfache URL-Validierung
        if not value.startswith(('http://', 'https://', 'ftp://', 'www.')):
            return False, "URL muss mit http://, https://, ftp:// oder www. beginnen"
        
        # Parse URL
        try:
            result = urlparse(value)
            if not result.netloc and not result.path:
                return False, "Ungültige URL-Struktur"
            
            # Prüfe auf verdächtige Zeichen
            if any(char in value for char in ['<', '>', '"', '{', '}', '|', '\\', '^', ' ']):
                return False, "URL enthält ungültige Zeichen"
            
            return True, None
            
        except Exception:
            return False, "URL konnte nicht geparst werden"
    
    def normalize(self, value: Any) -> Optional[str]:
        """Normalisiert URL"""
        if not value:
            return None
        
        value = str(value).strip()
        
        # Füge Protokoll hinzu wenn fehlt
        if value.startswith('www.'):
            value = 'https://' + value
        
        # Entferne trailing slash
        if value.endswith('/'):
            value = value[:-1]
        
        return value


class EmailValidator(BaseValidator):
    """Validiert E-Mail-Adressen"""
    
    EMAIL_REGEX = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    def validate(self, value: Any) -> Tuple[bool, Optional[str]]:
        """Validiert E-Mail"""
        if not value:
            return True, None  # E-Mail ist optional
        
        if not isinstance(value, str):
            return False, "E-Mail muss ein String sein"
        
        value = value.strip()
        
        if not self.EMAIL_REGEX.match(value):
            return False, "Ungültiges E-Mail-Format"
        
        # Prüfe auf verdächtige Patterns
        if value.count('@') != 1:
            return False, "E-Mail darf nur ein @ enthalten"
        
        if '..' in value:
            return False, "E-Mail darf keine doppelten Punkte enthalten"
        
        return True, None
    
    def normalize(self, value: Any) -> Optional[str]:
        """Normalisiert E-Mail"""
        if not value:
            return None
        
        return str(value).strip().lower()