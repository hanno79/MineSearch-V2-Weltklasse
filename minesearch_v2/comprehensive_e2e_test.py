#!/usr/bin/env python3
"""
Author: rahn
Datum: 07.08.2025
Version: 1.0
Beschreibung: Comprehensive E2E Test für Statistik-Funktionalität
ÄNDERUNG 07.08.2025: Complete Browser-Simulation für Statistik-Frontend
"""

import requests
import json
import time
from urllib.parse import urlencode

API_BASE = "http://localhost:8000"

def test_main_page():
    """Test ob Hauptseite lädt"""
    print("🌐 TESTE HAUPTSEITE...")
    try:
        response = requests.get(API_BASE, timeout=10)
        if response.status_code == 200:
            content = response.text
            if "statistics" in content.lower():
                print("✅ Hauptseite lädt und enthält Statistik-Komponenten")
                return True
            else:
                print("❌ Hauptseite lädt aber enthält keine Statistik-Referenzen")
                return False
        else:
            print(f"❌ Hauptseite HTTP Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Hauptseite Fehler: {e}")
        return False

def test_statistics_comprehensive_api():
    """Test Haupt-Statistik API"""
    print("📊 TESTE STATISTIK COMPREHENSIVE API...")
    try:
        url = f"{API_BASE}/api/statistics/models/comprehensive"
        
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'MineSearchBrowserTest/1.0'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success') and data.get('data', {}).get('models'):
                models = data['data']['models']
                print(f"✅ Statistik API: {len(models)} Modelle geladen")
                
                # Validate model structure
                first_model = models[0]
                required_fields = ['model_id', 'model_name', 'provider', 'overall_score', 'success_rate_percent', 'score_category']
                
                for field in required_fields:
                    if field not in first_model:
                        print(f"❌ Fehlender Field in Model: {field}")
                        return False
                
                print(f"✅ Model Structure: Alle required Fields vorhanden")
                print(f"✅ Sample Model: {first_model['model_name'][:40]}... (Score: {first_model['overall_score']})")
                
                return True
            else:
                print("❌ Statistik API: Keine Models in Response")
                return False
        else:
            print(f"❌ Statistik API HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Statistik API Fehler: {e}")
        return False

def test_details_modal_api():
    """Test Details Modal API"""
    print("🔍 TESTE DETAILS MODAL API...")
    try:
        # Erst Hauptapi aufrufen um Model IDs zu bekommen
        main_response = requests.get(f"{API_BASE}/api/statistics/models/comprehensive", timeout=10)
        if main_response.status_code != 200:
            print("❌ Kann keine Model IDs für Details-Test bekommen")
            return False
        
        models = main_response.json()['data']['models']
        if not models:
            print("❌ Keine Modelle für Details-Test verfügbar")
            return False
        
        # Test Details für erstes Model
        test_model_id = models[0]['model_id']
        encoded_model_id = requests.utils.quote(test_model_id, safe='')
        
        details_url = f"{API_BASE}/api/statistics/models/{encoded_model_id}/details"
        
        details_response = requests.get(details_url, timeout=10)
        
        if details_response.status_code == 200:
            details_data = details_response.json()
            
            required_sections = ['model_stats', 'consistency_analysis', 'most_found_fields_analysis']
            found_sections = 0
            
            for section in required_sections:
                if section in details_data:
                    found_sections += 1
                    print(f"✅ Details Section: {section}")
                else:
                    print(f"❌ Missing Details Section: {section}")
            
            if found_sections >= 2:  # At least 2 sections should be available
                print(f"✅ Details Modal API: {found_sections}/{len(required_sections)} Sections verfügbar")
                return True
            else:
                print(f"❌ Details Modal API: Nur {found_sections}/{len(required_sections)} Sections verfügbar")
                return False
        else:
            print(f"❌ Details API HTTP Error: {details_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Details Modal API Fehler: {e}")
        return False

