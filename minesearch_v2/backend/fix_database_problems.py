#!/usr/bin/env python3
"""
Author: rahn
Datum: 26.07.2025
Version: 1.0
Beschreibung: Behebt die identifizierten Datenbankprobleme - Datenkonistenz, Modellnamen, Performance-Anomalien
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path

# DATABASE_PATH
DATABASE_PATH = Path(__file__).parent / "mines.db"

def backup_database():
    """Erstelle Backup der Datenbank vor Änderungen"""
    backup_path = DATABASE_PATH.with_suffix(f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
    import shutil
    shutil.copy2(DATABASE_PATH, backup_path)
    print(f"✅ Backup erstellt: {backup_path}")
    return backup_path

def fix_model_names():
    """Korrigiere Modellnamen in der Datenbank"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Finde und korrigiere Modellnamen
    model_corrections = {
        'openrouter:llama-3.3-nemotron-super': 'nemotron super',
        'openrouter:cypher-alpha-free': 'cypher alpha'
    }
    
    for old_name, new_name in model_corrections.items():
        # Update in allen relevanten Tabellen mit korrekten Spaltennamen
        table_updates = [
            ('search_results', 'model_used'),
            ('model_statistics', 'model_id'), 
            ('model_summary', 'model_id'),
            ('field_consistency', 'model_id'),
            ('field_statistics', 'model_id')
        ]
        
        for table, column in table_updates:
            try:
                cursor.execute(f"UPDATE {table} SET {column} = ? WHERE {column} = ?", (new_name, old_name))
                affected = cursor.rowcount
                if affected > 0:
                    print(f"✅ Tabelle {table}.{column}: {affected} Einträge von '{old_name}' zu '{new_name}' korrigiert")
            except sqlite3.OperationalError as e:
                print(f"⚠️ Tabelle {table}.{column} Fehler: {e}")
    
    conn.commit()
    conn.close()

def fix_unrealistic_success_rates():
    """Behebt unrealistische 1.0% Erfolgsraten"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Neu berechnen der Erfolgsraten basierend auf tatsächlichen Daten (korrekte Spaltennamen)
    cursor.execute("""
        UPDATE model_summary 
        SET success_rate = (
            SELECT CAST(COUNT(CASE WHEN ms.success = 1 THEN 1 END) AS FLOAT) / COUNT(*) 
            FROM model_statistics ms 
            WHERE ms.model_id = model_summary.model_id
        ),
        total_tests = (
            SELECT COUNT(*) 
            FROM model_statistics ms 
            WHERE ms.model_id = model_summary.model_id
        ),
        data_success_rate = (
            SELECT CAST(COUNT(CASE WHEN ms.success = 1 AND ms.fields_found > 0 THEN 1 END) AS FLOAT) / COUNT(*) 
            FROM model_statistics ms 
            WHERE ms.model_id = model_summary.model_id
        )
        WHERE success_rate <= 0.02  -- Nur unrealistische Werte unter 2% korrigieren
    """)
    
    affected = cursor.rowcount
    print(f"✅ {affected} Modelle mit unrealistischen Erfolgsraten korrigiert")
    
    conn.commit()
    conn.close()

def fix_data_consistency():
    """Behebt Datenkonsistenz zwischen model_summary und model_statistics"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Synchronisiere test_count zwischen Tabellen (korrekte Spaltennamen)
    cursor.execute("""
        UPDATE model_summary 
        SET total_tests = (
            SELECT COUNT(*) 
            FROM model_statistics ms 
            WHERE ms.model_id = model_summary.model_id
        ),
        avg_sources_count = COALESCE((
            SELECT AVG(ms.sources_count) 
            FROM model_statistics ms 
            WHERE ms.model_id = model_summary.model_id AND ms.sources_count IS NOT NULL
        ), 0.0),
        avg_fields_found = COALESCE((
            SELECT AVG(ms.fields_found) 
            FROM model_statistics ms 
            WHERE ms.model_id = model_summary.model_id AND ms.fields_found IS NOT NULL
        ), 0.0),
        avg_response_time_ms = COALESCE((
            SELECT AVG(ms.response_time_ms) 
            FROM model_statistics ms 
            WHERE ms.model_id = model_summary.model_id AND ms.response_time_ms IS NOT NULL
        ), 0.0)
        WHERE model_id IN (
            SELECT DISTINCT model_id FROM model_statistics
        )
    """)
    
    affected = cursor.rowcount
    print(f"✅ {affected} Modelle - Datenkonsistenz zwischen Tabellen korrigiert")
    
    conn.commit()
    conn.close()

