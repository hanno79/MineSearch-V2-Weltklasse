#!/usr/bin/env python3
"""
Author: rahn
Datum: 26.07.2025
Version: 1.0
Beschreibung: SQL-basierte Lösungen für identifizierte Datenbankprobleme
"""

import sqlite3
import json
from datetime import datetime

def apply_database_fixes():
    """Wendet SQL-basierte Fixes für die identifizierten Probleme an"""
    
    db_path = "/app/minesearch_v2/backend/mines.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("=" * 80)
        print("DATENBANK-FIXES ANWENDEN")
        print("=" * 80)
        print(f"Ausführungszeitpunkt: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
        print()
        
        # BACKUP DER AKTUELLEN DATEN
        print("1. BACKUP ERSTELLEN")
        print("-" * 30)
        
        # Export der kritischen Tabellen
        tables_to_backup = ['model_summary', 'model_statistics', 'field_statistics']
        backup_data = {}
        
        for table in tables_to_backup:
            cursor.execute(f"SELECT * FROM {table}")
            backup_data[table] = cursor.fetchall()
            print(f"  ✓ {table}: {len(backup_data[table])} Datensätze gesichert")
        
        # FIX 1: Datenkonsistenz zwischen model_summary und model_statistics
        print("\n2. DATENKONSISTENZ REPARIEREN")
        print("-" * 30)
        
        # Neuberechnung der Testzahlen in model_summary
        cursor.execute("""
            UPDATE model_summary 
            SET total_tests = (
                SELECT COUNT(*) 
                FROM model_statistics 
                WHERE model_statistics.model_id = model_summary.model_id
            ),
            last_updated = datetime('now')
        """)
        
        affected_rows = cursor.rowcount
        print(f"  ✓ {affected_rows} model_summary Einträge aktualisiert")
        
        # FIX 2: Erfolgsraten korrigieren (1.0% zu korrekte Werte)
        print("\n3. ERFOLGSRATEN KORRIGIEREN")
        print("-" * 30)
        
        # Neuberechnung der Erfolgsraten basierend auf model_statistics
        cursor.execute("""
            UPDATE model_summary 
            SET success_rate = (
                SELECT CAST(COUNT(CASE WHEN success = 1 THEN 1 END) AS FLOAT) * 100.0 / COUNT(*)
                FROM model_statistics 
                WHERE model_statistics.model_id = model_summary.model_id
            ),
            data_success_rate = (
                SELECT CAST(COUNT(CASE WHEN success = 1 AND structured_data IS NOT NULL AND structured_data != '{}' THEN 1 END) AS FLOAT) * 100.0 / COUNT(*)
                FROM model_statistics 
                WHERE model_statistics.model_id = model_summary.model_id
            ),
            last_updated = datetime('now')
        """)
        
        affected_rows = cursor.rowcount
        print(f"  ✓ {affected_rows} Erfolgsraten neu berechnet")
        
        # FIX 3: Durchschnittswerte neu berechnen
        print("\n4. DURCHSCHNITTSWERTE NEU BERECHNEN")
        print("-" * 30)
        
        cursor.execute("""
            UPDATE model_summary 
            SET avg_response_time_ms = (
                SELECT AVG(response_time_ms)
                FROM model_statistics 
                WHERE model_statistics.model_id = model_summary.model_id
            ),
            avg_fields_found = (
                SELECT AVG(fields_found)
                FROM model_statistics 
                WHERE model_statistics.model_id = model_summary.model_id
            ),
            avg_sources_count = (
                SELECT AVG(sources_count)
                FROM model_statistics 
                WHERE model_statistics.model_id = model_summary.model_id
            ),
            last_updated = datetime('now')
        """)
        
        affected_rows = cursor.rowcount
        print(f"  ✓ {affected_rows} Durchschnittswerte neu berechnet")
        
        # FIX 4: Field_statistics neu berechnen
        print("\n5. FIELD_STATISTICS NEU BERECHNEN")
        print("-" * 30)
        
        # Lösche veraltete field_statistics
        cursor.execute("DELETE FROM field_statistics")
        print(f"  ✓ Veraltete field_statistics gelöscht")
        
        # Neu berechnen basierend auf aktuellen model_statistics
        cursor.execute("""
            INSERT INTO field_statistics (
                model_id, field_name, total_searches, times_found, times_empty, 
                success_rate, avg_confidence, last_updated, excluded_count, 
                conditional_logic_applied
            )
            SELECT 
                model_id,
                json_extract(value, '$.field') as field_name,
                COUNT(*) as total_searches,
                COUNT(CASE WHEN json_extract(value, '$.found') = 1 THEN 1 END) as times_found,
                COUNT(CASE WHEN json_extract(value, '$.found') = 0 THEN 1 END) as times_empty,
                CAST(COUNT(CASE WHEN json_extract(value, '$.found') = 1 THEN 1 END) AS FLOAT) * 100.0 / COUNT(*) as success_rate,
                AVG(COALESCE(json_extract(value, '$.confidence'), 0.0)) as avg_confidence,
                datetime('now') as last_updated,
                0 as excluded_count,
                0 as conditional_logic_applied
            FROM model_statistics, json_each(structured_data)
            WHERE structured_data IS NOT NULL 
                AND json_valid(structured_data)
                AND json_extract(value, '$.field') IS NOT NULL
            GROUP BY model_id, json_extract(value, '$.field')
        """)
        
        new_field_stats = cursor.rowcount
        print(f"  ✓ {new_field_stats} neue field_statistics Einträge erstellt")
        
        # FIX 5: Validierung und Bereinigung
        print("\n6. DATENVALIDIERUNG")
        print("-" * 30)
        
        # Entferne unmögliche Werte
        cursor.execute("UPDATE model_summary SET success_rate = 100.0 WHERE success_rate > 100.0")
        cursor.execute("UPDATE model_summary SET data_success_rate = 100.0 WHERE data_success_rate > 100.0")
        cursor.execute("UPDATE field_statistics SET success_rate = 100.0 WHERE success_rate > 100.0")
        cursor.execute("UPDATE field_statistics SET avg_confidence = 1.0 WHERE avg_confidence > 1.0")
        
        print(f"  ✓ Unmögliche Prozentwerte korrigiert")
        
        # Setze NULL-Werte auf vernünftige Defaults
        cursor.execute("UPDATE model_summary SET estimated_cost_per_request = 0.0 WHERE estimated_cost_per_request IS NULL")
        cursor.execute("UPDATE model_summary SET total_estimated_cost = 0.0 WHERE total_estimated_cost IS NULL")
        
        print(f"  ✓ NULL-Werte durch Defaults ersetzt")
        
        # VERIFICATION: Überprüfe die Fixes
        print("\n7. VERIFIKATION DER FIXES")
        print("-" * 30)
        
        # Prüfe korrigierte Erfolgsraten
        cursor.execute("""
            SELECT model_id, success_rate, data_success_rate, total_tests, avg_sources_count
            FROM model_summary 
            ORDER BY model_id
        """)
        corrected_data = cursor.fetchall()
        
        print("Korrigierte model_summary Daten:")
        for model_id, success_rate, data_success_rate, total_tests, avg_sources in corrected_data:
            print(f"  {model_id}:")
            print(f"    Erfolgsrate: {success_rate:.1f}%")
            print(f"    Daten-Erfolgsrate: {data_success_rate:.1f}%")
            print(f"    Tests: {total_tests}")
            print(f"    Durchschn. Quellen: {avg_sources:.1f}")
        
        # Prüfe field_statistics
        cursor.execute("SELECT COUNT(*) FROM field_statistics")
        field_count = cursor.fetchone()[0]
        print(f"\nfeld_statistics: {field_count} Einträge")
        
        # Prüfe auf verbleibende Anomalien
        cursor.execute("SELECT COUNT(*) FROM model_summary WHERE success_rate > 100")
        anomalies = cursor.fetchone()[0]
        print(f"Verbleibende Anomalien (>100%): {anomalies}")
        
        conn.commit()
        print(f"\n✓ Alle Änderungen gespeichert")
        
        # ROLLBACK INFORMATION
        print("\n8. ROLLBACK-INFORMATION")
        print("-" * 30)
        print("Falls ein Rollback benötigt wird:")
        print("1. Führen Sie database_rollback.py aus")
        print("2. Oder restaurieren Sie aus dem Backup")
        print(f"3. Backup-Timestamp: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
        
        conn.close()
        
        # Speichere Backup für Rollback
        with open('/app/minesearch_v2/backend/backup_data.json', 'w') as f:
            # Konvertiere Backup-Daten zu JSON-serialisierbarem Format
            json_backup = {}
            for table, data in backup_data.items():
                json_backup[table] = [list(row) for row in data]
            json.dump(json_backup, f, indent=2, default=str)
        
        print(f"\n✓ Backup gespeichert in backup_data.json")
        
        print("\n" + "=" * 80)
        print("DATENBANK-FIXES ERFOLGREICH ANGEWENDET")
        print("=" * 80)
        
    except Exception as e:
        print(f"FEHLER beim Anwenden der Fixes: {e}")
        print("Führen Sie ein Rollback durch falls nötig.")
        if 'conn' in locals():
            conn.rollback()
            conn.close()

def generate_sql_queries():
    """Generiert die verwendeten SQL-Queries für Dokumentationszwecke"""
    
    queries = {
        "datenkonsistenz_fix": """
            UPDATE model_summary 
            SET total_tests = (
                SELECT COUNT(*) 
                FROM model_statistics 
                WHERE model_statistics.model_id = model_summary.model_id
            ),
            last_updated = datetime('now');
        """,
        
        "erfolgsraten_fix": """
            UPDATE model_summary 
            SET success_rate = (
                SELECT CAST(COUNT(CASE WHEN success = 1 THEN 1 END) AS FLOAT) * 100.0 / COUNT(*)
                FROM model_statistics 
                WHERE model_statistics.model_id = model_summary.model_id
            ),
            data_success_rate = (
                SELECT CAST(COUNT(CASE WHEN success = 1 AND structured_data IS NOT NULL AND structured_data != '{}' THEN 1 END) AS FLOAT) * 100.0 / COUNT(*)
                FROM model_statistics 
                WHERE model_statistics.model_id = model_summary.model_id
            ),
            last_updated = datetime('now');
        """,
        
        "durchschnittswerte_fix": """
            UPDATE model_summary 
            SET avg_response_time_ms = (
                SELECT AVG(response_time_ms)
                FROM model_statistics 
                WHERE model_statistics.model_id = model_summary.model_id
            ),
            avg_fields_found = (
                SELECT AVG(fields_found)
                FROM model_statistics 
                WHERE model_statistics.model_id = model_summary.model_id
            ),
            avg_sources_count = (
                SELECT AVG(sources_count)
                FROM model_statistics 
                WHERE model_statistics.model_id = model_summary.model_id
            ),
            last_updated = datetime('now');
        """,
        
        "field_statistics_rebuild": """
            DELETE FROM field_statistics;
            
            INSERT INTO field_statistics (
                model_id, field_name, total_searches, times_found, times_empty, 
                success_rate, avg_confidence, last_updated, excluded_count, 
                conditional_logic_applied
            )
            SELECT 
                model_id,
                json_extract(value, '$.field') as field_name,
                COUNT(*) as total_searches,
                COUNT(CASE WHEN json_extract(value, '$.found') = 1 THEN 1 END) as times_found,
                COUNT(CASE WHEN json_extract(value, '$.found') = 0 THEN 1 END) as times_empty,
                CAST(COUNT(CASE WHEN json_extract(value, '$.found') = 1 THEN 1 END) AS FLOAT) * 100.0 / COUNT(*) as success_rate,
                AVG(COALESCE(json_extract(value, '$.confidence'), 0.0)) as avg_confidence,
                datetime('now') as last_updated,
                0 as excluded_count,
                0 as conditional_logic_applied
            FROM model_statistics, json_each(structured_data)
            WHERE structured_data IS NOT NULL 
                AND json_valid(structured_data)
                AND json_extract(value, '$.field') IS NOT NULL
            GROUP BY model_id, json_extract(value, '$.field');
        """,
        
        "datenvalidierung": """
            UPDATE model_summary SET success_rate = 100.0 WHERE success_rate > 100.0;
            UPDATE model_summary SET data_success_rate = 100.0 WHERE data_success_rate > 100.0;
            UPDATE field_statistics SET success_rate = 100.0 WHERE success_rate > 100.0;
            UPDATE field_statistics SET avg_confidence = 1.0 WHERE avg_confidence > 1.0;
            UPDATE model_summary SET estimated_cost_per_request = 0.0 WHERE estimated_cost_per_request IS NULL;
            UPDATE model_summary SET total_estimated_cost = 0.0 WHERE total_estimated_cost IS NULL;
        """
    }
    
    print("\n" + "=" * 80)
    print("VERWENDETE SQL-QUERIES")
    print("=" * 80)
    
    for name, query in queries.items():
        print(f"\n{name.upper()}:")
        print("-" * 40)
        print(query.strip())

if __name__ == "__main__":
    print("WARNUNG: Dieses Skript modifiziert die Datenbank!")
    print("Stellen Sie sicher, dass Sie ein Backup haben.")
    
    response = input("\nMöchten Sie die Fixes anwenden? (ja/nein): ")
    if response.lower() in ['ja', 'j', 'yes', 'y']:
        apply_database_fixes()
    else:
        print("Vorgang abgebrochen.")
        
    print("\nSQL-Queries für Dokumentation:")
    generate_sql_queries()