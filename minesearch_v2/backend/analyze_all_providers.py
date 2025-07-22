"""
Author: rahn  
Datum: 18.07.2025
Version: 1.0
Beschreibung: Analyse aller verfügbaren Provider für MineSearch v2 System
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

# Pfad für Imports hinzufügen
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from config.api_keys import APIKeysConfig
    from config.providers import PROVIDERS_CONFIG
    from config.models import MODELS_CONFIG
    from providers.registry import ProviderRegistry
except ImportError as e:
    print(f"⚠️  Import-Fehler: {e}")
    sys.exit(1)

class ProviderAnalyzer:
    """Analysiert alle verfügbaren Provider für das MineSearch v2 System"""
    
    def __init__(self):
        self.results = {}
        self.total_models = 0
        self.total_free_models = 0
        self.total_web_search_models = 0
        self.total_deep_research_models = 0
        self.api_key_status = {}
        self.provider_status = {}
        
    def analyze_api_keys(self) -> Dict[str, Any]:
        """Analysiert API-Key-Status für alle Provider"""
        print("\n🔑 ANALYSE: API-Key-Status")
        print("=" * 50)
        
        all_keys = APIKeysConfig.get_all_keys()
        missing_keys = APIKeysConfig.get_missing_keys()
        
        for key_name, key_value in all_keys.items():
            provider_name = key_name.replace('_API_KEY', '').lower()
            
            if key_value and key_value.strip():
                # Validierung nach Provider
                is_valid = APIKeysConfig.validate_key(key_name, key_value)
                
                if is_valid:
                    self.api_key_status[provider_name] = {
                        'status': 'valid',
                        'key_preview': key_value[:8] + "..." if len(key_value) > 8 else key_value,
                        'length': len(key_value)
                    }
                    print(f"✅ {provider_name:12} - Gültig ({len(key_value)} Zeichen)")
                else:
                    self.api_key_status[provider_name] = {
                        'status': 'invalid',
                        'key_preview': key_value[:8] + "..." if len(key_value) > 8 else key_value,
                        'length': len(key_value)
                    }
                    print(f"❌ {provider_name:12} - Ungültig (falsches Format)")
            else:
                self.api_key_status[provider_name] = {
                    'status': 'missing',
                    'key_preview': '',
                    'length': 0
                }
                print(f"❌ {provider_name:12} - Fehlend")
        
        return {
            'total_keys': len(all_keys),
            'valid_keys': len([k for k in self.api_key_status.values() if k['status'] == 'valid']),
            'missing_keys': len(missing_keys),
            'invalid_keys': len([k for k in self.api_key_status.values() if k['status'] == 'invalid']),
            'details': self.api_key_status
        }
    
    def analyze_provider_configuration(self) -> Dict[str, Any]:
        """Analysiert Provider-Konfiguration"""
        print("\n⚙️  ANALYSE: Provider-Konfiguration")
        print("=" * 50)
        
        enabled_providers = []
        disabled_providers = []
        
        for provider_name, config in PROVIDERS_CONFIG.items():
            is_enabled = config.get('enabled', False)
            has_api_key = bool(config.get('api_key', ''))
            model_count = len(config.get('models', {}))
            timeout = config.get('timeout', 60)
            
            provider_info = {
                'name': provider_name,
                'enabled': is_enabled,
                'has_api_key': has_api_key,
                'model_count': model_count,
                'timeout': timeout,
                'base_url': config.get('base_url', ''),
                'retry_attempts': config.get('retry_attempts', 1),
                'retry_delay': config.get('retry_delay', 5)
            }
            
            self.provider_status[provider_name] = provider_info
            
            if is_enabled:
                enabled_providers.append(provider_name)
                status_icon = "✅" if has_api_key else "⚠️ "
                print(f"{status_icon} {provider_name:12} - {model_count:2} Modelle, Timeout: {timeout}s")
            else:
                disabled_providers.append(provider_name)
                print(f"❌ {provider_name:12} - Deaktiviert")
        
        return {
            'total_providers': len(PROVIDERS_CONFIG),
            'enabled_providers': len(enabled_providers),
            'disabled_providers': len(disabled_providers),
            'enabled_list': enabled_providers,
            'disabled_list': disabled_providers,
            'details': self.provider_status
        }
    
    def analyze_models(self) -> Dict[str, Any]:
        """Analysiert alle verfügbaren Modelle"""
        print("\n🤖 ANALYSE: Modell-Konfiguration")
        print("=" * 50)
        
        provider_model_stats = {}
        
        for provider_name, models in MODELS_CONFIG.items():
            free_models = []
            paid_models = []
            web_search_models = []
            deep_research_models = []
            
            for model_id, model_config in models.items():
                is_free = model_config.get('is_free', False)
                supports_web_search = model_config.get('supports_web_search', False)
                supports_deep_research = model_config.get('supports_deep_research', False)
                
                if is_free:
                    free_models.append(model_id)
                else:
                    paid_models.append(model_id)
                
                if supports_web_search:
                    web_search_models.append(model_id)
                
                if supports_deep_research:
                    deep_research_models.append(model_id)
            
            provider_model_stats[provider_name] = {
                'total_models': len(models),
                'free_models': len(free_models),
                'paid_models': len(paid_models),
                'web_search_models': len(web_search_models),
                'deep_research_models': len(deep_research_models),
                'model_list': list(models.keys()),
                'free_model_list': free_models,
                'web_search_list': web_search_models,
                'deep_research_list': deep_research_models
            }
            
            # Globale Statistiken
            self.total_models += len(models)
            self.total_free_models += len(free_models)
            self.total_web_search_models += len(web_search_models)
            self.total_deep_research_models += len(deep_research_models)
            
            print(f"📊 {provider_name:12} - {len(models):2} Modelle "
                  f"(🆓 {len(free_models)}, 🔍 {len(web_search_models)}, 🔬 {len(deep_research_models)})")
        
        return {
            'total_models': self.total_models,
            'total_free_models': self.total_free_models,
            'total_web_search_models': self.total_web_search_models,
            'total_deep_research_models': self.total_deep_research_models,
            'provider_stats': provider_model_stats
        }
    
    def calculate_test_duration(self) -> Dict[str, Any]:
        """Berechnet geschätzte Testdauer für alle Provider"""
        print("\n⏱️  ANALYSE: Geschätzte Testdauer")
        print("=" * 50)
        
        test_scenarios = [
            "Simple Mining Query",
            "Complex Mining Research",
            "Web Search Integration",
            "Deep Research Analysis",
            "Error Handling Test"
        ]
        
        provider_test_times = {}
        total_test_time = 0
        
        for provider_name, config in PROVIDERS_CONFIG.items():
            if not config.get('enabled', False):
                continue
                
            models = config.get('models', {})
            model_count = len(models)
            avg_timeout = config.get('timeout', 60)
            
            # Geschätzte Zeit pro Modell: 
            # - 5 Test-Szenarien
            # - Durchschnittlich 70% der Timeout-Zeit
            # - Plus 30s Setup/Cleanup pro Modell
            time_per_model = (len(test_scenarios) * avg_timeout * 0.7) + 30
            provider_total_time = time_per_model * model_count
            
            provider_test_times[provider_name] = {
                'model_count': model_count,
                'avg_timeout': avg_timeout,
                'time_per_model': round(time_per_model, 1),
                'total_time_minutes': round(provider_total_time / 60, 1),
                'total_time_seconds': round(provider_total_time, 1)
            }
            
            total_test_time += provider_total_time
            
            print(f"📝 {provider_name:12} - {model_count:2} Modelle, "
                  f"~{round(provider_total_time/60, 1):4.1f} Min")
        
        return {
            'total_test_time_minutes': round(total_test_time / 60, 1),
            'total_test_time_hours': round(total_test_time / 3600, 1),
            'provider_times': provider_test_times,
            'test_scenarios': test_scenarios
        }
    
    def generate_test_list(self) -> List[str]:
        """Generiert Liste aller zu testenden Provider/Modelle"""
        print("\n📋 ANALYSE: Zu testende Provider/Modelle")
        print("=" * 50)
        
        test_list = []
        
        for provider_name, config in PROVIDERS_CONFIG.items():
            if not config.get('enabled', False):
                continue
                
            # Prüfe ob API-Key verfügbar
            api_key_info = self.api_key_status.get(provider_name, {})
            if api_key_info.get('status') != 'valid':
                print(f"⚠️  {provider_name:12} - Übersprungen (kein gültiger API-Key)")
                continue
                
            models = config.get('models', {})
            for model_id in models.keys():
                full_model_id = f"{provider_name}:{model_id}"
                test_list.append(full_model_id)
                
        print(f"✅ Gesamt zu testende Modelle: {len(test_list)}")
        
        return test_list
    
    def run_full_analysis(self) -> Dict[str, Any]:
        """Führt vollständige Analyse durch"""
        print("🔍 MINESEARCH V2 PROVIDER ANALYSE")
        print("=" * 60)
        print(f"Datum: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
        
        # Analyse durchführen
        api_analysis = self.analyze_api_keys()
        provider_analysis = self.analyze_provider_configuration()
        model_analysis = self.analyze_models()
        duration_analysis = self.calculate_test_duration()
        test_list = self.generate_test_list()
        
        # Zusammenfassung
        print("\n📊 ZUSAMMENFASSUNG")
        print("=" * 50)
        print(f"📦 Provider gesamt:     {provider_analysis['total_providers']}")
        print(f"✅ Provider aktiv:      {provider_analysis['enabled_providers']}")
        print(f"🔑 API-Keys gültig:     {api_analysis['valid_keys']}")
        print(f"🤖 Modelle gesamt:      {model_analysis['total_models']}")
        print(f"🆓 Kostenlose Modelle:  {model_analysis['total_free_models']}")
        print(f"🔍 Web-Search Modelle:  {model_analysis['total_web_search_models']}")
        print(f"🔬 Deep-Research Modelle: {model_analysis['total_deep_research_models']}")
        print(f"🧪 Testbare Modelle:    {len(test_list)}")
        print(f"⏱️  Geschätzte Testdauer: {duration_analysis['total_test_time_hours']} Stunden")
        
        # Vollständige Ergebnisse
        complete_results = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_providers': provider_analysis['total_providers'],
                'enabled_providers': provider_analysis['enabled_providers'],
                'valid_api_keys': api_analysis['valid_keys'],
                'total_models': model_analysis['total_models'],
                'free_models': model_analysis['total_free_models'],
                'web_search_models': model_analysis['total_web_search_models'],
                'deep_research_models': model_analysis['total_deep_research_models'],
                'testable_models': len(test_list),
                'estimated_test_hours': duration_analysis['total_test_time_hours']
            },
            'api_keys': api_analysis,
            'providers': provider_analysis,
            'models': model_analysis,
            'test_duration': duration_analysis,
            'test_list': test_list
        }
        
        return complete_results

def main():
    """Hauptfunktion"""
    analyzer = ProviderAnalyzer()
    
    try:
        results = analyzer.run_full_analysis()
        
        # Ergebnisse in JSON-Datei speichern
        output_file = f"provider_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Vollständige Analyse gespeichert: {output_file}")
        
        # Empfehlungen ausgeben
        print("\n💡 EMPFEHLUNGEN")
        print("=" * 50)
        
        if results['api_keys']['missing_keys'] > 0:
            print("⚠️  Fehlende API-Keys ergänzen für vollständige Tests")
        
        if results['test_duration']['total_test_time_hours'] > 6:
            print("⚠️  Testdauer sehr hoch - parallele Ausführung empfohlen")
        
        if results['summary']['free_models'] > 10:
            print("✅ Gute Anzahl kostenloser Modelle für umfangreiche Tests")
        
        if results['summary']['web_search_models'] > 5:
            print("✅ Ausreichend Web-Search Modelle für Mining-Research")
        
        return results
        
    except Exception as e:
        print(f"❌ Fehler bei der Analyse: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    results = main()