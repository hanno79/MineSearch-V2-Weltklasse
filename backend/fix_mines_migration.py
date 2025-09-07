#!/usr/bin/env python3
"""
Author: rahn
Datum: 07.09.2025
Version: 1.0
Beschreibung: KORRIGIERTE Mines-Migration für echte DB-Struktur

🔧 KORRIGIERTE MINES UNIQUE-CONSTRAINT MIGRATION
===============================================

Basierend auf echter Mines-Tabellen-Struktur:
- id (INTEGER)
- name (VARCHAR(255)) 
- country_id (INTEGER)
- region_id (INTEGER)
- created_at (DATETIME)
- updated_at (DATETIME)

UNIQUE-Constraint: name + country_id + region_id
"""

import sqlite3
import pandas as pd
from datetime import datetime
import time


def wait_for_db_unlock(db_path: str = 'mines.db', max_wait: int = 30) -> bool:
    """Wartet bis DB entsperrt ist"""
    print(f"🕐 Warte auf DB-Entsperrung...")
    
    for i in range(max_wait):
        try:
            conn = sqlite3.connect(db_path, timeout=1.0)
            conn.execute("SELECT 1")
            conn.close()
            print(f"   ✅ DB entsperrt nach {i+1} Sekunden")
            return True
        except sqlite3.OperationalError:
            if i < max_wait - 1:
                print(f"   ⏳ Warte... ({i+1}/{max_wait})")
                time.sleep(1)
            continue
    
    print(f"   ❌ DB bleibt nach {max_wait}s gesperrt")
    return False


def migrate_mines_table_corrected(db_path: str = 'mines.db') -> bool:
    """Migriert Mines-Tabelle mit korrekter Spalten-Struktur"""
    
    print("🛠️  STARTE KORRIGIERTE MINES-MIGRATION")
    print("=" * 50)
    
    # Warte auf DB-Entsperrung
    if not wait_for_db_unlock(db_path):
        print("❌ Migration abgebrochen - DB gesperrt")
        return False
    
    conn = sqlite3.connect(db_path)
    
    try:
        cursor = conn.cursor()
        
        # 1. Prüfe aktuelle Duplikate vor Migration
        print("\n📊 Prüfe aktuelle Mines-Duplikate...")
        cursor.execute("""
            SELECT name, country_id, region_id, COUNT(*) as count 
            FROM mines 
            GROUP BY name, country_id, region_id
            HAVING count > 1
            ORDER BY count DESC
        """)
        
        existing_duplicates = cursor.fetchall()
        if existing_duplicates:
            print(f"   ⚠️  {len(existing_duplicates)} Duplikat-Gruppen gefunden:")
            for dup in existing_duplicates[:3]:
                print(f"      '{dup[0]}' (country_id:{dup[1]}, region_id:{dup[2]}): {dup[3]}x")
            
            # Bereinige Duplikate vor Migration
            print("   🧹 Bereinige Duplikate vor Migration...")
            for name, country_id, region_id, count in existing_duplicates:
                # Behalte nur das erste (älteste) 
                cursor.execute("""
                    DELETE FROM mines 
                    WHERE id NOT IN (
                        SELECT MIN(id) 
                        FROM mines 
                        WHERE name = ? AND country_id = ? AND region_id = ?
                    ) AND name = ? AND country_id = ? AND region_id = ?
                """, (name, country_id, region_id, name, country_id, region_id))
                
                removed_count = cursor.rowcount
                print(f"      🗑️  Entfernt {removed_count} Duplikate von '{name}'")
        else:
            print("   ✅ Keine Duplikate gefunden - Migration kann sicher durchgeführt werden")
        
        # 2. Backup der aktuellen Tabelle
        print("\n💾 Erstelle Backup der MINES-Tabelle...")
        mines_backup = pd.read_sql_query("SELECT * FROM mines", conn)
        backup_file = f'mines_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        mines_backup.to_csv(backup_file, index=False)
        print(f"   ✅ Backup gespeichert: {backup_file}")
        
        # 3. Erstelle neue Tabelle mit UNIQUE-Constraint
        print("\n🔧 Erstelle neue MINES-Tabelle mit UNIQUE-Constraints...")
        cursor.execute("""
            CREATE TABLE mines_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(255) NOT NULL,
                country_id INTEGER,
                region_id INTEGER,
                created_at DATETIME,
                updated_at DATETIME,
                UNIQUE(name, country_id, region_id),  -- 🔑 COMPOSITE UNIQUE CONSTRAINT
                FOREIGN KEY (country_id) REFERENCES countries (id),
                FOREIGN KEY (region_id) REFERENCES regions (id)
            )
        """)
        
        # 4. Migriere Daten (sollten jetzt duplikatfrei sein)
        print("📦 Migriere Daten zur neuen Tabelle...")
        cursor.execute("""
            INSERT INTO mines_new (id, name, country_id, region_id, created_at, updated_at)
            SELECT id, name, country_id, region_id, created_at, updated_at 
            FROM mines
        """)
        
        migrated_rows = cursor.rowcount
        print(f"   📊 {migrated_rows} Mines erfolgreich migriert")
        
        # 5. Ersetze alte durch neue Tabelle
        print("🔄 Ersetze alte durch neue Tabelle...")
        cursor.execute("DROP TABLE mines")
        cursor.execute("ALTER TABLE mines_new RENAME TO mines")
        
        # 6. Commit der Änderungen
        conn.commit()
        print("✅ MINES-Migration erfolgreich abgeschlossen!")
        
        # 7. Validierung
        print("\n🔍 Validiere Migration...")
        cursor.execute("SELECT COUNT(*) FROM mines")
        final_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='mines'")
        table_exists = cursor.fetchone() is not None
        
        if table_exists and final_count == migrated_rows:
            print(f"   ✅ Validierung erfolgreich: {final_count} Mines in neuer Tabelle")
            return True
        else:
            print(f"   ❌ Validierung fehlgeschlagen!")
            return False
            
    except sqlite3.IntegrityError as e:
        conn.rollback()
        print(f"❌ INTEGRITY ERROR: {e}")
        print("   💡 Mögliche Ursache: Duplikate die nicht automatisch bereinigt werden konnten")
        return False
        
    except Exception as e:
        conn.rollback()
        print(f"❌ MIGRATIONS-FEHLER: {e}")
        return False
        
    finally:
        conn.close()


