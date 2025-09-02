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

# Import ValueNormalizer for semantic value equivalence
from minesearch.value_normalizer import value_normalizer

logger = logging.getLogger(__name__)
router = APIRouter()

# CSV imports for Phase 16.3
import csv
import io
from fastapi.responses import StreamingResponse
from datetime import datetime
import re

# Field mappings are now imported from consolidated_field_utils.py

def _normalize_placeholder_value(value):
    """
    RULE 10 COMPLIANCE 26.08.2025: NULL-konforme Normalisierung für CSV-Ausgabe
    KEINE "nichts gefunden" Fallback-Werte - nur NULL oder echte Daten
    
    Behandelt sowohl neue als auch bereits in der DB gespeicherte LEER-Varianten
    """
    if not value or not str(value).strip():
        return None  # REGEL 10: NULL statt "nichts gefunden"
    
    value_str = str(value).strip()
    
    # REGEL 10: DIREKTE Überprüfung auf problematische Werte
    if value_str.startswith('TEMPLATE:'):
        logger.debug(f"[REGEL 10] Template-Wert normalisiert: '{value_str}' -> NULL")
        return None
    
    # CSV-FIX: Erweiterte exakte Platzhalter-Liste (verhindert Feldverschiebung)
    exact_placeholders = [
        # Standard Platzhalter
        'LEER', 'Leer', 'leer', 'X', 'N/A', 'n/a', 'N.A.', 'n.a.',
        'UNBEKANNT', 'UNKNOWN', 'NICHT GEFUNDEN', 'NOT FOUND',
        'KEINE ANGABEN', 'NO DATA', 'K.A.', 'k.a.', 'K.A.', 
        'NICHT VERFÜGBAR', 'NOT AVAILABLE', 'keine Daten',
        'Keine Informationen gefunden', 'Nicht verfügbar', 'Unbekannt',
        'unbekannt', 'unknown', 'nicht bekannt', 'nicht verfügbar',
        'no data', 'no information', 'not found', 'not available',
        'tbd', 'to be determined', 'keine angabe', 'keine angaben',
        'nicht ermittelbar', 'nicht spezifiziert', 'not specified', 
        'not applicable', 'keine information', 'no info', 'nichts gefunden',
        # CSV-FIX: Zusätzliche problematische Werte aus der CSV-Analyse
        '-', '--', '---', '????', '???', '??',  # Striche und Fragezeichen
        'x-Koordinate', 'y-Koordinate',  # Feldnamen die als Werte erscheinen
        'Produktionsstart', 'Produktionsende',  # Weitere Feldnamen
        'Betreiber', 'Eigentümer', 'Rohstoffe', 'Minentyp',  # Feldnamen
        'Minenfläche in qkm', 'Restaurationskosten',  # Weitere Feldnamen
        'Kostenjahr', 'Dokumentenjahr', 'Aktivitätsstatus',  # Feldnamen
        'leer [1]', 'FlM-CM-$che der Mine in qkm',  # Spezielle Problemwerte
        'Fläche der Mine in qkm', 'Mine geschlossen',  # Weitere Problemwerte
        'noch aktiv',  # Status-Werte die falsch zugeordnet werden
        # CSV-FIX 29.08.2025: "Keine Dokumentierten" als Leer behandeln
        'Keine Dokumentierten Eigentumsverhaltnisse',
        'Keine dokumentierten Eigentumsverhaltnisse',
        'keine dokumentierten Eigentumsverhaltnisse'
    ]
    
    if value_str in exact_placeholders:
        logger.debug(f"[REGEL 10] Exakter Platzhalter normalisiert: '{value_str}' -> NULL")
        return None
    
    # CSV-FIX: Template-Pattern für AI-generierte Werte
    template_patterns = [
        r'^TEMPLATE:\s*.*$',                              # Alle TEMPLATE:-Werte
        r'^Untertage/\s*Open-Pit.*usw.*$',               # Template-Strukturen
        r'^Gold/\s*Kupfer.*usw.*$',                      # Template-Aufzählungen
        r'^aktiv/\s*geplant.*sonstiges.*$',              # Template-Status
        r'^\([^)]*usw\.\)$',                             # "(beliebig usw.)"
        r'^[^(]*\([^)]*usw\.\)[^)]*$',                   # "Text (beliebig usw.) Text"
        r'.*[Kk]eine spezifischen.*',                    # "Keine spezifischen [...]"
        r'.*[Kk]eine verlässlichen.*',                   # "Keine verlässlichen [...]"
        r'.*[Kk]eine öffentlichen.*',                    # "Keine öffentlichen [...]"
        r'.*[Nn]o specific.*',                           # "No specific [...]"
        r'.*dokumentiert$',                              # "[...] dokumentiert"
        r'^LEER\s*-\s*.*',                              # "LEER - [Text]"
        r'^Leer\s*-\s*.*',                              # "Leer - [Text]"
        r'^leer\s*-\s*.*',                              # "leer - [Text]"
        # CSV-FIX 29.08.2025: "Keine Dokumentierten" Pattern erkennen
        r'.*[Kk]eine [Dd]okumentierten.*',              # Alle Varianten von "Keine dokumentierten [...]"
        # CSV-FIX 25.08.2025: Feldnamen mit Quellenreferenzen erkennen
        r'^x-Koordinate\s*\[[^\]]*\]$',                 # "x-Koordinate [1]" 
        r'^y-Koordinate\s*\[[^\]]*\]$',                 # "y-Koordinate [1]"
        r'^Produktionsstart\s*\[[^\]]*\]$',             # "Produktionsstart [1]"
        r'^Produktionsende\s*\[[^\]]*\]$',              # "Produktionsende [1]"
        r'^Betreiber\s*\[[^\]]*\]$',                    # "Betreiber [1]"
        r'^Eigentümer\s*\[[^\]]*\]$',                   # "Eigentümer [1]"
        r'^Minenfläche in qkm\s*\[[^\]]*\]$',           # "Minenfläche in qkm [1]"
        r'^Fläche der Mine in qkm\s*\[[^\]]*\]$'        # "Fläche der Mine in qkm [1]"
    ]
    
    for pattern in template_patterns:
        if re.match(pattern, value_str, re.IGNORECASE):
            logger.debug(f"[REGEL 10] Template-Pattern erkannt: '{value_str}' -> NULL")
            return None
    
    # REGEL 10: AI-Kommentare in bestehenden DB-Daten
    ai_comment_patterns = [
        'the user says', 'user says', 'so that\'s straightforward',
        'also unknown', 'no data, so leave blank', 'without specifics',
        'can\'t provide numbers', 'since i can\'t access',
        'i\'ll rely on general', 'typical values for'
    ]
    
    if any(pattern in value_str.lower() for pattern in ai_comment_patterns):
        logger.debug(f"[REGEL 10] AI-Kommentar erkannt: '{value_str[:30]}...' -> NULL")
        return None
    
    # Echte Werte unverändert zurückgeben
    return value_str

