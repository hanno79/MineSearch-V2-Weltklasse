"""
Author: rahn
Datum: 13.08.2025
Version: 1.0
Beschreibung: Field-Mappings und Utility-Funktionen für konsolidierte Ergebnisse
Extrahiert aus consolidated_results.py für Regel-1-Compliance (<500 Zeilen)
"""

import logging

logger = logging.getLogger(__name__)

# PHASE 1.3: ENHANCED FIELD CONSOLIDATION MAPPING 14.08.2025
# Vollständige Feldkonsolidierung für maximale Feldabdeckung
FIELD_CONSOLIDATION_MAP = {
    # Basic Field Mappings - Englisch/Deutsch Konsolidierung
    'Name': 'Mine',  # Name -> Mine (remove duplicate)
    'Country': 'Land',  # Country -> Land (remove duplicate)
    'mine_name': 'Mine',  # English field name -> German
    'country': 'Land',   # English field name -> German
    'region': 'Region',  # English -> German
    
    # CRITICAL FIX: Rohstoff-Duplikat-Elimination (erweitert)
    'Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)': 'Rohstoffe',
    'Rohstoffabbau (Gold/Kupfer/Kohle/usw.)': 'Rohstoffe',
    'Rohstoffabbau': 'Rohstoffe',
    'Commodity': 'Rohstoffe',
    'Commodities': 'Rohstoffe',
    'Rohstofftyp': 'Rohstoffe',
    'Primary Commodity': 'Rohstoffe',
    'Main Commodity': 'Rohstoffe',
    'Hauptrohstoff': 'Rohstoffe',
    
    # PHASE 1.3: Erweiterte Betreiber/Eigentümer-Konsolidierung
    'Owner': 'Eigentümer',
    'Operator': 'Betreiber', 
    'Mine Owner': 'Eigentümer',
    'Mine Operator': 'Betreiber',
    'Operating Company': 'Betreiber',
    'Ownership': 'Eigentümer',
    'Management': 'Betreiber',
    'Unternehmen': 'Betreiber',  # Fallback
    
    # PHASE 1.3: Koordinaten-System-Konsolidierung
    'restoration_costs': 'Restaurationskosten',
    'cost_year': 'Kostenjahr',
    'document_year': 'Dokumentenjahr',
    'production_start': 'Produktionsstart',
    'production_end': 'Produktionsende',
    'mine_area': 'Minenfläche in qkm',
    'x_coordinate': 'x-Koordinate',
    'y_coordinate': 'y-Koordinate',
    'longitude': 'x-Koordinate',
    'latitude': 'y-Koordinate',
    'coordinates': 'x-Koordinate',  # Will need special handling
    
    # PHASE 1.3: Status/Typ-Konsolidierung  
    'status': 'Aktivitätsstatus',
    'mine_status': 'Aktivitätsstatus',
    'operation_status': 'Aktivitätsstatus',
    'activity_status': 'Aktivitätsstatus',
    'mine_type': 'Minentyp',
    'type': 'Minentyp',
    'operation_type': 'Minentyp',
    
    # PHASE 1.3: Produktions-Konsolidierung
    'annual_production': 'Fördermenge/Jahr',
    'production_rate': 'Fördermenge/Jahr',
    'yearly_production': 'Fördermenge/Jahr',
    'production_volume': 'Fördermenge/Jahr',
    'output': 'Fördermenge/Jahr',
    
    # PHASE 1.3: Sonstige wichtige Mappings
    'sources': 'Quellenangaben',
    'source': 'Quellenangaben',
    'data_sources': 'Quellenangaben',
    'references': 'Quellenangaben'
}

