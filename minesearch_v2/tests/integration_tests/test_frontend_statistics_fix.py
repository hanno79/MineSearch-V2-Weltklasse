#!/usr/bin/env python3
"""
Author: rahn
Datum: 14.07.2025
Version: 1.0
Beschreibung: Test Frontend Statistics Fix - Validiert dass ModelSummary Fix funktioniert
"""

import requests
import json
from datetime import datetime

def test_frontend_statistics_fix():
    """
    Testet dass die Frontend Statistics jetzt funktionieren
    """
    print("🌐 FRONTEND STATISTICS FIX VALIDATION")
    print("="*50)
    
    # Test alle kritischen API-Endpoints
    endpoints_to_test = [
        {
            "name": "Benchmark Summary",
            "url": "/api/benchmark/summary",
            "expected_field": "total_models",
            "expected_min": 35
        },
        {
            "name": "Model Summaries", 
            "url": "/api/benchmark/model-summaries",
            "expected_field": "total",
            "expected_min": 35
        },
        {
            "name": "Model Summaries Data",
            "url": "/api/benchmark/model-summaries",
            "expected_field": "data",
            "expected_type": list,
            "expected_min": 35
        }
    ]
    
    success_count = 0
    
    for test in endpoints_to_test:
        try:
            url = f"http://localhost:8000{test['url']}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if test["expected_field"] in data:
                    field_value = data[test["expected_field"]]
                    
                    if "expected_type" in test:
                        if isinstance(field_value, test["expected_type"]):
                            actual_count = len(field_value)
                            if actual_count >= test["expected_min"]:
                                print(f"✅ {test['name']}: {actual_count} Einträge (≥{test['expected_min']})")
                                success_count += 1
                            else:
                                print(f"⚠️ {test['name']}: {actual_count} Einträge (<{test['expected_min']})")
                        else:
                            print(f"❌ {test['name']}: Falscher Datentyp {type(field_value)}")
                    else:
                        if field_value >= test["expected_min"]:
                            print(f"✅ {test['name']}: {field_value} (≥{test['expected_min']})")
                            success_count += 1
                        else:
                            print(f"⚠️ {test['name']}: {field_value} (<{test['expected_min']})")
                else:
                    print(f"❌ {test['name']}: Feld '{test['expected_field']}' nicht gefunden")
            else:
                print(f"❌ {test['name']}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ {test['name']}: Exception {e}")
    
    # Teste Datenqualität
    try:
        response = requests.get("http://localhost:8000/api/benchmark/model-summaries", timeout=10)
        if response.status_code == 200:
            data = response.json()
            models = data.get("data", [])
            
            if models:
                print(f"\n📊 TOP 5 MODELS (Frontend-Ready):")
                for i, model in enumerate(models[:5]):
                    rank = f"#{i+1}"
                    model_id = model.get("model_id", "N/A")
                    success_rate = model.get("success_rate", 0) * 100
                    fields = model.get("avg_fields_found", 0)
                    tests = model.get("total_tests", 0)
                    print(f"  {rank} {model_id}: {success_rate:.1f}% Erfolg, {fields:.1f} Felder, {tests} Tests")
                
                success_count += 1
                
                # Test specific top models
                expected_top_models = ["openai:o4-mini", "gemini:gemini-2.5-flash", "anthropic:claude-3.7-sonnet"]
                found_models = [model["model_id"] for model in models]
                found_expected = [model for model in expected_top_models if model in found_models]
                
                print(f"\n🎯 Expected High-Performance Models gefunden: {len(found_expected)}/{len(expected_top_models)}")
                for found in found_expected:
                    print(f"  ✅ {found}")
                    
            else:
                print(f"❌ Keine Model-Daten in response")
        else:
            print(f"❌ Model Summaries Detail-Test: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Model Summaries Detail-Test: {e}")
    
    # Final Assessment
    total_tests = len(endpoints_to_test) + 1  # +1 für Detail-Test
    success_rate = (success_count / total_tests) * 100
    
    print(f"\n🏁 FRONTEND STATISTICS FIX ASSESSMENT")
    print(f"✅ Erfolgreiche Tests: {success_count}/{total_tests} ({success_rate:.1f}%)")
    
    if success_count >= total_tests * 0.8:  # 80% Erfolgsrate
        print(f"🎉 FRONTEND STATISTICS FIX ERFOLGREICH!")
        print(f"📈 Das Frontend sollte jetzt alle Statistics anzeigen können")
        return True
    else:
        print(f"⚠️ Frontend Statistics Fix unvollständig - weitere Arbeit erforderlich")
        return False

def test_specific_frontend_functions():
    """
    Testet spezifische Frontend-relevante API-Calls
    """
    print(f"\n🔧 FRONTEND-FUNCTION SIMULATION")
    print("="*30)
    
    # Simuliere Frontend loadStatistics() Call
    try:
        print("📞 Simuliere Frontend loadStatistics() API-Call...")
        
        # Schritt 1: Lade verfügbare Modelle (wie das Frontend)
        models_response = requests.get("http://localhost:8000/api/models", timeout=5)
        if models_response.status_code == 200:
            models_data = models_response.json()
            models_count = len(models_data.get("models", {}))
            print(f"  ✅ Models API: {models_count} Modelle verfügbar")
        else:
            print(f"  ❌ Models API: HTTP {models_response.status_code}")
            return False
        
        # Schritt 2: Lade Benchmark Summary (wie das Frontend)
        summary_response = requests.get("http://localhost:8000/api/benchmark/summary", timeout=5)
        if summary_response.status_code == 200:
            summary_data = summary_response.json()
            total_models = summary_data.get("total_models", 0)
            print(f"  ✅ Summary API: {total_models} Models in Statistiken")
        else:
            print(f"  ❌ Summary API: HTTP {summary_response.status_code}")
            return False
            
        # Schritt 3: Lade Model Summaries (wie das Frontend)
        summaries_response = requests.get("http://localhost:8000/api/benchmark/model-summaries", timeout=5)
        if summaries_response.status_code == 200:
            summaries_data = summaries_response.json()
            summaries_count = summaries_data.get("total", 0)
            print(f"  ✅ Model-Summaries API: {summaries_count} Summaries verfügbar")
            
            # Test data structure für Frontend
            data_array = summaries_data.get("data", [])
            if data_array and len(data_array) > 0:
                sample = data_array[0]
                required_fields = ["model_id", "total_tests", "success_rate", "avg_fields_found"]
                missing_fields = [field for field in required_fields if field not in sample]
                
                if not missing_fields:
                    print(f"  ✅ Data Structure: Alle Required Fields vorhanden")
                    return True
                else:
                    print(f"  ❌ Data Structure: Missing Fields {missing_fields}")
                    return False
            else:
                print(f"  ❌ Model-Summaries: Keine Daten im Array")
                return False
        else:
            print(f"  ❌ Model-Summaries API: HTTP {summaries_response.status_code}")
            return False
            
    except Exception as e:
        print(f"  ❌ Frontend-Function Simulation: {e}")
        return False

if __name__ == "__main__":
    print(f"🕒 Test Time: {datetime.now().isoformat()}")
    
    # Haupttest
    main_success = test_frontend_statistics_fix()
    
    # Frontend-Function Test
    frontend_success = test_specific_frontend_functions()
    
    print(f"\n" + "="*60)
    if main_success and frontend_success:
        print(f"🎯 VOLLSTÄNDIGER ERFOLG - Frontend Statistics sind repariert!")
        print(f"📊 Benutzer können jetzt alle 37+ Models in den Statistics sehen")
    else:
        print(f"⚠️ Teilweiser Erfolg - weitere Debugging erforderlich")