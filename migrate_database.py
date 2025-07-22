#!/usr/bin/env python3
"""
Author: rahn
Datum: 19.07.2025
Version: 1.0
Beschreibung: Einfache Datenbank-Migration für source_mapping
"""

import sys
import os
import sqlite3

sys.path.append(os.path.join(os.path.dirname(__file__), 'minesearch_v2', 'backend'))

def migrate_database():
    """Füge source_mapping Spalte zur search_results Tabelle hinzu"""
    db_path = "/app/minesearch_v2/backend/mines.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Datenbank nicht gefunden: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Prüfe ob Spalte bereits existiert
        cursor.execute("PRAGMA table_info(search_results)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'source_mapping' in columns:
            print("✅ source_mapping Spalte existiert bereits")
        else:
            print("📝 Füge source_mapping Spalte hinzu...")
            cursor.execute("ALTER TABLE search_results ADD COLUMN source_mapping JSON")
            conn.commit()
            print("✅ source_mapping Spalte hinzugefügt")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Migrations-Fehler: {str(e)}")

def main():
    print("🔧 Datenbank-Migration")
    print("=" * 30)
    
    migrate_database()
    
    print("=" * 30)
    print("✅ Migration abgeschlossen!")

if __name__ == "__main__":
    main()