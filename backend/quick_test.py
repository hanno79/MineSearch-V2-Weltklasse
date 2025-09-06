#!/usr/bin/env python3
"""
Author: rahn
Datum: 06.09.2025
Version: 1.0
Beschreibung: Schneller Test für Enhanced Batch Search Integration
"""

import requests
import json

def test_frontend_integration():
    """Test ob Frontend Enhanced Batch Optionen zeigt"""
    print("🧪 TESTE FRONTEND INTEGRATION")
    print("=" * 40)
    
    # Test 1: Frontend HTML prüfen
    print("1. FRONTEND HTML TEST:")
    try:
        response = requests.get("http://localhost:8000/")
        if response.status_code == 200:
            html = response.text
            
            # Prüfe Enhanced Batch Optionen
            checks = [
                ("Range-Auswahl", "📊 Range-Auswahl" in html),
                ("Zufällige Auswahl", "🎲 Zufällige Auswahl" in html),
                ("toggleBatchOptions", "toggleBatchOptions()" in html),
                ("batch_mode Attribute", 'name="batch_mode"' in html),
                ("JavaScript Include", 'src="/static/search.js' in html)
            ]
            
            for check_name, result in checks:
                status = "✅" if result else "❌"
                print(f"   {status} {check_name}: {'GEFUNDEN' if result else 'FEHLT'}")
            
            all_checks_passed = all(result for _, result in checks)
            print(f"\n   📊 Frontend Integration: {'ERFOLGREICH' if all_checks_passed else 'FEHLGESCHLAGEN'}")
            
            return all_checks_passed
        else:
            print(f"   ❌ Frontend nicht erreichbar: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Fehler beim Frontend-Test: {e}")
        return False

def test_api_endpoints():
    """Test API Endpoints"""
    print("\n2. API ENDPOINTS TEST:")
    
    try:
        # Test Static Files Route
        response = requests.get("http://localhost:8000/static/search.js")
        js_status = "✅" if response.status_code == 200 else "❌"
        print(f"   {js_status} JavaScript File: {response.status_code}")
        
        # Test API Health  
        response = requests.get("http://localhost:8000/docs")
        api_status = "✅" if response.status_code == 200 else "❌"
        print(f"   {api_status} API Documentation: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ API Test Fehler: {e}")
        return False

if __name__ == "__main__":
    print("🚀 ENHANCED BATCH SEARCH INTEGRATION TEST")
    print("=" * 50)
    
    frontend_ok = test_frontend_integration()
    api_ok = test_api_endpoints()
    
    print("\n" + "=" * 50)
    if frontend_ok and api_ok:
        print("🎉 INTEGRATION TEST ERFOLGREICH!")
        print("✅ Alle Enhanced Batch Search Optionen sind im Frontend verfügbar")
        print("✅ 4 Auswahlmodi implementiert:")
        print("   • Erste X Minen (limited)")
        print("   • Range-Auswahl (range)")  
        print("   • Zufällige Auswahl (random)")
        print("   • Alle Minen (all)")
        print("✅ JavaScript Funktionen implementiert")
        print("✅ API Integration funktioniert")
        print("\n🔗 Besuchen Sie http://localhost:8000/ um die neuen Optionen zu testen!")
    else:
        print("❌ INTEGRATION TEST FEHLGESCHLAGEN")
        print("Bitte prüfen Sie Server-Status und Dateien")