#!/usr/bin/env python3
"""
Simple CSV Export Test
Teste CSV-Export-Funktionalität direkt
"""

import asyncio
import aiohttp
import json
from datetime import datetime

async def test_csv_export():
    """Test CSV-Export mit echten Daten"""
    
    base_url = "http://localhost:5001"
    csv_url = f"{base_url}/api/results/export/csv"
    
    print("🔍 Testing CSV Export Functionality")
    print("=" * 50)
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test 1: CSV Export ohne Filter
            print("\n1. Testing CSV Export ohne Filter...")
            async with session.get(csv_url) as response:
                print(f"Status: {response.status}")
                print(f"Content-Type: {response.headers.get('Content-Type')}")
                print(f"Content-Disposition: {response.headers.get('Content-Disposition')}")
                
                if response.status == 200:
                    content = await response.text()
                    lines = content.split('\n')
                    print(f"✅ CSV generiert: {len(lines)} Zeilen")
                    
                    # Header prüfen
                    if lines:
                        header = lines[0]
                        print(f"Header: {header[:100]}...")
                        
                        # Pipe-Separatoren prüfen
                        if '|' in header:
                            print("✅ Pipe-Separatoren gefunden")
                            fields = header.split('|')
                            print(f"✅ {len(fields)} CSV-Felder erkannt")
                            print(f"Erste 5 Felder: {fields[:5]}")
                        else:
                            print("❌ Keine Pipe-Separatoren im Header")
                    
                    # Sample Content (erste Datenzeile)
                    if len(lines) > 1 and lines[1].strip():
                        sample_line = lines[1]
                        print(f"Sample Datenzeile: {sample_line[:100]}...")
                    else:
                        print("ℹ️ Keine Datenzeilen (leere Datenbank)")
                        
                else:
                    error_text = await response.text()
                    print(f"❌ CSV Export fehlgeschlagen: {error_text}")
            
            # Test 2: CSV Export mit Filtern
            print("\n2. Testing CSV Export mit Filtern...")
            params = {
                'days_back': '365',
                'exclude_exa': 'true',
                'sort_by': 'timestamp',
                'order': 'desc'
            }
            
            async with session.get(csv_url, params=params) as response:
                if response.status == 200:
                    content = await response.text()
                    lines = content.split('\n')
                    print(f"✅ Gefilterte CSV: {len(lines)} Zeilen")
                else:
                    error_text = await response.text()
                    print(f"❌ Gefilterter Export fehlgeschlagen: {error_text}")
                    
        print(f"\n✅ CSV Export Test abgeschlossen: {datetime.now().strftime('%H:%M:%S')}")
        
    except Exception as e:
        print(f"❌ Test Fehler: {e}")

if __name__ == "__main__":
    asyncio.run(test_csv_export())