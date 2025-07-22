"""
Author: rahn  
Datum: 18.07.2025
Version: 1.0
Beschreibung: Detaillierte Liste aller testbaren Modelle für das "all" Argument
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

# Pfad für Imports hinzufügen
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from config.api_keys import APIKeysConfig
    from config.providers import PROVIDERS_CONFIG
    from config.models import MODELS_CONFIG
except ImportError as e:
    print(f"⚠️  Import-Fehler: {e}")
    sys.exit(1)

class TestableModelsLister:
    """Listet alle testbaren Modelle für das MineSearch v2 System"""
    
    def __init__(self):
        self.api_key_status = {}
        self.check_api_keys()
        
    def check_api_keys(self):
        """Prüft API-Key-Status"""
        all_keys = APIKeysConfig.get_all_keys()
        
        for key_name, key_value in all_keys.items():
            provider_name = key_name.replace('_API_KEY', '').lower()
            is_valid = APIKeysConfig.validate_key(key_name, key_value) if key_value else False
            self.api_key_status[provider_name] = is_valid
    
    def get_testable_models(self) -> Dict[str, List[Dict[str, Any]]]:
        """Hole alle testbaren Modelle gruppiert nach Provider"""
        
        testable_models = {}
        
        for provider_name, config in PROVIDERS_CONFIG.items():
            if not config.get('enabled', False):
                continue
                
            # Prüfe API-Key
            if not self.api_key_status.get(provider_name, False):
                continue
                
            models = config.get('models', {})
            provider_models = []
            
            for model_id, model_config in models.items():
                model_info = {
                    'id': model_id,
                    'full_id': f"{provider_name}:{model_id}",
                    'name': model_config.get('name', model_id),
                    'description': model_config.get('description', ''),
                    'timeout': model_config.get('timeout', 60),
                    'max_tokens': model_config.get('max_tokens', 4000),
                    'is_free': model_config.get('is_free', False),
                    'supports_web_search': model_config.get('supports_web_search', False),
                    'supports_deep_research': model_config.get('supports_deep_research', False),
                    'credits_cost': model_config.get('credits_cost', 0)
                }
                provider_models.append(model_info)
            
            if provider_models:
                testable_models[provider_name] = provider_models
                
        return testable_models
    
    def print_detailed_list(self):
        """Druckt detaillierte Liste aller testbaren Modelle"""
        
        print("🧪 ALLE TESTBAREN MODELLE FÜR 'ALL' ARGUMENT")
        print("=" * 80)
        print(f"Datum: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
        print()
        
        testable_models = self.get_testable_models()
        
        total_models = 0
        total_free = 0
        total_web_search = 0
        total_deep_research = 0
        
        for provider_name, models in testable_models.items():
            print(f"📦 PROVIDER: {provider_name.upper()}")
            print("-" * 60)
            
            for model in models:
                total_models += 1
                
                # Icons für Features
                free_icon = "🆓" if model['is_free'] else "💰"
                web_icon = "🔍" if model['supports_web_search'] else "  "
                research_icon = "🔬" if model['supports_deep_research'] else "  "
                
                if model['is_free']:
                    total_free += 1
                if model['supports_web_search']:
                    total_web_search += 1
                if model['supports_deep_research']:
                    total_deep_research += 1
                
                print(f"  {free_icon}{web_icon}{research_icon} {model['full_id']:<35} "
                      f"(Timeout: {model['timeout']:3}s, Token: {model['max_tokens']:5})")
                print(f"      📝 {model['name']}")
                print(f"      💭 {model['description']}")
                
                if model['credits_cost'] > 0:
                    print(f"      💳 Kosten: {model['credits_cost']} Credits")
                
                print()
            
            print(f"   Subtotal: {len(models)} Modelle\n")
        
        print("📊 GESAMTSTATISTIK")
        print("=" * 80)
        print(f"🧪 Testbare Modelle gesamt:     {total_models}")
        print(f"🆓 Kostenlose Modelle:          {total_free}")
        print(f"🔍 Web-Search Modelle:          {total_web_search}")
        print(f"🔬 Deep-Research Modelle:       {total_deep_research}")
        print(f"📦 Aktive Provider:             {len(testable_models)}")
        
        # Geschätzte Testdauer
        avg_time_per_model = 10.5  # Minuten (basierend auf vorheriger Analyse)
        total_time_hours = (total_models * avg_time_per_model) / 60
        
        print(f"⏱️  Geschätzte Testdauer:        {total_time_hours:.1f} Stunden")
        print(f"🚀 Empfohlene Parallelisierung: {max(1, total_models // 10)} Threads")
        print()
        
        # Fehlende Provider
        missing_providers = []
        for provider_name in PROVIDERS_CONFIG.keys():
            if PROVIDERS_CONFIG[provider_name].get('enabled', False):
                if not self.api_key_status.get(provider_name, False):
                    missing_providers.append(provider_name)
        
        if missing_providers:
            print("⚠️  FEHLENDE API-KEYS")
            print("=" * 80)
            for provider in missing_providers:
                models_count = len(PROVIDERS_CONFIG[provider].get('models', {}))
                print(f"❌ {provider:12} - {models_count} Modelle nicht testbar")
            print()
        
        # Kategorisierung der Modelle
        print("📋 MODELL-KATEGORIEN")
        print("=" * 80)
        
        free_models = []
        web_search_models = []
        deep_research_models = []
        premium_models = []
        
        for provider_name, models in testable_models.items():
            for model in models:
                if model['is_free']:
                    free_models.append(model['full_id'])
                elif model['supports_web_search']:
                    web_search_models.append(model['full_id'])
                elif model['supports_deep_research']:
                    deep_research_models.append(model['full_id'])
                else:
                    premium_models.append(model['full_id'])
        
        print(f"🆓 KOSTENLOSE MODELLE ({len(free_models)}):")
        for model_id in sorted(free_models):
            print(f"   • {model_id}")
        
        print(f"\n🔍 WEB-SEARCH MODELLE ({len(web_search_models)}):")
        for model_id in sorted(web_search_models):
            print(f"   • {model_id}")
        
        print(f"\n🔬 DEEP-RESEARCH MODELLE ({len(deep_research_models)}):")
        for model_id in sorted(deep_research_models):
            print(f"   • {model_id}")
        
        print(f"\n💰 PREMIUM MODELLE ({len(premium_models)}):")
        for model_id in sorted(premium_models):
            print(f"   • {model_id}")
        
        print()
        
        return {
            'total_models': total_models,
            'free_models': total_free,
            'web_search_models': total_web_search,
            'deep_research_models': total_deep_research,
            'providers': len(testable_models),
            'estimated_hours': total_time_hours,
            'missing_providers': missing_providers,
            'testable_models': testable_models
        }
    
    def generate_test_command_examples(self):
        """Generiert Beispiele für Test-Kommandos"""
        
        print("💻 TEST-KOMMANDO BEISPIELE")
        print("=" * 80)
        
        testable_models = self.get_testable_models()
        
        # Beispiel für einzelne Provider
        print("🔸 EINZELNE PROVIDER TESTEN:")
        for provider_name in list(testable_models.keys())[:3]:
            print(f"   python batch_test.py --provider {provider_name}")
        
        print()
        
        # Beispiel für kostenlose Modelle
        free_models = []
        for provider_name, models in testable_models.items():
            for model in models:
                if model['is_free']:
                    free_models.append(model['full_id'])
        
        if free_models:
            print("🔸 NUR KOSTENLOSE MODELLE TESTEN:")
            print(f"   python batch_test.py --models {' '.join(free_models[:5])}")
            if len(free_models) > 5:
                print(f"   # ... und {len(free_models) - 5} weitere")
        
        print()
        
        # Beispiel für Web-Search Modelle
        web_search_models = []
        for provider_name, models in testable_models.items():
            for model in models:
                if model['supports_web_search']:
                    web_search_models.append(model['full_id'])
        
        if web_search_models:
            print("🔸 NUR WEB-SEARCH MODELLE TESTEN:")
            print(f"   python batch_test.py --models {' '.join(web_search_models[:3])}")
            if len(web_search_models) > 3:
                print(f"   # ... und {len(web_search_models) - 3} weitere")
        
        print()
        
        # Alle Modelle
        print("🔸 ALLE MODELLE TESTEN:")
        print("   python batch_test.py --provider all")
        print("   # WARNUNG: Sehr lange Laufzeit!")
        print()

def main():
    """Hauptfunktion"""
    
    try:
        lister = TestableModelsLister()
        stats = lister.print_detailed_list()
        lister.generate_test_command_examples()
        
        # Speichere Ergebnisse
        output_file = f"testable_models_list_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Detaillierte Liste gespeichert: {output_file}")
        
        return stats
        
    except Exception as e:
        print(f"❌ Fehler: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main()