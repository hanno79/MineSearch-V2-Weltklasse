"""
Author: Pattern Enhancement Researcher
Datum: 31.07.2025
Version: 1.0
Beschreibung: Erweiterte Pattern-Definitionen für verbesserte Mining-Datenextraktion

FORSCHUNGSERGEBNISSE:
- Fehlende Pattern: "derzeit etwa [ZAHL] [EINHEIT] [ROHSTOFF] pro [ZEITRAUM]"
- Fehlende Pattern: "[ROHSTOFF]. [Beschreibung] so primary commodity..."
- Cross-Field-Logik: Rohstoff + Menge in einem Text
- Intelligente Mengen-Extraktion mit Einheiten-Normalisierung
- Minentyp-Bereinigung für Auflistungen
"""

import re
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


def get_enhanced_production_patterns() -> List[str]:
    """
    ENHANCED PATTERN 31.07.2025: Erweiterte Pattern für Rohstoff + Produktionsmengen
    
    Erkennt komplexe Textstrukturen wie:
    - "derzeit etwa 270.000 Unzen Gold pro Jahr"
    - "currently produces 50,000 tonnes copper annually"
    - "jährliche Förderung von 1.2 Millionen Tonnen Eisenerz"
    
    Returns:
        Liste mit Regex-Patterns für kombinierte Rohstoff/Mengen-Extraktion
    """
    return [
        # DEUTSCH: "derzeit etwa [ZAHL] [EINHEIT] [ROHSTOFF] pro [ZEITRAUM]"
        r'derzeit\s+etwa\s+([\d,\.]+)\s+(Unzen|Tonnen|kg|t|Barrel|m³)\s+(Gold|Kupfer|Silber|Zink|Blei|Nickel|Kohle|Eisenerz|Öl|Gas)\s+pro\s+(Jahr|Monat|Tag)',
        
        # DEUTSCH: Varianten mit "jährlich"
        r'([\d,\.]+)\s+(Unzen|Tonnen|kg|t|Barrel|m³)\s+(Gold|Kupfer|Silber|Zink|Blei|Nickel|Kohle|Eisenerz|Öl|Gas)\s+jährlich',
        r'jährliche?\s+(?:Förderung|Produktion)\s+von\s+([\d,\.]+)\s+(Millionen\s+)?(Unzen|Tonnen|kg|t|Barrel|m³)\s+(Gold|Kupfer|Silber|Zink|Blei|Nickel|Kohle|Eisenerz)',
        r'produziert\s+jährlich\s+([\d,\.]+)\s+(Unzen|Tonnen|kg|t)\s+(Gold|Kupfer|Silber|Zink|Blei|Nickel|Kohle|Eisenerz)',
        
        # ENGLISCH: "currently produces [AMOUNT] [UNIT] [COMMODITY] annually"
        r'currently\s+produces?\s+([\d,\.]+)\s+(ounces?|tonnes?|tons?|kg|barrels?|m³)\s+(?:of\s+)?(gold|copper|silver|zinc|lead|nickel|coal|iron\s+ore|oil|gas)\s+annually',
        r'produces?\s+([\d,\.]+)\s+(ounces?|tonnes?|tons?|kg|barrels?)\s+(?:of\s+)?(gold|copper|silver|zinc|lead|nickel|coal|iron\s+ore)\s+per\s+(year|month|day)',
        r'annual\s+production\s+of\s+([\d,\.]+)\s+(ounces?|tonnes?|tons?|kg)\s+(?:of\s+)?(gold|copper|silver|zinc|lead|nickel|coal|iron\s+ore)',
        
        # FRANZÖSISCH (Quebec): "production annuelle de [AMOUNT] [UNIT] [COMMODITY]"
        r'production\s+annuelle\s+de\s+([\d,\.]+)\s+(onces?|tonnes?|kg|barils?)\s+(?:de\s+|d\')?(or|cuivre|argent|zinc|plomb|nickel|charbon|minerai\s+de\s+fer)',
        r'produit\s+annuellement\s+([\d,\.]+)\s+(onces?|tonnes?|kg)\s+(?:de\s+|d\')?(or|cuivre|argent|zinc|plomb|nickel|charbon)',
        
        # SPANISCH (Südamerika): "produce anualmente [AMOUNT] [UNIT] de [COMMODITY]"
        r'produce\s+anualmente\s+([\d,\.]+)\s+(onzas?|toneladas?|kg|barriles?)\s+de\s+(oro|cobre|plata|zinc|plomo|níquel|carbón|mineral\s+de\s+hierro)',
        r'producción\s+anual\s+de\s+([\d,\.]+)\s+(onzas?|toneladas?|kg)\s+de\s+(oro|cobre|plata|zinc|plomo|níquel|carbón)',
        
        # INDONESISCH: "memproduksi [AMOUNT] [UNIT] [COMMODITY] per tahun"
        r'memproduksi\s+([\d,\.]+)\s+(ons|ton|kg|barel)\s+(emas|tembaga|perak|seng|timbal|nikel|batubara|bijih\s+besi)\s+per\s+tahun',
        r'produksi\s+tahunan\s+([\d,\.]+)\s+(ons|ton|kg)\s+(emas|tembaga|perak|seng|timbal|nikel|batubara)'
    ]


