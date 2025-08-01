#!/usr/bin/env python3
"""
Author: rahn
Datum: 01.08.2025
Version: 1.0
Beschreibung: Validierung der Field-Order-Fixes für Enhanced Details Modal
"""

import json
import re

def validate_field_order_consistency():
    """Validiere dass Frontend und Backend die gleiche Feldreihenfolge verwenden"""
    
    print("🔍 VALIDIERUNG: Field-Order-Consistency zwischen Backend und Frontend")
    print("=" * 70)
    
    # 1. Backend FIELD_ORDER lesen
    backend_file = "minesearch_v2/backend/api/routes/consolidated_results.py"
    with open(backend_file, 'r', encoding='utf-8') as f:
        backend_content = f.read()
    
    # Extrahiere FIELD_ORDER aus Backend
    field_order_match = re.search(r'FIELD_ORDER = \[(.*?)\]', backend_content, re.DOTALL)
    if field_order_match:
        field_order_str = field_order_match.group(1)
        # Parse die Felder mit besserer Regex
        backend_fields = re.findall(r"'([^']+)'", field_order_str)
        
        print(f"✅ Backend FIELD_ORDER gefunden: {len(backend_fields)} Felder")
        print(f"   Beispiele: {backend_fields[:5]}...")
    else:
        print("❌ Backend FIELD_ORDER nicht gefunden")
        return False
    
    # 2. Frontend mainTableFieldOrder aus results-display.js lesen
    frontend_file = "minesearch_v2/frontend/js/results-display.js"
    with open(frontend_file, 'r', encoding='utf-8') as f:
        frontend_content = f.read()
    
    # Extrahiere mainTableFieldOrder
    frontend_order_match = re.search(r'const mainTableFieldOrder = \[(.*?)\];', frontend_content, re.DOTALL)
    if frontend_order_match:
        order_str = frontend_order_match.group(1)
        # Filtere nur echte Array-Elemente (mit Komma nach dem Anführungszeichen)
        frontend_fields = re.findall(r"'([^']+)'(?:\s*,|\s*$)", order_str)
        
        print(f"✅ Frontend results-display.js mainTableFieldOrder gefunden: {len(frontend_fields)} Felder")
        print(f"   Beispiele: {frontend_fields[:5]}...")
    else:
        print("❌ Frontend results-display.js mainTableFieldOrder nicht gefunden")
        return False
    
    # 3. Frontend mainTableFieldOrder aus index.html lesen
    index_file = "minesearch_v2/frontend/index.html"
    with open(index_file, 'r', encoding='utf-8') as f:
        index_content = f.read()
    
    # Extrahiere mainTableFieldOrder aus index.html
    index_order_match = re.search(r'const mainTableFieldOrder = \[(.*?)\];', index_content, re.DOTALL)
    if index_order_match:
        order_str = index_order_match.group(1)
        # Filtere nur echte Array-Elemente (mit Komma nach dem Anführungszeichen)
        index_fields = re.findall(r"'([^']+)'(?:\s*,|\s*$)", order_str)
        
        print(f"✅ Frontend index.html mainTableFieldOrder gefunden: {len(index_fields)} Felder")
        print(f"   Beispiele: {index_fields[:5]}...")
    else:
        print("❌ Frontend index.html mainTableFieldOrder nicht gefunden")
        return False
    
    # 4. Validierung der Konsistenz
    print("\n🔍 KONSISTENZ-ANALYSE:")
    print("-" * 50)
    
    # Backend-Felder ohne Meta-Felder (die im Frontend nicht im Details-Modal erscheinen)
    meta_fields = ['Mine', 'Land', 'Region', 'Modelle', 'Letzte Aktualisierung', 'Details']
    backend_data_fields = [f for f in backend_fields if f not in meta_fields]
    
    print(f"Backend Data-Felder (ohne Meta): {len(backend_data_fields)}")
    print(f"Frontend results-display.js: {len(frontend_fields)}")
    print(f"Frontend index.html: {len(index_fields)}")
    
    # Prüfe ob Frontend-Arrays identisch sind
    frontend_consistency = frontend_fields == index_fields
    print(f"✅ Frontend-Dateien konsistent: {frontend_consistency}")
    
    # Prüfe ob Frontend mit Backend-Data-Feldern übereinstimmt
    backend_frontend_consistency = backend_data_fields == frontend_fields
    print(f"✅ Backend-Frontend konsistent: {backend_frontend_consistency}")
    
    if not backend_frontend_consistency:
        print("\n❌ INKONSISTENZ ERKANNT:")
        print("Backend Data-Felder:", backend_data_fields)
        print("Frontend Felder:      ", frontend_fields)
        
        # Finde Unterschiede
        backend_set = set(backend_data_fields)
        frontend_set = set(frontend_fields)
        
        missing_in_frontend = backend_set - frontend_set
        extra_in_frontend = frontend_set - backend_set
        
        if missing_in_frontend:
            print(f"❌ Fehlen im Frontend: {missing_in_frontend}")
        if extra_in_frontend:
            print(f"❌ Extra im Frontend: {extra_in_frontend}")
    
    # 5. Prüfe _source_mapping Exclusion
    print("\n🔍 FIELD-EXCLUSION-ANALYSE:")
    print("-" * 50)
    
    # Prüfe results-display.js excludedDetailFields
    excluded_match = re.search(r'const excludedDetailFields = \[(.*?)\];', frontend_content, re.DOTALL)
    if excluded_match:
        excluded_str = excluded_match.group(1)
        excluded_fields = re.findall(r"'([^']+)'", excluded_str)
        
        has_source_mapping_exclusion = '_source_mapping' in excluded_fields
        print(f"✅ results-display.js excludedDetailFields: {len(excluded_fields)} Felder")
        print(f"✅ _source_mapping ausgeschlossen: {has_source_mapping_exclusion}")
    
    # Prüfe index.html excludedFields
    index_excluded_match = re.search(r'const excludedFields = \[(.*?)\];', index_content, re.DOTALL)
    if index_excluded_match:
        excluded_str = index_excluded_match.group(1)
        index_excluded_fields = re.findall(r"'([^']+)'", excluded_str)
        
        has_source_mapping_exclusion_index = '_source_mapping' in index_excluded_fields
        print(f"✅ index.html excludedFields: {len(index_excluded_fields)} Felder")
        print(f"✅ _source_mapping ausgeschlossen: {has_source_mapping_exclusion_index}")
    
    # 6. Gesamtbewertung
    print("\n🎯 GESAMTBEWERTUNG:")
    print("=" * 70)
    
    all_checks_passed = (
        frontend_consistency and 
        backend_frontend_consistency and
        has_source_mapping_exclusion and
        has_source_mapping_exclusion_index
    )
    
    if all_checks_passed:
        print("✅ ALLE VALIDIERUNGEN BESTANDEN!")
        print("   - Frontend-Dateien sind konsistent")
        print("   - Backend-Frontend Feldreihenfolge stimmt überein")
        print("   - _source_mapping wird korrekt ausgeschlossen")
        print("   - Enhanced Details Modal wird korrekte Reihenfolge anzeigen")
    else:
        print("❌ VALIDIERUNG FEHLGESCHLAGEN!")
        print("   Bitte Inkonsistenzen beheben bevor das System produktiv geht")
    
    return all_checks_passed

if __name__ == "__main__":
    validate_field_order_consistency()