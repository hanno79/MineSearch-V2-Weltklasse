#!/usr/bin/env python3
"""
Author: rahn
Datum: 04.09.2025
Version: 1.0
Beschreibung: Vollständige Schema-Migration für mine_data_fields - Erweitere auf normalisiertes Schema
"""

import sqlite3
import logging
from minesearch.database.db_utils import get_normalized_db_path, get_sqlite_connection

logger = logging.getLogger(__name__)

def migrate_mine_data_fields_full():
    """Erweitert mine_data_fields auf vollständiges normalisiertes Schema"""

    db_path = get_normalized_db_path()

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("🔧 [MIGRATION] Starte vollständige Schema-Migration für mine_data_fields...")

        # Prüfe aktuelle Spalten
        cursor.execute("PRAGMA table_info(mine_data_fields)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]

        print(f"📊 [MIGRATION] Aktuelle Spalten: {column_names}")

        # Füge fehlende Spalten hinzu
        new_columns = [
            ("raw_value", "TEXT"),
            ("normalized_value", "TEXT"),
            ("numeric_value", "REAL"),
            ("unit", "TEXT"),
            ("confidence_score", "REAL"),
            ("is_template_value", "BOOLEAN DEFAULT 0"),
            ("validation_status", "TEXT DEFAULT 'valid'"),
            ("source_name", "TEXT"),
            ("model_used", "TEXT")
        ]

        for col_name, col_type in new_columns:
            if col_name not in column_names:
                cursor.execute(f"ALTER TABLE mine_data_fields ADD COLUMN {col_name} {col_type}")
                print(f"✅ [MIGRATION] Spalte {col_name} hinzugefügt")
            else:
                print(f"⏭️ [MIGRATION] Spalte {col_name} existiert bereits")

        # Migriere bestehende Daten wenn vorhanden
        cursor.execute("SELECT COUNT(*) FROM mine_data_fields")
        existing_count = cursor.fetchone()[0]

        if existing_count > 0:
            print(f"📦 [MIGRATION] Migriere {existing_count} bestehende Einträge...")

            # Setze raw_value = field_value für bestehende Einträge
            cursor.execute("""
                UPDATE mine_data_fields
                SET raw_value = field_value,
                    normalized_value = field_value,
                    confidence_score = confidence,
                    model_used = model_id,
                    validation_status = 'migrated'
                WHERE raw_value IS NULL
            """)

            migrated_count = cursor.rowcount
            print(f"✅ [MIGRATION] {migrated_count} Einträge migriert")

        # Erstelle Indizes für bessere Performance
        indexes = [
            ("idx_mine_data_fields_search_result", "search_result_id"),
            ("idx_mine_data_fields_mine", "mine_id"),
            ("idx_mine_data_fields_field", "field_name"),
            ("idx_mine_data_fields_model", "model_used")
        ]

        for idx_name, col_name in indexes:
            try:
                cursor.execute(f"""
                    CREATE INDEX IF NOT EXISTS {idx_name}
                    ON mine_data_fields({col_name})
                """)
                print(f"✅ [MIGRATION] Index {idx_name} erstellt")
            except Exception as e:
                print(f"⚠️ [MIGRATION] Index {idx_name} Fehler: {e}")

        # Commit und schließe
        conn.commit()

        # Verifiziere neue Struktur
        cursor.execute("PRAGMA table_info(mine_data_fields)")
        new_columns_result = cursor.fetchall()
        new_column_names = [col[1] for col in new_columns_result]

        print(f"📊 [MIGRATION] Neue Spalten: {new_column_names}")
        print(f"🎉 [MIGRATION] Schema-Migration erfolgreich abgeschlossen")

        conn.close()
        return True

    except Exception as e:
        print(f"❌ [MIGRATION] Fehler bei Schema-Migration: {e}")
        if conn:
            conn.rollback()
            conn.close()
        raise

if __name__ == "__main__":
    migrate_mine_data_fields_full()
