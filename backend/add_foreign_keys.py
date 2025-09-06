#!/usr/bin/env python3
"""
Author: rahn
Datum: 06.09.2025
Version: 1.0
Beschreibung: Fügt Foreign Key Constraints zur mines Tabelle hinzu
"""

import sqlite3

def add_foreign_keys():
    """Fügt Foreign Key Constraints zur mines Tabelle hinzu"""
    
    conn = sqlite3.connect('mines.db')
    cursor = conn.cursor()
    
    print("🔗 FOREIGN KEY CONSTRAINTS HINZUFÜGEN")
    print("=" * 80)
    
    # Aktiviere Foreign Key Support
    cursor.execute("PRAGMA foreign_keys = ON")
    
    try:
        # Da SQLite keine ALTER TABLE ADD CONSTRAINT unterstützt,
        # müssen wir die Tabelle neu erstellen
        
        print("📋 Erstelle neue mines Tabelle mit Foreign Keys...")
        
        # 1. Erstelle neue Tabelle mit Foreign Keys
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS mines_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255) NOT NULL,
            country_id INTEGER,
            region_id INTEGER,
            latitude FLOAT,
            longitude FLOAT,
            commodity VARCHAR(100),
            status VARCHAR(50),
            mine_metadata JSON,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            
            -- Foreign Keys
            FOREIGN KEY (country_id) REFERENCES countries(id) ON DELETE SET NULL,
            FOREIGN KEY (region_id) REFERENCES regions(id) ON DELETE SET NULL
        )
        """)
        
        # 2. Kopiere Daten von alter Tabelle (falls vorhanden)
        cursor.execute("""
        INSERT INTO mines_new (
            id, name, country_id, region_id, 
            latitude, longitude, commodity, status,
            mine_metadata, created_at, updated_at
        )
        SELECT 
            id, name, country_id, region_id,
            latitude, longitude, commodity, status,
            mine_metadata, created_at, updated_at
        FROM mines
        """)
        
        # 3. Lösche alte Tabelle
        cursor.execute("DROP TABLE mines")
        
        # 4. Benenne neue Tabelle um
        cursor.execute("ALTER TABLE mines_new RENAME TO mines")
        
        print("✅ Foreign Keys erfolgreich hinzugefügt!")
        
        # Zeige neue Struktur
        print("\n📋 NEUE MINES TABELLEN-STRUKTUR:")
        cursor.execute("PRAGMA table_info(mines)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"   - {col[1]:<20} {col[2]:<15}")
            
        print("\n🔗 FOREIGN KEYS:")
        cursor.execute("PRAGMA foreign_key_list(mines)")
        fks = cursor.fetchall()
        for fk in fks:
            print(f"   - {fk[3]} -> {fk[2]}.{fk[4]}")
            
        conn.commit()
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    add_foreign_keys()