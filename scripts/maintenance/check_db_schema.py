#!/usr/bin/env python3
"""
Prüfe DB-Schema um herauszufinden welche Tabellen vorhanden sind
"""

import sqlite3
import sys
# Import für Root-Level-Scripts
try:
    # Versuche Backend-Import
    from minesearch.database.db_utils import get_normalized_db_path, get_sqlite_connection
except ImportError:
    # Fallback für Root-Level-Scripts
    from db_utils_root.db_utils import get_normalized_db_path, get_sqlite_connection

db_path = get_normalized_db_path()

try:
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Alle Tabellen anzeigen
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print("🗄️  VERFÜGBARE TABELLEN:")
        for table in tables:
            print(f"   - {table[0]}")
        
        print("\n📊 TABELLEN-DETAILS:")
        for table in tables:
            table_name = table[0]
            try:
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                print(f"\n📋 {table_name.upper()}:")
                for col in columns:
                    print(f"   - {col[1]} ({col[2]})")
                
                # Anzahl Einträge
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"   📊 Einträge: {count}")
                
            except Exception as e:
                print(f"   ❌ Fehler bei {table_name}: {e}")

except Exception as e:
    print(f"❌ Verbindungsfehler: {e}")