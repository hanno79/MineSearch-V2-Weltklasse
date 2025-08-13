"""
Author: rahn
Datum: 13.08.2025
Version: 1.0
Beschreibung: Field-Mappings und Utility-Funktionen für konsolidierte Ergebnisse
Extrahiert aus consolidated_results.py für Regel-1-Compliance (<500 Zeilen)
"""

import logging

logger = logging.getLogger(__name__)

# FIELD CONSOLIDATION AND RENAMING MAPPING
FIELD_CONSOLIDATION_MAP = {
    # Consolidate duplicate fields - map to preferred German names
    'Name': 'Mine',  # Name -> Mine (remove duplicate)
    'Country': 'Land',  # Country -> Land (remove duplicate)
    # Additional consolidation mappings
    'mine_name': 'Mine',  # English field name -> German
    'country': 'Land',   # English field name -> German
    # CRITICAL FIX 06.08.2025: Rohstoff-Duplikat-Elimination
    'Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)': 'Rohstoffe',  # Primary consolidation
    'Rohstoffabbau (Gold/Kupfer/Kohle/usw.)': 'Rohstoffe',     # Alternative spacing
    'Rohstoffabbau': 'Rohstoffe',                               # Short form
    'Commodity': 'Rohstoffe',                                   # English variant
    'Commodities': 'Rohstoffe',                                 # English plural
    'Rohstofftyp': 'Rohstoffe',                                # Alternative German
    # BACKEND-FIELD-SPECIALIST-FIX 30.07.2025: Kritische fehlende Mappings
    'restoration_costs': 'Restaurationskosten',  # English -> German
    'cost_year': 'Kostenjahr',  # English -> German  
    'document_year': 'Dokumentenjahr',  # English -> German
    'production_start': 'Produktionsstart',  # English -> German
    'mine_area': 'Minenfläche in qkm',  # English -> German
    'x_coordinate': 'x-Koordinate',  # English -> German
    'longitude': 'x-Koordinate',  # Alternative English -> German
    'latitude': 'y-Koordinate',  # Alternative English -> German
}

FIELD_RENAME_MAP = {
    # Rename fields as requested - USER REQUIREMENTS 30.07.2025
    'Jahr der Aufnahme der Kosten': 'Kostenjahr',
    'Jahr der Erstellung des Dokumentes': 'Dokumentenjahr', 
    'Jahr der Erstellung der Dokumentes': 'Dokumentenjahr',  # Alternative spelling
    'Fläche der Mine in qkm': 'Minenfläche in qkm',
    'Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)': 'Rohstoffe',
    'Rohstoffabbau (Gold/Kupfer/Kohle/usw.)': 'Rohstoffe',  # Alternative spacing
    'Minentyp (Untertage/ Open-Pit/ usw.)': 'Minentyp',
    # Additional potential variations
    'Jahr der Aufnahme der Kosten (YYYY)': 'Kostenjahr',
    'Jahr der Erstellung des Dokuments': 'Dokumentenjahr',
    'Fläche der Mine (qkm)': 'Minenfläche in qkm',
    'Rohstofftyp': 'Rohstoffe',
    'Commodity': 'Rohstoffe',
    # CRITICAL FIX 30.07.2025: Additional English field variations
    'Restoration Costs': 'Restaurationskosten',
    'Restoration Cost': 'Restaurationskosten',
    'Cost Year': 'Kostenjahr',
    'Document Year': 'Dokumentenjahr',
    'Mine Area': 'Minenfläche in qkm',
    'Production Start': 'Produktionsstart',
    'Start of Production': 'Produktionsstart',
    'Production Begin': 'Produktionsstart',
    # Potential DB field variations
    'Kosten für Restauration': 'Restaurationskosten',
    'Restaurierung Kosten': 'Restaurationskosten',
    'Wiederherstellungskosten': 'Restaurationskosten',
    # BACKEND-FIELD-SPECIALIST-FIX 30.07.2025: Weitere alternative Feldnamen
    'Restoration Costs': 'Restaurationskosten',
    'Restoration Cost': 'Restaurationskosten',
    'Cost Year': 'Kostenjahr',
    'Document Year': 'Dokumentenjahr',
    'Mine Area': 'Minenfläche in qkm',
    'Area': 'Minenfläche in qkm',
    'Area in qkm': 'Minenfläche in qkm',
    'Area (qkm)': 'Minenfläche in qkm',
    'Mine Size': 'Minenfläche in qkm',
    'Size (qkm)': 'Minenfläche in qkm',
    'X-Coordinate': 'x-Koordinate',
    'Y-Coordinate': 'y-Koordinate',
    'Longitude': 'x-Koordinate',
    'Latitude': 'y-Koordinate',
    'Production Start': 'Produktionsstart',
    'Start of Production': 'Produktionsstart',
    # Alternative deutsche Schreibweisen
    'Restaurierungskosten': 'Restaurationskosten',
    'Wiederherstellungskosten': 'Restaurationskosten',
    'Sanierungskosten': 'Restaurationskosten',
    'Schließungskosten': 'Restaurationskosten'
}

# PREFERRED FIELD ORDER for frontend - USER REQUIREMENTS 30.07.2025
FIELD_ORDER = [
    'Mine', 'Land', 'Region', 'Zuverlässigkeit', 'Modelle', 'Letzte Aktualisierung',
    'Betreiber', 'Eigentümer', 'Rohstoffe', 'Minentyp', 'Aktivitätsstatus', 
    'Produktionsstart', 'Produktionsende', 'Fördermenge/Jahr', 'Minenfläche in qkm',
    'x-Koordinate', 'y-Koordinate', 'Restaurationskosten', 'Kostenjahr', 
    'Dokumentenjahr', 'Quellenangaben', 'Details'
]

def consolidate_and_rename_field(field_name, field_value):
    """
    Konsolidiert doppelte Felder und benennt Felder um
    
    Returns: (final_field_name, field_value) or None if field should be skipped
    """
    # Step 1: Check if field should be consolidated (removed)
    if field_name in FIELD_CONSOLIDATION_MAP:
        target_field = FIELD_CONSOLIDATION_MAP[field_name]
        logger.debug(f"Consolidating field '{field_name}' -> '{target_field}'")
        return target_field, field_value
    
    # Step 2: Check if field should be renamed
    if field_name in FIELD_RENAME_MAP:
        new_name = FIELD_RENAME_MAP[field_name]
        logger.debug(f"Renaming field '{field_name}' -> '{new_name}'")
        return new_name, field_value
    
    # Step 3: Return original field
    return field_name, field_value