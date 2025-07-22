#!/usr/bin/env python3
"""
Author: rahn
Datum: 19.07.2025
Version: 1.0
Beschreibung: Test der Datenbereinigung auf existierenden Daten
"""

import requests
import json

API_BASE = "http://localhost:8000"

def test_existing_data_problems():
    """Teste existierende Daten auf die beschriebenen Probleme"""
    print("🔍 Prüfe existierende Daten auf Konsistenz-Probleme...")
    
    try:
        response = requests.get(f"{API_BASE}/api/benchmark/recent?limit=50", timeout=10)
        
        if response.status_code != 200:
            print(f"❌ API nicht erreichbar: HTTP {response.status_code}")
            return
        
        data = response.json()
        if not data.get("success"):
            print(f"❌ API-Fehler: {data.get('error', 'Unbekannt')}")
            return
        
        results = data.get("data", [])
        print(f"✅ {len(results)} Ergebnisse gefunden")
        
        # Analysiere Probleme
        problems = {
            "leer_daten": [],
            "minentyp_praefix": [],
            "leere_quellen": [],
            "gute_beispiele": []
        }
        
        for result in results:
            structured_data = result.get("structured_data", {})
            
            # Prüfe auf LEER-Probleme
            for field, value in structured_data.items():
                if isinstance(value, str):
                    if "LEER - keine verlässlichen Daten" in value:
                        problems["leer_daten"].append({
                            "mine": result.get("mine_name"),
                            "field": field,
                            "value": value
                        })
                    
                    if field == "Minentyp (Untertage/ Open-Pit/ usw.)" and "Untertage/ Open-Pit/ usw.)" in value:
                        problems["minentyp_praefix"].append({
                            "mine": result.get("mine_name"),
                            "value": value
                        })
            
            # Prüfe Quellenangaben
            quellenangaben = structured_data.get("Quellenangaben", "")
            if not quellenangaben or quellenangaben.strip() == "":
                problems["leere_quellen"].append(result.get("mine_name"))
            elif len(quellenangaben) > 50:  # Gute Quellenangaben
                problems["gute_beispiele"].append({
                    "mine": result.get("mine_name"),
                    "quellen_preview": quellenangaben[:100]
                })
        
        print("\n📊 Analyse-Ergebnisse:")
        print(f"  LEER-Daten Probleme: {len(problems['leer_daten'])}")
        print(f"  Minentyp-Präfix Probleme: {len(problems['minentyp_praefix'])}")
        print(f"  Leere Quellenangaben: {len(problems['leere_quellen'])}")
        print(f"  Gute Quellenangaben: {len(problems['gute_beispiele'])}")
        
        # Zeige Beispiele
        if problems["leer_daten"]:
            print("\n❌ LEER-Daten Beispiele:")
            for prob in problems["leer_daten"][:3]:
                print(f"  {prob['mine']} - {prob['field']}: {prob['value']}")
        
        if problems["minentyp_praefix"]:
            print("\n❌ Minentyp-Präfix Beispiele:")
            for prob in problems["minentyp_praefix"][:3]:
                print(f"  {prob['mine']}: {prob['value']}")
        
        if problems["gute_beispiele"]:
            print("\n✅ Gute Quellenangaben Beispiele:")
            for example in problems["gute_beispiele"][:2]:
                print(f"  {example['mine']}: {example['quellen_preview']}...")
        
        # Zusammenfassung
        total_problems = len(problems["leer_daten"]) + len(problems["minentyp_praefix"]) + len(problems["leere_quellen"])
        print(f"\n📋 Zusammenfassung: {total_problems} Probleme in {len(results)} Ergebnissen gefunden")
        
        if total_problems > 0:
            print("💡 Diese Probleme sollten durch die neue Bereinigungslogik behoben werden")
        else:
            print("✅ Keine Konsistenz-Probleme gefunden!")
        
    except Exception as e:
        print(f"❌ Fehler beim Test: {str(e)}")

def test_specific_mines():
    """Teste spezifische Minen aus der User-Liste"""
    print("\n🔍 Teste spezifische Minen...")
    
    mines_to_check = [
        "Denain", "Evans (Cameron)", "Barry", "Adsit", "Ahearn", "Aubin",
        "Bagamac", "Baldface", "Adanac", "Foxtrot", "Éléonore", "Aubelle"
    ]
    
    try:
        for mine_name in mines_to_check[:5]:  # Teste ersten 5
            response = requests.get(f"{API_BASE}/api/benchmark/recent?mine_name={mine_name}&limit=1", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("data"):
                    result = data["data"][0]
                    structured_data = result.get("structured_data", {})
                    
                    print(f"\n🏔️ {mine_name}:")
                    print(f"  Eigentümer: {structured_data.get('Eigentümer', 'N/A')}")
                    print(f"  Betreiber: {structured_data.get('Betreiber', 'N/A')}")
                    print(f"  Minentyp: {structured_data.get('Minentyp (Untertage/ Open-Pit/ usw.)', 'N/A')}")
                    print(f"  Aktivitätsstatus: {structured_data.get('Aktivitätsstatus', 'N/A')}")
                    
                    quellenangaben = structured_data.get('Quellenangaben', '')
                    if quellenangaben:
                        print(f"  Quellenangaben: {quellenangaben[:80]}...")
                    else:
                        print(f"  Quellenangaben: LEER")
                else:
                    print(f"🏔️ {mine_name}: Keine Daten gefunden")
            else:
                print(f"🏔️ {mine_name}: API-Fehler")
    
    except Exception as e:
        print(f"❌ Fehler beim Mine-Test: {str(e)}")

def main():
    print("🧪 Test existierender Daten")
    print("=" * 50)
    
    test_existing_data_problems()
    test_specific_mines()
    
    print("\n" + "=" * 50)
    print("✅ Datenanalyse abgeschlossen!")
    print("\n💡 Empfehlung: Nach der Implementierung sollten neue Suchen die bereinigten Werte zeigen")

if __name__ == "__main__":
    main()