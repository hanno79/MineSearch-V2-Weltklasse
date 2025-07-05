"""
Author: rahn
Datum: 05.07.2025
Version: 1.0
Beschreibung: Vereinfachter Test für Cross-Provider Source Sharing
"""

import asyncio
import json
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from search_service_multi import MultiProviderSearchService


async def test_source_sharing_simple():
    """Vereinfachter Test des Source Sharing"""
    
    service = MultiProviderSearchService()
    
    print("\n" + "="*80)
    print("CROSS-PROVIDER SOURCE SHARING - EINFACHER TEST")
    print("="*80)
    
    # Test-Mine
    mine_name = "Canadian Malartic"
    country = "Kanada"
    region = "Quebec"
    commodity = "Gold"
    
    # Nur funktionierende Provider testen
    test_models = ['perplexity:sonar-pro', 'openrouter:deepseek-free']
    
    print(f"\nMine: {mine_name} ({commodity}, {country})")
    print(f"Provider: {', '.join(test_models)}")
    print("-"*60)
    
    # Test 1: Normale Multi-Model Suche
    print("\n1. NORMALE SUCHE (ohne Source Sharing):")
    start = datetime.now()
    
    normal_result = await service.search_with_multiple_models(
        model_ids=test_models,
        mine_name=mine_name,
        country=country,
        commodity=commodity,
        region=region
    )
    
    duration1 = (datetime.now() - start).total_seconds()
    
    # Analysiere normale Ergebnisse
    if normal_result.get('success'):
        total_sources = 0
        max_coverage = 0
        
        for model_id, result in normal_result.get('results', {}).items():
            if result.get('success'):
                sources = result.get('sources', [])
                data = result.get('data', {})
                filled = sum(1 for v in data.values() if v and v != '-')
                coverage = (filled / len(data) * 100) if data else 0
                
                print(f"   {model_id}: {coverage:.0f}% Abdeckung, {len(sources)} Quellen")
                total_sources += len(sources)
                max_coverage = max(max_coverage, coverage)
        
        print(f"\n   Gesamt: {max_coverage:.0f}% beste Abdeckung, {total_sources} Quellen, {duration1:.1f}s")
    
    # Test 2: Source Sharing Suche
    print("\n\n2. SOURCE SHARING SUCHE:")
    start = datetime.now()
    
    sharing_result = await service.search_with_source_sharing(
        model_ids=test_models,
        mine_name=mine_name,
        country=country,
        commodity=commodity,
        region=region
    )
    
    duration2 = (datetime.now() - start).total_seconds()
    
    # Analysiere Source Sharing Ergebnisse
    if sharing_result.get('success'):
        data = sharing_result.get('data', {})
        filled = sum(1 for v in data.values() if v and v != '-')
        coverage = (filled / len(data) * 100) if data else 0
        sources = sharing_result.get('total_sources', 0)
        phases = sharing_result.get('phases_completed', 0)
        
        print(f"   Abdeckung: {coverage:.0f}%")
        print(f"   Quellen: {sources} (dedupliziert)")
        print(f"   Phasen: {phases}")
        print(f"   Zeit: {duration2:.1f}s")
        
        # Zeige Statistiken
        stats = sharing_result.get('statistics', {})
        if stats:
            print(f"\n   Statistiken:")
            print(f"   - Phase 1: {stats.get('phase1_coverage', 'N/A')}")
            print(f"   - Phase 2: {stats.get('phase2_coverage', 'N/A')}")
            print(f"   - Verbesserung: {stats.get('coverage_improvement', '0%')}")
        
        # Zeige kritische Felder
        critical = ['x-Koordinate', 'y-Koordinate', 'Eigentümer', 'Betreiber']
        found = [f for f in critical if data.get(f) and data.get(f) != '-']
        if found:
            print(f"\n   Kritische Felder gefunden: {', '.join(found)}")
        
        # Zeige Konfidenz
        confidence = sharing_result.get('confidence_scores', {})
        high_conf = {k: f"{v:.0%}" for k, v in confidence.items() if v >= 0.8}
        if high_conf:
            print(f"\n   Hohe Konfidenz (≥80%):")
            for field, conf in high_conf.items():
                print(f"   - {field}: {conf}")
    
    # Vergleich
    print("\n\n" + "="*60)
    print("VERGLEICH:")
    print("="*60)
    
    if normal_result.get('success') and sharing_result.get('success'):
        normal_cov = max_coverage
        sharing_cov = coverage
        improvement = sharing_cov - normal_cov
        
        print(f"Normal:        {normal_cov:.0f}% Abdeckung in {duration1:.1f}s")
        print(f"Source Sharing: {sharing_cov:.0f}% Abdeckung in {duration2:.1f}s")
        print(f"Verbesserung:  {improvement:+.0f}%")
        
        if improvement > 0:
            print("\n✅ Source Sharing verbessert die Ergebnisse!")
        else:
            print("\n⚠️  Keine signifikante Verbesserung durch Source Sharing")
    
    # Speichere Ergebnisse
    results = {
        'mine': {
            'name': mine_name,
            'country': country,
            'commodity': commodity
        },
        'normal': {
            'coverage': max_coverage if 'max_coverage' in locals() else 0,
            'sources': total_sources if 'total_sources' in locals() else 0,
            'duration': duration1
        },
        'sharing': {
            'coverage': coverage if 'coverage' in locals() else 0,
            'sources': sources if 'sources' in locals() else 0,
            'duration': duration2,
            'data': data if 'data' in locals() else {}
        }
    }
    
    filename = f"source_sharing_simple_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n\nErgebnisse gespeichert in: {filename}")


if __name__ == "__main__":
    asyncio.run(test_source_sharing_simple())