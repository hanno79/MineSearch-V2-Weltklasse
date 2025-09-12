"""
Author: rahn
Datum: 05.07.2025
Version: 1.0
Beschreibung: Utility-Funktionen für Multi-Provider Suchen
ÄNDERUNG 12.07.2025: count_filled_fields Funktion hinzugefügt
"""

import hashlib
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from functools import lru_cache

from minesearch.config import CSV_COLUMNS
from minesearch.utils import (
    generate_name_variants,
    generate_multilingual_search_terms,
    get_country_config,
)

logger = logging.getLogger(__name__)


def is_empty_value(value) -> bool:
    """
    CONSENSUS FIX: Prüft ob ein Wert als leer/ungültig gelten soll

    Args:
        value: Zu prüfender Wert

    Returns:
        True wenn Wert als leer gilt
    """
    if not value:
        return True

    normalized_value = str(value).lower().strip()

    # Liste der als leer geltenden Werte (identisch mit frontend)
    empty_values = [
        '', 'x', 'n/a', 'na', 'null', 'undefined', 'none', 'keine', 'keiner', 'kein',
        'unbekannt', 'unknown', 'nicht verfügbar', 'not available', 'no data',
        'keine angabe', 'keine daten', 'nicht vorhanden', 'not found',
        'leer', 'empty', '-', '--', '---', '?', '??', '???',
        'tbd', 'to be determined', 'wird ermittelt', 'in arbeit',
        'nicht angegeben', 'nicht ermittelt', 'k.a.', 'k.a', 'n.a.',
        'fehlt', 'missing', 'no information', 'no info',
        # CONSENSUS FIX: System-generierte Platzhalter
        'nichts gefunden', 'keine spezifischen daten dokumentiert',
        'keine verlässlichen daten', 'keine öffentlichen daten',
        'keine aktiven daten', 'no specific data', 'not documented'
    ]

    import re
    return (normalized_value in empty_values or
            len(normalized_value) == 0 or
            re.match(r'^[\s\-\?\.*]*$', normalized_value))  # Nur Leerzeichen, Striche, Fragezeichen


def count_filled_fields(structured_data: Dict[str, Any]) -> int:
    """
    Zählt korrekt gefüllte Felder aus structured_data

    ÄNDERUNG 12.07.2025: Neue Funktion für korrektes Feld-Tracking

    Args:
        structured_data: Dictionary mit Mining-Daten aus CSV_COLUMNS

    Returns:
        Anzahl der korrekt gefüllten Felder
    """
    if not structured_data:
        return 0

    filled_count = 0

    for field in CSV_COLUMNS:
        value = structured_data.get(field, '')

        # CONSENSUS FIX: Verwende robuste is_empty_value Funktion
        if value and not is_empty_value(value):
            filled_count += 1

    return filled_count


class SearchQueryBuilder:
    """Builder für Such-Queries"""

    @staticmethod
    def build_search_query(mine_name: str, name_variants: List[str],
    """build_search_query - TODO: Dokumentation hinzufügen"""
                          multilingual_terms: List[str], country: Optional[str],
                          commodity: Optional[str], model_id: str,
                          discovered_sources: List[Dict[str, Any]],
                          model_config: Dict) -> str:
        """Erstelle Suchanfrage basierend auf Modell-Fähigkeiten"""

        # Basis-Query
        query = f"Finde Informationen über die Mine: {mine_name}"

        if name_variants and len(name_variants) > 1:
            query += f" (auch bekannt als: {', '.join(name_variants[:2])})"

        if country:
            query += f" in {country}"

        if commodity:
            query += f", die {commodity} abbaut"

        # Füge discovered sources hinzu für Web-Search-fähige Modelle
        if hasattr(model_config, 'supports_web_search') and model_config.supports_web_search and discovered_sources:
            query += "\n\nPrüfe speziell diese Quellen:\n"
            for source in discovered_sources[:10]:
                query += f"- {source['url']} ({source.get("description", '')})\n"

        # Spezielle Anweisungen
        query += "\n\nFokussiere besonders auf:"
        query += "\n- Restaurationskosten / Closure Costs / Environmental Liabilities"
        query += "\n- Betreiber und Eigentümer"
        query += "\n- Produktionsdaten und Status"
        query += "\n- Genaue Koordinaten"

        return query