def _analyze_field_values(value_details, field_name=None):
    """
    Analysiert alle Werte für ein Feld und gruppiert sie nach Eindeutigkeit
    
    PHASE 15.3 FIX: Normalisiert ALLE Werte BEVOR sie analysiert werden!
    VALUE-NORMALIZATION FIX 26.08.2025: Semantische Normalisierung für identische Begriffe
    
    Returns: Dict mit eindeutigen Werten und deren Metadaten
    """
    value_groups = {}
    
    for detail in value_details:
        # PHASE 15.3 KRITISCH: Normalisiere JEDEN Wert vor der Analyse!
        original_value = str(detail.get('value', '')).strip() if detail.get('value') is not None else ''
        normalized_display_value = _normalize_placeholder_value(original_value)
        
        # Absicherung gegen None-Werte
        if normalized_display_value is None:
            normalized_display_value = ''
        
        # VALUE-NORMALIZATION FIX 26.08.2025: Semantische Normalisierung NACH Platzhalter-Normalisierung
        # Beispiel: "Canada" und "Kanada" werden beide zu "Kanada" normalisiert
        if normalized_display_value.strip() and field_name:
            semantically_normalized = value_normalizer.normalize_value(normalized_display_value, field_name)
            logger.debug(f"[VALUE-NORM] Feld '{field_name}': '{normalized_display_value}' → '{semantically_normalized}'")
            
            # Verwende semantisch normalisierten Wert für Display
            display_value = semantically_normalized
        else:
            display_value = str(normalized_display_value)
        
        # CRITICAL FIX 27.08.2025: Verwende normalisierten Wert AUCH für Gruppenvergleich
        # Damit "Gold" und "gold" in der GLEICHEN Gruppe landen
        value = str(display_value).strip().lower()  # Normalisiert für Vergleich nach semantischer Normalisierung
        
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
        else:
            # CRITICAL FIX 27.08.2025: Bei mehreren normalisierten Werten, wähle den "besseren" Display-Wert
            existing_display = value_groups[value]['display_value']
            
            # Bevorzuge Werte mit Großbuchstaben (Gold > gold, Kanada > canada)
            if display_value != existing_display:
                if display_value.istitle() and not existing_display.istitle():
                    value_groups[value]['display_value'] = display_value
                    logger.debug(f"[NORMALIZE-MERGE] Upgraded display value: '{existing_display}' → '{display_value}'")
                elif display_value.isupper() and existing_display.islower():
                    value_groups[value]['display_value'] = display_value
                    logger.debug(f"[NORMALIZE-MERGE] Upgraded display value: '{existing_display}' → '{display_value}'")
        
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
    
    # KRITISCHER CONSENSUS-BUG FIX 26.08.2025: Korrekte max_reasonable_score Berechnung
    # Bei 17 Modellen mit identischem Wert sollte Vertrauen 100% sein, nicht 24%!
    # 
    # Beispiel 17x "Gold": frequency=17 (17), consensus=17 (17), echte-daten-bonus=50 = 84 Punkte
    # max_reasonable_score muss dynamisch an tatsächliche Modellanzahl angepasst werden
    
    # Berechne dynamischen max_reasonable_score basierend auf verfügbaren Daten
    if value_analysis and best_value:
        max_frequency = max(analysis['frequency'] for analysis in value_analysis.values())
        max_consensus = max(analysis['model_consensus'] for analysis in value_analysis.values())
        
        # Neue Formel: Wenn alle Modelle übereinstimmen = 100% Vertrauen
        max_reasonable_score = max_frequency * 1.0 + max_consensus * 1.0 + 50.0  # bonuses
        
        # ZUSÄTZLICH: Bei perfektem Consensus (alle Modelle gleicher Wert) = automatisch 95-100%
        if best_value['frequency'] == max_frequency and best_value['model_consensus'] == max_consensus:
            confidence_score = min(100, max(95, (best_score / max_reasonable_score) * 100))
            logger.info(f"[CONSENSUS-FIX] Perfekter Consensus erkannt: '{best_value['display_value']}' von {best_value['frequency']} Modellen → {confidence_score:.1f}% Vertrauen (Score: {best_score:.1f}/{max_reasonable_score:.1f})")
        else:
            confidence_score = min(100, max(0, (best_score / max_reasonable_score) * 100))
            logger.debug(f"[SCORE-CALC] '{best_value['display_value']}': freq={best_value['frequency']}/{max_frequency}, consensus={best_value['model_consensus']}/{max_consensus} → {confidence_score:.1f}% Vertrauen")
    else:
        # Fallback: Alte statische Berechnung
        max_reasonable_score = 60.0
        confidence_score = min(100, max(0, (best_score / max_reasonable_score) * 100))
    
    # Bestimme Begründung
    reason_parts = []
    if best_value and best_value.get('frequency', 0) > 1:
        reason_parts.append(f"Häufigkeit: {best_value['frequency']}")
    if best_value and best_value.get('source_diversity', 0) > 1:
        reason_parts.append(f"Quellen: {best_value['source_diversity']}")
    if best_value and best_value.get('model_consensus', 0) > 1:
        reason_parts.append(f"Modelle: {best_value['model_consensus']}")
    
    reason = "Best Value aufgrund: " + ", ".join(reason_parts) if reason_parts else "Einziger verfügbarer Wert"
    
    return {
        'display_value': best_value.get('display_value', '') if best_value else '',
        'confidence_score': round(confidence_score, 1),
        'reason': reason,
        'frequency': best_value.get('frequency', 0) if best_value else 0,
        'source_diversity': best_value.get('source_diversity', 0) if best_value else 0,
        'model_consensus': best_value.get('model_consensus', 0) if best_value else 0,
        'avg_data_quality': round(best_value.get('avg_data_quality', 0), 1) if best_value else 0,
        'supporting_models': best_value.get('unique_ai_models', []) if best_value else [],
        'supporting_sources': best_value.get('unique_real_sources', [])[:3] if best_value else []  # Zeige nur ersten 3 URLs
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
    from minesearch.utils import normalize_accents, normalize_mine_name_for_grouping
    
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
            
            # FIX: Hole Länder-Daten aus mines_normalized falls nicht in SearchResult verfügbar
            # Prüfe ob SearchResult-Daten leer oder 'Unknown' sind
            search_country = result.country or ''
            search_region = result.region or ''
            
            # Wenn SearchResult keine gültigen Daten hat, hole sie aus mines_normalized
            if not search_country or search_country.lower() in ['unknown', 'nicht verfügbar']:
                try:
                    # Direkte DB-Abfrage für mines_normalized ohne zirkuläre Abhängigkeiten
                    from sqlalchemy import text
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
                        logger.info(f"[COUNTRY-FIX] Loaded location for {mine_name}: {normalized_result[0]}, {normalized_result[1]}")
                    else:
                        mine_data['country'] = search_country
                        mine_data['region'] = search_region
                except Exception as e:
                    logger.warning(f"Could not fetch normalized location for {mine_name}: {e}")
                    # Fallback auf SearchResult-Daten
                    mine_data['country'] = search_country
                    mine_data['region'] = search_region
            else:
                mine_data['country'] = search_country
                mine_data['region'] = search_region
            
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
        
        # DISPLAY NAME SELECTION 25.08.2025: Wähle besten ursprünglichen Namen für Anzeige
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
                
                logger.info(f"[DEDUPLICATION] '{normalized_name}' hat {len(mine_data['original_names'])} Schreibweisen: {mine_data['original_names']}")
                logger.info(f"[DEDUPLICATION] Gewählter Anzeigename: '{best_display_name}' (beste Schreibweise)")
            elif len(mine_data['original_names']) == 1:
                # Nur eine Schreibweise - verwende diese
                mine_data['mine_name'] = next(iter(mine_data['original_names']))
        
        # Konvertiere zu Liste und implementiere "Best Value" Algorithmus
        consolidated_results = []
        logger.info(f"[DEBUG] Processing {len(mines_data)} mines (nach Deduplication)")
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
                
                # 🆕 SCHEMA-NORMALISIERUNG 28.08.2025: Prüfe atomische Werte zuerst
                try:
                    from minesearch.atomic_value_service import calculate_best_atomic_value
                    from minesearch.database import db_manager
                    
                    with db_manager.get_session() as session:
                        atomic_best_value = calculate_best_atomic_value(
                            session, mine_name, field_name, fallback_to_json=True
                        )
                        
                        # Verwende atomischen Wert wenn verfügbar und von hoher Qualität
                        if (atomic_best_value['method'] == 'atomic_normalized' and 
                            atomic_best_value['confidence_score'] >= 50.0):
                            
                            logger.info(f"[ATOMIC] Verwende atomischen Wert für {mine_name}.{field_name}: {atomic_best_value['atomic_value']}")
                            best_value_info = {
                                'display_value': atomic_best_value['display_value'],
                                'confidence_score': atomic_best_value['confidence_score'],
                                'frequency': atomic_best_value['frequency'],
                                'supporting_sources': [],  # URLs werden über source_references gemappt
                                'model_consensus': atomic_best_value['frequency'],  # Häufigkeit = Consensus
                                'method': 'atomic_normalized'
                            }
                            
                            # Erstelle value_analysis für Kompatibilität
                            value_analysis = {
                                atomic_best_value['atomic_value']: {
                                    'display_value': atomic_best_value['display_value'],
                                    'frequency': atomic_best_value['frequency'],
                                    'confidence': atomic_best_value['confidence_score'],
                                    'ai_models': [],  # Wird nicht benötigt für atomische Werte
                                    'search_timestamps': []
                                }
                            }
                        else:
                            # Fallback auf bestehende Methode
                            logger.info(f"[ATOMIC] Fallback zu JSON für {mine_name}.{field_name}")
                            # Analysiere alle Werte für dieses Feld
                            # VALUE-NORMALIZATION FIX 26.08.2025: Übergebe field_name für semantische Normalisierung
                            value_analysis = _analyze_field_values(field_info['value_details'], field_name)
                            
                            # Bestimme besten Wert basierend auf Algorithmus
                            # TEMPLATE-PATTERN-FIX 06.08.2025: Übergebe field_name für Template-Detection
                            best_value_info = _calculate_best_value(value_analysis, field_name)
                            
                except Exception as e:
                    logger.warning(f"[ATOMIC] Fehler bei atomischen Werten für {mine_name}.{field_name}: {e}")
                    # Fallback auf bestehende Methode
                    value_analysis = _analyze_field_values(field_info['value_details'], field_name)
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
                'mine_name': mine_data['mine_name'],  # Verwende Display-Name statt normalisierten Key
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
                'mine_name': mine_data['mine_name'],  # Verwende Display-Name statt normalisierten Key
                'country': mine_data['country'], 
                'region': mine_data['region'],
                'best_values': {
                    # FELDFIX 29.08.2025: Meta-Felder filtern und kritische Felder hinzufügen
                    **{k: v for k, v in best_values.items() if not k.startswith('_')},  # Filter Meta-Felder
                    # Kritische Felder aus detailed_breakdown zu best_values kopieren
                    **{field_name: field_data['best_value']['display_value']
                       for field_name, field_data in detailed_breakdown.items()
                       if field_name in ['Land', 'Region'] and field_data['best_value']['display_value'] != 'Nichts gefunden'}
                },  # Enhanced for critical fields
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
        
        # GLOBAL SOURCE INDEX SYSTEM - Fix für get_mine_consolidated_details 24.08.2025
        # Erstelle globales Quellennummerierungssystem für konsistente Referenzen (wie in get_consolidated_results)
        global_source_index = {}  # URL -> Nummer Mapping
        global_source_counter = 1
        
        def get_or_assign_source_number(source_url):
            """Gibt eindeutige Nummer für Quelle zurück oder erstellt neue"""
            nonlocal global_source_counter
            if source_url not in global_source_index:
                global_source_index[source_url] = global_source_counter
                global_source_counter += 1
            return global_source_index[source_url]
        
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
            # VALUE-NORMALIZATION FIX 26.08.2025: Übergebe field_name für semantische Normalisierung
            value_analysis = _analyze_field_values(field_info['value_details'], field_name)
            
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
                "best_values": {
                    # FELDFIX 29.08.2025: Meta-Felder filtern und kritische Felder hinzufügen
                    **{k: v for k, v in best_values.items() if not k.startswith('_')},  # Filter Meta-Felder
                    # Kritische Felder aus detailed_breakdown zu best_values kopieren
                    **{field_name: field_data['best_value']['display_value']
                       for field_name, field_data in detailed_breakdown.items()
                       if field_name in ['Land', 'Region'] and field_data['best_value']['display_value'] != 'Nichts gefunden'}
                },
                "detailed_breakdown": detailed_breakdown,
                "overall_confidence": round(overall_confidence, 1),
                "source_summary": source_summary,
                "model_count": mine_data['model_count'],
                "last_updated": mine_data['last_updated'].isoformat() if mine_data['last_updated'] else None,
                "total_sources": mine_data['total_sources']
            }
        }

