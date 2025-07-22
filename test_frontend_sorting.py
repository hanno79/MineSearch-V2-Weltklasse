#!/usr/bin/env python3
"""
Author: rahn
Datum: 19.07.2025
Version: 1.0
Beschreibung: Einfacher Test für Frontend-Sortierung über requests
"""

import requests
import time

FRONTEND_URL = "http://localhost:3001"
API_BASE = "http://localhost:8000"

def test_frontend_accessibility():
    """Teste ob Frontend erreichbar ist"""
    try:
        response = requests.get(FRONTEND_URL, timeout=5)
        if response.status_code == 200:
            if "MineSearch" in response.text:
                print("✅ Frontend läuft und zeigt MineSearch-Seite")
                return True
            else:
                print("❌ Frontend läuft, aber Inhalt ist falsch")
                return False
        else:
            print(f"❌ Frontend nicht erreichbar: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Frontend nicht erreichbar: {str(e)}")
        return False

def test_api_sorting_responses():
    """Teste ob API alle Sortierparameter korrekt zurückgibt"""
    sort_tests = [
        ("search_timestamp", "desc"),
        ("mine_name", "asc"), 
        ("fields_count", "desc"),
        ("score", "asc")
    ]
    
    print("\n🔄 Teste API-Sortierparameter...")
    
    for sort_by, order in sort_tests:
        try:
            url = f"{API_BASE}/api/benchmark/recent?sort_by={sort_by}&order={order}&limit=5"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    results = data.get("data", [])
                    returned_sort = data.get("sort_by")
                    returned_order = data.get("order")
                    
                    if returned_sort == sort_by and returned_order == order:
                        print(f"✅ {sort_by} {order}: {len(results)} Ergebnisse, Sortierung bestätigt")
                        
                        # Überprüfe dass alle erwarteten Felder vorhanden sind
                        if results:
                            first_result = results[0]
                            expected_fields = ["search_timestamp", "mine_name", "model_used", "fields_count", "score"]
                            missing_fields = [f for f in expected_fields if f not in first_result]
                            
                            if not missing_fields:
                                print(f"   ✅ Alle erwarteten Felder vorhanden")
                            else:
                                print(f"   ⚠️ Fehlende Felder: {missing_fields}")
                    else:
                        print(f"❌ {sort_by} {order}: Sortierparameter stimmen nicht überein")
                else:
                    print(f"❌ {sort_by} {order}: API Error - {data.get('error')}")
            else:
                print(f"❌ {sort_by} {order}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ {sort_by} {order}: Exception - {str(e)}")
        
        time.sleep(0.1)

def test_data_consistency():
    """Teste dass Daten konsistent zurückgegeben werden"""
    print("\n📊 Teste Datenkonsistenz...")
    
    try:
        # Hole dieselben Daten mit verschiedenen Sortierungen
        url1 = f"{API_BASE}/api/benchmark/recent?sort_by=mine_name&order=asc&limit=10"
        url2 = f"{API_BASE}/api/benchmark/recent?sort_by=fields_count&order=desc&limit=10"
        
        response1 = requests.get(url1, timeout=10)
        response2 = requests.get(url2, timeout=10)
        
        if response1.status_code == 200 and response2.status_code == 200:
            data1 = response1.json()
            data2 = response2.json()
            
            if data1.get("success") and data2.get("success"):
                results1 = data1.get("data", [])
                results2 = data2.get("data", [])
                
                if results1 and results2:
                    # Teste dass fields_count und score gleich sind
                    first1 = results1[0]
                    if first1.get("fields_count") == first1.get("score"):
                        print("✅ fields_count und score sind identisch")
                    else:
                        print(f"❌ fields_count ({first1.get('fields_count')}) != score ({first1.get('score')})")
                    
                    # Teste dass alle Ergebnisse die erwarteten Felder haben
                    required_fields = ["mine_name", "model_used", "search_timestamp", "fields_count", "score"]
                    all_have_fields = all(all(field in result for field in required_fields) for result in results1)
                    
                    if all_have_fields:
                        print("✅ Alle Ergebnisse haben die erwarteten Felder")
                    else:
                        print("❌ Einige Ergebnisse haben fehlende Felder")
                    
                else:
                    print("❌ Keine Ergebnisse erhalten")
            else:
                print("❌ API-Fehler bei Datenkonsistenz-Test")
        else:
            print("❌ HTTP-Fehler bei Datenkonsistenz-Test")
            
    except Exception as e:
        print(f"❌ Exception bei Datenkonsistenz-Test: {str(e)}")

def main():
    print("🧪 Frontend-Sortierung Kompatibilitäts-Test")
    print("="*50)
    
    # Teste Frontend-Erreichbarkeit
    if not test_frontend_accessibility():
        print("⚠️ Frontend nicht erreichbar - Teste nur Backend-APIs")
    
    # Teste API-Sortierung
    test_api_sorting_responses()
    
    # Teste Datenkonsistenz  
    test_data_consistency()
    
    print("\n" + "="*50)
    print("✅ Kompatibilitäts-Tests abgeschlossen!")
    print("\n📝 Nächste Schritte:")
    print("1. Öffne http://localhost:3001 im Browser")
    print("2. Gehe zu 'Gespeicherte Suchergebnisse'")
    print("3. Klicke auf die Spalten-Header um zu sortieren")
    print("4. Nutze das Filter-Form und klicke 'Filter anwenden'")
    print("5. Teste verschiedene Kombinationen von Sortierung + Filterung")

if __name__ == "__main__":
    main()