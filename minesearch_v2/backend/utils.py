"""
Author: rahn
Datum: 30.06.2025
Version: 1.0
Beschreibung: Hilfsfunktionen für MineSearch
"""

import re
import logging
from typing import List, Dict, Any, Optional
from config import config

# ÄNDERUNG 30.06.2025: Strukturiertes Logging (Regel 16)
logger = logging.getLogger(__name__)


def normalize_accents(text: str) -> str:
    """
    Normalisiere französische und andere Akzente für bessere Suche
    
    Args:
        text: Text mit möglichen Akzenten
        
    Returns:
        Text ohne Akzente
    """
    accent_map = {
        'à': 'a', 'á': 'a', 'â': 'a', 'ä': 'a', 'æ': 'ae', 'ã': 'a', 'å': 'a', 'ā': 'a',
        'è': 'e', 'é': 'e', 'ê': 'e', 'ë': 'e', 'ē': 'e', 'ė': 'e', 'ę': 'e',
        'î': 'i', 'ï': 'i', 'í': 'i', 'ī': 'i', 'į': 'i', 'ì': 'i',
        'ô': 'o', 'ö': 'o', 'ò': 'o', 'ó': 'o', 'œ': 'oe', 'ø': 'o', 'ō': 'o', 'õ': 'o',
        'ù': 'u', 'ú': 'u', 'û': 'u', 'ü': 'u', 'ū': 'u', 'ů': 'u', 'ű': 'u', 'ŭ': 'u',
        'ç': 'c', 'ć': 'c', 'č': 'c', 'ĉ': 'c', 'ċ': 'c'
    }
    
    result = text
    for accented, normalized in accent_map.items():
        result = result.replace(accented, normalized)
        result = result.replace(accented.upper(), normalized.upper())
    
    return result


def get_country_config(country: str) -> Dict:
    """
    Hole länderspezifische Konfiguration
    
    Args:
        country: Landname
        
    Returns:
        Länderkonfiguration oder Standard-Fallback
    """
    if not country:
        return {}
    
    country_lower = country.lower()
    
    # Suche passende Konfiguration
    for country_key, config_data in config.COUNTRY_CONFIGS.items():
        if country_key.lower() in country_lower or country_lower in country_key.lower():
            logger.debug(f"[COUNTRY CONFIG] Gefunden für '{country}': {country_key}")
            return config_data
    
    # Standard-Fallback
    logger.debug(f"[COUNTRY CONFIG] Kein Match für '{country}', verwende Standard")
    return {'languages': ['en'], 'currency': 'USD'}


def generate_multilingual_search_terms(mine_name: str, country: Optional[str] = None) -> List[str]:
    """
    Generiere mehrsprachige Suchbegriffe basierend auf Land
    
    Args:
        mine_name: Name der Mine
        country: Land (optional)
        
    Returns:
        Liste mehrsprachiger Suchbegriffe
    """
    terms = []
    country_config = get_country_config(country) if country else {}
    
    # Hole Mining-Begriffe für das Land
    mining_terms = country_config.get('mining_terms', {})
    mine_words = mining_terms.get('mine', ['mine'])
    
    # Füge verschiedene Sprachvarianten hinzu
    for mine_word in mine_words:
        terms.append(f"{mine_word} {mine_name}")
        
        # Mit Akzenten und ohne
        normalized = normalize_accents(mine_name)
        if normalized != mine_name:
            terms.append(f"{mine_word} {normalized}")
    
    return terms


def generate_name_variants(mine_name: str) -> List[str]:
    """
    Generiere erweiterte Suchvarianten für Minennamen
    
    Args:
        mine_name: Originalname der Mine
        
    Returns:
        Liste von Namensvarianten
    """
    variants = set()
    
    # Original Name
    variants.add(mine_name)
    
    # Normalisierte Version (ohne Akzente)
    normalized = normalize_accents(mine_name)
    if normalized != mine_name:
        variants.add(normalized)
    
    # Erweiterte Präfix/Suffix-Varianten
    mine_prefixes = ['Mine', 'mine', 'Project', 'project', 'Property', 'property', 
                     'Deposit', 'deposit', 'Operation', 'operation']
    
    # Prüfe ob Name bereits ein Präfix hat
    has_prefix = False
    for prefix in mine_prefixes:
        if mine_name.lower().startswith(prefix.lower() + ' '):
            has_prefix = True
            # Entferne das Präfix für Varianten
            without_prefix = mine_name[len(prefix)+1:].strip()
            variants.add(without_prefix)
            variants.add(without_prefix.capitalize())
            variants.add(without_prefix.upper())
            variants.add(without_prefix.lower())
            break
    
    # Füge verschiedene Präfixe hinzu wenn noch keines vorhanden
    if not has_prefix:
        for prefix in ['Mine', 'Project', 'Property']:
            variants.add(f"{prefix} {mine_name}")
            variants.add(f"{prefix.lower()} {mine_name.lower()}")
    
    # Phonetische Ähnlichkeiten
    phonetic_replacements = [
        ('ck', 'k'), ('k', 'ck'),
        ('ph', 'f'), ('f', 'ph'),
        ('v', 'w'), ('w', 'v'),
        ('s', 'z'), ('z', 's'),
        ('c', 'k'), ('c', 's'),
        ('x', 'ks'), ('ks', 'x')
    ]
    
    current_variants = list(variants)
    for variant in current_variants:
        for old, new in phonetic_replacements:
            if old in variant.lower():
                new_variant = variant.lower().replace(old, new)
                variants.add(new_variant)
                variants.add(new_variant.capitalize())
    
    # Variante ohne Bindestriche und mit Bindestrichen
    if '-' in mine_name:
        variants.add(mine_name.replace('-', ' '))
        variants.add(mine_name.replace('-', ''))
    else:
        # Füge Bindestriche bei zusammengesetzten Wörtern hinzu
        words = mine_name.split()
        if len(words) > 1:
            variants.add('-'.join(words))
    
    # Entferne Klammern und deren Inhalt (z.B. "Mine Name (Gold)")
    if "(" in mine_name and ")" in mine_name:
        without_brackets = re.sub(r'\s*\([^)]*\)', '', mine_name).strip()
        variants.add(without_brackets)
        variants.add(normalize_accents(without_brackets))
        
        # Füge auch Varianten mit dem Inhalt der Klammern hinzu
        bracket_content = re.search(r'\(([^)]+)\)', mine_name)
        if bracket_content:
            commodity = bracket_content.group(1)
            variants.add(f"{without_brackets} {commodity}")
            variants.add(f"{commodity} {without_brackets}")
    
    # Gross-/Kleinschreibungsvarianten
    for variant in list(variants):
        variants.add(variant.upper())
        variants.add(variant.lower())
        variants.add(variant.title())
    
    # Entferne leere Strings und Duplikate
    variants = {v.strip() for v in variants if v.strip()}
    
    logger.debug(f"[NAME VARIANTS] {mine_name} → {len(variants)} Varianten generiert")
    
    return list(variants)


