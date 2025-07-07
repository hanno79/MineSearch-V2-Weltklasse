"""
Author: rahn
Datum: 05.07.2025
Version: 1.0
Beschreibung: Verarbeitungsfunktionen für Mining-Datenextraktion
"""

import re
import logging
from typing import Dict, Optional, List, Any
from utils import get_country_config

logger = logging.getLogger(__name__)


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
    
    return value