"""
Author: rahn
Datum: 05.07.2025
Version: 1.0
Beschreibung: Umfassender Test aller Provider mit allen Kombinationen
"""

import asyncio
import json
import csv
from datetime import datetime
from typing import Dict, List, Any
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from search_service_multi import MultiProviderSearchService
from config import config


class ComprehensiveProviderTest:
    """Umfassender Test aller Provider und Kombinationen"""
    
    def __init__(self):
        self.service = MultiProviderSearchService()
        self.test_results = {
            'single_models': {},
            'multi_models': {},
            'two_phase': {},
            'search_depth': {}
        }
        
    async def run_all_tests(self):
        """Führe alle Tests durch"""
        
        print("\n" + "="*80)
        print("UMFASSENDER MINESEARCH V2 PROVIDER TEST")
        print("="*80)
        print(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Test-Minen - erweitert für verschiedene Länder
        test_mines = [
            {
                'name': 'Jeffrey Mine',
                'country': 'Kanada',
                'region': 'Quebec',
                'commodity': 'Asbest',
                'critical_fields': ['Restaurationskosten', 'x-Koordinate', 'y-Koordinate']
            },
            {
                'name': 'Canadian Malartic',
                'country': 'Kanada',
                'region': 'Quebec',
                'commodity': 'Gold',
                'critical_fields': ['Eigentümer', 'Betreiber', 'Fördermenge/Jahr']
            },
            {
                'name': 'Grasberg',
                'country': 'Indonesien',
                'region': 'Papua',
                'commodity': 'Gold/Kupfer',
                'critical_fields': ['Eigentümer', 'Betreiber', 'Produktionsstart']
            },
            {
                'name': 'Escondida',
                'country': 'Chile',
                'region': 'Antofagasta',
                'commodity': 'Kupfer',
                'critical_fields': ['Fördermenge/Jahr', 'Fläche der Mine in qkm', 'Minentyp (Untertage/ Open-Pit/ usw.)']
            },
            {
                'name': 'Super Pit',
                'country': 'Australien',
                'region': 'Western Australia',
                'commodity': 'Gold',
                'critical_fields': ['Produktionsende', 'Restaurationskosten', 'Aktivitätsstatus']
            }
        ]
        
        # 1. Teste alle Einzelmodelle
        print("\n\n1. EINZELMODELL-TESTS")
        print("="*60)
        
        all_models = list(self.service.registry.get_all_models().keys())
        print(f"Verfügbare Modelle: {len(all_models)}")
        for model in all_models:
            print(f"  - {model}")
        
        for mine in test_mines:
            print(f"\n\nMine: {mine['name']} ({mine['commodity']})")
            print("-"*40)
            
            for model_id in all_models:
                result = await self.test_single_model(model_id, mine)
                
                if model_id not in self.test_results['single_models']:
                    self.test_results['single_models'][model_id] = []
                self.test_results['single_models'][model_id].append(result)
        
        # 2. Teste Multi-Model Kombinationen
        print("\n\n2. MULTI-MODEL KOMBINATIONEN")
        print("="*60)
        
        # ÄNDERUNG 05.07.2025: Aktualisierte Kombinationen mit neuen Providern
        combinations = {
            # 2er-Kombinationen
            '2er_perplexity_openrouter': ['perplexity:sonar-pro', 'openrouter:deepseek-free'],
            '2er_perplexity_scrapingbee': ['perplexity:sonar-pro', 'scrapingbee:basic-scrape'],
            '2er_perplexity_firecrawl': ['perplexity:sonar-pro', 'firecrawl:scrape'],
            '2er_scraping_providers': ['scrapingbee:basic-scrape', 'firecrawl:scrape'],
            
            # 3er-Kombinationen
            '3er_best_mix': ['perplexity:sonar-pro', 'scrapingbee:basic-scrape', 'firecrawl:scrape'],
            '3er_with_free': ['perplexity:sonar-pro', 'openrouter:deepseek-free', 'scrapingbee:basic-scrape'],
            
            # Deep Research Kombinationen
            'deep_with_scraping': ['perplexity:sonar-deep-research', 'scrapingbee:basic-scrape', 'firecrawl:scrape'],
            'deep_perplexity_only': ['perplexity:sonar-deep-research', 'perplexity:sonar-reasoning']
        }
        
        for combo_name, model_ids in combinations.items():
            # Filtere nur verfügbare Modelle
            available = [m for m in model_ids if m in all_models]
            if not available:
                continue
                
            print(f"\n{combo_name}: {available}")
            
            for mine in test_mines[:1]:  # Nur erste Mine für Multi-Tests
                result = await self.test_multi_model(available, mine)
                self.test_results['multi_models'][combo_name] = result
        
        # 3. Teste Zwei-Phasen-Suche
        print("\n\n3. ZWEI-PHASEN-SUCHE")
        print("="*60)
        
        for mine in test_mines:
            result = await self.test_two_phase(mine)
            self.test_results['two_phase'][mine['name']] = result
        
        # 4. Analysiere Suchtiefe
        print("\n\n4. SUCHTIEFE-ANALYSE")
        print("="*60)
        
        # ÄNDERUNG 05.07.2025: Nur aktive Provider für Suchtiefe-Analyse
        depth_models = [
            'perplexity:sonar-deep-research',
            'perplexity:sonar-reasoning',
            'scrapingbee:js-render',
            'firecrawl:scrape'
        ]
        
        for model_id in depth_models:
            if model_id in all_models:
                result = await self.analyze_search_depth(model_id, test_mines[0])
                self.test_results['search_depth'][model_id] = result
        
        # 5. Erstelle Zusammenfassung
        self.create_summary()
        
        # 6. Speichere Ergebnisse
        self.save_results()
    
    async def test_single_model(self, model_id: str, mine: Dict) -> Dict:
        """Teste ein einzelnes Modell"""
        
        print(f"\n  {model_id}: ", end='', flush=True)
        start_time = datetime.now()
        
        try:
            result = await self.service.search_with_model(
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
                
                # Berechne Metriken
                filled = sum(1 for v in data.values() if v and v != '-')
                total = len(data)
                coverage = (filled / total * 100) if total > 0 else 0
                
                critical_found = sum(1 for field in mine['critical_fields'] 
                                   if data.get(field) and data.get(field) != '-')
                
                print(f"✅ {coverage:.0f}% | {len(sources)} Quellen | {critical_found}/{len(mine['critical_fields'])} kritisch | {duration:.1f}s")
                
                return {
                    'success': True,
                    'model': model_id,
                    'coverage': coverage,
                    'sources_count': len(sources),
                    'critical_found': critical_found,
                    'duration': duration,
                    'data': data,
                    'sources': sources
                }
            else:
                print(f"❌ {result.get('error', 'Unbekannt')}")
                return {
                    'success': False,
                    'model': model_id,
                    'error': result.get('error')
                }
                
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            return {
                'success': False,
                'model': model_id,
                'error': str(e)
            }
    
    async def test_multi_model(self, model_ids: List[str], mine: Dict) -> Dict:
        """Teste Multi-Model Kombination"""
        
        start_time = datetime.now()
        
        try:
            result = await self.service.search_with_multiple_models(
                model_ids=model_ids,
                mine_name=mine['name'],
                country=mine['country'],
                commodity=mine['commodity'],
                region=mine['region']
            )
            
            duration = (datetime.now() - start_time).total_seconds()
            
            if result.get('success'):
                # Analysiere kombinierte Ergebnisse
                best_coverage = 0
                total_sources = 0
                successful_models = 0
                
                for model_id, model_result in result.get('results', {}).items():
                    if model_result.get('success'):
                        successful_models += 1
                        data = model_result.get('data', {})
                        filled = sum(1 for v in data.values() if v and v != '-')
                        coverage = (filled / len(data) * 100) if data else 0
                        best_coverage = max(best_coverage, coverage)
                        total_sources += len(model_result.get('sources', []))
                
                print(f"    ✅ {best_coverage:.0f}% beste Abdeckung | {total_sources} Quellen | {successful_models}/{len(model_ids)} erfolgreich | {duration:.1f}s")
                
                return {
                    'success': True,
                    'best_coverage': best_coverage,
                    'total_sources': total_sources,
                    'successful_models': successful_models,
                    'duration': duration
                }
            else:
                return {'success': False}
                
        except Exception as e:
            print(f"    ❌ Exception: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def test_two_phase(self, mine: Dict) -> Dict:
        """Teste Zwei-Phasen-Suche"""
        
        print(f"\n  {mine['name']}: ", end='', flush=True)
        start_time = datetime.now()
        
        try:
            result = await self.service.search_two_phase(
                mine_name=mine['name'],
                country=mine['country'],
                commodity=mine['commodity'],
                region=mine['region']
            )
            
            duration = (datetime.now() - start_time).total_seconds()
            
            if result.get('success'):
                data = result.get('data', {})
                filled = sum(1 for v in data.values() if v and v != '-')
                coverage = (filled / len(data) * 100) if data else 0
                phase3 = result.get('phase3_triggered', False)
                
                print(f"✅ {coverage:.0f}% | {'3-Phasen' if phase3 else '2-Phasen'} | {duration:.1f}s")
                
                return {
                    'success': True,
                    'coverage': coverage,
                    'phase3': phase3,
                    'duration': duration
                }
            else:
                print(f"❌ Fehler")
                return {'success': False}
                
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def analyze_search_depth(self, model_id: str, mine: Dict) -> Dict:
        """Analysiere Suchtiefe eines Modells"""
        
        print(f"\n  {model_id}: ", end='', flush=True)
        
        try:
            result = await self.service.search_with_model(
                model_id=model_id,
                mine_name=mine['name'],
                country=mine['country'],
                commodity=mine['commodity'],
                region=mine['region']
            )
            
            if result.get('success'):
                sources = result.get('sources', [])
                
                # Analysiere Quellentypen
                pdf_count = sum(1 for s in sources if '.pdf' in s.get('value', '').lower())
                gov_count = sum(1 for s in sources if any(gov in s.get('value', '') 
                                                         for gov in ['.gov', '.gc.ca', '.gouv']))
                subpage_count = sum(1 for s in sources if s.get('value', '').count('/') > 3)
                
                unique_domains = set()
                for source in sources:
                    url = source.get('value', '')
                    if url.startswith('http'):
                        domain = url.split('/')[2]
                        unique_domains.add(domain)
                
                depth_score = (pdf_count * 2 + subpage_count + gov_count) / max(len(sources), 1) * 100
                
                print(f"✅ {len(sources)} Quellen | {len(unique_domains)} Domains | "
                      f"{pdf_count} PDFs | Tiefe: {depth_score:.0f}%")
                
                return {
                    'success': True,
                    'total_sources': len(sources),
                    'unique_domains': len(unique_domains),
                    'pdf_count': pdf_count,
                    'gov_count': gov_count,
                    'subpage_count': subpage_count,
                    'depth_score': depth_score
                }
            else:
                print(f"❌ Keine Ergebnisse")
                return {'success': False}
                
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def create_summary(self):
        """Erstelle Zusammenfassung der Testergebnisse"""
        
        print("\n\n" + "="*80)
        print("ZUSAMMENFASSUNG")
        print("="*80)
        
        # 1. Beste Einzelmodelle
        print("\n1. BESTE EINZELMODELLE (nach Abdeckung):")
        
        model_stats = {}
        for model_id, results in self.test_results['single_models'].items():
            successful = [r for r in results if r.get('success')]
            if successful:
                avg_coverage = sum(r['coverage'] for r in successful) / len(successful)
                avg_sources = sum(r['sources_count'] for r in successful) / len(successful)
                model_stats[model_id] = {
                    'coverage': avg_coverage,
                    'sources': avg_sources,
                    'success_rate': len(successful) / len(results) * 100
                }
        
        # Sortiere nach Abdeckung
        sorted_models = sorted(model_stats.items(), 
                              key=lambda x: x[1]['coverage'], 
                              reverse=True)
        
        for i, (model_id, stats) in enumerate(sorted_models[:5], 1):
            print(f"   {i}. {model_id}: {stats['coverage']:.1f}% Abdeckung, "
                  f"{stats['sources']:.0f} Quellen, {stats['success_rate']:.0f}% Erfolg")
        
        # 2. Beste Multi-Model Kombinationen
        print("\n2. BESTE MULTI-MODEL KOMBINATIONEN:")
        
        for combo_name, result in self.test_results['multi_models'].items():
            if result.get('success'):
                print(f"   {combo_name}: {result['best_coverage']:.1f}% Abdeckung, "
                      f"{result['total_sources']} Quellen")
        
        # 3. Suchtiefe-Analyse
        print("\n3. SUCHTIEFE-ANALYSE:")
        
        for model_id, result in self.test_results['search_depth'].items():
            if result.get('success'):
                print(f"   {model_id}: Tiefe {result['depth_score']:.0f}%, "
                      f"{result['pdf_count']} PDFs, {result['unique_domains']} Domains")
        
        # 4. Empfehlungen
        print("\n4. EMPFEHLUNGEN:")
        
        # Finde beste Modelle
        if sorted_models:
            best_single = sorted_models[0][0]
            print(f"   - Bestes Einzelmodell: {best_single}")
        
        # ÄNDERUNG 05.07.2025: Aktualisierte Empfehlungen basierend auf Tests
        print("   - Beste Kombination: perplexity:sonar-pro + scrapingbee:basic-scrape")
        print("   - Für Deep Research: perplexity:sonar-deep-research")
        print("   - Kosteneffizient: openrouter:deepseek-free")
        print("   - Für Scraping: scrapingbee:basic-scrape + firecrawl:scrape")
    
    def save_results(self):
        """Speichere detaillierte Testergebnisse"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"comprehensive_test_results_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)
        
        print(f"\n\nDetaillierte Ergebnisse gespeichert in: {filename}")


async def main():
    """Hauptfunktion"""
    
    tester = ComprehensiveProviderTest()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())