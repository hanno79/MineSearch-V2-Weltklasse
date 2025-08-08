#!/usr/bin/env python3
"""
Author: rahn
Datum: 26.07.2025
Version: 1.0
Beschreibung: Untersuche getrennte Datenflüsse zwischen SearchResults und ModelStatistics
"""

import sqlite3
import json
from datetime import datetime, timedelta

def investigate_data_flows():
    """Untersuche warum SearchResults und ModelStatistics unterschiedliche Erfolgsraten haben"""
    
    conn = sqlite3.connect('mines.db')
    cursor = conn.cursor()
    
    print('=== INVESTIGATING DATA FLOWS ===')
    print(f'Investigation timestamp: {datetime.now().isoformat()}')
    print()
    
    # 1. Zeitanalyse - wann wurden die verschiedenen Einträge erstellt?
    print('=== TEMPORAL ANALYSIS ===')
    
    cursor.execute('''
        SELECT 
            'SearchResults' as table_name,
            COUNT(*) as total_count,
            MIN(search_timestamp) as earliest,
            MAX(search_timestamp) as latest,
            COUNT(CASE WHEN success = 1 THEN 1 END) as successful_count
        FROM search_results
        UNION ALL
        SELECT 
            'ModelStatistics' as table_name,
            COUNT(*) as total_count,
            MIN(timestamp) as earliest,
            MAX(timestamp) as latest,
            COUNT(CASE WHEN success = 1 THEN 1 END) as successful_count
        FROM model_statistics
    ''')
    
    results = cursor.fetchall()
    for result in results:
        table, total, earliest, latest, successful = result
        print(f'{table}:')
        print(f'  Total: {total}')
        print(f'  Successful: {successful}')
        print(f'  Success Rate: {(successful/total)*100:.1f}%' if total > 0 else '  Success Rate: 0%')
        print(f'  Time Range: {earliest} to {latest}')
        print()
    
    # 2. Sessions-Analyse - sind SearchResults aus batch operations?
    print('=== SESSION ANALYSIS ===')
    
    cursor.execute('''
        SELECT 
            session_id,
            COUNT(*) as count,
            COUNT(DISTINCT model_used) as unique_models,
            MIN(search_timestamp) as session_start,
            MAX(search_timestamp) as session_end
        FROM search_results
        WHERE session_id IS NOT NULL
        GROUP BY session_id
        ORDER BY session_start DESC
        LIMIT 5
    ''')
    
    sessions = cursor.fetchall()
    print('Recent Search Sessions:')
    for session in sessions:
        session_id, count, models, start, end = session
        print(f'  Session {session_id[:8]}...:')
        print(f'    {count} searches across {models} models')
        print(f'    Time: {start} to {end}')
        
        # Check if there are ModelStatistics for this session
        cursor.execute('''
            SELECT COUNT(*) 
            FROM model_statistics ms
            JOIN search_results sr ON ms.mine_name = sr.mine_name AND ms.model_id = sr.model_used
            WHERE sr.session_id = ?
        ''', (session_id,))
        
        matching_stats = cursor.fetchone()[0]
        print(f'    Matching ModelStatistics: {matching_stats}')
        print()
    
    # 3. Model Mismatch Analyse
    print('=== MODEL MISMATCH ANALYSIS ===')
    
    cursor.execute('''
        SELECT 
            sr.model_used,
            COUNT(sr.id) as search_results_count,
            COUNT(ms.id) as model_statistics_count,
            AVG(CASE WHEN sr.success = 1 THEN 1.0 ELSE 0.0 END) as sr_success_rate,
            AVG(CASE WHEN ms.success = 1 THEN 1.0 ELSE 0.0 END) as ms_success_rate
        FROM search_results sr
        LEFT JOIN model_statistics ms ON sr.model_used = ms.model_id AND sr.mine_name = ms.mine_name
        GROUP BY sr.model_used
        ORDER BY search_results_count DESC
        LIMIT 8
    ''')
    
    model_comparison = cursor.fetchall()
    print('Model Comparison (SearchResults vs ModelStatistics):')
    print('Model | SR Count | MS Count | SR Success | MS Success')
    print('-' * 60)
    for comp in model_comparison:
        model, sr_count, ms_count, sr_success, ms_success = comp
        sr_pct = (sr_success or 0) * 100
        ms_pct = (ms_success or 0) * 100
        print(f'{model[:25]:<25} | {sr_count:>8} | {ms_count:>8} | {sr_pct:>8.1f}% | {ms_pct:>8.1f}%')
    
    print()
    
    # 4. Error Message Analysis für ModelStatistics
    print('=== MODEL STATISTICS ERROR ANALYSIS ===')
    
    cursor.execute('''
        SELECT 
            error_message,
            COUNT(*) as count,
            COUNT(DISTINCT model_id) as models_affected,
            MIN(timestamp) as first_seen,
            MAX(timestamp) as last_seen
        FROM model_statistics
        WHERE error_message IS NOT NULL
        GROUP BY error_message
        ORDER BY count DESC
        LIMIT 10
    ''')
    
    errors = cursor.fetchall()
    if errors:
        print('Common Error Messages in ModelStatistics:')
        for error in errors:
            error_msg, count, models, first, last = error
            print(f'  "{error_msg}":')
            print(f'    Count: {count} across {models} models')
            print(f'    Period: {first} to {last}')
            print()
    else:
        print('No error messages found in ModelStatistics')
    
    # 5. Suche nach AutoStatsUpdater Aufrufen
    print('=== AUTO STATS UPDATER CALL PATTERN ===')
    
    # Check for patterns that suggest when AutoStatsUpdater is called
    cursor.execute('''
        SELECT 
            DATE(timestamp) as date,
            HOUR(timestamp) as hour,
            COUNT(*) as model_stats_created,
            COUNT(CASE WHEN success = 1 THEN 1 END) as successful_stats
        FROM model_statistics
        GROUP BY DATE(timestamp), HOUR(timestamp)
        ORDER BY date DESC, hour DESC
        LIMIT 10
    ''')
    
    try:
        hourly_stats = cursor.fetchall()
        print('ModelStatistics Creation Pattern (by hour):')
        for stat in hourly_stats:
            date, hour, created, successful = stat
            print(f'  {date} {hour:02d}:00 - Created: {created}, Successful: {successful}')
    except Exception as e:
        print(f'SQLite date functions not available: {e}')
        
        # Fallback: just check recent timestamps
        cursor.execute('''
            SELECT 
                timestamp,
                success,
                error_message
            FROM model_statistics
            ORDER BY timestamp DESC
            LIMIT 10
        ''')
        
        recent_stats = cursor.fetchall()
        print('Recent ModelStatistics entries:')
        for stat in recent_stats:
            timestamp, success, error = stat
            print(f'  {timestamp}: success={success}, error="{error}"')
    
    print()
    
    # 6. Source Discovery Analysis
    print('=== SOURCE DISCOVERY vs MODEL STATS ===')
    
    cursor.execute('''
        SELECT 
            COUNT(*) as total_search_results,
            COUNT(CASE WHEN sources IS NOT NULL AND sources != '[]' THEN 1 END) as results_with_sources,
            AVG(LENGTH(sources)) as avg_sources_length
        FROM search_results
    ''')
    
    source_analysis = cursor.fetchone()
    total_sr, with_sources, avg_length = source_analysis
    
    print(f'SearchResults Source Analysis:')
    print(f'  Total SearchResults: {total_sr}')
    print(f'  With Sources: {with_sources}')
    print(f'  Average Sources Length: {avg_length:.0f} chars')
    
    # Check if ModelStatistics capture sources properly
    cursor.execute('''
        SELECT 
            COUNT(*) as total_model_stats,
            COUNT(CASE WHEN sources_count > 0 THEN 1 END) as stats_with_sources,
            AVG(sources_count) as avg_sources_count
        FROM model_statistics
    ''')
    
    ms_source_analysis = cursor.fetchone()
    total_ms, ms_with_sources, avg_ms_sources = ms_source_analysis
    
    print(f'ModelStatistics Source Analysis:')
    print(f'  Total ModelStatistics: {total_ms}')
    print(f'  With Sources > 0: {ms_with_sources}')
    print(f'  Average Sources Count: {avg_ms_sources:.1f}')
    
    print()
    print('=== CONCLUSIONS ===')
    
    if total_sr > 0 and total_ms > 0:
        print(f'1. SearchResults: {total_sr} entries with {(with_sources/total_sr)*100:.1f}% having sources')
        print(f'2. ModelStatistics: {total_ms} entries with {(ms_with_sources/total_ms)*100:.1f}% having sources')
        print(f'3. This suggests ModelStatistics are NOT being generated from SearchResults')
        print(f'4. ModelStatistics appear to be from a separate testing/benchmark process')
        print(f'5. The AutoStatsUpdater.update_statistics_after_search() is likely NOT being called during real searches')
    
    conn.close()

if __name__ == "__main__":
    investigate_data_flows()