def clean_extracted_value(value: str) -> str:
    """
    Bereinige extrahierte Werte von Markup und Quellen-Referenzen
    
    Args:
        value: Zu bereinigender Wert
        
    Returns:
        Bereinigter Wert
    """
    if not value:
        return value
    
    # ÄNDERUNG 30.06.2025: Try-catch für Bereinigung (Regel 13)
    try:
        # Entferne ** Markierungen
        value = value.replace('**', '').strip()
        
        # Entferne [Quelle: ...] Referenzen
        value = re.sub(r'\[Quelle:[^\]]+\]', '', value).strip()
        
        # Entferne inline Quellen-Nummern wie [1], [2][3] etc.
        value = re.sub(r'\[\d+\](?:\[\d+\])*', '', value).strip()
        
        # Entferne einzelne eckige Klammern und andere Reste
        value = re.sub(r'[\[\]]', '', value).strip()
        
        # Entferne führende/nachfolgende Sonderzeichen
        value = value.strip(' -.,;:')
        
        # Entferne mehrfache Leerzeichen
        value = ' '.join(value.split())
        
        return value
        
    except Exception as e:
        logger.error(f"[CLEAN ERROR] Fehler beim Bereinigen von '{value[:50]}...': {str(e)}")
        return value


# ÄNDERUNG 01.07.2025: extract_source_numbers entfernt - existiert bereits in source_discovery.py
# Verwende: from source_discovery import extract_source_numbers


def validate_url(url: str) -> bool:
    """
    Validiere eine URL
    
    Args:
        url: Zu validierende URL
        
    Returns:
        True wenn gültig, False sonst
    """
    url_pattern = re.compile(
        r'^https?://'  # http:// oder https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...oder IP
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    return bool(url_pattern.match(url))


def extract_year_from_text(text: str) -> Optional[str]:
    """
    Extrahiere ein valides Jahr (1900-2030) aus Text
    
    Args:
        text: Text mit möglichem Jahr
        
    Returns:
        Jahr als String oder None
    """
    # Suche nach 4-stelligen Zahlen zwischen 1900 und 2030
    years = re.findall(r'\b(19\d{2}|20[0-3]\d)\b', text)
    
    if years:
        # Nimm das aktuellste Jahr
        return max(years)
    
    return None


def format_currency(amount: float, currency: str = "USD", is_planned: bool = False) -> str:
    """
    Formatiere Währungsbeträge
    
    Args:
        amount: Betrag
        currency: Währungscode
        is_planned: Ob es geplante Kosten sind
        
    Returns:
        Formatierter Währungsstring
    """
    formatted = f"${amount:,.0f} {currency}"
    
    if is_planned:
        formatted += " (geplant)"
    
    return formatted


def is_valid_coordinate(lat: Any, lon: Any) -> bool:
    """
    Prüfe ob Koordinaten gültig sind
    
    Args:
        lat: Latitude
        lon: Longitude
        
    Returns:
        True wenn gültige Koordinaten
    """
    try:
        lat_val = float(lat)
        lon_val = float(lon)
        
        # Latitude: -90 bis 90
        # Longitude: -180 bis 180
        return -90 <= lat_val <= 90 and -180 <= lon_val <= 180
        
    except (TypeError, ValueError):
        return False


def sanitize_filename(filename: str) -> str:
    """
    Bereinige Dateinamen für sichere Verwendung
    
    Args:
        filename: Ursprünglicher Dateiname
        
    Returns:
        Bereinigter Dateiname
    """
    # Entferne ungültige Zeichen
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Entferne führende/nachfolgende Punkte und Leerzeichen
    filename = filename.strip('. ')
    
    # Begrenze Länge
    if len(filename) > 200:
        filename = filename[:200]
    
    return filename

# ÄNDERUNG 01.07.2025: Duplizierte Funktionen entfernt - diese existieren bereits in source_discovery.py und data_extraction.py  # Entferne Duplikate und sortiere