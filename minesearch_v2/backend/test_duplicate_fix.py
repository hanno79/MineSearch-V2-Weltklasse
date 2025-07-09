"""
Author: rahn
Datum: 09.07.2025
Version: 1.0
Beschreibung: Test der Duplicate-Fix Änderungen
"""

import time
import requests
from concurrent.futures import ThreadPoolExecutor

print("=== TEST DER DUPLICATE-FIX ÄNDERUNGEN ===\n")

# 1. Test mehrfacher paralleler Aufrufe
print("1. Test: Mehrfache parallele Aufrufe des Sources-Tab")

def load_sources():
    try:
        response = requests.get("http://localhost:8000/api/sources?limit=20")
        data = response.json()
        return len(data['data']['sources']) if data['success'] else 0
    except Exception as e:
        return f"Error: {e}"

# Simuliere 5 parallele Aufrufe
with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(load_sources) for _ in range(5)]
    results = [f.result() for f in futures]
    
print(f"Ergebnisse der parallelen Aufrufe: {results}")
print(f"Alle gleich? {len(set(results)) == 1 and all(isinstance(r, int) for r in results)}")

# 2. Test der API mit verschiedenen Filtern
print("\n2. Test: API mit verschiedenen Filtern")

test_cases = [
    {"params": "", "name": "Ohne Filter"},
    {"params": "?country=Canada", "name": "Filter: Canada"},
    {"params": "?source_type=government", "name": "Filter: Government"},
    {"params": "?min_reliability=70", "name": "Filter: Min Reliability 70"},
]

for test in test_cases:
    response = requests.get(f"http://localhost:8000/api/sources{test['params']}&limit=10")
    data = response.json()
    if data['success']:
        sources = data['data']['sources']
        print(f"\n{test['name']}:")
        print(f"  Anzahl: {len(sources)}")
        
        # Prüfe auf Duplikate in der Antwort
        urls = [s['url'] for s in sources]
        if len(urls) != len(set(urls)):
            print(f"  WARNUNG: Duplikate gefunden!")
        else:
            print(f"  ✓ Keine Duplikate")

# 3. Test der Cleanup-Funktion
print("\n3. Test: Cleanup Duplikate")
response = requests.post("http://localhost:8000/api/sources/cleanup-duplicates")
data = response.json()
if data['success']:
    print(f"Cleanup erfolgreich: {data['data']['removed']} Duplikate entfernt")
else:
    print(f"Cleanup fehlgeschlagen: {data.get('error', 'Unbekannter Fehler')}")

print("\n=== TEST ABGESCHLOSSEN ===")