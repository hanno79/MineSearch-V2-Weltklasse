"""
Author: rahn
Datum: 07.08.2025
Version: 1.0
Beschreibung: Schneller Statistik-Funktionalität Test mit Requests
"""

import requests
import json
from datetime import datetime
import subprocess
import time

def test_statistics_api():
    """Teste die Statistik-API direkt"""
    base_url = "http://localhost:8000"
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "tests": [],
        "success": False
    }
    
    print("🚀 Teste Statistik-API Endpunkte...")
    
    # Test 1: Hauptseite erreichbar
    try:
        response = requests.get(base_url, timeout=10)
        results["tests"].append({
            "test": "main_page",
            "status": "SUCCESS" if response.status_code == 200 else "FAILED",
            "status_code": response.status_code
        })
        print(f"✅ Hauptseite: {response.status_code}")
    except Exception as e:
        results["tests"].append({
            "test": "main_page", 
            "status": "ERROR",
            "error": str(e)
        })
        print(f"❌ Hauptseite Fehler: {e}")
    
    # Test 2: Statistik-API Endpunkt
    statistics_endpoints = [
        "/api/statistics",
        "/api/statistics/",
        "/statistics",
        "/api/routes/statistics",
        "/consolidated-results"
    ]
    
    for endpoint in statistics_endpoints:
        try:
            url = f"{base_url}{endpoint}"
            response = requests.get(url, timeout=10)
            results["tests"].append({
                "test": f"statistics_api_{endpoint.replace('/', '_')}",
                "status": "SUCCESS" if response.status_code == 200 else "FAILED",
                "status_code": response.status_code,
                "content_length": len(response.text) if response.text else 0
            })
            print(f"✅ API {endpoint}: {response.status_code} ({len(response.text)} chars)")
            
            # Bei Erfolg: Analysiere JSON-Antwort
            if response.status_code == 200 and response.text:
                try:
                    data = response.json()
                    if isinstance(data, list):
                        print(f"   📊 {len(data)} Datensätze gefunden")
                    elif isinstance(data, dict):
                        print(f"   📊 Datenstruktur: {list(data.keys())[:5]}")
                except:
                    print(f"   📝 Text-Antwort: {response.text[:100]}...")
        except Exception as e:
            results["tests"].append({
                "test": f"statistics_api_{endpoint.replace('/', '_')}",
                "status": "ERROR", 
                "error": str(e)
            })
            print(f"❌ API {endpoint} Fehler: {e}")
    
    # Test 3: Prüfe ob Server läuft
    try:
        # Prüfe ob ein Python-Server läuft
        ps_result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
        python_processes = [line for line in ps_result.stdout.split('\n') if 'python' in line and '8000' in line]
        
        results["tests"].append({
            "test": "server_running",
            "status": "SUCCESS" if python_processes else "WARNING",
            "processes": len(python_processes)
        })
        print(f"🖥️ Server-Prozesse: {len(python_processes)}")
    except Exception as e:
        print(f"⚠️ Prozess-Check Fehler: {e}")
    
    # Bewerte Gesamterfolg
    successful_tests = len([t for t in results["tests"] if t["status"] == "SUCCESS"])
    total_tests = len(results["tests"])
    success_rate = successful_tests / total_tests if total_tests > 0 else 0
    
    results["success"] = success_rate > 0.5
    results["success_rate"] = success_rate
    results["successful_tests"] = successful_tests
    results["total_tests"] = total_tests
    
    # Speichere Ergebnisse
    report_file = f"quick_statistics_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n📋 Testbericht gespeichert: {report_file}")
    
    # Zusammenfassung
    print("\n" + "="*50)
    print("🎯 SCHNELLTEST ZUSAMMENFASSUNG")
    print("="*50)
    print(f"✅ Erfolgreiche Tests: {successful_tests}/{total_tests}")
    print(f"📊 Erfolgsrate: {success_rate*100:.1f}%")
    print(f"🎯 Gesamterfolg: {'JA' if results['success'] else 'NEIN'}")
    print("="*50)
    
    return results

if __name__ == "__main__":
    test_statistics_api()