def get_enhanced_commodity_extraction_patterns() -> List[str]:
    """
    ENHANCED PATTERN 31.07.2025: Erweiterte Pattern für "[ROHSTOFF]. [Beschreibung] so primary commodity..."
    
    Erkennt Textstrukturen wie:
    - "Gold. Lapa is a gold mine, so primary commodity is gold"
    - "Copper. This is a copper mining operation"
    - "Iron ore. The mine extracts iron ore as primary commodity"
    
    Returns:
        Liste mit Regex-Patterns für Rohstoff-Extraktion aus Erklärungen
    """
    return [
        # Pattern: "[ROHSTOFF]. [Erklärung] so primary commodity..."
        r'^(Gold|Kupfer|Silber|Zink|Blei|Nickel|Kohle|Eisenerz|Öl|Gas)\.\s+.*?so\s+primary\s+commodity',
        r'^(Gold|Copper|Silver|Zinc|Lead|Nickel|Coal|Iron\s+ore|Oil|Gas)\.\s+.*?so\s+primary\s+commodity',
        
        # Pattern: "[ROHSTOFF]. [Mine name] is a [ROHSTOFF] mine"
        r'^(Gold|Kupfer|Silber|Zink|Blei|Nickel|Kohle|Eisenerz)\.\s+\w+\s+is\s+a\s+\w+\s+mine',
        r'^(Gold|Copper|Silver|Zinc|Lead|Nickel|Coal|Iron\s+ore)\.\s+\w+\s+is\s+a\s+\w+\s+mine',
        
        # Pattern: "[ROHSTOFF]. [Beschreibung] extracts/mines [ROHSTOFF]"
        r'^(Gold|Kupfer|Silber|Zink|Blei|Nickel|Kohle|Eisenerz)\.\s+.*?(?:extracts?|mines?|fördert)\s+\w+',
        r'^(Gold|Copper|Silver|Zinc|Lead|Nickel|Coal|Iron\s+ore)\.\s+.*?(?:extracts?|mines?)\s+\w+',
        
        # Französische Varianten (Quebec)
        r'^(Or|Cuivre|Argent|Zinc|Plomb|Nickel|Charbon|Minerai\s+de\s+fer)\.\s+.*?(?:extrait|mine)\s+(?:de\s+l\'|du\s+)?\w+',
        
        # Spanische Varianten
        r'^(Oro|Cobre|Plata|Zinc|Plomo|Níquel|Carbón|Mineral\s+de\s+hierro)\.\s+.*?(?:extrae|mina)\s+\w+',
        
        # Indonesische Varianten
        r'^(Emas|Tembaga|Perak|Seng|Timbal|Nikel|Batubara|Bijih\s+besi)\.\s+.*?(?:mengekstrak|menambang)\s+\w+'
    ]


