"""
Author: rahn
Datum: 05.07.2025
Version: 1.0
Beschreibung: Verarbeitungsfunktionen für Mining-Datenextraktion
"""

import re
import logging
from typing import Dict, Optional, List, Any
from minesearch.utils import get_country_config

logger = logging.getLogger(__name__)


def is_template_or_dummy_value(value: str, field: str = None) -> bool:
    """
    CLEAN DATA AT SOURCE FIX 20.08.2025: Template/Dummy-Detection für Pre-Extraction Filtering
    
    Prüft ob ein AI-Response-Wert ein Template oder Dummy-Wert ist, bevor er in die DB gespeichert wird.
    Diese Funktion ist die erste Verteidigungslinie gegen Template-Werte aus AI-Responses.
    
    Args:
        value: Zu prüfender Wert aus AI-Response
        field: Feldname für spezifische Prüfungen
        
    Returns:
        True wenn Template/Dummy-Wert (soll abgelehnt werden), False wenn echter Wert
    """
    if not value or not str(value).strip():
        return True  # Leere Werte sind Dummy-Werte
        
    value_str = str(value).strip()
    value_lower = value_str.lower()
    
    # PHASE 1: DIREKTE TEMPLATE-MARKER - ABSOLUTE PRIORITÄT
    if value_str.startswith('TEMPLATE:'):
        logger.warning(f"[TEMPLATE DETECTION] Direkter TEMPLATE-Marker: '{value_str}'")
        return True
    
    # PHASE 2: CSV-HEADER-ÄHNLICHE TEMPLATE-PATTERNS
    template_patterns = [
        # Exact CSV header patterns that AI models often return as "examples"
        r'^Rohstoffabbau \(Gold[/\s]*Kupfer[/\s]*Kohle[/\s]*usw\.?\)$',
        r'^Minentyp \(Untertage[/\s]*Open-Pit[/\s]*usw\.?\)$', 
        r'^\(Gold[/\s]*Kupfer[/\s]*Kohle[/\s]*usw\.?\)$',
        r'^\(Untertage[/\s]*Open-Pit[/\s]*usw\.?\)$',
        r'^\(aktiv[/\s]*geplant[/\s]*geschlossen[/\s]*sonstiges\)$',
        # Template lists/patterns that AI models generate
        r'^(Gold|Kupfer|Kohle|Iron|Copper|Coal)[/\s]+(Kupfer|Gold|Iron|Copper)[/\s]+.*usw\.?$',
        r'^(Untertage|Open-Pit|Underground|Surface)[/\s]+(Open-Pit|Untertage|Surface)[/\s]+.*usw\.?$',
        r'^(aktiv|geplant|geschlossen|active|planned|closed)[/\s]+.*sonstiges$',
        # ADDITIONAL: Common template patterns found in real data
        r'^Gold[/\s]*Kupfer[/\s]*Kohle[/\s]*usw\.\)$',  # "Gold/ Kupfer/ Kohle/ usw.)"
        r'^Untertage[/\s]*Open-Pit[/\s]*usw\.\)$',      # "Untertage/ Open-Pit/ usw.)"
        r'^LEER \(keine verifizierte.*\)$',              # "LEER (keine verifizierte Information gefunden)"
    ]
    
    import re
    for pattern in template_patterns:
        if re.match(pattern, value_str, re.IGNORECASE):
            logger.warning(f"[TEMPLATE DETECTION] Template-Pattern erkannt: '{value_str}'")
            return True
    
    # PHASE 3: "NOT SPECIFIED" VARIANTEN (User-reported Problem)
    not_specified_patterns = [
        r'^Not specified in available.*',
        r'^No specific.*information.*',
        r'^Keine spezifischen.*Daten.*',
        r'^Not specified in the.*sources.*'
    ]
    
    for pattern in not_specified_patterns:
        if re.match(pattern, value_str, re.IGNORECASE):
            logger.warning(f"[TEMPLATE DETECTION] 'Not specified' Pattern: '{value_str}'")
            return True
    
    # PHASE 4: AI-META-RESPONSES (User-reported Problem 21.08.2025)
    # AI-generierte Template-Texte mit Meta-Anweisungen, die durch normale Filter rutschen
    ai_meta_patterns = [
        # Der spezifische gemeldete Fall
        r'.*junior mining company.*without concrete data.*per.*rules.*',
        r'.*But without concrete data.*should leave.*fields.*blank.*per.*rules.*',
        # Generische AI-Meta-Response Pattern
        r'.*should leave.*blank.*per.*rules.*',
        r'.*I should.*blank.*rules.*',
        r'.*As per.*rules.*fields.*blank.*',
        r'.*without concrete data.*leave.*blank.*',
        r'.*per the rules.*fields.*blank.*',
        r'.*following the rules.*blank.*',
        # Weitere AI-Meta-Anweisungen
        r'.*cannot specify.*without.*evidence.*',
        r'.*cannot specify.*without proper.*',
        r'.*would be inappropriate.*without.*data.*',
        r'.*should not provide.*without.*verification.*',
        r'.*extraction rules.*should.*blank.*',
        r'.*per.*extraction.*rules.*'
    ]
    
    for pattern in ai_meta_patterns:
        if re.search(pattern, value_str, re.IGNORECASE):
            logger.warning(f"[TEMPLATE DETECTION] AI-Meta-Response erkannt: '{value_str}'")
            return True
    
    # PHASE 5: EXPLIZITE DUMMY-WERTE
    explicit_dummies = [
        'placeholder', 'dummy', 'example', 'template', 'sample', 'test',
        'beispiel', 'muster', 'vorlage', 'beispieldaten',
        'not found', 'not available', 'not specified', 'unknown', 'n/a', 'tbd',
        'nicht gefunden', 'nicht verfügbar', 'unbekannt', 'k.a.', 'keine angabe'
    ]
    
    if value_lower in explicit_dummies:
        logger.warning(f"[TEMPLATE DETECTION] Expliziter Dummy-Wert: '{value_str}'")
        return True
    
    # PHASE 6: FELD-SPEZIFISCHE DUMMY-DETECTION
    if field == 'Restaurationskosten':
        # Unrealistic low values that are obvious placeholders
        if re.match(r'^\$?\s*[0-9]{1,2}(\.[0-9])?\s*(million|mio|usd|cad)?$', value_lower):
            logger.warning(f"[TEMPLATE DETECTION] Unrealistische Restaurationskosten: '{value_str}'")
            return True
    elif field in ['Betreiber', 'Eigentümer']:
        # Field labels appearing as values (AI model confusion)
        if value_lower in ['betreiber', 'eigentümer', 'owner', 'operator', 'company', 'unternehmen']:
            logger.warning(f"[TEMPLATE DETECTION] Field-Label als Wert: '{value_str}'")
            return True
    
    # Value passed all template/dummy checks - it's a real data value
    logger.debug(f"[TEMPLATE DETECTION] Echter Wert erkannt: '{value_str}'")
    return False


