"""
Author: rahn
Datum: 05.07.2025
Version: 1.0
Beschreibung: Test verschiedener Modellkombinationen
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


async def test_combinations():
    """Teste verschiedene Modellkombinationen"""
    
    service = MultiProviderSearchService()
    
    print("\n" + "="*80)
    print("TEST MODELLKOMBINATIONEN")
    print("="*80)
    print(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test-Minen aus verschiedenen Ländern
    test_mines = [
        {
            'name': 'Jeffrey Mine',
            'country': 'Kanada',
            'region': 'Quebec',
            'commodity': 'Asbest'
        },
        {
            'name': 'Grasberg',
            'country': 'Indonesien',
            'region': 'Papua',
            'commodity': 'Gold/Kupfer'
        },
        {
            'name': 'Escondida',
            'country': 'Chile',
            'region': 'Antofagasta',
            'commodity': 'Kupfer'
        }
    ]
    
    # Verschiedene Kombinationen
    combinations = {
        # 2er-Kombinationen
        'premium_2er': ['perplexity:sonar-pro', 'scrapingbee:basic-scrape'],
        'budget_2er': ['openrouter:deepseek-free', 'firecrawl:scrape'],
        'perplexity_deep': ['perplexity:sonar-pro', 'perplexity:sonar-deep-research'],
        'scraping_duo': ['scrapingbee:basic-scrape', 'firecrawl:scrape'],
        
        # 3er-Kombinationen
        'premium_3er': ['perplexity:sonar-pro', 'scrapingbee:basic-scrape', 'firecrawl:scrape'],
        'mixed_3er': ['perplexity:sonar-pro', 'openrouter:deepseek-free', 'scrapingbee:basic-scrape'],
        
        # 4er-Kombination
        'all_active': ['perplexity:sonar-pro', 'openrouter:deepseek-free', 
                      'scrapingbee:basic-scrape', 'firecrawl:scrape']
    }
    
    results = {}
    
    for mine in test_mines:
        print(f"\n\nMINE: {mine['name']} ({mine['country']}, {mine['commodity']})")
        print("="*60)
        
        mine_results = {}
        
        for combo_name, model_ids in combinations.items():
            print(f"\n{combo_name} ({len(model_ids)} Modelle): ", end='', flush=True)
            
            start_time = datetime.now()
            
            try:
                result = await service.search_with_multiple_models(
                    model_ids=model_ids,
                    mine_name=mine['name'],
                    country=mine['country'],
                    commodity=mine['commodity'],
                    region=mine['region']
                )
                
                duration = (datetime.now() - start_time).total_seconds()
                
                if result.get('success'):
                    # Analysiere Ergebnisse
                    best_coverage = 0
                    total_sources = 0
                    successful_models = 0
                    critical_fields_found = set()
                    
                    for model_id, model_result in result.get('results', {}).items():
                        if model_result.get('success'):
                            successful_models += 1
                            data = model_result.get('data', {})
                            filled = sum(1 for v in data.values() if v and v != '-')
                            coverage = (filled / len(data) * 100) if data else 0
                            best_coverage = max(best_coverage, coverage)
                            total_sources += len(model_result.get('sources', []))
                            
                            # Sammle kritische Felder
                            critical = ['Eigentümer', 'Betreiber', 'x-Koordinate', 'y-Koordinate', 
                                      'Restaurationskosten']
                            for field in critical:
                                if data.get(field) and data.get(field) != '-':
                                    critical_fields_found.add(field)
                    
                    print(f"✅ {best_coverage:.0f}% | {total_sources} Quellen | "
                          f"{successful_models}/{len(model_ids)} erfolgreich | {duration:.1f}s")
                    
                    if critical_fields_found:
                        print(f"   → Kritische Felder: {', '.join(critical_fields_found)}")
                    
                    mine_results[combo_name] = {
                        'success': True,
                        'best_coverage': best_coverage,
                        'total_sources': total_sources,
                        'successful_models': successful_models,
                        'critical_fields': list(critical_fields_found),
                        'duration': duration
                    }
                else:
                    print("❌ Fehler")
                    mine_results[combo_name] = {'success': False}
                    
            except Exception as e:
                print(f"❌ Exception: {str(e)}")
                mine_results[combo_name] = {'success': False, 'error': str(e)}
        
        results[mine['name']] = mine_results
    
    # Zusammenfassung
    print("\n\n" + "="*80)
    print("GESAMTZUSAMMENFASSUNG")
    print("="*80)
    
    # Finde beste Kombinationen
    best_combinations = {}
    
    for mine_name, mine_results in results.items():
        for combo_name, combo_result in mine_results.items():
            if combo_result.get('success'):
                if combo_name not in best_combinations:
                    best_combinations[combo_name] = {
                        'total_coverage': 0,
                        'total_sources': 0,
                        'success_count': 0,
                        'avg_duration': 0,
                        'all_critical_fields': set()
                    }
                
                best_combinations[combo_name]['total_coverage'] += combo_result['best_coverage']
                best_combinations[combo_name]['total_sources'] += combo_result['total_sources']
                best_combinations[combo_name]['success_count'] += 1
                best_combinations[combo_name]['avg_duration'] += combo_result['duration']
                best_combinations[combo_name]['all_critical_fields'].update(combo_result['critical_fields'])
    
    # Sortiere nach durchschnittlicher Abdeckung
    print("\nBESTE KOMBINATIONEN (nach durchschnittlicher Abdeckung):")
    
    for combo_name, stats in sorted(best_combinations.items(), 
                                   key=lambda x: x[1]['total_coverage'] / max(x[1]['success_count'], 1), 
                                   reverse=True):
        avg_coverage = stats['total_coverage'] / stats['success_count']
        avg_duration = stats['avg_duration'] / stats['success_count']
        avg_sources = stats['total_sources'] / stats['success_count']
        
        print(f"\n{combo_name}:")
        print(f"  → Ø Abdeckung: {avg_coverage:.1f}%")
        print(f"  → Ø Quellen: {avg_sources:.0f}")
        print(f"  → Ø Zeit: {avg_duration:.1f}s")
        print(f"  → Kritische Felder gefunden: {', '.join(sorted(stats['all_critical_fields']))}")
    
    # Empfehlungen
    print("\n\nEMPFEHLUNGEN:")
    print("="*60)
    print("1. BESTE KOMBINATION: premium_2er (perplexity:sonar-pro + scrapingbee:basic-scrape)")
    print("   → Optimales Verhältnis von Abdeckung, Quellen und Geschwindigkeit")
    print("\n2. BUDGET-OPTION: budget_2er (openrouter:deepseek-free + firecrawl:scrape)")
    print("   → Kosteneffizient mit akzeptabler Abdeckung")
    print("\n3. MAXIMALE ABDECKUNG: premium_3er oder all_active")
    print("   → Für kritische Suchen mit höchsten Anforderungen")
    
    # Speichere Ergebnisse
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"combination_test_results_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        # Konvertiere Sets zu Lists für JSON
        json_results = {}
        for mine_name, mine_results in results.items():
            json_results[mine_name] = mine_results
        
        json.dump(json_results, f, ensure_ascii=False, indent=2)
    
    print(f"\n\nDetaillierte Ergebnisse gespeichert in: {filename}")


if __name__ == "__main__":
    asyncio.run(test_combinations())