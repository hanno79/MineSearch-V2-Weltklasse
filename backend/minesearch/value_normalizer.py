"""
Compact Value Normalizer
Kompakte Version des Value Normalizers

Author: MineSearch Development Team
Date: 2025-01-11
"""

import re
import logging
from typing import Dict, List, Optional, Set, Tuple
from unicodedata import normalize

logger = logging.getLogger(__name__)


def parse_number_with_separators(value_str: str) -> Tuple[Optional[float], str, str]:
    """Intelligente Erkennung und Parsing von Zahlen mit Tausender-/Dezimaltrennzeichen"""
    if not value_str or not isinstance(value_str, str):
        return None, "", value_str

    # Extrahiere Zahl, Einheit und Rest
    number_match = re.search(r'([\d,.\s]+)', value_str)
    if not number_match:
        return None, "", value_str

    number_str = number_match.group(1).replace(',', '').replace(' ', '')
    
    try:
        number = float(number_str)
        unit = _extract_unit(value_str)
        suffix = _extract_suffix(value_str)
        return number, unit, suffix
    except ValueError:
        return None, "", value_str


def _extract_unit(value_str: str) -> str:
    """Extrahiere Einheit aus Wert"""
    units = ['oz', 'ounces', 'tons', 'tonnes', 'kg', 'kilograms', 'lbs', 'pounds']
    
    for unit in units:
        if unit.lower() in value_str.lower():
            return unit
    
    return ""


