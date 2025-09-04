#!/usr/bin/env python3
"""
Author: rahn
Datum: 04.09.2025
Version: 1.0
Beschreibung: Test der echten Suchfunktion nach Schema-Migration
"""

import sys
sys.path.insert(0, 'backend')

import asyncio
from datetime import datetime
from minesearch.data_extraction import DataExtractor

async def test_real_search():
    """Testet die echte Suchfunktion mit normalisierter Datenbank"""
    
    print("🧪 [TEST] Teste echte Suchfunktion nach Schema-Migration...")
    
    try:
        # Test-Daten für eine realistische Mine
        test_mine_name = 'Test Mine Real Search'
        test_model = 'test-model-real'
        test_structured_data = {
            'Country': 'Australien',
            'Region': 'Western Australia', 
            'Minentyp': 'Underground',
            'Aktivitätsstatus': 'Aktiv',
            'Hauptrohstoff': 'Gold',
            'Eigentümer': 'Test Mining Real Corp',
            'Betreiber': 'Test Operations Ltd',
            'Produktionsbeginn': '2020',
            'Fördermenge/Jahr': '150.000 oz Gold'
        }
        test_sources = [
            {'name': 'Mining Journal', 'url': 'http://mining-journal.com/test'},
            {'name': 'Company Report', 'url': 'http://company.com/report'}
        ]
        
        # Erstelle DataExtractor und speichere über die echte Funktion
        extractor = DataExtractor()
        
        session_id = f'real_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        
        print(f"📝 [TEST] Speichere mit session_id: {session_id}")
        print(f"📝 [TEST] Mine: {test_mine_name}")
        print(f"📝 [TEST] Felder: {len(test_structured_data)}")
        
        result_id = extractor.save_to_normalized_database(
            mine_name=test_mine_name,
            model_used=test_model,
            structured_data=test_structured_data,
            sources=test_sources,
            session_id=session_id,
            country='Australien',
            search_duration=2.3
        )
        
        print(f"✅ [TEST] Speicherung erfolgreich - Search Result ID: {result_id}")
        
        # Prüfe ob Daten in mine_data_fields ankommen
        import sqlite3
        conn = sqlite3.connect(get_normalized_db_path())
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM mine_data_fields WHERE search_result_id = ?', (result_id,))
        count = cursor.fetchone()[0]
        print(f"📊 [TEST] {count} Feldwerte in mine_data_fields gespeichert")
        
        if count > 0:
            print("\n🎯 [TEST] Gespeicherte Feldwerte:")
            cursor.execute('''
                SELECT field_name, raw_value, normalized_value, model_used 
                FROM mine_data_fields 
                WHERE search_result_id = ?
                ORDER BY field_name
            ''', (result_id,))
            
            for row in cursor.fetchall():
                print(f"  - {row[0]}: '{row[1]}' (normalized: '{row[2]}', model: {row[3]})")
                
        # Prüfe auch search_sessions
        cursor.execute('SELECT session_id, mine_id FROM search_sessions WHERE id = ?', (result_id,))
        session_row = cursor.fetchone()
        if session_row:
            print(f"\n✅ [TEST] Search Session: {session_row[0]} (Mine ID: {session_row[1]})")
        
        conn.close()
        
        return count > 0
        
    except Exception as e:
        print(f"❌ [TEST] Fehler beim Test: {e}")
        import traceback
from minesearch.database.db_utils import get_normalized_db_path, get_sqlite_connection
        traceback.print_exc()
        return False

# Run the test
if __name__ == "__main__":
    result = asyncio.run(test_real_search())
    print(f"\n🏁 [TEST] Echte Suchfunktion: {'✅ ERFOLGREICH' if result else '❌ FEHLGESCHLAGEN'}")