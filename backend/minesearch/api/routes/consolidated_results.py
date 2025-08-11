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

logger = logging.getLogger(__name__)
router = APIRouter()

# FIELD CONSOLIDATION AND RENAMING MAPPING
FIELD_CONSOLIDATION_MAP = {
    # Consolidate duplicate fields - map to preferred German names
    'Name': 'Mine',  # Name -> Mine (remove duplicate)
    'Country': 'Land',  # Country -> Land (remove duplicate)
    # Additional consolidation mappings
    'mine_name': 'Mine',  # English field name -> German
    'country': 'Land',   # English field name -> German
    # CRITICAL FIX 06.08.2025: Rohstoff-Duplikat-Elimination
    'Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)': 'Rohstoffe',  # Primary consolidation
    'Rohstoffabbau (Gold/Kupfer/Kohle/usw.)': 'Rohstoffe',     # Alternative spacing
    'Rohstoffabbau': 'Rohstoffe',                               # Short form
    'Commodity': 'Rohstoffe',                                   # English variant
    'Commodities': 'Rohstoffe',                                 # English plural
    'Rohstofftyp': 'Rohstoffe',                                # Alternative German
    # BACKEND-FIELD-SPECIALIST-FIX 30.07.2025: Kritische fehlende Mappings
    'restoration_costs': 'Restaurationskosten',  # English -> German
    'cost_year': 'Kostenjahr',  # English -> German  
    'document_year': 'Dokumentenjahr',  # English -> German
    'production_start': 'Produktionsstart',  # English -> German
    'mine_area': 'Minenfläche in qkm',  # English -> German
    'x_coordinate': 'x-Koordinate',  # English -> German
    'longitude': 'x-Koordinate',  # Alternative English -> German
    'latitude': 'y-Koordinate',  # Alternative English -> German
}

FIELD_RENAME_MAP = {
    # Rename fields as requested - USER REQUIREMENTS 30.07.2025
    'Jahr der Aufnahme der Kosten': 'Kostenjahr',
    'Jahr der Erstellung des Dokumentes': 'Dokumentenjahr', 
    'Jahr der Erstellung der Dokumentes': 'Dokumentenjahr',  # Alternative spelling
    'Fläche der Mine in qkm': 'Minenfläche in qkm',
    'Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)': 'Rohstoffe',
    'Rohstoffabbau (Gold/Kupfer/Kohle/usw.)': 'Rohstoffe',  # Alternative spacing
    'Minentyp (Untertage/ Open-Pit/ usw.)': 'Minentyp',
    # Additional potential variations
    'Jahr der Aufnahme der Kosten (YYYY)': 'Kostenjahr',
    'Jahr der Erstellung des Dokuments': 'Dokumentenjahr',
    'Fläche der Mine (qkm)': 'Minenfläche in qkm',
    'Rohstofftyp': 'Rohstoffe',
    'Commodity': 'Rohstoffe',
    # CRITICAL FIX 30.07.2025: Additional English field variations
    'Restoration Costs': 'Restaurationskosten',
    'Restoration Cost': 'Restaurationskosten',
    'Cost Year': 'Kostenjahr',
    'Document Year': 'Dokumentenjahr',
    'Mine Area': 'Minenfläche in qkm',
    'Production Start': 'Produktionsstart',
    'Start of Production': 'Produktionsstart',
    'Production Begin': 'Produktionsstart',
    # Potential DB field variations
    'Kosten für Restauration': 'Restaurationskosten',
    'Restaurierung Kosten': 'Restaurationskosten',
    'Wiederherstellungskosten': 'Restaurationskosten',
    # BACKEND-FIELD-SPECIALIST-FIX 30.07.2025: Weitere alternative Feldnamen
    'Restoration Costs': 'Restaurationskosten',
    'Restoration Cost': 'Restaurationskosten',
    'Cost Year': 'Kostenjahr',
    'Document Year': 'Dokumentenjahr',
    'Mine Area': 'Minenfläche in qkm',
    'Area': 'Minenfläche in qkm',
    'Area in qkm': 'Minenfläche in qkm',
    'Area (qkm)': 'Minenfläche in qkm',
    'Mine Size': 'Minenfläche in qkm',
    'Size (qkm)': 'Minenfläche in qkm',
    'X-Coordinate': 'x-Koordinate',
    'Y-Coordinate': 'y-Koordinate',
    'Longitude': 'x-Koordinate',
    'Latitude': 'y-Koordinate',
    'Production Start': 'Produktionsstart',
    'Start of Production': 'Produktionsstart',
    # Alternative deutsche Schreibweisen
    'Restaurierungskosten': 'Restaurationskosten',
    'Wiederherstellungskosten': 'Restaurationskosten',
    'Sanierungskosten': 'Restaurationskosten',
    'Schließungskosten': 'Restaurationskosten'
}

