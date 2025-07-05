"""
Author: rahn
Datum: 05.07.2025
Version: 1.0
Beschreibung: Test der korrigierten Scraping-Provider
"""

import asyncio
from datetime import datetime
from search_service_multi import MultiProviderSearchService


async def test_corrected_providers():
    """Testet die korrigierten Provider"""
    
    print("\n" + "="*80)
    print("TEST DER KORRIGIERTEN PROVIDER")
    print("="*80)
    
    service = MultiProviderSearchService()
    
    # Test-Mine
    mine = {
        'name': 'Jeffrey Mine',
        'country': 'Kanada',
        'region': 'Quebec',
        'commodity': 'Asbest'
    }
    
    # Teste nur die neuen Provider
    test_models = [
        'scrapingbee:basic-scrape',
        'scrapingbee:ai-extract',
        'firecrawl:scrape',
        'brightdata:web-scraper'
    ]
    
    print(f"\nTeste Mine: {mine['name']} ({mine['country']})")
    print("="*80)
    
    for model_id in test_models:
        print(f"\n{model_id}:", end=' ', flush=True)
        
        try:
            start = datetime.now()
            
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
                
                # Prüfe auf API-Notiz
                if metadata.get('note') == 'API-Integration ausstehend':
                    print(f"⚠️ Platzhalter-Implementierung ({duration:.1f}s)")
                else:
                    filled = sum(1 for v in data.values() if v and v != '-')
                    coverage = (filled / len(data) * 100) if data else 0
                    print(f"✅ {coverage:.0f}% Abdeckung | {len(sources)} Quellen | {duration:.1f}s")
                    
                    # Zeige Fehler im Content wenn vorhanden
                    content = result.get('content', '')
                    if 'error' in content.lower() or 'fehler' in content.lower():
                        print(f"   ⚠️ Inhalt enthält Fehler: {content[:100]}...")
            else:
                error = result.get('error', 'Unbekannt')
                print(f"❌ {error[:100]}")
                
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
    
    print("\n\n" + "="*80)
    print("ZUSAMMENFASSUNG")
    print("="*80)
    print("\nKorrekturen implementiert:")
    print("- ScrapingBee: API-Parameter angepasst, Premium Proxy aktiviert")
    print("- Firecrawl: Parameter für v1 API korrigiert, Domain-Fehler behoben")
    print("- Brightdata: Platzhalter-Implementierung (komplexe Proxy-API)")
    print("\nNächste Schritte:")
    print("1. ScrapingBee und Firecrawl API-Keys verifizieren")
    print("2. Brightdata API-Dokumentation studieren")
    print("3. Fokus auf funktionierende Provider (Perplexity, OpenRouter)")
    
    # Teste auch die Hauptprovider
    print("\n\nZum Vergleich - Hauptprovider:")
    print("="*80)
    
    main_models = ['perplexity:sonar-pro', 'openrouter:deepseek-free']
    
    for model_id in main_models:
        print(f"\n{model_id}:", end=' ', flush=True)
        
        try:
            start = datetime.now()
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
                filled = sum(1 for v in data.values() if v and v != '-')
                coverage = (filled / len(data) * 100) if data else 0
                print(f"✅ {coverage:.0f}% Abdeckung | {len(sources)} Quellen | {duration:.1f}s")
            else:
                print(f"❌ {result.get('error', 'Fehler')}")
        except Exception as e:
            print(f"❌ Exception: {str(e)}")


if __name__ == "__main__":
    asyncio.run(test_corrected_providers())