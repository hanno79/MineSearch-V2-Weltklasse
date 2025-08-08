#!/usr/bin/env python3
"""
Author: rahn
Datum: 26.07.2025
Version: 1.0
Beschreibung: Test ob AutoStatsUpdater korrekt funktioniert mit realen SearchResults-Daten
"""

import asyncio
import json
import sqlite3
from datetime import datetime
from auto_stats_updater import auto_stats_updater

async def test_auto_stats_integration():
    """Teste ob AutoStatsUpdater korrekt funktioniert"""
    
    print('=== AUTO STATS UPDATER INTEGRATION TEST ===')
    print(f'Test timestamp: {datetime.now().isoformat()}')
    print()
    
    # 1. Hole ein echtes SearchResult
    conn = sqlite3.connect('mines.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            mine_name,
            model_used,
            structured_data,
            sources,
            country,
            region,
            commodity,
            search_duration
        FROM search_results 
        WHERE success = 1 
        LIMIT 1
    ''')
    
    sr = cursor.fetchone()
    if not sr:
        print('ERROR: No successful SearchResults found!')
        return
    
    mine_name, model_used, structured_data_str, sources_str, country, region, commodity, duration = sr
    
    print(f'Testing with SearchResult:')
    print(f'  Mine: {mine_name}')
    print(f'  Model: {model_used}')
    print(f'  Country: {country}')
    print()
    
    # 2. Parse die Daten
    try:
        structured_data = json.loads(structured_data_str) if structured_data_str else {}
        sources = json.loads(sources_str) if sources_str else []
    except Exception as e:
        print(f'ERROR parsing JSON data: {e}')
        return
    
    # 3. Simuliere search_result für AutoStatsUpdater
    search_result = {
        "success": True,
        "data": {
            "structured_data": structured_data,
            "sources": sources
        }
    }
    
    print('Structured Data Preview:')
    for key, value in structured_data.items():
        if key.startswith('_'):
            continue
        print(f'  {key}: {value}')
    print()
    
    # 4. Teste _count_filled_fields vor dem Fix
    print('=== FIELD COUNTING TEST ===')
    
    # Simuliere alte Logik
    old_count = 0
    for key, value in structured_data.items():
        if value is not None and value != "" and value != [] and value != {}:
            if isinstance(value, (list, dict)):
                if value:
                    old_count += 1
            else:
                old_count += 1
    
    # Teste neue Logik
    updater = auto_stats_updater
    new_count = updater._count_filled_fields(structured_data)
    
    print(f'Old counting logic (with X as filled): {old_count}')
    print(f'New counting logic (X as empty): {new_count}')
    print()
    
    # 5. Teste AutoStatsUpdater.update_statistics_after_search()
    print('=== TESTING AUTO STATS UPDATER ===')
    
    # Count ModelStatistics before
    cursor.execute('SELECT COUNT(*) FROM model_statistics')
    before_count = cursor.fetchone()[0]
    
    try:
        result = await updater.update_statistics_after_search(
            mine_name=f"TEST_{mine_name}",  # Prefix um Test zu kennzeichnen
            model_used=model_used,
            search_result=search_result,
            response_time_ms=duration * 1000 if duration else None,
            country=country,
            commodity=commodity,
            region=region
        )
        
        print('AutoStatsUpdater Result:')
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(f'ERROR in AutoStatsUpdater: {e}')
        import traceback
        traceback.print_exc()
        return
    
    # 6. Prüfe ob ModelStatistics erstellt wurde
    print()
    print('=== VERIFICATION ===')
    
    cursor.execute('SELECT COUNT(*) FROM model_statistics')
    after_count = cursor.fetchone()[0]
    
    print(f'ModelStatistics before test: {before_count}')
    print(f'ModelStatistics after test: {after_count}')
    print(f'New entries created: {after_count - before_count}')
    
    if after_count > before_count:
        # Hole das neue Entry
        cursor.execute('''
            SELECT 
                model_id,
                mine_name,
                success,
                fields_found,
                sources_count,
                error_message,
                timestamp
            FROM model_statistics 
            ORDER BY timestamp DESC 
            LIMIT 1
        ''')
        
        new_entry = cursor.fetchone()
        model_id, mn, success, fields_found, sources_count, error_msg, timestamp = new_entry
        
        print()
        print('New ModelStatistics Entry:')
        print(f'  Model: {model_id}')
        print(f'  Mine: {mn}')
        print(f'  Success: {success}')
        print(f'  Fields Found: {fields_found}')
        print(f'  Sources Count: {sources_count}')
        print(f'  Error: {error_msg}')
        print(f'  Timestamp: {timestamp}')
        
        # Cleanup - entferne Test-Entry
        cursor.execute('DELETE FROM model_statistics WHERE mine_name LIKE "TEST_%"')
        conn.commit()
        print()
        print('Test entry cleaned up.')
    
    else:
        print('ERROR: No new ModelStatistics entry was created!')
    
    conn.close()
    
    print()
    print('=== TEST COMPLETE ===')

if __name__ == "__main__":
    asyncio.run(test_auto_stats_integration())