# PREFERRED FIELD ORDER for frontend - USER REQUIREMENTS 30.07.2025
FIELD_ORDER = [
    'Mine', 'Land', 'Region', 'Zuverlässigkeit', 'Modelle', 'Letzte Aktualisierung',
    'Betreiber', 'Eigentümer', 'Rohstoffe', 'Minentyp', 'Aktivitätsstatus', 
    'Produktionsstart', 'Produktionsende', 'Fördermenge/Jahr', 'Minenfläche in qkm',
    'x-Koordinate', 'y-Koordinate', 'Restaurationskosten', 'Kostenjahr', 
    'Dokumentenjahr', 'Quellenangaben', 'Details'
]

def _consolidate_and_rename_field(field_name, field_value):
    """
    Konsolidiert doppelte Felder und benennt Felder um
    
    Returns: (final_field_name, field_value) or None if field should be skipped
    """
    # Step 1: Check if field should be consolidated (removed)
    if field_name in FIELD_CONSOLIDATION_MAP:
        target_field = FIELD_CONSOLIDATION_MAP[field_name]
        logger.debug(f"Consolidating field '{field_name}' -> '{target_field}'")
        return target_field, field_value
    
    # Step 2: Check if field should be renamed
    if field_name in FIELD_RENAME_MAP:
        new_name = FIELD_RENAME_MAP[field_name]
        logger.debug(f"Renaming field '{field_name}' -> '{new_name}'")
        return new_name, field_value
    
    # Step 3: Return original field
    return field_name, field_value

