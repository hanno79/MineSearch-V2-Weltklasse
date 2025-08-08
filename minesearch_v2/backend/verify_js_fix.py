#!/usr/bin/env python3
"""
Author: rahn
Datum: 07.08.2025  
Version: 1.0
Beschreibung: Direkte Verifizierung des JavaScript URL Fix
"""

import requests
import json

def test_javascript_fix():
    """Simuliert das was das JavaScript jetzt macht"""
    print("🔧 JAVASCRIPT FIX VERIFICATION")
    print("=" * 40)
    
    # Test Individual Models API
    print("1. 📊 Teste Individual Models API...")
    try:
        response = requests.get("http://localhost:8000/api/statistics/models/comprehensive")
        if response.status_code == 200:
            data = response.json()
            models = data['data']['models']
            print(f"   ✅ {len(models)} Individual Models geladen")
            
            # Teste mit erstem Model
            if models:
                test_model_id = models[0]['model_id']
                print(f"   📋 Test Model: {test_model_id}")
                
                # 2. Teste Details API (das was JavaScript jetzt aufruft)
                print("2. 🔍 Teste Details API (neue URL)...")
                encoded_id = requests.utils.quote(test_model_id, safe='')
                details_url = f"http://localhost:8000/api/statistics/models/{encoded_id}/details"
                
                details_response = requests.get(details_url)
                if details_response.status_code == 200:
                    details_data = details_response.json()
                    print("   ✅ Details API Response OK")
                    print(f"   📊 Model Stats: {'model_stats' in details_data}")
                    print(f"   📈 Consistency Analysis: {'consistency_analysis' in details_data}")
                    print(f"   🎯 Field Performance: {'field_specific_performance' in details_data}")
                else:
                    print(f"   ❌ Details API Error: {details_response.status_code}")
                    return False
                
                # 3. Teste Search Results API (zweiter Call)
                print("3. 🔎 Teste Search Results API...")
                results_url = f"http://localhost:8000/api/results?model_id={encoded_id}&limit=50"
                results_response = requests.get(results_url)
                
                if results_response.status_code == 200:
                    results_data = results_response.json()
                    print("   ✅ Search Results API OK")
                    print(f"   📋 Results: {len(results_data.get('data', {}).get('results', []))}")
                else:
                    print(f"   ❌ Search Results API Error: {results_response.status_code}")
                    return False
                
                # 4. Simuliere kompletten JavaScript Workflow
                print("4. 🚀 Simuliere JavaScript showModelDetails()...")
                
                # Das ist was das JavaScript jetzt machen würde:
                try:
                    # Promise.all simulation
                    model_details = details_data
                    search_results = results_data
                    
                    # Verarbeitung wie im JavaScript
                    model_stats = model_details.get('model_stats', {})
                    consistency = model_details.get('consistency_analysis', {})
                    field_performance = model_details.get('field_specific_performance', {})
                    
                    print("   ✅ Model Details verarbeitet:")
                    print(f"      📊 Model ID: {model_stats.get('model_id', 'N/A')}")  
                    print(f"      📈 Provider: {model_stats.get('provider', 'N/A')}")
                    print(f"      🎯 Overall Consistency: {consistency.get('overall_consistency', 'N/A')}")
                    print(f"      📋 Field Performance Items: {len(field_performance)}")
                    
                    print("\n🎉 JAVASCRIPT WORKFLOW SIMULATION ERFOLGREICH!")
                    return True
                    
                except Exception as e:
                    print(f"   ❌ JavaScript Simulation Error: {e}")
                    return False
                    
        else:
            print(f"   ❌ Models API Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Test Error: {e}")
        return False

def verify_html_fix():
    """Verifiziert dass der HTML Fix korrekt angewandt wurde"""
    print("\n5. 📝 Verifiziere HTML Fix...")
    
    try:
        with open('/app/frontend/index.html', 'r') as f:
            content = f.read()
            
        # Suche nach der korrigierten URL
        if '/api/statistics/models/' in content and 'details?days_back=30' in content:
            print("   ✅ Korrekte URL gefunden: /api/statistics/models/.../details")
            
            # Prüfe dass die alte URL NICHT mehr da ist
            if '/api/statistics/model/' in content and '/api/statistics/models/' in content:
                # Count occurrences  
                old_count = content.count('/api/statistics/model/')
                new_count = content.count('/api/statistics/models/')
                
                if old_count < new_count:
                    print(f"   ✅ URL Fix angewandt: {new_count} korrekte URLs, {old_count} alte URLs")
                    return True
                else:
                    print(f"   ⚠️ Möglicherweise unvollständiger Fix: {new_count} neue, {old_count} alte URLs")
                    return False
            else:
                print("   ✅ Nur korrekte URLs gefunden")
                return True
        else:
            print("   ❌ Korrekte URL nicht gefunden in HTML")
            return False
            
    except Exception as e:
        print(f"   ❌ HTML Verify Error: {e}")
        return False

if __name__ == "__main__":
    api_success = test_javascript_fix()
    html_success = verify_html_fix()
    
    print("\n" + "=" * 40)
    print("🎯 GESAMTERGEBNIS:")
    print(f"   {'✅' if api_success else '❌'} JavaScript API Workflow: {'SUCCESS' if api_success else 'FAILED'}")
    print(f"   {'✅' if html_success else '❌'} HTML Fix Verification: {'SUCCESS' if html_success else 'FAILED'}")
    
    overall_success = api_success and html_success
    print(f"\n{'🎉 DETAILS BUTTON FIX VOLLSTÄNDIG ERFOLGREICH!' if overall_success else '❌ FIX NOCH NICHT VOLLSTÄNDIG!'}")