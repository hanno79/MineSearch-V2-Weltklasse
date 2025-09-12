#!/usr/bin/env python3
"""
Author: rahn
Datum: 13.07.2025
Version: 1.0
Beschreibung: Datenbank-Bereinigung - Entfernt Statistik- und Ergebnis-Daten, behält Sources
"""

import sqlite3
from minesearch.database.db_utils import get_normalized_db_path, get_sqlite_connection

def clean_database():
    """clean_database - TODO: Dokumentation hinzufügen"""
    print('🗑️ Bereinige Statistik- und Ergebnis-Tabellen...')

    # Verbinde zur Datenbank
    conn = sqlite3.connect(get_normalized_db_path())
    cursor = conn.cursor()

    # Statistik-Tabellen leeren
    tables_to_clear = [
        'model_statistics',
        'model_summary',
        'field_statistics',
        'field_consistency',
        'search_results',
        'mines'
    ]

    for table in tables_to_clear:
        try:
            cursor.execute(f'DELETE FROM {table}')
            print(f'✅ {table} geleert')
        except Exception as e:
            print(f'❌ Fehler bei {table}: {e}')

    # Sources beibehalten
    cursor.execute('SELECT COUNT(*) FROM sources')
    sources_count = cursor.fetchone()[0]
    print(f'📦 sources: {sources_count} Einträge BEIBEHALTEN')

    # Änderungen speichern
    conn.commit()

    # Validierung
    print('\n🔍 Validierung nach Bereinigung:')
    for table in tables_to_clear + ['sources']:
        try:
            cursor.execute(f'SELECT COUNT(*) FROM {table}')
            count = cursor.fetchone()[0]
            if table == 'sources' and count > 0:
                status = '✅'
            elif table != 'sources' and count == 0:
                status = '✅'
            else:
                status = '❌'
            print(f'{status} {table}: {count} Einträge')
        except Exception as e:
            print(f'❌ {table}: Fehler - {e}')

    conn.close()
    print('\n✅ Datenbank-Bereinigung abgeschlossen!')

if __name__ == "__main__":
    clean_database()
