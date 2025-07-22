"""
Author: rahn
Datum: 04.07.2025
Version: 1.0
Beschreibung: Umfassender System-Test mit Quebec-Minen
"""

import asyncio
import logging
from datetime import datetime
import json
import sys
import os
from typing import Dict, List, Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from search_service_multi import MultiProviderSearchService
from config.base import config

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Test-Minen aus Quebec
TEST_MINES = [
    {
        'name': 'Jeffrey Mine',
        'country': 'Kanada',
        'region': 'Quebec',
        'commodity': 'Asbest',
        'expected_fields': ['Restaurationskosten', 'x-Koordinate', 'y-Koordinate']
    },
    {
        'name': 'LAB Chrysotile Mine',
        'country': 'Kanada',
        'region': 'Quebec',
        'commodity': 'Chrysotil',
        'expected_fields': ['Eigentümer', 'Betreiber', 'Produktionsstart']
    },
    {
        'name': 'Horne Mine',
        'country': 'Kanada',
        'region': 'Quebec',
        'commodity': 'Kupfer',
        'expected_fields': ['Produktionsende', 'Fördermenge/Jahr']
    },
    {
        'name': 'East Malartic Mine',
        'country': 'Kanada',
        'region': 'Quebec',
        'commodity': 'Gold',
        'expected_fields': ['Aktivitätsstatus', 'Fläche der Mine in qkm']
    }
]


async def test_single_model(service: MultiProviderSearchService, model_id: str, mine: Dict):
    """Teste ein einzelnes Modell mit einer Mine"""
    
    print(f"\n  🔍 {model_id}: ", end='', flush=True)
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
            
            # Prüfe Datenabdeckung
            filled = sum(1 for v in data.values() if v and v != '-')
            total = len(data)
            coverage = (filled / total * 100) if total > 0 else 0
            
            # Prüfe kritische Felder
            critical_found = 0
            for field in mine['expected_fields']:
                if data.get(field):
                    critical_found += 1
            
            # Prüfe auf Platzhalter
            placeholder_found = False
            for field, value in data.items():
                if value and 'kosten' in field.lower():
                    if any(p in str(value).lower() for p in ['$1', '$2', '$3', 'cad', 'n/a', 'k.a']):
                        placeholder_found = True
                        break
            
            print(f"✅ {coverage:.0f}% | {critical_found}/{len(mine['expected_fields'])} kritisch | {duration:.1f}s", end='')
            
            if placeholder_found:
                print(" ⚠️ PLATZHALTER!")
            else:
                print()
            
            return {
                'success': True,
                'coverage': coverage,
                'critical_found': critical_found,
                'duration': duration,
                'data': data,
                'placeholder_found': placeholder_found
            }
        else:
            print(f"❌ Fehler: {result.get('error', 'Unbekannt')}")
            return {'success': False, 'error': result.get('error')}
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return {'success': False, 'error': str(e)}


async def test_multi_model(service: MultiProviderSearchService, model_ids: List[str], mine: Dict):
    """Teste Multi-Model-Suche"""
    
    print(f"\n  🔍 Multi-Model ({len(model_ids)} Modelle): ", end='', flush=True)
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
            # Sammle beste Ergebnisse
            best_coverage = 0
            all_results = result.get('results', {})
            
            for model_id, model_result in all_results.items():
                if model_result.get('success'):
                    data = model_result.get('data', {})
                    filled = sum(1 for v in data.values() if v and v != '-')
                    total = len(data)
                    coverage = (filled / total * 100) if total > 0 else 0
                    best_coverage = max(best_coverage, coverage)
            
            print(f"✅ Beste: {best_coverage:.0f}% | {duration:.1f}s")
            return {'success': True, 'best_coverage': best_coverage, 'duration': duration}
        else:
            print(f"❌ Fehler")
            return {'success': False}
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return {'success': False, 'error': str(e)}


async def test_two_phase(service: MultiProviderSearchService, mine: Dict):
    """Teste Zwei-Phasen-Suche"""
    
    print(f"\n  🔍 Zwei-Phasen-Suche: ", end='', flush=True)
    start_time = datetime.now()
    
    try:
        result = await service.search_two_phase(
            mine_name=mine['name'],
            country=mine['country'],
            commodity=mine['commodity'],
            region=mine['region']
        )
        
        duration = (datetime.now() - start_time).total_seconds()
        
        if result.get('success'):
            data = result.get('data', {})
            filled = sum(1 for v in data.values() if v and v != '-')
            total = len(data)
            coverage = (filled / total * 100) if total > 0 else 0
            
            phase3 = result.get('phase3_triggered', False)
            phase_info = "3-Phasen" if phase3 else "2-Phasen"
            
            print(f"✅ {coverage:.0f}% | {phase_info} | {duration:.1f}s")
            return {'success': True, 'coverage': coverage, 'duration': duration, 'phase3': phase3}
        else:
            print(f"❌ Fehler")
            return {'success': False}
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return {'success': False, 'error': str(e)}


