"""
Author: rahn
Datum: 11.09.2025
Version: 1.0
Beschreibung: Normalisierungs-Funktionen für Database-Einträge (Refactoring aus normalized_manager.py)
"""

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


def normalize_mine_name(name: str) -> str:
    """Normalisiere Mine-Namen für Konsistenz und Deduplizierung"""
    if not name:
        return ""

    # Basis-Normalisierung
    normalized = name.strip().lower()

    # Akzente entfernen (éléonore → eleonore)
    accent_map = {
        'à': 'a', 'á': 'a', 'â': 'a', 'ã': 'a', 'ä': 'a', 'å': 'a',
        'è': 'e', 'é': 'e', 'ê': 'e', 'ë': 'e',
        'ì': 'i', 'í': 'i', 'î': 'i', 'ï': 'i',
        'ò': 'o', 'ó': 'o', 'ô': 'o', 'õ': 'o', 'ö': 'o',
        'ù': 'u', 'ú': 'u', 'û': 'u', 'ü': 'u',
        'ý': 'y', 'ÿ': 'y',
        'ñ': 'n', 'ç': 'c'
    }

    for accented, normal in accent_map.items():
        normalized = normalized.replace(accented, normal)

    # Entferne Common Mine Suffixes für bessere Deduplizierung
    mine_suffixes = ['mine', 'project', 'deposit', 'property', 'complex', 'operation']
    words = normalized.split()
    filtered_words = [word for word in words if word not in mine_suffixes]

    if filtered_words:  # Mindestens ein Wort muss bleiben
        normalized = ' '.join(filtered_words)

    # Entferne Sonderzeichen außer Zahlen und Buchstaben
    normalized = re.sub(r'[^a-z0-9\s]', '', normalized)

    # Entferne doppelte Leerzeichen
    normalized = re.sub(r'\s+', ' ', normalized).strip()

    return normalized


def normalize_company_name(name: str) -> Optional[str]:
    """Normalisiere Unternehmensnamen"""
    if not name or name in ['Nicht gefunden', 'Not found', 'Unknown']:
        return None

    normalized = name.strip().lower()

    # Entferne häufige Firmen-Suffixe für bessere Deduplizierung
    company_suffixes = ['inc', 'ltd', 'corp', 'corporation', 'company', 'co', 'llc', 'gmbh', 'sa', 'ag']
    words = normalized.split()
    filtered_words = [word for word in words if word.rstrip('.,') not in company_suffixes]

    if filtered_words:
        normalized = ' '.join(filtered_words)

    # Grundlegende Bereinigung - BEHALTE Umlaute und Akzente
    # Entferne nur wirklich problematische Zeichen, behalte aber ä,ö,ü,é,è,etc.
    normalized = re.sub(r'[^\w\s&äöüßàáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿ]', '', normalized, flags=re.UNICODE)
    normalized = re.sub(r'\s+', ' ', normalized).strip()

    return normalized


def normalize_mine_type(type_name: str) -> Optional[str]:
    """Normalisiere Minentyp mit Synonym-Erkennung"""
    if not type_name:
        return None

    # Synonyme für Minentypen
    mine_type_synonyms = {
        # Open Pit Varianten
        'open-pit': 'Open-Pit',
        'open_pit': 'Open-Pit',
        'openpit': 'Open-Pit',
        'open pit': 'Open-Pit',
        'surface': 'Open-Pit',
        'tagebau': 'Tagebau',

        # Underground Varianten
        'underground': 'Untertage',
        'untertage': 'Untertage',
        'untertagebau': 'Untertage',
        'subsurface': 'Untertage',

        # Andere Typen
        'placer': 'Placer',
        'quarry': 'Quarry',
        'dredging': 'Dredging',
        'in-situ-leaching': 'In-Situ-Leaching',
        'solution mining': 'In-Situ-Leaching'
    }

    # Normalisiere Input
    normalized = type_name.lower().strip()

    # Prüfe Synonyme
    if normalized in mine_type_synonyms:
        return mine_type_synonyms[normalized]

    # Fallback: Originalnamen mit korrigierter Gross-/Kleinschreibung
    return type_name.title()


def normalize_country_name(country_name: str) -> Optional[str]:
    """Normalisiere Ländernamen zu deutschen Varianten"""
    if not country_name or country_name in ['Nicht gefunden', 'Not found', 'Unknown']:
        return None

    # Synonyme für Ländernamen - immer deutsche Variante bevorzugen
    country_synonyms = {
        # Kanada Varianten
        'canada': 'Kanada',
        'kanada': 'Kanada',

        # USA Varianten
        'usa': 'USA',
        'united states': 'USA',
        'united states of america': 'USA',
        'vereinigte staaten': 'USA',
        'us': 'USA',

        # Weitere Länder
        'australia': 'Australien',
        'australien': 'Australien',
        'chile': 'Chile',
        'peru': 'Peru',
        'brasilien': 'Brasilien',
        'brazil': 'Brasilien',
        'mexiko': 'Mexiko',
        'mexico': 'Mexiko',
        'russland': 'Russland',
        'russia': 'Russland',
        'china': 'China',
        'indien': 'Indien',
        'india': 'Indien',
        'südafrika': 'Südafrika',
        'south africa': 'Südafrika',
        'argentinien': 'Argentinien',
        'argentina': 'Argentinien',
        'kolumbien': 'Kolumbien',
        'colombia': 'Kolumbien'
    }

    # Normalisiere Input
    normalized = country_name.lower().strip()

    # Prüfe Synonyme
    if normalized in country_synonyms:
        return country_synonyms[normalized]

    # Fallback: Originalnamen mit korrigierter Gross-/Kleinschreibung
    return country_name.title()


