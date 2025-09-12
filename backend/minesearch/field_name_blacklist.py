"""
Author: rahn
Datum: 25.08.2025
Version: 1.0
Beschreibung: Feldnamen-Blacklist für Datenbankintegritäts-Validierung

KRITISCHER FIX 25.08.2025: Verhindert dass Feldnamen als Werte gespeichert werden
Lösung für: 111 Einträge mit "x-Koordinate" in Betreiber-Feld
"""

import re
import logging
from typing import Set, List, Pattern

logger = logging.getLogger(__name__)

# KRITISCHE FELDNAMEN-BLACKLIST 25.08.2025
# Diese Feldnamen dürfen NIEMALS als Werte in andere Felder geschrieben werden
CRITICAL_FIELD_NAMES = {
    # Koordinaten-Felder (häufigste Problemfälle)
    'x-Koordinate', 'y-Koordinate', 'x-koordinate', 'y-koordinate',
    'X-Koordinate', 'Y-Koordinate', 'Longitude', 'Latitude',
    'longitude', 'latitude', 'coordinates', 'Koordinaten',

    # Kosten- und Jahr-Felder
    'Restaurationskosten', 'restaurationskosten', 'Restoration Costs',
    'Kostenjahr', 'kostenjahr', 'Cost Year', 'Dokumentenjahr', 'dokumentenjahr',
    'Document Year', 'Produktionsstart', 'produktionsstart', 'Production Start',
    'Produktionsende', 'produktionsende', 'Production End',

    # Flächen- und Mengen-Felder
    'Minenfläche in qkm', 'minenfläche in qkm', 'Mine Area', 'mine area',
    'Fördermenge/Jahr', 'fördermenge/jahr', 'Annual Production', 'Production Volume',

    # Status- und Typ-Felder
    'Aktivitätsstatus', 'aktivitätsstatus', 'Activity Status', 'Mine Status',
    'Minentyp', 'minentyp', 'Mine Type', 'Operation Type',

    # Eigentums- und Betreiber-Felder
    'Betreiber', 'betreiber', 'Operator', 'operator',
    'Eigentümer', 'eigentümer', 'Owner', 'owner',
    'Mine Owner', 'mine owner', 'Mine Operator', 'mine operator',

    # Grunddaten-Felder
    'Mine', 'mine', 'Name', 'name', 'Mine Name', 'mine name',
    'Land', 'land', 'Country', 'country', 'Region', 'region',
    'Rohstoffe', 'rohstoffe', 'Commodities', 'commodities', 'Commodity',

    # Quellen- und Meta-Felder
    'Quellenangaben', 'quellenangaben', 'Sources', 'sources',
    'Details', 'details', 'Zuverlässigkeit', 'zuverlässigkeit',
    'Modelle', 'modelle', 'Models', 'models', 'Letzte Aktualisierung'
}

# ERWEITERTE MUSTER-BASIERTE BLACKLIST 25.08.2025
# Regex-Pattern für häufige Feldnamen-Variationen
FIELD_NAME_PATTERNS: List[Pattern] = [
    # Koordinaten mit optionalen Klammern/Einheiten
    re.compile(r'^[xy][-\s]*koordinate.*', re.IGNORECASE),
    re.compile(r'^(longitude|latitude).*', re.IGNORECASE),
    re.compile(r'^koordinaten.*', re.IGNORECASE),

    # Kosten mit optionalen Einheiten/Jahren
    re.compile(r'^restaurations?kosten.*', re.IGNORECASE),
    re.compile(r'^restoration\s+costs?.*', re.IGNORECASE),
    re.compile(r'^(kosten|cost)jahr.*', re.IGNORECASE),
    re.compile(r'^dokument(en)?jahr.*', re.IGNORECASE),

    # Produktions-Zeiträume
    re.compile(r'^produktions(start|ende).*', re.IGNORECASE),
    re.compile(r'^production\s+(start|end).*', re.IGNORECASE),

    # Flächen und Mengen
    re.compile(r'^minenfläche.*', re.IGNORECASE),
    re.compile(r'^mine\s+area.*', re.IGNORECASE),
    re.compile(r'^fördermenge.*', re.IGNORECASE),
    re.compile(r'^(annual\s+)?production.*', re.IGNORECASE),

    # Status und Typen
    re.compile(r'^aktivitäts?status.*', re.IGNORECASE),
    re.compile(r'^(mine\s+|activity\s+)?status.*', re.IGNORECASE),
    re.compile(r'^minen?typ.*', re.IGNORECASE),
    re.compile(r'^(mine\s+|operation\s+)?type.*', re.IGNORECASE),

    # Eigentum und Betrieb
    re.compile(r'^(mine\s+)?(betreiber|operator).*', re.IGNORECASE),
    re.compile(r'^(mine\s+)?(eigentümer|owner).*', re.IGNORECASE),

    # Grundfelder
    re.compile(r'^(mine\s+)?name.*', re.IGNORECASE),
    re.compile(r'^(land|country).*', re.IGNORECASE),
    re.compile(r'^(region|area).*', re.IGNORECASE),
    re.compile(r'^(rohstoffe?|commodit(y|ies)).*', re.IGNORECASE),

    # Meta-Felder
    re.compile(r'^quellen?angaben?.*', re.IGNORECASE),
    re.compile(r'^sources?.*', re.IGNORECASE),
    re.compile(r'^(details?|beschreibung).*', re.IGNORECASE),
    re.compile(r'^(zuverlässigkeit|reliability).*', re.IGNORECASE),
    re.compile(r'^(modelle?|models?).*', re.IGNORECASE),
]

