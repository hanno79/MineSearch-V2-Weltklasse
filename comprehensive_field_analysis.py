#!/usr/bin/env python3
"""
Comprehensive Field Analysis für MineSearch v2
Analysiert alle extrahierten und verfügbaren Felder
"""

import sqlite3
import json
import requests
import csv
from io import StringIO

def analyze_database_fields():
    """Analysiere alle Felder in der Datenbank"""
    
    print("📊 COMPREHENSIVE FIELD ANALYSIS")
    print("=" * 60)
    
    conn = sqlite3.connect('/app/minesearch_v2/backend/mines.db')
    cursor = conn.cursor()
    
    # Hole alle strukturierten Daten
    cursor.execute('SELECT mine_name, structured_data FROM search_results ORDER BY id')
    results = cursor.fetchall()
    
    all_fields = set()
    field_stats = {}
    mines_with_data = {}
    
    for mine_name, structured_data_json in results:
        if structured_data_json:
            structured_data = json.loads(structured_data_json)
            mines_with_data[mine_name] = structured_data
            
            for field, value in structured_data.items():
                all_fields.add(field)
                
                if field not in field_stats:
                    field_stats[field] = {'total': 0, 'filled': 0, 'x_marked': 0, 'empty': 0}
                
                field_stats[field]['total'] += 1
                
                if value and str(value).strip():
                    if str(value) == 'X':
                        field_stats[field]['x_marked'] += 1
                    else:
                        field_stats[field]['filled'] += 1
                else:
                    field_stats[field]['empty'] += 1
    
    print(f"📋 DATENBANK FELDER ANALYSE:")
    print(f"   Minen insgesamt: {len(results)}")
    print(f"   Minen mit Daten: {len(mines_with_data)}")
    print(f"   Einzigartige Felder: {len(all_fields)}")
    
    print(f"\n🔍 FELD-STATISTIKEN:")
    print("-" * 80)
    print(f"{'Feldname':<40} {'Gefüllt':<8} {'X-Markiert':<12} {'Leer':<8} {'Rate':<8}")
    print("-" * 80)
    
    for field in sorted(all_fields):
        if field in field_stats:
            stats = field_stats[field]
            fill_rate = f"{(stats['filled'] / stats['total']) * 100:.1f}%" if stats['total'] > 0 else "0%"
            print(f"{field:<40} {stats['filled']:<8} {stats['x_marked']:<12} {stats['empty']:<8} {fill_rate:<8}")
    
    # Zeige Beispieldaten für Mine mit den meisten Daten
    print(f"\n💎 BEISPIEL - BEST GEFÜLLTE MINE:")
    best_mine = None
    best_filled_count = 0
    
    for mine_name, data in mines_with_data.items():
        filled_count = sum(1 for v in data.values() if v and str(v).strip() and str(v) != 'X')
        if filled_count > best_filled_count:
            best_filled_count = filled_count
            best_mine = mine_name
    
    if best_mine:
        print(f"   Mine: {best_mine} ({best_filled_count} gefüllte Felder)")
        data = mines_with_data[best_mine]
        for field, value in data.items():
            if value and str(value).strip() and str(value) != 'X':
                print(f"     {field}: {value}")
    
    conn.close()
    return all_fields, field_stats

def analyze_csv_export():
    """Analysiere aktuellen CSV-Export"""
    
    print(f"\n📤 CSV-EXPORT ANALYSE:")
    print("-" * 40)
    
    response = requests.get("http://localhost:8000/api/results/export/csv")
    
    if response.status_code == 200:
        csv_content = response.text
        csv_reader = csv.DictReader(StringIO(csv_content), delimiter='|')
        
        headers = csv_reader.fieldnames
        print(f"   CSV Headers: {len(headers)} Felder")
        
        rows = list(csv_reader)
        print(f"   CSV Zeilen: {len(rows)} Minen")
        
        # Analysiere Feldabdeckung
        field_coverage = {}
        for header in headers:
            filled_count = sum(1 for row in rows if row.get(header, '').strip())
            field_coverage[header] = filled_count
        
        print(f"\n🎯 CSV FELD-ABDECKUNG:")
        print("-" * 50)
        print(f"{'Feldname':<25} {'Gefüllt':<8} {'Rate':<8}")
        print("-" * 50)
        
        for field, count in sorted(field_coverage.items(), key=lambda x: x[1], reverse=True):
            rate = f"{(count / len(rows)) * 100:.1f}%" if len(rows) > 0 else "0%"
            print(f"{field:<25} {count:<8} {rate:<8}")
        
        return headers, field_coverage
    else:
        print(f"   ❌ CSV-Export fehlgeschlagen: {response.status_code}")
        return [], {}

def compare_fields(db_fields, csv_headers):
    """Vergleiche Datenbank-Felder mit CSV-Headers"""
    
    print(f"\n🔄 FELD-MAPPING ANALYSE:")
    print("-" * 40)
    
    # Deutsche Felder aus der DB
    german_fields = [f for f in db_fields if any(c in f for c in 'äöüÄÖÜß') or 'Koordinate' in f or 'Mine' in f]
    english_fields = [f for f in db_fields if f not in german_fields]
    
    print(f"   Deutsche DB-Felder: {len(german_fields)}")
    print(f"   Englische DB-Felder: {len(english_fields)}")
    print(f"   CSV-Header: {len(csv_headers)}")
    
    print(f"\n📋 DEUTSCHE FELDER (DB):")
    for field in sorted(german_fields):
        print(f"     • {field}")
    
    print(f"\n📋 CSV-HEADER:")
    for header in sorted(csv_headers):
        print(f"     • {header}")
    
    # Fehlende Mappings
    print(f"\n⚠️  POTENTIELLE PROBLEME:")
    
    important_german_fields = [
        'Restaurationskosten', 'Jahr der Aufnahme der Kosten',
        'Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)', 
        'Fördermenge/Jahr', 'Fläche der Mine in qkm'
    ]
    
    for field in important_german_fields:
        if field in db_fields:
            print(f"     • '{field}' sollte im CSV gemappt werden")

if __name__ == "__main__":
    db_fields, field_stats = analyze_database_fields()
    csv_headers, field_coverage = analyze_csv_export()
    compare_fields(db_fields, csv_headers)
    
    print(f"\n✅ ANALYSE ABGESCHLOSSEN")
    print(f"   Vollständiger Report verfügbar für weitere Optimierungen")