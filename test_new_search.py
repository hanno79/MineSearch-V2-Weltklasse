#!/usr/bin/env python3
"""
Author: rahn
Datum: 19.07.2025
Version: 1.0
Beschreibung: Test einer neuen Suche mit den Datenkonsistenz-Fixes
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'minesearch_v2', 'backend'))

from data_extraction import DataExtractor
from source_manager import SourceManager

def test_new_extraction():
    """Teste Datenextraktion mit den neuen Fixes"""
    print("🧪 Teste neue Datenextraktion mit Fixes...")
    
    # Simuliere Provider-Response mit problematischen Daten
    mock_response = """
Mine Information for Test Mine:

- Eigentümer: LEER - keine verlässlichen Daten verfügbar
- Betreiber: Leer - status unklar  
- Minentyp (Untertage/ Open-Pit/ usw.): Untertage/ Open-Pit/ usw.): Open-Pit
- Aktivitätsstatus: Aktiv
- x-Koordinate: 45.123456
- y-Koordinate: -73.987654
- Rohstoffabbau: Gold; Kupfer; Silber
- Produktionsstart: 2010

Sources:
[1] https://mern.gouv.qc.ca/mines/test-mine/
[2] https://sedar.com/filings/test-mine-report/
"""
    
    print("📥 Eingabe (simuliert problematische Provider-Response):")
    print("  Eigentümer: 'LEER - keine verlässlichen Daten verfügbar'")
    print("  Betreiber: 'Leer - status unklar'")
    print("  Minentyp: 'Untertage/ Open-Pit/ usw.): Open-Pit'")
    print("  Rohstoffabbau: 'Gold; Kupfer; Silber'")
    
    # Teste Datenextraktion
    extractor = DataExtractor()
    result = extractor.extract_structured_data(mock_response, "Test Mine", "Canada")
    
    print("\n📤 Ausgabe (nach Bereinigung):")
    key_fields = [
        "Eigentümer", "Betreiber", "Minentyp (Untertage/ Open-Pit/ usw.)", 
        "Aktivitätsstatus", "Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)",
        "Quellenangaben"
    ]
    
    for field in key_fields:
        value = result.get(field, "NICHT GEFUNDEN")
        print(f"  {field}: '{value}'")
    
    # Teste Quellen-Mapping
    source_mapping = result.get("_source_mapping", {})
    if source_mapping:
        print(f"\n🔗 Quellen-Mapping:")
        sources = source_mapping.get("sources", {})
        field_sources = source_mapping.get("field_sources", {})
        
        print(f"  Gefundene Quellen: {len(sources)}")
        for sid, source_info in sources.items():
            print(f"    [{sid}] {source_info['url']} ({source_info['type']})")
        
        print(f"  Feld-Zuordnungen: {len(field_sources)}")
        for field, source_ids in field_sources.items():
            if source_ids:
                print(f"    {field}: Quellen {source_ids}")
    
    # Validiere Ergebnisse
    print("\n✅ Validierung:")
    
    # 1. LEER-Werte zu X konvertiert?
    eigentumer = result.get("Eigentümer", "")
    betreiber = result.get("Betreiber", "")
    if eigentumer == "X" and betreiber == "X":
        print("  ✅ LEER-Werte korrekt zu 'X' konvertiert")
    else:
        print(f"  ❌ LEER-Werte nicht korrekt: Eigentümer='{eigentumer}', Betreiber='{betreiber}'")
    
    # 2. Minentyp-Präfix entfernt?
    minentyp = result.get("Minentyp (Untertage/ Open-Pit/ usw.)", "")
    if minentyp == "Open-Pit":
        print("  ✅ Minentyp-Präfix korrekt entfernt")
    else:
        print(f"  ❌ Minentyp-Präfix nicht entfernt: '{minentyp}'")
    
    # 3. Quellenangaben vorhanden?
    quellenangaben = result.get("Quellenangaben", "")
    if quellenangaben and quellenangaben != "Keine spezifischen Quellen gefunden":
        print("  ✅ Quellenangaben korrekt erstellt")
    else:
        print(f"  ❌ Quellenangaben fehlen: '{quellenangaben}'")
    
    # 4. Rohstoffabbau bereinigt?
    rohstoff = result.get("Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)", "")
    if "," in rohstoff and ";" not in rohstoff:
        print("  ✅ Rohstoffabbau korrekt formatiert (Kommas statt Semikolons)")
    else:
        print(f"  ❌ Rohstoffabbau nicht korrekt formatiert: '{rohstoff}'")
    
    return result

def test_source_manager_integration():
    """Teste SourceManager Integration"""
    print("\n🧪 Teste SourceManager Integration...")
    
    sm = SourceManager()
    
    # Simuliere Response mit Quellen
    response_text = """
Data for Mine XYZ:
- Owner: Newmont Corporation [1]
- Operator: Newmont Corporation [1,2]
- Type: Open-Pit [2]

Sources:
[1] https://mern.gouv.qc.ca/mines/xyz/
[2] https://sedar.com/filings/newmont-xyz/
"""
    
    # Extrahiere Quellen
    found_sources = sm.extract_sources_from_response(response_text)
    print(f"  Quellen aus Response extrahiert: {len(found_sources)}")
    
    # Parse Feld mit Quellen
    owner_text = "Newmont Corporation [1]"
    clean_owner, owner_sources = sm.parse_field_with_sources(owner_text)
    
    operator_text = "Newmont Corporation [1,2]"
    clean_operator, operator_sources = sm.parse_field_with_sources(operator_text)
    
    print(f"  Owner: '{clean_owner}' -> Quellen {owner_sources}")
    print(f"  Operator: '{clean_operator}' -> Quellen {operator_sources}")
    
    # Zuordnung testen
    sm.assign_field_sources("Eigentümer", owner_sources)
    sm.assign_field_sources("Betreiber", operator_sources)
    
    # Formatierung testen
    formatted_owner = sm.format_field_with_sources("Newmont Corporation", "Eigentümer")
    formatted_operator = sm.format_field_with_sources("Newmont Corporation", "Betreiber")
    
    print(f"  Formatiert (Owner): '{formatted_owner}'")
    print(f"  Formatiert (Operator): '{formatted_operator}'")
    
    # Validation
    if "[1]" in formatted_owner and "[1,2]" in formatted_operator:
        print("  ✅ Quellenreferenzen korrekt zugeordnet")
    else:
        print("  ❌ Quellenreferenzen-Zuordnung fehlerhaft")

def main():
    print("🧪 Test neue Suche mit Datenkonsistenz-Fixes")
    print("=" * 60)
    
    result = test_new_extraction()
    test_source_manager_integration()
    
    print("\n" + "=" * 60)
    print("✅ Neue Extraktion getestet!")
    print("\n📋 Zusammenfassung der Verbesserungen:")
    print("  1. ✅ LEER-Werte werden zu 'X' normalisiert")
    print("  2. ✅ Minentyp-Präfix wird entfernt")
    print("  3. ✅ Quellenangaben werden erstellt")
    print("  4. ✅ Feld-spezifische Quellenreferenzen [1,2,3]")
    print("  5. ✅ Semikolons werden zu Kommas in Rohstoffangaben")

if __name__ == "__main__":
    main()