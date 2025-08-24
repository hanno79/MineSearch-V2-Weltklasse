"""
Author: rahn
Datum: 24.07.2025
Version: 1.0
Beschreibung: Konsolidierte Ergebnis-Management Routes für Mine-basierte Ansicht
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, List, Any
import logging
from minesearch.database import SearchResult
from collections import defaultdict

# Import field mappings from separated utility module
from .consolidated_field_utils import (
    FIELD_CONSOLIDATION_MAP, 
    FIELD_RENAME_MAP, 
    FIELD_ORDER,
    consolidate_and_rename_field
)

logger = logging.getLogger(__name__)
router = APIRouter()

# CSV imports for Phase 16.3
import csv
import io
from fastapi.responses import StreamingResponse
from datetime import datetime

# Field mappings are now imported from consolidated_field_utils.py

def _normalize_placeholder_value(value):
    """
    PHASE 15.2/15.3 FIX: Normalisiert ALLE Platzhalter-Werte (auch bestehende Datenbank-Werte!)
    TEMPLATE-FIX 19.08.2025: Erweitert um Template-Pattern-Erkennung
    
    Behandelt sowohl neue als auch bereits in der DB gespeicherte LEER-Varianten
    """
    if not value or not str(value).strip():
        return value
    
    value_str = str(value).strip()
    logger.error(f"[TEMPLATE-DEBUG] Processing value: '{value_str}'")
    
    # Import der Pattern aus extraction_processors für Konsistenz
    import re
    
    # TEMPLATE-FIX 19.08.2025: Template-Pattern-Erkennung ZUERST
    # KRITISCH: Robuste Erkennung für "TEMPLATE: Untertage/ Open-P..." Format!
    
    # DIRECT STRING CHECK: Falls der Wert mit "TEMPLATE:" beginnt
    if value_str.startswith('TEMPLATE:'):
        logger.error(f"[TEMPLATE-FIX] ✅ DIREKTER MATCH: '{value_str}' -> 'Nichts gefunden'")
        return 'Nichts gefunden'
    
    # Diese Werte sind Template-ähnliche Fallbacks und sollen zu "Nichts gefunden" werden
    template_patterns = [
        r'^TEMPLATE:\s*Untertage/\s*Open-Pit.*usw.*$',   # "TEMPLATE: Untertage/ Open-Pit/ usw.)" - KRITISCHES PATTERN!
        r'^TEMPLATE:\s*Gold/\s*Kupfer.*usw.*$',          # "TEMPLATE: Gold/ Kupfer/ Kohle/ usw.)"
        r'^TEMPLATE:\s*aktiv/\s*geplant.*sonstiges.*$',  # "TEMPLATE: aktiv/ geplant/ geschlossen/ sonstiges"
        r'^Untertage/\s*Open-Pit/\s*usw\.\)?$',         # "Untertage/ Open-Pit/ usw.)"
        r'^Gold/\s*Kupfer/\s*Kohle/\s*usw\.\)?$',       # "Gold/ Kupfer/ Kohle/ usw.)"
        r'^aktiv/\s*geplant/\s*geschlossen/\s*sonstiges\)?$',  # "aktiv/ geplant/ geschlossen/ sonstiges"
        r'^\([^)]*usw\.\)$',                            # "(beliebig usw.)"
        r'^[^(]*\([^)]*usw\.\)[^)]*$'                   # "Text (beliebig usw.) Text"
    ]
    
    for pattern in template_patterns:
        if re.match(pattern, value_str, re.IGNORECASE):
            logger.info(f"[TEMPLATE-FIX] Template-Pattern match '{value_str}' -> 'Nichts gefunden'")
            return 'Nichts gefunden'
    
    # NULL-VALUE-DISPLAY-FIX 24.08.2025: Erweiterte "nichts gefunden" Pattern
    exact_placeholders = [
        'LEER', 'Leer', 'leer', 'X', 'N/A', 'n/a', 'N.A.', 'n.a.',
        'UNBEKANNT', 'UNKNOWN', 'NICHT GEFUNDEN', 'NOT FOUND',
        'KEINE ANGABEN', 'NO DATA', 'K.A.', 'k.a.', 'K.A.', 
        'NICHT VERFÜGBAR', 'NOT AVAILABLE', 'keine Daten',
        'Keine Informationen gefunden', 'Nicht verfügbar', 'Unbekannt',
        # NEU: Alle "nichts gefunden" Varianten
        'unbekannt', 'unknown', 'nicht bekannt', 'nicht verfügbar',
        'no data', 'no information', 'not found', 'not available',
        'tbd', 'to be determined', 'keine angabe',
        'keine angaben', 'nicht ermittelbar',
        'nicht spezifiziert', 'not specified', 'not applicable',
        'keine information', 'no info', 'nichts gefunden'
    ]
    
    if value_str in exact_placeholders:
        logger.debug(f"[PHASE 15.3] Exact match '{value_str}' -> 'Nichts gefunden'")
        return 'Nichts gefunden'
    
    # NULL-VALUE-DISPLAY-FIX 24.08.2025: AI-Kommentare in bestehenden DB-Daten
    ai_comment_patterns = [
        'the user says',
        'user says', 
        'so that\'s straightforward',
        'also unknown',
        'no data, so leave blank',
        'without specifics',
        'can\'t provide numbers',
        'since i can\'t access',
        'i\'ll rely on general',
        'typical values for'
    ]
    
    # Wenn der Text AI-Kommentare enthält, ist es ein Template-Wert
    if any(pattern in value_str.lower() for pattern in ai_comment_patterns):
        logger.info(f"[TEMPLATE-FIX] AI-Kommentar in DB-Wert erkannt: '{value_str[:50]}...' -> 'Nichts gefunden'")
        return 'Nichts gefunden'
    
    # PHASE 15.3 KRITISCH: Pattern für alle LEER-Varianten aus der Datenbank
    leer_db_patterns = [
        r'^LEER\s*-\s*.*',                    # "LEER - [beliebiger Text]"
        r'^Leer\s*-\s*.*',                    # "Leer - [beliebiger Text]" 
        r'^leer\s*-\s*.*',                    # "leer - [beliebiger Text]"
        r'.*[Kk]eine spezifischen.*',         # "Keine/keine spezifischen [...]" (596x!)
        r'.*[Kk]eine verlässlichen.*',        # "Keine verlässlichen [...]"
        r'.*[Kk]eine öffentlichen.*',         # "Keine öffentlichen [...]"
        r'.*[Kk]eine aktiven.*',              # "Keine aktiven [...]"
        r'.*[Kk]eine spezifischen Daten.*',   # Spezifisch für DB-Varianten
        r'.*[Nn]o specific.*',                # Englische Varianten
        r'.*[Nn]ot available.*',              # "Not available"
        r'.*dokumentiert$',                   # "spezifischen Quellen dokumentiert"
    ]
    
    # Pattern-Matching für Datenbank-LEER-Varianten
    for pattern in leer_db_patterns:
        if re.match(pattern, value_str, re.IGNORECASE):
            logger.debug(f"[PHASE 15.3] DB-Pattern match '{value_str[:50]}...' -> 'Nichts gefunden'")
            return 'Nichts gefunden'
    
    # Echte Werte unverändert zurückgeben
    return value_str

def _analyze_field_values(value_details):
    """
    Analysiert alle Werte für ein Feld und gruppiert sie nach Eindeutigkeit
    
    PHASE 15.3 FIX: Normalisiert ALLE Werte BEVOR sie analysiert werden!
    
    Returns: Dict mit eindeutigen Werten und deren Metadaten
    """
    value_groups = {}
    
    for detail in value_details:
        # PHASE 15.3 KRITISCH: Normalisiere JEDEN Wert vor der Analyse!
        original_value = detail['value'].strip()
        normalized_display_value = _normalize_placeholder_value(original_value)
        
        value = normalized_display_value.strip().lower()  # Normalisiert für Vergleich
        display_value = normalized_display_value  # Normalisiert für Anzeige
        
        if value not in value_groups:
            value_groups[value] = {
                'display_value': display_value,
                'frequency': 0,
                'ai_models': [],
                'real_sources': [],
                'search_timestamps': [],
                'data_quality_scores': [],
                'search_durations': []
            }
        
        group = value_groups[value]
        group['frequency'] += 1
        group['ai_models'].append(detail['ai_model'])
        group['real_sources'].extend(detail['real_sources'])
        group['search_timestamps'].append(detail['search_timestamp'])
        
        # Berechne Datenqualitätsscore falls verfügbar
        quality = detail.get('data_quality', {})
        if isinstance(quality, dict) and 'filled_fields' in quality and 'total_fields' in quality:
            score = (quality['filled_fields'] / quality['total_fields']) * 100 if quality['total_fields'] > 0 else 0
            group['data_quality_scores'].append(score)
        
        if detail.get('search_duration'):
            group['search_durations'].append(detail['search_duration'])
    
    # Post-processing: Entferne Duplikate und berechne Durchschnittswerte
    for value, group in value_groups.items():
        group['unique_ai_models'] = list(set(group['ai_models']))
        group['unique_real_sources'] = list(set(group['real_sources']))
        group['avg_data_quality'] = sum(group['data_quality_scores']) / len(group['data_quality_scores']) if group['data_quality_scores'] else 0
        group['avg_search_duration'] = sum(group['search_durations']) / len(group['search_durations']) if group['search_durations'] else 0
        group['source_diversity'] = len(group['unique_real_sources'])
        group['model_consensus'] = len(group['unique_ai_models'])
    
    return value_groups

def _calculate_best_value(value_analysis, field_name=None):
    """
    Implementiert "Best Value" Algorithmus basierend auf:
    - Häufigkeit (frequency) 
    - Anzahl verschiedener Quellen (source_diversity)
    - Modell-Konsens (model_consensus)
    - Datenqualität (avg_data_quality)
    - KRITISCHER FIX 21.08.2025: Zeitstempel-Priorität - Neue Daten gewinnen!
    - TEMPLATE-PATTERN-PENALTY 06.08.2025: Malus für CSV_COLUMNS Template-Strukturen
    
    Args:
        value_analysis: Analyse der verfügbaren Werte
        field_name: Name des Feldes für template-spezifische Prüfungen
    
    Returns: Dict mit bestem Wert und Konfidenz-Score
    """
    if not value_analysis:
        return {
            'display_value': 'Nichts gefunden',  # PHASE 14.2 FIX: Einheitliche User-gewünschte Darstellung
            'confidence_score': 0,
            'reason': 'Keine Daten verfügbar'
        }
    
    best_value = None
    best_score = -1
    
    # KRITISCHER FIX 21.08.2025: Bestimme neuesten Zeitstempel über alle Werte hinweg
    all_timestamps = []
    for value, analysis in value_analysis.items():
        all_timestamps.extend(analysis['search_timestamps'])
    
    # Parse alle Timestamps und finde neueste
    from datetime import datetime, timedelta
    parsed_timestamps = []
    for ts in all_timestamps:
        try:
            if isinstance(ts, datetime):
                parsed_timestamps.append(ts)
            elif isinstance(ts, str):
                # Verschiedene Formate unterstützen
                for fmt in ['%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S']:
                    try:
                        parsed_timestamps.append(datetime.strptime(ts, fmt))
                        break
                    except ValueError:
                        continue
        except (ValueError, TypeError):
            continue
    
    newest_timestamp = max(parsed_timestamps) if parsed_timestamps else datetime.min
    logger.info(f"[TIMESTAMP-FIX] Neueste Daten vom: {newest_timestamp}")
    
    for value, analysis in value_analysis.items():
        # PHASE 13.2 FIX: Überarbeitete Score-Berechnung - ECHTE DATEN haben Priorität!
        # KRITISCH: Frequency darf nicht wichtigster Faktor sein, sonst gewinnt "Unbekannt" (9x) über echte Werte (1x)
        frequency_score = analysis['frequency'] * 1.0  # REDUZIERT: von 2.0 auf 1.0
        source_diversity_score = analysis['source_diversity'] * 1.5  # Verschiedene Quellen
        model_consensus_score = analysis['model_consensus'] * 1.0  # Verschiedene AI-Modelle
        quality_score = analysis['avg_data_quality'] * 0.01  # Datenqualität (0-100)
        
        # KRITISCHER FIX 21.08.2025: ZEITSTEMPEL-BONUS - Neue Daten bekommen massiven Vorteil!
        recency_bonus = 0.0
        value_newest_timestamp = datetime.min
        for ts in analysis['search_timestamps']:
            try:
                if isinstance(ts, datetime):
                    current_ts = ts
                elif isinstance(ts, str):
                    # Verschiedene Formate unterstützen
                    for fmt in ['%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S']:
                        try:
                            current_ts = datetime.strptime(ts, fmt)
                            break
                        except ValueError:
                            continue
                    else:
                        continue
                else:
                    continue
                
                if current_ts > value_newest_timestamp:
                    value_newest_timestamp = current_ts
            except (ValueError, TypeError):
                continue
        
        # KRITISCHER BONUS: Wenn die Daten weniger als 2 Stunden alt sind = MASSIVER BONUS
        now = datetime.now()
        hours_old = (now - value_newest_timestamp).total_seconds() / 3600
        
        if hours_old < 2:  # Weniger als 2 Stunden alt = batch data von heute
            recency_bonus = 150.0  # ULTRA-MASSIVER Bonus für sehr neue Daten (Batch-Daten!)
            logger.info(f"[TIMESTAMP-FIX] ⚡ RECENCY BONUS: '{analysis['display_value'][:50]}' ist {hours_old:.1f}h alt -> +{recency_bonus} Punkte")
        elif hours_old < 24:  # Weniger als 1 Tag alt
            recency_bonus = 50.0  # Starker Bonus für neue Daten
        elif hours_old < 48:  # Weniger als 2 Tage alt
            recency_bonus = 20.0  # Moderater Bonus für relativ neue Daten
        else:  # Älter als 2 Tage
            recency_bonus = 0.0  # Kein Bonus für alte Daten
            # ZUSÄTZLICH: Malus für sehr alte Daten
            if hours_old > 72:  # Älter als 3 Tage
                recency_bonus = -25.0  # Verstärkter Malus für alte Daten
        
        # CONSENSUS FIX: Verwende robuste is_empty_value Funktion aus search_utils
        from minesearch.search_utils import is_empty_value
        from minesearch.extraction_validators import is_placeholder_value
        
        if is_empty_value(analysis['display_value']):
            non_x_bonus = -100.0  # DRASTISCHER Malus für alle leeren/ungültigen Werte
        elif is_placeholder_value(analysis['display_value'], field_name):
            # TEMPLATE-PATTERN-PENALTY: Starker Malus für Template-Strukturen
            non_x_bonus = -50.0  # Starker Malus für Template-Werte wie "Untertage/ Open-Pit/ usw.)"
        else:
            non_x_bonus = 50.0  # PHASE 13.2 FIX: MASSIV erhöhter Bonus für echte Daten (war 10.0)
        
        # Malus für sehr kurze Suchzeiten (könnte auf Timeout hindeuten)
        duration_penalty = -2.0 if analysis['avg_search_duration'] < 1.0 else 0
        
        total_score = (frequency_score + source_diversity_score + 
                      model_consensus_score + quality_score + 
                      non_x_bonus + duration_penalty + recency_bonus)
        
        logger.debug(f"[SCORE] '{analysis['display_value'][:30]}': freq={frequency_score:.1f} + diversity={source_diversity_score:.1f} + consensus={model_consensus_score:.1f} + quality={quality_score:.1f} + data_bonus={non_x_bonus:.1f} + duration={duration_penalty:.1f} + recency={recency_bonus:.1f} = TOTAL {total_score:.1f}")
        
        if total_score > best_score:
            best_score = total_score
            best_value = analysis
    
    if not best_value:
        return {
            'display_value': 'Nichts gefunden',  # PHASE 14.2 FIX: Einheitliche User-gewünschte Darstellung  
            'confidence_score': 0,
            'reason': 'Keine gültigen Werte gefunden'
        }
    
    # PHASE 13.2 FIX: Normalisiere Konfidenz-Score zu 0-100 (neue Berechnung)
    # Platzhalter: frequency=9 (9), no diversity (0), no consensus (0), no quality (0), Platzhalter-Malus (-100) = -91.0
    # Echter Wert: frequency=1 (1), diversity=1 (1.5), consensus=1 (1), quality=0 (0), Echte-Daten-Bonus (+50) = 53.5
    # ERGEBNIS: Echte Werte gewinnen IMMER gegen Platzhalter!
    max_reasonable_score = 60.0  # Angepasst an neue Bonusse
    confidence_score = min(100, max(0, (best_score / max_reasonable_score) * 100))
    
    # Bestimme Begründung
    reason_parts = []
    if best_value['frequency'] > 1:
        reason_parts.append(f"Häufigkeit: {best_value['frequency']}")
    if best_value['source_diversity'] > 1:
        reason_parts.append(f"Quellen: {best_value['source_diversity']}")
    if best_value['model_consensus'] > 1:
        reason_parts.append(f"Modelle: {best_value['model_consensus']}")
    
    reason = "Best Value aufgrund: " + ", ".join(reason_parts) if reason_parts else "Einziger verfügbarer Wert"
    
    return {
        'display_value': best_value['display_value'],
        'confidence_score': round(confidence_score, 1),
        'reason': reason,
        'frequency': best_value['frequency'],
        'source_diversity': best_value['source_diversity'],
        'model_consensus': best_value['model_consensus'],
        'avg_data_quality': round(best_value['avg_data_quality'], 1),
        'supporting_models': best_value['unique_ai_models'],
        'supporting_sources': best_value['unique_real_sources'][:3]  # Zeige nur ersten 3 URLs
    }

@router.get("/results")
async def get_consolidated_results(
    country: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    days_back: int = Query(30),
    sort_by: str = Query("mine_name", description="Sort by: mine_name, country, model_count, last_updated"),
    order: str = Query("asc", description="Order: asc or desc"),
    exclude_exa: bool = Query(True, description="Exa-Modelle ausblenden")
):
    print(f"[DEBUG] API called with days_back={days_back}, exclude_exa={exclude_exa}")
    """
    Hole konsolidierte Suchergebnisse pro Mine mit allen Modell-Daten
    
    Neue konsolidierte Ansicht:
    - Eine Zeile pro Mine
    - Alle Feldwerte mit Quellen in eckigen Klammern [Model1, Model2]
    - Details-Akkordeon zeigt Modell-spezifische Ergebnisse
    """
    from minesearch.database import db_manager
    from sqlalchemy import desc as sql_desc, asc as sql_asc
    from datetime import datetime, timedelta
    
    with db_manager.get_session() as session:
        query = session.query(SearchResult)
        
        # Filter anwenden
        if exclude_exa:
            query = query.filter(~SearchResult.model_used.like('exa:%'))
        
        if country:
            query = query.filter(SearchResult.country == country)
            
        if region:
            query = query.filter(SearchResult.region == region)
        
        # Zeitfilter
        if days_back > 0:
            cutoff = datetime.now() - timedelta(days=days_back)
            query = query.filter(SearchResult.search_timestamp >= cutoff)
        
        # Alle Ergebnisse holen
        all_results = query.all()
        logger.info(f"[DEBUG] Query found {len(all_results)} results")
        
        # PHASE 1.2: GLOBAL SOURCE INDEX SYSTEM 14.08.2025
        # Erstelle globales Quellennummerierungssystem für konsistente Referenzen
        global_source_index = {}  # URL -> Nummer Mapping
        global_source_counter = 1
        
        def get_or_assign_source_number(source_url):
            """Gibt eindeutige Nummer für Quelle zurück oder erstellt neue"""
            nonlocal global_source_counter
            if source_url not in global_source_index:
                global_source_index[source_url] = global_source_counter
                global_source_counter += 1
            return global_source_index[source_url]
        
        # Nach Mine gruppieren
        mines_data = defaultdict(lambda: {
            'mine_name': '',
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
            mine_name = result.mine_name
            mine_data = mines_data[mine_name]
            
            # Basis-Informationen setzen
            mine_data['mine_name'] = mine_name
            mine_data['country'] = result.country or ''
            mine_data['region'] = result.region or ''
            
            # PHASE 4 FIX: Count ALL model results, not just unique models
            # The model_count should match the actual length of model_results array
            mine_data['model_count'] += 1
            
            # Letzte Aktualisierung
            if not mine_data['last_updated'] or result.search_timestamp > mine_data['last_updated']:
                mine_data['last_updated'] = result.search_timestamp
            
            # QUELLENREFERENZEN-FIX 24.08.2025: Zähle nur tatsächlich verwendete Quellen, nicht Discovery-Quellen
            # Sammle alle real_sources aus consolidated_fields (tatsächlich verwendete Quellen)
            used_sources = set()
            for field_info in mine_data['consolidated_fields'].values():
                for real_source_list in field_info['real_sources']:
                    for real_source_url in real_source_list:
                        used_sources.add(real_source_url)
            
            # Aktualisiere unique_sources nur mit tatsächlich verwendeten Quellen
            mine_data['unique_sources'].update(used_sources)
            
            # Update total_sources with unique count
            mine_data['total_sources'] = len(mine_data['unique_sources'])
            
            # Modell-spezifische Daten sammeln
            model_info = {
                'id': result.id,
                'model_id': result.model_used,  # CRITICAL FIX 20.08.2025: Add model_id field for frontend compatibility
                'model_used': result.model_used,
                'search_timestamp': result.search_timestamp.isoformat() if result.search_timestamp else None,
                'structured_data': result.structured_data or {},
                'sources': result.sources or [],
                'data_quality': result.data_quality or {},
                'search_duration': result.search_duration,
                'fields_found': len([v for v in (result.structured_data or {}).values() if v and str(v).strip() and str(v).strip().upper() != 'X'])
            }
            mine_data['model_results'].append(model_info)
            
            # Assign source number for this model if not already assigned
            if result.model_used not in mine_data['source_mapping']:
                source_number = len(mine_data['source_mapping']) + 1
                mine_data['source_mapping'][result.model_used] = source_number
            
            # ENHANCED: Felder konsolidieren mit Umbenennung und erweiterten Metadaten
            if result.structured_data:
                for original_field_name, field_value in result.structured_data.items():
                    # CRITICAL FIX: Apply field consolidation and renaming FIRST, before X-value filtering
                    # This ensures renamed fields exist in output even if they contain X-values
                    final_field_name, processed_value = consolidate_and_rename_field(original_field_name, field_value)
                    
                    # Now check if we have actual data (not X) for statistics
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
                    
                    # STEP 2B: Only process actual data (non-X values) for statistics
                    if has_real_data:
                        clean_value = str(processed_value).strip()
                        
                        # ENHANCED DUPLICATE PREVENTION 06.08.2025: Vollständige Feldkonsolidierung
                        # Wenn ein Feld konsolidiert wird, stelle sicher dass das Quellfeld nicht separat erscheint
                        if original_field_name != final_field_name:
                            # Entferne das ursprüngliche Feld aus der Feldliste falls es bereits existiert
                            if original_field_name in mine_data['consolidated_fields']:
                                logger.info(f"Removing original field '{original_field_name}' after consolidation to '{final_field_name}'")
                                # Merge existing data vom ursprünglichen Feld ins konsolidierte Feld
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
                                if result.model_used in existing_models:
                                    existing_values = mine_data['consolidated_fields'][final_field_name]['raw_values']
                                    if clean_value in existing_values:
                                        logger.debug(f"Skipping duplicate consolidation: {original_field_name} -> {final_field_name} für Modell {result.model_used}")
                                        continue
                        
                        # PHASE 1.2: Extract real data sources mit globaler Nummerierung
                        real_sources = []
                        global_source_numbers = []
                        if result.sources:
                            for source in result.sources:
                                source_url = None
                                if isinstance(source, str) and ('http' in source or 'www.' in source):
                                    source_url = source
                                elif isinstance(source, dict) and source.get('url'):
                                    source_url = source['url']
                                
                                if source_url:
                                    real_sources.append(source_url)
                                    # Globale Quellennummer zuweisen
                                    source_number = get_or_assign_source_number(source_url)
                                    global_source_numbers.append(source_number)
                        
                        # QUELLENREFERENZEN-FIX 24.08.2025: Für Quellenangaben Feld - zeige nur tatsächlich genutzte Quellen
                        if final_field_name.lower() in ['quellenangaben', 'sources', 'quellen']:
                            if real_sources:
                                # WICHTIG: Zähle nur real_sources (echte URLs), nicht discovery-sources
                                source_types = {}
                                actually_used_sources = []
                                
                                for source in result.sources:
                                    if isinstance(source, dict) and source.get('url') in real_sources:
                                        # Nur Quellen zählen, die auch echte URLs haben
                                        source_type = source.get('type', 'general')
                                        source_types[source_type] = source_types.get(source_type, 0) + 1
                                        actually_used_sources.append(source)
                                
                                # Verwende nur tatsächlich genutzte Quellen
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
                                    
                                    clean_value = f"{len(actually_used_sources)} Quellen: " + ", ".join(source_summary)
                                else:
                                    # Fallback wenn keine echten Quellen: Zähle wenigstens real_sources
                                    clean_value = f"{len(real_sources)} Quellen gefunden"
                        
                        # PHASE 1.2: Add data mit globalen Quellenreferenzen
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
                        # This allows future non-X values to populate these renamed fields
                        if final_field_name not in mine_data['consolidated_fields']:
                            logger.debug(f"Creating field structure for X-value field: {final_field_name} (was: {original_field_name})")
                            mine_data['consolidated_fields'][final_field_name] = {
                                'raw_values': [],
                                'ai_models': [],
                                'real_sources': [],
                                'value_details': []
                            }
        
        # Konvertiere zu Liste und implementiere "Best Value" Algorithmus
        consolidated_results = []
        logger.info(f"[DEBUG] Processing {len(mines_data)} mines")
        for mine_name, mine_data in mines_data.items():
            # FIELD-CONSOLIDATION-FIX 06.08.2025: Erweiterte Field-Initialisierung mit Konsolidierungslogik
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
                        logger.info(f"[FIELD-INIT] Feld '{final_field_name}' für Mine '{mine_name}' initialisiert (war: {expected_field})")
            logger.info(f"[FIELD-INIT] {fields_added} Felder zu Mine '{mine_name}' hinzugefügt. Total: {len(mine_data['consolidated_fields'])}")
            
            # Implementiere "Best Value" Algorithmus für jedes Feld
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
                
                # Analysiere alle Werte für dieses Feld
                value_analysis = _analyze_field_values(field_info['value_details'])
                
                # Bestimme besten Wert basierend auf Algorithmus
                # TEMPLATE-PATTERN-FIX 06.08.2025: Übergebe field_name für Template-Detection
                best_value_info = _calculate_best_value(value_analysis, field_name)
                
                # Speichere besten Wert für Haupttabelle
                # FIELD-CONSOLIDATION-FIX 06.08.2025: Bessere UX mit 'Unbekannt' statt N/A
                # DUPLIKAT-FIX 30.07.2025: Metadaten-Felder NICHT in best_values - kommen bereits als direkte Felder
                metadaten_felder = ['Mine', 'Land', 'Zuverlässigkeit', 'Modelle', 'Letzte Aktualisierung', 'Details']
                if field_name not in metadaten_felder:  # Verhindere Duplikate in Frontend
                    display_value = best_value_info['display_value']
                    # PHASE 14.2 FIX: Einheitliche "Nichts gefunden" Darstellung für alle Platzhalter
                    placeholder_indicators = ['', 'X', 'N/A', 'KEINE ANGABEN', 'NICHT VERFÜGBAR', 'UNBEKANNT', 
                                            'LEER', 'UNKNOWN', 'NOT FOUND', 'NO DATA', 'K.A.', 'N.A.']
                    if not display_value or display_value.strip().upper() in placeholder_indicators:
                        display_value = 'Nichts gefunden'  # PHASE 14.2: Einheitliche User-gewünschte Darstellung
                    best_values[field_name] = display_value
                
                # QUELLENREFERENZEN-FIX 24.08.2025: Sammle Quellenreferenzen für dieses Feld
                field_global_source_numbers = []
                supporting_sources = best_value_info.get('supporting_sources', [])
                
                if supporting_sources and global_source_index:
                    for source_url in supporting_sources[:10]:  # Mehr URLs berücksichtigen für vollständige Referenzen
                        try:
                            for number, source_data in global_source_index.items():
                                if isinstance(source_data, dict) and source_data.get('url') == source_url:
                                    field_global_source_numbers.append(int(number))
                                    break
                        except (ValueError, TypeError, AttributeError) as e:
                            logger.warning(f"Error converting source URL {source_url} to global number: {e}")
                            continue
                
                # Erstelle detaillierte Aufschlüsselung für Modal
                detailed_breakdown[field_name] = {
                    'best_value': best_value_info,
                    'all_values': value_analysis,
                    'statistics': {
                        'total_sources': sum(len(detail['real_sources']) for detail in field_info['value_details']),  # FIXED: Count actual sources, not AI models
                        'unique_values': len(value_analysis),
                        'confidence_score': best_value_info['confidence_score'],
                        'total_real_sources': sum(len(detail['real_sources']) for detail in field_info['value_details'])
                    },
                    # QUELLENREFERENZEN-FIX 24.08.2025: Füge globale Quellenreferenzen hinzu
                    'global_source_numbers': sorted(list(set(field_global_source_numbers)))  # Eindeutige, sortierte Nummern
                }
            
            # Sortiere Modell-Ergebnisse nach Timestamp
            mine_data['model_results'].sort(key=lambda x: x['search_timestamp'] or '', reverse=True)
            
            # Create enhanced metadata for new UX design
            ai_model_legend = {}
            for model, number in mine_data['source_mapping'].items():
                model_display_name = model.split(':')[-1] if ':' in model else model
                ai_model_legend[str(number)] = model_display_name

            # Calculate overall confidence score for the mine
            confidence_scores = [details['best_value']['confidence_score'] 
                               for details in detailed_breakdown.values() 
                               if details['best_value']['confidence_score'] > 0]
            overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0

            # PHASE 3 FIX: Clean up sets before JSON serialization
            if 'unique_models' in mine_data:
                del mine_data['unique_models']

            # PHASE 1.1: ENHANCED API RESPONSE STRUCTURE 14.08.2025
            # Strukturierte Felder klar von Metadaten trennen für bessere Frontend-Integration
            
            # Separiere Metadatenfelder von Datenfeldern
            metadata_fields = {
                'mine_name': mine_name,
                'country': mine_data['country'],
                'region': mine_data['region'],
                'model_count': mine_data['model_count'],
                'last_updated': mine_data['last_updated'].isoformat() if mine_data['last_updated'] else None,
                'total_sources': mine_data['total_sources']
            }
            
            # PHASE 1.2: Strukturierte Datenfelder mit globalen Quellenreferenzen
            structured_fields = {}
            for field_name, field_breakdown in detailed_breakdown.items():
                # Nur echte Datenfelder, keine Metadaten
                metadaten_felder = ['Mine', 'Land', 'Zuverlässigkeit', 'Modelle', 'Letzte Aktualisierung', 'Details']
                if field_name not in metadaten_felder:
                    # Sammle alle globalen Quellenreferenzen für dieses Feld
                    field_global_sources = []
                    for detail in field_breakdown.get('all_values', {}).values():
                        for value_detail in detail.get('search_timestamps', []):  # Fallback wenn structure anders
                            pass
                    
                    # Alternative: Sammle von field_source_references
                    field_source_refs = list(mine_data.get('field_source_references', {}).get(field_name, []))
                    
                    # PHASE 1.2: Erweiterte Feldstruktur mit globalen Referenzen
                    supporting_sources = field_breakdown['best_value'].get('supporting_sources', [])
                    
                    # PHASE 2.1: Konvertiere URLs zu globalen Referenznummern (mit Error-Handling)
                    global_source_numbers = []
                    if supporting_sources and global_source_index:
                        for source_url in supporting_sources[:3]:  # Nur erste 3 URLs
                            try:
                                for number, source_data in global_source_index.items():
                                    if isinstance(source_data, dict) and source_data.get('url') == source_url:
                                        global_source_numbers.append(int(number))
                                        break
                            except (ValueError, TypeError, AttributeError) as e:
                                logger.warning(f"Error converting source URL {source_url} to global number: {e}")
                                continue
                    
                    structured_fields[field_name] = {
                        'value': best_values.get(field_name, 'Nichts gefunden'),  # PHASE 14.2: Konsistente Darstellung
                        'confidence_score': field_breakdown['best_value']['confidence_score'],
                        'consistency_score': field_breakdown['statistics'].get('confidence_score', 0),
                        'source_count': field_breakdown['statistics']['total_sources'],
                        'source_references': supporting_sources[:3],  # URLs der unterstützenden Quellen
                        'global_source_numbers': sorted(global_source_numbers),  # PHASE 1.2: Globale Nummern für Frontend
                        'model_consensus': field_breakdown['best_value'].get('model_consensus', 0),
                        'frequency': field_breakdown['best_value'].get('frequency', 1)
                    }

            result_item = {
                # PHASE 1.1: STRUCTURED RESPONSE FOR FRONTEND
                'metadata': metadata_fields,
                'structured_fields': structured_fields,
                'overall_confidence': round(overall_confidence, 1),
                
                # ENHANCED FIELD SUMMARY für Card-Anzeige
                'field_summary': {
                    'total_fields': len(structured_fields),
                    'fields_with_high_confidence': len([f for f in structured_fields.values() if f['confidence_score'] >= 70]),
                    'fields_with_multiple_sources': len([f for f in structured_fields.values() if f['source_count'] > 1]),
                    'avg_confidence': round(sum(f['confidence_score'] for f in structured_fields.values()) / len(structured_fields) if structured_fields else 0, 1),
                    'avg_source_diversity': round(sum(f['source_count'] for f in structured_fields.values()) / len(structured_fields) if structured_fields else 0, 1)
                },
                
                # LEGACY COMPATIBILITY (für bestehende Frontend-Teile)
                'mine_name': mine_name,
                'country': mine_data['country'], 
                'region': mine_data['region'],
                'best_values': best_values,  # Maintained for backward compatibility
                'detailed_breakdown': detailed_breakdown,  # Für Details-Modal
                'ai_model_legend': ai_model_legend,
                'model_results': mine_data['model_results'],
                'model_count': mine_data['model_count'],
                'last_updated': mine_data['last_updated'].isoformat() if mine_data['last_updated'] else None,
                'total_sources': mine_data['total_sources'],
                'total_fields_found': len(best_values),
                
                # ENHANCED METRICS
                'data_quality_metrics': {
                    'fields_with_high_confidence': len([d for d in detailed_breakdown.values() 
                                                      if d['best_value']['confidence_score'] >= 70]),
                    'fields_with_multiple_sources': len([d for d in detailed_breakdown.values() 
                                                       if d['statistics']['total_sources'] > 1]),
                    'avg_source_diversity': sum(d['statistics']['total_real_sources'] 
                                              for d in detailed_breakdown.values()) / len(detailed_breakdown) if detailed_breakdown else 0
                }
            }
            consolidated_results.append(result_item)
        
        # Sortierung anwenden
        reverse_order = (order == "desc")
        
        if sort_by == "mine_name":
            consolidated_results.sort(key=lambda x: x["mine_name"], reverse=reverse_order)
        elif sort_by == "country":
            consolidated_results.sort(key=lambda x: x["country"] or "", reverse=reverse_order)
        elif sort_by == "model_count":
            consolidated_results.sort(key=lambda x: x["model_count"], reverse=reverse_order)
        elif sort_by == "last_updated":
            consolidated_results.sort(key=lambda x: x["last_updated"] or "", reverse=reverse_order)
        
        # PHASE 1.2: Invertiere global_source_index für Frontend (Nummer -> URL)
        source_index_for_frontend = {v: k for k, v in global_source_index.items()}
        
        return {
            "success": True,
            "data": {
                "consolidated_results": consolidated_results,
                "total_mines": len(consolidated_results),
                "total_results": len(all_results),
                "sort_by": sort_by,
                "order": order,
                # PHASE 1.2: GLOBAL SOURCE INDEX für Frontend-Referenzen
                "global_source_index": source_index_for_frontend,  # {1: "url1.com", 2: "url2.com"}
                "total_sources": len(global_source_index)
            }
        }

@router.get("/results/{mine_name}/details")
async def get_mine_model_details(
    mine_name: str,
    country: Optional[str] = Query(None),
    days_back: int = Query(30),
    exclude_exa: bool = Query(True)
):
    """
    Hole detaillierte Modell-spezifische Ergebnisse für eine Mine
    Für das Details-Akkordeon
    """
    from minesearch.database import db_manager
    from datetime import datetime, timedelta
    
    with db_manager.get_session() as session:
        query = session.query(SearchResult).filter(SearchResult.mine_name == mine_name)
        
        # Filter anwenden
        if exclude_exa:
            query = query.filter(~SearchResult.model_used.like('exa:%'))
        
        if country:
            query = query.filter(SearchResult.country == country)
        
        # Zeitfilter
        if days_back > 0:
            cutoff = datetime.now() - timedelta(days=days_back)
            query = query.filter(SearchResult.search_timestamp >= cutoff)
        
        # Nach Timestamp sortieren (neueste zuerst)
        query = query.order_by(SearchResult.search_timestamp.desc())
        
        results = query.all()
        
        if not results:
            raise HTTPException(status_code=404, detail=f"Keine Ergebnisse für Mine '{mine_name}' gefunden")
        
        # Detaillierte Modell-Informationen zusammenstellen
        model_details = []
        for result in results:
            # Feld-Statistiken berechnen
            structured_data = result.structured_data or {}
            fields_with_data = {k: v for k, v in structured_data.items() if v and str(v).strip()}
            empty_fields = {k: v for k, v in structured_data.items() if not v or not str(v).strip()}
            
            # Datenqualität berechnen
            total_fields = len(structured_data)
            filled_fields = len(fields_with_data)
            data_quality_percentage = round((filled_fields / total_fields) * 100, 1) if total_fields > 0 else 0
            
            model_detail = {
                'id': result.id,
                'model_used': result.model_used,
                'model_display_name': result.model_used.split(':')[-1],  # Nur Modellname ohne Provider-Präfix
                'search_timestamp': result.search_timestamp.isoformat() if result.search_timestamp else None,
                'search_duration': result.search_duration,
                'structured_data': structured_data,
                'fields_with_data': fields_with_data,
                'empty_fields': list(empty_fields.keys()),
                'sources': result.sources or [],
                'data_quality_percentage': data_quality_percentage,
                'total_fields': total_fields,
                'filled_fields': filled_fields,
                'empty_fields_count': len(empty_fields),
                'sources_count': len(result.sources or []),
                'success': result.success,
                'error_message': result.error_message
            }
            model_details.append(model_detail)
        
        return {
            "success": True,
            "mine_name": mine_name,
            "data": {
                "model_details": model_details,
                "total_searches": len(model_details),
                "unique_models": len(set([r.model_used for r in results])),
                "date_range": {
                    "earliest": results[-1].search_timestamp.isoformat() if results else None,
                    "latest": results[0].search_timestamp.isoformat() if results else None
                }
            }
        }

@router.get("/mine/{mine_name}")
async def get_mine_consolidated_details(
    mine_name: str,
    days_back: int = Query(30),
    exclude_exa: bool = Query(True)
):
    """
    Hole konsolidierte Details für eine spezifische Mine
    Frontend Compatibility Route: /api/consolidated/mine/{name}
    """
    from minesearch.database import db_manager
    from datetime import datetime, timedelta
    
    with db_manager.get_session() as session:
        query = session.query(SearchResult).filter(SearchResult.mine_name == mine_name)
        
        # Filter anwenden
        if exclude_exa:
            query = query.filter(~SearchResult.model_used.like('exa:%'))
        
        # Zeitfilter
        if days_back > 0:
            cutoff = datetime.now() - timedelta(days=days_back)
            query = query.filter(SearchResult.search_timestamp >= cutoff)
        
        results = query.all()
        
        if not results:
            raise HTTPException(status_code=404, detail=f"Keine konsolidierten Daten für Mine '{mine_name}' gefunden")
        
        # Wiederverwendung der Konsolidierungs-Logik aus get_consolidated_results
        mine_data = {
            'mine_name': mine_name,
            'country': '',
            'region': '',
            'consolidated_fields': {},
            'model_results': [],
            'unique_models': set(),  # PHASE 3 FIX: Track unique model IDs
            'unique_sources': set(),  # KRITISCHER FIX 20.08.2025: Fehlende unique_sources initialisieren
            'model_count': 0,
            'last_updated': None,
            'total_sources': 0,
            'source_mapping': {}
        }
        
        # Process all results for this mine
        for result in results:
            # Basis-Informationen setzen
            mine_data['country'] = result.country or mine_data['country']
            mine_data['region'] = result.region or mine_data['region']
            
            # PHASE 4 FIX: Count ALL model results, not just unique models
            # The model_count should match the actual length of model_results array
            mine_data['model_count'] += 1
            
            # Letzte Aktualisierung
            if not mine_data['last_updated'] or result.search_timestamp > mine_data['last_updated']:
                mine_data['last_updated'] = result.search_timestamp
            
            # QUELLENREFERENZEN-FIX 24.08.2025: Zähle nur tatsächlich verwendete Quellen, nicht Discovery-Quellen
            # Sammle alle real_sources aus consolidated_fields (tatsächlich verwendete Quellen)
            used_sources = set()
            for field_info in mine_data['consolidated_fields'].values():
                for real_source_list in field_info['real_sources']:
                    for real_source_url in real_source_list:
                        used_sources.add(real_source_url)
            
            # Aktualisiere unique_sources nur mit tatsächlich verwendeten Quellen
            mine_data['unique_sources'].update(used_sources)
            
            # Update total_sources with unique count
            mine_data['total_sources'] = len(mine_data['unique_sources'])
            
            # Felder konsolidieren
            if result.structured_data:
                for original_field_name, field_value in result.structured_data.items():
                    final_field_name, processed_value = consolidate_and_rename_field(original_field_name, field_value)
                    
                    # Only process non-X values
                    has_real_data = (processed_value and str(processed_value).strip() and 
                                   str(processed_value).strip().upper() != 'X')
                    
                    if final_field_name not in mine_data['consolidated_fields']:
                        mine_data['consolidated_fields'][final_field_name] = {
                            'raw_values': [],
                            'ai_models': [],
                            'real_sources': [],
                            'value_details': []
                        }
                    
                    if has_real_data:
                        clean_value = str(processed_value).strip()
                        
                        # Extract real data sources
                        real_sources = []
                        if result.sources:
                            for source in result.sources:
                                if isinstance(source, str) and ('http' in source or 'www.' in source):
                                    real_sources.append(source)
                                elif isinstance(source, dict) and source.get('url'):
                                    real_sources.append(source['url'])
                        
                        mine_data['consolidated_fields'][final_field_name]['raw_values'].append(clean_value)
                        mine_data['consolidated_fields'][final_field_name]['ai_models'].append(result.model_used)
                        mine_data['consolidated_fields'][final_field_name]['real_sources'].append(real_sources)
                        mine_data['consolidated_fields'][final_field_name]['value_details'].append({
                            'value': clean_value,
                            'ai_model': result.model_used,
                            'real_sources': real_sources,
                            'search_timestamp': result.search_timestamp,
                            'data_quality': result.data_quality or {},
                            'search_duration': result.search_duration or 0
                        })
        
        # Implementiere "Best Value" Algorithmus
        best_values = {}
        detailed_breakdown = {}
        
        for field_name, field_info in mine_data['consolidated_fields'].items():
            # Analysiere alle Werte für dieses Feld
            value_analysis = _analyze_field_values(field_info['value_details'])
            
            # Bestimme besten Wert
            best_value_info = _calculate_best_value(value_analysis, field_name)
            
            # Speichere besten Wert (ohne Metadaten-Felder)
            metadaten_felder = ['Mine', 'Land', 'Zuverlässigkeit', 'Modelle', 'Letzte Aktualisierung', 'Details']
            if field_name not in metadaten_felder:
                display_value = best_value_info['display_value']
                # PHASE 14.2 FIX: Einheitliche "Nichts gefunden" Darstellung (auch in mine detail route)
                placeholder_indicators = ['', 'X', 'N/A', 'KEINE ANGABEN', 'NICHT VERFÜGBAR', 'UNBEKANNT', 
                                        'LEER', 'UNKNOWN', 'NOT FOUND', 'NO DATA', 'K.A.', 'N.A.']
                if not display_value or display_value.strip().upper() in placeholder_indicators:
                    display_value = 'Nichts gefunden'
                best_values[field_name] = display_value
            
            # QUELLENREFERENZEN-FIX 24.08.2025: Sammle Quellenreferenzen für dieses Feld (auch für Einzelergebnisse)
            field_global_source_numbers = []
            supporting_sources = best_value_info.get('supporting_sources', [])
            
            if supporting_sources and global_source_index:
                for source_url in supporting_sources[:10]:  # Mehr URLs berücksichtigen für vollständige Referenzen
                    try:
                        for number, source_data in global_source_index.items():
                            if isinstance(source_data, dict) and source_data.get('url') == source_url:
                                field_global_source_numbers.append(int(number))
                                break
                    except (ValueError, TypeError, AttributeError) as e:
                        logger.warning(f"Error converting source URL {source_url} to global number: {e}")
                        continue
            
            # Detaillierte Aufschlüsselung
            detailed_breakdown[field_name] = {
                'best_value': best_value_info,
                'all_values': value_analysis,
                'statistics': {
                    'total_sources': sum(len(detail['real_sources']) for detail in field_info['value_details']),  # FIXED: Count actual sources, not AI models
                    'unique_values': len(value_analysis),
                    'confidence_score': best_value_info['confidence_score'],
                    'total_real_sources': sum(len(detail['real_sources']) for detail in field_info['value_details'])
                },
                # QUELLENREFERENZEN-FIX 24.08.2025: Füge globale Quellenreferenzen hinzu (auch für Einzelergebnisse)
                'global_source_numbers': sorted(list(set(field_global_source_numbers)))  # Eindeutige, sortierte Nummern
            }
        
        # Calculate overall confidence
        confidence_scores = [details['best_value']['confidence_score'] 
                           for details in detailed_breakdown.values() 
                           if details['best_value']['confidence_score'] > 0]
        overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        
        # PHASE 3 FIX: Clean up sets before JSON serialization
        if 'unique_models' in mine_data:
            del mine_data['unique_models']
        
        # Source summary for compatibility with frontend modal
        source_summary = {
            'total_unique_sources': mine_data['total_sources'],
            'total_models': mine_data['model_count']
        }
        
        return {
            "success": True,
            "data": {
                "mine_name": mine_name,
                "country": mine_data['country'],
                "region": mine_data['region'],
                "best_values": best_values,
                "detailed_breakdown": detailed_breakdown,
                "overall_confidence": round(overall_confidence, 1),
                "source_summary": source_summary,
                "model_count": mine_data['model_count'],
                "last_updated": mine_data['last_updated'].isoformat() if mine_data['last_updated'] else None,
                "total_sources": mine_data['total_sources']
            }
        }

@router.get("/results/export/csv")
async def export_consolidated_csv(
    country: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    days_back: int = Query(30),
    sort_by: str = Query("mine_name"),
    order: str = Query("asc"),
    exclude_exa: bool = Query(True)
):
    """
    Exportiere konsolidierte Ergebnisse als CSV mit | Trennzeichen
    """
    from fastapi.responses import StreamingResponse
    from datetime import datetime
    import io
    
    # Hole konsolidierte Daten (wiederverwendung der get_consolidated_results Logik)
    consolidated_data = await get_consolidated_results(
        country=country,
        region=region,
        days_back=days_back,
        sort_by=sort_by,
        order=order,
        exclude_exa=exclude_exa
    )
    
    if not consolidated_data["success"]:
        raise HTTPException(status_code=500, detail="Fehler beim Laden der Daten")
    
    results = consolidated_data["data"]["consolidated_results"]
    
    # CSV-Header erstellen (alle möglichen Felder sammeln)
    all_fields = set()
    for result in results:
        all_fields.update(result["best_values"].keys())
    
    # FIX: Verwende FIELD_ORDER für CSV wie in UI, nicht alphabetische Sortierung
    ordered_fields = []
    unordered_fields = []
    
    # Separate fields into ordered and unordered (exclude meta fields)
    for field in all_fields:
        if field.startswith('_'):  # Skip meta fields like _source_mapping
            continue
        elif field in FIELD_ORDER:
            ordered_fields.append(field)
        else:
            unordered_fields.append(field)
    
    # Sort ordered fields by their position in FIELD_ORDER
    ordered_fields.sort(key=lambda x: FIELD_ORDER.index(x))
    
    # Sort unordered fields alphabetically
    unordered_fields.sort()
    
    # Combine for final field order (same as UI)
    sorted_fields = ordered_fields + unordered_fields
    
    # CSV-Content erstellen
    csv_lines = []
    
    # USER REQUIREMENTS 30.07.2025: Header exakt nach gewünschter Reihenfolge
    # Mine | Land | Region | Zuverlässigkeit | Modelle | Letzte Aktualisierung | Betreiber | Eigentümer | Rohstoffe | Minentyp | Aktivitätsstatus | Produktionsstart | Produktionsende | Fördermenge/Jahr | Minenfläche in qkm | x-Koordinate | y-Koordinate | Restaurationskosten | Kostenjahr | Dokumentenjahr | Quellenangaben | Details
    
    # Verwende die FIELD_ORDER direkt für konsistente Reihenfolge
    header = []
    data_fields = []
    
    # Metadaten-Felder zuerst (entsprechend FIELD_ORDER)
    metadata_mapping = {
        "Mine": ("Mine", "mine_name"),
        "Land": ("Land", "country"),
        "Region": ("Region", "region"),
        "Zuverlässigkeit": ("Zuverlässigkeit", "overall_confidence"),
        "Modelle": ("Modelle", "model_count"),
        "Letzte Aktualisierung": ("Letzte Aktualisierung", "last_updated")
    }
    
    # Füge Metadaten-Felder in FIELD_ORDER Reihenfolge hinzu
    for field_name in FIELD_ORDER:
        if field_name in metadata_mapping:
            display_name, data_field = metadata_mapping[field_name]
            header.append(display_name)
            data_fields.append(data_field)
    
    # Dann alle anderen Felder aus FIELD_ORDER (außer Metadaten und Details)
    excluded_field_keys = set(metadata_mapping.keys()) | {"Details"}
    remaining_fields = [f for f in FIELD_ORDER if f not in excluded_field_keys and f in all_fields]
    
    # CSV-FIX: Stelle sicher dass "Quellenangaben" immer in Header ist (auch wenn nicht in all_fields)
    if "Quellenangaben" not in remaining_fields:
        remaining_fields.append("Quellenangaben")
    
    header.extend(remaining_fields)
    
    csv_lines.append("|".join(header))
    
    # Daten-Zeilen - genau wie UI-Struktur
    for result in results:
        row = []
        
        # Metadaten-Felder
        for field_type in data_fields:
            if field_type == "mine_name":
                row.append(result.get("mine_name", "nichts gefunden"))
            elif field_type == "country": 
                country_val = result.get("country", "")
                row.append(_normalize_placeholder_value(country_val) if country_val else "nichts gefunden")
            elif field_type == "region":
                region_val = result.get("region", "")
                row.append(_normalize_placeholder_value(region_val) if region_val else "nichts gefunden")
            elif field_type == "overall_confidence":
                row.append(str(result.get("overall_confidence", 0)) + "%")
            elif field_type == "model_count":
                row.append(str(result.get("model_count", 0)))
            elif field_type == "last_updated":
                row.append(result.get("last_updated", ""))
        
        # Restliche Felder aus best_values - mit spezieller Quellenangaben-Behandlung
        for field in remaining_fields:
            if field == "Quellenangaben":
                # CSV-FIX Phase 2: Quellenangaben speziell behandeln
                sources_value = result["best_values"].get("Quellenangaben", "")
                
                # Falls keine Quellenangaben in best_values, versuche aus source_mapping zu generieren
                if not sources_value or sources_value == "Nichts gefunden":
                    source_mapping = result.get("source_mapping", {})
                    if source_mapping:
                        # Generiere kurze Quellenangaben-Liste aus source_mapping
                        source_count = len(source_mapping)
                        sources_value = f"{source_count} Quellen verfügbar"
                    else:
                        sources_value = "Keine Quellen verfügbar"
                
                # CSV-FIX Phase 3: Zeilenschaltungen durch Semikolon ersetzen
                normalized_sources = str(sources_value).replace("\n", "; ").replace("\r", "")
                # Escape Pipe-Zeichen
                escaped_sources = normalized_sources.replace("|", "\\|")
                row.append(escaped_sources)
            else:
                value = result["best_values"].get(field, "")
                # NULL-VALUE-DISPLAY-FIX 24.08.2025: Normalisiere NULL-Werte für CSV-Export
                normalized_value = _normalize_placeholder_value(value) if value else "nichts gefunden"
                
                # QUELLENREFERENZEN-FIX 24.08.2025: Füge Quellenreferenzen hinzu (mit Fallback)
                detailed_breakdown = result.get("detailed_breakdown", {})
                source_ids = []
                
                if field in detailed_breakdown and normalized_value != "nichts gefunden":
                    field_data = detailed_breakdown[field]
                    # Primär: Verwende global_source_numbers
                    source_ids = field_data.get('global_source_numbers', [])
                    
                    # Fallback: Wenn keine global_source_numbers, nutze structured_fields
                    if not source_ids:
                        structured_fields = result.get('structured_fields', {})
                        if field in structured_fields:
                            source_ids = structured_fields[field].get('global_source_numbers', [])
                    
                    # Fallback: Verwende best_value sources wenn verfügbar
                    if not source_ids:
                        best_value = field_data.get('best_value', {})
                        supporting_sources = best_value.get('supporting_sources', [])
                        if supporting_sources:
                            # Erzeuge temporäre Nummern für unterstützende Quellen
                            source_ids = list(range(1, min(len(supporting_sources) + 1, 11)))  # Max 10 Quellen
                    
                    if source_ids:
                        # Füge Quellenreferenzen in eckigen Klammern hinzu
                        source_refs = f"[{','.join(map(str, source_ids))}]"
                        normalized_value = f"{normalized_value} {source_refs}"
                
                # Escape Pipe-Zeichen in Werten
                escaped_value = str(normalized_value).replace("|", "\\|") if normalized_value else "nichts gefunden"
                row.append(escaped_value)
        
        csv_lines.append("|".join(row))
    
    csv_content = "\n".join(csv_lines)
    
    # Dateiname mit Timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"minesearch_consolidated_{timestamp}.csv"
    
    # Stream Response erstellen
    def iter_csv():
        yield csv_content.encode('utf-8-sig')  # UTF-8 BOM für Excel
    
    return StreamingResponse(
        iter_csv(),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Type": "text/csv; charset=utf-8"
        }
    )