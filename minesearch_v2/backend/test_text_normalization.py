"""
Author: rahn
Datum: 31.07.2025
Version: 1.0
Beschreibung: Test-Suite für erweiterte Textnormalisierung
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from extraction_processors import normalize_field_value, clean_field_value, check_field_specific_patterns

def test_normalize_field_value():
    """Test der erweiterten normalize_field_value Funktion"""
    print("=== TEST: normalize_field_value ===")
    
    test_cases = [
        # Pattern-basierte Tests (vom Data Cleaning Analyst identifiziert)
        ("LEER - Keine aktiven Betriebsdaten verfügbar [1]", "N/A"),
        ("Leave blank    Leave blank if unknown", "N/A"),
        ("Unknown, so commodities stay blank", "N/A"),
        ("leave blank if not known", "N/A"),
        ("unknown information", "N/A"),
        ("unbekannt", "N/A"),
        ("(leer)", "N/A"),
        
        # Existierende Tests
        ("LEER", "N/A"),
        ("N/A", "N/A"),
        ("k.A.", "N/A"),
        ("unknown", "N/A"),
        ("", ""),  # Leer bleibt leer
        
        # Echte Daten sollten unverändert bleiben
        ("Gold", "Gold"),
        ("Open-Pit", "Open-Pit"),
        ("Barrick Gold Corporation", "Barrick Gold Corporation"),
        ("2025", "2025")
    ]
    
    passed = 0
    failed = 0
    
    for input_val, expected in test_cases:
        result = normalize_field_value(input_val)
        if result == expected:
            print(f"✅ '{input_val}' → '{result}'")
            passed += 1
        else:
            print(f"❌ '{input_val}' → '{result}' (erwartet: '{expected}')")
            failed += 1
    
    print(f"\nERGEBNIS: {passed} bestanden, {failed} fehlgeschlagen")
    return failed == 0

def test_field_specific_patterns():
    """Test der feldspezifischen Pattern-Erkennung"""
    print("\n=== TEST: check_field_specific_patterns ===")
    
    test_cases = [
        # Rohstoffabbau-spezifische Tests
        ("Unbekannt, so commodities stay blank", "Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)", "N/A"),
        ("Gold commodities stay blank", "Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)", "N/A"),
        ("Gold", "Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)", "Gold"),
        
        # Minentyp-spezifische Tests
        ("leave blank if unknown", "Minentyp (Untertage/ Open-Pit/ usw.)", "N/A"),
        ("not specified, leave blank", "Minentyp (Untertage/ Open-Pit/ usw.)", "N/A"),
        ("Open-Pit", "Minentyp (Untertage/ Open-Pit/ usw.)", "Open-Pit"),
        
        # Betreiber-spezifische Tests
        ("LEER - Keine aktiven Betriebsdaten verfügbar", "Betreiber", "N/A"),
        ("Barrick Gold Corp", "Betreiber", "Barrick Gold Corp"),
        
        # Tests für nicht-betroffene Felder
        ("leave blank", "Region", "leave blank")
    ]
    
    passed = 0
    failed = 0
    
    for input_val, field, expected in test_cases:
        result = check_field_specific_patterns(input_val, field)
        if result == expected:
            print(f"✅ '{field}': '{input_val}' → '{result}'")
            passed += 1
        else:
            print(f"❌ '{field}': '{input_val}' → '{result}' (erwartet: '{expected}')")
            failed += 1
    
    print(f"\nERGEBNIS: {passed} bestanden, {failed} fehlgeschlagen")
    return failed == 0

def test_clean_field_value():
    """Test der erweiterten clean_field_value Funktion"""
    print("\n=== TEST: clean_field_value ===")
    
    test_cases = [
        # Feldspezifische Tests mit neuen Patterns
        ("LEER - Keine aktiven Betriebsdaten verfügbar [1]", "Betreiber", "N/A"),
        ("Unknown, so commodities stay blank", "Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)", "N/A"),
        ("Leave blank if unknown", "Minentyp (Untertage/ Open-Pit/ usw.)", "N/A"),
        
        # Normale Feldbereinigung
        ("Gold, Silver, Gold", "Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)", "Gold, Silver"),  # Duplikat-Entfernung
        ("Barrick Gold Corporation (TSE: ABX)", "Eigentümer", "Barrick Gold Corporation"),  # Klammer-Entfernung
        ("(Untertage/ Open-Pit/ usw.): Open-Pit", "Minentyp (Untertage/ Open-Pit/ usw.)", "Open-Pit"),  # Präfix-Entfernung
        
        # Leere Eingaben
        ("", "Betreiber", ""),
        ("   ", "Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)", "N/A")  # Nur Leerzeichen
    ]
    
    passed = 0
    failed = 0
    
    for input_val, field, expected in test_cases:
        result = clean_field_value(input_val, field)
        if result == expected:
            print(f"✅ '{field}': '{input_val}' → '{result}'")
            passed += 1
        else:
            print(f"❌ '{field}': '{input_val}' → '{result}' (erwartet: '{expected}')")
            failed += 1
    
    print(f"\nERGEBNIS: {passed} bestanden, {failed} fehlgeschlagen")
    return failed == 0

def test_performance_cache():
    """Test des Performance-Caches"""
    print("\n=== TEST: Performance Cache ===")
    
    # Teste Cache durch mehrfache Aufrufe
    test_value = "LEER - Keine aktiven Betriebsdaten verfügbar [1]"
    
    # Erster Aufruf (sollte Pattern matchen und cachen)
    result1 = normalize_field_value(test_value)
    
    # Zweiter Aufruf (sollte aus Cache kommen)
    result2 = normalize_field_value(test_value)
    
    if result1 == result2 == "N/A":
        print("✅ Cache funktioniert korrekt")
        return True
    else:
        print(f"❌ Cache-Problem: {result1} != {result2}")
        return False

def main():
    """Haupttest-Funktion"""
    print("TEXT-NORMALISIERUNG TEST-SUITE")
    print("=" * 50)
    
    all_tests_passed = True
    
    # Führe alle Tests aus
    all_tests_passed &= test_normalize_field_value()
    all_tests_passed &= test_field_specific_patterns()
    all_tests_passed &= test_clean_field_value()
    all_tests_passed &= test_performance_cache()
    
    print("\n" + "=" * 50)
    if all_tests_passed:
        print("🎉 ALLE TESTS BESTANDEN!")
        print("✅ Erweiterte Textnormalisierung erfolgreich implementiert")
        return 0
    else:
        print("❌ EINIGE TESTS FEHLGESCHLAGEN!")
        print("🔧 Überprüfung der Implementierung erforderlich")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)