def clean_old_invalid_data():
    """Entfernt alte und ungültige Dateneinträge"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Entferne Einträge mit NULL oder unrealistischen Werten (korrekte Spaltennamen)
    cursor.execute("""
        DELETE FROM model_statistics 
        WHERE success IS NULL 
           OR sources_count IS NULL
           OR sources_count > 50  -- Unrealistisch hohe Quellenzahl
           OR fields_found IS NULL
           OR fields_found > 25   -- Unrealistisch hohe Feldanzahl
    """)
    
    deleted = cursor.rowcount
    print(f"✅ {deleted} ungültige Einträge aus model_statistics entfernt")
    
    conn.commit()
    conn.close()

def validate_fixes():
    """Validiert die durchgeführten Korrekturen"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    print("\n📊 VALIDIERUNG DER KORREKTUREN:")
    
    # Prüfe Modellnamen
    cursor.execute("SELECT DISTINCT model_id FROM model_summary ORDER BY model_id")
    models = [row[0] for row in cursor.fetchall()]
    print(f"✅ Verfügbare Modelle ({len(models)}): {', '.join(models)}")
    
    # Prüfe Erfolgsraten
    cursor.execute("SELECT model_id, success_rate, total_tests FROM model_summary ORDER BY success_rate DESC")
    for model_id, success_rate, total_tests in cursor.fetchall()[:8]:
        print(f"📈 {model_id}: {success_rate:.1%} ({total_tests} Tests)")
    
    # Prüfe Datenkonsistenz
    cursor.execute("""
        SELECT ms.model_id, 
               COUNT(*) as actual_tests,
               msum.total_tests as reported_tests
        FROM model_statistics ms
        JOIN model_summary msum ON ms.model_id = msum.model_id
        GROUP BY ms.model_id, msum.total_tests
        HAVING actual_tests != reported_tests
    """)
    
    inconsistent = cursor.fetchall()
    if inconsistent:
        print(f"⚠️ {len(inconsistent)} Modelle haben noch Konsistenz-Probleme")
    else:
        print("✅ Alle Modelle haben konsistente Testanzahlen")
    
    conn.close()

def main():
    """Hauptfunktion - führt alle Korrekturen durch"""
    print("🔧 DATENBANK-REPARATUR GESTARTET")
    print("=" * 50)
    
    if not DATABASE_PATH.exists():
        print(f"❌ Datenbank nicht gefunden: {DATABASE_PATH}")
        return
    
    # 1. Backup erstellen
    backup_path = backup_database()
    
    try:
        # 2. Modellnamen korrigieren
        print("\n🏷️ Korrigiere Modellnamen...")
        fix_model_names()
        
        # 3. Erfolgsraten korrigieren
        print("\n📊 Korrigiere unrealistische Erfolgsraten...")
        fix_unrealistic_success_rates()
        
        # 4. Datenkonsistenz reparieren
        print("\n🔄 Repariere Datenkonsistenz...")
        fix_data_consistency()
        
        # 5. Alte Daten bereinigen
        print("\n🧹 Bereinige ungültige Daten...")
        clean_old_invalid_data()
        
        # 6. Validierung
        print("\n🔍 Validiere Korrekturen...")
        validate_fixes()
        
        print("\n✅ DATENBANK-REPARATUR ERFOLGREICH ABGESCHLOSSEN")
        print(f"💾 Backup gespeichert unter: {backup_path}")
        
    except Exception as e:
        print(f"\n❌ FEHLER bei Datenbank-Reparatur: {e}")
        print(f"🔄 Stelle Backup wieder her: {backup_path}")
        import shutil
        shutil.copy2(backup_path, DATABASE_PATH)
        raise

if __name__ == "__main__":
    main()