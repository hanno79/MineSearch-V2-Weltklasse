#!/usr/bin/env python3
"""
Author: rahn
Datum: 04.09.2025
Version: 1.0
Beschreibung: Prüft die Struktur der Referenz-Tabellen
"""

import sys
sys.path.insert(0, 'backend')

import sqlite3
from minesearch.database.db_utils import get_normalized_db_path, get_sqlite_connection

def check_table_structure():
    """Prüft die Struktur der Referenz-Tabellen"""

    conn = sqlite3.connect(get_normalized_db_path())
    cursor = conn.cursor()

    # Prüfe mine_types Struktur
    print("📊 [MINE-TYPES] Tabellenstruktur:")
    cursor.execute("PRAGMA table_info(mine_types)")
    columns = cursor.fetchall()
    for col in columns:
        print(f"   {col[1]} ({col[2]})")

    print("\n📊 [MINE-TYPES] Aktuelle Inhalte:")
    cursor.execute("SELECT * FROM mine_types")
    rows = cursor.fetchall()
    for row in rows:
        print(f"   {row}")

    # Prüfe activity_statuses Struktur
    print("\n📊 [ACTIVITY-STATUSES] Tabellenstruktur:")
    cursor.execute("PRAGMA table_info(activity_statuses)")
    columns = cursor.fetchall()
    for col in columns:
        print(f"   {col[1]} ({col[2]})")

    print("\n📊 [ACTIVITY-STATUSES] Aktuelle Inhalte:")
    cursor.execute("SELECT * FROM activity_statuses")
    rows = cursor.fetchall()
    for row in rows:
        print(f"   {row}")

    conn.close()

if __name__ == "__main__":
    check_table_structure()