def normalize_field_value(value: str) -> str:
    """
    FELDANZEIGE-FIX 14.07.2025: Normalisiert Feldwerte für einheitliche Anzeige
    CRITICAL-FIX 19.08.2025: Drastisch reduzierte Template-Pattern-Erkennung - verhindert Konvertierung echter Daten
    
    Args:
        value: Rohwert aus Provider
        
    Returns:
        Normalisierter Wert: "nichts gefunden" für echte Nicht-Funde, echte Daten bleiben unverändert
    """
    if not value or value.strip() == '':
        # Komplett leer = nicht gesucht (bleibt leer)
        return ''
    
    value_cleaned = value.strip()
    
    # CRITICAL-FIX 19.08.2025 + 20.08.2025: Erweiterte Template-Placeholder-Liste
    # Echte Template-Placeholder, die definitiv keine Daten enthalten
    explicit_placeholders = [
        'N/A', 'n/a', 'N.A.', 'n.a.',
        '-', '—', '–',
        'k.A.', 'k.a.', 'K.A.',
        'unknown', 'Unknown', 'UNKNOWN',
        'not available', 'Not available', 'NOT AVAILABLE',
        'not found', 'Not found', 'NOT FOUND',
        'no data', 'No data', 'NO DATA',
        # ZUSATZ 20.08.2025: User-reported Placeholder-Varianten
        'not specified', 'Not specified', 'NOT SPECIFIED',
        'not specified in available', 'Not specified in available ...',
        'Not specified in available data', 'not specified in available data',
        'nicht spezifiziert', 'Nicht spezifiziert',
        'nicht angegeben', 'Nicht angegeben',
        'unbekannt', 'Unbekannt', 'UNBEKANNT'
    ]
    
    # CRITICAL-FIX 19.08.2025: Nur EXAKTE Matches - keine Pattern-Matching mehr
    # Das verhindert dass echte Daten wie "Company Ltd." zu Template-Werten konvertiert werden
    if value_cleaned in explicit_placeholders:
        return 'nichts gefunden'  # User Request: "schreiben wir einfach nur überall 'nichts gefunden'"
    
    # CRITICAL-FIX 19.08.2025: Alle anderen Werte (inkl. echte Daten) bleiben UNVERÄNDERT
    # Keine aggressive Pattern-Matching oder LEER-Konvertierung mehr
    return value


