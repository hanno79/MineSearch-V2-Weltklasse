#!/usr/bin/env python3
"""
Test script for premium models search functionality
"""

import requests
import json
import time

def test_premium_search():
    print("=== PREMIUM-MODELL SUCHTEST ===")
    
    # Test mit Claude 3.5 Sonnet über OpenRouter
    test_model = "openrouter:claude-3.5-sonnet"
    test_mine = "Eleonore Mine"
    
    print(f"📋 Teste Modell: {test_model}")
    print(f"⛏️  Teste Mine: {test_mine}")
    
    # Batch-Search Request (Form-Data für diese Route)
    batch_data = {
        "session_id": "premium-test-session", 
        "selected_models": test_model,  # Komma-getrennt für mehrere Modelle
        "search_type": "standard",
        "count": 1,
        "search_all": "false"
    }
    
    print("\n🔄 Starte Batch-Search...")
    start_time = time.time()
    
    try:
        response = requests.post(
            "http://localhost:8000/api/batch-search",
            data=batch_data,  # Form-Data statt JSON
            timeout=120
        )
        
        duration = time.time() - start_time
        print(f"⏱️  Duration: {duration:.1f}s")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                results = data.get('results', [])
                print(f"✅ Search erfolgreich: {len(results)} Ergebnisse")
                
                for result in results:
                    print(f"\n📋 Mine: {result.get('mine_name')}")
                    print(f"🤖 Model: {result.get('model_id')}")
                    print(f"✅ Success: {result.get('success')}")
                    
                    if result.get('success'):
                        structured_data = result.get('structured_data', {})
                        print(f"📊 Extrahierte Felder: {len(structured_data)}")
                        
                        # Zeige ein paar wichtige Felder
                        for field in ['Country', 'Region', 'Eigentümer', 'Aktivitätsstatus']:
                            if field in structured_data:
                                value = structured_data[field]
                                if isinstance(value, dict):
                                    display_value = value.get('display_value', 'N/A')
                                else:
                                    display_value = value
                                print(f"   {field}: {display_value}")
                    else:
                        print(f"❌ Fehler: {result.get('error', 'Unbekannter Fehler')}")
                        
            else:
                print(f"❌ API Fehler: {data.get('error', 'Unbekannter Fehler')}")
        else:
            print(f"❌ HTTP Fehler: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_premium_search()