"""
Author: rahn
Datum: 05.07.2025
Version: 1.0
Beschreibung: Umfassender Test für neue Scraping-Provider
"""

import asyncio
from datetime import datetime
import json
from search_service_multi import MultiProviderSearchService


async def test_new_providers():
    """Testet die neuen Scraping-Provider umfassend"""
    
    print("\n" + "="*80)
    print("TEST DER NEUEN SCRAPING-PROVIDER")
    print("="*80)
    
    service = MultiProviderSearchService()
    
    # Test-Minen für verschiedene Anwendungsfälle
    test_mines = [
        {
            'name': 'Jeffrey Mine',
            'country': 'Kanada',
            'region': 'Quebec',
            'commodity': 'Asbest',
            'description': 'Historische Asbestmine mit umfangreicher Dokumentation'
        },
        {
            'name': 'Antamina',
            'country': 'Peru',
            'region': 'Ancash',
            'commodity': 'Kupfer/Zink',
            'description': 'Große aktive Mine mit aktuellen Finanzdaten'
        }
    ]
    
    # Neue Provider-Modelle
    new_models = [
        # ScrapingBee
        'scrapingbee:basic-scrape',
        'scrapingbee:js-render',
        'scrapingbee:ai-extract',
        # Firecrawl
        'firecrawl:scrape',
        'firecrawl:crawl',
        'firecrawl:extract',
        # Brightdata
        'brightdata:web-scraper',
        'brightdata:browser-api',
        'brightdata:search-api'
    ]
    
    # Verfügbare Modelle prüfen
    all_models = list(service.registry.get_all_models().keys())
    print(f"\nGesamtzahl verfügbarer Modelle: {len(all_models)}")
    
    # Zeige nur neue Provider
    new_provider_models = [m for m in all_models if m.startswith(('scrapingbee:', 'firecrawl:', 'brightdata:'))]
    print(f"\nNeue Provider-Modelle ({len(new_provider_models)}):")
    for model in new_provider_models:
        config = service.registry.get_model_config(model)
        print(f"  - {model}: {config.description}")
    
    # Teste jede Mine mit jedem neuen Modell
    all_results = []
    
    for mine in test_mines:
        print(f"\n\n{'='*80}")
        print(f"TESTE MINE: {mine['name']} ({mine['country']})")
        print(f"Beschreibung: {mine['description']}")
        print("="*80)
        
        mine_results = {
            'mine': mine,
            'results': {}
        }
        
        for model_id in new_models:
            if model_id not in all_models:
                print(f"\n{model_id}: ⚠️ Nicht verfügbar")
                continue
            
            print(f"\n{'-'*60}")
            print(f"Modell: {model_id}")
            config = service.registry.get_model_config(model_id)
            print(f"Beschreibung: {config.description}")
            if hasattr(config, 'credits_cost'):
                print(f"Credits: {config.credits_cost}")
            print("-"*60)
            
            start = datetime.now()
            
            try:
                result = await service.search_with_model(
                    model_id=model_id,
                    mine_name=mine['name'],
                    country=mine['country'],
                    commodity=mine['commodity'],
                    region=mine['region']
                )
                
                duration = (datetime.now() - start).total_seconds()
                
                if result.get('success'):
                    data = result.get('data', {})
                    sources = result.get('sources', [])
                    metadata = result.get('metadata', {})
                    
                    # Analysiere Ergebnisse
                    filled_fields = sum(1 for v in data.values() if v and v != '-')
                    total_fields = len(data)
                    coverage = (filled_fields / total_fields * 100) if total_fields > 0 else 0
                    
                    # Wichtige Felder
                    critical_fields = {
                        'Koordinaten': (data.get('x-Koordinate', '-') != '-' and 
                                       data.get('y-Koordinate', '-') != '-'),
                        'Eigentümer': data.get('Eigentümer', '-') != '-',
                        'Betreiber': data.get('Betreiber', '-') != '-',
                        'Restaurationskosten': data.get('Restaurationskosten', '-') != '-',
                        'Produktionsstart': data.get('Produktionsstart', '-') != '-',
                        'Minentyp': data.get('Minentyp (Untertage/ Open-Pit/ usw.)', '-') != '-'
                    }
                    
                    critical_found = sum(1 for v in critical_fields.values() if v)
                    
                    print(f"✅ ERFOLG")
                    print(f"   Dauer: {duration:.1f}s")
                    print(f"   Abdeckung: {coverage:.1f}% ({filled_fields}/{total_fields} Felder)")
                    print(f"   Kritische Felder: {critical_found}/6")
                    print(f"   Quellen: {len(sources)}")
                    
                    # Zeige gefundene kritische Felder
                    if critical_found > 0:
                        print("   Gefundene kritische Felder:")
                        for field, found in critical_fields.items():
                            if found:
                                if field == 'Koordinaten':
                                    print(f"     - {field}: {data.get('x-Koordinate')}, {data.get('y-Koordinate')}")
                                else:
                                    field_map = {
                                        'Eigentümer': 'Eigentümer',
                                        'Betreiber': 'Betreiber',
                                        'Restaurationskosten': 'Restaurationskosten',
                                        'Produktionsstart': 'Produktionsstart',
                                        'Minentyp': 'Minentyp (Untertage/ Open-Pit/ usw.)'
                                    }
                                    value = data.get(field_map[field], '')
                                    print(f"     - {field}: {value[:50]}{'...' if len(value) > 50 else ''}")
                    
                    # Quellenanalyse
                    if sources:
                        print("   Quellentypen:")
                        source_types = {}
                        for source in sources:
                            s_type = source.get('type', 'unknown')
                            source_types[s_type] = source_types.get(s_type, 0) + 1
                        for s_type, count in source_types.items():
                            print(f"     - {s_type}: {count}")
                        
                        # Zeige erste Quelle
                        print(f"   Erste Quelle: {sources[0].get('value', '')[:100]}...")
                    
                    # Metadata
                    if metadata:
                        print("   Metadata:")
                        for key, value in metadata.items():
                            if key not in ['provider', 'model']:
                                print(f"     - {key}: {value}")
                    
                    mine_results['results'][model_id] = {
                        'success': True,
                        'duration': duration,
                        'coverage': coverage,
                        'critical_fields': critical_found,
                        'sources': len(sources),
                        'data': data
                    }
                    
                else:
                    error = result.get('error', 'Unbekannter Fehler')
                    print(f"❌ FEHLER: {error[:200]}")
                    mine_results['results'][model_id] = {
                        'success': False,
                        'error': error,
                        'duration': duration
                    }
                    
            except Exception as e:
                print(f"❌ EXCEPTION: {str(e)}")
                mine_results['results'][model_id] = {
                    'success': False,
                    'error': str(e),
                    'duration': (datetime.now() - start).total_seconds()
                }
        
        all_results.append(mine_results)
    
    # Gesamtauswertung
    print("\n\n" + "="*80)
    print("GESAMTAUSWERTUNG")
    print("="*80)
    
    # Erfolgreichste Modelle
    model_stats = {}
    for mine_result in all_results:
        for model_id, result in mine_result['results'].items():
            if model_id not in model_stats:
                model_stats[model_id] = {
                    'successes': 0,
                    'failures': 0,
                    'total_coverage': 0,
                    'total_critical': 0,
                    'total_duration': 0,
                    'total_sources': 0
                }
            
            if result['success']:
                model_stats[model_id]['successes'] += 1
                model_stats[model_id]['total_coverage'] += result['coverage']
                model_stats[model_id]['total_critical'] += result['critical_fields']
                model_stats[model_id]['total_sources'] += result['sources']
            else:
                model_stats[model_id]['failures'] += 1
            
            model_stats[model_id]['total_duration'] += result['duration']
    
    print("\nMODELL-RANKING (nach durchschnittlicher Abdeckung):")
    
    ranked_models = []
    for model_id, stats in model_stats.items():
        if stats['successes'] > 0:
            avg_coverage = stats['total_coverage'] / stats['successes']
            avg_critical = stats['total_critical'] / stats['successes']
            avg_sources = stats['total_sources'] / stats['successes']
            avg_duration = stats['total_duration'] / (stats['successes'] + stats['failures'])
            
            ranked_models.append({
                'model': model_id,
                'avg_coverage': avg_coverage,
                'avg_critical': avg_critical,
                'avg_sources': avg_sources,
                'avg_duration': avg_duration,
                'success_rate': stats['successes'] / (stats['successes'] + stats['failures']) * 100
            })
    
    ranked_models.sort(key=lambda x: x['avg_coverage'], reverse=True)
    
    for i, model in enumerate(ranked_models, 1):
        print(f"\n{i}. {model['model']}:")
        print(f"   - Durchschnittliche Abdeckung: {model['avg_coverage']:.1f}%")
        print(f"   - Kritische Felder (Ø): {model['avg_critical']:.1f}/6")
        print(f"   - Quellen (Ø): {model['avg_sources']:.1f}")
        print(f"   - Dauer (Ø): {model['avg_duration']:.1f}s")
        print(f"   - Erfolgsrate: {model['success_rate']:.0f}%")
    
    # Speichere detaillierte Ergebnisse
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"new_providers_test_results_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump({
            'test_date': timestamp,
            'mines_tested': test_mines,
            'models_tested': new_models,
            'detailed_results': all_results,
            'model_rankings': ranked_models
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n\nDetaillierte Ergebnisse gespeichert in: {filename}")
    
    # Empfehlungen
    print("\n" + "="*80)
    print("EMPFEHLUNGEN")
    print("="*80)
    
    if ranked_models:
        best_model = ranked_models[0]
        print(f"\n1. BESTES MODELL: {best_model['model']}")
        print(f"   - Beste durchschnittliche Abdeckung: {best_model['avg_coverage']:.1f}%")
        print(f"   - Findet durchschnittlich {best_model['avg_critical']:.1f} kritische Felder")
        
        # Schnellstes Modell mit guter Qualität
        fast_good_models = [m for m in ranked_models if m['avg_coverage'] > 30 and m['avg_duration'] < 60]
        if fast_good_models:
            fastest = min(fast_good_models, key=lambda x: x['avg_duration'])
            print(f"\n2. SCHNELL & GUT: {fastest['model']}")
            print(f"   - {fastest['avg_coverage']:.1f}% Abdeckung in nur {fastest['avg_duration']:.1f}s")
        
        # Deep Research Empfehlung
        deep_models = [m for m in ranked_models if 'crawl' in m['model'] or 'browser' in m['model'] or 'extract' in m['model']]
        if deep_models:
            best_deep = deep_models[0]
            print(f"\n3. DEEP RESEARCH: {best_deep['model']}")
            print(f"   - Für umfassende Suchen mit {best_deep['avg_sources']:.1f} Quellen im Schnitt")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    asyncio.run(test_new_providers())