#!/usr/bin/env python3
"""
Author: rahn
Datum: 29.07.2025
Version: 1.0
Beschreibung: Database analysis to find actual non-X values for target fields
"""

import sqlite3
import json
from pathlib import Path
from minesearch.database.db_utils import get_normalized_db_path, get_sqlite_connection

def analyze_database_fields():
    """Analyze the database to find actual non-X values for target fields"""
    
    db_path = Path(get_normalized_db_path())
    if not db_path.exists():
        print(f"Database not found at {db_path}")
        return
    
    target_fields = [
        'Jahr der Aufnahme der Kosten',
        'Jahr der Erstellung des Dokumentes', 
        'Fläche der Mine in qkm'
    ]
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Query to get all structured_data containing our target fields
        query = """
        SELECT mine_name, model_used, structured_data, search_timestamp
        FROM search_results 
        WHERE structured_data IS NOT NULL
        ORDER BY search_timestamp DESC
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        print(f"=== DATABASE ANALYSIS: {len(results)} records found ===")
        
        # Analyze structured_data for target fields
        field_analysis = {}
        for target_field in target_fields:
            field_analysis[target_field] = {
                'total_occurrences': 0,
                'x_values': 0,
                'non_x_values': 0,
                'unique_non_x_values': set(),
                'examples': []
            }
        
        for mine_name, model_used, structured_data_json, timestamp in results:
            if not structured_data_json:
                continue
                
            try:
                structured_data = json.loads(structured_data_json)
            except:
                continue
            
            for target_field in target_fields:
                if target_field in structured_data:
                    field_analysis[target_field]['total_occurrences'] += 1
                    
                    value = str(structured_data[target_field]).strip()
                    is_x = value.upper() == 'X'
                    
                    if is_x:
                        field_analysis[target_field]['x_values'] += 1
                    else:
                        field_analysis[target_field]['non_x_values'] += 1
                        field_analysis[target_field]['unique_non_x_values'].add(value)
                        
                        # Store examples
                        if len(field_analysis[target_field]['examples']) < 5:
                            field_analysis[target_field]['examples'].append({
                                'mine': mine_name,
                                'model': model_used,
                                'value': value,
                                'timestamp': timestamp
                            })
        
        # Print analysis results
        print("\n=== FIELD VALUE ANALYSIS ===")
        for field, analysis in field_analysis.items():
            print(f"\n{field}:")
            print(f"  Total occurrences: {analysis['total_occurrences']}")
            print(f"  X-values: {analysis['x_values']}")
            print(f"  Non-X values: {analysis['non_x_values']}")
            print(f"  Unique non-X values: {len(analysis['unique_non_x_values'])}")
            
            if analysis['unique_non_x_values']:
                print(f"  Sample values: {list(analysis['unique_non_x_values'])[:5]}")
                
            if analysis['examples']:
                print(f"  Examples:")
                for example in analysis['examples']:
                    print(f"    {example['mine']} ({example['model']}): {example['value']}")
        
        print("\n=== CONCLUSION ===")        
        total_non_x = sum(analysis['non_x_values'] for analysis in field_analysis.values())
        if total_non_x > 0:
            print(f"FOUND {total_non_x} non-X values across all target fields!")
            print("ISSUE CONFIRMED: These values should appear as renamed fields but are filtered out.")
        else:
            print("All values for target fields are X-values - no data loss occurring.")
            
        conn.close()
        
    except Exception as e:
        print(f"Database analysis error: {e}")

if __name__ == "__main__":
    analyze_database_fields()