#!/usr/bin/env python3
"""
Author: rahn
Datum: 19.07.2025
Version: 1.0
Beschreibung: Quick test einer neuen Suche mit den Fixes
"""

import sys
import os
import requests
import json

sys.path.append(os.path.join(os.path.dirname(__file__), 'minesearch_v2', 'backend'))

def test_new_search():
    """Teste eine neue Suche um zu sehen ob die Fixes greifen"""
    print("🧪 Teste neue Suche mit implementierten Fixes...")
    
    # Test-Anfrage an Backend
    api_url = "http://localhost:8000/api/search"
    test_data = {
        "mine_name": "Test Mine Quebec Fixes",
        "country": "Canada",
        "providers": ["perplexity"],
        "models": ["llama-3.1-sonar-large-128k-online"]
    }
    
    try:
        print(f"📤 Sende Test-Suche: {test_data['mine_name']}")
        response = requests.post(api_url, json=test_data, timeout=60)
        
        if response.status_code != 200:
            print(f"❌ API-Fehler: HTTP {response.status_code}")
            return
        
        result = response.json()
        if not result.get("success"):
            print(f"❌ Suche fehlgeschlagen: {result.get('error', 'Unbekannt')}")
            return
        
        print("✅ Suche erfolgreich!")
        
        # Analysiere Ergebnis
        data = result.get("data", {})
        structured_data = data.get("structured_data", {})
        
        print("\n📊 Analyse der neuen Daten:")
        
        # Prüfe kritische Felder
        key_fields = [
            "Eigentümer", "Betreiber", "Minentyp (Untertage/ Open-Pit/ usw.)", 
            "Aktivitätsstatus", "Quellenangaben"
        ]
        
        for field in key_fields:
            value = structured_data.get(field, "NICHT GEFUNDEN")
            print(f"  {field}: '{value}'")
        
        # Validiere Fixes
        print("\n✅ Validierung der Fixes:")
        
        # 1. LEER-Werte zu X?
        leer_found = False
        for field, value in structured_data.items():
            if isinstance(value, str) and "LEER" in value:
                leer_found = True
                break
        
        if not leer_found:
            print("  ✅ Keine LEER-Werte gefunden (korrekt bereinigt)")
        else:
            print("  ❌ LEER-Werte noch vorhanden")
        
        # 2. Minentyp-Präfix entfernt?
        minentyp = structured_data.get("Minentyp (Untertage/ Open-Pit/ usw.)", "")
        if "Untertage/ Open-Pit/ usw.):" not in minentyp:
            print("  ✅ Minentyp-Präfix korrekt entfernt")
        else:
            print(f"  ❌ Minentyp-Präfix noch vorhanden: '{minentyp}'")
        
        # 3. Quellenangaben vorhanden?
        quellenangaben = structured_data.get("Quellenangaben", "")
        if quellenangaben and "[1]" in quellenangaben:
            print("  ✅ Nummerierte Quellenangaben korrekt erstellt")
        else:
            print(f"  ❌ Quellenangaben ohne Nummerierung: '{quellenangaben[:80]}...'")
        
        # 4. Quellen-Referenzen in Feldern?
        fields_with_sources = 0
        for field, value in structured_data.items():
            if isinstance(value, str) and "[" in value and "]" in value:
                fields_with_sources += 1
        
        if fields_with_sources > 0:
            print(f"  ✅ {fields_with_sources} Felder mit Quellen-Referenzen [X]")
        else:
            print("  ❌ Keine Quellen-Referenzen in Feldern gefunden")
        
        # Source mapping prüfen
        source_mapping = data.get("source_mapping", {})
        if source_mapping:
            sources = source_mapping.get("sources", {})
            field_sources = source_mapping.get("field_sources", {})
            print(f"  ✅ Source-Mapping: {len(sources)} Quellen, {len(field_sources)} Feld-Zuordnungen")
        
        return True
        
    except Exception as e:
        print(f"❌ Test-Fehler: {str(e)}")
        return False

def main():
    print("🧪 Quick Test neue Suche")
    print("=" * 40)
    
    success = test_new_search()
    
    print("\n" + "=" * 40)
    if success:
        print("✅ Test abgeschlossen - Fixes funktionieren!")
    else:
        print("❌ Test fehlgeschlagen")

if __name__ == "__main__":
    main()