#!/usr/bin/env python3
"""
Author: rahn
Datum: 19.07.2025
Version: 1.0
Beschreibung: Demo der implementierten Datenkonsistenz-Fixes
"""

from extraction_processors import normalize_field_value, clean_field_value
from source_manager import SourceManager
from data_extraction import DataExtractor

def demo_leer_fixes():
    """Demonstriert LEER-Werte Normalisierung"""
    print("🔧 Demo: LEER-Werte Normalisierung")
    print("-" * 40)
    
    test_values = [
        "LEER - keine verlässlichen Daten verfügbar",
        "LEER - Keine verlässlichen Daten verfügbar", 
        "Leer - status unklar",
        "LEER - status unklar",
        "LEER - Minentyp unbekannt",
        "LEER - Typ unbekannt",
        "Normale Werte bleiben"
    ]
    
    for value in test_values:
        normalized = normalize_field_value(value)
        status = "✅ KONVERTIERT" if normalized == "X" else "➡️ BEHALTEN"
        print(f"  '{value}' → '{normalized}' {status}")

def demo_minentyp_fixes():
    """Demonstriert Minentyp-Präfix Entfernung"""
    print("\n🔧 Demo: Minentyp-Präfix Entfernung")
    print("-" * 40)
    
    test_values = [
        "Untertage/ Open-Pit/ usw.): Open-Pit",
        "Untertage/ Open-Pit/ usw.): Untertage",
        "Untertage/ Open-Pit/ usw.): LEER - Typ unbekannt",
        "(Untertage/ Open-Pit/ usw.): Surface",
        "Open-Pit ohne Präfix"
    ]
    
    for value in test_values:
        cleaned = clean_field_value(value, "Minentyp (Untertage/ Open-Pit/ usw.)")
        has_prefix = "Untertage/ Open-Pit/ usw.):" in value
        status = "✅ BEREINIGT" if has_prefix and "Untertage/ Open-Pit/ usw.):" not in cleaned else "➡️ UNVERÄNDERT"
        print(f"  '{value}' → '{cleaned}' {status}")

def demo_source_management():
    """Demonstriert Quellen-Management"""
    print("\n🔧 Demo: Quellen-Management")
    print("-" * 40)
    
    sm = SourceManager()
    
    # Simuliere Quellen-Extraktion
    mock_response = """
    Mine data for Test:
    - Owner: Newmont Corp [1]
    - Operator: Newmont Corp [1,2]
    - Type: Open-Pit [2]
    
    Sources:
    [1] https://mern.gouv.qc.ca/mines/test/
    [2] https://sedar.com/filings/test/
    """
    
    print("  📥 Response mit Quellen:")
    print("     - Owner: Newmont Corp [1]")
    print("     - Operator: Newmont Corp [1,2]")
    print("     - Sources: [1] gov.qc.ca, [2] sedar.com")
    
    # Extrahiere Quellen
    found_sources = sm.extract_sources_from_response(mock_response)
    print(f"\n  🔍 Extrahierte Quellen: {len(found_sources)}")
    
    # Parse Felder
    owner_clean, owner_sources = sm.parse_field_with_sources("Newmont Corp [1]")
    operator_clean, operator_sources = sm.parse_field_with_sources("Newmont Corp [1,2]")
    
    print(f"  📝 Owner: '{owner_clean}' → Quellen {owner_sources}")
    print(f"  📝 Operator: '{operator_clean}' → Quellen {operator_sources}")
    
    # Zuordnung
    sm.assign_field_sources("Eigentümer", owner_sources)
    sm.assign_field_sources("Betreiber", operator_sources)
    
    # Formatierung
    formatted_owner = sm.format_field_with_sources("Newmont Corp", "Eigentümer")
    formatted_operator = sm.format_field_with_sources("Newmont Corp", "Betreiber")
    
    print(f"  📤 Formatiert Owner: '{formatted_owner}'")
    print(f"  📤 Formatiert Operator: '{formatted_operator}'")
    
    # Quellenangaben
    summary = sm.get_sources_summary()
    print(f"  📋 Quellenangaben:")
    for line in summary.split('\n'):
        print(f"     {line}")

def demo_full_extraction():
    """Demonstriert komplette Extraktion mit allen Fixes"""
    print("\n🔧 Demo: Komplette Extraktion")
    print("-" * 40)
    
    mock_response = """
    Mining Information for Demo Mine:
    
    Basic Information:
    - Eigentümer: LEER - keine verlässlichen Daten verfügbar
    - Betreiber: Leer - status unklar
    - Minentyp (Untertage/ Open-Pit/ usw.): Untertage/ Open-Pit/ usw.): Open-Pit
    - Aktivitätsstatus: Aktiv
    - Rohstoffabbau: Gold; Kupfer; Silber
    
    Location:
    - x-Koordinate: 45.123456
    - y-Koordinate: -73.987654
    
    Sources:
    [1] https://mern.gouv.qc.ca/mines/demo/
    [2] https://sedar.com/filings/demo-report/
    """
    
    print("  📥 Input mit problematischen Daten:")
    print("     - Eigentümer: 'LEER - keine verlässlichen Daten verfügbar'")
    print("     - Betreiber: 'Leer - status unklar'")
    print("     - Minentyp: 'Untertage/ Open-Pit/ usw.): Open-Pit'")
    print("     - Rohstoffabbau: 'Gold; Kupfer; Silber'")
    
    extractor = DataExtractor()
    result = extractor.extract_structured_data(mock_response, "Demo Mine", "Canada")
    
    print("\n  📤 Output nach Bereinigung:")
    key_fields = ["Eigentümer", "Betreiber", "Minentyp (Untertage/ Open-Pit/ usw.)", "Aktivitätsstatus", "Quellenangaben"]
    
    for field in key_fields:
        value = result.get(field, "N/A")
        print(f"     - {field}: '{value}'")
    
    # Zeige Source Mapping
    source_mapping = result.get("_source_mapping", {})
    if source_mapping:
        sources = source_mapping.get("sources", {})
        print(f"\n  🔗 Quellen-Mapping: {len(sources)} Quellen erfasst")

def main():
    print("🧪 Demo der Datenkonsistenz-Fixes")
    print("=" * 50)
    
    demo_leer_fixes()
    demo_minentyp_fixes() 
    demo_source_management()
    demo_full_extraction()
    
    print("\n" + "=" * 50)
    print("✅ Alle Fixes erfolgreich demonstriert!")
    print("\n📋 Zusammenfassung der Verbesserungen:")
    print("  1. ✅ LEER-Werte → 'X' Normalisierung")
    print("  2. ✅ Minentyp-Präfix Entfernung")
    print("  3. ✅ Quellen-Nummerierung [1,2,3]") 
    print("  4. ✅ Feld-spezifische Quellenreferenzen")
    print("  5. ✅ Strukturierte Quellenangaben")

if __name__ == "__main__":
    main()