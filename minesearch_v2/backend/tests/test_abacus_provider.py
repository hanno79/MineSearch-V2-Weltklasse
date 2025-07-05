"""
Author: rahn
Datum: 04.07.2025
Version: 1.0
Beschreibung: Test-Skript für Abacus AI Provider
"""

import asyncio
import logging
from datetime import datetime
import json

from config import config
from providers.abacus_provider import AbacusProvider

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_abacus_provider():
    """Teste Abacus AI Provider mit einer Quebec-Mine"""
    
    print("\n" + "="*60)
    print("ABACUS AI PROVIDER TEST")
    print("="*60)
    
    # Provider initialisieren
    provider_config = config.PROVIDERS.get('abacus', {})
    if not provider_config.get('api_key'):
        print("❌ FEHLER: Kein ABACUS_API_KEY in .env gefunden!")
        return
    
    provider = AbacusProvider(
        api_key=provider_config['api_key'],
        config=provider_config
    )
    
    # Validiere Konfiguration
    if not provider.validate_config():
        print("❌ FEHLER: Provider-Konfiguration ungültig!")
        return
    
    print(f"✅ Provider initialisiert")
    print(f"📋 Verfügbare Modelle: {list(provider.get_models().keys())}")
    
    # Test-Mine aus Quebec
    test_mine = {
        'name': 'Jeffrey Mine',
        'country': 'Kanada',
        'region': 'Quebec',
        'commodity': 'Asbest'
    }
    
    print(f"\n🔍 Teste mit Mine: {test_mine['name']}")
    print(f"   Land: {test_mine['country']}")
    print(f"   Region: {test_mine['region']}")
    print(f"   Rohstoff: {test_mine['commodity']}")
    
    # Query erstellen
    query = f"""Suche detaillierte Informationen über die {test_mine['name']} Mine in {test_mine['region']}, {test_mine['country']}.
Diese Mine war bekannt für {test_mine['commodity']}-Abbau.
Finde insbesondere Restaurationskosten, GPS-Koordinaten, Eigentümer/Betreiber und Produktionsdaten."""
    
    # Optionen
    options = {
        'mine_name': test_mine['name'],
        'country': test_mine['country'],
        'region': test_mine['region'],
        'commodity': test_mine['commodity'],
        'currency': 'CAD',
        'temperature': 0.2
    }
    
    print("\n⏳ Starte Deep Research (kann 2-5 Minuten dauern)...")
    start_time = datetime.now()
    
    try:
        # Führe Suche durch
        result = await provider.search(
            query=query,
            model_id='deep-agent',
            options=options
        )
        
        duration = (datetime.now() - start_time).total_seconds()
        print(f"\n✅ Suche abgeschlossen in {duration:.1f} Sekunden")
        
        # Ergebnisse anzeigen
        if result.success:
            print("\n📊 ERGEBNISSE:")
            print("-" * 50)
            
            # Strukturierte Daten
            data = result.structured_data
            print("\nExtrahierte Daten:")
            for field, value in data.items():
                if value and value != '-':
                    print(f"  {field}: {value}")
            
            # Datenabdeckung
            filled_fields = sum(1 for v in data.values() if v and v != '-')
            total_fields = len(data)
            coverage = (filled_fields / total_fields) * 100 if total_fields > 0 else 0
            print(f"\n📈 Datenabdeckung: {filled_fields}/{total_fields} ({coverage:.1f}%)")
            
            # Kritische Felder prüfen
            print("\n🔍 Kritische Felder:")
            critical_fields = ['Restaurationskosten', 'x-Koordinate', 'y-Koordinate', 
                             'Eigentümer', 'Betreiber']
            for field in critical_fields:
                value = data.get(field, '')
                status = "✅" if value and value != '-' else "❌"
                print(f"  {status} {field}: {value if value else 'Nicht gefunden'}")
            
            # Quellen
            print(f"\n📚 Gefundene Quellen: {len(result.sources)}")
            for i, source in enumerate(result.sources[:5], 1):
                print(f"  [{i}] {source.get('value', source.get('url', 'Unbekannt'))}")
            
            # Metadata
            print("\n🔧 Metadata:")
            print(f"  Session ID: {result.metadata.get('session_id', 'N/A')}")
            print(f"  Deep Research: {result.metadata.get('deep_research', False)}")
            print(f"  Discovered Sources: {result.metadata.get('discovered_sources_count', 0)}")
            
        else:
            print(f"\n❌ FEHLER: {result.error}")
            
    except Exception as e:
        print(f"\n❌ FEHLER bei Test: {str(e)}")
        logger.error(f"Test fehlgeschlagen", exc_info=True)
    
    print("\n" + "="*60)
    print("TEST ABGESCHLOSSEN")
    print("="*60)


async def test_comparison():
    """Vergleiche Abacus mit anderen Providern"""
    
    print("\n" + "="*60)
    print("PROVIDER-VERGLEICH")
    print("="*60)
    
    test_mine = {
        'name': 'LAB Chrysotile Mine',
        'country': 'Kanada',
        'region': 'Quebec',
        'commodity': 'Chrysotil'
    }
    
    providers_to_test = [
        ('perplexity:sonar-pro', 'Perplexity Sonar Pro'),
        ('abacus:deep-agent', 'Abacus Deep Agent')
    ]
    
    results = {}
    
    for model_id, model_name in providers_to_test:
        print(f"\n🔍 Teste {model_name}...")
        
        # Multi-Provider Search Service nutzen
        from search_service_multi import MultiProviderSearchService
        service = MultiProviderSearchService()
        
        try:
            result = await service.search_with_model(
                model_id=model_id,
                mine_name=test_mine['name'],
                country=test_mine['country'],
                commodity=test_mine['commodity'],
                region=test_mine['region']
            )
            
            if result.get('success'):
                data = result.get('data', {})
                filled = sum(1 for v in data.values() if v and v != '-')
                total = len(data)
                coverage = (filled / total) * 100 if total > 0 else 0
                
                results[model_name] = {
                    'coverage': coverage,
                    'restoration_costs': data.get('Restaurationskosten', ''),
                    'coordinates': f"{data.get('x-Koordinate', '')}, {data.get('y-Koordinate', '')}",
                    'duration': result.get('search_duration', 0)
                }
                
                print(f"  ✅ Datenabdeckung: {coverage:.1f}%")
                print(f"  ⏱️ Dauer: {result.get('search_duration', 0):.1f}s")
            else:
                print(f"  ❌ Fehler: {result.get('error', 'Unbekannt')}")
                
        except Exception as e:
            print(f"  ❌ Exception: {str(e)}")
    
    # Vergleichstabelle
    if results:
        print("\n📊 VERGLEICHSERGEBNISSE:")
        print("-" * 80)
        print(f"{'Modell':<25} {'Abdeckung':<15} {'Restauration':<20} {'Dauer':<10}")
        print("-" * 80)
        
        for model, data in results.items():
            print(f"{model:<25} {data['coverage']:<15.1f}% "
                  f"{data['restoration_costs'][:18]:<20} {data['duration']:<10.1f}s")


if __name__ == "__main__":
    # Einzeltest
    asyncio.run(test_abacus_provider())
    
    # Optional: Vergleichstest
    # asyncio.run(test_comparison())