def get_enhanced_mine_type_patterns() -> List[str]:
    """
    ENHANCED PATTERN 31.07.2025: Erweiterte Pattern für Minentyp-Bereinigung
    
    Bereinigt komplexe Auflistungen und extrahiert den tatsächlichen Typ:
    - "(Untertage/ Open-Pit/ usw.): Open-Pit" → "Open-Pit"
    - "Type: Underground mining operation" → "Underground"
    - "Tagebau und Untertage kombiniert" → "Tagebau/Untertage"
    
    Returns:
        Liste mit Regex-Patterns für Minentyp-Extraktion
    """
    return [
        # Pattern: Kombinierte Typen ZUERST (spezifischste Pattern)
        r'(Open-Pit\s+(?:und|and)\s+Underground|Tagebau\s+(?:und|and)\s+Untertage|Underground\s+(?:und|and)\s+Open-Pit)',
        r'(Surface\s+(?:und|and)\s+Underground|Tagebau\s+(?:und|and)\s+Tiefbau)',
        r'(Tagebau\s+und\s+Untertage\s+kombiniert)',
        
        # Pattern: Entferne Präfix und extrahiere Typ
        r'(?:Minentyp\s*)?(?:\(Untertage/\s*Open-Pit/\s*usw\.\))?\s*:?\s*(Open-Pit|Tagebau|Underground|Untertage|Surface|Strip\s+mine|Quarry|Steinbruch)',
        
        # Pattern: "Type: [ACTUAL_TYPE] mining operation"
        r'Type:\s*(Open-Pit|Tagebau|Underground|Untertage|Surface|Strip)\s*(?:mining\s+operation|mine)?',
        
        # Pattern: Klare Typ-Angaben
        r'(?:Mine\s+type|Typ|Type):\s*(Open-Pit|Tagebau|Underground|Untertage|Surface|Quarry|Strip\s+mine|Steinbruch)',
        
        # Pattern: In Fließtext erwähnt
        r'(?:is\s+an?|ist\s+ein)\s*(Open-Pit|Tagebau|Underground|Untertage|Surface)\s+(?:mine|operation|Betrieb)',
        
        # Französische Pattern (Quebec)
        r'(?:Type\s+de\s+mine|Exploitation):\s*(Ciel\s+ouvert|Souterraine|Surface)',
        r'(?:mine\s+à|exploitation\s+)\s*(ciel\s+ouvert|souterraine)',
        
        # Spanische Pattern
        r'(?:Tipo\s+de\s+mina|Explotación):\s*(Cielo\s+abierto|Subterránea|Superficie)',
        
        # Indonesische Pattern
        r'(?:Jenis\s+tambang|Tipe\s+penambangan):\s*(Terbuka|Bawah\s+tanah|Permukaan)'
    ]


def extract_cross_field_data(text: str) -> Dict[str, str]:
    """
    CROSS-FIELD PATTERN 31.07.2025: Extrahiert Rohstoff + Fördermenge aus einem Text
    
    Analysiert Texte wie:
    "derzeit etwa 270.000 Unzen Gold pro Jahr"
    
    Args:
        text: Input-Text
        
    Returns:
        Dict mit extrahierten Werten für 'commodity' und 'production'
    """
    result = {'commodity': '', 'production': ''}
    
    # Pattern für kombinierte Rohstoff/Produktions-Daten
    production_patterns = get_enhanced_production_patterns()
    
    for pattern in production_patterns:
        try:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Extrahiere Komponenten - flexiblere Gruppenzuordnung
                groups = match.groups()
                
                if len(groups) >= 3:
                    # Bestimme Position von amount, unit, commodity basierend auf Pattern
                    if 'jährliche' in pattern and 'von' in pattern:
                        # Pattern: "jährliche Förderung von [AMOUNT] [UNIT] [COMMODITY]"
                        amount = groups[0]
                        # groups[1] könnte "Millionen" sein, groups[2] die Einheit, groups[3] der Rohstoff
                        if len(groups) >= 4 and groups[1]:  # "Millionen" vorhanden
                            unit = f"{groups[1]}{groups[2]}"  # "Millionen Tonnen"
                            commodity = groups[3]
                        else:
                            unit = groups[2] if len(groups) > 2 else groups[1]
                            commodity = groups[3] if len(groups) > 3 else groups[2]
                    else:
                        # Standard Pattern - amount, unit, commodity (das "of" ist optional und erfasst keine Gruppe)
                        amount = groups[0]
                        unit = groups[1] 
                        commodity = groups[2]
                    
                    # Normalisiere Rohstoff
                    commodity_normalized = normalize_commodity_name(commodity)
                    
                    # Formatiere Produktionsmenge
                    if len(groups) >= 4 and 'pro' in pattern:
                        period = groups[-1]  # Letztes Element ist der Zeitraum
                        production_formatted = f"{amount} {unit}/{period}"
                    else:
                        production_formatted = f"{amount} {unit}/Jahr"
                    
                    # Setze Ergebnisse nur wenn Normalisierung erfolgreich war
                    if commodity_normalized is not None:
                        result['commodity'] = commodity_normalized
                        result['production'] = production_formatted
                    
                    logger.debug(f"Cross-field extraction: '{commodity_normalized}' + '{production_formatted}' from pattern {pattern[:50]}")
                    break
                    
        except re.error as e:
            logger.warning(f"Regex error in cross-field pattern: {e}")
            continue
    
    return result


