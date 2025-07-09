"""
Author: rahn
Datum: 09.07.2025
Version: 1.0
Beschreibung: Test der Sources API
"""

import requests
import json

# Test der Sources API
print("=== TEST DER SOURCES API ===\n")

# 1. Hole alle Quellen ohne Filter
response = requests.get("http://localhost:8000/api/sources?limit=20")
data = response.json()

if data['success']:
    sources = data['data']['sources']
    print(f"Anzahl erhaltene Quellen: {len(sources)}")
    print(f"Total in DB laut API: {data['data']['total']}")
    
    # Prüfe auf Duplikate
    urls = [s['url'] for s in sources]
    unique_urls = set(urls)
    
    print(f"\nAnzahl unique URLs: {len(unique_urls)}")
    if len(urls) != len(unique_urls):
        print("WARNUNG: Duplikate gefunden!")
        from collections import Counter
        duplicates = Counter(urls)
        for url, count in duplicates.items():
            if count > 1:
                print(f"  {count}x: {url}")
    else:
        print("Keine Duplikate in der API-Antwort")
    
    # Zeige erste 5 Quellen
    print("\nErste 5 Quellen:")
    for i, source in enumerate(sources[:5]):
        print(f"\n{i+1}. ID: {source['id']}")
        print(f"   URL: {source['url'][:50]}...")
        print(f"   Domain: {source['domain']}")
        print(f"   Land: {source['country']}")
        print(f"   Typ: {source['source_type']}")
        print(f"   Score: {source['reliability_score']:.1f}%")
        print(f"   Erfolgsquote: {source['success_rate']:.1f}%")

# 2. Test mit Filtern
print("\n\n=== TEST MIT FILTERN ===")
response = requests.get("http://localhost:8000/api/sources?country=Canada&limit=10")
data = response.json()

if data['success']:
    sources = data['data']['sources']
    print(f"Quellen für Canada: {len(sources)}")
    
    # Prüfe ob alle wirklich Canada sind
    non_canada = [s for s in sources if s['country'] != 'Canada' and s['country'] is not None]
    if non_canada:
        print(f"WARNUNG: {len(non_canada)} Quellen sind nicht aus Canada!")
        for s in non_canada:
            print(f"  - {s['domain']} ({s['country']})")
    else:
        print("Alle Quellen sind korrekt gefiltert (Canada oder Global)")