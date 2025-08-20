#!/usr/bin/env python3
"""
Check the /api/models endpoint to see all available models
"""

import requests
import json

try:
    # Check models API (this is what the frontend uses)
    response = requests.get("http://localhost:8000/api/models")
    data = response.json()
    
    print(f'📊 Models API Response:')
    print(f'  Success: {data.get("success")}')
    
    if 'models' in data:
        models = data['models']
        print(f'  Total models: {len(models)}')
        
        # Group by provider
        providers = {}
        for model in models:
            if isinstance(model, dict):
                model_id = model.get('model_id', str(model))
            else:
                model_id = str(model)
            
            if ':' in model_id:
                provider = model_id.split(':')[0]
                if provider not in providers:
                    providers[provider] = 0
                providers[provider] += 1
        
        print(f'\n🏢 Models by provider:')
        for provider, count in providers.items():
            print(f'  {provider}: {count} models')
        
        print(f'\n📋 First 10 models:')
        for i, model in enumerate(models[:10]):
            if isinstance(model, dict):
                model_id = model.get('model_id', str(model))
            else:
                model_id = str(model)
            print(f'  {i+1}. {model_id}')
        
        print(f'\n🎯 This should match our expected 55 models!')
        
    else:
        print('❌ No models key in response')
        print(f'Response keys: {list(data.keys())}')

except Exception as e:
    print('❌ Error:', str(e))