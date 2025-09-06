#!/usr/bin/env python3
"""
Author: rahn
Datum: 06.09.2025
Version: 1.0
Beschreibung: Erstellt fehlende Tabellen für vollständige Suchergebnis-Speicherung
"""

import sqlite3
from datetime import datetime

def create_missing_tables():
    """Erstellt field_definitions und mine_data_fields Tabellen"""
    
    conn = sqlite3.connect('mines.db')
    cursor = conn.cursor()
    
    print("🔧 FEHLENDE TABELLEN ERSTELLEN")
    print("=" * 80)
    
    try:
        # 1. Erstelle field_definitions Tabelle
        print("📋 Erstelle field_definitions Tabelle...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS field_definitions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            field_name VARCHAR(255) NOT NULL UNIQUE,
            display_name VARCHAR(255),
            data_type VARCHAR(50) DEFAULT 'text',
            description TEXT,
            is_required BOOLEAN DEFAULT FALSE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # 2. Erstelle mine_data_fields Tabelle  
        print("📋 Erstelle mine_data_fields Tabelle...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS mine_data_fields (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            search_result_id INTEGER,
            mine_id INTEGER NOT NULL,
            field_name VARCHAR(255) NOT NULL,
            field_value TEXT,
            raw_value TEXT,
            normalized_value TEXT,
            numeric_value REAL,
            unit VARCHAR(50),
            confidence_score REAL DEFAULT 0.8,
            is_template_value BOOLEAN DEFAULT FALSE,
            validation_status VARCHAR(50) DEFAULT 'pending',
            source_name TEXT,
            model_used VARCHAR(255),
            session_id VARCHAR(255),
            extraction_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            model_id INTEGER,
            source_id INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            
            -- Foreign Keys
            FOREIGN KEY (mine_id) REFERENCES mines(id) ON DELETE CASCADE,
            FOREIGN KEY (search_result_id) REFERENCES search_sessions(id) ON DELETE CASCADE
        )
        """)
        
        # 3. Erstelle Indizes für Performance
        print("📋 Erstelle Indizes...")
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_mine_data_fields_mine_id 
        ON mine_data_fields(mine_id)
        """)
        
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_mine_data_fields_search_result_id 
        ON mine_data_fields(search_result_id)
        """)
        
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_mine_data_fields_field_name 
        ON mine_data_fields(field_name)
        """)
        
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_mine_data_fields_model_used 
        ON mine_data_fields(model_used)
        """)
        
        print("✅ Alle Tabellen und Indizes erfolgreich erstellt!")
        
        # 4. Zeige Tabellen-Strukturen
        print("\n📋 FIELD_DEFINITIONS STRUKTUR:")
        cursor.execute("PRAGMA table_info(field_definitions)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"   - {col[1]:<20} {col[2]:<15} {'NOT NULL' if col[3] else 'NULL'}")
            
        print("\n📋 MINE_DATA_FIELDS STRUKTUR:")
        cursor.execute("PRAGMA table_info(mine_data_fields)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"   - {col[1]:<25} {col[2]:<15} {'NOT NULL' if col[3] else 'NULL'}")
            
        print("\n🔗 FOREIGN KEYS (mine_data_fields):")
        cursor.execute("PRAGMA foreign_key_list(mine_data_fields)")
        fks = cursor.fetchall()
        for fk in fks:
            print(f"   - {fk[3]} -> {fk[2]}.{fk[4]}")
            
        # 5. Füge Standard-Feldnamen hinzu
        print("\n📊 Füge Standard-Feldnamen zu field_definitions hinzu...")
        
        standard_fields = [
            ('Name', 'Mine Name', 'text'),
            ('Country', 'Country', 'text'), 
            ('Region', 'Region/Province', 'text'),
            ('Eigentümer', 'Owner', 'text'),
            ('Betreiber', 'Operator', 'text'),
            ('x-Koordinate', 'X-Coordinate', 'numeric'),
            ('y-Koordinate', 'Y-Coordinate', 'numeric'),
            ('Aktivitätsstatus', 'Activity Status', 'text'),
            ('Restaurationskosten', 'Restoration Costs', 'numeric'),
            ('Jahr der Aufnahme der Kosten', 'Cost Year', 'numeric'),
            ('Jahr der Erstellung des Dokumentes', 'Document Year', 'numeric'),
            ('Rohstoffabbau', 'Commodity', 'text'),
            ('Minentyp', 'Mine Type', 'text'),
            ('Produktionsstart', 'Production Start', 'numeric'),
            ('Produktionsende', 'Production End', 'numeric'),
            ('Fördermenge/Jahr', 'Annual Production', 'numeric'),
            ('Fläche der Mine in qkm', 'Mine Area (km²)', 'numeric'),
            ('Quellenangaben', 'Sources', 'text')
        ]
        
        for field_name, display_name, data_type in standard_fields:
            cursor.execute("""
            INSERT OR IGNORE INTO field_definitions (field_name, display_name, data_type)
            VALUES (?, ?, ?)
            """, (field_name, display_name, data_type))
        
        # Final count
        cursor.execute("SELECT COUNT(*) FROM field_definitions")
        count = cursor.fetchone()[0]
        print(f"✅ {count} Standard-Feldnamen in field_definitions gespeichert")
            
        conn.commit()
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()
    
    print(f"\n✅ Fehlende Tabellen erfolgreich erstellt!")
    print("🎯 System ist jetzt bereit für vollständige Suchergebnis-Speicherung")

if __name__ == "__main__":
    create_missing_tables()