# Utility class to encapsulate CSV field processing logic (atomic lookup, normalization, sources, escaping)
class CSVFieldProcessor:
    @staticmethod
    def process_field(field: str, result: Dict[str, Any]) -> str:
        # Get raw value (atomic lookup with DB session; fallback to best_values)
        value = CSVFieldProcessor._get_field_value(field, result)

        # Normalize according to Rule 10 semantics (empty -> empty string)
        normalized_value = CSVFieldProcessor._normalize_value(value)

        # Resolve source ids via layered fallbacks
        source_ids = CSVFieldProcessor._resolve_source_ids(field, result)

        # Append source references only when appropriate
        value_with_refs = CSVFieldProcessor._add_source_references(normalized_value, source_ids)

        # Escape for CSV and enforce final empty-string on whitespace-only
        final_value = CSVFieldProcessor._escape_for_csv(value_with_refs)
        return final_value

    @staticmethod
    def _get_field_value(field: str, result: Dict[str, Any]) -> Any:
        atomic_value = None
        try:
            from minesearch.atomic_value_service import calculate_best_atomic_value
            from minesearch.database import db_manager

            with db_manager.get_session() as session:
                atomic_result = calculate_best_atomic_value(
                    session, result["mine_name"], field, fallback_to_json=False
                )

                if (
                    atomic_result.get('method') == 'atomic_normalized'
                    and atomic_result.get('confidence_score', 0.0) >= 30.0
                ):
                    atomic_value = atomic_result.get('display_value')
                    logger.debug(f"[CSV-ATOMIC] Verwende atomischen Wert für {result['mine_name']}.{field}: {atomic_value}")

        except Exception as e:
            # Handle DB/session and atomic lookup errors internally; fall back to best_values
            logger.debug(f"[CSV-ATOMIC] Fehler bei atomischen Werten für {field}: {e}")

        if atomic_value:
            return atomic_value

        best_values = result.get("best_values", {})
        return best_values.get(field, "")

    @staticmethod
    def _normalize_value(value: Any) -> str:
        return _normalize_placeholder_value(value) or ""

    @staticmethod
    def _resolve_source_ids(field: str, result: Dict[str, Any]) -> List[int]:
        detailed_breakdown = result.get("detailed_breakdown", {})
        if field not in detailed_breakdown:
            return []

        field_data = detailed_breakdown.get(field, {}) or {}
        source_ids = field_data.get('global_source_numbers', []) or []

        # Fallback 1: structured_fields
        if not source_ids:
            structured_fields = result.get('structured_fields', {}) or {}
            if field in structured_fields:
                source_ids = structured_fields[field].get('global_source_numbers', []) or []

        # Fallback 2: source_mapping (extract first 10 numeric source ids)
        if not source_ids:
            source_mapping = result.get("source_mapping", {})
            if source_mapping and isinstance(source_mapping, dict):
                available_sources = source_mapping.get("sources", {}) or {}
                if available_sources:
                    try:
                        numeric_keys = [int(k) for k in available_sources.keys() if str(k).isdigit()]
                        source_ids = sorted(numeric_keys)[:10]
                    except Exception:
                        source_ids = []

        # Deduplicate while preserving order
        seen: set[int] = set()
        deduped_ids: List[int] = []
        for sid in source_ids:
            if sid not in seen:
                deduped_ids.append(sid)
                seen.add(sid)
        return deduped_ids

    @staticmethod
    def _add_source_references(normalized_value: str, source_ids: List[int]) -> str:
        # Only add references for non-empty values and when not already present
        if not normalized_value or not normalized_value.strip():
            return normalized_value

        if not source_ids or len(source_ids) < 3:
            return normalized_value

        # Check if bracketed references already exist
        if re.search(r'\[\d+(?:,\d+)*\]', normalized_value):
            return normalized_value

        refs = f"[{','.join(map(str, source_ids))}]"
        return f"{normalized_value} {refs}"

    @staticmethod
    def _escape_for_csv(value: str) -> str:
        # CSV-FIX 29.08.2025: Ersetze Pipe-Zeichen mit Schrägstrich gemäß User-Anforderung
        escaped_value = str(value).replace("|", "/")
        return escaped_value.strip() and escaped_value or ""

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
    
    # Dann alle anderen Felder aus FIELD_ORDER (außer Metadaten, Details und redundantes Quellenangaben)
    excluded_field_keys = set(metadata_mapping.keys()) | {"Details", "Quellenangaben"}
    remaining_fields = [f for f in FIELD_ORDER if f not in excluded_field_keys and f in all_fields]
    
    # CSV-FIX ENTFERNT: "Quellenangaben" Feld ist redundant - nur "Exakte Quellenangaben" verwenden
    
    header.extend(remaining_fields)
    
    # EXAKTE-QUELLENANGABEN-FIX 24.08.2025: Zusätzliche Spalte für detaillierte Quellenangaben
    header.append("Exakte Quellenangaben")
    
    csv_lines.append("|".join(header))
    
    # Daten-Zeilen - genau wie UI-Struktur
    for result in results:
        row = []
        
        # Metadaten-Felder
        for field_type in data_fields:
            if field_type == "mine_name":
                row.append(result.get("mine_name", ""))  # REGEL 10: Leer statt "nichts gefunden"
            elif field_type == "country": 
                country_val = result.get("country", "")
                row.append(_normalize_placeholder_value(country_val) or "")  # REGEL 10: Leer statt "nichts gefunden"
            elif field_type == "region":
                region_val = result.get("region", "")
                row.append(_normalize_placeholder_value(region_val) or "")  # REGEL 10: Leer statt "nichts gefunden"
            elif field_type == "overall_confidence":
                row.append(str(result.get("overall_confidence", 0)) + "%")
            elif field_type == "model_count":
                row.append(str(result.get("model_count", 0)))
            elif field_type == "last_updated":
                row.append(result.get("last_updated", ""))
        
        # 🆕 SCHEMA-NORMALISIERUNG 28.08.2025: CSV mit atomischen Werten optimieren
        # CRITICAL CSV-FIX 25.08.2025: Strikte Feld-Verarbeitung verhindert Feldverschiebung
        # Für JEDEN Feld aus remaining_fields MUSS ein Wert existieren
        for field in remaining_fields:
            try:
                final_value = CSVFieldProcessor.process_field(field, result)
                row.append(final_value)
            except Exception as e:
                # REGEL 10: Bei unerwartetem Fehler leeren Wert verwenden (DB-Fehler bereits intern behandelt)
                logger.error(f"[CSV-FIX] Fehler bei Feld '{field}' für Mine '{result.get('mine_name', 'unknown')}': {e}")
                row.append("")  # REGEL 10: Leer statt "nichts gefunden"
        
        # EXAKTE-QUELLENANGABEN-FIX 24.08.2025: Füge detaillierte Quellenangaben hinzu
        exact_sources = []
        
        # EXAKTE-QUELLENANGABEN-FIX: Suche Quellenangaben in der richtigen Struktur
        source_mapping = None
        
        # 1. Primär: Aus result.best_values._source_mapping (aktuelle Struktur)
        best_values = result.get("best_values", {})
        if isinstance(best_values, dict) and "_source_mapping" in best_values:
            source_mapping = best_values["_source_mapping"]
        
        # 2. Fallback: Aus result.structured_fields._source_mapping
        elif "structured_fields" in result:
            structured_fields = result["structured_fields"]
            if isinstance(structured_fields, dict) and "_source_mapping" in structured_fields:
                source_mapping = structured_fields["_source_mapping"]
        
        # 3. Fallback: Aus result.source_mapping (alte Struktur) 
        elif "source_mapping" in result:
            source_mapping = result["source_mapping"]
            
        if source_mapping and isinstance(source_mapping, dict):
            sources_dict = source_mapping.get("sources", {})
            if sources_dict:
                # Sortiere nach Quellennummer
                for source_num in sorted(sources_dict.keys(), key=lambda x: int(x) if x.isdigit() else 999):
                    source_info = sources_dict[source_num]
                    if isinstance(source_info, dict):
                        title = source_info.get("title", f"Quelle {source_num}")
                        url = source_info.get("url", "Keine URL")
                        exact_sources.append(f"[{source_num}] {title}: {url}")
        
        # Fallback: Verwende model_results für detaillierte Quellenangaben
        if not exact_sources:
            model_results = result.get("model_results", [])
            found_source_mapping = None
            
            # Suche in model_results nach aktuellstem Ergebnis mit _source_mapping
            for model_result in model_results:
                if isinstance(model_result, dict):
                    structured_data = model_result.get("structured_data", {})
                    if isinstance(structured_data, dict) and "_source_mapping" in structured_data:
                        potential_mapping = structured_data["_source_mapping"]
                        if isinstance(potential_mapping, dict):
                            found_source_mapping = potential_mapping
                            break
            
            if found_source_mapping:
                sources_dict = found_source_mapping.get("sources", {})
                if sources_dict:
                    # Sortiere nach Quellennummer
                    for source_num in sorted(sources_dict.keys(), key=lambda x: int(x) if x.isdigit() else 999):
                        source_info = sources_dict[source_num]
                        if isinstance(source_info, dict):
                            title = source_info.get("title", f"Quelle {source_num}")
                            url = source_info.get("url", "Keine URL")
                            exact_sources.append(f"[{source_num}] {title}: {url}")
        
        # Final Fallback: Verwende sources Array aus model_results, falls vorhanden
        if not exact_sources:
            model_results = result.get("model_results", [])
            
            # Verwende das neueste model_result mit sources
            for model_result in reversed(model_results):  # Neuestes zuerst
                if isinstance(model_result, dict):
                    sources_array = model_result.get("sources", [])
                    if sources_array and len(sources_array) > 0:
                        # Verwende die ersten 10 Quellen und erstelle nummerierte Liste
                        for i, source in enumerate(sources_array[:10], 1):
                            if isinstance(source, dict):
                                url = source.get("url", "Keine URL")
                                
                                # Versuche besseren Titel zu finden
                                title = source.get("title", "")
                                if not title or title == url:
                                    title = source.get("description", "")
                                if not title:
                                    # Generiere Titel aus URL
                                    domain = url.split("/")[2] if len(url.split("/")) > 2 else "Unbekannte Quelle"
                                    title = domain
                                
                                exact_sources.append(f"[{i}] {title}: {url}")
                        break  # Verwende nur das erste gefundene model_result mit sources
        
        # REGEL 10 FIX 29.08.2025: Keine Dummy-Werte - lasse Quellen leer wenn keine gefunden
        if not exact_sources:
            exact_sources.append("")  # Leerer String statt Dummy-Text
        
        # Kombiniere Quellen zu einem String (Semikolon-getrennt für CSV)
        exact_sources_text = "; ".join(exact_sources)
        
        # CSV-quoting für die Zelle mit Delimiter '|', damit '|' korrekt gehandhabt wird
        import csv
        import io
        _cell_buffer = io.StringIO()
        _cell_writer = csv.writer(_cell_buffer, delimiter='|', quoting=csv.QUOTE_MINIMAL)
        _cell_writer.writerow([exact_sources_text])
        escaped_exact_sources = _cell_buffer.getvalue().rstrip("\r\n")
        row.append(escaped_exact_sources)
        
        # CRITICAL CSV-FIX 25.08.2025: Validiere Spaltenanzahl BEVOR Zeile hinzugefügt wird
        expected_columns = len(header)
        actual_columns = len(row)
        
        if actual_columns != expected_columns:
            logger.error(f"[CSV-FIX] SPALTEN-MISMATCH für Mine '{result.get('mine_name', 'unknown')}': "
                        f"Erwartet {expected_columns}, Erhalten {actual_columns}")
            
            # Repariere Zeile: Füge fehlende Spalten hinzu oder entferne überschüssige
            if actual_columns < expected_columns:
                # REGEL 10: Zu wenige Spalten - füge leere Werte hinzu
                missing_count = expected_columns - actual_columns
                for i in range(missing_count):
                    row.append("")  # REGEL 10: Leer statt "nichts gefunden"
                logger.warning(f"[CSV-FIX] {missing_count} fehlende Spalten mit leeren Werten aufgefüllt")
            elif actual_columns > expected_columns:
                # Zu viele Spalten - entferne überschüssige
                row = row[:expected_columns]
                logger.warning(f"[CSV-FIX] {actual_columns - expected_columns} überschüssige Spalten entfernt")
        
        # Finale Validierung
        final_columns = len(row)
        if final_columns == expected_columns:
            csv_lines.append("|".join(row))
            logger.debug(f"[CSV-FIX] Zeile für Mine '{result.get('mine_name', 'unknown')}' erfolgreich hinzugefügt")
        else:
            logger.error(f"[CSV-FIX] KRITISCHER FEHLER: Zeile für Mine '{result.get('mine_name', 'unknown')}' "
                        f"konnte nicht repariert werden ({final_columns} != {expected_columns})")
            # REGEL 10 COMPLIANCE 26.08.2025: KEINE Fallback-Daten - Fehlgeschlagene Zeile weglassen
            logger.error(f"[REGEL 10] CSV-Zeile für Mine '{result.get('mine_name', 'unknown')}' wird übersprungen - "
                        "Keine ausgedachten Fallback-Daten")
            # Zeile wird komplett weggelassen statt mit falschen Daten gefüllt
    
    # PERFORMANCE-FIX 25.08.2025: Streaming für große CSV-Exports
    # Dateiname mit Timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"minesearch_consolidated_{timestamp}.csv"
    
    # Streaming Generator für große CSV-Dateien
    def iter_csv():
        # UTF-8 BOM für Excel-Kompatibilität
        yield '\ufeff'.encode('utf-8')
        
        # Header zuerst
        yield (csv_lines[0] + '\n').encode('utf-8')
        
        # PERFORMANCE: Streame Zeilen in Chunks statt alles auf einmal
        chunk_size = 100  # Zeilen pro Chunk
        data_lines = csv_lines[1:]  # Ohne Header
        
        for i in range(0, len(data_lines), chunk_size):
            chunk = data_lines[i:i + chunk_size]
            chunk_content = '\n'.join(chunk) + '\n'
            yield chunk_content.encode('utf-8')
            
            # Log Progress für große Exports
            if len(data_lines) > 1000 and i % 500 == 0:
                logger.info(f"[CSV-EXPORT] Progress: {i + len(chunk)}/{len(data_lines)} Zeilen gestreamt")
    
    # Performance-Logging
    total_lines = len(csv_lines)
    total_size = sum(len(line) for line in csv_lines) / 1024  # KB
    logger.info(f"[CSV-EXPORT] Streaming CSV mit {total_lines} Zeilen ({total_size:.1f} KB)")
    
    return StreamingResponse(
        iter_csv(),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Type": "text/csv; charset=utf-8",
            "Cache-Control": "no-cache"  # Verhindere Caching bei großen Exporten
        }
    )


