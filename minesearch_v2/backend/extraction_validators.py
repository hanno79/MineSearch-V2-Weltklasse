"""
Author: rahn
Datum: 05.07.2025
Version: 1.0
Beschreibung: Validierungsfunktionen für Mining-Datenextraktion
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def is_placeholder_value(value: str, field: str = None) -> bool:
    """
    Prüft ob ein Wert ein verbotener Platzhalter ist
    
    Args:
        value: Zu prüfender Wert
        field: Feldname (optional für spezifische Prüfungen)
        
    Returns:
        True wenn Platzhalter erkannt, False sonst
    """
    if not value:
        return False
        
    value_lower = str(value).lower().strip()
    
    # ÄNDERUNG 11.07.2025: REGEL 10 ENFORCEMENT - Alle Platzhalter entfernen
    # Gemäß Regel 10: Felder LEER lassen wenn keine Daten gefunden
    general_placeholders = [
        'k.a', 'k.a.', 'n/a', 'n.a.', '-', '--', '---',
        'keine angabe', 'keine daten', 'nicht verfügbar',
        'no data', 'not found', 'not available'
    ]
    
    # ÄNDERUNG 11.07.2025: REGEL 10 ENFORCEMENT - ALLE unklaren Werte sind Platzhalter!
    # Gemäß Regel 10: "STRIKT VERBOTEN: Dummy-Werte und Fallback-Werte"
    # Wenn keine Daten gefunden werden: Feld LEER lassen - KEINE Platzhalter!
    dummy_expressions = [
        'unbekannt', 'unknown', 'nicht gefunden', 
        'keine spezifischen daten gefunden',
        'keine informationen verfügbar',
        'not specified', 'nicht spezifiziert',
        'not found', 'nicht verfügbar',
        'no data', 'keine daten',
        'information not available'
    ]
    
    # ALLE unklaren Aussagen sind Platzhalter und müssen entfernt werden
    if value_lower in dummy_expressions:
        logger.debug(f"[PLACEHOLDER] '{value}' ist ein DUMMY-Wert - REGEL 10 Verstoß!")
        return True
    
    if value_lower in general_placeholders:
        logger.debug(f"[PLACEHOLDER] '{value}' ist ein Platzhalter")
        return True
    
    # Grok-spezifische Probleme für alle Felder
    if any(marker in value.upper() for marker in ['UPDATE', 'NEU', 'CHANGED', 'AKTUELL', 'BREAKING']):
        logger.debug(f"[PLACEHOLDER] '{value}' enthält Grok UPDATE-Marker")
        return True
    
    # Feldspezifische Prüfungen
    if field == 'Restaurationskosten':
        # Unrealistisch niedrige Werte
        if re.match(r'^\$?\s*[0-9]\s*(?:CAD|CDN|USD)?$', value):
            logger.debug(f"[PLACEHOLDER] Restaurationskosten '{value}' ist Minimalwert")
            return True
        if re.match(r'^\$?\s*[1-9]\d?\s*(?:CAD|CDN|USD)?$', value) and 'million' not in value_lower:
            # Werte unter 100 ohne "million" sind unrealistisch
            logger.debug(f"[PLACEHOLDER] Restaurationskosten '{value}' ist zu niedrig")
            return True
    
    elif field == 'Eigentümer' or field == 'Betreiber':
        # Grok-spezifische Eigentümer-Probleme
        if value.upper() in ['UPDATE', 'CHANGED', 'UNKNOWN', 'AKTUELL']:
            logger.debug(f"[PLACEHOLDER] Eigentümer/Betreiber '{value}' ist Grok-Marker")
            return True
    
    logger.debug(f"[PLACEHOLDER] '{value}' ist KEIN Platzhalter für Feld '{field}'")
    return False


def validate_coordinate(value: str, coord_type: str) -> Optional[str]:
    """
    Validiert und formatiert Koordinaten
    
    Args:
        value: Koordinatenwert
        coord_type: 'x' für Latitude, 'y' für Longitude
        
    Returns:
        Formatierter Koordinatenwert oder None bei ungültigen Werten
    """
    if not value:
        return None
    
    # ÄNDERUNG 05.07.2025: Strikte Validierung gegen falsche Werte wie Jahre
    # Prüfe ob der Wert wie ein Jahr aussieht (4 Ziffern zwischen 1900 und 2100)
    if re.match(r'^(19|20)\d{2}$', str(value).strip()):
        logger.warning(f"Koordinate enthält Jahr statt Koordinate: {value}")
        return None
    
    # Prüfe auf andere nicht-numerische Inhalte
    if any(word in str(value).lower() for word in ['jahr', 'year', 'datum', 'date', 'aktiv', 'active', 'geschlossen', 'closed']):
        logger.warning(f"Koordinate enthält Text statt Koordinate: {value}")
        return None
    
    try:
        # Entferne Grad-Zeichen und Whitespace
        cleaned = re.sub(r'[°\s]+', '', str(value))
        
        # Versuche als Float zu parsen
        coord_float = float(cleaned)
        
        # ÄNDERUNG 05.07.2025: Mindestens 4 Nachkommastellen für echte Koordinaten
        # Prüfe ob genug Präzision vorhanden ist
        if '.' in str(value):
            decimal_places = len(str(value).split('.')[-1])
            if decimal_places < 4:
                logger.warning(f"Koordinate hat zu wenig Präzision ({decimal_places} Nachkommastellen): {value}")
                return None
        
        # Validiere Bereiche
        if coord_type == 'x':  # Latitude
            if -90 <= coord_float <= 90:
                return f"{coord_float:.6f}"
            else:
                logger.warning(f"Latitude außerhalb gültigen Bereichs: {coord_float}")
                return None
        else:  # Longitude
            if -180 <= coord_float <= 180:
                return f"{coord_float:.6f}"
            else:
                logger.warning(f"Longitude außerhalb gültigen Bereichs: {coord_float}")
                return None
                
    except ValueError:
        # Versuche DMS Format zu parsen
        dms_match = re.match(r'(\d+)°\s*(\d+)[\'′]\s*(\d+(?:\.\d+)?)[\"″]\s*([NSEW])', value)
        if dms_match:
            degrees = float(dms_match.group(1))
            minutes = float(dms_match.group(2))
            seconds = float(dms_match.group(3))
            direction = dms_match.group(4)
            
            # Konvertiere zu Dezimalgrad
            decimal = degrees + minutes/60 + seconds/3600
            
            # Negativ für Süd/West
            if direction in ['S', 'W']:
                decimal = -decimal
            
            # Validiere und gib zurück
            if coord_type == 'x' and -90 <= decimal <= 90:
                return f"{decimal:.6f}"
            elif coord_type == 'y' and -180 <= decimal <= 180:
                return f"{decimal:.6f}"
    
    return None


def validate_restoration_cost(value: str, currency: str = 'USD') -> Optional[str]:
    """
    Validiert Restaurationskosten und filtert unrealistische Werte
    
    Args:
        value: Kostenwert als String
        currency: Währung (default: USD)
        
    Returns:
        Validierter Wert oder None bei unrealistischen Werten
    """
    if not value:
        return None
    
    # ÄNDERUNG 11.07.2025: Jahr-Pattern Detection für Grok-Fehler
    # Prüfe ob der Wert wie ein Jahr aussieht (z.B. "CAD$2024.0 million")
    year_pattern_match = re.search(r'\$?(20[0-9]{2})\.?0?\s*(?:million|mio|millionen|billion)', value.lower())
    if year_pattern_match:
        year = int(year_pattern_match.group(1))
        logger.warning(f"Jahr als Restaurationskosten erkannt und gefiltert: {value} (Jahr: {year})")
        return None
    
    # Prüfe auf direkte Jahr-Pattern ohne Währungszeichen
    if re.match(r'^(20[0-9]{2})\.?0?$', value.strip()):
        logger.warning(f"Direktes Jahr als Restaurationskosten erkannt und gefiltert: {value}")
        return None
    
    # Prüfe auf UPDATE-Marker oder andere Grok-spezifische Probleme
    if any(marker in value.upper() for marker in ['UPDATE', 'NEU', 'CHANGED', 'AKTUELL']):
        logger.warning(f"UPDATE-Marker in Restaurationskosten erkannt und gefiltert: {value}")
        return None
    
    # ÄNDERUNG 06.07.2025: Erweiterte Pattern-Erkennung für k/K und thousand
    # Extrahiere numerischen Wert mit erweiterten Patterns
    value_lower = value.lower()
    
    # Prüfe verschiedene Formate
    # Format: 5k, 150K, 45.3M
    k_match = re.search(r'([\d,]+(?:\.\d+)?)\s*[kK](?:\s|$)', value)
    m_match = re.search(r'([\d,]+(?:\.\d+)?)\s*[mM](?:\s|$)', value)
    
    # Format: thousand, tausend
    thousand_match = re.search(r'([\d,]+(?:\.\d+)?)\s*(?:thousand|tausend)', value_lower)
    
    # Standard numerisches Format
    number_match = re.search(r'([\d,]+(?:\.\d+)?)', value)
    
    if not number_match:
        return None
    
    try:
        # Bestimme den Multiplikator basierend auf dem Format
        if k_match:
            # k/K = Tausend
            num_value = float(k_match.group(1).replace(',', '')) * 1000
            is_raw_value = True
        elif m_match:
            # m/M = Million
            num_value = float(m_match.group(1).replace(',', ''))
            is_millions = True
        elif thousand_match:
            # "thousand" = Tausend
            num_value = float(thousand_match.group(1).replace(',', '')) * 1000
            is_raw_value = True
        else:
            # Standard-Zahl
            num_value = float(number_match.group(1).replace(',', ''))
            # Prüfe ob "million" oder ähnliches im String
            is_millions = any(term in value_lower for term in ['million', 'mio', 'millones', 'miliar'])
            is_raw_value = not is_millions
        # ÄNDERUNG 06.07.2025: Variablen-Initialisierung korrigiert
        if 'is_millions' not in locals():
            is_millions = False
        if 'is_raw_value' not in locals():
            is_raw_value = False
        
        # Wenn Rohwert (k/K/thousand Format)
        if is_raw_value:
            # Werte unter 1.000 sind unrealistisch
            if num_value < 1000:
                logger.info(f"Restaurationskosten-Wert unter Schwellenwert (1.000) gefiltert: {value}")
                return None
            # Konvertiere zu Millionen für konsistente Ausgabe
            num_value = num_value / 1000000
            value = f"{num_value:.3f} Millionen {currency}"
        # Wenn nicht in Millionen angegeben (normale Zahl ohne Suffix)
        elif not is_millions:
            # ÄNDERUNG 06.07.2025: Schwellenwert auf 1.000 gesenkt für kleine Minen/Explorationsphasen
            # Werte unter 1.000 sind unrealistisch für Restaurationskosten
            if num_value < 1000:
                logger.info(f"Restaurationskosten-Wert unter Schwellenwert (1.000) gefiltert: {value}")
                return None
            # Konvertiere zu Millionen
            num_value = num_value / 1000000
            value = f"{num_value:.3f} Millionen {currency}"
        
        # ÄNDERUNG 06.07.2025: Schwellenwert auf 0.001 Millionen (= 1.000 real) gesenkt
        # Prüfe auf unrealistisch niedrige Millionen-Werte
        if is_millions and num_value < 0.001:  # Unter 1.000 in echter Währung
            logger.info(f"Millionen-Wert unter Schwellenwert (0.001 = 1.000 real) gefiltert: {value}")
            return None
        
        # Prüfe auf unrealistisch hohe Werte (über 10 Milliarden)
        if is_millions and num_value > 10000:
            logger.info(f"Unrealistisch hoher Millionen-Wert gefiltert: {value}")
            return None
        
        return value
        
    except ValueError:
        logger.warning(f"Konnte Restaurationskosten nicht parsen: {value}")
        return None


def validate_year(value: str, field_type: str = 'general') -> Optional[str]:
    """
    Validiert Jahresangaben
    
    Args:
        value: Jahreswert als String
        field_type: Art des Jahresfeldes ('costs', 'document', 'production')
        
    Returns:
        Validiertes Jahr oder None
    """
    if not value:
        return None
    
    # Extrahiere 4-stellige Jahreszahl
    year_match = re.search(r'\b(19\d{2}|20\d{2})\b', value)
    if not year_match:
        return None
    
    year = int(year_match.group(1))
    current_year = 2025  # Aktuelles Jahr
    
    # Validiere je nach Feldtyp
    if field_type == 'costs':
        # Kosten-Jahre sollten nicht zu alt sein (max 20 Jahre)
        if year < current_year - 20:
            logger.info(f"Kosten-Jahr zu alt: {year}")
            return None
        # Und nicht in der Zukunft
        if year > current_year:
            return None
    
    elif field_type == 'document':
        # Dokumente können älter sein, aber nicht aus der Zukunft
        if year > current_year:
            return None
        # Aber auch nicht älter als 1950
        if year < 1950:
            return None
    
    elif field_type == 'production':
        # Produktionsjahre können sehr alt sein (historische Minen)
        if year < 1800:
            return None
        # Produktionsstart kann in naher Zukunft liegen (geplante Minen)
        if year > current_year + 10:
            return None
    
    return str(year)


def validate_area(value: str) -> Optional[str]:
    """
    Validiert Flächenangaben
    
    Args:
        value: Flächenangabe als String
        
    Returns:
        Validierte Fläche oder None
    """
    if not value:
        return None
    
    # Extrahiere numerischen Wert
    number_match = re.search(r'([\d,]+(?:\.\d+)?)', value)
    if not number_match:
        return None
    
    try:
        area = float(number_match.group(1).replace(',', ''))
        
        # Unrealistisch kleine Flächen (unter 0.01 km²)
        if area < 0.01:
            logger.info(f"Unrealistisch kleine Minenfläche: {area} km²")
            return None
        
        # Unrealistisch große Flächen (über 10.000 km²)
        if area > 10000:
            logger.info(f"Unrealistisch große Minenfläche: {area} km²")
            return None
        
        return f"{area} km²"
        
    except ValueError:
        return None