# SPEZIELLE BLACKLIST-KATEGORIEN 25.08.2025
# Häufige AI-generierte Feldnamen die als Werte erscheinen
AI_GENERATED_FIELD_PATTERNS: List[Pattern] = [
    # WICHTIG: QUELLENREFERENZEN SIND LEGITIM!
    # Pattern mit [1,2,3] am Ende sind KEINE Kontamination sondern normale Quellenreferenzen
    # Deaktiviert: re.compile(r'^.+\s+\[\d+(,\s*\d+)*\]$'),

    # Felder mit Pipe-Trennzeichen (aus CSV-Problemen)
    re.compile(r'.*\|.*'),

    # Template-Strukturen die wie Feldnamen aussehen (OHNE Quellenreferenzen)
    re.compile(r'^[A-Z][a-z]+(/[A-Z][a-z]+)+\s*\(.*usw\.?\).*', re.IGNORECASE),  # "Gold/Kupfer/Kohle (usw.)"
    re.compile(r'.*\(.*[/|].*usw\.?\).*', re.IGNORECASE),  # "(Gold/ Kupfer/ usw.)"

    # ECHTE FELDNAMEN ALS WERTE (das ursprüngliche Problem)
    # Nur nackte Feldnamen ohne jegliche Werte dahinter
    re.compile(r'^(x-koordinate|y-koordinate)$', re.IGNORECASE),  # Nackte Koordinatenfelder
    re.compile(r'^(restaurationskosten|kostenjahr|dokumentenjahr)$', re.IGNORECASE),  # Nackte Kostenfelder
    re.compile(r'^(produktionsstart|produktionsende)$', re.IGNORECASE),  # Nackte Zeitfelder
    re.compile(r'^(betreiber|eigentümer|operator|owner)$', re.IGNORECASE),  # Nackte Betreiber-/Eigentümerfelder
]

