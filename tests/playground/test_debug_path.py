#!/usr/bin/env python3
"""
Author: rahn
Datum: 04.09.2025
Version: 1.0
Beschreibung: Debug welcher Code-Pfad genommen wird
"""

import sys
sys.path.insert(0, 'backend')

import logging
logging.basicConfig(level=logging.DEBUG)

from minesearch.database.normalized_manager import NormalizedDatabaseManager

def test_debug_path():
    """Testet welcher Pfad in save_mine_field_data genommen wird"""
    
    print("🐛 [DEBUG-PATH] Test welcher Code-Pfad genommen wird...")
    
    db_manager = NormalizedDatabaseManager()
    
    # Test-Daten
    test_data = {
        'Country': 'Debug-Test-Land',
        'Region': 'Debug-Test-Region'
    }
    
    print("🔍 [DEBUG-PATH] Rufe save_mine_field_data OHNE db_session auf...")
    
    # Ohne db_session - sollte den ELSE-Pfad nehmen
    db_manager.save_mine_field_data(
        mine_id=8,
        search_result_id=8,  
        structured_data=test_data,
        model_used='debug-path-test',
        sources=[]
    )
    
    print("✅ [DEBUG-PATH] save_mine_field_data beendet")
    
    # Prüfe Ergebnis
    import sqlite3
from minesearch.database.db_utils import get_normalized_db_path, get_sqlite_connection
    conn = sqlite3.connect(get_normalized_db_path())
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM mine_data_fields WHERE model_used = ?', ('debug-path-test',))
    count = cursor.fetchone()[0]
    print(f"📊 [DEBUG-PATH] {count} Einträge mit model_used='debug-path-test'")
    
    if count > 0:
        cursor.execute('SELECT field_name, raw_value FROM mine_data_fields WHERE model_used = ?', ('debug-path-test',))
        for row in cursor.fetchall():
            print(f"  - {row[0]}: '{row[1]}'")
    
    conn.close()
    return count > 0

if __name__ == "__main__":
    success = test_debug_path()
    print(f"🎯 [DEBUG-PATH] Test: {'✅ ERFOLGREICH' if success else '❌ FEHLGESCHLAGEN'}")