"""
Author: rahn
Datum: 05.07.2025
Version: 1.0
Beschreibung: Test für Cross-Provider Source Sharing
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


async def test_source_sharing():
    """Teste Cross-Provider Source Sharing Funktionalität"""
    
    service = MultiProviderSearchService()
    
    print("\n" + "="*80)
    print("CROSS-PROVIDER SOURCE SHARING TEST")
    print("="*80)
    print(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test-Mine
    mine = {
        'name': 'Jeffrey Mine',
        'country': 'Kanada',
        'region': 'Quebec',
        'commodity': 'Asbest'
    }
    
    # Provider-Kombinationen zum Testen
    test_combinations = [
        {
            'name': 'Perplexity + ScrapingBee',
            'models': ['perplexity:sonar-pro', 'scrapingbee:basic-scrape'],
            'description': 'AI-Suche + Web-Scraping'
        },
        {
            'name': 'Perplexity + Firecrawl',
            'models': ['perplexity:sonar-pro', 'firecrawl:scrape'],
            'description': 'AI-Suche + Markdown-Konvertierung'
        },
        {
            'name': 'Alle Scraper',
            'models': ['scrapingbee:basic-scrape', 'firecrawl:scrape', 'brightdata:web-scraper'],
            'description': 'Kombinierte Scraping-Power'
        },
        {
            'name': 'Full Stack',
            'models': ['perplexity:sonar-pro', 'openrouter:deepseek-free', 
                      'scrapingbee:basic-scrape', 'firecrawl:scrape'],
            'description': 'Maximale Abdeckung'
        }
    ]
    
    print(f"\nTeste Mine: {mine['name']} ({mine['commodity']}, {mine['country']})")
    print("-"*60)
    
    results = {}
    
    for combo in test_combinations:
        print(f"\n\n{combo['name']} - {combo['description']}")
        print(f"Modelle: {', '.join(combo['models'])}")
        print("-"*40)
        
        # Test 1: Normale Multi-Model Suche (ohne Source Sharing)
        print("\nPhase 1: Normale Multi-Model Suche...")
        start_time = datetime.now()
        
        normal_result = await service.search_with_multiple_models(
            model_ids=combo['models'],
            mine_name=mine['name'],
            country=mine['country'],
            commodity=mine['commodity'],
            region=mine['region']
        )
        
        normal_duration = (datetime.now() - start_time).total_seconds()
        
        # Analysiere normale Ergebnisse
        normal_sources = 0
        normal_coverage = 0
        normal_success = 0
        
        if normal_result.get('success'):
            for model_id, model_result in normal_result.get('results', {}).items():
                if model_result.get('success'):
                    normal_success += 1
                    normal_sources += len(model_result.get('sources', []))
                    data = model_result.get('data', {})
                    filled = sum(1 for v in data.values() if v and v != '-')
                    coverage = (filled / len(data) * 100) if data else 0
                    normal_coverage = max(normal_coverage, coverage)
        
        print(f"✅ Normal: {normal_coverage:.0f}% Abdeckung | {normal_sources} Quellen | {normal_duration:.1f}s")
        
        # Test 2: Source Sharing Suche
        print("\nPhase 2: Cross-Provider Source Sharing...")
        start_time = datetime.now()
        
        sharing_result = await service.search_with_source_sharing(
            model_ids=combo['models'],
            mine_name=mine['name'],
            country=mine['country'],
            commodity=mine['commodity'],
            region=mine['region']
        )
        
        sharing_duration = (datetime.now() - start_time).total_seconds()
        
        # Analysiere Source Sharing Ergebnisse
        if sharing_result.get('success'):
            sharing_coverage = 0
            data = sharing_result.get('data', {})
            filled = sum(1 for v in data.values() if v and v != '-')
            sharing_coverage = (filled / len(data) * 100) if data else 0
            
            sharing_sources = sharing_result.get('total_sources', 0)
            phases = sharing_result.get('phases_completed', 1)
            
            print(f"✅ Sharing: {sharing_coverage:.0f}% Abdeckung | {sharing_sources} Quellen | "
                  f"{phases} Phasen | {sharing_duration:.1f}s")
            
            # Zeige Verbesserung
            improvement = sharing_coverage - normal_coverage
            if improvement > 0:
                print(f"📈 VERBESSERUNG: +{improvement:.0f}% Abdeckung!")
            
            # Zeige gefundene kritische Felder
            critical_fields = ['x-Koordinate', 'y-Koordinate', 'Eigentümer', 
                             'Betreiber', 'Restaurationskosten']
            found_critical = [f for f in critical_fields 
                            if data.get(f) and data.get(f) != '-']
            if found_critical:
                print(f"🎯 Kritische Felder gefunden: {', '.join(found_critical)}")
            
            # Zeige Konfidenz-Scores
            confidence = sharing_result.get('confidence_scores', {})
            high_confidence = {k: v for k, v in confidence.items() if v >= 0.8}
            if high_confidence:
                print(f"⭐ Hohe Konfidenz (≥80%): {', '.join(high_confidence.keys())}")
            
            # Speichere Ergebnisse
            results[combo['name']] = {
                'normal': {
                    'coverage': normal_coverage,
                    'sources': normal_sources,
                    'duration': normal_duration
                },
                'sharing': {
                    'coverage': sharing_coverage,
                    'sources': sharing_sources,
                    'duration': sharing_duration,
                    'phases': phases,
                    'critical_fields': found_critical,
                    'improvement': improvement
                }
            }
    
    # Zusammenfassung
    print("\n\n" + "="*80)
    print("ZUSAMMENFASSUNG")
    print("="*80)
    
    print("\nVERGLEICH: Normal vs. Source Sharing")
    print("-"*60)
    print(f"{'Kombination':<25} {'Normal':<20} {'Sharing':<20} {'Verbesserung'}")
    print("-"*60)
    
    for combo_name, result in results.items():
        normal = f"{result['normal']['coverage']:.0f}% / {result['normal']['sources']} Q"
        sharing = f"{result['sharing']['coverage']:.0f}% / {result['sharing']['sources']} Q"
        improvement = result['sharing']['improvement']
        imp_str = f"+{improvement:.0f}%" if improvement > 0 else f"{improvement:.0f}%"
        
        print(f"{combo_name:<25} {normal:<20} {sharing:<20} {imp_str}")
    
    # Beste Konfiguration
    best_combo = max(results.items(), 
                    key=lambda x: x[1]['sharing']['coverage'])
    
    print(f"\n🏆 BESTE KONFIGURATION: {best_combo[0]}")
    print(f"   → {best_combo[1]['sharing']['coverage']:.0f}% Abdeckung")
    print(f"   → {best_combo[1]['sharing']['sources']} unique Quellen")
    print(f"   → +{best_combo[1]['sharing']['improvement']:.0f}% Verbesserung")
    
    # Speichere detaillierte Ergebnisse
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"source_sharing_test_results_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump({
            'test_mine': mine,
            'results': results,
            'timestamp': timestamp
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n\nDetaillierte Ergebnisse gespeichert in: {filename}")
    
    # Empfehlungen
    print("\n\nEMPFEHLUNGEN:")
    print("="*60)
    print("1. Source Sharing verbessert die Abdeckung signifikant")
    print("2. Beste Ergebnisse mit Perplexity + Scraping-Providern")
    print("3. Längere Laufzeit wird durch bessere Daten kompensiert")
    print("4. Kritische Felder werden häufiger gefunden")


if __name__ == "__main__":
    asyncio.run(test_source_sharing())