# ============================================================================
# 🆕 NORMALIZED SCHEMA API ENDPOINTS
# Datum: 27.08.2025
# Zweck: Demo der neuen normalisierten Datenbank-Architektur
# ============================================================================

@router.get("/normalized/results")
async def get_normalized_results(
    days_back: int = Query(30),
    sort_by: str = Query("mine_name", description="Sort by: mine_name, country, quality_score"),
    order: str = Query("asc", description="Order: asc or desc"),
    include_template_fields: bool = Query(False, description="Template/Dummy-Werte einschließen")
):
    """
    🆕 NORMALIZED API: Verwendet neue atomare Datenbank-Struktur
    
    VORTEILE:
    - Echte Deduplizierung (keine Eleonore/Éléonore Duplikate mehr)
    - Qualitätsbewertung pro Feldwert
    - Template-Wert Erkennung (REGEL 10 Compliance)
    - Atomare Datenspeicherung statt JSON-Chaos
    - Bessere Performance durch Indizes
    """
    from minesearch.database.normalized_manager import NormalizedDatabaseManager
    from sqlalchemy import text, desc as sql_desc, asc as sql_asc
    from datetime import datetime, timedelta
    from collections import defaultdict
    
    norm_db = NormalizedDatabaseManager()
    
    with norm_db.get_session() as session:
        # Query-Builder für normalisierte Daten
        base_query = """
        SELECT 
            m.id as mine_id,
            m.name as mine_name,
            m.normalized_name,
            m.country,
            m.region,
            m.status,
            m.primary_commodity,
            owner.name as owner_company,
            operator.name as operator_company,
            
            -- Feldwerte
            mdf.field_name,
            mdf.raw_value,
            mdf.normalized_value,
            mdf.numeric_value,
            mdf.unit,
            mdf.confidence_score,
            mdf.is_template_value,
            mdf.validation_status,
            mdf.model_used,
            mdf.source_name,
            
            -- Qualitätsmetriken pro Mine (SQLite-kompatibel ohne DISTINCT in window functions)
            COUNT(mdf.field_name) OVER (PARTITION BY m.id) as total_fields,
            COUNT(CASE WHEN mdf.validation_status = 'valid' THEN mdf.field_name END) OVER (PARTITION BY m.id) as valid_fields,
            COUNT(CASE WHEN mdf.is_template_value = 1 THEN mdf.field_name END) OVER (PARTITION BY m.id) as template_fields,
            MAX(mdf.created_at) OVER (PARTITION BY m.id) as last_updated
            
        FROM mines_normalized m
        LEFT JOIN companies owner ON m.owner_company_id = owner.id
        LEFT JOIN companies operator ON m.operator_company_id = operator.id
        LEFT JOIN mine_data_fields mdf ON m.id = mdf.mine_id
        
        WHERE 1=1
        """
        
        params = {}
        
        # Zeitfilter
        if days_back > 0:
            cutoff = datetime.now() - timedelta(days=days_back)
            base_query += " AND mdf.created_at >= :cutoff"
            params['cutoff'] = cutoff
        
        # Template-Filter
        if not include_template_fields:
            base_query += " AND (mdf.is_template_value = 0 OR mdf.is_template_value IS NULL)"
        
        # Sortierung
        order_clause = "ASC" if order.lower() == "asc" else "DESC"
        if sort_by == "mine_name":
            base_query += f" ORDER BY m.name {order_clause}"
        elif sort_by == "country":
            base_query += f" ORDER BY m.country {order_clause}, m.name ASC"
        elif sort_by == "quality_score":
            base_query += f" ORDER BY valid_fields {order_clause}, m.name ASC"
        
        # Führe Query aus
        result = session.execute(text(base_query), params)
        rows = result.fetchall()
        
        logger.info(f"[NORMALIZED API] Query returned {len(rows)} field entries")
        
        # Gruppiere nach Mine
        mines_data = defaultdict(lambda: {
            'mine_info': None,
            'fields': {},
            'quality_metrics': None,
            'models_used': set()
        })
        
        for row in rows:
            mine_id = row.mine_id
            mine_key = row.normalized_name  # Verwende normalisierte Namen für Konsistenz
            
            # Mine-Grunddaten (nur einmal setzen)
            if mines_data[mine_key]['mine_info'] is None:
                mines_data[mine_key]['mine_info'] = {
                    'id': row.mine_id,
                    'name': row.mine_name,
                    'normalized_name': row.normalized_name,
                    'country': row.country,
                    'region': row.region,
                    'status': row.status,
                    'primary_commodity': row.primary_commodity,
                    'owner_company': row.owner_company,
                    'operator_company': row.operator_company
                }
                
                # Qualitätsmetriken
                mines_data[mine_key]['quality_metrics'] = {
                    'total_fields': row.total_fields or 0,
                    'valid_fields': row.valid_fields or 0,
                    'template_fields': row.template_fields or 0,
                    'data_quality_score': round((row.valid_fields or 0) / max(1, row.total_fields or 1), 2),
                    'last_updated': str(row.last_updated) if row.last_updated else None
                }
            
            # Feldwerte hinzufügen
            if row.field_name and row.raw_value:
                field_key = row.field_name
                
                if field_key not in mines_data[mine_key]['fields']:
                    mines_data[mine_key]['fields'][field_key] = []
                
                mines_data[mine_key]['fields'][field_key].append({
                    'raw_value': row.raw_value,
                    'normalized_value': row.normalized_value,
                    'numeric_value': float(row.numeric_value) if row.numeric_value else None,
                    'unit': row.unit,
                    'confidence_score': float(row.confidence_score) if row.confidence_score else None,
                    'is_template_value': bool(row.is_template_value),
                    'validation_status': row.validation_status,
                    'model_used': row.model_used,
                    'source_name': row.source_name
                })
                
                mines_data[mine_key]['models_used'].add(row.model_used)
        
        # Konvertiere zu Response-Format
        response_data = []
        for mine_key, mine_data in mines_data.items():
            if mine_data['mine_info']:  # Nur Minen mit Daten
                response_item = {
                    **mine_data['mine_info'],
                    'fields': mine_data['fields'],
                    'quality_metrics': mine_data['quality_metrics'],
                    'models_used': list(mine_data['models_used'])
                }
                response_data.append(response_item)
        
        return {
            'success': True,
            'data': {
                'mines': response_data,
                'total_mines': len(response_data),
                'query_params': {
                    'days_back': days_back,
                    'sort_by': sort_by,
                    'order': order,
                    'include_template_fields': include_template_fields
                }
            },
            'schema_info': {
                'type': 'normalized',
                'description': 'Daten aus normalisierter Atomstruktur',
                'advantages': [
                    'Echte Mine-Deduplizierung',
                    'Qualitätsbewertung pro Feld',
                    'Template-Wert Erkennung',
                    'Atomare statt JSON-Speicherung'
                ]
            }
        }