def is_field_name_value(value: str, target_field: str = None) -> bool:
    """
    KRITISCHE FUNKTION 25.08.2025: Prüft ob ein Wert ein Feldname ist

    Verhindert dass Feldnamen als Werte gespeichert werden.
    Lösung für echte Feldkontamination (nicht Quellenreferenzen).

    Args:
        value: Zu prüfender Wert
        target_field: Ziel-Feld wo der Wert gespeichert werden soll (optional)

    Returns:
        True wenn Wert ein Feldname ist und blockiert werden muss
    """
    if not value or not str(value).strip():
        return False

    # SPEZIAL-FELDER AUSSCHLIESSEN (25.08.2025)
    if target_field in ['_source_mapping', 'source_mapping', 'sources']:
        logger.debug(f"[FIELD-NAME-CHECK] Spezialfeld '{target_field}' - keine Feldnamen-Prüfung")
        return False

    value_str = str(value).strip()
    value_lower = value_str.lower()

    # DEBUG-LOGGING für kritische Fälle
    if target_field:
        logger.debug(f"[FIELD-NAME-CHECK] Prüfe Wert '{value_str}' für Zielfeld '{target_field}'")

    # 1. EXAKTE FELDNAMEN-MATCHES (häufigste Fälle)
    if value_str in CRITICAL_FIELD_NAMES or value_lower in {name.lower() for name in CRITICAL_FIELD_NAMES}:
        logger.error(f"[CRITICAL] Feldname als Wert erkannt: '{value_str}' → BLOCKIERT")
        return True

    # 2. PATTERN-BASIERTE FELDNAMEN-ERKENNUNG
    for pattern in FIELD_NAME_PATTERNS:
        if pattern.match(value_str):
            logger.error(f"[CRITICAL] Feldname-Pattern erkannt: '{value_str}' → BLOCKIERT")
            return True

    # 3. AI-GENERIERTE FELDNAMEN-STRUKTUREN (nur echte Probleme, nicht Quellenreferenzen)
    for pattern in AI_GENERATED_FIELD_PATTERNS:
        if pattern.match(value_str):
            logger.warning(f"[AI-FIELD-PATTERN] AI-Feldname-Struktur: '{value_str}' → BLOCKIERT")
            return True

    # 4. SPEZIELLE CROSS-FIELD-KONTAMINATION (erweiterte Prüfungen)
    if target_field:
        # Koordinaten in Betreiber/Eigentümer-Feldern (häufigster Problemfall)
        if target_field in ['Betreiber', 'Eigentümer'] and re.match(r'^[xy][-\s]*koordinate', value_lower):
            logger.error(f"[CROSS-FIELD] Koordinate in {target_field}-Feld: '{value_str}' → BLOCKIERT")
            return True

        # Kosten in Status-Feldern
        if target_field in ['Aktivitätsstatus'] and 'kosten' in value_lower:
            logger.error(f"[CROSS-FIELD] Kosten-Feld in {target_field}: '{value_str}' → BLOCKIERT")
            return True

        # Status in Koordinaten-Feldern
        if target_field in ['x-Koordinate', 'y-Koordinate'] and any(status in value_lower for status
in ['aktiv', 'geschlossen', 'geplant']):
            logger.error(f"[CROSS-FIELD] Status in {target_field}: '{value_str}' → BLOCKIERT")
            return True

    # 5. WERT IST KEIN FELDNAME
    logger.debug(f"[FIELD-NAME-CHECK] Wert '{value_str}' ist kein Feldname → OK")
    return False

def get_blacklisted_values() -> Set[str]:
    """
    Gibt alle blacklisted Feldnamen als Set zurück

    Returns:
        Set aller kritischen Feldnamen
    """
    return CRITICAL_FIELD_NAMES.copy()

def add_custom_field_name(field_name: str) -> None:
    """
    Fügt einen benutzerdefinierten Feldnamen zur Blacklist hinzu

    Args:
        field_name: Neuer Feldname der zur Blacklist hinzugefügt werden soll
    """
    CRITICAL_FIELD_NAMES.add(field_name)
    logger.info(f"[BLACKLIST] Benutzerdefinierten Feldnamen hinzugefügt: '{field_name}'")

def validate_extracted_fields(data: dict) -> dict:
    """
    KRITISCHE VALIDIERUNG 25.08.2025: Prüft alle extrahierten Felder auf Feldnamen-Kontamination

    Entfernt alle Werte die Feldnamen sind und ersetzt sie durch None (NULL in DB).

    Args:
        data: Dictionary mit extrahierten Feldern

    Returns:
        Bereinigtes Dictionary ohne Feldnamen-Kontaminationen
    """
    cleaned_data = data.copy()
    contamination_count = 0

    for field_name, field_value in data.items():
        if field_value and str(field_value).strip():
            if is_field_name_value(field_value, field_name):
                logger.error(f"[FIELD-CONTAMINATION] Feldname-Kontamination entfernt:
'{field_value}' aus Feld '{field_name}'")
                cleaned_data[field_name] = None  # NULL in DB
                contamination_count += 1

    if contamination_count > 0:
        logger.warning(f"[FIELD-VALIDATION] {contamination_count} Feldnamen-Kontaminationen entfernt")
    else:
        logger.debug(f"[FIELD-VALIDATION] Keine Feldnamen-Kontaminationen gefunden")

    return cleaned_data

# EXPORT der wichtigsten Funktionen
__all__ = [
    'is_field_name_value',
    'validate_extracted_fields',
    'get_blacklisted_values',
    'add_custom_field_name',
    'CRITICAL_FIELD_NAMES'
]
