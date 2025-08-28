#!/usr/bin/env python3
"""
Test script for all providers
"""

import requests
import json

def test_all_providers():
    try:
        response = requests.get("http://localhost:8000/api/available-models")
        data = response.json()
        models = data['data']['available_models']
        unavailable = data['data']['unavailable_models']
        
        print(f"=== ALLE PROVIDER-TEST ===")
        print(f"Verfügbare Modelle: {len(models)}")
        print(f"Nicht verfügbare Modelle: {len(unavailable)}")
        
        # Zähle nach echten Provider (nicht Kategorie)
        providers = {}
        for model_id, model_data in models.items():
            provider = model_data['provider']
            if provider not in providers:
                providers[provider] = []
            providers[provider].append(model_id)
        
        print(f"\n=== VERFÜGBARE PROVIDER ===")
        for provider, model_list in providers.items():
            print(f"🔹 {provider.upper()}: {len(model_list)} Modelle")
            
        # Zeige nicht verfügbare Provider
        if unavailable:
            print(f"\n=== NICHT VERFÜGBARE MODELLE ===")
            unavail_providers = {}
            for model_id, model_data in unavailable.items():
                provider = model_data['provider']
                if provider not in unavail_providers:
                    unavail_providers[provider] = []
                unavail_providers[provider].append({
                    'model_id': model_id,
                    'status': model_data.get('provider_status', 'unknown'),
                    'error': model_data.get('error', 'No error info')
                })
            
            for provider, model_list in unavail_providers.items():
                print(f"❌ {provider.upper()}: {len(model_list)} Modelle nicht verfügbar")
                for model_info in model_list[:2]:  # Zeige erste 2
                    print(f"   • {model_info['model_id']} - {model_info['status']}")
                    print(f"     Fehler: {model_info['error'][:50]}...")
                    
        # Erwartete Provider-Liste
        expected_providers = [
            'openrouter', 'abacus', 'tavily', 'exa', 'scrapingbee', 
            'firecrawl', 'brightdata'
        ]
        
        print(f"\n=== PROVIDER-STATUS CHECK ===")
        for exp_provider in expected_providers:
            if exp_provider in providers:
                print(f"✅ {exp_provider.upper()}: Verfügbar ({len(providers[exp_provider])} Modelle)")
            else:
                # Check if it's in unavailable
                found_unavail = any(model_data['provider'] == exp_provider for model_data in unavailable.values())
                if found_unavail:
                    print(f"⚠️  {exp_provider.upper()}: Nicht verfügbar (Provider-Problem)")
                else:
                    print(f"❌ {exp_provider.upper()}: Komplett fehlend")
        
    except Exception as e:
        print(f"Fehler: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_all_providers()