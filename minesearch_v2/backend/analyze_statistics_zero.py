#!/usr/bin/env python3
"""
Author: rahn
Datum: 26.07.2025
Version: 1.0
Beschreibung: Analysiere warum alle Statistik-Werte 0 sind
"""

import sqlite3
import json
from datetime import datetime

def analyze_database():
    """Analysiere Datenbank-Inhalte für Statistik-Probleme"""
    
    # Verbindung zur Datenbank
    conn = sqlite3.connect('mines.db')
    cursor = conn.cursor()
    
    print('=== DATABASE ANALYSIS - ZERO VALUES INVESTIGATION ===')
    print(f'Analysis timestamp: {datetime.now().isoformat()}')
    print()
    
    # 1. Tabellen-Strukturen und Anzahlen anzeigen
    tables = ['model_statistics', 'model_summary', 'field_statistics', 'search_results']
    for table in tables:
        try:
            cursor.execute(f'SELECT COUNT(*) FROM {table}')
            count = cursor.fetchone()[0]
            print(f'{table}: {count} records')
            
            if count > 0:
                cursor.execute(f'PRAGMA table_info({table})')
                columns = [col[1] for col in cursor.fetchall()]
                print(f'  Columns: {", ".join(columns)}')
                
                # Erste 2 Einträge anzeigen
                cursor.execute(f'SELECT * FROM {table} LIMIT 2')
                rows = cursor.fetchall()
                if rows:
                    for i, row in enumerate(rows[:2]):
                        print(f'  Sample {i+1}: {row}')
        except Exception as e:
            print(f'{table}: ERROR - {e}')
        print()
    
    # 2. Model Summary Details
    print('=== MODEL SUMMARY ANALYSIS ===')
    try:
        cursor.execute('SELECT * FROM model_summary')
        summaries = cursor.fetchall()
        cursor.execute('PRAGMA table_info(model_summary)')
        columns = [col[1] for col in cursor.fetchall()]
        
        if summaries:
            for summary in summaries:
                data = dict(zip(columns, summary))
                print(f'Model: {data["model_id"]}')
                for key, value in data.items():
                    if key != 'model_id':
                        print(f'  {key}: {value}')
                print()
        else:
            print('No model summaries found!')
            
    except Exception as e:
        print(f'ERROR reading model_summary: {e}')
    print()
    
    # 3. Model Statistics Aggregation
    print('=== MODEL STATISTICS ANALYSIS ===')
    try:
        cursor.execute('''
            SELECT 
                model_id, 
                COUNT(*) as total_records,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_records,
                AVG(CAST(success as FLOAT)) as success_rate,
                AVG(fields_found) as avg_fields,
                AVG(response_time_ms) as avg_response_time,
                MIN(timestamp) as first_test,
                MAX(timestamp) as last_test
            FROM model_statistics 
            GROUP BY model_id 
            LIMIT 10
        ''')
        stats = cursor.fetchall()
        
        if stats:
            print('Model Statistics Aggregation:')
            for stat in stats:
                print(f'  Model {stat[0]}:')
                print(f'    Total records: {stat[1]}')
                print(f'    Successful: {stat[2]}')
                print(f'    Success rate: {stat[3]:.2f}' if stat[3] else '    Success rate: None')
                print(f'    Avg fields: {stat[4]:.2f}' if stat[4] else '    Avg fields: None')
                print(f'    Avg response time: {stat[5]:.2f}ms' if stat[5] else '    Avg response time: None')
                print(f'    Time range: {stat[6]} to {stat[7]}')
                print()
        else:
            print('No model statistics found!')
            
    except Exception as e:
        print(f'ERROR reading model_statistics: {e}')
    print()
    
    # 4. Field Statistics Analysis
    print('=== FIELD STATISTICS ANALYSIS ===')
    try:
        cursor.execute('''
            SELECT 
                model_id,
                field_name,
                total_searches,
                times_found,
                times_empty,
                success_rate
            FROM field_statistics 
            ORDER BY model_id, field_name
            LIMIT 20
        ''')
        field_stats = cursor.fetchall()
        
        if field_stats:
            print('Field Statistics:')
            for stat in field_stats:
                print(f'  {stat[0]} - {stat[1]}: searches={stat[2]}, found={stat[3]}, empty={stat[4]}, rate={stat[5]:.2f}')
        else:
            print('No field statistics found!')
            
    except Exception as e:
        print(f'ERROR reading field_statistics: {e}')
    print()
    
    # 5. Search Results Analysis
    print('=== SEARCH RESULTS ANALYSIS ===')
    try:
        cursor.execute('''
            SELECT 
                model_used,
                COUNT(*) as total_searches,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_searches,
                AVG(search_duration) as avg_duration
            FROM search_results 
            GROUP BY model_used
            ORDER BY total_searches DESC
            LIMIT 10
        ''')
        search_stats = cursor.fetchall()
        
        if search_stats:
            print('Search Results by Model:')
            for stat in search_stats:
                print(f'  {stat[0]}: total={stat[1]}, successful={stat[2]}, avg_duration={stat[3]:.2f}s' if stat[3] else f'  {stat[0]}: total={stat[1]}, successful={stat[2]}, avg_duration=None')
        else:
            print('No search results found!')
            
    except Exception as e:
        print(f'ERROR reading search_results: {e}')
    print()
    
    # 6. Data Connection Analysis - überprüfe Verbindung zwischen Tabellen
    print('=== DATA CONNECTION ANALYSIS ===')
    try:
        # Suche nach SearchResults ohne entsprechende ModelStatistics
        cursor.execute('''
            SELECT COUNT(*) as orphaned_searches
            FROM search_results sr
            LEFT JOIN model_statistics ms ON sr.mine_name = ms.mine_name AND sr.model_used = ms.model_id
            WHERE ms.id IS NULL
        ''')
        orphaned = cursor.fetchone()[0]
        print(f'SearchResults without ModelStatistics: {orphaned}')
        
        # Suche nach ModelStatistics ohne entsprechende ModelSummary
        cursor.execute('''
            SELECT ms.model_id, COUNT(*) as stats_count
            FROM model_statistics ms
            LEFT JOIN model_summary sum ON ms.model_id = sum.model_id
            WHERE sum.model_id IS NULL
            GROUP BY ms.model_id
        ''')
        no_summary = cursor.fetchall()
        if no_summary:
            print('ModelStatistics without ModelSummary:')
            for stat in no_summary:
                print(f'  {stat[0]}: {stat[1]} statistics records')
        else:
            print('All ModelStatistics have corresponding ModelSummary')
            
    except Exception as e:
        print(f'ERROR in connection analysis: {e}')
    
    # 7. Raw Data Sample für Debugging
    print('\n=== RAW DATA SAMPLES FOR DEBUGGING ===')
    try:
        # Ein konkretes Beispiel aus ModelStatistics
        cursor.execute('SELECT * FROM model_statistics WHERE fields_found > 0 LIMIT 1')
        ms_sample = cursor.fetchone()
        if ms_sample:
            cursor.execute('PRAGMA table_info(model_statistics)')
            ms_columns = [col[1] for col in cursor.fetchall()]
            ms_data = dict(zip(ms_columns, ms_sample))
            print('ModelStatistics sample with fields_found > 0:')
            for key, value in ms_data.items():
                print(f'  {key}: {value}')
        else:
            print('No ModelStatistics records with fields_found > 0 found!')
            
        print()
        
        # Ein konkretes Beispiel aus SearchResults
        cursor.execute('SELECT * FROM search_results WHERE structured_data IS NOT NULL LIMIT 1')
        sr_sample = cursor.fetchone()
        if sr_sample:
            cursor.execute('PRAGMA table_info(search_results)')
            sr_columns = [col[1] for col in cursor.fetchall()]
            sr_data = dict(zip(sr_columns, sr_sample))
            print('SearchResults sample with structured_data:')
            for key, value in sr_data.items():
                if key == 'structured_data' and value:
                    try:
                        data = json.loads(value)
                        print(f'  {key}: {len(data)} fields - {list(data.keys())[:5]}...')
                    except:
                        print(f'  {key}: {str(value)[:100]}...')
                else:
                    print(f'  {key}: {value}')
        else:
            print('No SearchResults with structured_data found!')
            
    except Exception as e:
        print(f'ERROR in raw data analysis: {e}')
    
    conn.close()
    print('\n=== ANALYSIS COMPLETE ===')

if __name__ == "__main__":
    analyze_database()