#!/usr/bin/env python3
"""
Author: rahn
Datum: 26.07.2025
Version: 1.0
Beschreibung: Detaillierte Problemanalyse für spezifische Datenbankissues
"""

import sqlite3
import json
from datetime import datetime
from collections import defaultdict

def detailed_problem_analysis():
    """Detaillierte Analyse der spezifischen Datenbankprobleme"""
    
    db_path = "/app/minesearch_v2/backend/mines.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("=" * 80)
        print("DETAILLIERTE PROBLEMANALYSE - MINESEARCH V2")
        print("=" * 80)
        print(f"Analysezeitpunkt: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
        print()
        
        # PROBLEM 1: Fehlende Modelle "nemotron super" und "cypher alpha"
        print("PROBLEM 1: FEHLENDE MODELLE")
        print("=" * 50)
        
        # Alle verfügbaren Modelle aus model_statistics
        cursor.execute("SELECT DISTINCT model_id FROM model_statistics ORDER BY model_id")
        available_models = [row[0] for row in cursor.fetchall()]
        
        print(f"Verfügbare Modelle in model_statistics ({len(available_models)}):")
        for model in available_models:
            print(f"  - {model}")
        
        # Modelle aus search_results
        cursor.execute("SELECT DISTINCT model_used FROM search_results WHERE model_used IS NOT NULL ORDER BY model_used")
        search_models = [row[0] for row in cursor.fetchall()]
        
        print(f"\nModelle in search_results ({len(search_models)}):")
        for model in search_models:
            print(f"  - {model}")
        
        # Prüfe model_summary
        cursor.execute("SELECT model_id FROM model_summary ORDER BY model_id")
        summary_models = [row[0] for row in cursor.fetchall()]
        
        print(f"\nModelle in model_summary ({len(summary_models)}):")
        for model in summary_models:
            print(f"  - {model}")
        
        print("\nANALYSE:")
        target_models = ["nemotron super", "cypher alpha"]
        for target in target_models:
            found_anywhere = (
                target in available_models or 
                target in search_models or 
                target in summary_models
            )
            print(f"  ✗ '{target}': {'GEFUNDEN' if found_anywhere else 'NICHT GEFUNDEN'}")
        
        # PROBLEM 2: Details-Tabelle "0 Quellen mit 100% Erfolgsrate"
        print("\n\nPROBLEM 2: DETAILS-TABELLE ANOMALIEN")
        print("=" * 50)
        
        # Analysiere model_summary für 100% Erfolgsraten
        cursor.execute("""
            SELECT model_id, success_rate, data_success_rate, total_tests, 
                   avg_sources_count, estimated_cost_per_request
            FROM model_summary 
            ORDER BY model_id
        """)
        summary_data = cursor.fetchall()
        
        print("model_summary Daten:")
        for row in summary_data:
            model_id, success_rate, data_success_rate, total_tests, avg_sources, cost = row
            print(f"  Modell: {model_id}")
            print(f"    Erfolgsrate: {success_rate}%")
            print(f"    Daten-Erfolgsrate: {data_success_rate}%")
            print(f"    Tests: {total_tests}")
            print(f"    Durchschn. Quellen: {avg_sources}")
            print(f"    Kosten pro Request: {cost}")
            
            # Prüfe auf problematische Muster
            if success_rate == 100.0 and avg_sources == 0:
                print(f"    ⚠️  PROBLEM: 100% Erfolgsrate mit 0 Quellen!")
            elif success_rate > 100:
                print(f"    ⚠️  PROBLEM: Erfolgsrate über 100%!")
        
        # Analysiere field_statistics für Anomalien
        print("\nfield_statistics Anomalien:")
        cursor.execute("""
            SELECT model_id, field_name, success_rate, times_found, times_empty, total_searches
            FROM field_statistics 
            WHERE success_rate > 100 OR (success_rate = 100 AND times_found = 0)
            ORDER BY model_id, field_name
        """)
        field_anomalies = cursor.fetchall()
        
        if field_anomalies:
            for row in field_anomalies:
                model, field, rate, found, empty, total = row
                print(f"  {model}.{field}: {rate}% (gefunden: {found}, leer: {empty}, total: {total})")
        else:
            print("  Keine Anomalien in field_statistics gefunden")
        
        # PROBLEM 3: Performance-Daten über 100%
        print("\n\nPROBLEM 3: PERFORMANCE-ANOMALIEN")
        print("=" * 50)
        
        # Prüfe alle numerischen Felder auf Werte über 100%
        tables_to_check = [
            ('model_summary', ['success_rate', 'data_success_rate', 'overall_consistency']),
            ('field_statistics', ['success_rate', 'avg_confidence']),
            ('model_statistics', ['response_time_ms'])  # Hier könnten unrealistische Werte sein
        ]
        
        for table_name, columns in tables_to_check:
            print(f"\nTabelle: {table_name}")
            for column in columns:
                try:
                    if 'rate' in column.lower() or 'consistency' in column.lower() or 'confidence' in column.lower():
                        # Prozent-basierte Felder sollten <= 100 sein
                        cursor.execute(f"""
                            SELECT {column}, COUNT(*) as count 
                            FROM {table_name} 
                            WHERE {column} > 100 
                            GROUP BY {column}
                            ORDER BY {column} DESC
                        """)
                        over_100 = cursor.fetchall()
                        
                        if over_100:
                            print(f"  {column} > 100%:")
                            for value, count in over_100:
                                print(f"    Wert: {value}%, Häufigkeit: {count}")
                        
                        # Auch exakt 100% mit verdächtigen Kombinationen prüfen
                        if column == 'success_rate':
                            cursor.execute(f"""
                                SELECT model_id, {column}, avg_sources_count, total_tests
                                FROM {table_name} 
                                WHERE {column} = 100 AND avg_sources_count = 0
                            """)
                            suspicious_100 = cursor.fetchall()
                            
                            if suspicious_100:
                                print(f"  Verdächtige 100% Werte (mit 0 Quellen):")
                                for model, rate, sources, tests in suspicious_100:
                                    print(f"    {model}: {rate}% mit {sources} Quellen ({tests} Tests)")
                    
                    elif 'response_time' in column.lower():
                        # Response times über 60 Sekunden (60000ms) sind verdächtig
                        cursor.execute(f"""
                            SELECT {column}, COUNT(*) as count 
                            FROM {table_name} 
                            WHERE {column} > 60000 
                            GROUP BY {column}
                            ORDER BY {column} DESC
                            LIMIT 10
                        """)
                        slow_responses = cursor.fetchall()
                        
                        if slow_responses:
                            print(f"  {column} > 60 Sekunden:")
                            for value, count in slow_responses:
                                print(f"    Wert: {value}ms ({value/1000:.1f}s), Häufigkeit: {count}")
                        
                except Exception as e:
                    print(f"  Fehler bei {column}: {e}")
        
        # PROBLEM 4: Datenintegrität und Timestamps
        print("\n\nPROBLEM 4: DATENINTEGRITÄT")
        print("=" * 50)
        
        # Prüfe auf veraltete Daten
        cursor.execute("""
            SELECT 
                MIN(last_updated) as oldest_update,
                MAX(last_updated) as newest_update,
                COUNT(*) as total_records
            FROM model_summary
        """)
        summary_timestamps = cursor.fetchone()
        
        if summary_timestamps[0]:
            print(f"model_summary Timestamps:")
            print(f"  Älteste Aktualisierung: {summary_timestamps[0]}")
            print(f"  Neueste Aktualisierung: {summary_timestamps[1]}")
            print(f"  Gesamte Datensätze: {summary_timestamps[2]}")
        
        # Prüfe auf inkonsistente Daten zwischen Tabellen
        cursor.execute("""
            SELECT 
                ms.model_id,
                ms.total_tests as summary_tests,
                COUNT(stat.id) as statistics_records
            FROM model_summary ms
            LEFT JOIN model_statistics stat ON ms.model_id = stat.model_id
            GROUP BY ms.model_id, ms.total_tests
        """)
        consistency_check = cursor.fetchall()
        
        print(f"\nDatenkonsistenz zwischen model_summary und model_statistics:")
        for model, summary_tests, stat_records in consistency_check:
            if summary_tests != stat_records:
                print(f"  ⚠️  {model}: Summary zeigt {summary_tests} Tests, aber {stat_records} Records in statistics")
            else:
                print(f"  ✓ {model}: {summary_tests} Tests konsistent")
        
        # LÖSUNGSVORSCHLÄGE
        print("\n\nLÖSUNGSVORSCHLÄGE")
        print("=" * 50)
        
        print("1. FEHLENDE MODELLE:")
        print("   - Prüfen Sie die Konfiguration der Provider")
        print("   - Überprüfen Sie die Modell-IDs in der Provider-Konfiguration")
        print("   - Möglicherweise wurden diese Modelle nicht getestet oder sind inaktiv")
        
        print("\n2. ERFOLGSRATEN-ANOMALIEN:")
        print("   - Bereinigen Sie Datensätze mit 100% Erfolgsrate bei 0 Quellen")
        print("   - Überprüfen Sie die Berechnungslogik für Erfolgsraten")
        print("   - Implementieren Sie Validierung für unmögliche Werte")
        
        print("\n3. PERFORMANCE-ANOMALIEN:")
        print("   - Begrenzen Sie Prozentwerte auf 0-100 Bereich")
        print("   - Prüfen Sie Response-Times über 60 Sekunden auf Plausibilität")
        print("   - Implementieren Sie Data-Validation vor dem Einfügen")
        
        print("\n4. DATENINTEGRITÄT:")
        print("   - Synchronisieren Sie Zähler zwischen verwandten Tabellen")
        print("   - Implementieren Sie regelmäßige Datenvalidierung")
        print("   - Aktualisieren Sie veraltete Timestamps")
        
        conn.close()
        
        print("\n" + "=" * 80)
        print("DETAILLIERTE PROBLEMANALYSE ABGESCHLOSSEN")
        print("=" * 80)
        
    except Exception as e:
        print(f"FEHLER bei detaillierter Problemanalyse: {e}")

if __name__ == "__main__":
    detailed_problem_analysis()