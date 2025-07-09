"""
Author: rahn
Datum: 09.07.2025
Version: 1.0
Beschreibung: Test der Scraping-Provider (Firecrawl, ScrapingBee, Brightdata)
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any
import json

from model_benchmark_service import ModelBenchmarkService
from database import db_manager, ModelStatistics, ModelSummary, Source
from sqlalchemy import func

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test-Minen
TEST_MINES = [
    {'name': 'Éléonore', 'country': 'Canada', 'region': 'Quebec', 'commodity': 'Gold'},
    {'name': 'Niobec', 'country': 'Canada', 'region': 'Quebec', 'commodity': 'Niobium'},
    {'name': 'LaRonde', 'country': 'Canada', 'region': 'Quebec', 'commodity': 'Gold'}
]

# Scraping-Provider zu testen
SCRAPING_PROVIDERS = {
    'firecrawl': ['scrape', 'crawl', 'extract'],
    'scrapingbee': ['basic-scrape', 'js-render', 'ai-extract'],
    'brightdata': ['web-scraper', 'browser-api', 'serp']
}


class ScrapingProviderTester:
    def __init__(self):
        self.benchmark_service = ModelBenchmarkService()
        self.results = {}
        
    async def test_model_with_mine(self, provider: str, model: str, mine_data: Dict) -> Dict:
        """Teste ein Modell mit einer Mine"""
        model_id = f"{provider}:{model}"
        
        logger.info(f"\n{'='*50}")
        logger.info(f"Teste {model_id} mit {mine_data['name']}")
        logger.info(f"{'='*50}")
        
        try:
            # Führe Benchmark durch
            result = await asyncio.wait_for(
                self.benchmark_service.benchmark_model(
                    model_id=model_id,
                    mine_data=mine_data,
                    runs=5
                ),
                timeout=600  # 10 Minuten Timeout
            )
            
            # Hole Statistiken aus DB
            with db_manager.get_session() as session:
                summary = session.query(ModelSummary).filter_by(model_id=model_id).first()
                
                if summary:
                    logger.info(f"✅ {model_id} Ergebnisse:")
                    logger.info(f"   - Tests: {summary.total_tests}")
                    logger.info(f"   - Erfolgsrate: {summary.success_rate:.0%}")
                    logger.info(f"   - Ø Felder: {summary.avg_fields_found:.1f}")
                    logger.info(f"   - Konsistenz: {summary.overall_consistency:.2f}")
                    logger.info(f"   - Ø Zeit: {summary.avg_response_time_ms:.0f}ms")
            
            return {
                'success': True,
                'result': result,
                'timestamp': datetime.now().isoformat()
            }
            
        except asyncio.TimeoutError:
            logger.error(f"❌ Timeout bei {model_id}")
            return {
                'success': False,
                'error': 'Timeout nach 10 Minuten',
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"❌ Fehler bei {model_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def test_provider(self, provider: str, models: List[str]) -> Dict:
        """Teste einen Provider mit allen seinen Modellen"""
        logger.info(f"\n{'#'*60}")
        logger.info(f"# Teste Scraping-Provider: {provider}")
        logger.info(f"{'#'*60}")
        
        provider_results = {}
        
        for model in models:
            model_results = {}
            
            # Teste mit allen 3 Minen
            for mine_data in TEST_MINES:
                result = await self.test_model_with_mine(provider, model, mine_data)
                model_results[mine_data['name']] = result
                
                # Kurze Pause zwischen Tests
                await asyncio.sleep(2)
            
            provider_results[model] = model_results
        
        return provider_results
    
    async def run_all_tests(self):
        """Führe alle Scraping-Provider Tests durch"""
        logger.info("=== STARTE SCRAPING-PROVIDER TESTS ===")
        logger.info(f"Provider: {', '.join(SCRAPING_PROVIDERS.keys())}")
        logger.info(f"Minen: {', '.join([m['name'] for m in TEST_MINES])}")
        
        # Initiale Statistiken
        with db_manager.get_session() as session:
            initial_sources = session.query(func.count(Source.id)).scalar()
            initial_tests = session.query(func.count(ModelStatistics.id)).scalar()
            logger.info(f"\nStart-Statistiken:")
            logger.info(f"  - Quellen: {initial_sources}")
            logger.info(f"  - Tests: {initial_tests}")
        
        # Teste alle Provider
        for provider, models in SCRAPING_PROVIDERS.items():
            self.results[provider] = await self.test_provider(provider, models)
        
        # Speichere Ergebnisse
        with open('scraping_provider_results.json', 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False, default=str)
        
        # Finale Statistiken
        with db_manager.get_session() as session:
            final_sources = session.query(func.count(Source.id)).scalar()
            final_tests = session.query(func.count(ModelStatistics.id)).scalar()
            
            logger.info(f"\n{'='*60}")
            logger.info("FINALE STATISTIKEN:")
            logger.info(f"  - Quellen: {initial_sources} → {final_sources} (+{final_sources - initial_sources})")
            logger.info(f"  - Tests: {initial_tests} → {final_tests} (+{final_tests - initial_tests})")
            
            # Zeige alle Scraping-Provider Ergebnisse
            scraping_summaries = session.query(
                ModelSummary
            ).filter(
                ModelSummary.model_id.like('firecrawl:%') |
                ModelSummary.model_id.like('scrapingbee:%') |
                ModelSummary.model_id.like('brightdata:%')
            ).all()
            
            logger.info("\nSCRAPING-PROVIDER ÜBERSICHT:")
            for summary in scraping_summaries:
                logger.info(f"  {summary.model_id}:")
                logger.info(f"    - Tests: {summary.total_tests}")
                logger.info(f"    - Erfolg: {summary.success_rate:.0%}")
                logger.info(f"    - Felder: {summary.avg_fields_found:.1f}")
                logger.info(f"    - Konsistenz: {summary.overall_consistency:.2f}")
        
        return self.results


async def main():
    """Hauptfunktion"""
    tester = ScrapingProviderTester()
    
    # Führe Tests durch
    results = await tester.run_all_tests()
    
    # Zusammenfassung
    logger.info("\n✅ Scraping-Provider Tests abgeschlossen!")
    logger.info("Ergebnisse gespeichert in: scraping_provider_results.json")
    
    # Zeige Zusammenfassung
    total_tests = 0
    successful_tests = 0
    
    for provider, models in results.items():
        for model, mines in models.items():
            for mine, result in mines.items():
                total_tests += 1
                if result.get('success'):
                    successful_tests += 1
    
    logger.info(f"\nGESAMT-ZUSAMMENFASSUNG:")
    logger.info(f"  - Provider getestet: {len(results)}")
    logger.info(f"  - Tests durchgeführt: {total_tests}")
    logger.info(f"  - Erfolgreiche Tests: {successful_tests} ({successful_tests/total_tests*100:.0f}%)")


if __name__ == "__main__":
    asyncio.run(main())