# PHASE 1.3: ENHANCED FIELD RENAME MAPPING 14.08.2025
# Erweiterte Umbenennung für vollständige Feldabdeckung
FIELD_RENAME_MAP = {
    # Original USER REQUIREMENTS 30.07.2025
    'Jahr der Aufnahme der Kosten': 'Kostenjahr',
    'Jahr der Erstellung des Dokumentes': 'Dokumentenjahr', 
    'Jahr der Erstellung der Dokumentes': 'Dokumentenjahr',  # Alternative spelling
    'Fläche der Mine in qkm': 'Minenfläche in qkm',
    'Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)': 'Rohstoffe',
    'Rohstoffabbau (Gold/Kupfer/Kohle/usw.)': 'Rohstoffe',  # Alternative spacing
    'Minentyp (Untertage/ Open-Pit/ usw.)': 'Minentyp',
    
    # PHASE 1.3: Erweiterte zeitbezogene Felder
    'Jahr der Aufnahme der Kosten (YYYY)': 'Kostenjahr',
    'Jahr der Erstellung des Dokuments': 'Dokumentenjahr',
    'Document Creation Year': 'Dokumentenjahr',
    'Cost Assessment Year': 'Kostenjahr',
    'Year of Cost Assessment': 'Kostenjahr',
    'Dokumentationsjahr': 'Dokumentenjahr',
    'Kostenermittlungsjahr': 'Kostenjahr',
    
    # PHASE 1.3: Erweiterte Flächenfelder
    'Fläche der Mine (qkm)': 'Minenfläche in qkm',
    'Minenfläche (qkm)': 'Minenfläche in qkm',
    'Fläche (qkm)': 'Minenfläche in qkm',
    'Area': 'Minenfläche in qkm',
    'Area in qkm': 'Minenfläche in qkm',
    'Area (qkm)': 'Minenfläche in qkm',
    'Mine Size': 'Minenfläche in qkm',
    'Size (qkm)': 'Minenfläche in qkm',
    'Total Area': 'Minenfläche in qkm',
    'Site Area': 'Minenfläche in qkm',
    
    # PHASE 1.3: Erweiterte Kostenfelder
    'Restoration Costs': 'Restaurationskosten',
    'Restoration Cost': 'Restaurationskosten',
    'Remediation Costs': 'Restaurationskosten',
    'Closure Costs': 'Restaurationskosten',
    'Reclamation Costs': 'Restaurationskosten',
    'Environmental Costs': 'Restaurationskosten',
    'Kosten für Restauration': 'Restaurationskosten',
    'Restaurierungskosten': 'Restaurationskosten',
    'Wiederherstellungskosten': 'Restaurationskosten',
    'Sanierungskosten': 'Restaurationskosten',
    'Schließungskosten': 'Restaurationskosten',
    'Umweltkosten': 'Restaurationskosten',
    
    # PHASE 1.3: Erweiterte Koordinatenfelder
    'X-Coordinate': 'x-Koordinate',
    'Y-Coordinate': 'y-Koordinate',
    'Longitude': 'x-Koordinate',
    'Latitude': 'y-Koordinate',
    'Längengrad': 'x-Koordinate',
    'Breitengrad': 'y-Koordinate',
    'GPS Longitude': 'x-Koordinate',
    'GPS Latitude': 'y-Koordinate',
    'East Coordinate': 'x-Koordinate',
    'North Coordinate': 'y-Koordinate',
    
    # PHASE 1.3: Erweiterte Produktionsfelder
    'Production Start': 'Produktionsstart',
    'Start of Production': 'Produktionsstart',
    'Production Begin': 'Produktionsstart',
    'Operation Start': 'Produktionsstart',
    'Mining Start': 'Produktionsstart',
    'Produktionsbeginn': 'Produktionsstart',
    'Betriebsstart': 'Produktionsstart',
    'Abbaubeginn': 'Produktionsstart',
    
    'Production End': 'Produktionsende',
    'End of Production': 'Produktionsende',
    'Operation End': 'Produktionsende',
    'Mining End': 'Produktionsende',  
    'Closure Date': 'Produktionsende',
    'Produktionsende': 'Produktionsende',
    'Betriebsende': 'Produktionsende',
    'Schließung': 'Produktionsende',
    
    # PHASE 1.3: Erweiterte Minentyp-Felder
    'Mine Type': 'Minentyp',
    'Mining Method': 'Minentyp',
    'Operation Type': 'Minentyp',
    'Extraction Method': 'Minentyp',
    'Abbaumethode': 'Minentyp',
    'Bergbautyp': 'Minentyp',
    'Förderart': 'Minentyp',
    
    # PHASE 1.3: Erweiterte Status-Felder  
    'Mine Status': 'Aktivitätsstatus',
    'Operation Status': 'Aktivitätsstatus',
    'Activity Status': 'Aktivitätsstatus',
    'Current Status': 'Aktivitätsstatus',
    'Betriebsstatus': 'Aktivitätsstatus',
    'Minenstatus': 'Aktivitätsstatus',
    'Aktueller Status': 'Aktivitätsstatus'
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
    PHASE 1.3: Enhanced field consolidation mit Template-Pattern-Erkennung
    Konsolidiert doppelte Felder und benennt Felder um
    
    Returns: (final_field_name, processed_field_value)
    """
    # Step 1: Check if field should be consolidated (removed)
    if field_name in FIELD_CONSOLIDATION_MAP:
        target_field = FIELD_CONSOLIDATION_MAP[field_name]
        logger.debug(f"[PHASE 1.3] Consolidating field '{field_name}' -> '{target_field}'")
        return target_field, _process_field_value(field_value, target_field)
    
    # Step 2: Check if field should be renamed
    if field_name in FIELD_RENAME_MAP:
        new_name = FIELD_RENAME_MAP[field_name]
        logger.debug(f"[PHASE 1.3] Renaming field '{field_name}' -> '{new_name}'")
        return new_name, _process_field_value(field_value, new_name)
    
    # Step 3: Return original field with processed value
    return field_name, _process_field_value(field_value, field_name)

def _process_field_value(field_value, field_name):
    """
    PHASE 1.3: Verarbeitet Feldwerte und erkennt Template-Pattern
    """
    if not field_value or not str(field_value).strip():
        return field_value
    
    value_str = str(field_value).strip()
    
    # PHASE 1.3: Template-Pattern-Erkennung
    template_patterns = [
        # Häufige Template-Strukturen die AI-Modelle verwenden
        r'.*\(.*[/|]+.*\)',  # "(Gold/ Kupfer/ Kohle/ usw.)" pattern
        r'.*\(.*\s+or\s+.*\)',  # "(Underground or Open-Pit)" pattern  
        r'.*\(e\.g\..*\)',  # "(e.g. Gold, Copper)" pattern
        r'.*\(z\.B\..*\)',  # "(z.B. Gold, Kupfer)" pattern
        r'.*\(beispielsweise.*\)',  # Template explanations
        r'.*\(such as.*\)',  # English template explanations
        r'.*(usw\.|etc\.)\)',  # Endings with "usw." or "etc."
        r'^(Not specified|Not available|Unknown|TBD|N/A|-)$',  # Explicit placeholder values
        r'^(Nicht angegeben|Nicht verfügbar|Unbekannt|k\.A\.|n\.a\.)$'  # German placeholders
    ]
    
    import re
    for pattern in template_patterns:
        if re.match(pattern, value_str, re.IGNORECASE):
            logger.debug(f"[PHASE 1.3] Template pattern detected in field '{field_name}': '{value_str}'")
            # Mark as template but don't remove - let scoring system handle it
            return f"TEMPLATE: {value_str}"
    
    # PHASE 1.3: Spezielle Feldverarbeitung
    if field_name in ['x-Koordinate', 'y-Koordinate']:
        # Extract numeric coordinates from various formats
        coord_match = re.search(r'(-?\d+\.?\d*)', value_str)
        if coord_match:
            return coord_match.group(1)
    
    if field_name == 'Minenfläche in qkm':
        # Extract area values and normalize units
        area_match = re.search(r'(\d+\.?\d*)\s*(qkm|km²|km2|square km)', value_str, re.IGNORECASE)
        if area_match:
            return f"{area_match.group(1)} qkm"
    
    if field_name in ['Kostenjahr', 'Dokumentenjahr', 'Produktionsstart', 'Produktionsende']:
        # Extract years from various date formats
        year_match = re.search(r'(19|20)\d{2}', value_str)
        if year_match:
            return year_match.group(0)
    
    return field_value

def is_template_value(value, field_name=None):
    """
    PHASE 1.3: Prüft ob ein Wert ein Template-Pattern ist
    """
    if not value or not str(value).strip():
        return True
        
    value_str = str(value).strip()
    
    # Check if value starts with TEMPLATE: marker
    if value_str.startswith('TEMPLATE:'):
        return True
        
    # Additional template checks
    template_indicators = [
        '(', '/', 'usw.', 'etc.', 'z.B.', 'e.g.',
        'Not specified', 'Not available', 'Unknown',
        'Nicht angegeben', 'Nicht verfügbar', 'Unbekannt'
    ]
    
    return any(indicator in value_str for indicator in template_indicators)