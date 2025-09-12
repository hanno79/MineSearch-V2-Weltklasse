"""
Author: rahn
Datum: 11.09.2025
Version: 1.0
Beschreibung: Datenverarbeitungs-Logic für konsolidierte Ergebnis-Verarbeitung (Refactoring aus consolidated_results.py)
"""

import logging
from typing import Dict, List, Any, Optional
from collections import defaultdict
from datetime import datetime, timedelta

# Import field mappings from separated utility module
from .consolidated_field_utils import (
    FIELD_CONSOLIDATION_MAP,
    FIELD_RENAME_MAP,
    FIELD_ORDER,
    consolidate_and_rename_field
)

# Import utility functions
from .consolidated_utils import _analyze_field_values, _calculate_best_value

logger = logging.getLogger(__name__)


def process_mine_data_grouping(all_results, global_source_index_func):
    """
    PHASE 1.2: Verarbeitet Suchergebnisse und gruppiert nach Minen mit Deduplication

    Args:
        all_results: Liste aller SearchResult-Objekte
        global_source_index_func: Funktion zur globalen Quellennummerierung

    Returns:
        dict: Gruppierte und verarbeitete Mine-Daten
    """
    from minesearch.utils import normalize_accents, normalize_mine_name_for_grouping

    # Nach Mine gruppieren - MIT AKZENT-NORMALISIERUNG 24.08.2025
    mines_data = defaultdict(lambda: {
        'mine_name': '',
        'original_names': set(),  # Sammle alle ursprünglichen Schreibweisen
        'country': '',
        'region': '',
        'consolidated_fields': {},
        'model_results': [],
        'unique_models': set(),  # PHASE 3 FIX: Track unique model IDs to prevent overcounting
        'unique_sources': set(),  # PHASE 2 FIX: Track unique source URLs to prevent overcounting
        'model_count': 0,
        'last_updated': None,
        'total_sources': 0,
        'source_mapping': {},  # Maps model names to source numbers (legacy)
        'field_source_references': {}  # Maps field values to global source numbers
    })

    for result in all_results:
        # DEDUPLICATION FIX 25.08.2025: Erweiterte Normalisierung für bessere Duplikat-Erkennung
        mine_name = result.mine_name
        normalized_mine_name = normalize_mine_name_for_grouping(mine_name)

        # Gruppiere nach normalisiertem Namen
        mine_data = mines_data[normalized_mine_name]

        # Sammle ursprüngliche Schreibweisen
        mine_data['original_names'].add(mine_name)

        # Basis-Informationen setzen - wähle häufigsten Namen für Anzeige
        if not mine_data['mine_name']:
            mine_data['mine_name'] = mine_name  # Erster Name als Initial

        # Länderdaten verarbeiten
        mine_data = _process_location_data(mine_data, result, mine_name)

        # PHASE 4 FIX: Count ALL model results, not just unique models
        mine_data['model_count'] += 1

        # Letzte Aktualisierung
        if not mine_data['last_updated'] or result.search_timestamp > mine_data['last_updated']:
            mine_data['last_updated'] = result.search_timestamp

        # Modell-spezifische Daten sammeln
        model_info = _create_model_info(result)
        mine_data['model_results'].append(model_info)

        # Source mapping für Legacy-Kompatibilität
        if result.model_used not in mine_data['source_mapping']:
            source_number = len(mine_data['source_mapping']) + 1
            mine_data['source_mapping'][result.model_used] = source_number

        # Feldkonsolidierung verarbeiten
        if result.structured_data:
            mine_data = _process_field_consolidation(
                mine_data, result, global_source_index_func
            )

    # QUELLENREFERENZEN-FIX 24.08.2025: Zähle nur tatsächlich verwendete Quellen
    for mine_data in mines_data.values():
        used_sources = set()
        for field_info in mine_data['consolidated_fields'].values():
            for real_source_list in field_info['real_sources']:
                for real_source_url in real_source_list:
                    used_sources.add(real_source_url)

        mine_data['unique_sources'].update(used_sources)
        mine_data['total_sources'] = len(mine_data['unique_sources'])

    return mines_data


