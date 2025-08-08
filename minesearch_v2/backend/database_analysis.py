#!/usr/bin/env python3
"""
Author: rahn
Datum: 26.07.2025
Version: 1.0
Beschreibung: Detaillierte Analyse der mines.db Datenbank zur Identifikation von Datenproblemen
"""

import sqlite3
import json
from datetime import datetime

def analyze_database():
    """Führt eine umfassende Analyse der mines.db Datenbank durch"""
    
    db_path = "/app/minesearch_v2/backend/mines.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("=" * 80)
        print("MINESEARCH V2 - DATENBANKANALYSE")
        print("=" * 80)
        print(f"Analysezeitpunkt: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
        print(f"Datenbankpfad: {db_path}")
        print()
        
        # 1. TABELLEN STRUKTUR ANALYSIEREN
        print("1. DATENBANKSTRUKTUR")
        print("-" * 40)
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"Gefundene Tabellen: {len(tables)}")
        for table in tables:
            table_name = table[0]
            print(f"  - {table_name}")
            
            # Zeilen zählen
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"    Datensätze: {count}")
            
            # Schema anzeigen
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            print("    Spalten:")
            for col in columns:
                print(f"      - {col[1]} ({col[2]})")
        
        print()
        
        # 2. MODELL-SUCHE: nemotron super und cypher alpha
        print("2. MODELL-SUCHE")
        print("-" * 40)
        
        target_models = ["nemotron super", "cypher alpha"]
        found_models = {}
        all_models = set()
        
        for table in tables:
            table_name = table[0]
            
            # Alle Spalten einer Tabelle durchsuchen
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            for col in columns:
                col_name = col[1]
                
                # Prüfen ob Spalte Modell-relevante Namen enthält
                if any(keyword in col_name.lower() for keyword in ['model', 'provider', 'source']):
                    try:
                        cursor.execute(f"SELECT DISTINCT {col_name} FROM {table_name} WHERE {col_name} IS NOT NULL")
                        values = cursor.fetchall()
                        
                        for value in values:
                            if value[0]:
                                model_name = str(value[0]).lower()
                                all_models.add(str(value[0]))
                                
                                for target in target_models:
                                    if target.lower() in model_name:
                                        if target not in found_models:
                                            found_models[target] = []
                                        found_models[target].append({
                                            'table': table_name,
                                            'column': col_name,
                                            'value': value[0]
                                        })
                    except Exception as e:
                        print(f"    Fehler bei {table_name}.{col_name}: {e}")
        
        print("Gesuchte Modelle:")
        for model in target_models:
            if model in found_models:
                print(f"  ✓ '{model}' GEFUNDEN:")
                for entry in found_models[model]:
                    print(f"    - Tabelle: {entry['table']}, Spalte: {entry['column']}, Wert: {entry['value']}")
            else:
                print(f"  ✗ '{model}' NICHT GEFUNDEN")
        
        print(f"\nAlle gefundenen Modelle/Provider ({len(all_models)}):")
        for model in sorted(all_models):
            print(f"  - {model}")
        
        print()
        
        # 3. DETAILS-TABELLE PROBLEM ANALYSIEREN
        print("3. DETAILS-TABELLE ANALYSE")
        print("-" * 40)
        
        # Suche nach batch_results oder ähnlichen Tabellen
        detail_tables = [t[0] for t in tables if 'result' in t[0].lower() or 'detail' in t[0].lower()]
        
        for table_name in detail_tables:
            print(f"Analyse von Tabelle: {table_name}")
            
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            col_names = [col[1] for col in columns]
            
            # Suche nach Spalten mit Erfolgsraten oder Quellenangaben
            rate_columns = [col for col in col_names if any(keyword in col.lower() for keyword in ['rate', 'success', 'prozent', 'percent'])]
            source_columns = [col for col in col_names if any(keyword in col.lower() for keyword in ['source', 'quelle', 'count', 'anzahl'])]
            
            print(f"  Rate-Spalten: {rate_columns}")
            print(f"  Quellen-Spalten: {source_columns}")
            
            # Prüfe auf "0 Quellen mit 100% Erfolgsrate" Pattern
            try:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 10")
                sample_data = cursor.fetchall()
                
                print(f"  Beispieldaten (erste 10 Einträge):")
                for i, row in enumerate(sample_data[:3]):  # Nur erste 3 zeigen
                    print(f"    Zeile {i+1}: {row}")
                
                # Suche nach problematischen Mustern
                for rate_col in rate_columns:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {rate_col} = 100 OR {rate_col} = '100%'")
                    high_rate_count = cursor.fetchone()[0]
                    print(f"  Einträge mit 100% in {rate_col}: {high_rate_count}")
                
                for source_col in source_columns:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {source_col} = 0")
                    zero_source_count = cursor.fetchone()[0]
                    print(f"  Einträge mit 0 in {source_col}: {zero_source_count}")
                    
            except Exception as e:
                print(f"  Fehler bei Analyse: {e}")
        
        print()
        
        # 4. PERFORMANCE-ANOMALIEN SUCHEN
        print("4. PERFORMANCE-ANOMALIEN")
        print("-" * 40)
        
        for table_name in [t[0] for t in tables]:
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            for col in columns:
                col_name = col[1]
                col_type = col[2]
                
                # Prüfe numerische Spalten auf Werte über 100%
                if any(keyword in col_name.lower() for keyword in ['rate', 'percent', 'prozent', 'erfolg', 'success']):
                    try:
                        cursor.execute(f"SELECT {col_name}, COUNT(*) as count FROM {table_name} WHERE CAST({col_name} AS REAL) > 100 GROUP BY {col_name}")
                        anomalies = cursor.fetchall()
                        
                        if anomalies:
                            print(f"  Anomalien in {table_name}.{col_name}:")
                            for anomaly in anomalies:
                                print(f"    Wert: {anomaly[0]}, Häufigkeit: {anomaly[1]}")
                    except Exception as e:
                        # Spalte ist möglicherweise nicht numerisch
                        pass
        
        # 5. DATENINTEGRITÄT PRÜFUNG
        print("\n5. DATENINTEGRITÄT")
        print("-" * 40)
        
        for table_name in [t[0] for t in tables]:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            total_count = cursor.fetchone()[0]
            
            if total_count > 0:
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                
                for col in columns:
                    col_name = col[1]
                    
                    # Prüfe auf NULL-Werte
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {col_name} IS NULL")
                    null_count = cursor.fetchone()[0]
                    
                    if null_count > 0:
                        null_percent = (null_count / total_count) * 100
                        if null_percent > 10:  # Mehr als 10% NULL-Werte
                            print(f"  {table_name}.{col_name}: {null_percent:.1f}% NULL-Werte ({null_count}/{total_count})")
        
        conn.close()
        
        print("\n" + "=" * 80)
        print("ANALYSE ABGESCHLOSSEN")
        print("=" * 80)
        
    except Exception as e:
        print(f"FEHLER bei Datenbankanalyse: {e}")

if __name__ == "__main__":
    analyze_database()