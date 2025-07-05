"""
Author: rahn
Datum: 05.07.2025
Version: 1.0
Beschreibung: Schneller Validierungstest für wichtigste Modelle
"""

import asyncio
from datetime import datetime
from search_service_multi import MultiProviderSearchService


async def quick_test():
    """Schneller Test der wichtigsten Modelle"""
    
    print("\n" + "="*60)
    print("SCHNELLER VALIDIERUNGSTEST")
    print("="*60)
    
    service = MultiProviderSearchService()
    
    # Test-Mine
    mine = {
        'name': 'Jeffrey Mine',
        'country': 'Kanada',
        'region': 'Quebec',
        'commodity': 'Asbest'
    }
    
    # Wichtigste Modelle
    test_models = [
        'perplexity:sonar',
        'perplexity:sonar-pro',
        'perplexity:sonar-deep-research',
        'tavily:search',
        'tavily:deep-research',
        'exa:neural-search',
        'exa:research',
        'openrouter:deepseek-free'
    ]
    
    # Verfügbare Modelle prüfen
    all_models = list(service.registry.get_all_models().keys())
    
    print(f"\nVerfügbare Modelle: {len(all_models)}")
    for model in all_models:
        print(f"  - {model}")
    
    print(f"\n\nTeste Mine: {mine['name']} ({mine['commodity']})")
    print("="*60)
    
    results = {}
    
    for model_id in test_models:
        if model_id not in all_models:
            print(f"\n{model_id}: ⚠️ Nicht verfügbar")
            continue
            
        print(f"\n{model_id}:", end=' ', flush=True)
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
                
                # Wichtige Felder prüfen
                important_fields = {
                    'Restaurationskosten': data.get('Restaurationskosten', ''),
                    'x-Koordinate': data.get('x-Koordinate', ''),
                    'y-Koordinate': data.get('y-Koordinate', ''),
                    'Eigentümer': data.get('Eigentümer', ''),
                    'Betreiber': data.get('Betreiber', '')
                }
                
                filled = sum(1 for v in data.values() if v and v != '-')
                coverage = (filled / len(data) * 100) if data else 0
                
                print(f"✅ {coverage:.0f}% Abdeckung | {len(sources)} Quellen | {duration:.1f}s")
                
                # Zeige gefundene wichtige Felder
                found_important = {k: v for k, v in important_fields.items() if v and v != '-'}
                if found_important:
                    print(f"   Gefunden: {', '.join(found_important.keys())}")
                    for field, value in found_important.items():
                        print(f"   - {field}: {value[:50]}{'...' if len(value) > 50 else ''}")
                
                # Quellenanalyse
                if sources:
                    print(f"   Quellentypen:")
                    pdf_count = sum(1 for s in sources if '.pdf' in s.get('value', '').lower())
                    gov_count = sum(1 for s in sources if any(d in s.get('value', '') for d in ['.gov', '.gc.ca']))
                    print(f"   - PDFs: {pdf_count}")
                    print(f"   - Regierung: {gov_count}")
                    print(f"   - Erste Quelle: {sources[0].get('value', '')[:80]}...")
                
                results[model_id] = {
                    'success': True,
                    'coverage': coverage,
                    'sources': len(sources),
                    'duration': duration,
                    'important_found': len(found_important)
                }
                
            else:
                error = result.get('error', 'Unbekannt')
                print(f"❌ {error[:100]}")
                results[model_id] = {'success': False, 'error': error}
                
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            results[model_id] = {'success': False, 'error': str(e)}
    
    # Zusammenfassung
    print("\n\n" + "="*60)
    print("ZUSAMMENFASSUNG")
    print("="*60)
    
    successful = {k: v for k, v in results.items() if v.get('success')}
    if successful:
        sorted_by_coverage = sorted(successful.items(), 
                                   key=lambda x: x[1]['coverage'], 
                                   reverse=True)
        
        print("\nERFOLGREICHE MODELLE (nach Abdeckung):")
        for i, (model_id, data) in enumerate(sorted_by_coverage, 1):
            print(f"{i}. {model_id}: {data['coverage']:.1f}% | "
                  f"{data['sources']} Quellen | "
                  f"{data['important_found']} wichtige Felder")
    
    failed = {k: v for k, v in results.items() if not v.get('success')}
    if failed:
        print("\nFEHLGESCHLAGENE MODELLE:")
        for model_id, data in failed.items():
            print(f"- {model_id}: {data['error'][:80]}")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    asyncio.run(quick_test())