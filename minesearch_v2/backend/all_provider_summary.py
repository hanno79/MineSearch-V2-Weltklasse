"""
Author: rahn  
Datum: 18.07.2025
Version: 1.0
Beschreibung: Finale Zusammenfassung aller verfügbaren Provider für das "all" Argument
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

def generate_final_summary():
    """Generiert finale Zusammenfassung für das 'all' Argument"""
    
    print("🎯 FINALE ZUSAMMENFASSUNG: ALLE VERFÜGBAREN PROVIDER")
    print("=" * 80)
    print(f"Analyse-Datum: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    print()
    
    # API-Key Status
    all_keys = APIKeysConfig.get_all_keys()
    valid_keys = []
    missing_keys = []
    
    for key_name, key_value in all_keys.items():
        provider_name = key_name.replace('_API_KEY', '').lower()
        if key_value and APIKeysConfig.validate_key(key_name, key_value):
            valid_keys.append(provider_name)
        else:
            missing_keys.append(provider_name)
    
    # Provider-Statistiken
    enabled_providers = []
    disabled_providers = []
    testable_providers = []
    
    for provider_name, config in PROVIDERS_CONFIG.items():
        if config.get('enabled', False):
            enabled_providers.append(provider_name)
            if provider_name in valid_keys:
                testable_providers.append(provider_name)
        else:
            disabled_providers.append(provider_name)
    
    # Modell-Statistiken
    total_models = 0
    testable_models = 0
    free_models = 0
    web_search_models = 0
    deep_research_models = 0
    
    for provider_name, models in MODELS_CONFIG.items():
        provider_model_count = len(models)
        total_models += provider_model_count
        
        if provider_name in testable_providers:
            testable_models += provider_model_count
            
            for model_id, model_config in models.items():
                if model_config.get('is_free', False):
                    free_models += 1
                if model_config.get('supports_web_search', False):
                    web_search_models += 1
                if model_config.get('supports_deep_research', False):
                    deep_research_models += 1
    
    # Testdauer-Schätzung
    avg_test_time_per_model = 10.5  # Minuten
    total_test_hours = (testable_models * avg_test_time_per_model) / 60
    
    print("📊 STATISTIKEN")
    print("-" * 40)
    print(f"📦 Provider gesamt:           {len(PROVIDERS_CONFIG)}")
    print(f"✅ Provider aktiviert:        {len(enabled_providers)}")
    print(f"🔑 Provider mit API-Key:      {len(valid_keys)}")
    print(f"🧪 Testbare Provider:         {len(testable_providers)}")
    print(f"❌ Fehlende API-Keys:         {len(missing_keys)}")
    print()
    print(f"🤖 Modelle gesamt:            {total_models}")
    print(f"🧪 Testbare Modelle:          {testable_models}")
    print(f"🆓 Kostenlose Modelle:        {free_models}")
    print(f"🔍 Web-Search Modelle:        {web_search_models}")
    print(f"🔬 Deep-Research Modelle:     {deep_research_models}")
    print()
    print(f"⏱️  Geschätzte Testdauer:      {total_test_hours:.1f} Stunden")
    print(f"🚀 Empfohlene Threads:        {max(1, testable_models // 10)}")
    print()
    
    # Testbare Provider Details
    print("🎯 TESTBARE PROVIDER (mit API-Key)")
    print("-" * 40)
    for provider_name in testable_providers:
        models = MODELS_CONFIG.get(provider_name, {})
        timeout = PROVIDERS_CONFIG[provider_name].get('timeout', 60)
        model_count = len(models)
        
        # Modell-Features zählen
        provider_free = sum(1 for m in models.values() if m.get('is_free', False))
        provider_web = sum(1 for m in models.values() if m.get('supports_web_search', False))
        provider_research = sum(1 for m in models.values() if m.get('supports_deep_research', False))
        
        feature_icons = []
        if provider_free > 0:
            feature_icons.append(f"🆓×{provider_free}")
        if provider_web > 0:
            feature_icons.append(f"🔍×{provider_web}")
        if provider_research > 0:
            feature_icons.append(f"🔬×{provider_research}")
        
        features_str = " ".join(feature_icons) if feature_icons else "💰"
        
        print(f"  ✅ {provider_name:<12} │ {model_count:2} Modelle │ {timeout:3}s │ {features_str}")
    
    # Nicht testbare Provider
    if missing_keys:
        print("\n⚠️  NICHT TESTBARE PROVIDER (fehlende API-Keys)")
        print("-" * 40)
        for provider_name in missing_keys:
            if provider_name in enabled_providers:
                models = MODELS_CONFIG.get(provider_name, {})
                model_count = len(models)
                print(f"  ❌ {provider_name:<12} │ {model_count:2} Modelle │ API-Key fehlt")
    
    # Empfehlungen
    print("\n💡 EMPFEHLUNGEN FÜR 'ALL' TESTS")
    print("-" * 40)
    
    if len(testable_providers) >= 10:
        print("✅ Gute Provider-Abdeckung für umfassende Tests")
    else:
        print("⚠️  Wenige testbare Provider - API-Keys ergänzen")
    
    if free_models >= 5:
        print("✅ Ausreichend kostenlose Modelle für erste Tests")
    else:
        print("⚠️  Wenige kostenlose Modelle verfügbar")
    
    if web_search_models >= 10:
        print("✅ Gute Web-Search-Abdeckung für Mining-Research")
    else:
        print("⚠️  Wenige Web-Search-Modelle verfügbar")
    
    if total_test_hours > 8:
        print("⚠️  Sehr lange Testdauer - Parallelisierung empfohlen")
        print("   🔧 Nutze --parallel Parameter für schnellere Tests")
    
    if total_test_hours > 12:
        print("⚠️  Extreme Testdauer - Batch-Tests in Teilmengen erwägen")
        print("   🔧 Nutze --provider Parameter für einzelne Provider")
    
    # Prioritäts-Empfehlungen
    print("\n🎯 PRIORITÄTS-EMPFEHLUNGEN")
    print("-" * 40)
    
    # Kostenlose Modelle zuerst
    free_provider_models = []
    for provider_name in testable_providers:
        models = MODELS_CONFIG.get(provider_name, {})
        for model_id, model_config in models.items():
            if model_config.get('is_free', False):
                free_provider_models.append(f"{provider_name}:{model_id}")
    
    if free_provider_models:
        print("🆓 PRIORITÄT 1: Kostenlose Modelle zuerst testen")
        print("   Kommando: python batch_test.py --models \\")
        for i, model in enumerate(free_provider_models[:5]):  # Erste 5 zeigen
            print(f"     {model} \\")
        if len(free_provider_models) > 5:
            print(f"     # ... und {len(free_provider_models) - 5} weitere")
    
    # Web-Search Modelle für Mining
    web_search_provider_models = []
    for provider_name in testable_providers:
        models = MODELS_CONFIG.get(provider_name, {})
        for model_id, model_config in models.items():
            if model_config.get('supports_web_search', False):
                web_search_provider_models.append(f"{provider_name}:{model_id}")
    
    if web_search_provider_models:
        print("\n🔍 PRIORITÄT 2: Web-Search Modelle für Mining-Research")
        print("   Kommando: python batch_test.py --models \\")
        for i, model in enumerate(web_search_provider_models[:3]):  # Erste 3 zeigen
            print(f"     {model} \\")
        if len(web_search_provider_models) > 3:
            print(f"     # ... und {len(web_search_provider_models) - 3} weitere")
    
    # Alle Modelle
    print("\n🎯 PRIORITÄT 3: Alle Modelle (vollständiger Test)")
    print("   Kommando: python batch_test.py --provider all")
    print(f"   Warnung: ~{total_test_hours:.1f} Stunden Laufzeit!")
    
    # Zusammenfassung für JSON
    summary_data = {
        'timestamp': datetime.now().isoformat(),
        'total_providers': len(PROVIDERS_CONFIG),
        'enabled_providers': len(enabled_providers),
        'testable_providers': len(testable_providers),
        'valid_api_keys': len(valid_keys),
        'missing_api_keys': len(missing_keys),
        'total_models': total_models,
        'testable_models': testable_models,
        'free_models': free_models,
        'web_search_models': web_search_models,
        'deep_research_models': deep_research_models,
        'estimated_test_hours': total_test_hours,
        'recommended_threads': max(1, testable_models // 10),
        'testable_providers_list': testable_providers,
        'missing_providers_list': missing_keys,
        'free_models_list': free_provider_models,
        'web_search_models_list': web_search_provider_models,
        'recommendations': {
            'good_provider_coverage': len(testable_providers) >= 10,
            'sufficient_free_models': free_models >= 5,
            'good_web_search_coverage': web_search_models >= 10,
            'needs_parallelization': total_test_hours > 8,
            'needs_batch_splitting': total_test_hours > 12
        }
    }
    
    return summary_data

def main():
    """Hauptfunktion"""
    
    try:
        summary = generate_final_summary()
        
        # JSON-Datei speichern
        output_file = f"all_provider_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Zusammenfassung gespeichert: {output_file}")
        print("\n🎉 ANALYSE ABGESCHLOSSEN")
        print("=" * 80)
        print("Das MineSearch v2 System ist bereit für umfassende Provider-Tests!")
        print(f"Verwende 'python batch_test.py --provider all' für alle {summary['testable_models']} Modelle.")
        
        return summary
        
    except Exception as e:
        print(f"❌ Fehler bei der Zusammenfassung: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main()