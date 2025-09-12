"""
Author: rahn
Datum: 11.09.2025
Version: 1.0
Beschreibung: Core DataExtractor Klasse (aufgeteilt aus data_extraction.py)
"""

import re
import logging
from typing import Dict, List, Any, Optional
from minesearch.config import config, CSV_COLUMNS, FIELDS_WITHOUT_SOURCES
from minesearch.utils import clean_extracted_value, get_country_config
from minesearch.source_discovery import extract_sources_from_content

# Importiere neue Module
from minesearch.extraction_patterns import get_extraction_patterns, get_enhanced_coordinate_patterns
from minesearch.extraction_validators import (
    is_placeholder_value, validate_coordinate,
    validate_restoration_cost, validate_year, validate_area
)
from minesearch.extraction_processors import (
    process_restoration_costs, process_activity_status,
    split_country_region, find_region_from_content,
    process_sources, post_process_data, clean_field_value,
    is_template_or_dummy_value, extract_core_value,
    extract_restoration_cost_year
)
from minesearch.source_manager import SourceManager
from minesearch.field_name_blacklist import is_field_name_value
from minesearch.database.normalized_manager import NormalizedDatabaseManager

logger = logging.getLogger(__name__)


class DataExtractor:
    """Klasse für strukturierte Datenextraktion aus Mining-Suchergebnissen"""

    def __init__(self):
        self.patterns = get_extraction_patterns()
        self.coordinate_patterns = get_enhanced_coordinate_patterns()
        self.source_manager = SourceManager()
        self.normalized_db = NormalizedDatabaseManager()

    def _get_field_status_marker(self, field: str, activity_status: str) -> str:
        """
        CONDITIONAL-FIELDS-FIX 15.07.2025: Generiert aussagekräftige Status-Marker

        Args:
            field: Feldname
            activity_status: Aktivitätsstatus der Mine

        Returns:
            Status-Marker für das Feld
        """
        if not activity_status or activity_status.lower() in ['unknown', 'n/a', '']:
            return 'unknown_status'

        status_lower = activity_status.lower()

        # Aktive Minen - alle Felder relevant
        if status_lower in ['active', 'operating', 'production', 'in production']:
            return 'active_mine'

        # Inaktive/geschlossene Minen - nur historische Daten relevant
        elif status_lower in ['inactive', 'closed', 'abandoned', 'mothballed']:
            if field in ['annual_production', 'production_capacity', 'current_production']:
                return 'inactive_mine_historical'
            elif field in ['reserves', 'resources', 'ore_grade']:
                return 'inactive_mine_reserves'
            else:
                return 'inactive_mine_general'

        # Geplante Minen - nur Planungsdaten relevant
        elif status_lower in ['planned', 'development', 'under development', 'construction']:
            if field in ['annual_production', 'production_capacity']:
                return 'planned_mine_production'
            elif field in ['reserves', 'resources', 'ore_grade']:
                return 'planned_mine_reserves'
            elif field in ['investment_cost', 'capex', 'development_cost']:
                return 'planned_mine_investment'
            else:
                return 'planned_mine_general'

        # Exploration - nur Explorationsdaten relevant
        elif status_lower in ['exploration', 'exploratory', 'prospecting']:
            if field in ['reserves', 'resources', 'ore_grade']:
                return 'exploration_reserves'
            elif field in ['exploration_budget', 'drilling_results']:
                return 'exploration_data'
            else:
                return 'exploration_general'

        # Unbekannter Status
        else:
            return 'unknown_status'

    def extract_field_value(self, field: str, content: str, mine_name: str = "",
                          activity_status: str = "", model_id: str = "") -> Dict[str, Any]:
        """
        Extrahiert einen spezifischen Feldwert aus dem Inhalt

        Args:
            field: Name des zu extrahierenden Feldes
            content: Textinhalt für die Extraktion
            mine_name: Name der Mine (für Kontext)
            activity_status: Aktivitätsstatus der Mine
            model_id: ID des verwendeten Modells

        Returns:
            Dictionary mit extrahiertem Wert und Metadaten
        """
        try:
            # Generiere Status-Marker
            status_marker = self._get_field_status_marker(field, activity_status)

            # Prüfe ob Feld für diesen Status relevant ist
            if status_marker == 'unknown_status' and field in ['annual_production', 'current_production']:
                logger.warning(f"[EXTRACTION] Unbekannter Status für {mine_name}, Feld {field} möglicherweise nicht relevant")

            # Extrahiere Wert basierend auf Feldtyp
            if field in self.patterns:
                pattern_info = self.patterns[field]
                extracted_data = self._extract_with_pattern(field, content, pattern_info, mine_name)
            elif field in self.coordinate_patterns:
                extracted_data = self._extract_coordinates(field, content, mine_name)
            else:
                # Fallback für unbekannte Felder
                extracted_data = self._extract_generic(field, content, mine_name)

            # Post-Processing
            if extracted_data and extracted_data.get('value'):
                extracted_data = post_process_data(extracted_data, field, mine_name)

            # Füge Status-Marker hinzu
            if extracted_data:
                extracted_data['status_marker'] = status_marker
                extracted_data['activity_status'] = activity_status

            return extracted_data or {}

        except Exception as e:
            logger.error(f"[EXTRACTION] Fehler bei Extraktion von {field} für {mine_name}: {e}")
            return {
                'field': field,
                'value': None,
                'confidence': 0.0,
                'error': str(e),
                'status_marker': self._get_field_status_marker(field, activity_status),
                'activity_status': activity_status
            }

    def _extract_with_pattern(self, field: str, content: str, pattern_info: Dict, mine_name: str) -> Dict[str, Any]:
        """Extrahiert Wert mit vordefiniertem Pattern"""
        try:
            patterns = pattern_info.get('patterns', [])
            if not patterns:
                return None

            best_match = None
            best_confidence = 0.0

            for pattern in patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    confidence = self._calculate_confidence(match, pattern_info, mine_name)
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_match = match

            if best_match:
                value = best_match.group(1) if best_match.groups() else best_match.group(0)
                return {
                    'field': field,
                    'value': clean_field_value(value),
                    'confidence': best_confidence,
                    'method': 'pattern_match',
                    'pattern_used': best_match.re.pattern
                }

            return None

        except Exception as e:
            logger.error(f"[EXTRACTION] Pattern-Fehler für {field}: {e}")
            return None

    def _extract_coordinates(self, field: str, content: str, mine_name: str) -> Dict[str, Any]:
        """Extrahiert Koordinaten mit speziellen Patterns"""
        try:
            coordinate_patterns = self.coordinate_patterns[field]
            best_match = None
            best_confidence = 0.0

            for pattern_info in coordinate_patterns:
                pattern = pattern_info['pattern']
                matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)

                for match in matches:
                    lat = match.group('lat')
                    lon = match.group('lon')

                    if lat and lon:
                        confidence = self._calculate_coordinate_confidence(match, pattern_info, mine_name)
                        if confidence > best_confidence:
                            best_confidence = confidence
                            best_match = {
                                'lat': lat,
                                'lon': lon,
                                'pattern_used': pattern
                            }

            if best_match:
                return {
                    'field': field,
                    'value': f"{best_match['lat']}, {best_match['lon']}",
                    'confidence': best_confidence,
                    'method': 'coordinate_extraction',
                    'pattern_used': best_match['pattern_used']
                }

            return None

        except Exception as e:
            logger.error(f"[EXTRACTION] Koordinaten-Fehler für {field}: {e}")
            return None

    def _extract_generic(self, field: str, content: str, mine_name: str) -> Dict[str, Any]:
        """Generische Extraktion für unbekannte Felder"""
        try:
            # Suche nach Feldname + Wert Patterns
            field_patterns = [
                rf"{re.escape(field)}[:\s]+([^\n\r]+)",
                rf"{re.escape(field)}[:\s]*([^\n\r]+)",
                rf"{re.escape(field.lower())}[:\s]+([^\n\r]+)",
                rf"{re.escape(field.upper())}[:\s]+([^\n\r]+)"
            ]

            for pattern in field_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    value = match.group(1).strip()
                    if value and not is_field_name_value(value):
                        return {
                            'field': field,
                            'value': clean_field_value(value),
                            'confidence': 0.3,  # Niedrige Konfidenz für generische Extraktion
                            'method': 'generic_extraction',
                            'pattern_used': pattern
                        }

            return None

        except Exception as e:
            logger.error(f"[EXTRACTION] Generische Extraktion-Fehler für {field}: {e}")
            return None

    def _calculate_confidence(self, match, pattern_info: Dict, mine_name: str) -> float:
        """Berechnet Konfidenz-Score für einen Match"""
        try:
            base_confidence = pattern_info.get('confidence', 0.5)

            # Erhöhe Konfidenz basierend auf Match-Qualität
            match_text = match.group(0).lower()

            # Prüfe auf Mine-Name im Kontext
            if mine_name and mine_name.lower() in match_text:
                base_confidence += 0.2

            # Prüfe auf Zahlen/Units
            if re.search(r'\d+', match_text):
                base_confidence += 0.1

            # Prüfe auf Units
            if re.search(r'(ton|kg|g|oz|lb|m|km|ha|acre|year|€|$|usd|eur)', match_text):
                base_confidence += 0.1

            return min(base_confidence, 1.0)

        except Exception as e:
            logger.error(f"[EXTRACTION] Konfidenz-Berechnung Fehler: {e}")
            return 0.0

    def _calculate_coordinate_confidence(self, match, pattern_info: Dict, mine_name: str) -> float:
        """Berechnet Konfidenz-Score für Koordinaten-Match"""
        try:
            base_confidence = pattern_info.get('confidence', 0.6)

            # Prüfe auf gültige Koordinaten-Bereiche
            lat = float(match.group('lat'))
            lon = float(match.group('lon'))

            if -90 <= lat <= 90 and -180 <= lon <= 180:
                base_confidence += 0.2

            # Prüfe auf Mine-Name im Kontext
            match_text = match.group(0).lower()
            if mine_name and mine_name.lower() in match_text:
                base_confidence += 0.2

            return min(base_confidence, 1.0)

        except Exception as e:
            logger.error(f"[EXTRACTION] Koordinaten-Konfidenz Fehler: {e}")
            return 0.0
