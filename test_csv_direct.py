#!/usr/bin/env python3
"""
Direct CSV Test - Teste CSV Service ohne Backend
"""

import sys
import os
sys.path.append('/app/minesearch_v2/backend')

from datetime import datetime
from csv_service import CSVExportService

def test_csv_direct():
    """Teste CSV Service direkt"""
    
    print("🔍 Direct CSV Service Test")
    print("=" * 40)
    
    # Mock-Ergebnis erstellen
    class MockResult:
        def __init__(self, mine_num):
            self.id = mine_num
            self.search_timestamp = datetime.now()
            self.mine_name = f"Quebec Mine {mine_num}"
            self.country = "Canada"
            self.region = "Quebec"
            self.commodity = "Copper"
            self.model_used = "abacus:deep-agent"
            self.search_duration = 30.0 + mine_num
            self.session_id = f"session-{mine_num}"
            self.success = True
            self.error_message = None
            self.structured_data = {
                'owner': f'Mining Company {mine_num}',
                'operator': f'Operator {mine_num}',
                'latitude': f'48.{mine_num:06d}',
                'longitude': f'-78.{mine_num:06d}',
                'mine_type': 'Underground',
                'status': 'Active',
                'restoration_costs': f'{mine_num * 1000000}',
                'restoration_currency': 'CAD',
                'restoration_year': '2023',
                'annual_production': f'{mine_num * 100}',
                'ore_reserves': f'{mine_num * 1000}'
            }
            self.sources = [
                {'url': f'https://source{mine_num}.com', 'type': 'government'},
                {'url': f'https://tech{mine_num}.com', 'type': 'technical'}
            ]
    
    try:
        # CSV Service initialisieren
        csv_service = CSVExportService()
        print(f"✅ CSV Service initialisiert")
        print(f"   Headers: {len(csv_service.get_csv_headers())}")
        print(f"   Delimiter: '{csv_service.delimiter}'")
        
        # Test-Daten erstellen
        results = [MockResult(i) for i in range(1, 4)]  # 3 Test-Minen
        print(f"✅ {len(results)} Test-Ergebnisse erstellt")
        
        # CSV generieren
        csv_content = csv_service.generate_csv_export(results)
        print(f"✅ CSV Content generiert ({len(csv_content)} Zeichen)")
        
        # CSV analysieren
        lines = csv_content.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        
        print(f"\n📊 CSV-Analyse:")
        print(f"   Gesamtzeilen: {len(lines)}")
        print(f"   Nicht-leere Zeilen: {len(non_empty_lines)}")
        
        # Header analysieren
        header = non_empty_lines[0]
        header_fields = header.split('|')
        print(f"   Header-Felder: {len(header_fields)}")
        print(f"   Erste 5 Felder: {header_fields[:5]}")
        
        # Datenzeilen analysieren  
        data_lines = non_empty_lines[1:]
        print(f"   Datenzeilen: {len(data_lines)}")
        
        if data_lines:
            sample_data = data_lines[0].split('|')
            print(f"   Sample-Daten-Felder: {len(sample_data)}")
            
            # Prüfe wichtige Felder
            if len(sample_data) >= len(header_fields):
                print(f"   Mine Name: {sample_data[2]}")
                print(f"   Country: {sample_data[3]}")
                print(f"   Provider: {sample_data[7]}")
                print(f"   Owner: {sample_data[15] if len(sample_data) > 15 else 'N/A'}")
                print(f"   Latitude: {sample_data[17] if len(sample_data) > 17 else 'N/A'}")
        
        # Datei speichern
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'/app/minesearch_results_test_{timestamp}.csv'
        
        with open(filename, 'w', encoding='utf-8-sig') as f:
            f.write(csv_content)
        
        print(f"\n💾 CSV gespeichert: {filename}")
        
        # Validierung
        pipe_count_header = header.count('|')
        expected_pipes = len(header_fields) - 1
        
        print(f"\n✅ Validierung:")
        print(f"   Header Pipes: {pipe_count_header} (erwartet: {expected_pipes})")
        print(f"   Encoding: UTF-8 with BOM")
        print(f"   Delimiter: Pipe (|)")
        
        if pipe_count_header == expected_pipes:
            print("✅ CSV-Format korrekt!")
            return True, filename
        else:
            print("❌ CSV-Format inkorrekt!")
            return False, filename
            
    except Exception as e:
        print(f"❌ CSV Test fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()
        return False, None

if __name__ == "__main__":
    success, filename = test_csv_direct()
    
    if success:
        print(f"\n🎉 CSV-Export Test erfolgreich!")
        print(f"📁 Datei: {filename}")
        print(f"🔧 Tipp: Öffne die Datei mit Excel oder LibreOffice")
        print(f"💡 Bei Excel: Importiere als Text mit Pipe-Trennzeichen")
    else:
        print(f"\n💥 CSV-Export Test fehlgeschlagen!")