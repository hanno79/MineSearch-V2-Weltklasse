#!/usr/bin/env python3
"""
Author: rahn
Datum: 06.09.2025
Version: 1.0
Beschreibung: Fix für fehlende normalized_name und normalized_value Spalten
"""

import sqlite3
from datetime import datetime

def fix_database_schema():
    """Fügt fehlende Spalten zu den Tabellen hinzu"""
    print("🔧 DATENBANK SCHEMA FIX")
    print("=" * 50)
    
    # Verwende WAL-Mode und längeres Timeout für Locks
    conn = sqlite3.connect('mines.db', timeout=30.0)
    conn.execute('PRAGMA journal_mode=WAL;')
    cursor = conn.cursor()
    
    try:
        # 1. Prüfe aktuelle Struktur der companies Tabelle
        print("1. PRÜFE COMPANIES TABELLE:")
        cursor.execute("PRAGMA table_info(companies)")
        companies_columns = [row[1] for row in cursor.fetchall()]
        print(f"   Aktuelle Spalten: {companies_columns}")
        
        # Füge normalized_name zu companies hinzu, falls fehlt
        if 'normalized_name' not in companies_columns:
            print("   ➕ Füge normalized_name Spalte hinzu...")
            cursor.execute("ALTER TABLE companies ADD COLUMN normalized_name TEXT")
            print("   ✅ normalized_name Spalte hinzugefügt")
        else:
            print("   ✅ normalized_name Spalte bereits vorhanden")
        
        # 2. Prüfe aktuelle Struktur der mine_data_fields Tabelle
        print("\n2. PRÜFE MINE_DATA_FIELDS TABELLE:")
        cursor.execute("PRAGMA table_info(mine_data_fields)")
        fields_columns = [row[1] for row in cursor.fetchall()]
        print(f"   Aktuelle Spalten: {fields_columns}")
        
        # Füge normalized_value zu mine_data_fields hinzu, falls fehlt
        if 'normalized_value' not in fields_columns:
            print("   ➕ Füge normalized_value Spalte hinzu...")
            cursor.execute("ALTER TABLE mine_data_fields ADD COLUMN normalized_value TEXT")
            print("   ✅ normalized_value Spalte hinzugefügt")
        else:
            print("   ✅ normalized_value Spalte bereits vorhanden")
        
        # 3. Prüfe Sources Tabelle für typical_content_types
        print("\n3. PRÜFE SOURCES TABELLE:")
        cursor.execute("PRAGMA table_info(sources)")
        sources_columns = [row[1] for row in cursor.fetchall()]
        print(f"   Aktuelle Spalten: {sources_columns}")
        
        # Füge typical_content_types zu sources hinzu, falls fehlt
        if 'typical_content_types' not in sources_columns:
            print("   ➕ Füge typical_content_types Spalte hinzu...")
            cursor.execute("ALTER TABLE sources ADD COLUMN typical_content_types TEXT")
            print("   ✅ typical_content_types Spalte hinzugefügt")
        else:
            print("   ✅ typical_content_types Spalte bereits vorhanden")
        
        # 4. Initialisiere normalized_name für bestehende companies
        print("\n4. INITIALISIERE NORMALIZED WERTE:")
        cursor.execute("SELECT COUNT(*) FROM companies WHERE normalized_name IS NULL")
        null_normalized = cursor.fetchone()[0]
        
        if null_normalized > 0:
            print(f"   🔄 Setze normalized_name für {null_normalized} Companies...")
            cursor.execute("""
                UPDATE companies 
                SET normalized_name = LOWER(TRIM(name)) 
                WHERE normalized_name IS NULL
            """)
            print(f"   ✅ {null_normalized} normalized_name Werte gesetzt")
        else:
            print("   ✅ Alle Companies haben bereits normalized_name")
        
        # 5. Initialisiere normalized_value für bestehende mine_data_fields
        cursor.execute("SELECT COUNT(*) FROM mine_data_fields WHERE normalized_value IS NULL")
        null_normalized_values = cursor.fetchone()[0]
        
        if null_normalized_values > 0:
            print(f"   🔄 Setze normalized_value für {null_normalized_values} Feldwerte...")
            cursor.execute("""
                UPDATE mine_data_fields 
                SET normalized_value = LOWER(TRIM(primitive_value)) 
                WHERE normalized_value IS NULL AND primitive_value IS NOT NULL
            """)
            print(f"   ✅ {null_normalized_values} normalized_value Werte gesetzt")
        else:
            print("   ✅ Alle mine_data_fields haben bereits normalized_value")
        
        conn.commit()
        
        # 6. Finale Validierung
        print("\n5. FINALE VALIDIERUNG:")
        
        # Prüfe companies
        cursor.execute("SELECT COUNT(*) FROM companies")
        total_companies = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM companies WHERE normalized_name IS NOT NULL")
        normalized_companies = cursor.fetchone()[0]
        
        # Prüfe mine_data_fields
        cursor.execute("SELECT COUNT(*) FROM mine_data_fields")
        total_fields = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM mine_data_fields WHERE normalized_value IS NOT NULL")
        normalized_fields = cursor.fetchone()[0]
        
        print(f"   📊 Companies: {normalized_companies}/{total_companies} mit normalized_name")
        print(f"   📊 Fields: {normalized_fields}/{total_fields} mit normalized_value")
        
        if normalized_companies == total_companies and normalized_fields == total_fields:
            print("\n🎉 SCHEMA FIX ERFOLGREICH!")
            print("✅ Alle fehlenden Spalten hinzugefügt")
            print("✅ Alle normalized Werte initialisiert")
            print("✅ Database bereit für normalized operations")
            return True
        else:
            print("\n❌ SCHEMA FIX TEILWEISE FEHLGESCHLAGEN!")
            return False
        
    except Exception as e:
        print(f"\n❌ Fehler beim Schema Fix: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    print(f"🧪 STARTE DATABASE SCHEMA FIX - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    success = fix_database_schema()
    
    if success:
        print(f"\n🎯 SCHEMA FIX KOMPLETT!")
        print("Die 'fehlgeschlagenen Ergebnisse' sollten jetzt reduziert sein.")
        print("Database-Speicher-Fehler behoben.")
        print()
        print("🔄 EMPFEHLUNG:")
        print("   - Server neu starten für Schema-Aktivierung")
        print("   - Neue Batch-Suche testen")
        print("   - Fehlgeschlagene Ergebnisse sollten nur noch Qualitäts-Filter sein")
    else:
        print(f"\n❌ SCHEMA FIX UNVOLLSTÄNDIG")
        print("Manuelle Überprüfung erforderlich")