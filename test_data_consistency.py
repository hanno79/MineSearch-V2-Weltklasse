#!/usr/bin/env python3
"""
Author: rahn
Datum: 19.07.2025
Version: 1.0
Beschreibung: Test-Script für Datenkonsistenz-Fixes
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'minesearch_v2', 'backend'))

from extraction_processors import normalize_field_value, clean_field_value
from source_manager import SourceManager

def test_normalize_field_value():
    """Teste die erweiterte normalize_field_value Funktion"""
    print("🧪 Teste normalize_field_value...")
    
    test_cases = [
        # Alte LEER-Varianten 
        ("LEER - keine verlässlichen Daten verfügbar", "X"),
        ("LEER - Keine verlässlichen Daten verfügbar", "X"),
        ("Leer - status unklar", "X"),
        ("LEER - Minentyp unbekannt", "X"),
        ("LEER - Typ unklar", "X"),
        # Reguläre Werte
        ("Newmont Corporation", "Newmont Corporation"),
        ("Open-Pit", "Open-Pit"),
        ("", ""),  # Leer bleibt leer
        # Alte Varianten
        ("N/A", "X"),
        ("Unbekannt", "X"),
        ("-", "X")
    ]
    
    for input_val, expected in test_cases:
        result = normalize_field_value(input_val)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{input_val}' -> '{result}' (erwartet: '{expected}')")
        
        if result != expected:
            print(f"   FEHLER: Ergebnis stimmt nicht überein!")

def test_clean_field_value():
    """Teste die erweiterte clean_field_value Funktion"""
    print("\n🧪 Teste clean_field_value für Minentyp...")
    
    test_cases = [
        # Minentyp-Bereinigung
        ("Untertage/ Open-Pit/ usw.): Untertage", "Minentyp (Untertage/ Open-Pit/ usw.)", "Untertage"),
        ("(Untertage/ Open-Pit/ usw.): Open-Pit", "Minentyp (Untertage/ Open-Pit/ usw.)", "Open-Pit"),
        ("Minentyp (Untertage/ Open-Pit/ usw.): Exploration", "Minentyp (Untertage/ Open-Pit/ usw.)", "Exploration"),
        ("Open-Pit mit großer Kapazität", "Minentyp (Untertage/ Open-Pit/ usw.)", "Open-Pit mit großer Kapazität"),
        # Andere Felder unverändert
        ("Newmont Corporation (100%)", "Eigentümer", "Newmont Corporation"),
        ("Gold, Kupfer, Silber", "Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)", "Gold, Kupfer, Silber")
    ]
    
    for input_val, field, expected in test_cases:
        result = clean_field_value(input_val, field)
        status = "✅" if result == expected else "❌"
        print(f"{status} [{field}] '{input_val}' -> '{result}' (erwartet: '{expected}')")
        
        if result != expected:
            print(f"   FEHLER: Ergebnis stimmt nicht überein!")

def test_source_manager():
    """Teste die SourceManager Klasse"""
    print("\n🧪 Teste SourceManager...")
    
    sm = SourceManager()
    
    # Test: Quellen hinzufügen
    id1 = sm.add_source("https://mern.gouv.qc.ca/mines/", "MERN Quebec", "government", 0.9)
    id2 = sm.add_source("https://sedar.com/filings/", "SEDAR Filings", "exchange", 0.8)
    id3 = sm.add_source("https://mern.gouv.qc.ca/mines/", "MERN Quebec", "government", 0.9)  # Duplikat
    
    print(f"✅ Quelle 1 ID: {id1}")
    print(f"✅ Quelle 2 ID: {id2}")
    print(f"✅ Quelle 3 ID (Duplikat): {id3} (sollte gleich wie ID 1 sein)")
    
    if id1 != id3:
        print(f"❌ FEHLER: Duplikat-Erkennung funktioniert nicht!")
    
    # Test: Feld-Zuordnung
    sm.assign_field_sources("Eigentümer", [id1, id2])
    sm.assign_field_sources("Minentyp (Untertage/ Open-Pit/ usw.)", [id1])
    
    # Test: Formatierung mit Quellen
    formatted1 = sm.format_field_with_sources("Newmont Corporation", "Eigentümer")
    formatted2 = sm.format_field_with_sources("Open-Pit", "Minentyp (Untertage/ Open-Pit/ usw.)")
    formatted3 = sm.format_field_with_sources("Gold", "Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)")
    
    print(f"✅ Formatiert (Eigentümer): '{formatted1}' (sollte [1,2] enthalten)")
    print(f"✅ Formatiert (Minentyp): '{formatted2}' (sollte [1] enthalten)")
    print(f"✅ Formatiert (Rohstoff): '{formatted3}' (sollte unverändert sein)")
    
    # Test: Quellen-Summary
    summary = sm.get_sources_summary()
    print(f"✅ Quellen-Summary erstellt ({len(summary)} Zeichen)")
    
    # Test: Parse mit Quellen
    text_with_sources = "Open-Pit [1,2] mit großer Kapazität"
    clean_text, source_ids = sm.parse_field_with_sources(text_with_sources)
    
    print(f"✅ Parse-Test: '{text_with_sources}' -> Text: '{clean_text}', Quellen: {source_ids}")
    
    if clean_text != "Open-Pit mit großer Kapazität" or source_ids != [1, 2]:
        print(f"❌ FEHLER: Parse-Funktion funktioniert nicht korrekt!")

def test_realistic_scenario():
    """Teste ein realistisches Szenario"""
    print("\n🧪 Teste realistisches Szenario...")
    
    # Simuliere problematische Eingabedaten
    problematic_data = {
        "Eigentümer": "LEER - keine verlässlichen Daten verfügbar",
        "Betreiber": "Leer - status unklar", 
        "Minentyp (Untertage/ Open-Pit/ usw.)": "Untertage/ Open-Pit/ usw.): Open-Pit",
        "Aktivitätsstatus": "Aktiv",
        "Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)": "Gold; Kupfer; Silber"
    }
    
    print("Eingabedaten (problematisch):")
    for field, value in problematic_data.items():
        print(f"  {field}: '{value}'")
    
    print("\nNach Bereinigung:")
    cleaned_data = {}
    for field, value in problematic_data.items():
        # Schritt 1: Normalisierung
        normalized = normalize_field_value(value)
        # Schritt 2: Feldspezifische Bereinigung
        cleaned = clean_field_value(normalized, field)
        cleaned_data[field] = cleaned
        
        print(f"  {field}: '{cleaned}'")
    
    # Prüfe Ergebnisse
    expected_results = {
        "Eigentümer": "X",
        "Betreiber": "X",
        "Minentyp (Untertage/ Open-Pit/ usw.)": "Open-Pit",
        "Aktivitätsstatus": "Aktiv",
        "Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)": "Gold, Kupfer, Silber"
    }
    
    all_correct = True
    for field, expected in expected_results.items():
        actual = cleaned_data[field]
        if actual != expected:
            print(f"❌ FEHLER bei {field}: Erwartet '{expected}', bekommen '{actual}'")
            all_correct = False
    
    if all_correct:
        print("✅ Alle Bereinigungen korrekt!")
    else:
        print("❌ Einige Bereinigungen fehlerhaft!")

def main():
    print("🧪 Datenkonsistenz-Tests")
    print("=" * 50)
    
    try:
        test_normalize_field_value()
        test_clean_field_value()
        test_source_manager()
        test_realistic_scenario()
        
        print("\n" + "=" * 50)
        print("✅ Alle Tests abgeschlossen!")
        
    except Exception as e:
        print(f"\n❌ FEHLER während Tests: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()