def test_unique_constraint():
    """Testet das neue UNIQUE-Constraint"""
    print("\n🧪 TESTE UNIQUE-CONSTRAINT...")
    
    conn = sqlite3.connect('mines.db')
    try:
        cursor = conn.cursor()
        
        # Versuche Duplikat einzufügen
        test_name = f"TEST_MINE_{datetime.now().strftime('%H%M%S')}"
        
        # Erstes Insert - sollte funktionieren
        cursor.execute("""
            INSERT INTO mines (name, country_id, region_id) 
            VALUES (?, 1, 1)
        """, (test_name,))
        
        first_insert_id = cursor.lastrowid
        print(f"   ✅ Erster Insert erfolgreich: ID {first_insert_id}")
        
        # Zweites Insert mit gleichen Werten - sollte fehlschlagen
        try:
            cursor.execute("""
                INSERT INTO mines (name, country_id, region_id) 
                VALUES (?, 1, 1)
            """, (test_name,))
            
            print("   ❌ UNIQUE-Constraint funktioniert NICHT - Duplikat wurde eingefügt!")
            return False
            
        except sqlite3.IntegrityError:
            print("   ✅ UNIQUE-Constraint funktioniert - Duplikat verhindert!")
            
            # Cleanup
            cursor.execute("DELETE FROM mines WHERE id = ?", (first_insert_id,))
            conn.commit()
            return True
            
    except Exception as e:
        print(f"   ❌ Test fehlgeschlagen: {e}")
        return False
        
    finally:
        conn.close()


def main():
    """Hauptfunktion für korrigierte Mines-Migration"""
    
    print("🔧 KORRIGIERTE MINES UNIQUE-CONSTRAINT MIGRATION")
    print("=" * 60)
    print("Diese Migration:")
    print("1. 🧹 Bereinigt bestehende Mines-Duplikate")
    print("2. 💾 Erstellt Backup der aktuellen Daten")
    print("3. 🔧 Fügt UNIQUE(name, country_id, region_id) hinzu")
    print("4. 🧪 Testet das neue Constraint")
    print()
    
    user_confirm = input("Korrigierte Migration ausführen? (y/N): ").strip().lower()
    
    if user_confirm in ['y', 'yes']:
        success = migrate_mines_table_corrected()
        
        if success:
            print("\n🎉 MIGRATION ERFOLGREICH!")
            
            # Test das neue Constraint
            if test_unique_constraint():
                print("🛡️  MINES-Tabelle ist jetzt permanent gegen Duplikate geschützt!")
            
        else:
            print("\n❌ Migration fehlgeschlagen - siehe Fehlerausgabe oben")
            
    else:
        print("❌ Migration abgebrochen")


if __name__ == "__main__":
    main()