class DataQualityCalculator:
    """Berechnung von Datenqualitäts-Metriken"""

    @staticmethod
    def calculate_data_quality(structured_data: Dict[str, str]) -> Dict[str, Any]:
        """Berechne Datenqualitäts-Metriken"""

        filled_fields = sum(1 for col in CSV_COLUMNS if structured_data.get(col) and col != 'Name')
        total_fields = len(CSV_COLUMNS) - 1  # Minus Name-Feld
        data_completeness = filled_fields / total_fields if total_fields > 0 else 0

        # Bestimme Qualitätsstufe
        if data_completeness >= 0.7:
            quality_level = "Hoch"
        elif data_completeness >= 0.4:
            quality_level = "Mittel"
        else:
            quality_level = "Niedrig"

        return {
            "filled_fields": filled_fields,
            "total_fields": total_fields,
            "completeness_percentage": round(data_completeness * 100),
            "quality_level": quality_level,
            "missing_critical_fields": [
                col for col in ['Betreiber', 'Restaurationskosten', 'Rohstoff']
                if not structured_data.get(col)
            ]
        }


class SourceCacheManager:
    """Manager für Source-Caching"""

    def __init__(self):
    """__init__ - TODO: Dokumentation hinzufügen"""
        self._source_cache = {}

    def generate_cache_key(self, mine_name: str, country: str,
    """generate_cache_key - TODO: Dokumentation hinzufügen"""
                          commodity: str, region: str) -> str:
        """Generiere eindeutigen Cache-Key für Quellen"""
        key_parts = [mine_name, country or '', commodity or '', region or '']
        key_string = '|'.join(key_parts).lower()
        return hashlib.md5(key_string.encode()).hexdigest()

    @lru_cache(maxsize=100)
    def get_cached_sources(self, cache_key: str) -> Optional[List[Dict]]:
        """Hole gecachte Quellen wenn vorhanden"""
        cached = self._source_cache.get(cache_key)
        if cached and cached['expires'] > datetime.now():
            return cached['sources']
        return None

    def cache_sources(self, cache_key: str, sources: List[Dict], ttl_seconds: int):
        """Cache Quellen mit TTL"""
        self._source_cache[cache_key] = {
            'sources': sources,
            'expires': datetime.now() + timedelta(seconds=ttl_seconds)
        }

    def clear_expired(self):
        """Lösche abgelaufene Cache-Einträge"""
        now = datetime.now()
        expired_keys = [k for k, v in self._source_cache.items() if v['expires'] <= now]
        for key in expired_keys:
            del self._source_cache[key]


class ResultCombiner:
    """Kombiniert Ergebnisse aus verschiedenen Phasen"""

    @staticmethod
    def combine_phase_results(phase1_result: Dict, phase2_results: List[Dict]) -> Dict[str, Any]:
        """Kombiniere Ergebnisse aus beiden Phasen"""

        best_data = {}
        confidence_scores = {}
        all_sources = []

        # Sammle alle erfolgreichen Ergebnisse
        valid_results = [r for r in phase2_results if isinstance(r, dict) and r.get('success')]

        # Füge auch Phase 1 hinzu wenn erfolgreich
        if phase1_result.get('success'):
            valid_results.insert(0, phase1_result)

        # Kombiniere Daten mit Konfidenz-Scoring
        for field in CSV_COLUMNS:
            if field == 'Name':
                continue

            field_values = []
            for result in valid_results:
                field_value = result.get("data", {}).get(field)
                if field_value and not is_empty_value(field_value):
                    field_values.append(field_value)

            if field_values:
                # Wähle den häufigsten Wert (einfache Mehrheitsentscheidung)
                from collections import Counter
                value_counts = Counter(field_values)
                best_value, count = value_counts.most_common(1)[0]
                best_data[field] = best_value
                confidence_scores[field] = count / len(valid_results)
            else:
                # CONSENSUS FIX: Für komplett leere Felder = 0% Confidence
                confidence_scores[field] = 0.0

        # Sammle alle Quellen
        for result in valid_results:
            if result.get('sources'):
                all_sources.extend(result['sources'])

        # Dedupliziere Quellen
        unique_sources = []
        seen_urls = set()
        for source in all_sources:
            url = source.get("url", source.get('value', ''))
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_sources.append(source)

        return {
            'best_data': best_data,
            'confidence': confidence_scores,
            'all_sources': unique_sources[:20]  # Top 20 Quellen
        }

    @staticmethod
    def integrate_phase3_results(combined_data: Dict, phase3_result: Dict) -> Dict:
        """Integriere Phase 3 Ergebnisse in kombinierte Daten"""

        phase3_data = phase3_result.get("data", {})

        # Fülle fehlende Felder mit Phase 3 Daten
        for field, value in phase3_data.items():
            if value and not combined_data['best_data'].get(field):
                combined_data['best_data'][field] = value
                combined_data['confidence'][field] = 0.8  # Phase 3 Konfidenz

        # Erweitere Quellen
        if phase3_result.get('sources'):
            combined_data['all_sources'].extend(phase3_result['sources'])

        return combined_data
