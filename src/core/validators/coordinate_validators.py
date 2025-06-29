"""
Author: rahn
Datum: 27.06.2025
Version: 1.0
Beschreibung: Koordinaten-Validierung
"""

import re
from typing import Any, Optional, Tuple
from .base import BaseValidator
from ..logger import get_logger

logger = get_logger(__name__)


class CoordinateValidator(BaseValidator):
    """Validierung für Koordinaten"""
    
    def validate_coordinates(self, coords: Any, region: Optional[str] = None) -> Optional[Tuple[float, float]]:
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
    
    def parse_coordinate_string(self, coord_str: str) -> Optional[Tuple[float, float]]:
        """Parst verschiedene Koordinatenformate aus String"""
        self.reset_errors()
        return self.validate_coordinates(coord_str)