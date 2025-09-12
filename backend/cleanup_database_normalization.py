#!/usr/bin/env python3
"""
Author: rahn
Datum: 06.09.2025
Version: 1.0
Beschreibung: Bereinigt die Datenbank und entfernt Legacy-Tabellen
"""

import sqlite3
from datetime import datetime

def cleanup_database():
    """Entfernt Legacy-Tabellen und behält nur normalisierte Struktur"""

    # Legacy-Tabellen die entfernt werden sollen
    LEGACY_TABLES = [
        # Field-System (Legacy)
        'field_consistency',
        'field_statistics',
        'field_search_results',
        'field_search_source_usages',
        'field_value_sources',
        'field_values',  # Diese auch, da wir FieldValue in normalized_models haben

        # Model-Tracking (Legacy)
        'model_field_consistency',
        'model_source_contributions',
        'model_statistics',
        'model_statistics_comprehensive',
        'model_summary',

        # Andere Legacy
        'sequential_search_results',
        'source_discovery_sessions',
        'mines_backup',  # Backup-Tabelle

        # Leere Lookup-Tabellen die nicht verwendet werden
        'activity_statuses',  # Leer und nicht verwendet
        'mine_types',         # Leer und nicht verwendet
        'production_periods', # Leer und nicht verwendet
        'restoration_costs',  # Leer und nicht verwendet
    ]

    # Tabellen die BEHALTEN werden sollen (12 Tabellen)
    KEEP_TABLES = [
        # Stammdaten (6)
        'countries',
        'regions',
        'commodities',
        'companies',
        'ai_models',
        'sources',

        # Kerntabelle (1)
        'mines',

        # Beziehungen (3)
        'mine_commodities',
        'mine_owners',
        'mine_operators',

        # Ergebnisse (2)
        'search_results',
        'search_sessions',
    ]

    conn = sqlite3.connect('mines.db')
    cursor = conn.cursor()

    print("🧹 DATENBANK-BEREINIGUNG")
    print("=" * 80)

    # Aktuelle Tabellen
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    current_tables = [t[0] for t in cursor.fetchall()]
    print(f"📊 Aktuelle Tabellen: {len(current_tables)}")

    # Lösche Legacy-Tabellen
    deleted_count = 0
    for table in LEGACY_TABLES:
        if table in current_tables:
            try:
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
                print(f"   ❌ Gelöscht: {table}")
                deleted_count += 1
            except Exception as e:
                print(f"   ⚠️ Fehler beim Löschen von {table}: {e}")

    # Commit
    conn.commit()

    # Neue Tabellenliste
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    remaining_tables = [t[0] for t in cursor.fetchall()]

    print(f"\n✅ BEREINIGUNG ABGESCHLOSSEN")
    print(f"   - {deleted_count} Legacy-Tabellen gelöscht")
    print(f"   - {len(remaining_tables)} Tabellen verbleiben")

    print(f"\n📋 VERBLEIBENDE TABELLEN:")
    for table in remaining_tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        status = "✅" if table in KEEP_TABLES else "⚠️"
        print(f"   {status} {table:<30} ({count} Zeilen)")

    # VACUUM zur Optimierung
    print(f"\n🔧 Optimiere Datenbank...")
    cursor.execute("VACUUM")

    conn.close()
    print(f"\n✅ Datenbank erfolgreich bereinigt!")

if __name__ == "__main__":
    cleanup_database()
