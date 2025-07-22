#!/usr/bin/env python3
import sqlite3

def analyze_database():
    conn = sqlite3.connect('/app/minesearch_v2/backend/mines.db')
    cursor = conn.cursor()

    print('=== DETAILED PROBLEMATIC RECORDS ANALYSIS ===')

    # Check for potential data quality issues
    cursor.execute('SELECT COUNT(*) FROM sources WHERE reliability_score = 50.0')
    default_scores = cursor.fetchone()[0]
    print(f'Sources with default reliability score (50.0): {default_scores}')

    cursor.execute('SELECT COUNT(*) FROM sources WHERE total_searches = 0')
    unused_sources = cursor.fetchone()[0]
    print(f'Sources never used in searches: {unused_sources}')

    # Check field statistics for potential anomalies
    cursor.execute('SELECT field_name, COUNT(*) as models FROM field_statistics GROUP BY field_name')
    all_fields = cursor.fetchall()
    print(f'Field coverage across models:')
    for field, count in all_fields:
        if count != 5:
            print(f'  {field}: {count} models (expected 5)')

    # Check for extremely low success rates
    cursor.execute('SELECT model_id, field_name, success_rate FROM field_statistics WHERE success_rate < 0.1 ORDER BY success_rate')
    low_success = cursor.fetchall()
    print(f'Fields with very low success rates (<10%):')
    for model, field, rate in low_success:
        print(f'  {model} - {field}: {rate*100:.1f}%')

    # Check for missing JSON data
    cursor.execute('SELECT COUNT(*) FROM search_results WHERE structured_data IS NULL')
    missing_data = cursor.fetchone()[0]
    print(f'Search results with no structured data: {missing_data}')

    conn.close()

if __name__ == '__main__':
    analyze_database()