#!/usr/bin/env python3
"""
Debug script to check API model count
"""

import requests
import json

try:
    # Check statistics API
    response = requests.get("http://localhost:8000/api/statistics/models/comprehensive")
    data = response.json()
    
    if data.get('success'):
        models = data.get('data', {}).get('models', [])
        print(f'📊 Total models in API response: {len(models)}')
        
        # Count by status
        tested = [m for m in models if m.get('status') != 'available']
        available = [m for m in models if m.get('status') == 'available']
        
        print(f'✅ Tested models: {len(tested)}')
        print(f'🆕 Available models: {len(available)}')
        print(f'🎯 Total expected: {len(tested) + len(available)}')
        
        # Show first few available models
        if available:
            print(f'\n📋 First 5 available models:')
            for model in available[:5]:
                print(f'  - {model["model_id"]}')
        
        # Check if provider registry has models
        print(f'\n🔍 Sample tested models:')
        for model in tested[:3]:
            print(f'  - {model["model_id"]} (Score: {model.get("overall_score", 0)})')
            
    else:
        print('❌ API returned error:', data)

except Exception as e:
    print('❌ Error:', str(e))