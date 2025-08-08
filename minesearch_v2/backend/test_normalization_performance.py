#!/usr/bin/env python3
"""
Author: rahn
Datum: 31.07.2025
Version: 1.0
Beschreibung: Performance-Test für erweiterte Textbereinigung
"""

from extraction_processors import normalize_field_value, check_field_specific_patterns
import time

# Test-Daten aus echten problematischen API-Responses
test_cases = [
    # Bereits bereinigt (soll N/A werden)
    "LEER - Keine aktiven Betriebsdaten verfügbar [1]",
    "LEER (Junior-Explorationsunternehmen, nicht öffentlich identifiziert)",
    "(leer)",
    
    # Lange AI-Unsicherheits-Texte (sollen N/A werden)
    "companies like Osisko or IAMGOLD, but I'm not sure about this one. If I can't recall, I should leave it blank rather than guess",
    "Gold als wahrscheinlichster Rohstoff basierend auf Quebecs Bergbaustruktur, aber unsicher",
    "Ohne NI 43-101-Berichte oder GESTIM-Einträge bleibt der Rohstoff unklar",
    "Technische Projektbeschreibungen (Seltene Erden)",
    
    # Kurze gültige Werte (sollen bleiben)
    "Aktiv",
    "Osisko Development Corp",
    "Quebec",
    "Untertage",
    "noch aktiv",
    "25.000000"
]

print("=== NORMALISIERUNGS-PERFORMANCE-TEST ===")
print(f"Testing {len(test_cases)} cases...")

start_time = time.time()

for i, test_value in enumerate(test_cases, 1):
    original_value = test_value
    
    # Step 1: Basis-Normalisierung
    normalized = normalize_field_value(test_value)
    
    # Step 2: Feldspezifische Prüfung (Beispiel-Feld)
    final_value = check_field_specific_patterns(normalized, "Eigentümer")
    
    print(f"{i:2d}. '{original_value[:60]}{'...' if len(original_value) > 60 else ''}' -> '{final_value}'")

end_time = time.time()
processing_time = (end_time - start_time) * 1000  # in ms

print(f"\n📊 Performance: {processing_time:.2f}ms für {len(test_cases)} Werte")
print(f"📊 Durchschnitt: {processing_time/len(test_cases):.2f}ms pro Wert")

# Erwartete Resultate validieren
expected_na_count = sum(1 for case in test_cases if any(keyword in case.lower() for keyword in [
    'leer', 'not sure', 'unsure', 'wahrscheinlichste', 'aber unsicher', 'bleibt unklar', "can't recall"
]))

actual_na_count = sum(1 for case in test_cases if normalize_field_value(case) == 'N/A')

print(f"\n✅ Erwartete N/A-Bereinigungen: {expected_na_count}")
print(f"✅ Tatsächliche N/A-Bereinigungen: {actual_na_count}")
print(f"{'✅ BESTANDEN' if actual_na_count >= expected_na_count - 1 else '❌ FEHLER'}")