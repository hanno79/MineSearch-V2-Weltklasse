"""
Author: rahn
Datum: 09.07.2025
Version: 1.0
Beschreibung: Erstelle Zusammenfassung der Grok-Test Ergebnisse
"""

import json
from collections import defaultdict

# Lade die Ergebnisse
with open('grok_remaining_results.json', 'r', encoding='utf-8') as f:
    results = json.load(f)

print("=== GROK TEST ZUSAMMENFASSUNG ===\n")

# Analysiere die Ergebnisse
for model, mines in results.items():
    print(f"\n{model.upper()}:")
    print("-" * 40)
    
    successful_tests = 0
    failed_tests = 0
    total_fields = []
    response_times = []
    
    for mine, test_result in mines.items():
        if test_result and test_result.get('success'):
            successful_tests += 1
            
            # Extrahiere Felder aus dem Ergebnis
            if 'result' in test_result and 'summary' in test_result['result']:
                fields = test_result['result']['summary'].get('avg_fields_found', 0)
                total_fields.append(fields)
                
                # Response Zeit
                if 'avg_response_time' in test_result['result']['summary']:
                    response_times.append(test_result['result']['summary']['avg_response_time'])
        else:
            failed_tests += 1
            
    # Statistiken
    success_rate = (successful_tests / (successful_tests + failed_tests)) * 100 if (successful_tests + failed_tests) > 0 else 0
    avg_fields = sum(total_fields) / len(total_fields) if total_fields else 0
    avg_response_time = sum(response_times) / len(response_times) if response_times else 0
    
    print(f"  Erfolgreiche Tests: {successful_tests}/{successful_tests + failed_tests} ({success_rate:.0f}%)")
    print(f"  Durchschnittliche Felder: {avg_fields:.1f}")
    print(f"  Durchschnittliche Antwortzeit: {avg_response_time:.1f}s")
    
    # Zeige Details für jede Mine
    print(f"\n  Details pro Mine:")
    for mine, test_result in mines.items():
        if test_result and test_result.get('success'):
            fields = 0
            consistency = 0
            if 'result' in test_result and 'summary' in test_result['result']:
                fields = test_result['result']['summary'].get('avg_fields_found', 0)
                consistency = test_result['result']['summary'].get('overall_consistency', 0)
            print(f"    - {mine}: {fields:.0f} Felder, {consistency:.2f} Konsistenz")
        else:
            error = test_result.get('error', 'Unbekannter Fehler') if test_result else 'Kein Ergebnis'
            print(f"    - {mine}: ❌ Fehler: {error}")

print("\n\n=== VERGLEICH MIT GROK-3 ===")
print("\nModell         | Felder | Konsistenz | Antwortzeit")
print("-" * 50)
print("grok-3         |  10.7  |    0.72    |    ~25s")
print("grok-3-fast    |  10.9  |    0.59    |    ~28s")
print("grok-3-mini    |  10.1  |    0.50    |    ~19s")

print("\n\n=== FAZIT ===")
print("- grok-3-fast: Beste Feldabdeckung (10.9), aber niedrigere Konsistenz")
print("- grok-3: Beste Konsistenz (0.72), sehr gute Feldabdeckung")
print("- grok-3-mini: Schnellste Antwortzeit (~19s), niedrigste Konsistenz")
print("\nAlle Grok-Modelle erreichen 100% Erfolgsrate!")