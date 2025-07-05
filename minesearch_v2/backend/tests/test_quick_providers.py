"""
Author: rahn
Datum: 05.07.2025
Version: 1.0
Beschreibung: Schneller Test der wichtigsten Provider
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from search_service_multi import MultiProviderSearchService
from config import config


async def quick_test():
    """Schneller Test der wichtigsten Provider"""
    
    service = MultiProviderSearchService()
    
    print("\n" + "="*80)
    print("SCHNELLER PROVIDER TEST")
    print("="*80)
    print(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test-Mine
    mine = {
        'name': 'Canadian Malartic',
        'country': 'Kanada',
        'region': 'Quebec',
        'commodity': 'Gold'
    }
    
    # Wichtigste Modelle
    test_models = [
        'perplexity:sonar-pro',
        'openrouter:deepseek-free',
        'scrapingbee:basic-scrape',
        'firecrawl:scrape'
    ]
    
    print(f"\nTeste Mine: {mine['name']} ({mine['commodity']})")
    print("-"*60)
    
    results = {}
    
    # 1. Teste Einzelmodelle
    print("\n1. EINZELMODELL-TESTS:")
    for model_id in test_models:
        print(f"\n{model_id}: ", end='', flush=True)
        start_time = datetime.now()
        
        try:
            result = await service.search_with_model(
                model_id=model_id,
                mine_name=mine['name'],
                country=mine['country'],
                commodity=mine['commodity'],
                region=mine['region']
            )
            
            duration = (datetime.now() - start_time).total_seconds()
            
            if result.get('success'):
                data = result.get('data', {})
                sources = result.get('sources', [])
                filled = sum(1 for v in data.values() if v and v != '-')
                coverage = (filled / len(data) * 100) if data else 0
                
                print(f"✅ {coverage:.0f}% | {len(sources)} Quellen | {duration:.1f}s")
                
                # Zeige kritische Felder
                critical = ['Eigentümer', 'Betreiber', 'x-Koordinate', 'y-Koordinate']
                found_critical = [f for f in critical if data.get(f) and data.get(f) != '-']
                if found_critical:
                    print(f"   Gefunden: {', '.join(found_critical)}")
                
                results[model_id] = {
                    'success': True,
                    'coverage': coverage,
                    'sources': len(sources),
                    'duration': duration,
                    'critical_fields': found_critical
                }
            else:
                print(f"❌ {result.get('error', 'Fehler')}")
                results[model_id] = {'success': False, 'error': result.get('error')}
                
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            results[model_id] = {'success': False, 'error': str(e)}
    
    # 2. Teste beste Kombination
    print("\n\n2. MULTI-MODEL TEST:")
    print("\nBeste Kombination (perplexity + scrapingbee): ", end='', flush=True)
    
    start_time = datetime.now()
    try:
        result = await service.search_with_multiple_models(
            model_ids=['perplexity:sonar-pro', 'scrapingbee:basic-scrape'],
            mine_name=mine['name'],
            country=mine['country'],
            commodity=mine['commodity'],
            region=mine['region']
        )
        
        duration = (datetime.now() - start_time).total_seconds()
        
        if result.get('success'):
            best_coverage = 0
            total_sources = 0
            
            for model_result in result.get('results', {}).values():
                if model_result.get('success'):
                    data = model_result.get('data', {})
                    filled = sum(1 for v in data.values() if v and v != '-')
                    coverage = (filled / len(data) * 100) if data else 0
                    best_coverage = max(best_coverage, coverage)
                    total_sources += len(model_result.get('sources', []))
            
            print(f"✅ {best_coverage:.0f}% | {total_sources} Quellen | {duration:.1f}s")
        else:
            print("❌ Fehler")
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
    
    # 3. Zusammenfassung
    print("\n\n" + "="*60)
    print("ZUSAMMENFASSUNG:")
    print("="*60)
    
    # Sortiere nach Abdeckung
    successful = {k: v for k, v in results.items() if v.get('success')}
    if successful:
        sorted_models = sorted(successful.items(), 
                             key=lambda x: x[1].get('coverage', 0), 
                             reverse=True)
        
        print("\nErfolgreiche Modelle (nach Abdeckung):")
        for model_id, stats in sorted_models:
            print(f"  {model_id}: {stats['coverage']:.0f}% Abdeckung, "
                  f"{stats['sources']} Quellen, {stats['duration']:.1f}s")
            if stats.get('critical_fields'):
                print(f"    → Kritische Felder: {', '.join(stats['critical_fields'])}")
    
    print("\n✅ Test abgeschlossen!")
    
    # Speichere Ergebnisse
    filename = f"quick_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nErgebnisse gespeichert in: {filename}")


if __name__ == "__main__":
    asyncio.run(quick_test())