def extract_commodity_from_explanation(text: str) -> Optional[str]:
    """
    EXPLANATION PATTERN 31.07.2025: Extrahiert Rohstoff aus Erklärungstexten
    
    Args:
        text: Text mit Format "[ROHSTOFF]. [Erklärung]..."
        
    Returns:
        Extrahierter Rohstoff oder None wenn nicht gefunden
    """
    commodity_patterns = get_enhanced_commodity_extraction_patterns()
    
    for pattern in commodity_patterns:
        try:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                commodity = match.group(1)
                normalized = normalize_commodity_name(commodity)
                if normalized is not None:
                    logger.debug(f"Commodity from explanation: '{normalized}' from pattern {pattern[:50]}")
                    return normalized
        except re.error as e:
            logger.warning(f"Regex error in commodity pattern: {e}")
            continue
    
    # REGEL 10 KONFORM: Kein Dummy-Marker - echte "nicht gefunden"
    return None  # Echte "nicht gefunden" - kein ausgedachter X-Marker


def extract_mine_type_from_complex_text(text: str) -> Optional[str]:
    """
    MINE TYPE PATTERN 31.07.2025: Extrahiert Minentyp aus komplexen Auflistungen
    
    Args:
        text: Text mit Minentyp-Informationen
        
    Returns:
        Bereinigter Minentyp oder None wenn nicht gefunden
    """
    mine_type_patterns = get_enhanced_mine_type_patterns()
    
    for pattern in mine_type_patterns:
        try:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                mine_type = match.group(1)
                normalized = normalize_mine_type(mine_type)
                if normalized is not None:
                    logger.debug(f"Mine type extracted: '{normalized}' from pattern {pattern[:50]}")
                    return normalized
        except re.error as e:
            logger.warning(f"Regex error in mine type pattern: {e}")
            continue
    
    # REGEL 10 KONFORM: Kein Dummy-Marker - echte "nicht gefunden"
    return None  # Echte "nicht gefunden" - kein ausgedachter X-Marker