def process_restoration_costs(value: str, full_match: str, currency: str) -> str:
    """
    Verarbeitet und formatiert Restaurationskosten
    
    Args:
        value: Extrahierter Wert
        full_match: Vollständiger Match-String
        currency: Währung
        
    Returns:
        Formatierter Kostenwert
    """
    try:
        # Entferne Kommas für Parsing
        clean_value = value.replace(',', '')
        amount = float(clean_value)
        
        # Prüfe ob bereits in Millionen
        if any(term in full_match.lower() for term in ['million', 'mio', 'millones', 'miliar']):
            # Für Indonesien: 1 miliar = 1 billion = 1000 million
            if 'miliar' in full_match.lower() and currency == 'IDR':
                amount = amount * 1000
            return f"{amount:.1f} Millionen {currency}"
        else:
            # Prüfe ob Wert realistisch ist (mindestens 100.000)
            if amount >= 100000:
                # Konvertiere zu Millionen
                amount_millions = amount / 1000000
                return f"{amount_millions:.1f} Millionen {currency}"
            else:
                # Zu klein, wahrscheinlich bereits in Millionen gemeint
                return f"{amount:.1f} Millionen {currency}"
    except ValueError:
        return f"{value} {currency}"


def process_activity_status(status_text: str) -> str:
    """
    Standardisiert Aktivitätsstatus-Angaben
    
    Args:
        status_text: Roher Status-Text
        
    Returns:
        Standardisierter Status
    """
    status_lower = status_text.lower().strip()
    
    # Mapping zu standardisierten Werten
    status_mapping = {
        # Aktiv
        'aktiv': 'Aktiv',
        'active': 'Aktiv',
        'in betrieb': 'Aktiv',
        'operating': 'Aktiv',
        'produktion': 'Aktiv',
        'production': 'Aktiv',
        
        # Geschlossen
        'geschlossen': 'Geschlossen',
        'closed': 'Geschlossen',
        'stillgelegt': 'Geschlossen',
        'abandoned': 'Geschlossen',
        'eingestellt': 'Geschlossen',
        
        # Temporär stillgelegt
        'temporär stillgelegt': 'Temporär stillgelegt',
        'temporarily closed': 'Temporär stillgelegt',
        'care and maintenance': 'Temporär stillgelegt',
        'suspended': 'Temporär stillgelegt',
        
        # In Entwicklung
        'in entwicklung': 'In Entwicklung',
        'under development': 'In Entwicklung',
        'developing': 'In Entwicklung',
        'construction': 'In Entwicklung',
        
        # Geplant
        'geplant': 'Geplant',
        'planned': 'Geplant',
        'proposed': 'Geplant',
        
        # Exploration
        'exploration': 'Explorationsphase',
        'explorationsphase': 'Explorationsphase',
        'exploring': 'Explorationsphase'
    }
    
    # Suche nach Übereinstimmungen
    for key, standardized in status_mapping.items():
        if key in status_lower:
            return standardized
    
    # Wenn keine Übereinstimmung, gib Original zurück (kapitalisiert)
    return status_text.strip().capitalize()


