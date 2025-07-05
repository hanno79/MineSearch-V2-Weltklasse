"""
Author: rahn
Datum: 05.07.2025
Version: 1.0
Beschreibung: Detaillierter Test aller Provider mit Fokus auf Tavily/Exa Debugging
"""

import asyncio
import logging
import json
import csv
from datetime import datetime
from typing import Dict, List, Any, Optional
import sys
import os

# Füge Backend-Verzeichnis zum Python-Pfad hinzu
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from search_service_multi import MultiProviderSearchService
from config import config

# ÄNDERUNG 05.07.2025: Detailliertes Logging für Debugging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'test_run_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Setze spezifisches Debug-Logging für Tavily und Exa
logging.getLogger('providers.tavily_provider').setLevel(logging.DEBUG)
logging.getLogger('providers.exa_provider').setLevel(logging.DEBUG)


class ProviderTester:
    """Umfassender Tester für alle Provider"""
    
    def __init__(self):
        self.service = MultiProviderSearchService()
        self.results = {}
        self.test_mines = []
        
    def load_test_mines(self, csv_path: str):
        """Lade Test-Minen aus CSV"""
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            self.test_mines = list(reader)
        logger.info(f"Geladen: {len(self.test_mines)} Test-Minen")
        
    async def test_provider_health(self):
        """Teste Health-Status aller Provider"""
        print("\n" + "="*80)
        print("PROVIDER HEALTH CHECK")
        print("="*80)
        
        health_status = await self.service.registry.health_check()
        
        for provider, status in health_status.items():
            status_symbol = "✅" if status else "❌"
            print(f"{provider}: {status_symbol}")
            
        return health_status
        
    async def test_single_provider(self, provider_name: str, model_id: str, mine: Dict) -> Dict:
        """Teste einen einzelnen Provider mit detailliertem Logging"""
        
        logger.info(f"\n{'='*60}")
        logger.info(f"TESTE: {model_id} für {mine['Name']}")
        logger.info(f"{'='*60}")
        
        start_time = datetime.now()
        
        try:
            # Detaillierte Parameter
            search_params = {
                'model_id': model_id,
                'mine_name': mine['Name'],
                'country': mine['Country'],
                'commodity': mine['Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)'],
                'region': mine['Region']
            }
            
            logger.debug(f"Search Parameters: {json.dumps(search_params, indent=2)}")
            
            # Führe Suche durch
            result = await self.service.search_with_model(**search_params)
            
            duration = (datetime.now() - start_time).total_seconds()
            
            if result.get('success'):
                data = result.get('data', {})
                sources = result.get('sources', [])
                
                # Analysiere Ergebnisse
                filled_fields = sum(1 for v in data.values() if v and v != '-')
                total_fields = len(data)
                coverage = (filled_fields / total_fields * 100) if total_fields > 0 else 0
                
                # Prüfe kritische Felder
                critical_fields = ['Restaurationskosten', 'x-Koordinate', 'y-Koordinate', 
                                 'Eigentümer', 'Betreiber']
                critical_found = sum(1 for field in critical_fields if data.get(field))
                
                # Log detaillierte Ergebnisse
                logger.info(f"✅ ERFOLG: {coverage:.1f}% Abdeckung, {len(sources)} Quellen")
                logger.info(f"Kritische Felder: {critical_found}/{len(critical_fields)}")
                
                # Debug: Zeige gefundene Daten
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug("Gefundene Daten:")
                    for field, value in data.items():
                        if value and value != '-':
                            logger.debug(f"  {field}: {value}")
                
                return {
                    'success': True,
                    'provider': provider_name,
                    'model': model_id,
                    'coverage': coverage,
                    'critical_found': critical_found,
                    'sources_count': len(sources),
                    'duration': duration,
                    'data': data,
                    'sources': sources
                }
                
            else:
                error = result.get('error', 'Unbekannter Fehler')
                logger.error(f"❌ FEHLER: {error}")
                
                # Spezielle Behandlung für Tavily/Exa Fehler
                if provider_name in ['tavily', 'exa']:
                    logger.error(f"DEBUGGING {provider_name.upper()}:")
                    logger.error(f"Full Error Response: {json.dumps(result, indent=2)}")
                    
                    # Prüfe Provider-spezifische Probleme
                    provider = self.service.registry.get_provider(provider_name)
                    if provider:
                        # Validiere Konfiguration
                        is_valid = provider.validate_config()
                        logger.error(f"Config Valid: {is_valid}")
                        
                        # Prüfe API-Key
                        has_key = bool(provider.api_key)
                        logger.error(f"API Key Present: {has_key}")
                
                return {
                    'success': False,
                    'provider': provider_name,
                    'model': model_id,
                    'error': error,
                    'duration': duration
                }
                
        except Exception as e:
            logger.exception(f"Exception bei {model_id}: {str(e)}")
            return {
                'success': False,
                'provider': provider_name,
                'model': model_id,
                'error': str(e),
                'duration': (datetime.now() - start_time).total_seconds()
            }
    
    async def test_all_providers_for_mine(self, mine: Dict) -> Dict:
        """Teste alle Provider für eine Mine"""
        mine_results = {}
        
        print(f"\n{'='*80}")
        print(f"MINE: {mine['Name']} ({mine['Region']}, {mine['Country']})")
        print(f"Rohstoff: {mine['Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)']}")
        print("="*80)
        
        # Hole alle verfügbaren Modelle
        all_models = self.service.registry.get_all_models()
        
        # Teste jeden Provider
        for model_id, model_config in all_models.items():
            provider_name = model_config.provider
            
            print(f"\nTeste {model_id}... ", end='', flush=True)
            
            result = await self.test_single_provider(provider_name, model_id, mine)
            mine_results[model_id] = result
            
            if result['success']:
                print(f"✅ {result['coverage']:.0f}% | {result['sources_count']} Quellen | {result['duration']:.1f}s")
            else:
                print(f"❌ {result['error']}")
                
        return mine_results
    
    async def test_multi_model_combinations(self, mine: Dict) -> Dict:
        """Teste Multi-Model Kombinationen"""
        print(f"\n{'='*60}")
        print("MULTI-MODEL KOMBINATIONEN")
        print("="*60)
        
        combinations = {
            '2er_best': ['perplexity:sonar-pro', 'tavily:search'],
            '2er_reasoning': ['perplexity:sonar-reasoning-pro', 'openrouter:deepseek-free'],
            '3er_comprehensive': ['perplexity:sonar-pro', 'tavily:search', 'exa:neural-search'],
            'all_available': list(self.service.registry.get_all_models().keys())[:4]
        }
        
        results = {}
        
        for combo_name, model_ids in combinations.items():
            # Filtere nur verfügbare Modelle
            available_models = [m for m in model_ids if self.service.registry.is_model_available(m)]
            
            if not available_models:
                continue
                
            print(f"\n{combo_name} ({len(available_models)} Modelle): ", end='', flush=True)
            
            start_time = datetime.now()
            
            try:
                result = await self.service.search_with_multiple_models(
                    model_ids=available_models,
                    mine_name=mine['Name'],
                    country=mine['Country'],
                    commodity=mine['Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)'],
                    region=mine['Region']
                )
                
                duration = (datetime.now() - start_time).total_seconds()
                
                if result.get('success'):
                    # Analysiere kombinierte Ergebnisse
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
                    
                    results[combo_name] = {
                        'success': True,
                        'best_coverage': best_coverage,
                        'total_sources': total_sources,
                        'duration': duration,
                        'models_used': available_models
                    }
                else:
                    print(f"❌ Fehler")
                    results[combo_name] = {'success': False}
                    
            except Exception as e:
                print(f"❌ Exception: {str(e)}")
                results[combo_name] = {'success': False, 'error': str(e)}
                
        return results
    
    async def analyze_search_depth(self, mine: Dict, model_id: str) -> Dict:
        """Analysiere Suchtiefe für ein spezifisches Modell"""
        logger.info(f"\nAnalysiere Suchtiefe für {model_id}")
        
        result = await self.service.search_with_model(
            model_id=model_id,
            mine_name=mine['Name'],
            country=mine['Country'],
            commodity=mine['Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)'],
            region=mine['Region']
        )
        
        if not result.get('success'):
            return {'success': False}
            
        sources = result.get('sources', [])
        
        # Analysiere Quellen
        source_types = {
            'official': 0,  # Regierungsseiten
            'company': 0,   # Unternehmensseiten
            'news': 0,      # Nachrichtenseiten
            'technical': 0, # Technische Berichte
            'other': 0      # Sonstige
        }
        
        domains_accessed = set()
        pdf_count = 0
        subpage_count = 0
        
        for source in sources:
            url = source.get('value', '')
            domains_accessed.add(url.split('/')[2] if url.startswith('http') else '')
            
            # Kategorisiere Quelle
            if any(gov in url for gov in ['.gov', '.gc.ca', '.gouv']):
                source_types['official'] += 1
            elif any(corp in url for corp in ['mining.com', 'company', 'corp']):
                source_types['company'] += 1
            elif any(news in url for news in ['news', 'article', 'press']):
                source_types['news'] += 1
            elif '.pdf' in url:
                source_types['technical'] += 1
                pdf_count += 1
            else:
                source_types['other'] += 1
                
            # Prüfe ob Unterseite
            if url.count('/') > 3:
                subpage_count += 1
        
        return {
            'success': True,
            'total_sources': len(sources),
            'unique_domains': len(domains_accessed),
            'source_types': source_types,
            'pdf_count': pdf_count,
            'subpage_count': subpage_count,
            'depth_score': (pdf_count * 2 + subpage_count) / max(len(sources), 1) * 100
        }
    
    async def run_comprehensive_test(self):
        """Führe umfassenden Test durch"""
        
        print("\n" + "="*80)
        print("MINESEARCH V2 - UMFASSENDER PROVIDER TEST")
        print("="*80)
        print(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Test-Minen: {len(self.test_mines)}")
        
        # 1. Health Check
        health_status = await self.test_provider_health()
        
        # 2. Teste jede Mine
        all_results = {}
        
        for i, mine in enumerate(self.test_mines[:5]):  # Erste 5 Minen für Test
            print(f"\n\n[{i+1}/{5}] Teste Mine: {mine['Name']}")
            
            # Einzelmodell-Tests
            mine_results = await self.test_all_providers_for_mine(mine)
            
            # Multi-Model Tests
            multi_results = await self.test_multi_model_combinations(mine)
            
            # Suchtiefe für beste Modelle
            depth_analysis = {}
            best_models = ['perplexity:sonar-pro', 'tavily:search', 'exa:neural-search']
            
            for model_id in best_models:
                if self.service.registry.is_model_available(model_id):
                    depth_result = await self.analyze_search_depth(mine, model_id)
                    depth_analysis[model_id] = depth_result
            
            all_results[mine['Name']] = {
                'single_models': mine_results,
                'multi_models': multi_results,
                'depth_analysis': depth_analysis
            }
        
        # 3. Erstelle Zusammenfassung
        self.create_summary(all_results, health_status)
        
        # 4. Speichere detaillierte Ergebnisse
        self.save_results(all_results)
        
    def create_summary(self, results: Dict, health_status: Dict):
        """Erstelle Zusammenfassung der Testergebnisse"""
        
        print("\n\n" + "="*80)
        print("ZUSAMMENFASSUNG")
        print("="*80)
        
        # Provider-Status
        print("\n1. PROVIDER-STATUS:")
        for provider, status in health_status.items():
            print(f"   {provider}: {'✅ OK' if status else '❌ FEHLER'}")
        
        # Beste Einzelmodelle
        print("\n2. BESTE EINZELMODELLE:")
        model_stats = {}
        
        for mine_results in results.values():
            for model_id, result in mine_results['single_models'].items():
                if result['success']:
                    if model_id not in model_stats:
                        model_stats[model_id] = {
                            'total_coverage': 0,
                            'success_count': 0,
                            'avg_duration': 0
                        }
                    model_stats[model_id]['total_coverage'] += result['coverage']
                    model_stats[model_id]['success_count'] += 1
                    model_stats[model_id]['avg_duration'] += result['duration']
        
        # Sortiere nach durchschnittlicher Abdeckung
        for model_id, stats in sorted(model_stats.items(), 
                                     key=lambda x: x[1]['total_coverage'] / max(x[1]['success_count'], 1), 
                                     reverse=True)[:5]:
            avg_coverage = stats['total_coverage'] / stats['success_count']
            avg_duration = stats['avg_duration'] / stats['success_count']
            print(f"   {model_id}: {avg_coverage:.1f}% Abdeckung, {avg_duration:.1f}s")
        
        # Tavily/Exa Spezialanalyse
        print("\n3. TAVILY/EXA ANALYSE:")
        tavily_success = sum(1 for mine in results.values() 
                           for m, r in mine['single_models'].items() 
                           if 'tavily' in m and r['success'])
        exa_success = sum(1 for mine in results.values() 
                         for m, r in mine['single_models'].items() 
                         if 'exa' in m and r['success'])
        
        total_tests = len(results)
        print(f"   Tavily Erfolgsrate: {tavily_success}/{total_tests*2} Tests")
        print(f"   Exa Erfolgsrate: {exa_success}/{total_tests*2} Tests")
        
        # Empfehlungen
        print("\n4. EMPFEHLUNGEN:")
        print("   - Beste Einzelmodell-Konfiguration: perplexity:sonar-pro")
        print("   - Beste Multi-Model-Konfiguration: perplexity + tavily")
        print("   - Für Deep Research: perplexity:sonar-deep-research")
        
    def save_results(self, results: Dict):
        """Speichere detaillierte Ergebnisse"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_results_detailed_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
            
        print(f"\n\nDetaillierte Ergebnisse gespeichert in: {filename}")


async def main():
    """Hauptfunktion"""
    
    # Erstelle Tester
    tester = ProviderTester()
    
    # Lade Test-Minen
    tester.load_test_mines('test_mines_quebec.csv')
    
    # Führe Tests durch
    await tester.run_comprehensive_test()


if __name__ == "__main__":
    asyncio.run(main())