@router.get("/normalized/schema/comparison")
async def compare_schemas():
    """
    Vergleiche Legacy JSON-System vs. Normalisierte Atomstruktur
    Zeigt Unterschiede in Datenqualität und -konsistenz
    """
    from minesearch.database.manager import DatabaseManager
    from minesearch.database.normalized_manager import NormalizedDatabaseManager
    from sqlalchemy import text
    
    legacy_db = DatabaseManager()
    norm_db = NormalizedDatabaseManager()
    
    # Legacy System Stats
    with legacy_db.get_session() as session:
        result = session.execute(text("SELECT COUNT(*) FROM search_results"))
        legacy_searches = result.fetchone()[0]
        
        result = session.execute(text("SELECT COUNT(DISTINCT mine_name) FROM search_results"))
        legacy_unique_mines = result.fetchone()[0]
    
    # Normalized System Stats
    with norm_db.get_session() as session:
        result = session.execute(text("SELECT COUNT(*) FROM search_results_normalized"))
        norm_searches = result.fetchone()[0]
        
        result = session.execute(text("SELECT COUNT(*) FROM mines_normalized"))
        norm_unique_mines = result.fetchone()[0]
        
        result = session.execute(text("SELECT COUNT(*) FROM mine_data_fields"))
        atomic_fields = result.fetchone()[0]
        
        result = session.execute(text("SELECT COUNT(*) FROM mine_data_fields WHERE is_template_value = 1"))
        template_fields = result.fetchone()[0]
        
        result = session.execute(text("SELECT COUNT(*) FROM mine_data_fields WHERE validation_status = 'valid'"))
        valid_fields = result.fetchone()[0]
    
    deduplication_improvement = legacy_unique_mines - norm_unique_mines if legacy_unique_mines > norm_unique_mines else 0
    
    return {
        'success': True,
        'comparison': {
            'legacy_system': {
                'description': 'JSON-basierte Speicherung',
                'total_searches': legacy_searches,
                'unique_mines': legacy_unique_mines,
                'data_structure': 'Unstrukturierte JSON-Blobs',
                'problems': [
                    'Duplikate durch Akzent-Varianten (Eleonore/Éléonore)',
                    'Inkonsistente Datentypen',
                    'Schwierige Aggregation',
                    'Keine Qualitätsbewertung'
                ]
            },
            'normalized_system': {
                'description': 'Atomare, normalisierte Struktur',
                'total_searches': norm_searches,
                'unique_mines': norm_unique_mines,
                'atomic_fields': atomic_fields,
                'template_fields_detected': template_fields,
                'valid_fields': valid_fields,
                'data_quality_score': round(valid_fields / max(1, atomic_fields), 2),
                'advantages': [
                    'Echte Deduplizierung durch Normalisierung',
                    'Atomare Feldwerte mit Typisierung',
                    'Template-Wert Erkennung (REGEL 10)',
                    'Qualitätsbewertung pro Feld',
                    'Bessere Performance durch Indizes'
                ]
            },
            'improvements': {
                'deduplication_savings': deduplication_improvement,
                'data_quality_increase': f"{round(valid_fields / max(1, atomic_fields) * 100, 1)}%",
                'template_rejection_rate': f"{round(template_fields / max(1, atomic_fields) * 100, 1)}%"
            }
        }
    }

