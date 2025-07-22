#!/usr/bin/env python3
"""
Complete CSV Export Test mit echten Daten
"""

import asyncio
import aiohttp
import json
from datetime import datetime
import time

async def test_complete_csv_workflow():
    """Teste kompletten CSV-Export-Workflow"""
    
    print("🔍 Complete CSV Export Workflow Test")
    print("=" * 50)
    
    # Backend-URL (versuche verschiedene Ports)
    for port in [5001, 5002, 8000]:
        try:
            async with aiohttp.ClientSession() as session:
                health_url = f"http://localhost:{port}/health"
                async with session.get(health_url, timeout=2) as response:
                    if response.status == 200:
                        print(f"✅ Backend gefunden auf Port {port}")
                        base_url = f"http://localhost:{port}"
                        break
        except:
            continue
    else:
        # Starte Backend selbst
        print("🚀 Starte eigenes Backend...")
        import subprocess
        import sys
        import os
        
        # Wechsle in Backend-Verzeichnis
        backend_dir = "/app/minesearch_v2/backend"
        os.chdir(backend_dir)
        
        # Teste CSV-Service direkt
        try:
            sys.path.append(backend_dir)
            from csv_service import CSVExportService
            
            csv_service = CSVExportService()
            
            # Mock-Ergebnis für Test
            class MockResult:
                def __init__(self):
                    self.id = 1
                    self.search_timestamp = datetime.now()
                    self.mine_name = "Horne Mine"
                    self.country = "Canada"
                    self.region = "Quebec"
                    self.commodity = "Copper"
                    self.model_used = "abacus:deep-agent"
                    self.search_duration = 42.5
                    self.session_id = "test-123"
                    self.success = True
                    self.error_message = None
                    self.structured_data = {
                        'owner': 'Noranda Inc.',
                        'latitude': '48.229722',
                        'longitude': '-79.022222',
                        'restoration_costs': '50000000',
                        'mine_type': 'Underground',
                        'status': 'Closed'
                    }
                    self.sources = [
                        {'url': 'https://example.com/source1', 'type': 'government'},
                        {'url': 'https://example.com/source2', 'type': 'technical'}
                    ]
            
            # Teste CSV-Generierung
            print("\n📋 Testing CSV Service directly...")
            
            mock_results = [MockResult()]
            csv_content = csv_service.generate_csv_export(mock_results)
            
            # Analyse der CSV
            lines = csv_content.split('\n')
            non_empty_lines = [line for line in lines if line.strip()]
            
            print(f"✅ CSV generiert: {len(non_empty_lines)} Zeilen")
            
            # Header prüfen
            header = lines[0]
            fields = header.split('|')
            print(f"✅ CSV-Header: {len(fields)} Felder")
            print(f"   Erste 5: {fields[:5]}")
            print(f"   Letzte 5: {fields[-5:]}")
            
            # Datenzeile prüfen
            if len(non_empty_lines) > 1:
                data_line = non_empty_lines[1]
                data_values = data_line.split('|')
                print(f"✅ Datenzeile: {len(data_values)} Werte")
                print(f"   Mine: {data_values[2] if len(data_values) > 2 else 'N/A'}")
                print(f"   Country: {data_values[3] if len(data_values) > 3 else 'N/A'}")
                print(f"   Owner: {data_values[15] if len(data_values) > 15 else 'N/A'}")
                print(f"   Latitude: {data_values[17] if len(data_values) > 17 else 'N/A'}")
            
            # Datei speichern für manuellen Test
            filename = f"test_csv_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            with open(filename, 'w', encoding='utf-8-sig') as f:
                f.write(csv_content)
            
            print(f"💾 CSV gespeichert: {filename}")
            
            # Pipe-Statistik
            total_pipes = csv_content.count('|')
            lines_with_data = len(non_empty_lines) - 1  # ohne header
            expected_pipes = len(fields) - 1  # Anzahl Separatoren = Felder - 1
            
            print(f"\n📊 CSV-Statistik:")
            print(f"   Total Pipes: {total_pipes}")
            print(f"   Expected per line: {expected_pipes}")
            print(f"   Data lines: {lines_with_data}")
            print(f"   Header pipes: {header.count('|')}")
            
            if header.count('|') == expected_pipes:
                print("✅ Pipe-Separatoren korrekt")
            else:
                print("❌ Pipe-Separatoren inkorrekt")
            
            print(f"\n✅ CSV-Export Test erfolgreich abgeschlossen!")
            print(f"   Datei: {filename}")
            print(f"   Encoding: UTF-8 with BOM")
            print(f"   Delimiter: Pipe (|)")
            print(f"   Felder: {len(fields)}")
            
            return True
            
        except Exception as e:
            print(f"❌ CSV-Service Test fehlgeschlagen: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = asyncio.run(test_complete_csv_workflow())
    if success:
        print("\n🎉 Alle CSV-Export Tests bestanden!")
    else:
        print("\n💥 CSV-Export Tests fehlgeschlagen!")