def normalize_commodity_name(commodity: str) -> Optional[str]:
    """
    NORMALISIERUNG 31.07.2025: Normalisiert Rohstoffnamen zu Standard-Format
    
    Args:
        commodity: Rohstoffname in beliebiger Sprache
        
    Returns:
        Normalisierter deutscher Rohstoffname oder None wenn leer/ungültig
    """
    if not commodity or not commodity.strip():
        # REGEL 10 KONFORM: Kein Dummy-Marker - echte "nicht gefunden"
        return None  # Echte "nicht gefunden" - kein ausgedachter X-Marker
    
    commodity_lower = commodity.lower().strip()
    
    # Mapping verschiedener Sprachen zu deutschen Standard-Namen
    commodity_mapping = {
        # Gold
        'gold': 'Gold', 'or': 'Gold', 'oro': 'Gold', 'emas': 'Gold',
        
        # Kupfer
        'copper': 'Kupfer', 'kupfer': 'Kupfer', 'cuivre': 'Kupfer', 'cobre': 'Kupfer', 'tembaga': 'Kupfer',
        
        # Silber
        'silver': 'Silber', 'silber': 'Silber', 'argent': 'Silber', 'plata': 'Silber', 'perak': 'Silber',
        
        # Zink
        'zinc': 'Zink', 'zink': 'Zink', 'seng': 'Zink',
        
        # Blei
        'lead': 'Blei', 'blei': 'Blei', 'plomb': 'Blei', 'plomo': 'Blei', 'timbal': 'Blei',
        
        # Nickel
        'nickel': 'Nickel', 'níquel': 'Nickel', 'nikel': 'Nickel',
        
        # Kohle
        'coal': 'Kohle', 'kohle': 'Kohle', 'charbon': 'Kohle', 'carbón': 'Kohle', 'batubara': 'Kohle',
        
        # Eisenerz
        'iron ore': 'Eisenerz', 'iron_ore': 'Eisenerz', 'eisenerz': 'Eisenerz', 
        'minerai de fer': 'Eisenerz', 'mineral de hierro': 'Eisenerz', 'bijih besi': 'Eisenerz',
        
        # Öl
        'oil': 'Öl', 'öl': 'Öl', 'pétrole': 'Öl', 'petróleo': 'Öl', 'minyak': 'Öl',
        
        # Gas
        'gas': 'Gas', 'gaz': 'Gas', 'gas natural': 'Gas'
    }
    
    # Suche nach Mapping
    normalized = commodity_mapping.get(commodity_lower)
    if normalized:
        return normalized
    
    # Fallback: Capitalize first letter
    return commodity.strip().title()


def normalize_mine_type(mine_type: str) -> Optional[str]:
    """
    NORMALISIERUNG 31.07.2025: Normalisiert Minentyp zu Standard-Format
    
    Args:
        mine_type: Minentyp in beliebiger Sprache
        
    Returns:
        Normalisierter deutscher Minentyp oder None wenn leer/ungültig
    """
    if not mine_type or not mine_type.strip():
        # REGEL 10 KONFORM: Kein Dummy-Marker - echte "nicht gefunden"
        return None  # Echte "nicht gefunden" - kein ausgedachter X-Marker
    
    mine_type_lower = mine_type.lower().strip()
    
    # Mapping verschiedener Sprachen zu deutschen Standard-Namen
    type_mapping = {
        # Open-Pit / Tagebau
        'open-pit': 'Open-Pit', 'open pit': 'Open-Pit', 'openpit': 'Open-Pit',
        'tagebau': 'Tagebau', 'surface': 'Tagebau', 'strip mine': 'Tagebau',
        'ciel ouvert': 'Open-Pit', 'cielo abierto': 'Open-Pit', 'terbuka': 'Open-Pit',
        
        # Underground / Untertage
        'underground': 'Untertage', 'untertage': 'Untertage', 'tiefbau': 'Untertage',
        'souterraine': 'Untertage', 'subterránea': 'Untertage', 'bawah tanah': 'Untertage',
        
        # Quarry / Steinbruch
        'quarry': 'Steinbruch', 'steinbruch': 'Steinbruch',
        
        # Kombinierte Typen
        'open-pit und underground': 'Open-Pit/Untertage',
        'tagebau und untertage': 'Tagebau/Untertage',
        'surface und underground': 'Tagebau/Untertage',
        'surface and underground': 'Tagebau/Untertage',
        'tagebau und untertage kombiniert': 'Tagebau/Untertage'
    }
    
    # Suche nach Mapping
    normalized = type_mapping.get(mine_type_lower)
    if normalized:
        return normalized
    
    # Prüfe auf kombinierte Typen mit verschiedenen Trennzeichen
    if any(sep in mine_type_lower for sep in [' und ', ' and ', '/', '+', ',']):
        # Extrahiere einzelne Typen und normalisiere sie
        separators = [' und ', ' and ', '/', '+', ',']
        for sep in separators:
            if sep in mine_type_lower:
                parts = [part.strip() for part in mine_type_lower.split(sep)]
                normalized_parts = []
                for part in parts:
                    norm_part = type_mapping.get(part, part.title())
                    if norm_part != "X" and norm_part not in normalized_parts:
                        normalized_parts.append(norm_part)
                if len(normalized_parts) > 1:
                    return '/'.join(normalized_parts)
    
    # Fallback: Capitalize
    return mine_type.strip().title()


