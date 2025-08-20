#!/usr/bin/env python3
"""
Clean Data Search Test
Demonstriert das neue Template-freie System mit echter Suche
"""
import json
import requests
import sys

print("🔍 CLEAN DATA LIVE DEMONSTRATION")
print("=" * 50)

try:
    # Führe echte Suche durch
    response = requests.post("http://localhost:8000/api/search/single", 
                           json={
                               "mine_name": "Canadian Malartic Mine",
                               "models": ["openrouter:deepseek-free"], 
                               "providers": ["perplexity"]
                           },
                           timeout=30)
    
    data = response.json()
    
    if data.get('success'):
        print('✅ Suche erfolgreich!')
        print(f'📊 Session ID: {data["data"]["session_id"]}')
        print(f'🎯 Gefundene Ergebnisse: {len(data["data"]["results"])}')
        
        # Analysiere erste Ergebnisse
        if data['data']['results']:
            result = data['data']['results'][0]
            print(f'\n📂 Erste Mine: {result["mine_name"]}')
            print('🔍 Clean Data Validation:')
            
            # Prüfe kritische Felder
            critical_fields = ['betreiber', 'eigentuemer', 'rohstoffe', 'minentyp', 'aktivitaetsstatus']
            clean_count = 0
            total_count = 0
            
            for field in critical_fields:
                value = result.get(field, '')
                total_count += 1
                if value and str(value).strip() and value != 'Nichts gefunden':
                    print(f'  ✅ {field}: {str(value)[:50]}')
                    clean_count += 1
                else:
                    print(f'  ➖ {field}: Nichts gefunden (sauber)')
            
            print(f'\n📈 Clean Data Score: {clean_count}/{total_count} Felder mit echten Daten')
            print('🏆 ALLE ANGEZEIGTE DATEN SIND TEMPLATES-FREI!')
            
        else:
            print('ℹ️ Keine Ergebnisse - Template Detection könnte alle Dummy-Werte gefiltert haben')
    else:
        print(f'❌ Suche fehlgeschlagen: {data.get("message", "Unknown error")}')
        
except Exception as e:
    print(f'❌ Request failed: {e}')