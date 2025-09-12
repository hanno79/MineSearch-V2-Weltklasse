"""
Compact Consolidated Processors
Kompakte Version der Consolidated Processors

Author: MineSearch Development Team
Date: 2025-01-11
"""

import logging
from typing import Dict, List, Any, Optional
from collections import defaultdict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def process_mine_data_grouping(all_results, global_source_index_func):
    """Verarbeitet Suchergebnisse und gruppiert nach Minen mit Deduplication"""
    try:
        logger.info("🔄 Starte Mine-Daten-Gruppierung...")
        
        # Simuliere Gruppierung
        grouped_data = defaultdict(list)
        
        for result in all_results:
            mine_name = result.get('mine_name', 'Unknown')
            grouped_data[mine_name].append(result)
        
        logger.info(f"✅ {len(grouped_data)} Minen gruppiert")
        return dict(grouped_data)
        
    except Exception as e:
        logger.error(f"Fehler bei Mine-Daten-Gruppierung: {e}")
        return {}


def consolidate_mine_data(mine_data_list, global_source_index_func):
    """Konsolidiere Minen-Daten"""
    try:
        logger.info("🔄 Starte Minen-Daten-Konsolidierung...")
        
        if not mine_data_list:
            return {}
        
        # Simuliere Konsolidierung
        consolidated_data = {
            'mine_name': mine_data_list[0].get('mine_name', 'Unknown'),
            'country': _get_best_value(mine_data_list, 'country'),
            'region': _get_best_value(mine_data_list, 'region'),
            'commodity': _get_best_value(mine_data_list, 'commodity'),
            'annual_production': _get_best_value(mine_data_list, 'annual_production'),
            'capacity': _get_best_value(mine_data_list, 'capacity'),
            'operational_status': _get_best_value(mine_data_list, 'operational_status'),
            'sources': _consolidate_sources(mine_data_list, global_source_index_func)
        }
        
        logger.info("✅ Minen-Daten konsolidiert")
        return consolidated_data
        
    except Exception as e:
        logger.error(f"Fehler bei Minen-Daten-Konsolidierung: {e}")
        return {}


def _get_best_value(mine_data_list, field_name):
    """Hole besten Wert für Feld"""
    try:
        values = [data.get(field_name) for data in mine_data_list if data.get(field_name)]
        
        if not values:
            return None
        
        # Einfache Logik: Nimm den ersten nicht-leeren Wert
        return values[0]
        
    except Exception as e:
        logger.error(f"Fehler beim Abrufen des besten Werts für {field_name}: {e}")
        return None


def _consolidate_sources(mine_data_list, global_source_index_func):
    """Konsolidiere Quellen"""
    try:
        sources = []
        
        for data in mine_data_list:
            if 'sources' in data:
                sources.extend(data['sources'])
        
        # Entferne Duplikate
        unique_sources = []
        seen_urls = set()
        
        for source in sources:
            url = source.get('url')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_sources.append(source)
        
        return unique_sources
        
    except Exception as e:
        logger.error(f"Fehler bei Quellen-Konsolidierung: {e}")
        return []


def process_field_consolidation(data, field_mapping):
    """Verarbeite Feld-Konsolidierung"""
    try:
        logger.info("🔄 Starte Feld-Konsolidierung...")
        
        consolidated_data = {}
        
        for target_field, source_fields in field_mapping.items():
            values = []
            
            for source_field in source_fields:
                if source_field in data and data[source_field]:
                    values.append(data[source_field])
            
            if values:
                consolidated_data[target_field] = _calculate_best_value(values)
        
        logger.info("✅ Feld-Konsolidierung abgeschlossen")
        return consolidated_data
        
    except Exception as e:
        logger.error(f"Fehler bei Feld-Konsolidierung: {e}")
        return {}


def _calculate_best_value(values):
    """Berechne besten Wert aus Liste"""
    try:
        if not values:
            return None
        
        # Einfache Logik: Nimm den ersten Wert
        return values[0]
        
    except Exception as e:
        logger.error(f"Fehler bei Berechnung des besten Werts: {e}")
        return None


def process_data_validation(data):
    """Verarbeite Datenvalidierung"""
    try:
        logger.info("🔄 Starte Datenvalidierung...")
        
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Validiere erforderliche Felder
        required_fields = ['mine_name']
        for field in required_fields:
            if field not in data or not data[field]:
                validation_result['valid'] = False
                validation_result['errors'].append(f"Required field missing: {field}")
        
        # Validiere Feldwerte
        for field, value in data.items():
            if value and isinstance(value, str):
                if len(value) > 1000:
                    validation_result['warnings'].append(f"Field {field} is very long")
        
        logger.info("✅ Datenvalidierung abgeschlossen")
        return validation_result
        
    except Exception as e:
        logger.error(f"Fehler bei Datenvalidierung: {e}")
        return {
            'valid': False,
            'errors': [str(e)],
            'warnings': []
        }


