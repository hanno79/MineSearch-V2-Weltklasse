#!/usr/bin/env python3
"""
Author: rahn
Datum: 26.07.2025
Version: 1.0
Beschreibung: Debug warum SearchResults success=1 aber ModelStatistics success=0
"""

import sqlite3
import json
from datetime import datetime

def debug_stats_disconnect():
    """Debug der Diskrepanz zwischen SearchResults und ModelStatistics"""
    
    conn = sqlite3.connect('mines.db')
    cursor = conn.cursor()
    
    print('=== DEBUGGING STATS DISCONNECT ===')
    print(f'Debug timestamp: {datetime.now().isoformat()}')
    print()
    
    # 1. Hole ein SearchResult mit success=1
    cursor.execute('''
        SELECT 
            mine_name, 
            model_used, 
            structured_data, 
            success,
            search_timestamp,
            sources
        FROM search_results 
        WHERE success = 1 
        LIMIT 3
    ''')
    
    search_results = cursor.fetchall()
    
    print('=== SEARCH RESULTS (success=1) ===')
    for i, sr in enumerate(search_results):
        mine_name, model_used, structured_data, success, timestamp, sources = sr
        print(f'SearchResult {i+1}:')
        print(f'  Mine: {mine_name}')
        print(f'  Model: {model_used}')
        print(f'  Success: {success}')
        print(f'  Timestamp: {timestamp}')
        
        # Parse structured_data
        try:
            if structured_data:
                data = json.loads(structured_data)
                print(f'  Structured Data Keys: {list(data.keys())}')
                
                # Zähle non-empty values
                filled_count = 0
                empty_count = 0
                x_count = 0
                
                for key, value in data.items():
                    if key.startswith('_'):  # Skip internal fields
                        continue
                        
                    if value is None or value == "" or value == []:
                        empty_count += 1
                    elif value == "X":
                        x_count += 1
                    else:
                        filled_count += 1
                        print(f'    {key}: {value}')
                
                print(f'  Field Analysis: {filled_count} filled, {empty_count} empty, {x_count} marked as "X"')
                
                # This shows WHY fields_found = 0!
                # X values are counted as empty in the statistics logic
                
        except Exception as e:
            print(f'  Error parsing structured_data: {e}')
        
        print()
    
    # 2. Hole entsprechende ModelStatistics für das gleiche Model/Mine
    for sr in search_results:
        mine_name, model_used, _, _, _, _ = sr
        
        cursor.execute('''
            SELECT 
                model_id,
                mine_name,
                success,
                fields_found,
                sources_count,
                structured_data,
                error_message,
                timestamp
            FROM model_statistics 
            WHERE model_id = ? AND mine_name = ?
            ORDER BY timestamp DESC
            LIMIT 3
        ''', (model_used, mine_name))
        
        model_stats = cursor.fetchall()
        
        print(f'=== MODEL STATISTICS for {model_used}/{mine_name} ===')
        if model_stats:
            for i, ms in enumerate(model_stats):
                model_id, mn, success, fields_found, sources_count, structured_data, error_msg, timestamp = ms
                print(f'  ModelStat {i+1}:')
                print(f'    Success: {success}')
                print(f'    Fields Found: {fields_found}')
                print(f'    Sources Count: {sources_count}')
                print(f'    Error: {error_msg}')
                print(f'    Timestamp: {timestamp}')
                
                # Parse structured_data from ModelStatistics
                try:
                    if structured_data:
                        data = json.loads(structured_data)
                        print(f'    ModelStat Structured Data Keys: {list(data.keys())}')
                except Exception as e:
                    print(f'    Error parsing ModelStat structured_data: {e}')
        else:
            print('  NO MODEL STATISTICS FOUND!')
        print()
    
    # 3. Check the FIELD COUNTING LOGIC
    print('=== FIELD COUNTING LOGIC ANALYSIS ===')
    
    # Simulate the _count_filled_fields logic from auto_stats_updater
    cursor.execute('''
        SELECT structured_data 
        FROM search_results 
        WHERE success = 1 
        LIMIT 1
    ''')
    
    result = cursor.fetchone()
    if result and result[0]:
        try:
            structured_data = json.loads(result[0])
            
            print('Simulating _count_filled_fields() logic:')
            filled_count = 0
            
            for key, value in structured_data.items():
                if key.startswith('_'):  # Skip internal fields  
                    continue
                    
                is_filled = False
                if value is not None and value != "" and value != [] and value != {}:
                    # Check for complex values
                    if isinstance(value, (list, dict)):
                        if value:  # Not empty
                            is_filled = True
                    else:
                        is_filled = True
                
                print(f'  {key}: "{value}" -> {"FILLED" if is_filled else "EMPTY"}')
                if is_filled:
                    filled_count += 1
            
            print(f'Total filled fields by current logic: {filled_count}')
            print()
            print('PROBLEM IDENTIFIED: "X" values are counted as FILLED by the algorithm!')
            print('But "X" means "no data found" - should be counted as EMPTY!')
            
        except Exception as e:
            print(f'Error in simulation: {e}')
    
    # 4. Check AutoStatsUpdater calls
    print('=== CHECKING AUTO STATS UPDATER INTEGRATION ===')
    
    # Look for patterns in ModelStatistics that suggest the auto updater is working
    cursor.execute('''
        SELECT 
            COUNT(*) as total_model_stats,
            COUNT(CASE WHEN success = 1 THEN 1 END) as successful_stats,
            COUNT(CASE WHEN fields_found > 0 THEN 1 END) as stats_with_fields,
            AVG(fields_found) as avg_fields_found,
            MIN(timestamp) as earliest,
            MAX(timestamp) as latest
        FROM model_statistics
    ''')
    
    stats_summary = cursor.fetchone()
    total, successful, with_fields, avg_fields, earliest, latest = stats_summary
    
    print(f'ModelStatistics Summary:')
    print(f'  Total entries: {total}')
    print(f'  Successful: {successful}')
    print(f'  With fields > 0: {with_fields}')
    print(f'  Average fields: {avg_fields:.2f}')
    print(f'  Time range: {earliest} to {latest}')
    
    print()
    print('=== DIAGNOSIS ===')
    print('1. SearchResults have success=1 with structured_data containing "X" values')
    print('2. AutoStatsUpdater._count_filled_fields() counts "X" as filled fields')
    print('3. But "X" actually means "no data found" and should count as 0')
    print('4. This creates the illusion of success when no real data was extracted')
    
    conn.close()

if __name__ == "__main__":
    debug_stats_disconnect()