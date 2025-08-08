#!/usr/bin/env python3
"""
Author: rahn
Datum: 26.07.2025
Version: 1.0
Beschreibung: Regeneriere ModelStatistics aus existierenden SearchResults mit korrigierter Logik
"""

import asyncio
import logging
import sqlite3
import json
from datetime import datetime
from auto_stats_updater import auto_stats_updater
from model_summary_generator import ModelSummaryGenerator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def regenerate_model_statistics():
    """Regeneriere ModelStatistics aus existierenden SearchResults"""
    
    print('=== REGENERATING MODEL STATISTICS ===')
    print(f'Regeneration started: {datetime.now().isoformat()}')
    print()
    
    conn = sqlite3.connect('mines.db')
    cursor = conn.cursor()
    
    # 1. Lösche bestehende ModelStatistics (aus benchmark tests)
    print('Step 1: Removing old ModelStatistics...')
    cursor.execute('SELECT COUNT(*) FROM model_statistics')
    old_count = cursor.fetchone()[0]
    
    cursor.execute('DELETE FROM model_statistics')
    conn.commit()
    
    print(f'  Removed {old_count} old ModelStatistics entries')
    print()
    
    # 2. Hole alle SearchResults
    print('Step 2: Loading SearchResults...')
    cursor.execute('''
        SELECT 
            mine_name,
            model_used,
            structured_data,
            sources,
            country,
            region,
            commodity,
            search_duration,
            success,
            search_timestamp
        FROM search_results 
        ORDER BY search_timestamp ASC
    ''')
    
    search_results = cursor.fetchall()
    print(f'  Found {len(search_results)} SearchResults to process')
    print()
    
    # 3. Konvertiere SearchResults zu ModelStatistics
    print('Step 3: Converting SearchResults to ModelStatistics...')
    
    successful_conversions = 0
    failed_conversions = 0
    processed_models = set()
    
    for i, sr in enumerate(search_results):
        mine_name, model_used, structured_data_str, sources_str, country, region, commodity, duration, success, timestamp = sr
        
        try:
            # Parse JSON data
            structured_data = json.loads(structured_data_str) if structured_data_str else {}
            sources = json.loads(sources_str) if sources_str else []
            
            # Prepare search_result for AutoStatsUpdater
            search_result = {
                "success": bool(success),
                "data": {
                    "structured_data": structured_data,
                    "sources": sources
                }
            }
            
            # Call AutoStatsUpdater
            result = await auto_stats_updater.update_statistics_after_search(
                mine_name=mine_name,
                model_used=model_used,
                search_result=search_result,
                response_time_ms=duration * 1000 if duration else None,
                country=country,
                commodity=commodity,
                region=region
            )
            
            if result.get('success'):
                successful_conversions += 1
                processed_models.add(model_used)
                
                if i % 10 == 0:  # Progress update every 10 items
                    print(f'  Progress: {i+1}/{len(search_results)} ({((i+1)/len(search_results)*100):.1f}%)')
            else:
                failed_conversions += 1
                error_msg = result.get('error', 'Unknown error')
                logger.warning(f'Failed to convert {model_used}/{mine_name}: {error_msg}')
                
        except Exception as e:
            failed_conversions += 1
            logger.error(f'Error processing {model_used}/{mine_name}: {e}')
    
    print(f'  Conversion completed!')
    print(f'  Successful: {successful_conversions}')
    print(f'  Failed: {failed_conversions}')
    print(f'  Models processed: {len(processed_models)}')
    print()
    
    # 4. Verify new ModelStatistics
    print('Step 4: Verifying new ModelStatistics...')
    cursor.execute('''
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN success = 1 THEN 1 END) as successful,
            COUNT(DISTINCT model_id) as unique_models,
            AVG(fields_found) as avg_fields
        FROM model_statistics
    ''')
    
    verification = cursor.fetchone()
    total, successful, unique_models, avg_fields = verification
    
    print(f'  New ModelStatistics:')
    print(f'    Total entries: {total}')
    print(f'    Successful: {successful}')
    print(f'    Success rate: {(successful/total)*100:.1f}%' if total > 0 else '    Success rate: 0%')
    print(f'    Unique models: {unique_models}')
    print(f'    Average fields found: {avg_fields:.2f}' if avg_fields else '    Average fields found: 0')
    print()
    
    # 5. Regenerate ModelSummary
    print('Step 5: Regenerating ModelSummary...')
    
    generator = ModelSummaryGenerator()
    summary_result = generator.generate_all_model_summaries()
    
    if summary_result.get('success'):
        print(f'  ModelSummary regenerated successfully!')
        summaries_generated = summary_result.get('summaries_generated', 0)
        duration_seconds = summary_result.get('duration_seconds', 0)
        print(f'    Summaries generated: {summaries_generated}')
        print(f'    Duration: {duration_seconds:.2f} seconds')
    else:
        error_msg = summary_result.get('error', 'Unknown error')
        print(f'  ERROR regenerating ModelSummary: {error_msg}')
    
    print()
    
    # 6. Show final statistics comparison
    print('Step 6: Final Statistics Comparison...')
    
    cursor.execute('''
        SELECT 
            model_id,
            total_tests,
            success_rate,
            avg_fields_found,
            avg_sources_count
        FROM model_summary
        ORDER BY success_rate DESC, avg_fields_found DESC
        LIMIT 10
    ''')
    
    summaries = cursor.fetchall()
    
    if summaries:
        print('Top Models by Performance:')
        print('Model | Tests | Success % | Avg Fields | Avg Sources')
        print('-' * 65)
        for summary in summaries:
            model_id, tests, success_rate, fields, sources = summary
            success_pct = (success_rate or 0) * 100
            print(f'{model_id[:25]:<25} | {tests:>5} | {success_pct:>8.1f}% | {fields:>10.2f} | {sources:>11.1f}')
    else:
        print('No ModelSummary data available')
    
    conn.close()
    
    print()
    print('=== REGENERATION COMPLETE ===')
    print(f'Completed at: {datetime.now().isoformat()}')
    
    return {
        "success": True,
        "search_results_processed": len(search_results),
        "successful_conversions": successful_conversions,
        "failed_conversions": failed_conversions,
        "models_processed": len(processed_models),
        "model_summary_regenerated": summary_result.get('success', False),
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    result = asyncio.run(regenerate_model_statistics())
    
    print()
    print('REGENERATION SUMMARY:')
    print(json.dumps(result, indent=2))