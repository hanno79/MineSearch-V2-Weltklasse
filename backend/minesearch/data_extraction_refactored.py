"""
Author: rahn
Datum: 11.09.2025
Version: 2.0
Beschreibung: Refaktorisierte Datenextraktion für MineSearch v2 (REGEL 1 konform: <500 Zeilen)
"""

import logging
from typing import Dict, List, Any, Optional
from .data_extraction_core import DataExtractor

logger = logging.getLogger(__name__)


class DataExtractionService:
    """Service-Klasse für Datenextraktion - koordiniert verschiedene Extraktions-Module"""

    def __init__(self):
    """__init__ - TODO: Dokumentation hinzufügen"""
        self.extractor = DataExtractor()

    def extract_all_fields(self, content: str, mine_name: str = "",
    """extract_all_fields - TODO: Dokumentation hinzufügen"""
                          activity_status: str = "", model_id: str = "") -> Dict[str, Any]:
        """
        Extrahiert alle verfügbaren Felder aus dem Inhalt

        Args:
            content: Textinhalt für die Extraktion
            mine_name: Name der Mine
            activity_status: Aktivitätsstatus der Mine
            model_id: ID des verwendeten Modells

        Returns:
            Dictionary mit allen extrahierten Feldern
        """
        try:
            logger.info(f"[EXTRACTION] Starte Extraktion für {mine_name} mit Modell {model_id}")

            # Definiere Felder die extrahiert werden sollen
            fields_to_extract = [
                'mine_name', 'country', 'region', 'coordinates',
                'mineral_type', 'mining_method', 'production_status',
                'annual_production', 'production_capacity', 'reserves',
                'owner_company', 'operator_company', 'investment_cost',
                'operating_cost', 'employment', 'environmental_impact'
            ]

            extracted_data = {}
            extraction_stats = {
                'total_fields': len(fields_to_extract),
                'successful_extractions': 0,
                'failed_extractions': 0,
                'placeholder_values': 0,
                'fallback_values': 0
            }

            # Extrahiere jedes Feld
            for field in fields_to_extract:
                try:
                    result = self.extractor.extract_field_value(
                        field, content, mine_name, activity_status, model_id
                    )

                    if result and result.get('value'):
                        extracted_data[field] = result
                        extraction_stats['successful_extractions'] += 1

                        # Zähle Placeholder/Fallback Werte
                        if result.get("is_placeholder", False):
                            extraction_stats['placeholder_values'] += 1
                        if result.get("is_fallback", False):
                            extraction_stats['fallback_values'] += 1
                    else:
                        extraction_stats['failed_extractions'] += 1

                except Exception as e:
                    logger.error(f"[EXTRACTION] Fehler bei Feld {field}: {e}")
                    extraction_stats['failed_extractions'] += 1

            # Berechne Erfolgsrate
            success_rate = (extraction_stats['successful_extractions'] /
                          extraction_stats['total_fields']) * 100

            logger.info(f"[EXTRACTION] Extraktion abgeschlossen für {mine_name}: "
                       f"{extraction_stats['successful_extractions']}/{extraction_stats['total_fields']} "
                       f"Felder ({success_rate:.1f}% Erfolgsrate)")

            return {
                'mine_name': mine_name,
                'model_id': model_id,
                'extracted_data': extracted_data,
                'extraction_stats': extraction_stats,
                'success_rate': success_rate,
                'activity_status': activity_status
            }

        except Exception as e:
            logger.error(f"[EXTRACTION] Kritischer Fehler bei Extraktion für {mine_name}: {e}")
            return {
                'mine_name': mine_name,
                'model_id': model_id,
                'extracted_data': {},
                'extraction_stats': {'error': str(e)},
                'success_rate': 0.0,
                'activity_status': activity_status
            }

    def extract_specific_fields(self, fields: List[str], content: str,
    """extract_specific_fields - TODO: Dokumentation hinzufügen"""
                              mine_name: str = "", activity_status: str = "",
                              model_id: str = "") -> Dict[str, Any]:
        """
        Extrahiert spezifische Felder aus dem Inhalt

        Args:
            fields: Liste der zu extrahierenden Felder
            content: Textinhalt für die Extraktion
            mine_name: Name der Mine
            activity_status: Aktivitätsstatus der Mine
            model_id: ID des verwendeten Modells

        Returns:
            Dictionary mit extrahierten Feldern
        """
        try:
            logger.info(f"[EXTRACTION] Extrahiere spezifische Felder für {mine_name}: {fields}")

            extracted_data = {}
            extraction_stats = {
                'requested_fields': len(fields),
                'successful_extractions': 0,
                'failed_extractions': 0
            }

            # Extrahiere jedes angeforderte Feld
            for field in fields:
                try:
                    result = self.extractor.extract_field_value(
                        field, content, mine_name, activity_status, model_id
                    )

                    if result and result.get('value'):
                        extracted_data[field] = result
                        extraction_stats['successful_extractions'] += 1
                    else:
                        extraction_stats['failed_extractions'] += 1

                except Exception as e:
                    logger.error(f"[EXTRACTION] Fehler bei Feld {field}: {e}")
                    extraction_stats['failed_extractions'] += 1

            # Berechne Erfolgsrate
            success_rate = (extraction_stats['successful_extractions'] /
                          extraction_stats['requested_fields']) * 100 if fields else 0

            return {
                'mine_name': mine_name,
                'model_id': model_id,
                'requested_fields': fields,
                'extracted_data': extracted_data,
                'extraction_stats': extraction_stats,
                'success_rate': success_rate,
                'activity_status': activity_status
            }

        except Exception as e:
            logger.error(f"[EXTRACTION] Fehler bei spezifischer Extraktion für {mine_name}: {e}")
            return {
                'mine_name': mine_name,
                'model_id': model_id,
                'requested_fields': fields,
                'extracted_data': {},
                'extraction_stats': {'error': str(e)},
                'success_rate': 0.0,
                'activity_status': activity_status
            }

    def validate_extraction_results(self, extraction_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validiert Extraktions-Ergebnisse

        Args:
            extraction_results: Ergebnisse der Datenextraktion

        Returns:
            Validierte und bereinigte Ergebnisse
        """
        try:
            validated_results = extraction_results.copy()
            validation_stats = {
                'total_fields': 0,
                'validated_fields': 0,
                'invalid_fields': 0,
                'warnings': []
            }

            extracted_data = extraction_results.get("extracted_data", {})

            for field, data in extracted_data.items():
                validation_stats['total_fields'] += 1

                # Validiere Feld-Daten
                if self._validate_field_data(field, data):
                    validation_stats['validated_fields'] += 1
                else:
                    validation_stats['invalid_fields'] += 1
                    validation_stats['warnings'].append(f"Ungültige Daten für Feld {field}")

            # Füge Validierungs-Statistiken hinzu
            validated_results['validation_stats'] = validation_stats
            validated_results['validation_success_rate'] = (
                validation_stats['validated_fields'] / validation_stats['total_fields'] * 100
                if validation_stats['total_fields'] > 0 else 0
            )

            return validated_results

        except Exception as e:
            logger.error(f"[EXTRACTION] Validierungsfehler: {e}")
            return extraction_results

    def _validate_field_data(self, field: str, data: Dict[str, Any]) -> bool:
        """Validiert Daten für ein spezifisches Feld"""
        try:
            if not data or not data.get('value'):
                return False

            value = data.get('value')

            # Feld-spezifische Validierung
            if field == 'coordinates':
                return self._validate_coordinates(value)
            elif field in ['annual_production', 'production_capacity']:
                return self._validate_production_value(value)
            elif field in ['reserves', 'resources']:
                return self._validate_reserves_value(value)
            elif field == 'investment_cost':
                return self._validate_cost_value(value)
            else:
                # Generische Validierung
                return self._validate_generic_value(value)

        except Exception as e:
            logger.error(f"[EXTRACTION] Validierungsfehler für Feld {field}: {e}")
            return False

    def _validate_coordinates(self, value: str) -> bool:
        """Validiert Koordinaten-Werte"""
        try:
            if ',' in value:
                parts = value.split(',')
                if len(parts) == 2:
                    lat, lon = parts[0].strip(), parts[1].strip()
                    return (-90 <= float(lat) <= 90 and -180 <= float(lon) <= 180)
            return False
        except:
            return False

    def _validate_production_value(self, value: str) -> bool:
        """Validiert Produktions-Werte"""
        try:
            # Suche nach Zahlen in verschiedenen Formaten
            import re
            numbers = re.findall(r'\d+(?:\.\d+)?', value)
            return len(numbers) > 0
        except:
            return False

    def _validate_reserves_value(self, value: str) -> bool:
        """Validiert Reserven-Werte"""
        try:
            import re
            numbers = re.findall(r'\d+(?:\.\d+)?', value)
            return len(numbers) > 0
        except:
            return False

    def _validate_cost_value(self, value: str) -> bool:
        """Validiert Kosten-Werte"""
        try:
            import re
            numbers = re.findall(r'\d+(?:\.\d+)?', value)
            return len(numbers) > 0
        except:
            return False

    def _validate_generic_value(self, value: str) -> bool:
        """Generische Validierung für unbekannte Felder"""
        try:
            # Prüfe auf leere oder Platzhalter-Werte
            if not value or value.strip() == '':
                return False

            # Prüfe auf bekannte Platzhalter
            placeholder_indicators = ['n/a', 'unknown', 'not available', 'tbd', 'tba']
            if value.lower().strip() in placeholder_indicators:
                return False

            return True
        except:
            return False


# Exportiere die Hauptklasse für einfachen Import
DataExtractor = DataExtractionService