def normalize_activity_status(status_name: str) -> Optional[str]:
    """Normalisiere Aktivitätsstatus mit Synonym-Erkennung"""
    if not status_name:
        return None

    # Synonyme für Aktivitätsstatus
    activity_synonyms = {
        # Aktiv Varianten
        'active': 'aktiv',
        'aktiv': 'aktiv',
        'exploitation': 'aktiv',
        'operating': 'aktiv',
        'in betrieb': 'aktiv',

        # Geschlossen Varianten
        'closed': 'geschlossen',
        'geschlossen': 'geschlossen',
        'inactive': 'geschlossen',
        'stillgelegt': 'stillgelegt',

        # Entwicklung Varianten
        'development': 'in Entwicklung',
        'entwicklung': 'in Entwicklung',
        'in entwicklung': 'in Entwicklung',
        'under development': 'in Entwicklung',

        # Exploration Varianten
        'exploration': 'Exploration',
        'erkundung': 'Exploration',

        # Geplant Varianten
        'planned': 'geplant',
        'geplant': 'geplant',

        # Andere Status
        'feasibility': 'Feasibility',
        'pausiert': 'pausiert',
        'in wartung': 'in Wartung'
    }

    # Normalisiere Input
    normalized = status_name.lower().strip()

    # Prüfe Synonyme
    if normalized in activity_synonyms:
        return activity_synonyms[normalized]

    # Fallback: Originalnamen mit korrigierter Gross-/Kleinschreibung
    return status_name.title()


def calculate_confidence_score(field_name: str, raw_value: str, atomic_value: str) -> float:
    """
    Berechne dynamischen Confidence Score basierend auf verschiedenen Faktoren

    Args:
        field_name: Name des Feldes
        raw_value: Ursprünglicher Wert vor Bereinigung
        atomic_value: Bereinigter atomarer Wert

    Returns:
        Confidence Score zwischen 0.0 und 1.0
    """
    confidence = 0.5  # Basis-Confidence

    # 1. Faktor: Länge und Vollständigkeit des Wertes
    if len(atomic_value.strip()) > 0:
        confidence += 0.2

    if len(atomic_value.strip()) > 10:
        confidence += 0.1

    # 2. Faktor: Strukturierte vs. unstrukturierte Daten
    if field_name.lower() in ['country', 'land', 'region', 'state', 'province']:
        # Geografische Daten sind meist zuverlässig
        confidence += 0.2

    # 3. Faktor: Numerische Werte (Koordinaten, etc.)
    try:
        float(atomic_value)
        # Numerische Werte sind präzise
        confidence += 0.15
    except:
        pass

    # 4. Faktor: Bereinigungsaufwand (mehr Bereinigung = weniger Confidence)
    cleaning_impact = len(raw_value) - len(atomic_value)
    if cleaning_impact > 0:
        # Pro entferntes Zeichen reduziere Confidence leicht
        reduction = min(cleaning_impact * 0.01, 0.15)
        confidence -= reduction

    # 5. Faktor: Spezielle Felder mit hoher Zuverlässigkeit
    high_confidence_fields = [
        'name', 'mine_name', 'commodity', 'owner', 'operator',
        'latitude', 'longitude', 'coordinates'
    ]
    if any(hcf in field_name.lower() for hcf in high_confidence_fields):
        confidence += 0.1

    # 6. Faktor: Template-ähnliche Werte (niedrigere Confidence)
    template_indicators = [
        '[placeholder', '[template', 'xxx', 'n/a', 'unknown', 'tbd'
    ]
    if any(indicator in atomic_value.lower() for indicator in template_indicators):
        confidence -= 0.3

    # Begrenze auf 0.1 bis 1.0
    return max(0.1, min(1.0, confidence))


def detect_template_value(field_name: str, atomic_value: str) -> bool:
    """
    Erkenne ob ein Wert ein Template/Platzhalter ist

    Args:
        field_name: Name des Feldes
        atomic_value: Zu prüfender Wert

    Returns:
        True wenn Template-Wert erkannt wird
    """
    if not atomic_value or not atomic_value.strip():
        return False

    value_lower = atomic_value.lower().strip()

    # 1. Offensichtliche Template-Indikatoren
    template_indicators = [
        'template', 'placeholder', 'example', 'sample',
        '[template', '[placeholder', '[example',
        'xxx', 'yyy', 'zzz',
        'n/a', 'n.a.', 'not available', 'not applicable',
        'tbd', 'to be determined', 'to be defined',
        'unknown', 'unbekannt', 'nicht bekannt',
        'pending', 'ausstehend',
        'insert', 'enter', 'add',
        'your ', 'dein ', 'ihre ',
        '[insert', '[enter', '[add'
    ]

    for indicator in template_indicators:
        if indicator in value_lower:
            return True

    # 2. Wiederholende Zeichen (xxx, 999, ---)
    if len(set(atomic_value.strip())) == 1 and len(atomic_value.strip()) >= 3:
        return True

    # 3. Brackets um gesamten Wert
    if atomic_value.startswith('[') and atomic_value.endswith(']'):
        return True

    # 4. Spezielle Muster für bestimmte Felder
    if field_name.lower() in ['email', 'e-mail', 'contact']:
        # Template-E-Mails
        if 'example.com' in value_lower or 'test@' in value_lower:
            return True

    if field_name.lower() in ['phone', 'telefon', 'telephone']:
        # Template-Telefonnummern
        if value_lower in ['123-456-7890', '+1-xxx-xxx-xxxx', '000-000-0000']:
            return True

    # 5. Koordinaten-Templates
    if field_name.lower() in ['latitude', 'longitude', 'lat', 'lon', 'coordinates']:
        if value_lower in ['0.0', '0', '00.0000', 'xx.xxxx']:
            return True

    return False
