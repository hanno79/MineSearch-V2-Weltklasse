"""
Author: rahn
Datum: 29.07.2025
Version: 1.0
Beschreibung: Standardisierte Hilfsfunktionen für Feldberechnungen und -validierung
"""

from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

def count_filled_fields(structured_data: Dict[str, Any], exclude_x_values: bool = True) -> int:
    """
    Standardisierte Funktion zur Zählung von gefüllten Feldern
    
    Args:
        structured_data: Dictionary mit Feldnamen und Werten
        exclude_x_values: Ob X-Werte ausgeschlossen werden sollen (default: True)
    
    Returns:
        Anzahl der Felder mit echten Daten
    """
    if not structured_data:
        return 0
    
    filled_count = 0
    for field_name, field_value in structured_data.items():
        if is_field_filled(field_value, exclude_x_values):
            filled_count += 1
    
    return filled_count

def is_field_filled(field_value: Any, exclude_x_values: bool = True) -> bool:
    """
    Prüft ob ein Feldwert als "gefüllt" gilt
    
    Args:
        field_value: Der zu prüfende Wert
        exclude_x_values: Ob X-Werte als leer gelten sollen
    
    Returns:
        True wenn Feld als gefüllt gilt, False sonst
    """
    # Grundlegende Leer-Prüfung
    if not field_value:
        return False
    
    # String-Wert prüfen
    str_value = str(field_value).strip()
    if not str_value:
        return False
    
    # X-Werte ausschließen wenn gewünscht
    if exclude_x_values and str_value.upper() == 'X':
        return False
    
    # Standard "leer"-Werte ausschließen
    empty_indicators = {
        'n/a', 'na', 'unknown', 'unbekannt', 'leer', 'null', 'none', 
        'not available', 'nicht verfügbar', 'keine angabe', 'keine daten'
    }
    
    if str_value.lower() in empty_indicators:
        return False
    
    return True

def calculate_data_quality_percentage(structured_data: Dict[str, Any], total_expected_fields: int = 22) -> float:
    """
    Berechnet die Datenqualität als Prozentsatz
    
    Args:
        structured_data: Dictionary mit Feldnamen und Werten
        total_expected_fields: Anzahl der erwarteten Felder (default: 22)
    
    Returns:
        Prozentsatz der Datenqualität (0-100)
    """
    if not structured_data or total_expected_fields <= 0:
        return 0.0
    
    filled_fields = count_filled_fields(structured_data, exclude_x_values=True)
    return round((filled_fields / total_expected_fields) * 100, 1)

def get_empty_fields(structured_data: Dict[str, Any]) -> List[str]:
    """
    Gibt eine Liste der leeren Felder zurück
    
    Args:
        structured_data: Dictionary mit Feldnamen und Werten
    
    Returns:
        Liste der Feldnamen die leer sind
    """
    if not structured_data:
        return []
    
    empty_fields = []
    for field_name, field_value in structured_data.items():
        if not is_field_filled(field_value, exclude_x_values=True):
            empty_fields.append(field_name)
    
    return empty_fields

def get_filled_fields(structured_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Gibt ein Dictionary mit nur den gefüllten Feldern zurück
    
    Args:
        structured_data: Dictionary mit Feldnamen und Werten
    
    Returns:
        Dictionary mit nur gefüllten Feldern
    """
    if not structured_data:
        return {}
    
    filled_fields = {}
    for field_name, field_value in structured_data.items():
        if is_field_filled(field_value, exclude_x_values=True):
            filled_fields[field_name] = field_value
    
    return filled_fields

def standardize_field_value(field_value: Any) -> str:
    """
    Standardisiert einen Feldwert für Vergleiche
    
    Args:
        field_value: Der zu standardisierende Wert
    
    Returns:
        Standardisierter String-Wert
    """
    if not field_value:
        return ""
    
    str_value = str(field_value).strip()
    
    # Standardisiere häufige Varianten von "leer" Werten
    empty_variants = {
        'n/a': 'N/A',
        'na': 'N/A', 
        'unknown': 'Unbekannt',
        'not available': 'Nicht verfügbar',
        'keine angabe': 'Keine Angabe',
        'keine daten': 'Keine Daten',
        'null': 'N/A',
        'none': 'N/A'
    }
    
    lower_value = str_value.lower()
    if lower_value in empty_variants:
        return empty_variants[lower_value]
    
    return str_value

def validate_field_consistency(field_values: List[Any]) -> Dict[str, Any]:
    """
    Validiert die Konsistenz von Feldwerten aus verschiedenen Quellen
    
    Args:
        field_values: Liste von Werten für dasselbe Feld aus verschiedenen Quellen
    
    Returns:
        Dictionary mit Konsistenz-Metriken
    """
    if not field_values:
        return {
            'is_consistent': True,
            'unique_values': 0,
            'most_common_value': None,
            'confidence_score': 0
        }
    
    # Standardisiere alle Werte
    standardized_values = [standardize_field_value(v) for v in field_values if is_field_filled(v)]
    
    if not standardized_values:
        return {
            'is_consistent': True,
            'unique_values': 0,
            'most_common_value': None,
            'confidence_score': 0
        }
    
    # Zähle einzigartige Werte
    value_counts = {}
    for value in standardized_values:
        value_counts[value] = value_counts.get(value, 0) + 1
    
    unique_values = len(value_counts)
    most_common_value = max(value_counts.items(), key=lambda x: x[1])
    
    # Berechne Konsistenz-Score
    total_values = len(standardized_values)
    consistency_ratio = most_common_value[1] / total_values
    confidence_score = round(consistency_ratio * 100, 1)
    
    return {
        'is_consistent': unique_values == 1,
        'unique_values': unique_values,
        'most_common_value': most_common_value[0],
        'most_common_count': most_common_value[1],
        'total_values': total_values,
        'confidence_score': confidence_score,
        'all_values': list(value_counts.keys())
    }

# Legacy-Kompatibilität: Export der Hauptfunktion unter dem alten Namen
def count_filled_fields_legacy(structured_data: Dict[str, Any]) -> int:
    """Legacy-Wrapper für count_filled_fields"""
    return count_filled_fields(structured_data, exclude_x_values=True)

# Modul-Export für einfache Imports
__all__ = [
    'count_filled_fields',
    'is_field_filled', 
    'calculate_data_quality_percentage',
    'get_empty_fields',
    'get_filled_fields',
    'standardize_field_value',
    'validate_field_consistency',
    'count_filled_fields_legacy'
]