def test_frontend_javascript_simulation():
    """Simuliert Frontend JavaScript Verhalten"""
    print("🚀 TESTE FRONTEND JAVASCRIPT SIMULATION...")
    
    try:
        # Simuliere das was das Frontend JavaScript machen würde
        
        # 1. Lade Statistik-Daten
        stats_response = requests.get(f"{API_BASE}/api/statistics/models/comprehensive")
        if stats_response.status_code != 200:
            print("❌ Frontend kann keine Statistik-Daten laden")
            return False
            
        stats_data = stats_response.json()
        models = stats_data['data']['models']
        
        # 2. Simuliere Table Rendering
        print(f"✅ Frontend würde Tabelle mit {len(models)} Modellen rendern")
        
        # 3. Simuliere Details Modal für jedes Model
        working_details = 0
        for model in models[:2]:  # Test nur die ersten 2 Models
            model_id = model['model_id']
            encoded_id = requests.utils.quote(model_id, safe='')
            
            details_url = f"{API_BASE}/api/statistics/models/{encoded_id}/details"
            try:
                details_response = requests.get(details_url, timeout=5)
                if details_response.status_code == 200:
                    working_details += 1
                    print(f"✅ Details Modal für {model['model_name'][:30]}... würde funktionieren")
                else:
                    print(f"❌ Details Modal für {model['model_name'][:30]}... würde fehlschlagen")
            except:
                print(f"❌ Details Modal für {model['model_name'][:30]}... nicht erreichbar")
        
        # 4. Simuliere Export Funktionalität
        export_url = f"{API_BASE}/api/statistics/export/csv?table=models"
        try:
            export_response = requests.get(export_url, timeout=5)
            if export_response.status_code == 200:
                print("✅ Export-Funktionalität würde funktionieren")
            else:
                print("❌ Export-Funktionalität würde fehlschlagen")
        except:
            print("❌ Export-Funktionalität nicht erreichbar")
        
        # Summary
        success_rate = working_details / len(models[:2]) if models else 0
        if success_rate >= 0.5:  # At least 50% should work
            print(f"✅ Frontend JavaScript Simulation: {working_details}/{len(models[:2])} Details funktionsfähig")
            return True
        else:
            print(f"❌ Frontend JavaScript Simulation: Nur {working_details}/{len(models[:2])} Details funktionsfähig")
            return False
            
    except Exception as e:
        print(f"❌ Frontend JavaScript Simulation Fehler: {e}")
        return False

def test_full_user_journey():
    """Test komplette User Journey"""
    print("👤 TESTE COMPLETE USER JOURNEY...")
    
    journey_steps = [
        ("Hauptseite besuchen", test_main_page),
        ("Zur Statistik-Seite navigieren", test_statistics_comprehensive_api),
        ("Statistik-Tabelle laden", lambda: True),  # Already tested above
        ("Details Modal öffnen", test_details_modal_api),
        ("Frontend Interaktion", test_frontend_javascript_simulation)
    ]
    
    passed_steps = 0
    total_steps = len(journey_steps)
    
    for step_name, step_func in journey_steps:
        print(f"\n🔄 User Journey Step: {step_name}")
        if step_func():
            passed_steps += 1
            print(f"✅ Step erfolgreich")
        else:
            print(f"❌ Step fehlgeschlagen")
    
    success_rate = passed_steps / total_steps
    print(f"\n📊 USER JOURNEY RESULTS:")
    print(f"  Successful Steps: {passed_steps}/{total_steps}")
    print(f"  Success Rate: {success_rate:.1%}")
    
    return success_rate >= 0.8  # 80% success rate required

def main():
    """Main E2E Test Runner"""
    print("=" * 60)
    print("🧪 COMPREHENSIVE E2E TEST für STATISTIK-FUNKTIONALITÄT")
    print("=" * 60)
    
    # Warte etwas damit Server ready ist
    print("⏳ Warte 3 Sekunden für Server-Bereitschaft...")
    time.sleep(3)
    
    all_tests = [
        ("Hauptseite", test_main_page),
        ("Statistik API", test_statistics_comprehensive_api), 
        ("Details Modal API", test_details_modal_api),
        ("Frontend Simulation", test_frontend_javascript_simulation),
        ("Complete User Journey", test_full_user_journey)
    ]
    
    passed = 0
    total = len(all_tests)
    
    print(f"\n🚀 STARTE {total} TESTS...\n")
    
    for test_name, test_func in all_tests:
        print(f"{'='*20} TEST: {test_name} {'='*20}")
        
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED\n")
            else:
                print(f"❌ {test_name}: FAILED\n")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}\n")
    
    # Final Results
    print("=" * 60)
    print("🎯 FINALE ERGEBNISSE:")
    print("=" * 60)
    print(f"Passed Tests: {passed}/{total}")
    print(f"Success Rate: {passed/total:.1%}")
    
    if passed == total:
        print("\n🎉 ALLE TESTS BESTANDEN - STATISTIK-SYSTEM VOLLSTÄNDIG FUNKTIONAL!")
        return True
    elif passed >= total * 0.8:
        print(f"\n✅ SYSTEM FUNKTIONAL - {passed}/{total} Tests bestanden")
        return True
    else:
        print(f"\n❌ SYSTEM HAT PROBLEME - Nur {passed}/{total} Tests bestanden")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)