async def main():
    """Haupttest-Funktion"""
    
    print("="*80)
    print("UMFASSENDER MINESEARCH V2 SYSTEMTEST")
    print("="*80)
    print(f"Datum: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Anzahl Test-Minen: {len(TEST_MINES)}")
    print("="*80)
    
    # Service initialisieren
    service = MultiProviderSearchService()
    
    # Verfügbare Modelle
    all_models = list(service.registry.get_all_models().keys())
    print(f"\nVerfügbare Modelle ({len(all_models)}):")
    for model in all_models:
        print(f"  - {model}")
    
    # Test-Konfigurationen
    test_configs = {
        'Einzelmodelle': [
            'perplexity:sonar-pro',
            'perplexity:sonar-reasoning-pro',
            'openrouter:deepseek-free'
        ],
        'Multi-Model (Best)': ['perplexity:sonar-pro', 'perplexity:sonar-reasoning-pro'],
        'Multi-Model (All)': all_models[:3],  # Erste 3 Modelle
        'Zwei-Phasen': 'two-phase'
    }
    
    # Wenn Abacus verfügbar, füge es hinzu
    if 'abacus:deep-agent' in all_models:
        test_configs['Abacus Deep Agent'] = ['abacus:deep-agent']
    
    # Ergebnis-Sammlung
    results = {}
    
    # Teste jede Mine
    for mine in TEST_MINES:
        print(f"\n{'='*60}")
        print(f"MINE: {mine['name']} ({mine['region']}, {mine['country']})")
        print(f"Rohstoff: {mine['commodity']}")
        print(f"Kritische Felder: {', '.join(mine['expected_fields'])}")
        print("="*60)
        
        mine_results = {}
        
        # Einzelmodell-Tests
        print("\n1. EINZELMODELL-TESTS:")
        for model_id in test_configs['Einzelmodelle']:
            if model_id in all_models:
                result = await test_single_model(service, model_id, mine)
                mine_results[model_id] = result
        
        # Multi-Model-Tests
        print("\n2. MULTI-MODEL-TESTS:")
        for config_name, model_ids in test_configs.items():
            if config_name.startswith('Multi-Model'):
                result = await test_multi_model(service, model_ids, mine)
                mine_results[config_name] = result
        
        # Zwei-Phasen-Test
        print("\n3. ERWEITERTE SUCH-MODI:")
        result = await test_two_phase(service, mine)
        mine_results['Zwei-Phasen'] = result
        
        # Abacus Test wenn verfügbar
        if 'Abacus Deep Agent' in test_configs:
            print("\n4. ABACUS DEEP AGENT:")
            for model_id in test_configs['Abacus Deep Agent']:
                result = await test_single_model(service, model_id, mine)
                mine_results['Abacus'] = result
        
        results[mine['name']] = mine_results
    
    # Zusammenfassung
    print("\n" + "="*80)
    print("ZUSAMMENFASSUNG")
    print("="*80)
    
    # Beste Ergebnisse pro Mine
    print("\nBESTE DATENABDECKUNG PRO MINE:")
    for mine_name, mine_results in results.items():
        best_coverage = 0
        best_method = ""
        
        for method, result in mine_results.items():
            if result.get('success'):
                coverage = result.get('coverage', result.get('best_coverage', 0))
                if coverage > best_coverage:
                    best_coverage = coverage
                    best_method = method
        
        print(f"  {mine_name}: {best_coverage:.0f}% ({best_method})")
    
    # Platzhalter-Warnung
    print("\nPLATZHALTER-PRÜFUNG:")
    placeholder_count = 0
    for mine_name, mine_results in results.items():
        for method, result in mine_results.items():
            if result.get('placeholder_found'):
                placeholder_count += 1
                print(f"  ⚠️ {mine_name} - {method}: Platzhalter gefunden!")
    
    if placeholder_count == 0:
        print("  ✅ Keine Platzhalter gefunden!")
    
    # Performance-Statistiken
    print("\nPERFORMANCE-STATISTIKEN:")
    total_duration = 0
    test_count = 0
    
    for mine_results in results.values():
        for result in mine_results.values():
            if result.get('duration'):
                total_duration += result['duration']
                test_count += 1
    
    if test_count > 0:
        avg_duration = total_duration / test_count
        print(f"  Durchschnittliche Suchzeit: {avg_duration:.1f}s")
        print(f"  Gesamtdauer aller Tests: {total_duration:.1f}s")
    
    print("\n" + "="*80)
    print("TEST ABGESCHLOSSEN")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())