def split_country_region(data: Dict[str, str]) -> Dict[str, str]:
    """
    Trennt kombinierte Country/Region Angaben
    
    Args:
        data: Daten-Dictionary
        
    Returns:
        Aktualisiertes Dictionary
    """
    # Wenn Country und Region leer sind, aber einer von beiden was enthält
    if data.get('Country') and ',' in data['Country'] and not data.get('Region'):
        parts = data['Country'].split(',', 1)
        if len(parts) == 2:
            data['Region'] = parts[0].strip()
            data['Country'] = parts[1].strip()
    
    # Spezialbehandlung für bekannte Regionen
    if data.get('Region'):
        region = data['Region']
        # Quebec/Kanada Korrektur
        if region.lower() in ['quebec', 'québec'] and not data.get('Country'):
            data['Country'] = 'Kanada'
        # Chile Regionen
        elif any(chilean_region in region.lower() for chilean_region in 
                ['antofagasta', 'atacama', 'coquimbo', 'valparaíso']):
            if not data.get('Country'):
                data['Country'] = 'Chile'
    
    return data


def find_region_from_content(country: str, content: str, country_config: Dict) -> str:
    """
    Findet Region basierend auf Land und Inhalt
    
    Args:
        country: Land
        content: Textinhalt
        country_config: Länderspezifische Konfiguration
        
    Returns:
        Gefundene Region oder leerer String
    """
    if not country_config:
        return ""
    
    # Hole regions für das Land
    regions = country_config.get('regions', [])
    if not regions:
        return ""
    
    content_lower = content.lower()
    
    # Suche nach Regionen im Text
    for region in regions:
        # Erstelle Varianten für die Suche
        region_variants = [region.lower()]
        
        # Füge Varianten ohne Akzente hinzu
        accent_map = {
            'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
            'á': 'a', 'à': 'a', 'â': 'a', 'ä': 'a',
            'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
            'ó': 'o', 'ò': 'o', 'ô': 'o', 'ö': 'o',
            'ú': 'u', 'ù': 'u', 'û': 'u', 'ü': 'u',
            'ñ': 'n'
        }
        
        region_no_accent = region.lower()
        for accented, plain in accent_map.items():
            region_no_accent = region_no_accent.replace(accented, plain)
        
        if region_no_accent != region.lower():
            region_variants.append(region_no_accent)
        
        # Suche nach jeder Variante
        for variant in region_variants:
            # Suche mit Wortgrenzen
            if re.search(r'\b' + re.escape(variant) + r'\b', content_lower):
                return region
    
    return ""


def process_sources(data: Dict[str, str], all_sources: List[Dict[str, Any]]) -> Dict[str, str]:
    """
    Verarbeitet und formatiert Quellenangaben
    
    Args:
        data: Daten-Dictionary
        all_sources: Liste aller gefundenen Quellen
        
    Returns:
        Aktualisiertes Dictionary mit formatierten Quellen
    """
    if not all_sources:
        data['Quellenangaben'] = 'Keine spezifischen Quellen gefunden'
        return data
    
    # Formatiere Quellen
    formatted_sources = []
    for idx, source in enumerate(all_sources[:10], 1):  # Maximal 10 Quellen
        source_text = f"[{idx}] {source.get('title', source.get('value', 'Unbekannte Quelle'))}"
        if source.get('url'):
            source_text += f" - {source['url']}"
        formatted_sources.append(source_text)
    
    data['Quellenangaben'] = '\n'.join(formatted_sources)
    
    return data


