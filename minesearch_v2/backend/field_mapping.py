"""
Author: rahn
Datum: 29.07.2025
Version: 1.0
Beschreibung: Feldmapping für Konsolidierung und Umbenennungen
"""

# Mapping von alten zu neuen Feldnamen
FIELD_MAPPING = {
    # Konsolidierungen
    'Name': 'Mine',
    'Country': 'Land',
    
    # Umbenennungen
    'Jahr der Aufnahme der Kosten': 'Kostenjahr',
    'Jahr der Erstellung des Dokumentes': 'Dokumentenjahr',
    'Fläche der Mine in qkm': 'Minenfläche in qkm',
    'Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)': 'Rohstoffe',
    
    # Unveränderte Felder (zur Vollständigkeit)
    'Region': 'Region',
    'Betreiber': 'Betreiber',
    'Eigentümer': 'Eigentümer',
    'Minentyp': 'Minentyp',
    'Aktivitätsstatus': 'Aktivitätsstatus',
    'Produktionsstart': 'Produktionsstart',
    'Produktionsende': 'Produktionsende',
    'Fördermenge/Jahr': 'Fördermenge/Jahr',
    'x-Koordinate': 'x-Koordinate',
    'y-Koordinate': 'y-Koordinate',
    'Restaurationskosten': 'Restaurationskosten',
    'Quellenangaben': 'Quellenangaben',
    
    # Neue Felder
    # DEFINITIVE-FIX 01.08.2025: Zuverlässigkeit entfernt - wird nur über overall_confidence angezeigt
    'Modelle': 'Modelle',
    'Letzte Aktualisierung': 'Letzte Aktualisierung',
    'Details': 'Details'
}

# Umgekehrtes Mapping (neu zu alt)
REVERSE_FIELD_MAPPING = {v: k for k, v in FIELD_MAPPING.items()}

def convert_old_to_new(data_dict):
    """
    Konvertiert ein Dictionary mit alten Feldnamen zu neuen Feldnamen
    
    Args:
        data_dict: Dictionary mit alten Feldnamen
        
    Returns:
        Dictionary mit neuen Feldnamen
    """
    if not isinstance(data_dict, dict):
        return data_dict
    
    converted = {}
    for old_key, value in data_dict.items():
        new_key = FIELD_MAPPING.get(old_key, old_key)
        converted[new_key] = value
    
    return converted

def convert_new_to_old(data_dict):
    """
    Konvertiert ein Dictionary mit neuen Feldnamen zu alten Feldnamen
    
    Args:
        data_dict: Dictionary mit neuen Feldnamen
        
    Returns:
        Dictionary mit alten Feldnamen
    """
    if not isinstance(data_dict, dict):
        return data_dict
    
    converted = {}
    for new_key, value in data_dict.items():
        old_key = REVERSE_FIELD_MAPPING.get(new_key, new_key)
        converted[old_key] = value
    
    return converted

def get_field_display_order():
    """
    Gibt die gewünschte Anzeigereihenfolge der Felder zurück
    
    Returns:
        Liste der Feldnamen in der gewünschten Reihenfolge
    """
    return [
        'Mine', 'Land', 'Region', 'Modelle', 'Letzte Aktualisierung',
        'Betreiber', 'Eigentümer', 'Rohstoffe', 'Minentyp', 'Aktivitätsstatus', 
        'Produktionsstart', 'Produktionsende', 'Fördermenge/Jahr', 'Minenfläche in qkm',
        'x-Koordinate', 'y-Koordinate', 'Restaurationskosten', 'Kostenjahr', 
        'Dokumentenjahr', 'Quellenangaben', 'Details'
    ]