def apply_enhanced_patterns_to_field(value: str, field: str) -> str:
    """
    PATTERN ENHANCEMENT 31.07.2025: Wendet erweiterte Pattern-Logik auf Felder an
    
    Args:
        value: Rohwert aus Provider
        field: Feldname
        
    Returns:
        Mit erweiterten Patterns verbesserter Wert
    """
    if not value or not value.strip():
        # REGEL 10 KONFORM: Kein Dummy-Marker - echte "nicht gefunden"
        return None  # Echte "nicht gefunden" - kein ausgedachter X-Marker
    
    value = value.strip()
    
    # Feld-spezifische Verbesserungen
    if field in ['Rohstoff', 'Rohstoffe']:
        # 1. Prüfe auf Erklärungsformat "[ROHSTOFF]. [Beschreibung]..."
        commodity_from_explanation = extract_commodity_from_explanation(value)
        if commodity_from_explanation is not None:
            return commodity_from_explanation
        
        # 2. Prüfe auf Cross-Field-Daten (Rohstoff + Produktion)
        cross_field_data = extract_cross_field_data(value)
        if cross_field_data['commodity']:
            return cross_field_data['commodity']
    
    elif field == 'Fördermenge/Jahr Rohstoff':
        # NEU 07.09.2025: Cross-Field-Daten für Rohstoff-Produktionsmenge
        cross_field_data = extract_cross_field_data(value)
        if cross_field_data['production']:
            # Prüfe ob es sich um Rohstoff-spezifische Produktion handelt (Unzen, spezifische Tonnage)
            production_lower = cross_field_data['production'].lower()
            if any(unit in production_lower for unit in ['oz', 'ounces', 'unzen', 'tonnes of', 'tons of']):
                return cross_field_data['production']
    
    elif field == 'Fördermenge/Jahr Abraum':
        # NEU 07.09.2025: Cross-Field-Daten für Gesamtextraktion
        cross_field_data = extract_cross_field_data(value)
        if cross_field_data['production']:
            # Prüfe ob es sich um Gesamtextraktion handelt (Million Tonnen, Gesamtmaterial)
            production_lower = cross_field_data['production'].lower()
            if any(indicator in production_lower for indicator in ['million', 'mt', 'total', 'waste', 'overburden', 'material']):
                return cross_field_data['production']
    
    elif field in ['Minentyp', 'Minentyp']:
        # Erweiterte Minentyp-Extraktion
        mine_type_extracted = extract_mine_type_from_complex_text(value)
        if mine_type_extracted is not None:
            return mine_type_extracted
    
    # Keine Verbesserung gefunden
    return value


# Integration in bestehende clean_field_value Funktion
def enhance_field_with_patterns(value: str, field: str) -> str:
    """
    INTEGRATION 31.07.2025: Integriert erweiterte Pattern in bestehende Bereinigung
    
    Args:
        value: Bereits durch clean_field_value bereinigter Wert
        field: Feldname
        
    Returns:
        Mit erweiterten Patterns weiter verbesserter Wert
    """
    # Wende erweiterte Pattern nur an wenn noch kein guter Wert gefunden
    if value in ["X", "N/A", "", "LEER"] or len(value) > 100:
        enhanced_value = apply_enhanced_patterns_to_field(value, field)
        if enhanced_value != "X" and enhanced_value != value:
            logger.info(f"Enhanced pattern applied to {field}: '{value[:50]}...' → '{enhanced_value}'")
            return enhanced_value
    
    return value