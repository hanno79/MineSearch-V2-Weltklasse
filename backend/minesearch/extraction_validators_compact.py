"""
Compact Extraction Validators
Kompakte Version der Extraction Validators

Author: MineSearch Development Team
Date: 2025-01-11
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def is_placeholder_value(value: str, field: str = None) -> bool:
    """Prüft ob ein Wert ein verbotener Platzhalter ist"""
    if not value:
        return False
    
    value_lower = value.lower().strip()
    
    # Verbotene Platzhalter
    forbidden_placeholders = [
        'template:', 'not specified', 'no data', 'n/a', 'unknown',
        'not available', 'not found', 'tbd', 'to be determined',
        'keine angabe', 'nicht verfügbar', 'unbekannt', 'placeholder',
        'example', 'sample', 'test', 'dummy', 'mock'
    ]
    
    return any(placeholder in value_lower for placeholder in forbidden_placeholders)


def is_valid_mine_name(name: str) -> bool:
    """Validiere Minen-Name"""
    if not name or not isinstance(name, str):
        return False
    
    name = name.strip()
    
    # Mindestlänge
    if len(name) < 2:
        return False
    
    # Maximal 100 Zeichen
    if len(name) > 100:
        return False
    
    # Keine Platzhalter
    if is_placeholder_value(name):
        return False
    
    # Muss mindestens einen Buchstaben enthalten
    if not re.search(r'[a-zA-Z]', name):
        return False
    
    return True


def is_valid_country(country: str) -> bool:
    """Validiere Land"""
    if not country or not isinstance(country, str):
        return False
    
    country = country.strip()
    
    # Mindestlänge
    if len(country) < 2:
        return False
    
    # Maximal 50 Zeichen
    if len(country) > 50:
        return False
    
    # Keine Platzhalter
    if is_placeholder_value(country):
        return False
    
    # Muss mindestens einen Buchstaben enthalten
    if not re.search(r'[a-zA-Z]', country):
        return False
    
    return True


def is_valid_region(region: str) -> bool:
    """Validiere Region"""
    if not region or not isinstance(region, str):
        return False
    
    region = region.strip()
    
    # Mindestlänge
    if len(region) < 2:
        return False
    
    # Maximal 100 Zeichen
    if len(region) > 100:
        return False
    
    # Keine Platzhalter
    if is_placeholder_value(region):
        return False
    
    return True


def is_valid_commodity(commodity: str) -> bool:
    """Validiere Rohstoff"""
    if not commodity or not isinstance(commodity, str):
        return False
    
    commodity = commodity.strip()
    
    # Mindestlänge
    if len(commodity) < 2:
        return False
    
    # Maximal 50 Zeichen
    if len(commodity) > 50:
        return False
    
    # Keine Platzhalter
    if is_placeholder_value(commodity):
        return False
    
    # Muss mindestens einen Buchstaben enthalten
    if not re.search(r'[a-zA-Z]', commodity):
        return False
    
    return True


def is_valid_production_value(value: str) -> bool:
    """Validiere Produktionswert"""
    if not value or not isinstance(value, str):
        return False
    
    value = value.strip()
    
    # Keine Platzhalter
    if is_placeholder_value(value):
        return False
    
    # Prüfe auf numerische Werte
    if re.match(r'^\d+(\.\d+)?$', value):
        return True
    
    # Prüfe auf Werte mit Einheiten
    if re.match(r'^\d+(\.\d+)?\s*[a-zA-Z]+$', value):
        return True
    
    return False


def is_valid_capacity_value(value: str) -> bool:
    """Validiere Kapazitätswert"""
    if not value or not isinstance(value, str):
        return False
    
    value = value.strip()
    
    # Keine Platzhalter
    if is_placeholder_value(value):
        return False
    
    # Prüfe auf numerische Werte
    if re.match(r'^\d+(\.\d+)?$', value):
        return True
    
    # Prüfe auf Werte mit Einheiten
    if re.match(r'^\d+(\.\d+)?\s*[a-zA-Z]+$', value):
        return True
    
    return False


def is_valid_operational_status(status: str) -> bool:
    """Validiere Betriebsstatus"""
    if not status or not isinstance(status, str):
        return False
    
    status = status.strip().lower()
    
    # Gültige Status-Werte
    valid_statuses = [
        'operational', 'active', 'producing', 'in production',
        'development', 'under development', 'exploration',
        'care and maintenance', 'suspended', 'closed',
        'mothballed', 'idle', 'standby'
    ]
    
    return status in valid_statuses


def is_valid_ownership_percentage(percentage: str) -> bool:
    """Validiere Eigentumsanteil"""
    if not percentage or not isinstance(percentage, str):
        return False
    
    percentage = percentage.strip()
    
    # Keine Platzhalter
    if is_placeholder_value(percentage):
        return False
    
    # Prüfe auf Prozent-Werte
    if re.match(r'^\d+(\.\d+)?%?$', percentage):
        return True
    
    return False


def is_valid_url(url: str) -> bool:
    """Validiere URL"""
    if not url or not isinstance(url, str):
        return False
    
    url = url.strip()
    
    # Keine Platzhalter
    if is_placeholder_value(url):
        return False
    
    # Einfache URL-Validierung
    url_pattern = re.compile(
        r'^https?://'  # http:// oder https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # Domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
        r'(?::\d+)?'  # Port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    return bool(url_pattern.match(url))


def is_valid_email(email: str) -> bool:
    """Validiere E-Mail"""
    if not email or not isinstance(email, str):
        return False
    
    email = email.strip()
    
    # Keine Platzhalter
    if is_placeholder_value(email):
        return False
    
    # Einfache E-Mail-Validierung
    email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    
    return bool(email_pattern.match(email))


def is_valid_phone(phone: str) -> bool:
    """Validiere Telefonnummer"""
    if not phone or not isinstance(phone, str):
        return False
    
    phone = phone.strip()
    
    # Keine Platzhalter
    if is_placeholder_value(phone):
        return False
    
    # Entferne Leerzeichen und Sonderzeichen
    clean_phone = re.sub(r'[^\d+]', '', phone)
    
    # Mindestlänge
    if len(clean_phone) < 7:
        return False
    
    # Maximal 20 Zeichen
    if len(clean_phone) > 20:
        return False
    
    return True


def is_valid_date(date_str: str) -> bool:
    """Validiere Datum"""
    if not date_str or not isinstance(date_str, str):
        return False
    
    date_str = date_str.strip()
    
    # Keine Platzhalter
    if is_placeholder_value(date_str):
        return False
    
    # Prüfe verschiedene Datumsformate
    date_patterns = [
        r'^\d{4}-\d{2}-\d{2}$',  # YYYY-MM-DD
        r'^\d{2}/\d{2}/\d{4}$',  # MM/DD/YYYY
        r'^\d{2}\.\d{2}\.\d{4}$',  # DD.MM.YYYY
        r'^\d{4}$'  # YYYY
    ]
    
    return any(re.match(pattern, date_str) for pattern in date_patterns)


def is_valid_coordinate(coord: str) -> bool:
    """Validiere Koordinate"""
    if not coord or not isinstance(coord, str):
        return False
    
    coord = coord.strip()
    
    # Keine Platzhalter
    if is_placeholder_value(coord):
        return False
    
    # Prüfe auf Dezimalgrad
    if re.match(r'^-?\d+(\.\d+)?$', coord):
        return True
    
    # Prüfe auf Grad/Minuten/Sekunden
    if re.match(r'^\d+°\d+\'\d+\.?\d*"[NS]?$', coord):
        return True
    
    return False


def validate_field_value(field_name: str, value: str) -> dict:
    """Validiere Feldwert basierend auf Feldname"""
    result = {
        'valid': False,
        'error': None,
        'value': value
    }
    
    if not value or not isinstance(value, str):
        result['error'] = 'Value is empty or not a string'
        return result
    
    value = value.strip()
    
    # Keine Platzhalter
    if is_placeholder_value(value):
        result['error'] = 'Value is a placeholder'
        return result
    
    # Feld-spezifische Validierung
    if field_name.lower() in ['mine_name', 'name']:
        result['valid'] = is_valid_mine_name(value)
        if not result['valid']:
            result['error'] = 'Invalid mine name'
    
    elif field_name.lower() in ['country']:
        result['valid'] = is_valid_country(value)
        if not result['valid']:
            result['error'] = 'Invalid country'
    
    elif field_name.lower() in ['region', 'province', 'state']:
        result['valid'] = is_valid_region(value)
        if not result['valid']:
            result['error'] = 'Invalid region'
    
    elif field_name.lower() in ['commodity', 'mineral', 'ore']:
        result['valid'] = is_valid_commodity(value)
        if not result['valid']:
            result['error'] = 'Invalid commodity'
    
    elif field_name.lower() in ['production', 'annual_production']:
        result['valid'] = is_valid_production_value(value)
        if not result['valid']:
            result['error'] = 'Invalid production value'
    
    elif field_name.lower() in ['capacity', 'processing_capacity']:
        result['valid'] = is_valid_capacity_value(value)
        if not result['valid']:
            result['error'] = 'Invalid capacity value'
    
    elif field_name.lower() in ['operational_status', 'status']:
        result['valid'] = is_valid_operational_status(value)
        if not result['valid']:
            result['error'] = 'Invalid operational status'
    
    elif field_name.lower() in ['ownership', 'ownership_percentage']:
        result['valid'] = is_valid_ownership_percentage(value)
        if not result['valid']:
            result['error'] = 'Invalid ownership percentage'
    
    elif field_name.lower() in ['url', 'website']:
        result['valid'] = is_valid_url(value)
        if not result['valid']:
            result['error'] = 'Invalid URL'
    
    elif field_name.lower() in ['email', 'contact_email']:
        result['valid'] = is_valid_email(value)
        if not result['valid']:
            result['error'] = 'Invalid email'
    
    elif field_name.lower() in ['phone', 'telephone', 'contact_phone']:
        result['valid'] = is_valid_phone(value)
        if not result['valid']:
            result['error'] = 'Invalid phone number'
    
    elif field_name.lower() in ['date', 'start_date', 'end_date']:
        result['valid'] = is_valid_date(value)
        if not result['valid']:
            result['error'] = 'Invalid date'
    
    elif field_name.lower() in ['latitude', 'longitude', 'lat', 'lng']:
        result['valid'] = is_valid_coordinate(value)
        if not result['valid']:
            result['error'] = 'Invalid coordinate'
    
    else:
        # Allgemeine Validierung für unbekannte Felder
        result['valid'] = len(value) > 0 and len(value) <= 500
        if not result['valid']:
            result['error'] = 'Value too short or too long'
    
    return result


def validate_extraction_result(result: dict) -> dict:
    """Validiere gesamtes Extraktionsergebnis"""
    validation_result = {
        'valid': True,
        'errors': [],
        'warnings': [],
        'field_validations': {}
    }
    
    if not result or not isinstance(result, dict):
        validation_result['valid'] = False
        validation_result['errors'].append('Result is not a dictionary')
        return validation_result
    
    # Validiere jedes Feld
    for field_name, field_value in result.items():
        if field_value:
            field_validation = validate_field_value(field_name, str(field_value))
            validation_result['field_validations'][field_name] = field_validation
            
            if not field_validation['valid']:
                validation_result['valid'] = False
                validation_result['errors'].append(f"{field_name}: {field_validation['error']}")
    
    # Prüfe auf mindestens ein gültiges Feld
    valid_fields = sum(1 for v in validation_result['field_validations'].values() if v['valid'])
    if valid_fields == 0:
        validation_result['valid'] = False
        validation_result['errors'].append('No valid fields found')
    
    return validation_result


__all__ = [
    "is_placeholder_value",
    "is_valid_mine_name",
    "is_valid_country",
    "is_valid_region",
    "is_valid_commodity",
    "is_valid_production_value",
    "is_valid_capacity_value",
    "is_valid_operational_status",
    "is_valid_ownership_percentage",
    "is_valid_url",
    "is_valid_email",
    "is_valid_phone",
    "is_valid_date",
    "is_valid_coordinate",
    "validate_field_value",
    "validate_extraction_result"
]
