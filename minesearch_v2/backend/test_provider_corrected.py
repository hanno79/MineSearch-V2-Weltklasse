#!/usr/bin/env python3
"""
Author: rahn
Datum: 12.07.2025
Version: 1.0
Beschreibung: Korrigiertes Provider-Test-Script mit akkurater Feld-Zählung
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Tuple
from config import CSV_COLUMNS

BASE_URL = 'http://localhost:8000'

def count_filled_fields(structured_data: Dict[str, Any]) -> Tuple[int, List[str], float]:
    """
    Zählt korrekt gefüllte Felder aus structured_data
    
    Returns:
        (filled_count, important_fields, success_rate)
    """
    if not structured_data:
        return 0, [], 0.0
    
    filled_fields = 0
    important_fields = []
    
    # Wichtige Felder für Bewertung
    important_field_names = [
        'Eigentümer', 'Betreiber', 'Country', 'Region', 
        'Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)',
        'Minentyp (Untertage/ Open-Pit/ usw.)',
        'Aktivitätsstatus', 'Produktionsstart'
    ]
    
    for field in CSV_COLUMNS:
        value = structured_data.get(field, '')
        is_filled = bool(value and str(value).strip() and 
                        str(value).lower() not in ['n/a', 'unknown', '', 'null', 'none'])
        
        if is_filled:
            filled_fields += 1
            if field in important_field_names:
                important_fields.append(f'{field}: {value}')
    
    success_rate = filled_fields / len(CSV_COLUMNS) if CSV_COLUMNS else 0
    return filled_fields, important_fields, success_rate

def test_provider_model(model_id: str, mine_data: Dict[str, str]) -> Dict[str, Any]:
    """
    Testet ein Provider-Modell mit korrekter Feld-Analyse
    """
    print(f'    Testing: {mine_data["name"]}')
    
    try:
        start_time = time.time()
        
        response = requests.post(
            f'{BASE_URL}/api/search?model={model_id}',
            json={
                'mine_name': mine_data['name'],
                'country': mine_data['country'],
                'region': mine_data['region']
            },
            timeout=120
        )
        
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success') and result.get('data'):
                # KORREKTE Analyse: structured_data verwenden
                structured_data = result['data'].get('structured_data', {})
                filled_count, important_fields, success_rate = count_filled_fields(structured_data)
                
                # Quality Score aus API
                quality_score = result['data'].get('quality_score', 0)
                
                print(f'      ✅ API Success: {filled_count}/19 fields ({success_rate:.1%})')
                
                # Zeige wichtige Felder
                if important_fields:
                    print(f'      📊 Key Data: {"; ".join(important_fields[:3])}')
                
                return {
                    'success': True,
                    'api_success': True,
                    'fields_found': filled_count,
                    'success_rate': success_rate,
                    'quality_score': quality_score,
                    'response_time': response_time,
                    'important_fields': important_fields,
                    'raw_structured_data': structured_data
                }
            else:
                error_msg = result.get('error', 'Unknown API error')
                print(f'      ❌ API Error: {error_msg}')
                return {
                    'success': False,
                    'api_success': False,
                    'error': error_msg,
                    'response_time': response_time
                }
        else:
            print(f'      ❌ HTTP Error {response.status_code}')
            return {
                'success': False,
                'api_success': False,
                'error': f'HTTP {response.status_code}',
                'response_time': response_time
            }
            
    except Exception as e:
        print(f'      ❌ Request Error: {str(e)}')
        return {
            'success': False,
            'api_success': False,
            'error': str(e)
        }

def run_corrected_provider_tests():
    """
    Führt korrigierte Provider-Tests durch
    """
    print('=== KORRIGIERTE PROVIDER TESTS ===')
    print(f'Timestamp: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print(f'Total CSV Fields: {len(CSV_COLUMNS)}')
    print()
    
    # Test-Daten
    quebec_mines = [
        {'name': 'Éléonore', 'country': 'Canada', 'region': 'Quebec'},
        {'name': 'Niobec', 'country': 'Canada', 'region': 'Quebec'}
    ]
    
    # Repräsentative Modelle aus verschiedenen Providern
    test_models = [
        'perplexity:sonar-pro',
        'openrouter:deepseek-free', 
        'anthropic:claude-3.7-sonnet',
        'gemini:gemini-2.5-flash-lite',
        'tavily:search'
    ]
    
    all_results = []
    
    for model_id in test_models:
        print(f'\n[MODEL] {model_id}')
        print('=' * 60)
        
        model_results = []
        
        for mine_data in quebec_mines:
            result = test_provider_model(model_id, mine_data)
            result['model'] = model_id
            result['mine'] = mine_data['name']
            model_results.append(result)
            all_results.append(result)
        
        # Modell-Zusammenfassung
        successful_tests = [r for r in model_results if r.get('success')]
        if successful_tests:
            avg_fields = sum(r.get('fields_found', 0) for r in successful_tests) / len(successful_tests)
            avg_success_rate = sum(r.get('success_rate', 0) for r in successful_tests) / len(successful_tests)
            avg_response_time = sum(r.get('response_time', 0) for r in successful_tests) / len(successful_tests)
            
            print(f'    📊 Summary: {len(successful_tests)}/{len(model_results)} successful')
            print(f'    📈 Avg Fields: {avg_fields:.1f}/19 ({avg_success_rate:.1%})')
            print(f'    ⏱️ Avg Time: {avg_response_time:.0f}ms')
        else:
            print(f'    ❌ All tests failed')
    
    # Gesamt-Zusammenfassung
    print('\n\n=== ZUSAMMENFASSUNG ALLER TESTS ===')
    successful_results = [r for r in all_results if r.get('success')]
    
    if successful_results:
        total_tests = len(all_results)
        successful_tests = len(successful_results)
        
        avg_fields = sum(r.get('fields_found', 0) for r in successful_results) / len(successful_results)
        avg_success_rate = sum(r.get('success_rate', 0) for r in successful_results) / len(successful_results)
        
        print(f'Total Tests: {total_tests}')
        print(f'Successful: {successful_tests} ({successful_tests/total_tests:.1%})')
        print(f'Average Fields Found: {avg_fields:.1f}/19 ({avg_success_rate:.1%})')
        
        # Top Performer
        best_result = max(successful_results, key=lambda x: x.get('fields_found', 0))
        print(f'Best Performance: {best_result["model"]} - {best_result.get("fields_found", 0)}/19 fields')
        
    else:
        print('❌ No successful tests')
    
    return all_results

if __name__ == '__main__':
    results = run_corrected_provider_tests()