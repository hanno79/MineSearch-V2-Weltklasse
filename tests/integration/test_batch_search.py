#!/usr/bin/env python3
"""
Author: rahn
Datum: 04.09.2025
Version: 1.0
Beschreibung: Test der Batch-Suche nach Schema-Migration
"""

import sys
sys.path.insert(0, 'backend')

import asyncio
from datetime import datetime
from minesearch.data_extraction import DataExtractor

def test_batch_save():
    """Testet Batch-ähnliche Speicherung (simuliert den Batch-Workflow)"""
    
    print("🧪 [BATCH-TEST] Teste Batch-ähnliche Speicherung...")
    
    # Simuliere 3 Mining-Ergebnisse wie bei einer Batch-Suche
    test_mines = [
        {
            'mine_name': 'Batch Test Mine 1',
            'country': 'Chile',
            'model': 'batch-test-model-1',
            'data': {
                'Country': 'Chile',
                'Region': 'Antofagasta',
                'Aktivitätsstatus': 'Aktiv',
                'Hauptrohstoff': 'Kupfer',
                'Minentyp': 'Open-Pit'
            }
        },
        {
            'mine_name': 'Batch Test Mine 2', 
            'country': 'Peru',
            'model': 'batch-test-model-2',
            'data': {
                'Country': 'Peru',
                'Region': 'Cajamarca',
                'Aktivitätsstatus': 'Aktiv',
                'Hauptrohstoff': 'Gold',
                'Eigentümer': 'Newmont Corporation'
            }
        },
        {
            'mine_name': 'Batch Test Mine 3',
            'country': 'Canada',
            'model': 'batch-test-model-3', 
            'data': {
                'Country': 'Canada',
                'Region': 'Ontario',
                'Aktivitätsstatus': 'Geschlossen',
                'Hauptrohstoff': 'Nickel',
                'Produktionsende': '2019'
            }
        }
    ]
    
    extractor = DataExtractor()
    saved_results = []
    
    try:
        for mine in test_mines:
            session_id = f'batch_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}_{mine["mine_name"].replace(" ", "_")}'
            
            print(f"📝 [BATCH-TEST] Speichere: {mine['mine_name']}")
            
            result_id = extractor.save_to_normalized_database(
                mine_name=mine['mine_name'],
                model_used=mine['model'],
                structured_data=mine['data'],
                sources=[{'name': f"Test Source for {mine['mine_name']}", 'url': 'http://example.com'}],
                session_id=session_id,
                country=mine['country'],
                search_duration=1.8
            )
            
            saved_results.append(result_id)
            print(f"✅ [BATCH-TEST] {mine['mine_name']} gespeichert - ID: {result_id}")
        
        # Prüfe Gesamtergebnis - DB-Verbindung über zentrales Config-System
        import sys
        sys.path.append('/app/backend')
        from minesearch.database.db_utils import get_sqlite_connection
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        
        total_fields = 0
        for result_id in saved_results:
            cursor.execute('SELECT COUNT(*) FROM mine_data_fields WHERE search_result_id = ?', (result_id,))
            count = cursor.fetchone()[0]
            total_fields += count
            print(f"📊 [BATCH-TEST] Search Result {result_id}: {count} Feldwerte")
        
        print(f"\n🎯 [BATCH-TEST] Gesamt: {total_fields} Feldwerte von {len(test_mines)} Minen")
        
        # Zeige Beispiel-Daten
        if total_fields > 0:
            print("\n📋 [BATCH-TEST] Beispiel gespeicherte Feldwerte:")
            cursor.execute("""
                SELECT m.name as mine_name, mdf.field_name, mdf.normalized_value, mdf.model_used
                FROM mine_data_fields mdf
                JOIN search_sessions ss ON mdf.search_result_id = ss.id
                JOIN mines m ON ss.mine_id = m.id
                WHERE mdf.model_used LIKE 'batch-test-model-%'
                ORDER BY m.name, mdf.field_name
                LIMIT 10
            """)
            
            for row in cursor.fetchall():
                print(f"  - {row[0]}: {row[1]} = '{row[2]}' (Model: {row[3]})")
        
        conn.close()
        
        return total_fields > 0
        
    except Exception as e:
        print(f"❌ [BATCH-TEST] Fehler: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_batch_save()
    print(f"\n🏁 [BATCH-TEST] Batch-Speicherung: {'✅ ERFOLGREICH' if success else '❌ FEHLGESCHLAGEN'}")