def _process_location_data(mine_data, result, mine_name):
    """Verarbeitet Länder- und Regionsdaten mit Fallback auf mines_normalized"""
    search_country = result.country or ''
    search_region = result.region or ''

    # Wenn SearchResult keine gültigen Daten hat, hole sie aus mines_normalized
    if not search_country or search_country.lower() in ['unknown', 'nicht verfügbar']:
        try:
            # Direkte DB-Abfrage für mines_normalized ohne zirkuläre Abhängigkeiten
            from sqlalchemy import text
            from minesearch.database import db_manager

            with db_manager.get_session() as session:
                normalized_query = session.execute(text("""
                    SELECT country, region
                    FROM mines_normalized
                    WHERE name = :mine_name OR normalized_name = :mine_name
                    LIMIT 1
                """), {"mine_name": mine_name})
                normalized_result = normalized_query.fetchone()

                if normalized_result and normalized_result[0]:
                    mine_data['country'] = normalized_result[0] or search_country
                    mine_data['region'] = normalized_result[1] or search_region
                    logger.info(f"[COUNTRY-FIX] Loaded location for {mine_name}:
{normalized_result[0]}, {normalized_result[1]}")
                else:
                    mine_data['country'] = search_country
                    mine_data['region'] = search_region
        except Exception as e:
            logger.warning(f"Could not fetch normalized location for {mine_name}: {e}")
            mine_data['country'] = search_country
            mine_data['region'] = search_region
    else:
        mine_data['country'] = search_country
        mine_data['region'] = search_region

    return mine_data


def _create_model_info(result):
    """Erstellt Modell-Info-Dictionary aus SearchResult"""
    return {
        'id': result.id,
        'model_id': result.model_used,  # CRITICAL FIX 20.08.2025: Add model_id field for frontend compatibility
        'model_used': result.model_used,
        'search_timestamp': result.search_timestamp.isoformat() if result.search_timestamp else None,
        'structured_data': result.structured_data or {},
        'sources': result.sources or [],
        'data_quality': result.data_quality or {},
        'search_duration': result.search_duration,
        'fields_found': len([v for v in (result.structured_data or {}).values() if v and
str(v).strip() and str(v).strip().upper() != 'X'])
    }


def _process_field_consolidation(mine_data, result, global_source_index_func):
    """
    ENHANCED: Felder konsolidieren mit Umbenennung und erweiterten Metadaten
    """
    for original_field_name, field_value in result.structured_data.items():
        # CRITICAL FIX: Apply field consolidation and renaming FIRST, before X-value filtering
        final_field_name, processed_value = consolidate_and_rename_field(original_field_name, field_value)

        # Now check if we have actual data_dict (not X) for statistics
        has_real_data = (processed_value and str(processed_value).strip() and
                       str(processed_value).strip().upper() != 'X')

        # STEP 2A: Store field structure even for X-values (for consistent field schema)
        if final_field_name not in mine_data['consolidated_fields']:
            mine_data['consolidated_fields'][final_field_name] = {
                'raw_values': [],
                'ai_models': [],
                'real_sources': [],
                'value_details': []
            }

        # STEP 2B: Only process actual data_dict (non-X values) for statistics
        if has_real_data:
            clean_value = str(processed_value).strip()

            # ENHANCED DUPLICATE PREVENTION 06.08.2025: Vollständige Feldkonsolidierung
            mine_data = _handle_field_consolidation_duplicates(
                mine_data, original_field_name, final_field_name, clean_value, result.model_used
            )

            # PHASE 1.2: Extract real data_dict sources mit globaler Nummerierung
            real_sources, global_source_numbers = _extract_real_sources(
                result.sources, global_source_index_func
            )

            # QUELLENREFERENZEN-FIX 24.08.2025: Für Quellenangaben Feld - zeige nur tatsächlich genutzte Quellen
            if final_field_name.lower() in ['quellenangaben', 'sources', 'quellen']:
                clean_value = _process_sources_field(result.sources, real_sources)

            # PHASE 1.2: Add data_dict mit globalen Quellenreferenzen
            mine_data['consolidated_fields'][final_field_name]['raw_values'].append(clean_value)
            mine_data['consolidated_fields'][final_field_name]['ai_models'].append(result.model_used)
            mine_data['consolidated_fields'][final_field_name]['real_sources'].append(real_sources)
            mine_data['consolidated_fields'][final_field_name]['value_details'].append({
                'value': clean_value,
                'ai_model': result.model_used,
                'real_sources': real_sources,
                'global_source_numbers': global_source_numbers,  # PHASE 1.2: Globale Referenzen
                'search_timestamp': result.search_timestamp,
                'data_quality': result.data_quality or {},
                'search_duration': result.search_duration or 0
            })

            # PHASE 1.2: Store field-specific source references
            if final_field_name not in mine_data['field_source_references']:
                mine_data['field_source_references'][final_field_name] = set()
            mine_data['field_source_references'][final_field_name].update(global_source_numbers)
        else:
            # STEP 4: Even for X-values, ensure we have the field structure for future data
            if final_field_name not in mine_data['consolidated_fields']:
                logger.debug(f"Creating field structure for X-value field: {final_field_name} (was:
{original_field_name})")
                mine_data['consolidated_fields'][final_field_name] = {
                    'raw_values': [],
                    'ai_models': [],
                    'real_sources': [],
                    'value_details': []
                }

    return mine_data


def _handle_field_consolidation_duplicates(mine_data, original_field_name, final_field_name, clean_value, model_used):
    """Behandelt Duplikate bei der Feldkonsolidierung"""
    if original_field_name != final_field_name:
        # Entferne das ursprüngliche Feld aus der Feldliste falls es bereits existiert
        if original_field_name in mine_data['consolidated_fields']:
            logger.info(f"Removing original field '{original_field_name}' after consolidation to '{final_field_name}'")
            # Merge existing data_dict vom ursprünglichen Feld ins konsolidierte Feld
            original_field_data = mine_data['consolidated_fields'][original_field_name]
            if final_field_name not in mine_data['consolidated_fields']:
                mine_data['consolidated_fields'][final_field_name] = {
                    'raw_values': [],
                    'ai_models': [],
                    'real_sources': [],
                    'value_details': []
                }
            # Merge data
            mine_data['consolidated_fields'][final_field_name]['raw_values'].extend(original_field_data['raw_values'])
            mine_data['consolidated_fields'][final_field_name]['ai_models'].extend(original_field_data['ai_models'])

mine_data['consolidated_fields'][final_field_name]['real_sources'].extend(original_field_data['real_sources'])

mine_data['consolidated_fields'][final_field_name]['value_details'].extend(original_field_data['value_details'])
            # Remove original field
            del mine_data['consolidated_fields'][original_field_name]

        # Smart duplicate avoidance for same model contributing twice
        target_field_exists = final_field_name in mine_data['consolidated_fields']
        if target_field_exists:
            existing_models = mine_data['consolidated_fields'][final_field_name]['ai_models']
            if model_used in existing_models:
                existing_values = mine_data['consolidated_fields'][final_field_name]['raw_values']
                if clean_value in existing_values:
                    logger.debug(f"Skipping duplicate consolidation: {original_field_name} ->
{final_field_name} für Modell {model_used}")
                    return mine_data

    return mine_data


def _extract_real_sources(sources, global_source_index_func):
    """Extrahiert echte Quellen-URLs und weist globale Nummern zu"""
    real_sources = []
    global_source_numbers = []

    if sources:
        for source in sources:
            source_url = None
            if isinstance(source, str) and ('http' in source or 'www.' in source):
                source_url = source
            elif isinstance(source, dict) and source.get('url'):
                source_url = source['url']

            if source_url:
                real_sources.append(source_url)
                # Globale Quellennummer zuweisen
                source_number = global_source_index_func(source_url)
                global_source_numbers.append(source_number)

    return real_sources, global_source_numbers


def _process_sources_field(sources, real_sources):
    """Verarbeitet Quellenangaben-Feld mit Kategorisierung"""
    if not sources:
        return f"{len(real_sources)} Quellen gefunden" if real_sources else "Keine Quellen"

    actually_used_sources = []
    source_types = {}

    for source in sources:
        if isinstance(source, dict) and source.get('url') in real_sources:
            # Nur Quellen zählen, die auch echte URLs haben
            source_type = source.get("type", 'general')
            source_types[source_type] = source_types.get(source_type, 0) + 1
            actually_used_sources.append(source)

    if actually_used_sources:
        source_summary = []
        for stype, count in source_types.items():
            if stype == 'government':
                source_summary.append(f"{count} Behörden-Quellen")
            elif stype == 'database':
                source_summary.append(f"{count} Datenbank-Quellen")
            elif stype == 'industry':
                source_summary.append(f"{count} Industrie-Quellen")
            elif stype == 'document':
                source_summary.append(f"{count} Dokument-Quellen")
            elif stype == 'expert_knowledge':
                source_summary.append(f"{count} Fachwissen-Quellen")
            else:
                source_summary.append(f"{count} {stype}-Quellen")

        return f"{len(actually_used_sources)} Quellen: " + ", ".join(source_summary)
    else:
        # Fallback wenn keine echten Quellen: Zähle wenigstens real_sources
        return f"{len(real_sources)} Quellen gefunden"


def select_display_names(mines_data, all_results):
    """
    DISPLAY NAME SELECTION 25.08.2025: Wähle besten ursprünglichen Namen für Anzeige
    """
    for normalized_name, mine_data in mines_data.items():
        if len(mine_data['original_names']) > 1:
            # Zähle Häufigkeit jeder Schreibweise in den Daten
            name_counts = {}
            for original_name in mine_data['original_names']:
                name_counts[original_name] = sum(1 for result in all_results
                                               if result.mine_name == original_name and
                                               normalize_mine_name_for_grouping(result.mine_name) == normalized_name)

            # Wähle besten Namen: Priorität für vollständige Namen (mit "Mine" etc.)
            best_display_name = max(mine_data['original_names'], key=lambda name: (
                name_counts.get(name, 0),  # Häufigkeit
                len(name),  # Länge (längere Namen bevorzugt)
                ' mine' in name.lower() or ' project' in name.lower()  # Suffixe bevorzugt
            ))

            mine_data['mine_name'] = best_display_name

            logger.info(f"[DEDUPLICATION] '{normalized_name}' hat {len(mine_data['original_names'])}
Schreibweisen: {mine_data['original_names']}")
            logger.info(f"[DEDUPLICATION] Gewählter Anzeigename: '{best_display_name}' (beste Schreibweise)")
        elif len(mine_data['original_names']) == 1:
            # Nur eine Schreibweise - verwende diese
            mine_data['mine_name'] = next(iter(mine_data['original_names']))

    return mines_data


def initialize_expected_fields(mine_data, mine_name):
    """
    FIELD-CONSOLIDATION-FIX 06.08.2025: Erweiterte Field-Initialisierung mit Konsolidierungslogik
    """
    from minesearch.config.base import CSV_COLUMNS

    logger.info(f"[FIELD-INIT] Prüfe {len(CSV_COLUMNS)} erwartete Felder für Mine '{mine_name}' nach Konsolidierung")
    fields_added = 0

    for expected_field in CSV_COLUMNS:
        if expected_field not in ['Mine', 'Quellenangaben']:  # Skip meta fields
            # CRITICAL: Apply same consolidation logic to expected fields
            final_field_name, _ = consolidate_and_rename_field(expected_field, "")

            # Only add if the final field name doesn't exist yet
            if final_field_name not in mine_data['consolidated_fields']:
                mine_data['consolidated_fields'][final_field_name] = {
                    'raw_values': [],
                    'ai_models': [],
                    'real_sources': [],
                    'value_details': []
                }
                fields_added += 1
                logger.info(f"[FIELD-INIT] Feld '{final_field_name}' für Mine '{mine_name}'
initialisiert (war: {expected_field})")

    logger.info(f"[FIELD-INIT] {fields_added} Felder zu Mine '{mine_name}' hinzugefügt. Total:
{len(mine_data['consolidated_fields'])}")
    return mine_data


def process_best_value_algorithm(mine_data, mine_name):
    """
    Implementiert "Best Value" Algorithmus für jedes Feld mit intelligenter Analyse
    """
    from minesearch.utils import normalize_mine_name_for_grouping

    best_values = {}  # Für Haupttabelle - nur bester Wert pro Feld
    detailed_breakdown = {}  # Für Details-Modal - vollständige Aufschlüsselung

    # STEP 3: Process fields in preferred order
    ordered_fields = []
    unordered_fields = []

    # Separate fields into ordered and unordered
    for field_name in mine_data['consolidated_fields'].keys():
        if field_name in FIELD_ORDER:
            ordered_fields.append(field_name)
        else:
            unordered_fields.append(field_name)

    # Sort ordered fields by their position in FIELD_ORDER
    ordered_fields.sort(key=lambda x: FIELD_ORDER.index(x))

    # Process fields in order: ordered first, then unordered alphabetically
    all_field_names = ordered_fields + sorted(unordered_fields)

    for field_name in all_field_names:
        field_info = mine_data['consolidated_fields'][field_name]

        # 🆕 SCHEMA-NORMALISIERUNG 28.08.2025: Prüfe atomische Werte zuerst
        atomic_best_value = _try_atomic_value_lookup(mine_name, field_name)

        if atomic_best_value and atomic_best_value.get("confidence_score", 0) >= 50.0:
            logger.info(f"[ATOMIC] Verwende atomischen Wert für {mine_name}.{field_name}:
{atomic_best_value['atomic_value']}")
            best_value_info = {
                'display_value': atomic_best_value['display_value'],
                'confidence_score': atomic_best_value['confidence_score'],
                'source_info': atomic_best_value['source'],
                'method': 'atomic_normalized'
            }
        else:
            # FALLBACK: Intelligente Analyse der JSON-Daten
            logger.debug(f"[FALLBACK] Atomischer Wert für {mine_name}.{field_name} nicht
verfügbar/unzureichend - nutze JSON-Analyse")

            # Intelligente Feld-Analyse
            analysis_result = _analyze_field_values(field_info['value_details'], field_name)
            best_value = _calculate_best_value(analysis_result, field_name)

            if best_value is not None:
                best_value_info = {
                    'display_value': best_value,
                    'confidence_score': analysis_result.get("confidence_score", 0.0),
                    'source_info': f"{analysis_result.get("best_value_support", 0)} Modelle",
                    'method': 'intelligent_analysis'
                }
            else:
                best_value_info = {
                    'display_value': '',
                    'confidence_score': 0.0,
                    'source_info': 'Keine verlässlichen Daten',
                    'method': 'no_data'
                }

        # Store in results
        best_values[field_name] = best_value_info['display_value']

        # Detailed breakdown for modal
        detailed_breakdown[field_name] = {
            'best_value': best_value_info,
            'all_values': field_info['raw_values'],
            'sources': field_info['ai_models'],
            'value_count': len(field_info['raw_values']),
            'model_count': len(set(field_info['ai_models']))
        }

    return best_values, detailed_breakdown


def _try_atomic_value_lookup(mine_name, field_name):
    """Versucht atomischen Wert zu finden mit Fehlerbehandlung"""
    try:
        from minesearch.atomic_value_service import calculate_best_atomic_value
        from minesearch.database import db_manager

        with db_manager.get_session() as session:
            atomic_best_value = calculate_best_atomic_value(
                session, mine_name, field_name, fallback_to_json=True
            )

            # Verwende atomischen Wert wenn verfügbar und von hoher Qualität
            if (atomic_best_value.get('method') == 'atomic_normalized' and
                atomic_best_value.get("confidence_score", 0) >= 50.0):
                return atomic_best_value

    except Exception as e:
        logger.debug(f"[ATOMIC] Lookup failed for {mine_name}.{field_name}: {e}")

    return None


def create_global_source_index(search_results):
    """
    Erstellt einen globalen Index aller verwendeten Quellen

    Args:
        search_results: Liste aller Suchergebnisse

    Returns:
        Dict mit Quellen-Index
    """
    source_index = {}
    source_counter = 1

    for result in search_results:
        try:
            import json
            real_sources = result.real_sources if result.real_sources else []

            for source in real_sources:
                if source not in source_index:
                    source_index[str(source_counter)] = {
                        'url': str(source),
                        'title': f'Source {source_counter}',
                        'first_seen': result.search_timestamp.isoformat() if result.search_timestamp else None
                    }
                    source_counter += 1
        except Exception as e:
            logger.debug(f"Error processing source for global index: {e}")
            continue

    return source_index
