"""
Author: rahn
Datum: 11.09.2025
Version: 1.0  
Beschreibung: Utility-Funktionen für Konsolidierte Ergebnis-Verarbeitung (Refactoring aus consolidated_results.py)
"""

import logging
import re
from typing import Optional, Dict, List, Any
from collections import defaultdict

# Import ValueNormalizer for semantic value equivalence
from minesearch.value_normalizer import value_normalizer

logger = logging.getLogger(__name__)


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
    PHASE 12.1: Intelligente Bewertung von Feldwerten mit Smart Analytics
    
    Bewertet die Qualität und Zuverlässigkeit der gefundenen Werte über alle Modelle hinweg
    Berücksichtigt: Konsistenz, Quellen-Qualität, semantische Ähnlichkeit, Template-Detection
    """
    
    logger.debug(f"[ANALYZE] Analysiere {len(value_details)} Werte für Feld '{field_name}'")
    
    # Schritt 1: Template/Placeholder Detection (REGEL 10)
    clean_values = []
    for detail in value_details:
        clean_value = _normalize_placeholder_value(detail.get('value'))
        if clean_value is not None:  # Nur echte Werte weiterverarbeiten
            detail_copy = detail.copy()
            detail_copy['value'] = clean_value
            detail_copy['original_value'] = detail.get('value')  # Original für Logging
            clean_values.append(detail_copy)
    
    logger.debug(f"[ANALYZE] Nach Template-Bereinigung: {len(clean_values)}/{len(value_details)} Werte übrig")
    
    if not clean_values:
        logger.debug(f"[ANALYZE] Feld '{field_name}': Alle Werte waren Templates/Platzhalter")
        return {
            'total_values': len(value_details),
            'valid_values': 0,
            'unique_values': 0,
            'confidence_score': 0.0,
            'consistency_score': 0.0,
            'best_value': None,
            'source_quality': 'none',
            'template_filtered': len(value_details)
        }
    
    # Schritt 2: Werte-Gruppierung mit semantischer Ähnlichkeit
    value_groups = defaultdict(list)
    
    for detail in clean_values:
        value = detail['value']
        model_id = detail.get('model_id', 'unknown')
        
        # Finde semantisch ähnliche Gruppe oder erstelle neue
        grouped = False
        for existing_value in value_groups:
            if value_normalizer.are_values_equivalent(value, existing_value, field_name):
                value_groups[existing_value].append(detail)
                grouped = True
                logger.debug(f"[ANALYZE] '{value}' ({model_id}) → Gruppe '{existing_value}'")
                break
        
        if not grouped:
            value_groups[value].append(detail)
            logger.debug(f"[ANALYZE] '{value}' ({model_id}) → Neue Gruppe")
    
    logger.debug(f"[ANALYZE] {len(value_groups)} semantische Gruppen identifiziert")
    
    # Schritt 3: Gruppen-Bewertung und Best-Value-Ermittlung
    scored_groups = []
    
    for group_value, group_details in value_groups.items():
        # Basis-Score: Anzahl unterstützender Modelle
        support_score = len(group_details) * 10
        
        # Model-Quality-Bonus
        model_bonus = 0
        premium_models = ['claude-3.5-sonnet', 'gpt-4o', 'gemini-pro']
        search_models = ['tavily', 'exa', 'perplexity']
        
        for detail in group_details:
            model_id = detail.get('model_id', '')
            if any(premium in model_id.lower() for premium in premium_models):
                model_bonus += 15
            elif any(search in model_id.lower() for search in search_models):
                model_bonus += 10
            else:
                model_bonus += 5
        
        # Value-Quality-Score (Länge, Spezifität, etc.)
        value_quality_score = min(len(str(group_value)), 50)  # Max 50 Punkte für Länge
        
        # Numerische Werte bevorzugen für numerische Felder
        numeric_bonus = 0
        numeric_fields = ['production_volume', 'area_qkm', 'coordinates', 'year']
        if field_name and any(nf in field_name.lower() for nf in numeric_fields):
            try:
                float(str(group_value).replace(',', '.'))
                numeric_bonus = 20
            except ValueError:
                pass
        
        total_score = support_score + model_bonus + value_quality_score + numeric_bonus
        
        scored_groups.append({
            'value': group_value,
            'details': group_details,
            'support_count': len(group_details),
            'support_score': support_score,
            'model_bonus': model_bonus,
            'value_quality': value_quality_score,
            'numeric_bonus': numeric_bonus,
            'total_score': total_score
        })
        
        logger.debug(f"[ANALYZE] Gruppe '{group_value}': {total_score} Punkte ({len(group_details)} Support, {model_bonus} Model-Bonus)")
    
    # Sortiere Gruppen nach Score (höchster zuerst)
    scored_groups.sort(key=lambda x: x['total_score'], reverse=True)
    
    # Schritt 4: Konsistenz-Score berechnen
    if len(scored_groups) == 1:
        consistency_score = 100.0  # Perfekte Konsistenz
    else:
        # Anteil der Modelle die den Top-Value unterstützen
        top_support = scored_groups[0]['support_count']
        total_models = len(clean_values)
        consistency_score = (top_support / total_models) * 100
    
    # Schritt 5: Konfidenz-Score berechnen
    if not scored_groups:
        confidence_score = 0.0
    else:
        max_possible_score = len(clean_values) * 25 + 50  # Theoretisches Maximum
        actual_score = scored_groups[0]['total_score']
        confidence_score = min((actual_score / max_possible_score) * 100, 100.0)
    
    # Schritt 6: Ergebnis zusammenstellen
    analysis_result = {
        'total_values': len(value_details),
        'valid_values': len(clean_values),
        'unique_values': len(scored_groups),
        'confidence_score': round(confidence_score, 1),
        'consistency_score': round(consistency_score, 1),
        'template_filtered': len(value_details) - len(clean_values),
        'groups': scored_groups[:3]  # Top 3 Gruppen für Details
    }
    
    if scored_groups:
        analysis_result['best_value'] = scored_groups[0]['value']
        analysis_result['best_value_support'] = scored_groups[0]['support_count']
        
        # Source Quality Assessment
        best_models = [d.get('model_id', '') for d in scored_groups[0]['details']]
        if any(pm in ' '.join(best_models).lower() for pm in premium_models):
            analysis_result['source_quality'] = 'premium'
        elif any(sm in ' '.join(best_models).lower() for sm in search_models):
            analysis_result['source_quality'] = 'search'
        else:
            analysis_result['source_quality'] = 'standard'
    else:
        analysis_result['best_value'] = None
        analysis_result['source_quality'] = 'none'
    
    logger.debug(f"[ANALYZE] Feld '{field_name}' Analyse komplett: Konfidenz {confidence_score:.1f}%, Konsistenz {consistency_score:.1f}%")
    
    return analysis_result


def _calculate_best_value(value_analysis, field_name=None):
    """
    PHASE 12.2: Ermittlung des besten Werts basierend auf intelligenter Analyse
    
    Nutzt die Analyse-Ergebnisse um den zuverlässigsten Wert zu bestimmen
    Berücksichtigt: Konfidenz, Konsistenz, Quellen-Qualität
    
    Returns: Der beste verfügbare Wert oder None
    """
    
    logger.debug(f"[BEST-VALUE] Berechne besten Wert für Feld '{field_name}'")
    
    if not value_analysis or not value_analysis.get('groups'):
        logger.debug(f"[BEST-VALUE] Keine validen Gruppen für '{field_name}'")
        return None
    
    best_group = value_analysis['groups'][0]
    best_value = best_group['value']
    
    # Qualitäts-Gating: Nur Werte mit ausreichender Konfidenz verwenden
    confidence_threshold = 30.0  # Mindest-Konfidenz 30%
    actual_confidence = value_analysis.get('confidence_score', 0.0)
    
    if actual_confidence < confidence_threshold:
        logger.debug(f"[BEST-VALUE] Konfidenz zu niedrig: {actual_confidence:.1f}% < {confidence_threshold}% für '{field_name}'")
        return None
    
    # Konsistenz-Check: Bei sehr niedriger Konsistenz vorsichtig sein
    consistency = value_analysis.get('consistency_score', 0.0)
    if consistency < 25.0 and value_analysis.get('unique_values', 0) > 2:
        logger.warning(f"[BEST-VALUE] Niedrige Konsistenz ({consistency:.1f}%) bei '{field_name}' mit {value_analysis.get('unique_values')} verschiedenen Werten")
        # Trotzdem den besten Wert verwenden, aber loggen
    
    logger.debug(f"[BEST-VALUE] Gewählt für '{field_name}': '{best_value}' (Konfidenz: {actual_confidence:.1f}%, Support: {best_group['support_count']})")
    
    return best_value