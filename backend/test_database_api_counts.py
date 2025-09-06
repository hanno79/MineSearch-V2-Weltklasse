#!/usr/bin/env python3
"""
Author: rahn
Datum: 06.09.2025
Version: 1.0
Beschreibung: Testet die Database API Counts nach der Aktualisierung
"""

import requests
import json
from time import sleep

def test_database_api_counts():
    """Testet die Database API /tables Endpoint"""
    
    print("🧪 TESTE DATABASE API COUNTS")
    print("=" * 60)
    
    try:
        # 1. Warte bis API verfügbar ist
        print("1. Warte auf API-Verfügbarkeit...")
        
        max_retries = 10
        for i in range(max_retries):
            try:
                response = requests.get("http://localhost:8000/api/database/tables", timeout=5)
                if response.status_code == 200:
                    print(f"   ✅ API verfügbar nach {i+1} Versuchen")
                    break
                else:
                    print(f"   ❌ API Response Code: {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"   Versuch {i+1}: API nicht erreichbar - {e}")
                sleep(2)
        else:
            print("   ❌ API nicht verfügbar nach 10 Versuchen")
            return False
        
        # 2. Teste /tables Endpoint
        print("\n2. Teste /api/database/tables Endpoint...")
        
        response = requests.get("http://localhost:8000/api/database/tables")
        
        if response.status_code != 200:
            print(f"   ❌ API Fehler: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        data = response.json()
        
        if not data.get('success'):
            print(f"   ❌ API Success=False: {data}")
            return False
        
        print(f"   ✅ API Response erfolgreich")
        
        # 3. Analysiere Tables Response
        tables = data.get('tables', [])
        categories = data.get('categories', {})
        
        print(f"\n3. Analysiere Tables Response:")
        print(f"   📊 Total Tables: {len(tables)}")
        print(f"   📊 Categories: {len(categories)}")
        
        # 4. Prüfe spezifische Count-Problems
        print(f"\n4. Prüfe Count-Anzeige für wichtige Tabellen:")
        
        important_tables = [
            'countries', 'regions', 'commodities', 'companies', 
            'activity_statuses', 'mine_types', 'mines', 'mine_data_fields'
        ]
        
        count_errors = []
        
        for table_info in tables:
            table_name = table_info.get('name')
            row_count = table_info.get('row_count', 0)
            
            if table_name in important_tables:
                if row_count == 0:
                    print(f"   ⚠️  {table_name:<20}: {row_count} (ZEIGT NULL OBWOHL DATEN VORHANDEN?)")
                    count_errors.append(table_name)
                else:
                    print(f"   ✅ {table_name:<20}: {row_count}")
        
        # 5. Prüfe Kategorisierung
        print(f"\n5. Prüfe Kategorisierung:")
        
        for category, table_list in categories.items():
            print(f"   📂 {category}: {len(table_list)} Tabellen")
            for table in table_list[:3]:  # Erste 3
                print(f"     - {table}")
            if len(table_list) > 3:
                print(f"     - ... und {len(table_list) - 3} weitere")
        
        # 6. Frontend-spezifische Prüfung
        print(f"\n6. Frontend Count-Display Simulation:")
        
        frontend_display = []
        
        for table_info in tables:
            table_name = table_info.get('name')
            row_count = table_info.get('row_count', 0)
            category = table_info.get('category', 'Unknown')
            
            # Simuliere Frontend-Format
            display_text = f"{table_name} ({row_count})"
            frontend_display.append({
                'name': table_name,
                'display': display_text,
                'count': row_count,
                'category': category
            })
            
            if row_count == 0 and table_name in important_tables:
                print(f"   ⚠️  Frontend würde zeigen: '{display_text}' - PROBLEM!")
            elif table_name in important_tables:
                print(f"   ✅ Frontend würde zeigen: '{display_text}' - OK")
        
        # 7. Fazit
        print(f"\n🎯 FAZIT:")
        
        if count_errors:
            print(f"   ❌ {len(count_errors)} Tabellen zeigen (0) obwohl Daten vorhanden:")
            for error_table in count_errors:
                print(f"     - {error_table}")
            print(f"   🔧 Frontend Count-Problem BESTÄTIGT - API-Update notwendig")
            return False
        else:
            print(f"   ✅ Alle wichtigen Tabellen zeigen korrekte Counts")
            print(f"   ✅ Frontend Count-Problem BEHOBEN")
            return True
        
    except Exception as e:
        print(f"❌ Fehler beim API-Test: {e}")
        return False

if __name__ == "__main__":
    success = test_database_api_counts()
    
    if success:
        print(f"\n🎉 DATABASE API COUNT-TEST ERFOLGREICH!")
        print("✅ Frontend sollte jetzt korrekte Counts anzeigen")
    else:
        print(f"\n❌ DATABASE API COUNT-TEST FEHLGESCHLAGEN")
        print("🔧 Weitere Fixes erforderlich")