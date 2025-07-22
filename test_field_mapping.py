#!/usr/bin/env python3
"""
Test Field Mapping für CSV Export
"""

import requests
import csv
from io import StringIO

def test_csv_export_with_field_mapping():
    """Test CSV Export mit neuem Field Mapping"""
    
    print("🔍 Testing CSV Export with Field Mapping")
    print("=" * 50)
    
    # CSV Export abrufen
    response = requests.get("http://localhost:8000/api/results/export/csv")
    
    if response.status_code == 200:
        csv_content = response.text
        
        # CSV parsen
        csv_reader = csv.DictReader(StringIO(csv_content), delimiter='|')
        
        print(f"✅ CSV erfolgreich geladen")
        
        # Analysiere jede Mine
        mines_with_data = 0
        
        for row in csv_reader:
            mine_name = row.get('mine_name', '')
            owner = row.get('owner', '')
            operator = row.get('operator', '')
            status = row.get('status', '')
            latitude = row.get('latitude', '')
            production_start = row.get('production_start', '')
            
            # Zähle Minen mit Daten
            if any([owner, operator, status, latitude, production_start]):
                mines_with_data += 1
                print(f"\n📊 {mine_name}:")
                if owner: print(f"   Owner: {owner}")
                if operator: print(f"   Operator: {operator}")
                if status: print(f"   Status: {status}")
                if latitude: print(f"   Latitude: {latitude}")
                if production_start: print(f"   Production Start: {production_start}")
        
        print(f"\n✅ Gefunden: {mines_with_data} Minen mit extrahierten Daten")
        
        # Speichere verbesserten CSV für Inspektion
        with open('/app/improved_mining_export.csv', 'w', encoding='utf-8-sig') as f:
            f.write(csv_content)
        
        print(f"💾 Vollständiger CSV gespeichert: /app/improved_mining_export.csv")
        
    else:
        print(f"❌ CSV Export fehlgeschlagen: {response.status_code}")

if __name__ == "__main__":
    test_csv_export_with_field_mapping()