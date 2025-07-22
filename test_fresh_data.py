#!/usr/bin/env python3
"""
Author: rahn
Datum: 19.07.2025
Version: 1.0
Beschreibung: Test der Datenkonsistenz-Fixes mit frischen Daten nach DB-Clear
"""

import requests
import json
import time
import sys

API_BASE = "http://localhost:8002"

def test_search_with_fixes(mine_name, country="Canada"):
    """Führe eine neue Suche durch und prüfe die Datenqualität"""
    print(f"🔍 Teste Suche für: {mine_name}")
    
    # Suche durchführen
    search_data = {
        "mine_name": mine_name,
        "country": country,
        "providers": ["perplexity"],  # Verwende bekannten Provider
        "models": ["llama-3.1-sonar-large-128k-online"]
    }
    
    try:
        print(f"  📤 Sende Suchanfrage...")
        response = requests.post(f"{API_BASE}/api/search", json=search_data, timeout=120)
        
        if response.status_code != 200:
            print(f"  ❌ API-Fehler: HTTP {response.status_code}")
            if response.status_code == 500:
                try:
                    error_data = response.json()
                    print(f"     Fehler-Details: {error_data.get('error', 'Unbekannt')}")
                except:
                    print(f"     Server-Antwort: {response.text[:200]}...")
            return None
        
        result = response.json()
        if not result.get("success"):
            print(f"  ❌ Suche fehlgeschlagen: {result.get('error', 'Unbekannt')}")
            return None
        
        print(f"  ✅ Suche erfolgreich!")
        return result.get("data", {})
        
    except requests.exceptions.Timeout:
        print(f"  ⏱️ Timeout - Suche dauert zu lange")
        return None
    except Exception as e:
        print(f"  ❌ Fehler: {str(e)}")
        return None

def analyze_data_quality(mine_name, data):
    """Analysiere die Datenqualität der Suchergebnisse"""
    print(f"\n📊 Datenqualität-Analyse für {mine_name}:")
    print("-" * 50)
    
    structured_data = data.get("structured_data", {})
    if not structured_data:
        print("  ❌ Keine strukturierten Daten gefunden")
        return
    
    # Analysiere kritische Felder
    issues = []
    improvements = []
    
    # 1. Prüfe auf LEER-Werte
    leer_fields = []
    for field, value in structured_data.items():
        if isinstance(value, str) and "LEER" in value.upper():
            leer_fields.append((field, value))
    
    if leer_fields:
        print("  ❌ LEER-Werte gefunden (sollten X sein):")
        for field, value in leer_fields[:3]:
            print(f"     {field}: '{value}'")
        issues.append("LEER-Werte nicht konvertiert")
    else:
        print("  ✅ Keine LEER-Werte gefunden (korrekt bereinigt)")
        improvements.append("LEER-Normalisierung erfolgreich")
    
    # 2. Prüfe Minentyp-Präfix
    minentyp = structured_data.get("Minentyp (Untertage/ Open-Pit/ usw.)", "")
    if "Untertage/ Open-Pit/ usw.):" in minentyp:
        print(f"  ❌ Minentyp-Präfix vorhanden: '{minentyp}'")
        issues.append("Minentyp-Präfix nicht entfernt")
    else:
        print(f"  ✅ Minentyp sauber: '{minentyp}'")
        improvements.append("Minentyp-Präfix erfolgreich entfernt")
    
    # 3. Prüfe Quellenangaben
    quellenangaben = structured_data.get("Quellenangaben", "")
    if not quellenangaben or quellenangaben == "Keine spezifischen Quellen gefunden":
        print(f"  ⚠️ Quellenangaben leer oder Standard: '{quellenangaben}'")
        issues.append("Quellenangaben nicht generiert")
    elif "[1]" in quellenangaben or "[2]" in quellenangaben:
        print(f"  ✅ Nummerierte Quellenangaben: '{quellenangaben[:80]}...'")
        improvements.append("Strukturierte Quellenangaben erstellt")
    else:
        print(f"  ⚠️ Quellenangaben ohne Nummerierung: '{quellenangaben[:80]}...'")
    
    # 4. Prüfe Quellen-Referenzen in Feldern
    fields_with_refs = 0
    for field, value in structured_data.items():
        if isinstance(value, str) and "[" in value and "]" in value and value != "X":
            fields_with_refs += 1
    
    if fields_with_refs > 0:
        print(f"  ✅ {fields_with_refs} Felder mit Quellen-Referenzen [X]")
        improvements.append(f"Quellen-Referenzen in {fields_with_refs} Feldern")
    else:
        print(f"  ⚠️ Keine Quellen-Referenzen in Feldern gefunden")
    
    # 5. Zeige einige Beispiel-Felder
    print(f"\n📋 Beispiel-Felder:")
    key_fields = ["Eigentümer", "Betreiber", "Aktivitätsstatus", "Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)"]
    for field in key_fields:
        value = structured_data.get(field, "N/A")
        print(f"  {field}: '{value}'")
    
    # Source Mapping prüfen
    source_mapping = data.get("source_mapping", {})
    if source_mapping and source_mapping.get("sources"):
        sources_count = len(source_mapping["sources"])
        field_mappings = len(source_mapping.get("field_sources", {}))
        print(f"\n🔗 Source-Mapping: {sources_count} Quellen, {field_mappings} Feld-Zuordnungen")
        improvements.append(f"Source-Mapping mit {sources_count} Quellen")
    
    # Zusammenfassung
    print(f"\n📈 Qualitäts-Zusammenfassung:")
    print(f"  ✅ Verbesserungen: {len(improvements)}")
    for improvement in improvements[:3]:
        print(f"     • {improvement}")
    
    if issues:
        print(f"  ❌ Probleme: {len(issues)}")
        for issue in issues[:3]:
            print(f"     • {issue}")
    else:
        print(f"  🎯 Alle Datenqualitäts-Checks bestanden!")
    
    return len(issues) == 0

def main():
    print("🧪 Test frischer Daten nach Datenkonsistenz-Fixes")
    print("=" * 60)
    
    # Liste der zu testenden Minen (die zuvor Probleme hatten)
    test_mines = [
        "Denain",
        "Evans Cameron", 
        "Barry"
    ]
    
    successful_tests = 0
    failed_tests = 0
    
    for mine_name in test_mines:
        print(f"\n{'='*60}")
        
        # Führe Suche durch
        data = test_search_with_fixes(mine_name)
        
        if data:
            # Analysiere Datenqualität
            quality_ok = analyze_data_quality(mine_name, data)
            if quality_ok:
                successful_tests += 1
            else:
                failed_tests += 1
            
            # Kurze Pause zwischen Tests
            time.sleep(2)
        else:
            failed_tests += 1
            print(f"  ❌ Suche für {mine_name} fehlgeschlagen")
    
    # Gesamt-Zusammenfassung
    print(f"\n{'='*60}")
    print(f"📊 GESAMT-ERGEBNIS")
    print(f"✅ Erfolgreiche Tests: {successful_tests}")
    print(f"❌ Fehlgeschlagene Tests: {failed_tests}")
    
    if successful_tests > 0:
        print(f"\n🎯 Die Datenkonsistenz-Fixes funktionieren bei {successful_tests} von {len(test_mines)} Tests!")
    
    if failed_tests == 0:
        print(f"🏆 ALLE TESTS BESTANDEN - Fixes vollständig erfolgreich!")
    else:
        print(f"⚠️ {failed_tests} Tests benötigen weitere Aufmerksamkeit")

if __name__ == "__main__":
    main()