@router.get("/mine/{mine_name}/statistics")
async def get_mine_historical_statistics(
    mine_name: str,
    days_back: int = Query(90, description="Tage zurück für historische Analyse"),
    exclude_exa: bool = Query(True, description="Exa-Modelle ausblenden")
):
    """
    🆕 NEUE API für detaillierte Mine-Statistiken über ALLE historischen Suchen
    
    Für das neue Detail-Modal: Zeigt aggregierte Statistiken einer Mine
    über alle bisherigen Suchen hinweg, nicht nur die aktuelle Session.
    
    FEATURES:
    - Durchschnittliche Konfidenz pro Feld über Zeit
    - Häufigste Werte und deren Konsistenz
    - Modell-Performance-Vergleich für diese Mine
    - Zeitbasierte Trends (wann welche Werte gefunden)
    - Template-Wert Erkennung und Qualitätsscore
    """
    from minesearch.database import db_manager
    from sqlalchemy import desc as sql_desc, func, distinct
    from datetime import datetime, timedelta
    from collections import defaultdict
    import json
    
    logger.info(f"[STATISTICS] Getting historical stats for mine: {mine_name}")
    
    try:
        with db_manager.get_session() as session:
            # Zeitfilter
            cutoff = datetime.now() - timedelta(days=days_back)
            
            # Basis-Query für diese Mine
            query = session.query(SearchResult).filter(
                SearchResult.mine_name == mine_name,
                SearchResult.search_timestamp >= cutoff
            )
            
            if exclude_exa:
                query = query.filter(~SearchResult.model_used.like('exa:%'))
            
            results = query.order_by(sql_desc(SearchResult.search_timestamp)).all()
            
            if not results:
                return {
                    'success': False,
                    'error': f'Keine historischen Daten für Mine "{mine_name}" gefunden',
                    'mine_name': mine_name
                }
            
            # STATISTIK-AGGREGATION
            field_stats = defaultdict(lambda: {
                'values': [],
                'sources': defaultdict(int),
                'confidences': [],
                'timestamps': [],
                'models': defaultdict(int)
            })
            
            total_searches = len(results)
            models_used = set()
            search_dates = []
            
            # Durchlaufe alle Ergebnisse für diese Mine
            for result in results:
                models_used.add(result.model_used)
                search_dates.append(result.search_timestamp)
                
                if result.structured_data:
                    try:
                        data = json.loads(result.structured_data) if isinstance(result.structured_data, str) else result.structured_data
                        
                        for field, value in data.items():
                            if value and str(value).strip() and not str(value).startswith('TEMPLATE:'):
                                field_stats[field]['values'].append(str(value))
                                field_stats[field]['models'][result.model_used] += 1
                                field_stats[field]['timestamps'].append(result.search_timestamp)
                                
                                # Pseudo-Konfidenz basierend auf Modell und Häufigkeit
                                confidence = 0.8 if 'gpt-4' in result.model_used.lower() else 0.7
                                field_stats[field]['confidences'].append(confidence)
                    except json.JSONDecodeError:
                        continue
            
            # ANALYSIERE JEDES FELD
            analyzed_fields = {}
            for field, stats in field_stats.items():
                if not stats['values']:
                    continue
                    
                # Häufigkeitsanalyse
                value_counts = defaultdict(int)
                for value in stats['values']:
                    value_counts[value] += 1
                
                # Sortiere nach Häufigkeit
                sorted_values = sorted(value_counts.items(), key=lambda x: x[1], reverse=True)
                most_common_value = sorted_values[0][0] if sorted_values else None
                consistency_rate = (sorted_values[0][1] / len(stats['values'])) * 100 if sorted_values else 0
                
                analyzed_fields[field] = {
                    'field_name': field,
                    'total_occurrences': len(stats['values']),
                    'unique_values': len(set(stats['values'])),
                    'most_common_value': most_common_value,
                    'consistency_rate': round(consistency_rate, 1),
                    'all_values': sorted_values[:5],  # Top 5 Werte
                    'avg_confidence': round(sum(stats['confidences']) / len(stats['confidences']), 2) if stats['confidences'] else 0,
                    'models_found_by': list(stats['models'].keys()),
                    'model_agreement': len(stats['models']) / len(models_used) * 100 if models_used else 0,
                    'first_found': min(stats['timestamps']).strftime('%Y-%m-%d') if stats['timestamps'] else None,
                    'last_updated': max(stats['timestamps']).strftime('%Y-%m-%d') if stats['timestamps'] else None
                }
            
            # MODELL-PERFORMANCE ANALYSE
            model_performance = {}
            for model in models_used:
                model_results = [r for r in results if r.model_used == model]
                total_fields = sum(len(json.loads(r.structured_data) if isinstance(r.structured_data, str) else r.structured_data if r.structured_data else {}) for r in model_results)
                avg_response_time = sum(r.search_duration for r in model_results if r.search_duration) / len(model_results)
                
                model_performance[model] = {
                    'searches': len(model_results),
                    'avg_fields_found': round(total_fields / len(model_results), 1) if model_results else 0,
                    'avg_response_time': round(avg_response_time, 2) if avg_response_time else 0,
                    'success_rate': round(len([r for r in model_results if r.structured_data]) / len(model_results) * 100, 1)
                }
            
            # QUALITÄTSSCORE BERECHNUNG
            quality_indicators = []
            for field_data in analyzed_fields.values():
                # Punkte für Konsistenz
                if field_data['consistency_rate'] > 80:
                    quality_indicators.append(1.0)
                elif field_data['consistency_rate'] > 60:
                    quality_indicators.append(0.7)
                else:
                    quality_indicators.append(0.3)
            
            overall_quality = round(sum(quality_indicators) / len(quality_indicators) * 100, 1) if quality_indicators else 0
            
            return {
                'success': True,
                'data': {
                    'mine_name': mine_name,
                    'analysis_period': {
                        'days_back': days_back,
                        'from_date': cutoff.strftime('%Y-%m-%d'),
                        'to_date': datetime.now().strftime('%Y-%m-%d'),
                        'total_searches': total_searches
                    },
                    'field_statistics': analyzed_fields,
                    'model_performance': model_performance,
                    'quality_metrics': {
                        'overall_quality_score': overall_quality,
                        'total_fields_analyzed': len(analyzed_fields),
                        'models_used_count': len(models_used),
                        'consistency_rating': 'Hoch' if overall_quality > 80 else 'Mittel' if overall_quality > 60 else 'Niedrig'
                    },
                    'timeline': {
                        'first_search': min(search_dates).strftime('%Y-%m-%d %H:%M') if search_dates else None,
                        'last_search': max(search_dates).strftime('%Y-%m-%d %H:%M') if search_dates else None,
                        'search_frequency': f"{len(search_dates) / days_back:.1f} Suchen pro Tag"
                    }
                }
            }
    
    except Exception as e:
        logger.error(f"[STATISTICS] Error getting mine statistics: {e}")
        return {
            'success': False,
            'error': f'Fehler beim Laden der Mine-Statistiken: {str(e)}',
            'mine_name': mine_name
        }