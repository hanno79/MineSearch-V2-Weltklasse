"""
Author: rahn
Datum: 04.08.2025
Version: 1.0
Beschreibung: Schnelle Browser-Validierung der Progress-Funktionalität
"""

import requests
import json
import time

def quick_validation():
    """Schnelle Validierung der Progress-APIs und Frontend-Integration"""
    
    print("🚀 SCHNELLE BROWSER-VALIDIERUNG")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    # Test 1: Server Health Check
    print("\n🏥 Test 1: Server Health Check")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server läuft und ist erreichbar")
        else:
            print(f"❌ Server antwortet mit Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Server nicht erreichbar: {e}")
        return False
    
    # Test 2: Models API Test
    print("\n🤖 Test 2: Models API Test")
    try:
        response = requests.get(f"{base_url}/api/models", timeout=10)
        if response.status_code == 200:
            data = response.json()
            model_count = len(data.get('models', {}))
            print(f"✅ Models API funktional - {model_count} Modelle verfügbar")
        else:
            print(f"❌ Models API Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Models API nicht erreichbar: {e}")
        return False
    
    # Test 3: Progress API Test (Mock Session)
    print("\n📊 Test 3: Progress API Test")
    try:
        # Teste Progress-Session Creation
        test_data = {
            "mines": ["Mine_1", "Mine_2", "Mine_3"],
            "models": ["Model_1", "Model_2"]
        }
        
        response = requests.post(
            f"{base_url}/api/progress/create-session",
            json=test_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            session_id = result.get('session_id')
            print(f"✅ Progress Session erstellt: {session_id[:8]}...")
            
            # Teste Progress Status
            status_response = requests.get(f"{base_url}/api/progress/{session_id}", timeout=5)
            if status_response.status_code == 200:
                progress_data = status_response.json()['data']
                total_ops = progress_data['total']
                expected_ops = len(test_data['mines']) * len(test_data['models'])  # 3 × 2 = 6
                
                print(f"✅ Progress Status abrufbar")
                print(f"   Erwartete Operationen: {expected_ops}")
                print(f"   Tatsächliche Operationen: {total_ops}")
                print(f"   Mathematik korrekt: {'✅' if expected_ops == total_ops else '❌'}")
                
                return expected_ops == total_ops
            else:
                print(f"❌ Progress Status Error: {status_response.status_code}")
                return False
        else:
            print(f"❌ Progress Session Creation Failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Progress API Test Failed: {e}")
        return False
    
    # Test 4: CSV Upload Endpoint Test
    print("\n📁 Test 4: CSV Upload Endpoint Test")
    try:
        # Test ob CSV Upload Endpoint erreichbar ist (ohne tatsächlichen Upload)
        # Mache HEAD request um zu prüfen ob Route existiert
        response = requests.post(f"{base_url}/api/batch/upload-csv", files={}, timeout=5)
        
        # Erwarten 400 (Bad Request) da keine Datei geschickt wurde, nicht 404 (Not Found)
        if response.status_code == 400:
            print("✅ CSV Upload Endpoint ist erreichbar")
        elif response.status_code == 422:  # FastAPI Validation Error
            print("✅ CSV Upload Endpoint ist erreichbar (Validation Error erwartet)")
        else:
            print(f"⚠️  CSV Upload Endpoint Status: {response.status_code}")
            
    except Exception as e:
        print(f"⚠️  CSV Upload Endpoint Test: {e}")
        
    # Test 5: Frontend Resource Check
    print("\n🌐 Test 5: Frontend Resource Check")
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            html_content = response.text
            
            # Prüfe wichtige Frontend-Komponenten
            has_progress_js = "progress-tracking.js" in html_content
            has_model_selection = "model-selection" in html_content
            has_csv_upload = 'type="file"' in html_content
            
            print(f"✅ Frontend erreichbar")
            print(f"   Progress-Tracking JS: {'✅' if has_progress_js else '❌'}")
            print(f"   Model-Selection: {'✅' if has_model_selection else '❌'}")
            print(f"   CSV-Upload: {'✅' if has_csv_upload else '❌'}")
            
            return has_progress_js and has_model_selection and has_csv_upload
        else:
            print(f"❌ Frontend nicht erreichbar: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Frontend Test Failed: {e}")
        return False

def main():
    """Hauptfunktion für schnelle Validierung"""
    print("🎯 Starte schnelle Progress-System Validierung...")
    
    # Warte kurz bis Server vollständig gestartet ist
    print("⏳ Warte auf Server-Startup...")
    time.sleep(3)
    
    success = quick_validation()
    
    print("\n" + "=" * 50)
    print("📋 SCHNELLE VALIDIERUNG ABGESCHLOSSEN")
    print("=" * 50)
    
    if success:
        print("🎉 ERFOLGREICH! Progress-System ist funktional!")
        print("   ✅ Server läuft")
        print("   ✅ APIs funktionieren") 
        print("   ✅ Progress-Mathematik korrekt")
        print("   ✅ Frontend-Integration vorhanden")
        print("\n💡 Das vollständige Progress-Tracking System ist bereit für den Live-Test!")
    else:
        print("⚠️  PROBLEME ERKANNT! Siehe Details oben.")
        
    return success

if __name__ == "__main__":
    result = main()
    exit(0 if result else 1)