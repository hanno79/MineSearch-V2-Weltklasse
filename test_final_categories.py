#!/usr/bin/env python3
"""
Final test for all provider categories
"""

import requests
import json

def test_final_categories():
    try:
        response = requests.get("http://localhost:8000/api/available-models")
        data = response.json()
        models = data['data']['available_models']
        
        print(f"=== FINALE KATEGORIEN-TEST ===")
        print(f"Gesamt Modelle: {len(models)}")
        
        # Zähle nach provider_category
        categories = {}
        for model_id, model_data in models.items():
            cat = model_data.get('provider_category', None)
            if cat is None:
                cat = 'keine_kategorie'
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(model_id)
        
        print(f"\n=== ALLE KATEGORIEN ({len(categories)}) ===")
        for category, model_list in sorted(categories.items(), key=lambda x: x[0] or 'zzz'):
            if category != 'keine_kategorie':
                print(f"🏷️  {category.upper()}: {len(model_list)} Modelle")
                if len(model_list) <= 3:
                    for model_id in model_list:
                        print(f"   ✅ {model_id}")
                else:
                    for model_id in sorted(model_list)[:3]:
                        print(f"   ✅ {model_id}")
                    print(f"   ... und {len(model_list)-3} weitere")
                print()
            
        if 'keine_kategorie' in categories:
            print(f"⚠️  OHNE KATEGORIE: {len(categories['keine_kategorie'])} Modelle")
            for model_id in categories['keine_kategorie'][:5]:
                print(f"   ❌ {model_id}")
            
        # Erwartete Kategorien
        expected = ['openrouter', 'anthropic', 'gemini', 'openai', 'grok', 'perplexity', 
                   'abacus', 'tavily', 'exa', 'scrapingbee', 'firecrawl', 'brightdata']
        
        print(f"\n=== KATEGORIEN-VOLLSTÄNDIGKEIT ===")
        for exp_cat in expected:
            if exp_cat in categories:
                count = len(categories[exp_cat])
                print(f"✅ {exp_cat.upper()}: {count} Modelle")
            else:
                print(f"❌ {exp_cat.upper()}: Fehlt komplett")
        
        # OpenRouter Aufschlüsselung
        if 'openrouter' in categories:
            openrouter_models = categories['openrouter'] 
            print(f"\n=== OPENROUTER AUFSCHLÜSSELUNG ({len(openrouter_models)} Modelle) ===")
            # Die alten DeepSeek/NVIDIA-Modelle etc. sollten hier sein
            for model_id in sorted(openrouter_models)[:8]:  # Zeige erste 8
                print(f"   🔸 {model_id}")
            if len(openrouter_models) > 8:
                print(f"   ... und {len(openrouter_models)-8} weitere")
        
    except Exception as e:
        print(f"Fehler: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_final_categories()