def _analyze_field_values(value_details):
    """
    Analysiert alle Werte für ein Feld und gruppiert sie nach Eindeutigkeit
    
    Returns: Dict mit eindeutigen Werten und deren Metadaten
    """
    value_groups = {}
    
    for detail in value_details:
        value = detail['value'].strip().lower()  # Normalisiert für Vergleich
        display_value = detail['value'].strip()  # Original für Anzeige
        
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
    - Zuverlässigkeit der Quellen
    - TEMPLATE-PATTERN-PENALTY 06.08.2025: Malus für CSV_COLUMNS Template-Strukturen
    
    Args:
        value_analysis: Analyse der verfügbaren Werte
        field_name: Name des Feldes für template-spezifische Prüfungen
    
    Returns: Dict mit bestem Wert und Konfidenz-Score
    """
    if not value_analysis:
        return {
            'display_value': 'Unbekannt',  # FIELD-CONSOLIDATION-FIX 06.08.2025: Bessere UX als X oder N/A
            'confidence_score': 0,
            'reason': 'Keine Daten verfügbar'
        }
    
    best_value = None
    best_score = -1
    
    for value, analysis in value_analysis.items():
        # Gewichtete Score-Berechnung
        frequency_score = analysis['frequency'] * 2.0  # Häufigkeit wichtigster Faktor
        source_diversity_score = analysis['source_diversity'] * 1.5  # Verschiedene Quellen
        model_consensus_score = analysis['model_consensus'] * 1.0  # Verschiedene AI-Modelle
        quality_score = analysis['avg_data_quality'] * 0.01  # Datenqualität (0-100)
        
        # ENHANCED BONUS SYSTEM 06.08.2025: Stärkere Präferenz für echte Daten
        # TEMPLATE-PATTERN-PENALTY 06.08.2025: Starker Malus für Template-Strukturen
        display_val = analysis['display_value'].strip().upper()
        
        # Import is_placeholder_value für Template-Pattern-Erkennung
        from minesearch.extraction_validators import is_placeholder_value
        
        if display_val in ['X', 'N/A', 'UNBEKANNT', 'KEINE ANGABEN', 'NICHT VERFÜGBAR', '']:
            non_x_bonus = 0  # Keine Bonus für Platzhalter-Werte
        elif is_placeholder_value(analysis['display_value'], field_name):
            # TEMPLATE-PATTERN-PENALTY: Starker Malus für Template-Strukturen
            non_x_bonus = -50.0  # Starker Malus für Template-Werte wie "Untertage/ Open-Pit/ usw.)"
        else:
            non_x_bonus = 10.0  # Erhöhter Bonus für echte Daten (war 5.0)
        
        # Malus für sehr kurze Suchzeiten (könnte auf Timeout hindeuten)
        duration_penalty = -2.0 if analysis['avg_search_duration'] < 1.0 else 0
        
        total_score = (frequency_score + source_diversity_score + 
                      model_consensus_score + quality_score + 
                      non_x_bonus + duration_penalty)
        
        if total_score > best_score:
            best_score = total_score
            best_value = analysis
    
    if not best_value:
        return {
            'display_value': 'Unbekannt',  # FIELD-CONSOLIDATION-FIX 06.08.2025: Konsistente UX
            'confidence_score': 0,
            'reason': 'Keine gültigen Werte gefunden'
        }
    
    # Normalisiere Konfidenz-Score zu 0-100 (realistischer)
    # Base score: frequency=1 (2), no diversity (0), no consensus (0), no quality (0), non-X bonus (5) = 7
    # Good score: frequency=3 (6), diversity=2 (3), consensus=3 (3), quality=50 (0.5), non-X (5) = 17.5
    max_reasonable_score = 18.0
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
        
        # Nach Mine gruppieren
        mines_data = defaultdict(lambda: {
            'mine_name': '',
            'country': '',
            'region': '',
            'consolidated_fields': {},
            'model_results': [],
            'model_count': 0,
            'last_updated': None,
            'total_sources': 0,
            'source_mapping': {}  # Maps model names to source numbers
        })
        
        for result in all_results:
            mine_name = result.mine_name
            mine_data = mines_data[mine_name]
            
            # Basis-Informationen setzen
            mine_data['mine_name'] = mine_name
            mine_data['country'] = result.country or ''
            mine_data['region'] = result.region or ''
            mine_data['model_count'] += 1
            
            # Letzte Aktualisierung
            if not mine_data['last_updated'] or result.search_timestamp > mine_data['last_updated']:
                mine_data['last_updated'] = result.search_timestamp
            
            # Quellen zählen
            mine_data['total_sources'] += len(result.sources or [])
            
            # Modell-spezifische Daten sammeln
            model_info = {
                'id': result.id,
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
                    final_field_name, processed_value = _consolidate_and_rename_field(original_field_name, field_value)
                    
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
                        
                        # Extract real data sources (URLs) from sources list
                        real_sources = []
                        if result.sources:
                            for source in result.sources:
                                if isinstance(source, str) and ('http' in source or 'www.' in source):
                                    real_sources.append(source)
                                elif isinstance(source, dict) and source.get('url'):
                                    real_sources.append(source['url'])
                        
                        # CRITICAL FIX: Für Quellenangaben Feld - zeige echte Quellen statt "Keine"
                        if final_field_name.lower() in ['quellenangaben', 'sources', 'quellen']:
                            if real_sources:
                                # Erstelle zusammengefasste Quellenangabe
                                source_types = {}
                                for source in result.sources:
                                    if isinstance(source, dict):
                                        source_type = source.get('type', 'general')
                                        source_types[source_type] = source_types.get(source_type, 0) + 1
                                
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
                                    else:
                                        source_summary.append(f"{count} {stype}-Quellen")
                                
                                clean_value = f"{len(real_sources)} Quellen: " + ", ".join(source_summary)
                        
                        # STEP 3: Add data to the already-created field structure
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
        for mine_name, mine_data in mines_data.items():
            # FIELD-CONSOLIDATION-FIX 06.08.2025: Erweiterte Field-Initialisierung mit Konsolidierungslogik
            from minesearch.config.base import CSV_COLUMNS
            logger.info(f"[FIELD-INIT] Prüfe {len(CSV_COLUMNS)} erwartete Felder für Mine '{mine_name}' nach Konsolidierung")
            fields_added = 0
            for expected_field in CSV_COLUMNS:
                if expected_field not in ['Mine', 'Quellenangaben']:  # Skip meta fields
                    # CRITICAL: Apply same consolidation logic to expected fields
                    final_field_name, _ = _consolidate_and_rename_field(expected_field, "")
                    
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
                    # ENHANCED VALUE CLEANING 06.08.2025: Mehr Platzhalter-Werte erkennen
                    if not display_value or display_value.strip().upper() in ['', 'X', 'N/A', 'KEINE ANGABEN', 'NICHT VERFÜGBAR']:
                        display_value = 'Unbekannt'
                    best_values[field_name] = display_value
                
                # Erstelle detaillierte Aufschlüsselung für Modal
                detailed_breakdown[field_name] = {
                    'best_value': best_value_info,
                    'all_values': value_analysis,
                    'statistics': {
                        'total_sources': len(set([detail['ai_model'] for detail in field_info['value_details']])),
                        'unique_values': len(value_analysis),
                        'confidence_score': best_value_info['confidence_score'],
                        'total_real_sources': sum(len(detail['real_sources']) for detail in field_info['value_details'])
                    }
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

            result_item = {
                'mine_name': mine_name,
                'country': mine_data['country'],
                'region': mine_data['region'],
                
                # NEW UX DESIGN: Simplified main table data
                'best_values': best_values,  # Only best value per field for main table
                'overall_confidence': round(overall_confidence, 1),
                
                # NEW UX DESIGN: Complete breakdown for details modal
                'detailed_breakdown': detailed_breakdown,
                
                # Legacy compatibility (maintained for now)
                'ai_model_legend': ai_model_legend,  # Maps model numbers to AI model names
                'model_results': mine_data['model_results'],
                'model_count': mine_data['model_count'],
                'last_updated': mine_data['last_updated'].isoformat() if mine_data['last_updated'] else None,
                'total_sources': mine_data['total_sources'],
                'total_fields_found': len(best_values),
                
                # NEW METRICS
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
        
        return {
            "success": True,
            "data": {
                "consolidated_results": consolidated_results,
                "total_mines": len(consolidated_results),
                "total_results": len(all_results),
                "sort_by": sort_by,
                "order": order
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
            mine_data['model_count'] += 1
            
            # Letzte Aktualisierung
            if not mine_data['last_updated'] or result.search_timestamp > mine_data['last_updated']:
                mine_data['last_updated'] = result.search_timestamp
            
            # Quellen zählen
            mine_data['total_sources'] += len(result.sources or [])
            
            # Felder konsolidieren
            if result.structured_data:
                for original_field_name, field_value in result.structured_data.items():
                    final_field_name, processed_value = _consolidate_and_rename_field(original_field_name, field_value)
                    
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
                if not display_value or display_value.strip().upper() in ['', 'X', 'N/A', 'KEINE ANGABEN', 'NICHT VERFÜGBAR']:
                    display_value = 'Unbekannt'
                best_values[field_name] = display_value
            
            # Detaillierte Aufschlüsselung
            detailed_breakdown[field_name] = {
                'best_value': best_value_info,
                'all_values': value_analysis,
                'statistics': {
                    'total_sources': len(set([detail['ai_model'] for detail in field_info['value_details']])),
                    'unique_values': len(value_analysis),
                    'confidence_score': best_value_info['confidence_score'],
                    'total_real_sources': sum(len(detail['real_sources']) for detail in field_info['value_details'])
                }
            }
        
        # Calculate overall confidence
        confidence_scores = [details['best_value']['confidence_score'] 
                           for details in detailed_breakdown.values() 
                           if details['best_value']['confidence_score'] > 0]
        overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        
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
    header.extend(remaining_fields)
    
    csv_lines.append("|".join(header))
    
    # Daten-Zeilen - genau wie UI-Struktur
    for result in results:
        row = []
        
        # Metadaten-Felder
        for field_type in data_fields:
            if field_type == "mine_name":
                row.append(result.get("mine_name", ""))
            elif field_type == "country": 
                row.append(result.get("country", ""))
            elif field_type == "region":
                row.append(result.get("region", ""))
            elif field_type == "overall_confidence":
                row.append(str(result.get("overall_confidence", 0)) + "%")
            elif field_type == "model_count":
                row.append(str(result.get("model_count", 0)))
            elif field_type == "last_updated":
                row.append(result.get("last_updated", ""))
        
        # Restliche Felder aus best_values
        for field in remaining_fields:
            value = result["best_values"].get(field, "")
            # Escape Pipe-Zeichen in Werten
            escaped_value = str(value).replace("|", "\\|") if value else ""
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