#!/usr/bin/env python3
"""
Author: rahn
Datum: 19.07.2025
Version: 1.0
Beschreibung: Test-Script für Sortier- und Filterfunktionen der MineSearch Frontend
"""

import requests
import json
import time

API_BASE = "http://localhost:8000"

def test_sorting():
    """Teste alle Sortieroptionen"""
    print("🔄 Teste Sortierung...")
    
    test_cases = [
        ("search_timestamp", "desc", "Zeitpunkt absteigend"),
        ("search_timestamp", "asc", "Zeitpunkt aufsteigend"),
        ("mine_name", "asc", "Mine A-Z"),
        ("mine_name", "desc", "Mine Z-A"),
        ("model_used", "asc", "Modell A-Z"),
        ("model_used", "desc", "Modell Z-A"),
        ("fields_count", "desc", "Felder absteigend"),
        ("fields_count", "asc", "Felder aufsteigend"),
        ("score", "desc", "Score absteigend"),
        ("score", "asc", "Score aufsteigend")
    ]
    
    for sort_by, order, description in test_cases:
        try:
            url = f"{API_BASE}/api/benchmark/recent?sort_by={sort_by}&order={order}&limit=3"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    results = data.get("data", [])
                    print(f"✅ {description}: {len(results)} Ergebnisse")
                    
                    # Zeige erste Werte zur Verifikation
                    if results:
                        if sort_by == "search_timestamp":
                            values = [r.get("search_timestamp", "N/A")[:10] for r in results[:2]]
                        elif sort_by in ["fields_count", "score"]:
                            values = [r.get(sort_by, 0) for r in results[:2]]
                        else:
                            values = [r.get(sort_by, "N/A") for r in results[:2]]
                        print(f"   📊 Erste Werte: {values}")
                else:
                    print(f"❌ {description}: API Fehler - {data.get('error', 'Unbekannt')}")
            else:
                print(f"❌ {description}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ {description}: Exception - {str(e)}")
        
        time.sleep(0.1)  # Kurze Pause zwischen Requests

def test_filtering():
    """Teste Filterfunktionen"""
    print("\n🔍 Teste Filterung...")
    
    test_cases = [
        ({"mine_name": "Foxtrot"}, "Filter nach Mine: Foxtrot"),
        ({"country": "Canada"}, "Filter nach Land: Canada"),
        ({"days_back": "7"}, "Filter: Letzte 7 Tage"),
        ({"mine_name": "Éléonore", "country": "Canada"}, "Kombiniert: Mine + Land"),
    ]
    
    for params, description in test_cases:
        try:
            url = f"{API_BASE}/api/benchmark/recent"
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    results = data.get("data", [])
                    print(f"✅ {description}: {len(results)} Ergebnisse gefunden")
                    
                    # Zeige Beispiel-Ergebnisse
                    if results:
                        first = results[0]
                        mine = first.get("mine_name", "N/A")
                        country = first.get("country", "N/A")
                        timestamp = first.get("search_timestamp", "N/A")[:10]
                        print(f"   📋 Beispiel: {mine} ({country}) - {timestamp}")
                else:
                    print(f"❌ {description}: API Fehler - {data.get('error', 'Unbekannt')}")
            else:
                print(f"❌ {description}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ {description}: Exception - {str(e)}")
        
        time.sleep(0.1)

def test_combined():
    """Teste Sortierung + Filterung kombiniert"""
    print("\n🔄+🔍 Teste Sortierung + Filterung kombiniert...")
    
    test_cases = [
        ({"mine_name": "Foxtrot", "sort_by": "search_timestamp", "order": "desc"}, 
         "Foxtrot nach Zeitpunkt sortiert"),
        ({"country": "Canada", "sort_by": "mine_name", "order": "asc"}, 
         "Canada nach Mine A-Z sortiert"),
        ({"days_back": "30", "sort_by": "fields_count", "order": "desc"}, 
         "30 Tage nach Feldern sortiert"),
    ]
    
    for params, description in test_cases:
        try:
            url = f"{API_BASE}/api/benchmark/recent"
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    results = data.get("data", [])
                    print(f"✅ {description}: {len(results)} Ergebnisse")
                    
                    # Verifikation der Sortierung
                    if len(results) >= 2:
                        sort_by = params.get("sort_by", "search_timestamp")
                        if sort_by in ["fields_count", "score"]:
                            values = [r.get(sort_by, 0) for r in results[:3]]
                        else:
                            values = [r.get(sort_by, "N/A") for r in results[:3]]
                        print(f"   📊 Sortierte Werte: {values}")
                else:
                    print(f"❌ {description}: API Fehler - {data.get('error', 'Unbekannt')}")
            else:
                print(f"❌ {description}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ {description}: Exception - {str(e)}")
        
        time.sleep(0.1)

def main():
    print("🧪 MineSearch Sortier- und Filter-Tests")
    print("="*50)
    
    # Teste Backend-Erreichbarkeit
    try:
        response = requests.get(f"{API_BASE}/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend erreichbar")
        else:
            print(f"❌ Backend nicht erreichbar: HTTP {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Backend nicht erreichbar: {str(e)}")
        return
    
    # Führe Tests durch
    test_sorting()
    test_filtering() 
    test_combined()
    
    print("\n" + "="*50)
    print("✅ Alle Tests abgeschlossen!")
    print("💡 Tipp: Öffne http://localhost:3001 um das Frontend zu testen")

if __name__ == "__main__":
    main()