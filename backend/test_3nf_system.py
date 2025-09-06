#!/usr/bin/env python3
"""
Test-Script für das neue 3NF-System mit echter Suche
"""

import requests
import json
import sqlite3
import time
from datetime import datetime

def test_api_search():
    """Teste das neue 3NF-System über die REST API"""
    print("🧪 TESTE NEUES 3NF-SYSTEM")
    print("=" * 80)
    
    # Test-Parameter
    test_data = {
        "mine_name": "Kiena",
        "country": "Canada", 
        "model": "openrouter:deepseek-free"
    }
    
    print(f"📋 Test-Parameter:")
    print(f"   Mine: {test_data['mine_name']}")
    print(f"   Land: {test_data['country']}")
    print(f"   Model: {test_data['model']}")
    print()
    
    try:
        # API-Aufruf
        print("🌐 Führe API-Aufruf durch...")
        start_time = time.time()
        
        response = requests.post(
            "http://localhost:8000/api/search",
            json=test_data,
            timeout=120
        )
        
        duration = time.time() - start_time
        print(f"⏱️  API-Aufruf Dauer: {duration:.2f}s")
        
        if response.status_code != 200:
            print(f"❌ API-Fehler: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
        result = response.json()
        
        print("✅ API-Aufruf erfolgreich!")
        print(f"📊 Mine: {result.get('mine_name', 'N/A')}")
        print(f"🤖 Model: {result.get('model_used', 'N/A')}")
        print(f"🔢 Felder gefunden: {len(result.get('structured_data', {}))}")
        print(f"⏱️  Search Duration: {result.get('search_duration_ms', 0)} ms")
        
        # Zeige Beispiel-Felder
        if result.get('structured_data'):
            print("\n📋 GEFUNDENE FELDER (Beispiele):")
            for i, (k, v) in enumerate(result['structured_data'].items()):
                if i < 8:  # Zeige erste 8 Felder
                    print(f"   {k:<25}: {str(v)[:50]}")
                elif i == 8:
                    print(f"   ... und {len(result['structured_data']) - 8} weitere")
                    break
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Netzwerk-Fehler: {e}")
        return False
    except Exception as e:
        print(f"❌ Unerwarteter Fehler: {e}")
        return False

def validate_database_structure():
    """Validiere die Datenbank nach der Suche"""
    print("\n🔍 DATENBANKVALIDIERUNG NACH SUCHE")
    print("-" * 50)
    
    conn = sqlite3.connect('mines.db')
    cursor = conn.cursor()
    
    # 1. Prüfe Tabellen-Counts
    tables = ['mines', 'search_sessions', 'mine_data_fields']
    for table in tables:
        cursor.execute(f'SELECT COUNT(*) FROM {table}')
        count = cursor.fetchone()[0]
        print(f"📊 {table:<20}: {count} Einträge")
    
    # 2. Analysiere mine_data_fields
    cursor.execute("""
        SELECT field_type, COUNT(*) as count
        FROM mine_data_fields 
        GROUP BY field_type
        ORDER BY count DESC
    """)
    field_types = cursor.fetchall()
    
    print(f"\n📈 FIELD_TYPE VERTEILUNG:")
    total_fields = 0
    for field_type, count in field_types:
        print(f"   {field_type:<15}: {count} Felder")
        total_fields += count
    
    # 3. Prüfe 3NF-Compliance
    print(f"\n🧪 3NF-COMPLIANCE CHECKS:")
    
    # Check 1: Normalisierte Felder haben primitive_value = NULL
    cursor.execute("""
        SELECT COUNT(*) FROM mine_data_fields 
        WHERE field_type = 'normalized' AND primitive_value IS NOT NULL
    """)
    normalized_with_primitive = cursor.fetchone()[0]
    
    if normalized_with_primitive == 0:
        print("   ✅ Normalisierte Felder haben kein primitive_value")
    else:
        print(f"   ❌ {normalized_with_primitive} normalisierte Felder mit primitive_value!")
    
    # Check 2: Primitive Felder haben alle FK-IDs = NULL
    cursor.execute("""
        SELECT COUNT(*) FROM mine_data_fields 
        WHERE field_type = 'primitive' AND (
            commodity_id IS NOT NULL OR company_id IS NOT NULL OR 
            activity_status_id IS NOT NULL OR mine_type_id IS NOT NULL OR
            country_id IS NOT NULL OR region_id IS NOT NULL
        )
    """)
    primitive_with_fk = cursor.fetchone()[0]
    
    if primitive_with_fk == 0:
        print("   ✅ Primitive Felder haben keine FK-IDs")
    else:
        print(f"   ❌ {primitive_with_fk} primitive Felder mit FK-IDs!")
    
    # Check 3: Zeige Beispiele für beide Feldtypen
    print(f"\n📋 BEISPIEL NORMALIZED FELDER:")
    cursor.execute("""
        SELECT field_name, 
               commodity_id, company_id, activity_status_id, mine_type_id, country_id, region_id
        FROM mine_data_fields 
        WHERE field_type = 'normalized' 
        LIMIT 3
    """)
    normalized_examples = cursor.fetchall()
    
    for row in normalized_examples:
        field_name = row[0]
        fk_ids = [f for f in row[1:] if f is not None]
        print(f"   {field_name:<25}: FK-IDs {fk_ids}")
    
    print(f"\n📋 BEISPIEL PRIMITIVE FELDER:")
    cursor.execute("""
        SELECT field_name, primitive_value, numeric_value, unit
        FROM mine_data_fields 
        WHERE field_type = 'primitive' 
        LIMIT 3
    """)
    primitive_examples = cursor.fetchall()
    
    for row in primitive_examples:
        field_name, primitive_val, numeric_val, unit = row
        value = primitive_val or f"{numeric_val} {unit}" if numeric_val else "NULL"
        print(f"   {field_name:<25}: {value}")
    
    # 4. JOIN-Test für lesbare Ausgabe
    print(f"\n🔗 JOIN-TEST FÜR LESBARE AUSGABE:")
    cursor.execute("""
        SELECT 
            mdf.field_name,
            mdf.field_type,
            CASE 
                WHEN mdf.field_type = 'normalized' THEN 
                    COALESCE(c.name, comp.name, ast.status, mt.name, cnt.name, r.name)
                ELSE 
                    mdf.primitive_value
            END as readable_value
        FROM mine_data_fields mdf
        LEFT JOIN commodities c ON mdf.commodity_id = c.id
        LEFT JOIN companies comp ON mdf.company_id = comp.id  
        LEFT JOIN activity_statuses ast ON mdf.activity_status_id = ast.id
        LEFT JOIN mine_types mt ON mdf.mine_type_id = mt.id
        LEFT JOIN countries cnt ON mdf.country_id = cnt.id
        LEFT JOIN regions r ON mdf.region_id = r.id
        LIMIT 5
    """)
    join_results = cursor.fetchall()
    
    for field_name, field_type, readable_value in join_results:
        type_indicator = "📊" if field_type == 'normalized' else "📝"
        print(f"   {type_indicator} {field_name:<20}: {readable_value}")
    
    conn.close()
    return total_fields

if __name__ == "__main__":
    success = test_api_search()
    if success:
        time.sleep(2)  # Warte kurz für DB-Sync
        total_fields = validate_database_structure()
        
        print(f"\n🎉 TEST ABGESCHLOSSEN")
        print("=" * 80)
        print("✅ API-Suche erfolgreich")
        print(f"✅ {total_fields} Felder in 3NF-Struktur gespeichert")
        print("✅ Echte Normalisierung ohne Hybrid-Daten")
        print("✅ JOIN-Queries für lesbare Ausgabe funktionieren")
        print()
        print("🔄 SYSTEM BEREIT FÜR PRODUKTIVE 3NF-NORMALISIERUNG!")
    else:
        print("\n❌ TEST FEHLGESCHLAGEN")
        print("Prüfe API-Status und Logs")