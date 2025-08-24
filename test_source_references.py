#!/usr/bin/env python3
"""
Test script für Quellenreferenzen
"""
import requests
import json
import re

def test_source_references():
    print("[QUELLENREFERENZ-TEST] Starte Test der Quellenreferenzen...")
    
    # API-Aufruf
    response = requests.post(
        "http://localhost:8000/api/search",
        headers={"Content-Type": "application/json"},
        json={
            "mine_name": "Eleonore Mine",
            "model": "openrouter:deepseek-free",
            "country": "Kanada"
        }
    )
    
    if response.status_code != 200:
        print(f"❌ API-Fehler: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        return
    
    try:
        data = response.json()
        print(f"[DEBUG] Response keys: {list(data.keys())}")
        print(f"[DEBUG] Full response: {json.dumps(data, indent=2)[:500]}...")
        
        if 'error' in data and data['error'] is not None:
            print(f'❌ Fehler: {data["error"]}')
            return
        
        if 'message' in data and 'data' not in data:
            print(f'⚠️ Nur Message erhalten: {data["message"]}')
            return
        
        if 'data' not in data:
            print('❌ Keine Daten in Response')
            return
            
        result_data = data['data']
        
        # Die strukturierten Daten sind im 'structured_data' Feld
        if 'structured_data' in result_data:
            structured_data = result_data['structured_data']
            print(f'✅ Mine: {structured_data.get("Name", "N/A")}')
            print(f'✅ Betreiber: {structured_data.get("Betreiber", "N/A")}')
            print(f'✅ Aktivitätsstatus: {structured_data.get("Aktivitätsstatus", "N/A")}')
            print(f'✅ Quellenangaben: {structured_data.get("Quellenangaben", "N/A")[:100]}...')
        else:
            structured_data = result_data
        
        # Prüfe auf [1] Referenzen in den strukturierten Daten
        source_refs_found = []
        for field, value in structured_data.items():
            if isinstance(value, str) and '[' in value and ']' in value:
                # Prüfe auf Zahlen in eckigen Klammern
                if re.search(r'\[\d+(?:,\s*\d+)*\]', value):
                    source_refs_found.append(f'{field}: {value[:60]}')
        
        if source_refs_found:
            print(f'\n🎯 QUELLENREFERENZEN GEFUNDEN ({len(source_refs_found)} Felder):')
            for ref in source_refs_found:
                print(f'  • {ref}')
        else:
            print('\n❌ KEINE QUELLENREFERENZEN IN [X] FORMAT GEFUNDEN')
            
        # Liste alle nicht-leeren Felder in structured_data
        non_empty_fields = [k for k, v in structured_data.items() if v and v != 'nichts gefunden']
        print(f'\n📊 ALLE NICHT-LEEREN FELDER ({len(non_empty_fields)}):')
        for field in non_empty_fields:
            value = structured_data[field]
            print(f'  • {field}: {str(value)[:40]}...')
            
    except Exception as e:
        print(f'❌ JSON-Parse-Fehler: {e}')
        print(f'Raw Response: {response.text[:500]}')

if __name__ == "__main__":
    test_source_references()