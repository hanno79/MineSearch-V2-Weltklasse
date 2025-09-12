"""
Extraction Processors Module
Verarbeitungsfunktionen für Mining-Datenextraktion

Author: MineSearch Development Team
Date: 2025-01-11
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

    # PHASE 1: DIREKTE TEMPLATE-MARKER UND "NICHTS GEFUNDEN" WERTE - ABSOLUTE PRIORITÄT
    if value_str.startswith('TEMPLATE:'):
        logger.warning(f"[TEMPLATE DETECTION] Direkter TEMPLATE-Marker: '{value_str}'")
        return True

    # NEU: "Unbekannt" und ähnliche "nichts gefunden" Werte
    unknown_patterns = [
        'unbekannt', 'unknown', 'nicht bekannt', 'nicht verfügbar',
        'no data', 'no information', 'not found', 'not available',
        'n/a', 'na', 'tbd', 'to be determined', 'keine angabe',
        'keine angaben', 'keine daten', 'nicht ermittelbar',
        'nicht spezifiziert', 'not specified', 'not applicable',
        'keine information', 'no info', 'nichts gefunden',
        # REGEL 10 FIX 29.08.2025: Spezifische DB-Dummy-Werte
        'keine spezifischen quellen dokumentiert', 'keine spezifischen quellen gefunden'
    ]

    for pattern in unknown_patterns:
        if pattern in value_lower:
            logger.warning(f"[TEMPLATE DETECTION] Unbekannt-Pattern gefunden: '{value_str}'")
            return True

    # PHASE 2: GENERISCHE TEMPLATE-PATTERNS
    generic_template_patterns = [
        r'\[.*?\]',  # [PLACEHOLDER] oder [FIELD_NAME]
        r'\{.*?\}',  # {PLACEHOLDER} oder {FIELD_NAME}
        r'<.*?>',    # <PLACEHOLDER> oder <FIELD_NAME>
        r'___+',     # ____ oder ______
        r'xxx+',     # xxx oder xxxxx
        r'###+',     # ### oder #####
        r'\.\.\.+',  # ... oder .....
    ]

    for pattern in generic_template_patterns:
        if re.search(pattern, value_str):
            logger.warning(f"[TEMPLATE DETECTION] Template-Pattern gefunden: '{value_str}'")
            return True

    # PHASE 3: FELD-SPEZIFISCHE PRÜFUNGEN
    if field:
        if _is_field_specific_template(value_str, field):
            return True

    # PHASE 4: LÄNGEN-BASIERTE PRÜFUNGEN
    if len(value_str) < 2:
        logger.warning(f"[TEMPLATE DETECTION] Zu kurzer Wert: '{value_str}'")
        return True

    if len(value_str) > 1000:
        logger.warning(f"[TEMPLATE DETECTION] Ungewöhnlich langer Wert: {len(value_str)} Zeichen")
        return True

    # PHASE 5: ZAHLEN-BASIERTE PRÜFUNGEN
    if _is_numeric_template(value_str):
        return True

    # PHASE 6: WORT-BASIERTE PRÜFUNGEN
    if _is_word_based_template(value_str):
        return True

    return False


def _is_field_specific_template(value_str: str, field: str) -> bool:
    """Feld-spezifische Template-Prüfungen"""
    field_lower = field.lower()
    value_lower = value_str.lower()

    # Spezifische Feld-Patterns
    if 'name' in field_lower:
        if value_lower in ['name', 'mine name', 'company name']:
            return True

    if 'location' in field_lower or 'country' in field_lower:
        if value_lower in ['location', 'country', 'region', 'address']:
            return True

    if 'production' in field_lower:
        if value_lower in ['production', 'output', 'capacity']:
            return True

    return False


def _is_numeric_template(value_str: str) -> bool:
    """Zahlen-basierte Template-Prüfungen"""
    # Nur Zahlen ohne Einheiten
    if re.match(r'^\d+$', value_str):
        if len(value_str) > 10:  # Ungewöhnlich lange Zahlen
            return True

    # Typische Template-Zahlen
    template_numbers = ['0', '1', '100', '1000', '999', '9999']
    if value_str in template_numbers:
        return True

    return False


def _is_word_based_template(value_str: str) -> bool:
    """Wort-basierte Template-Prüfungen"""
    value_lower = value_str.lower()

    # Typische Template-Wörter
    template_words = [
        'example', 'sample', 'test', 'demo', 'placeholder',
        'beispiel', 'muster', 'test', 'demo', 'platzhalter'
    ]

    for word in template_words:
        if word in value_lower:
            return True

    return False


def clean_extracted_value(value: str, field: str = None) -> Optional[str]:
    """
    Bereinige extrahierten Wert

    Args:
        value: Roher extrahierter Wert
        field: Feldname für spezifische Bereinigung

    Returns:
        Bereinigter Wert oder None wenn ungültig
    """
    if not value:
        return None

    # Konvertiere zu String und entferne Whitespace
    cleaned = str(value).strip()

    # Prüfe auf Template/Dummy-Werte
    if is_template_or_dummy_value(cleaned, field):
        return None

    # Weitere Bereinigungen
    cleaned = _remove_common_artifacts(cleaned)
    cleaned = _normalize_formatting(cleaned)

    return cleaned if cleaned else None


def _remove_common_artifacts(value: str) -> str:
    """Entferne häufige Artefakte aus extrahierten Werten"""
    # Entferne HTML-Tags
    value = re.sub(r'<[^>]+>', '', value)
    
    # Entferne Markdown-Formatierung
    value = re.sub(r'\*\*(.*?)\*\*', r'\1', value)  # **bold**
    value = re.sub(r'\*(.*?)\*', r'\1', value)      # *italic*
    
    # Entferne überflüssige Leerzeichen
    value = re.sub(r'\s+', ' ', value)
    
    return value.strip()


def _normalize_formatting(value: str) -> str:
    """Normalisiere Formatierung"""
    # Normalisiere Anführungszeichen
    value = value.replace('"', '"').replace('"', '"')
    value = value.replace(''', "'").replace(''', "'")
    
    # Normalisiere Bindestriche
    value = value.replace('–', '-').replace('—', '-')
    
    return value


__all__ = ["is_template_or_dummy_value", "clean_extracted_value"]