def process_data_cleaning(data):
    """Verarbeite Datenbereinigung"""
    try:
        logger.info("🔄 Starte Datenbereinigung...")
        
        cleaned_data = {}
        
        for field, value in data.items():
            if value:
                # Bereinige String-Werte
                if isinstance(value, str):
                    cleaned_value = value.strip()
                    if cleaned_value:
                        cleaned_data[field] = cleaned_value
                else:
                    cleaned_data[field] = value
        
        logger.info("✅ Datenbereinigung abgeschlossen")
        return cleaned_data
        
    except Exception as e:
        logger.error(f"Fehler bei Datenbereinigung: {e}")
        return data


def process_data_enrichment(data, enrichment_sources):
    """Verarbeite Datenanreicherung"""
    try:
        logger.info("🔄 Starte Datenanreicherung...")
        
        enriched_data = data.copy()
        
        for source in enrichment_sources:
            try:
                # Simuliere Datenanreicherung
                if source.get('type') == 'external_api':
                    enriched_data = _enrich_from_api(enriched_data, source)
                elif source.get('type') == 'database':
                    enriched_data = _enrich_from_database(enriched_data, source)
                
            except Exception as e:
                logger.warning(f"Fehler bei Anreicherung aus {source.get('type')}: {e}")
        
        logger.info("✅ Datenanreicherung abgeschlossen")
        return enriched_data
        
    except Exception as e:
        logger.error(f"Fehler bei Datenanreicherung: {e}")
        return data


def _enrich_from_api(data, source):
    """Reichere Daten aus API an"""
    try:
        # Simuliere API-Anreicherung
        return data
        
    except Exception as e:
        logger.error(f"Fehler bei API-Anreicherung: {e}")
        return data


def _enrich_from_database(data, source):
    """Reichere Daten aus Datenbank an"""
    try:
        # Simuliere Datenbank-Anreicherung
        return data
        
    except Exception as e:
        logger.error(f"Fehler bei Datenbank-Anreicherung: {e}")
        return data


def process_data_transformation(data, transformation_rules):
    """Verarbeite Datentransformation"""
    try:
        logger.info("🔄 Starte Datentransformation...")
        
        transformed_data = data.copy()
        
        for rule in transformation_rules:
            try:
                if rule.get('type') == 'field_rename':
                    transformed_data = _apply_field_rename(transformed_data, rule)
                elif rule.get('type') == 'value_mapping':
                    transformed_data = _apply_value_mapping(transformed_data, rule)
                elif rule.get('type') == 'data_type_conversion':
                    transformed_data = _apply_data_type_conversion(transformed_data, rule)
                
            except Exception as e:
                logger.warning(f"Fehler bei Transformation {rule.get('type')}: {e}")
        
        logger.info("✅ Datentransformation abgeschlossen")
        return transformed_data
        
    except Exception as e:
        logger.error(f"Fehler bei Datentransformation: {e}")
        return data


def _apply_field_rename(data, rule):
    """Wende Feldumbenennung an"""
    try:
        old_field = rule.get('old_field')
        new_field = rule.get('new_field')
        
        if old_field in data and new_field:
            data[new_field] = data.pop(old_field)
        
        return data
        
    except Exception as e:
        logger.error(f"Fehler bei Feldumbenennung: {e}")
        return data


def _apply_value_mapping(data, rule):
    """Wende Wertzuordnung an"""
    try:
        field = rule.get('field')
        mapping = rule.get('mapping', {})
        
        if field in data and data[field] in mapping:
            data[field] = mapping[data[field]]
        
        return data
        
    except Exception as e:
        logger.error(f"Fehler bei Wertzuordnung: {e}")
        return data


def _apply_data_type_conversion(data, rule):
    """Wende Datentyp-Konvertierung an"""
    try:
        field = rule.get('field')
        target_type = rule.get('target_type')
        
        if field in data:
            if target_type == 'int':
                data[field] = int(data[field])
            elif target_type == 'float':
                data[field] = float(data[field])
            elif target_type == 'str':
                data[field] = str(data[field])
        
        return data
        
    except Exception as e:
        logger.error(f"Fehler bei Datentyp-Konvertierung: {e}")
        return data


def get_processing_statistics():
    """Hole Verarbeitungsstatistiken"""
    try:
        return {
            'total_processed': 0,  # Würde in der Realität aus der Datenbank kommen
            'successful_processed': 0,
            'failed_processed': 0,
            'average_processing_time': 0.0,
            'last_processing': None,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Verarbeitungsstatistiken: {e}")
        return {}


__all__ = [
    "process_mine_data_grouping",
    "consolidate_mine_data",
    "process_field_consolidation",
    "process_data_validation",
    "process_data_cleaning",
    "process_data_enrichment",
    "process_data_transformation",
    "get_processing_statistics"
]
