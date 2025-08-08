#!/usr/bin/env python3
"""
Author: rahn
Datum: 29.07.2025
Version: 1.0
Beschreibung: Debug script to analyze field processing and X-value filtering issue
"""

import requests
import json

def analyze_field_processing():
    """Analyze the field processing issue in MineSearch v2"""
    
    url = 'http://localhost:8000/api/results/consolidated'
    try:
        response = requests.get(url, timeout=15)
        data = response.json()
        
        if not (data.get('success') and data.get('data', {}).get('consolidated_results')):
            print("No consolidated results found")
            return
            
        results = data['data']['consolidated_results']
        
        # Analyze multiple mines to understand the pattern
        print('=== FIELD RENAMING ANALYSIS ===')
        
        target_original_fields = {
            'Jahr der Aufnahme der Kosten': 'Kostenjahr',
            'Jahr der Erstellung des Dokumentes': 'Dokumentenjahr', 
            'Fläche der Mine in qkm': 'Minenfläche in qkm'
        }
        
        found_non_x_values = {}
        total_mines_checked = min(5, len(results))  # Check first 5 mines
        
        for i in range(total_mines_checked):
            mine = results[i]
            mine_name = mine.get('mine_name', f'Mine_{i}')
            print(f'\n--- {mine_name} ---')
            
            # Check model results for original field names and values
            model_results = mine.get('model_results', [])
            for j, model in enumerate(model_results[:3]):  # Check first 3 models per mine
                model_name = model.get('model_used', f'Model_{j}')
                structured_data = model.get('structured_data', {})
                
                print(f'  Model {model_name}:')
                for original_field, renamed_field in target_original_fields.items():
                    value = structured_data.get(original_field, 'NOT_FOUND')
                    is_x = str(value).strip().upper() == 'X'
                    
                    print(f'    {original_field}: {value} (X-value: {is_x})')
                    
                    # Track non-X values
                    if not is_x and value != 'NOT_FOUND' and str(value).strip():
                        if renamed_field not in found_non_x_values:
                            found_non_x_values[renamed_field] = []
                        found_non_x_values[renamed_field].append({
                            'mine': mine_name,
                            'model': model_name,
                            'original_field': original_field,
                            'value': value
                        })
        
        print('\n=== SUMMARY OF NON-X VALUES FOUND ===')
        for renamed_field, instances in found_non_x_values.items():
            print(f'{renamed_field}: {len(instances)} non-X values found')
            for instance in instances[:2]:  # Show first 2 examples
                print(f'  Example: {instance["mine"]} -> {instance["value"]} (from {instance["model"]})')
                
        print('\n=== PROCESSING FLOW ISSUE IDENTIFIED ===')
        print('PROBLEM: X-values are filtered out BEFORE field renaming occurs')
        print('LOCATION: consolidated_results.py line 283-284')
        print('CODE: if field_value and str(field_value).strip() and str(field_value).strip().upper() != "X":')
        print('RESULT: Original fields with only X-values never get processed for renaming')
        
        # Detailed analysis of the processing flow
        print('\n=== DETAILED PROCESSING FLOW ANALYSIS ===')
        sample_mine = results[0]
        model_results = sample_mine.get('model_results', [])
        if model_results:
            sample_model = model_results[0]
            structured_data = sample_model.get('structured_data', {})
            
            print(f'Sample model structured_data fields: {len(structured_data)}')
            print('Processing simulation:')
            
            for original_field, renamed_field in target_original_fields.items():
                value = structured_data.get(original_field, 'NOT_FOUND')
                if value != 'NOT_FOUND':
                    is_x = str(value).strip().upper() == 'X'
                    filtered_out = is_x  # This is where the issue occurs
                    
                    print(f'  {original_field}:')
                    print(f'    Value: "{value}"')
                    print(f'    Is X-value: {is_x}')
                    print(f'    Filtered out before renaming: {filtered_out}')
                    print(f'    Would be renamed to: {renamed_field}')
                    
                    if filtered_out:
                        print(f'    >>> ISSUE: Field never reaches renaming logic!')
                    
        return found_non_x_values
        
    except Exception as e:
        print(f'Error: {e}')
        return None

if __name__ == "__main__":
    analyze_field_processing()