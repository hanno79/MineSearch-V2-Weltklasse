"""
Author: rahn
Datum: 08.07.2025
Version: 1.0
Beschreibung: Zentraler Validation Service für konsistente Datenvalidierung
"""

import re
import logging
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime

from config import CSV_COLUMNS
from extraction_validators import (
    is_placeholder_value, validate_coordinate,
    validate_restoration_cost, validate_year, validate_area
)

logger = logging.getLogger(__name__)


class ValidationService:
    """
    Zentraler Service für Datenvalidierung
    
    Stellt einheitliche Validierung für alle Provider sicher
    """
    
    def __init__(self):
        # Ungültige Betreiber-Namen
        self.invalid_operators = [
            'koordinaten', 'coordinates', 'coords', 'koordinate', 
            'dhilmar', 'n/a', 'unknown', 'unbekannt', '-'
        ]
        
        # Verdächtige Restaurationskosten-Muster
        self.suspicious_restoration_patterns = [
            r'^\$?1\.0+\s*(million|mio|m)?',  # $1.0 million
            r'^\$?2\.0+\s*(million|mio|m)?',  # $2.0 million
            r'^\$?10{3,}\.0+\s*(million|mio|m)?',  # $10000.0 million
            r'^\$?0\.0+\s*(million|mio|m)?',  # $0.0 million
        ]
        
        # Kritische Felder für Qualitätsbewertung
        self.critical_fields = [
            'Eigentümer', 'Betreiber', 'Restaurationskosten',
            'x-Koordinate', 'y-Koordinate', 'Aktivitätsstatus'
        ]
    
    def validate_mine_data(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        """
        Validiere komplette Minendaten
        
        Args:
            data: Dictionary mit Minendaten
            
        Returns:
            Tuple aus (bereinigten Daten, Liste von Validierungsfehlern)
        """
        cleaned_data = data.copy()
        errors = []
        
        # Validiere jedes Feld
        for field, value in data.items():
            if not value or not str(value).strip():
                continue
            
            # Betreiber validieren
            if field == 'Betreiber':
                is_valid, cleaned = self.validate_operator(str(value))
                if not is_valid:
                    errors.append(f"Ungültiger Betreiber: {value}")
                    cleaned_data[field] = "X"  # Nicht gefunden markieren
                else:
                    cleaned_data[field] = cleaned
            
            # Restaurationskosten validieren
            elif field == 'Restaurationskosten':
                is_valid, cleaned = self.validate_restoration_cost(str(value))
                if not is_valid:
                    errors.append(f"Verdächtige Restaurationskosten: {value}")
                    cleaned_data[field] = "X"  # Nicht gefunden markieren
                else:
                    cleaned_data[field] = cleaned
            
            # Koordinaten validieren
            elif field in ['x-Koordinate', 'y-Koordinate']:
                coord_type = 'lon' if field == 'x-Koordinate' else 'lat'
                is_valid = validate_coordinate(str(value), coord_type)
                if not is_valid:
                    errors.append(f"Ungültige {field}: {value}")
                    cleaned_data[field] = "X"  # Nicht gefunden markieren
            
            # Jahr validieren
            elif 'jahr' in field.lower() or 'datum' in field.lower():
                is_valid = validate_year(str(value))
                if not is_valid and value:
                    errors.append(f"Ungültiges Jahr in {field}: {value}")
            
            # Platzhalter-Check für alle Felder
            if is_placeholder_value(str(value), field):
                errors.append(f"Platzhalter-Wert in {field}: {value}")
                cleaned_data[field] = "X"  # Nicht gefunden markieren
        
        return cleaned_data, errors
    
    def validate_operator(self, operator: str) -> Tuple[bool, str]:
        """
        Validiere Betreiber-Namen
        
        Args:
            operator: Betreiber-Name
            
        Returns:
            Tuple aus (ist_valide, bereinigter_wert)
        """
        if not operator or not operator.strip():
            return False, ""
        
        cleaned = operator.strip()
        
        # Prüfe auf ungültige Werte
        if cleaned.lower() in self.invalid_operators:
            logger.warning(f"[VALIDATION] Ungültiger Betreiber abgelehnt: {operator}")
            return False, ""
        
        # Prüfe auf Koordinaten-Muster
        if 'koordinaten:' in cleaned.lower() or re.match(r'^-?\d+\.?\d*,?\s*-?\d+\.?\d*$', cleaned):
            logger.warning(f"[VALIDATION] Koordinaten als Betreiber erkannt: {operator}")
            return False, ""
        
        # Mindestlänge
        if len(cleaned) < 2:
            return False, ""
        
        return True, cleaned
    
    def validate_restoration_cost(self, cost: str) -> Tuple[bool, str]:
        """
        Validiere Restaurationskosten
        
        Args:
            cost: Restaurationskosten-String
            
        Returns:
            Tuple aus (ist_valide, bereinigter_wert)
        """
        if not cost or not cost.strip():
            return True, ""  # Leere Werte sind OK
        
        cleaned = cost.strip()
        
        # Verwende existierende Validierung
        is_valid = validate_restoration_cost(cleaned)
        if not is_valid:
            return False, ""
        
        # Zusätzliche Prüfung auf verdächtige Muster
        for pattern in self.suspicious_restoration_patterns:
            if re.match(pattern, cleaned, re.IGNORECASE):
                logger.warning(f"[VALIDATION] Verdächtige Restaurationskosten: {cost}")
                return False, ""
        
        # Prüfe auf zu runde Zahlen (1.0, 2.0, 10.0 etc.)
        if re.search(r'\b\d+\.0+\b', cleaned) and 'million' in cleaned.lower():
            # Erlaubt sind nur realistische runde Zahlen
            match = re.search(r'(\d+)\.0+', cleaned)
            if match:
                number = int(match.group(1))
                # Verdächtige runde Zahlen: 1, 2, 10, 100, 1000, 10000
                if number in [1, 2, 10, 100, 1000, 10000]:
                    logger.warning(f"[VALIDATION] Zu runde Restaurationskosten: {cost}")
                    return False, ""
        
        return True, cleaned
    
    def remove_placeholder_values(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Entferne alle Platzhalter-Werte aus den Daten
        
        Args:
            data: Dictionary mit Daten
            
        Returns:
            Bereinigtes Dictionary
        """
        cleaned = {}
        
        for field, value in data.items():
            if value and not is_placeholder_value(str(value), field):
                cleaned[field] = value
            else:
                # FALLBACK: X-Marker für nicht-valide Werte - REGEL 10 KONFORM
                cleaned[field] = "X"  # Fallback bei Platzhalter-/invaliden Werten
        
        return cleaned
    
    def get_data_quality_score(self, data: Dict[str, Any]) -> float:
        """
        Berechne Datenqualitäts-Score (0.0 - 1.0)
        
        Args:
            data: Dictionary mit validierten Daten
            
        Returns:
            Qualitäts-Score zwischen 0.0 und 1.0
        """
        if not data:
            return 0.0
        
        # Zähle gefüllte Felder
        total_fields = len(CSV_COLUMNS)
        filled_fields = sum(1 for col in CSV_COLUMNS if data.get(col) and str(data[col]).strip())
        
        # Basis-Score: Anteil gefüllter Felder
        base_score = filled_fields / total_fields if total_fields > 0 else 0.0
        
        # Bonus für kritische Felder
        critical_bonus = 0.0
        for field in self.critical_fields:
            if data.get(field) and str(data[field]).strip():
                critical_bonus += 0.05  # 5% Bonus pro kritischem Feld
        
        # Kombinierter Score (max 1.0)
        total_score = min(1.0, base_score + critical_bonus)
        
        # Penalty für verdächtige Werte
        _, errors = self.validate_mine_data(data)
        if errors:
            penalty = len(errors) * 0.05  # 5% Abzug pro Fehler
            total_score = max(0.0, total_score - penalty)
        
        return round(total_score, 2)
    
    def get_field_confidence(self, value: str, field: str, sources: List[str]) -> float:
        """
        Berechne Konfidenz für einen einzelnen Feldwert
        
        Args:
            value: Feldwert
            field: Feldname
            sources: Liste von Quellen die diesen Wert gefunden haben
            
        Returns:
            Konfidenz-Score zwischen 0.0 und 1.0
        """
        if not value or not str(value).strip():
            return 0.0
        
        # Basis-Konfidenz basierend auf Anzahl Quellen
        base_confidence = min(1.0, len(sources) * 0.25)  # 25% pro Quelle, max 100%
        
        # Validierung des Werts
        if field == 'Betreiber':
            is_valid, _ = self.validate_operator(value)
            if not is_valid:
                return 0.0
        elif field == 'Restaurationskosten':
            is_valid, _ = self.validate_restoration_cost(value)
            if not is_valid:
                return 0.0
        
        # Platzhalter-Check
        if is_placeholder_value(value, field):
            return 0.0
        
        return base_confidence
    
    def create_validation_report(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Erstelle detaillierten Validierungsbericht
        
        Args:
            data: Zu validierende Daten
            
        Returns:
            Dictionary mit Validierungsergebnissen
        """
        cleaned_data, errors = self.validate_mine_data(data)
        quality_score = self.get_data_quality_score(cleaned_data)
        
        # Analysiere welche Felder problematisch sind
        field_analysis = {}
        for field in CSV_COLUMNS:
            value = data.get(field, "")
            if value:
                field_analysis[field] = {
                    'has_value': True,
                    'is_valid': field not in [e.split(':')[0] for e in errors if ':' in e],
                    'original_value': value,
                    'cleaned_value': cleaned_data.get(field, "")
                }
            else:
                field_analysis[field] = {
                    'has_value': False,
                    'is_valid': True,
                    'original_value': "",
                    'cleaned_value': ""
                }
        
        return {
            'quality_score': quality_score,
            'total_fields': len(CSV_COLUMNS),
            'filled_fields': sum(1 for f in field_analysis.values() if f['has_value']),
            'valid_fields': sum(1 for f in field_analysis.values() if f['is_valid'] and f['has_value']),
            'errors': errors,
            'field_analysis': field_analysis,
            'cleaned_data': cleaned_data,
            'timestamp': datetime.now().isoformat()
        }


# Singleton-Instanz
validation_service = ValidationService()