def _extract_suffix(value_str: str) -> str:
    """Extrahiere Suffix aus Wert"""
    # Entferne Zahl und Einheit, behalte Rest
    cleaned = re.sub(r'[\d,.\s]+', '', value_str)
    cleaned = re.sub(r'\b(oz|ounces|tons|tonnes|kg|kilograms|lbs|pounds)\b', '', cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


def normalize_country_name(country: str) -> str:
    """Normalisiere Ländernamen"""
    if not country:
        return ""
    
    country = country.strip()
    
    # Normalisiere Unicode
    country = normalize('NFKD', country)
    
    # Ländernamen-Mapping
    country_mapping = {
        'kanada': 'Canada',
        'canada': 'Canada',
        'australien': 'Australia',
        'australia': 'Australia',
        'chile': 'Chile',
        'peru': 'Peru',
        'brasilien': 'Brazil',
        'brazil': 'Brazil',
        'usa': 'United States',
        'united states': 'United States',
        'vereinigte staaten': 'United States'
    }
    
    return country_mapping.get(country.lower(), country)


def normalize_region_name(region: str) -> str:
    """Normalisiere Regionsnamen"""
    if not region:
        return ""
    
    region = region.strip()
    
    # Normalisiere Unicode
    region = normalize('NFKD', region)
    
    # Regionsnamen-Mapping
    region_mapping = {
        'quebec': 'Québec',
        'québec': 'Québec',
        'ontario': 'Ontario',
        'british columbia': 'British Columbia',
        'bc': 'British Columbia',
        'alberta': 'Alberta',
        'saskatchewan': 'Saskatchewan',
        'manitoba': 'Manitoba'
    }
    
    return region_mapping.get(region.lower(), region)


def normalize_commodity_name(commodity: str) -> str:
    """Normalisiere Rohstoffnamen"""
    if not commodity:
        return ""
    
    commodity = commodity.strip()
    
    # Normalisiere Unicode
    commodity = normalize('NFKD', commodity)
    
    # Rohstoffnamen-Mapping
    commodity_mapping = {
        'gold': 'Gold',
        'silber': 'Silver',
        'silver': 'Silver',
        'kupfer': 'Copper',
        'copper': 'Copper',
        'eisen': 'Iron',
        'iron': 'Iron',
        'kohle': 'Coal',
        'coal': 'Coal',
        'uran': 'Uranium',
        'uranium': 'Uranium'
    }
    
    return commodity_mapping.get(commodity.lower(), commodity)


def normalize_operational_status(status: str) -> str:
    """Normalisiere Betriebsstatus"""
    if not status:
        return ""
    
    status = status.strip()
    
    # Normalisiere Unicode
    status = normalize('NFKD', status)
    
    # Status-Mapping
    status_mapping = {
        'operational': 'Operational',
        'betrieb': 'Operational',
        'aktiv': 'Operational',
        'active': 'Operational',
        'development': 'Development',
        'entwicklung': 'Development',
        'exploration': 'Exploration',
        'erkundung': 'Exploration',
        'care and maintenance': 'Care and Maintenance',
        'wartung': 'Care and Maintenance',
        'suspended': 'Suspended',
        'ausgesetzt': 'Suspended',
        'closed': 'Closed',
        'geschlossen': 'Closed'
    }
    
    return status_mapping.get(status.lower(), status)


def normalize_mining_method(method: str) -> str:
    """Normalisiere Bergbaumethode"""
    if not method:
        return ""
    
    method = method.strip()
    
    # Normalisiere Unicode
    method = normalize('NFKD', method)
    
    # Methode-Mapping
    method_mapping = {
        'open pit': 'Open Pit',
        'tagebau': 'Open Pit',
        'underground': 'Underground',
        'untertage': 'Underground',
        'surface': 'Surface',
        'oberfläche': 'Surface'
    }
    
    return method_mapping.get(method.lower(), method)


def normalize_processing_method(method: str) -> str:
    """Normalisiere Verarbeitungsmethode"""
    if not method:
        return ""
    
    method = method.strip()
    
    # Normalisiere Unicode
    method = normalize('NFKD', method)
    
    # Methode-Mapping
    method_mapping = {
        'heap leaching': 'Heap Leaching',
        'heap leach': 'Heap Leaching',
        'cyanide leaching': 'Cyanide Leaching',
        'flotation': 'Flotation',
        'gravity separation': 'Gravity Separation',
        'magnetic separation': 'Magnetic Separation'
    }
    
    return method_mapping.get(method.lower(), method)


def normalize_ownership_percentage(ownership: str) -> str:
    """Normalisiere Eigentumsanteil"""
    if not ownership:
        return ""
    
    ownership = ownership.strip()
    
    # Entferne Prozentzeichen und normalisiere
    ownership = re.sub(r'%', '', ownership)
    
    try:
        # Konvertiere zu Float und zurück zu String
        percentage = float(ownership)
        return f"{percentage:.1f}%"
    except ValueError:
        return ownership


def normalize_production_value(value: str) -> str:
    """Normalisiere Produktionswert"""
    if not value:
        return ""
    
    value = value.strip()
    
    # Parse Zahl und Einheit
    number, unit, suffix = parse_number_with_separators(value)
    
    if number is not None:
        # Formatiere Zahl
        if number >= 1000000:
            formatted_number = f"{number/1000000:.1f}M"
        elif number >= 1000:
            formatted_number = f"{number/1000:.1f}K"
        else:
            formatted_number = f"{number:.1f}"
        
        # Kombiniere mit Einheit
        if unit:
            return f"{formatted_number} {unit}"
        else:
            return formatted_number
    
    return value


def normalize_capacity_value(value: str) -> str:
    """Normalisiere Kapazitätswert"""
    if not value:
        return ""
    
    value = value.strip()
    
    # Parse Zahl und Einheit
    number, unit, suffix = parse_number_with_separators(value)
    
    if number is not None:
        # Formatiere Zahl
        if number >= 1000000:
            formatted_number = f"{number/1000000:.1f}M"
        elif number >= 1000:
            formatted_number = f"{number/1000:.1f}K"
        else:
            formatted_number = f"{number:.1f}"
        
        # Kombiniere mit Einheit
        if unit:
            return f"{formatted_number} {unit}"
        else:
            return formatted_number
    
    return value


def normalize_date(date_str: str) -> str:
    """Normalisiere Datum"""
    if not date_str:
        return ""
    
    date_str = date_str.strip()
    
    # Versuche verschiedene Datumsformate zu erkennen
    date_patterns = [
        r'(\d{4})-(\d{2})-(\d{2})',  # YYYY-MM-DD
        r'(\d{2})/(\d{2})/(\d{4})',  # MM/DD/YYYY
        r'(\d{2})\.(\d{2})\.(\d{4})',  # DD.MM.YYYY
        r'(\d{4})'  # YYYY
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, date_str)
        if match:
            if pattern == r'(\d{4})':
                return match.group(1)
            else:
                return date_str
    
    return date_str


def normalize_url(url: str) -> str:
    """Normalisiere URL"""
    if not url:
        return ""
    
    url = url.strip()
    
    # Füge http:// hinzu falls nicht vorhanden
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    return url


def normalize_email(email: str) -> str:
    """Normalisiere E-Mail"""
    if not email:
        return ""
    
    email = email.strip().lower()
    
    # Einfache E-Mail-Validierung
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(email_pattern, email):
        return email
    
    return ""


def normalize_phone(phone: str) -> str:
    """Normalisiere Telefonnummer"""
    if not phone:
        return ""
    
    phone = phone.strip()
    
    # Entferne alle nicht-numerischen Zeichen außer +
    phone = re.sub(r'[^\d+]', '', phone)
    
    # Formatiere Telefonnummer
    if phone.startswith('+'):
        return phone
    elif len(phone) >= 10:
        return f"+1{phone}"
    else:
        return phone


def normalize_field_value(field_name: str, value: str) -> str:
    """Normalisiere Feldwert basierend auf Feldname"""
    if not value:
        return ""
    
    # Feld-spezifische Normalisierung
    if field_name.lower() in ['country', 'land']:
        return normalize_country_name(value)
    elif field_name.lower() in ['region', 'provinz', 'state']:
        return normalize_region_name(value)
    elif field_name.lower() in ['commodity', 'rohstoff', 'mineral']:
        return normalize_commodity_name(value)
    elif field_name.lower() in ['operational_status', 'status']:
        return normalize_operational_status(value)
    elif field_name.lower() in ['mining_method', 'bergbaumethode']:
        return normalize_mining_method(value)
    elif field_name.lower() in ['processing_method', 'verarbeitungsmethode']:
        return normalize_processing_method(value)
    elif field_name.lower() in ['ownership', 'eigentum']:
        return normalize_ownership_percentage(value)
    elif field_name.lower() in ['annual_production', 'jahresproduktion']:
        return normalize_production_value(value)
    elif field_name.lower() in ['capacity', 'kapazität']:
        return normalize_capacity_value(value)
    elif field_name.lower() in ['date', 'datum']:
        return normalize_date(value)
    elif field_name.lower() in ['url', 'website']:
        return normalize_url(value)
    elif field_name.lower() in ['email', 'e-mail']:
        return normalize_email(value)
    elif field_name.lower() in ['phone', 'telefon']:
        return normalize_phone(value)
    else:
        # Allgemeine Normalisierung
        return value.strip()


def get_normalization_statistics() -> Dict[str, Any]:
    """Hole Normalisierungsstatistiken"""
    return {
        'total_normalizations': 0,  # Würde in der Realität aus der Datenbank kommen
        'successful_normalizations': 0,
        'failed_normalizations': 0,
        'average_processing_time': 0.0,
        'last_normalization': None,
        'timestamp': '2025-01-11T12:00:00Z'
    }


__all__ = [
    "parse_number_with_separators",
    "normalize_country_name",
    "normalize_region_name",
    "normalize_commodity_name",
    "normalize_operational_status",
    "normalize_mining_method",
    "normalize_processing_method",
    "normalize_ownership_percentage",
    "normalize_production_value",
    "normalize_capacity_value",
    "normalize_date",
    "normalize_url",
    "normalize_email",
    "normalize_phone",
    "normalize_field_value",
    "get_normalization_statistics"
]
