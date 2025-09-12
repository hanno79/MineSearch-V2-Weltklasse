#!/usr/bin/env python3
"""
Author: rahn
Datum: 06.09.2025
Version: 1.0
Beschreibung: Radikale Datenbank-Bereinigung für echte 3NF-Normalisierung
Entfernt alle Hybrid-Reste und erstellt saubere Trennung zwischen normalisierten und primitiven Feldern
"""

import sqlite3
from datetime import datetime

def radical_database_cleanup():
    """Radikale Bereinigung für echte 3NF ohne Hybrid-Reste"""

    conn = sqlite3.connect('mines.db')
    cursor = conn.cursor()

    print("🧹 RADIKALE DATENBANK-BEREINIGUNG FÜR ECHTE 3NF")
    print("=" * 80)

    try:
        # PHASE 1: RADIKALER FRESH START
        print("\n📋 PHASE 1: RADIKALER FRESH START")
        print("-" * 40)

        print("1.1 Lösche ALLE bestehenden Daten...")

        # Lösche alle Daten (behalte nur Schema und Lookup-Tabellen)
        tables_to_clear = [
            'mine_data_fields',
            'search_sessions',
            'mines',
            'companies'  # Wird neu befüllt
        ]

        for table in tables_to_clear:
            cursor.execute(f"DELETE FROM {table}")
            print(f"   ✅ {table} geleert")

        # Reset Auto-Increment
        cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('mine_data_fields',
'search_sessions', 'mines', 'companies')")
        print("   ✅ Auto-Increment zurückgesetzt")

        # PHASE 2: SCHEMA-ÜBERARBEITUNG FÜR ECHTE 3NF
        print("\n📋 PHASE 2: SCHEMA FÜR ECHTE 3NF")
        print("-" * 40)

        print("2.1 Erstelle neue mine_data_fields Struktur...")

        # Erstelle neue mine_data_fields Tabelle mit sauberer Trennung
        cursor.execute("DROP TABLE IF EXISTS mine_data_fields_new")
        cursor.execute("""
        CREATE TABLE mine_data_fields_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            search_result_id INTEGER,
            mine_id INTEGER NOT NULL,
            field_name VARCHAR(255) NOT NULL,
            field_type VARCHAR(20) NOT NULL CHECK(field_type IN ('normalized', 'primitive')),

            -- FÜR NORMALISIERTE FELDER (NUR IDs, KEIN TEXT)
            commodity_id INTEGER,
            company_id INTEGER,
            activity_status_id INTEGER,
            mine_type_id INTEGER,
            country_id INTEGER,
            region_id INTEGER,

            -- FÜR PRIMITIVE FELDER (NUR WERTE, KEINE IDs)
            primitive_value TEXT,
            numeric_value REAL,
            unit VARCHAR(50),

            -- METADATA (für beide Typen)
            confidence_score REAL DEFAULT 0.8,
            is_template_value BOOLEAN DEFAULT FALSE,
            validation_status VARCHAR(50) DEFAULT 'valid',
            source_name TEXT,
            model_used VARCHAR(255),
            session_id VARCHAR(255),
            extraction_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            model_id INTEGER,
            source_id INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

            -- CONSTRAINTS
            FOREIGN KEY (mine_id) REFERENCES mines(id) ON DELETE CASCADE,
            FOREIGN KEY (search_result_id) REFERENCES search_sessions(id) ON DELETE CASCADE,
            FOREIGN KEY (commodity_id) REFERENCES commodities(id),
            FOREIGN KEY (company_id) REFERENCES companies(id),
            FOREIGN KEY (activity_status_id) REFERENCES activity_statuses(id),
            FOREIGN KEY (mine_type_id) REFERENCES mine_types(id),
            FOREIGN KEY (country_id) REFERENCES countries(id),
            FOREIGN KEY (region_id) REFERENCES regions(id),

            -- 3NF CONSTRAINT: Entweder normalized ODER primitive, niemals beides
            CHECK (
                (field_type = 'normalized' AND primitive_value IS NULL AND
                 (commodity_id IS NOT NULL OR company_id IS NOT NULL OR
                  activity_status_id IS NOT NULL OR mine_type_id IS NOT NULL OR
                  country_id IS NOT NULL OR region_id IS NOT NULL))
                OR
                (field_type = 'primitive' AND primitive_value IS NOT NULL AND
                 commodity_id IS NULL AND company_id IS NULL AND
                 activity_status_id IS NULL AND mine_type_id IS NULL AND
                 country_id IS NULL AND region_id IS NULL)
            )
        )
        """)

        print("   ✅ Neue mine_data_fields Struktur erstellt")

        # Ersetze alte Tabelle
        cursor.execute("DROP TABLE mine_data_fields")
        cursor.execute("ALTER TABLE mine_data_fields_new RENAME TO mine_data_fields")

        print("   ✅ Alte Tabelle ersetzt")

        # PHASE 3: INDIZES FÜR PERFORMANCE
        print("\n📋 PHASE 3: PERFORMANCE-OPTIMIERUNG")
        print("-" * 40)

        performance_indexes = [
            ("idx_mine_data_fields_type", "mine_data_fields(field_type)"),
            ("idx_mine_data_fields_normalized", "mine_data_fields(commodity_id, company_id,
activity_status_id, mine_type_id, country_id, region_id)"),
            ("idx_mine_data_fields_primitive", "mine_data_fields(primitive_value)"),
            ("idx_mine_data_fields_mine_field", "mine_data_fields(mine_id, field_name)"),
            ("idx_mine_data_fields_session", "mine_data_fields(session_id)")
        ]

        for idx_name, idx_def in performance_indexes:
            cursor.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {idx_def}")
            print(f"   ✅ Index {idx_name} erstellt")

        # PHASE 4: FELD-KATEGORISIERUNG
        print("\n📋 PHASE 4: FELD-KATEGORISIERUNG")
        print("-" * 40)

        # Erstelle Field-Type-Mapping Tabelle
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS field_type_mapping (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            field_pattern VARCHAR(255) NOT NULL UNIQUE,
            field_type VARCHAR(20) NOT NULL CHECK(field_type IN ('normalized', 'primitive')),
            target_table VARCHAR(50),
            description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Definiere Standard-Kategorisierung
        field_mappings = [
            # NORMALIZED FIELDS (werden zu FK-IDs)
            ('rohstoffabbau%', 'normalized', 'commodities', 'Rohstoffe -> commodities'),
            ('%commodity%', 'normalized', 'commodities', 'Rohstoffe -> commodities'),
            ('eigentümer%', 'normalized', 'companies', 'Eigentümer -> companies'),
            ('betreiber%', 'normalized', 'companies', 'Betreiber -> companies'),
            ('%owner%', 'normalized', 'companies', 'Eigentümer -> companies'),
            ('%operator%', 'normalized', 'companies', 'Betreiber -> companies'),
            ('aktivitätsstatus%', 'normalized', 'activity_statuses', 'Status -> activity_statuses'),
            ('%activity%', 'normalized', 'activity_statuses', 'Status -> activity_statuses'),
            ('%status%', 'normalized', 'activity_statuses', 'Status -> activity_statuses'),
            ('minentyp%', 'normalized', 'mine_types', 'Typ -> mine_types'),
            ('%mine%type%', 'normalized', 'mine_types', 'Typ -> mine_types'),
            ('country', 'normalized', 'countries', 'Land -> countries'),
            ('land', 'normalized', 'countries', 'Land -> countries'),
            ('region', 'normalized', 'regions', 'Region -> regions'),

            # PRIMITIVE FIELDS (bleiben als Text/Zahlen)
            ('name', 'primitive', None, 'Minenname bleibt Text'),
            ('%koordinate%', 'primitive', None, 'Koordinaten bleiben numerisch'),
            ('%coordinate%', 'primitive', None, 'Koordinaten bleiben numerisch'),
            ('latitude', 'primitive', None, 'Koordinaten bleiben numerisch'),
            ('longitude', 'primitive', None, 'Koordinaten bleiben numerisch'),
            ('%jahr%', 'primitive', None, 'Jahreszahlen bleiben numerisch'),
            ('%year%', 'primitive', None, 'Jahreszahlen bleiben numerisch'),
            ('%datum%', 'primitive', None, 'Datumsangaben bleiben Text'),
            ('%date%', 'primitive', None, 'Datumsangaben bleiben Text'),
            ('%menge%', 'primitive', None, 'Mengenangaben bleiben numerisch'),
            ('%volume%', 'primitive', None, 'Mengenangaben bleiben numerisch'),
            ('%fläche%', 'primitive', None, 'Flächenangaben bleiben numerisch'),
            ('%area%', 'primitive', None, 'Flächenangaben bleiben numerisch'),
            ('%kosten%', 'primitive', None, 'Kostenangaben bleiben numerisch'),
            ('%cost%', 'primitive', None, 'Kostenangaben bleiben numerisch'),
            ('%quellenangaben%', 'primitive', None, 'Quellen bleiben Text'),
            ('%sources%', 'primitive', None, 'Quellen bleiben Text')
        ]

        # Füge Mappings hinzu
        for pattern, field_type, target_table, description in field_mappings:
            cursor.execute("""
            INSERT OR IGNORE INTO field_type_mapping (field_pattern, field_type, target_table, description)
            VALUES (?, ?, ?, ?)
            """, (pattern, field_type, target_table, description))

        print(f"   ✅ {len(field_mappings)} Feld-Kategorien definiert")

        # FINAL VALIDATION
        print("\n📋 FINAL VALIDATION")
        print("-" * 40)

        # Validiere Schema-Integrität
        cursor.execute("PRAGMA table_info(mine_data_fields)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]

        required_columns = ['field_type', 'commodity_id', 'primitive_value']
        missing_columns = [col for col in required_columns if col not in column_names]

        if missing_columns:
            raise Exception(f"Fehlende Spalten: {missing_columns}")
        else:
            print("   ✅ Schema-Integrität validiert")

        # Zähle Lookup-Tabellen
        lookup_tables = ['commodities', 'companies', 'activity_statuses', 'mine_types', 'countries', 'regions']
        for table in lookup_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"   📊 {table}: {count} Einträge")

        cursor.execute("SELECT COUNT(*) FROM field_type_mapping")
        mapping_count = cursor.fetchone()[0]
        print(f"   📊 field_type_mapping: {mapping_count} Kategorien")

        conn.commit()

        print("\n🎉 RADIKALE BEREINIGUNG ABGESCHLOSSEN!")
        print("=" * 80)
        print("✅ Echte 3NF ohne Hybrid-Reste")
        print("✅ Saubere Trennung: normalized vs primitive")
        print("✅ Constraint-basierte Datenintegrität")
        print("✅ Performance-optimierte Indizes")
        print("✅ Automatische Feld-Kategorisierung")
        print()
        print("🔄 SYSTEM BEREIT FÜR SAUBERE NORMALISIERUNG!")

    except Exception as e:
        print(f"❌ Fehler bei radikaler Bereinigung: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    radical_database_cleanup()