def post_process_data(data: Dict[str, str], content: str, country_config: Dict) -> Dict[str, str]:
    """
    Post-Processing der extrahierten Daten
    
    Args:
        data: Extrahierte Daten
        content: Original-Content
        country_config: Länderspezifische Konfiguration
        
    Returns:
        Verarbeitete Daten
    """
    # Country aus dem Inhalt extrahieren wenn nicht vorhanden
    if not data.get('Country') and country_config:
        data['Country'] = country_config.get('name', '')
    
    # Trenne Country/Region wenn nötig
    data = split_country_region(data)
    
    # Versuche Region zu finden wenn nicht vorhanden
    if not data.get('Region') and data.get('Country'):
        region = find_region_from_content(data['Country'], content, country_config)
        if region:
            data['Region'] = region
    
    # Bereinige Aktivitätsstatus
    if data.get('Aktivitätsstatus'):
        data['Aktivitätsstatus'] = process_activity_status(data['Aktivitätsstatus'])
    
    # Formatiere Koordinaten
    for coord_field in ['x-Koordinate', 'y-Koordinate']:
        if data.get(coord_field):
            # Stelle sicher, dass Koordinaten im richtigen Format sind
            coord_value = data[coord_field]
            # Entferne zusätzliche Zeichen
            coord_value = re.sub(r'[°\s]+$', '', coord_value)
            data[coord_field] = coord_value
    
    # FELDANZEIGE-FIX 14.07.2025: Normalisiere alle Feldwerte für einheitliche Anzeige
    for field, value in data.items():
        if isinstance(value, str):
            data[field] = normalize_field_value(value)
    
    return data


def clean_field_value(value: str, field: str) -> str:
    """
    Bereinigt extrahierte Feldwerte
    
    Args:
        value: Rohwert
        field: Feldname
        
    Returns:
        Bereinigter Wert
    """
    if not value:
        return ""
    
    # Entferne führende/nachfolgende Leerzeichen
    value = value.strip()
    
    # Entferne mehrfache Leerzeichen
    value = re.sub(r'\s+', ' ', value)
    
    # Feldspezifische Bereinigung
    if field in ['Eigentümer', 'Betreiber']:
        # Entferne Klammern am Ende
        value = re.sub(r'\s*\([^)]*\)\s*$', '', value)
        # Entferne "Ltd.", "Inc." etc. am Ende wenn zu lang
        if len(value) > 50:
            value = re.sub(r'\s+(Ltd\.?|Inc\.?|Corp\.?|Company|Corporation)\s*$', '', value, flags=re.I)
    
    elif field == 'Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)':
        # Standardisiere Trennzeichen
        value = re.sub(r'[;/]', ', ', value)
        # Entferne Duplikate
        minerals = [m.strip() for m in value.split(',')]
        minerals = list(dict.fromkeys(minerals))  # Erhält Reihenfolge
        value = ', '.join(minerals)
    
    elif field == 'Minentyp (Untertage/ Open-Pit/ usw.)':
        # DATENKONSISTENZ-FIX 19.07.2025: Entferne störendes Präfix
        # Entferne "(Untertage/ Open-Pit/ usw.): " oder ähnliche Präfixe
        prefixes_to_remove = [
            r'Untertage/ Open-Pit/ usw\.\):\s*',
            r'\(Untertage/ Open-Pit/ usw\.\):\s*',
            r'Minentyp \(Untertage/ Open-Pit/ usw\.\):\s*',
            r'Typ:\s*',
            r'Mine type:\s*',
            r'Type:\s*'
        ]
        
        for prefix_pattern in prefixes_to_remove:
            value = re.sub(prefix_pattern, '', value, flags=re.IGNORECASE)
        
        # Bereinige auch häufige redundante Angaben
        value = re.sub(r'^\(Untertage/ Open-Pit/ usw\.\):?\s*', '', value, flags=re.IGNORECASE)
        
        # Entferne führende/nachfolgende Leerzeichen nach Bereinigung
        value = value.strip()
    
    # DATENKONSISTENZ-FIX 19.07.2025: Normalisiere LEER-Werte NACH allen Bereinigungen
    value = normalize_field_value(value)
    
    return value