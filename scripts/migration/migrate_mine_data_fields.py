#!/usr/bin/env python3
"""
Author: rahn
Datum: 04.09.2025
Version: 1.0
Beschreibung: Schema-Migration für mine_data_fields Tabelle - Füge search_result_id hinzu
"""

import sqlite3
import logging
from minesearch.database.db_utils import get_normalized_db_path, get_sqlite_connection

logger = logging.getLogger(__name__)

def migrate_mine_data_fields():
    """Fügt die search_result_id Spalte zur mine_data_fields Tabelle hinzu"""

    db_path = get_normalized_db_path()

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("🔧 [MIGRATION] Starte Schema-Migration für mine_data_fields...")

        # Prüfe ob search_result_id bereits existiert
        cursor.execute("PRAGMA table_info(mine_data_fields)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]

        if 'search_result_id' in column_names:
            print("✅ [MIGRATION] search_result_id Spalte existiert bereits")
            return

        # Füge die neue Spalte hinzu
        cursor.execute("""
            ALTER TABLE mine_data_fields
            ADD COLUMN search_result_id INTEGER
        """)

        print("✅ [MIGRATION] search_result_id Spalte hinzugefügt")

        # Erstelle Index für bessere Performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_mine_data_fields_search_result_id
            ON mine_data_fields(search_result_id)
        """)

        print("✅ [MIGRATION] Index für search_result_id erstellt")

        # Commit und schließe
        conn.commit()
        conn.close()

        print("🎉 [MIGRATION] Schema-Migration erfolgreich abgeschlossen")

    except Exception as e:
        print(f"❌ [MIGRATION] Fehler bei Schema-Migration: {e}")
        if conn:
            conn.rollback()
            conn.close()
        raise

if __name__ == "__main__":
    migrate_mine_data_fields()
