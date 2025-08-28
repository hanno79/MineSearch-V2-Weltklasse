#!/usr/bin/env python3
"""
Test script for premium models integration
"""

import requests
import json

def test_premium_models():
    try:
        response = requests.get("http://localhost:8000/api/available-models")
        data = response.json()
        models = data['data']['available_models']
        
        print(f"=== VERFÜGBARE MODELLE: {len(models)} ===")
        
        # Zähle Premium-Modelle nach provider_category
        categories = {}
        for model_id, model_data in models.items():
            cat = model_data.get('provider_category', 'unknown')
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(model_id)
        
        print()
        for category, model_list in categories.items():
            if category and category != 'unknown':
                print(f"🏷️  KATEGORIE {category.upper()}: {len(model_list)} Modelle")
                for model_id in sorted(model_list)[:3]:  # Zeige erste 3
                    print(f"   ✅ {model_id}")
                if len(model_list) > 3:
                    print(f"   ... und {len(model_list)-3} weitere")
                print()
        
        # Überprüfe spezifische Premium-Modelle
        premium_check = [
            'openrouter:claude-3.5-sonnet',
            'openrouter:gemini-2.0-flash',
            'openrouter:gpt-4o',
            'openrouter:grok-2',
            'openrouter:perplexity-sonar-pro'
        ]
        
        print("=== PREMIUM-MODELLE CHECK ===")
        available_ids = list(models.keys())
        for check_id in premium_check:
            status = '✅ GEFUNDEN' if check_id in available_ids else '❌ FEHLT'
            print(f"{status}: {check_id}")
        
        # Zeige auch provider_category bei den Premium-Modellen
        print("\n=== PREMIUM-MODELL DETAILS ===")
        for model_id, model_data in models.items():
            if model_id in premium_check:
                print(f"📋 {model_id}")
                print(f"   Name: {model_data['name']}")
                print(f"   Provider: {model_data['provider']}")
                print(f"   Kategorie: {model_data.get('provider_category', 'keine')}")
                print()
        
    except Exception as e:
        print(f"Fehler: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_premium_models()