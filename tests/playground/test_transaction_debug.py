#!/usr/bin/env python3
"""
Author: rahn
Datum: 04.09.2025
Version: 1.0
Beschreibung: Detailliertes Transaktions-Debugging
"""

import sys
sys.path.insert(0, 'backend')

import logging
logging.basicConfig(level=logging.DEBUG)

from minesearch.database.normalized_manager import NormalizedDatabaseManager
from sqlalchemy import text

def test_transaction_debug():
    """Testet Transaktionen und Commits sehr detailliert"""
    
    print("🔍 [TRANSACTION-DEBUG] Detailliertes Transaktions-Debugging...")
    
    db_manager = NormalizedDatabaseManager()
    
    # Test-Daten
    test_data = {
        'Country': 'Transaction-Test-Land',
        'Region': 'Transaction-Test-Region'
    }
    
    try:
        # 1. Teste mit eigener Session (wie im ELSE-Zweig)
        print("\n📊 [TRANSACTION-DEBUG] Teste mit eigener Session...")
        
        with db_manager.get_session() as session:
            print("✅ [TRANSACTION-DEBUG] Session erstellt")
            
            # Manueller INSERT wie in der save_mine_field_data Funktion
            for field_name, field_value in test_data.items():
                if not field_value:
                    continue
                    
                print(f"📝 [TRANSACTION-DEBUG] Füge ein: {field_name} = {field_value}")
                
                session.execute(text("""
                    INSERT INTO mine_data_fields (
                        search_result_id, mine_id, field_name, raw_value, normalized_value,
                        numeric_value, unit, confidence_score, is_template_value,
                        validation_status, source_name, model_used
                    ) VALUES (
                        :search_result_id, :mine_id, :field_name, :raw_value, :normalized_value,
                        :numeric_value, :unit, :confidence_score, :is_template_value,
                        :validation_status, :source_name, :model_used
                    )
                """), {
                    'search_result_id': 8,
                    'mine_id': 8,
                    'field_name': field_name,
                    'raw_value': field_value,
                    'normalized_value': field_value,
                    'numeric_value': None,
                    'unit': None,
                    'confidence_score': 0.9,
                    'is_template_value': False,
                    'validation_status': 'valid',
                    'source_name': 'transaction-test',
                    'model_used': 'transaction-test-model'
                })
                
            print("💾 [TRANSACTION-DEBUG] Daten eingefügt, vor Commit...")
            
            # Prüfe in derselben Session
            result = session.execute(text("""
                SELECT COUNT(*) FROM mine_data_fields WHERE model_used = 'transaction-test-model'
            """))
            count_before_commit = result.fetchone()[0]
            print(f"📊 [TRANSACTION-DEBUG] Vor Commit in derselben Session: {count_before_commit} Einträge")
            
            # Commit
            session.commit()
            print("✅ [TRANSACTION-DEBUG] Session committed")
            
            # Prüfe nach Commit in derselben Session
            result = session.execute(text("""
                SELECT COUNT(*) FROM mine_data_fields WHERE model_used = 'transaction-test-model'
            """))
            count_after_commit = result.fetchone()[0]
            print(f"📊 [TRANSACTION-DEBUG] Nach Commit in derselben Session: {count_after_commit} Einträge")
        
        # 2. Prüfe mit neuer Session (wie wenn man von außen schaut)
        print("\n🔍 [TRANSACTION-DEBUG] Prüfe mit neuer Session...")
        
        import sqlite3
        conn = sqlite3.connect(get_normalized_db_path())
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM mine_data_fields WHERE model_used = ?', ('transaction-test-model',))
        count_external = cursor.fetchone()[0]
        print(f"📊 [TRANSACTION-DEBUG] Von externer SQLite Verbindung: {count_external} Einträge")
        
        if count_external > 0:
            cursor.execute('SELECT field_name, raw_value FROM mine_data_fields WHERE model_used = ?', ('transaction-test-model',))
            print("📋 [TRANSACTION-DEBUG] Gefundene Einträge:")
            for row in cursor.fetchall():
                print(f"  - {row[0]}: '{row[1]}'")
        
        conn.close()
        
        return count_external > 0
        
    except Exception as e:
        print(f"❌ [TRANSACTION-DEBUG] Fehler: {e}")
        import traceback
from minesearch.database.db_utils import get_normalized_db_path, get_sqlite_connection
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_transaction_debug()
    print(f"\n🎯 [TRANSACTION-DEBUG] Test: {'✅ ERFOLGREICH' if success else '❌ FEHLGESCHLAGEN'}")