"""
Author: rahn
Datum: 09.07.2025
Version: 1.0
Beschreibung: Schneller Test der Scraping-Provider - Ein Modell pro Provider
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

# Test mit nur einer Mine
TEST_MINE = {'name': 'Éléonore', 'country': 'Canada', 'region': 'Quebec', 'commodity': 'Gold'}

# Ein Modell pro Scraping-Provider für schnellen Test
SCRAPING_MODELS = {
    'firecrawl:scrape': 'Firecrawl Basic Scraping',
    'scrapingbee:basic-scrape': 'ScrapingBee Basic Scraping',
    'brightdata:web-scraper': 'Brightdata Web Scraper'
}


class QuickScrapingTester:
    def __init__(self):
        self.benchmark_service = ModelBenchmarkService()
        self.results = {}
        
    async def test_model(self, model_id: str, description: str) -> Dict:
        """Teste ein Modell"""
        logger.info(f"\n{'='*60}")
        logger.info(f"Teste {description} ({model_id})")
        logger.info(f"{'='*60}")
        
        try:
            # Führe nur 2 Durchläufe für schnelleren Test
            result = await asyncio.wait_for(
                self.benchmark_service.benchmark_model(
                    model_id=model_id,
                    mine_data=TEST_MINE,
                    runs=2
                ),
                timeout=120  # 2 Minuten Timeout
            )
            
            # Hole Statistiken aus DB
            with db_manager.get_session() as session:
                summary = session.query(ModelSummary).filter_by(model_id=model_id).first()
                
                if summary:
                    logger.info(f"✅ {model_id} Ergebnisse:")
                    logger.info(f"   - Tests gesamt: {summary.total_tests}")
                    logger.info(f"   - Erfolgsrate: {summary.success_rate:.0%}")
                    logger.info(f"   - Ø Felder gefunden: {summary.avg_fields_found:.1f}")
                    logger.info(f"   - Konsistenz: {summary.overall_consistency:.2f}")
                    logger.info(f"   - Ø Response Zeit: {summary.avg_response_time_ms:.0f}ms")
                    
                    # Zeige letzte Statistiken
                    latest_stats = session.query(ModelStatistics).filter_by(
                        model_id=model_id
                    ).order_by(ModelStatistics.timestamp.desc()).limit(2).all()
                    
                    logger.info(f"\n   Letzte Tests:")
                    for stat in latest_stats:
                        logger.info(f"   - {stat.timestamp.strftime('%H:%M:%S')}: "
                                  f"{'✓' if stat.success else '✗'} "
                                  f"{stat.fields_found} Felder, "
                                  f"{stat.response_time_ms}ms")
            
            return {
                'success': True,
                'result': result,
                'timestamp': datetime.now().isoformat()
            }
            
        except asyncio.TimeoutError:
            logger.error(f"❌ Timeout bei {model_id}")
            return {
                'success': False,
                'error': 'Timeout nach 2 Minuten',
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"❌ Fehler bei {model_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def run_tests(self):
        """Führe alle Tests durch"""
        logger.info("=== STARTE SCHNELLTEST DER SCRAPING-PROVIDER ===")
        logger.info(f"Modelle: {len(SCRAPING_MODELS)}")
        logger.info(f"Test-Mine: {TEST_MINE['name']}")
        logger.info(f"Durchläufe pro Modell: 2")
        
        # Teste alle Modelle
        for model_id, description in SCRAPING_MODELS.items():
            self.results[model_id] = await self.test_model(model_id, description)
            # Kurze Pause zwischen Tests
            await asyncio.sleep(2)
        
        # Zeige Zusammenfassung
        logger.info(f"\n{'='*60}")
        logger.info("ZUSAMMENFASSUNG SCRAPING-PROVIDER:")
        logger.info(f"{'='*60}")
        
        with db_manager.get_session() as session:
            for model_id in SCRAPING_MODELS.keys():
                summary = session.query(ModelSummary).filter_by(model_id=model_id).first()
                if summary:
                    status = "✅ FUNKTIONIERT" if summary.success_rate > 0 else "❌ FEHLER"
                    logger.info(f"\n{model_id}: {status}")
                    logger.info(f"  - Erfolgsrate: {summary.success_rate:.0%}")
                    logger.info(f"  - Durchschnittliche Felder: {summary.avg_fields_found:.1f}")
                    logger.info(f"  - Durchschnittliche Zeit: {summary.avg_response_time_ms:.0f}ms")
                else:
                    logger.info(f"\n{model_id}: ❌ KEINE DATEN")
        
        # Speichere Ergebnisse
        with open('scraping_quick_test_results.json', 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False, default=str)
        
        return self.results


async def main():
    """Hauptfunktion"""
    tester = QuickScrapingTester()
    
    # Führe Tests durch
    results = await tester.run_tests()
    
    # Finale Zusammenfassung
    total_success = sum(1 for r in results.values() if r.get('success'))
    total_tests = len(results)
    
    logger.info(f"\n✅ Schnelltest abgeschlossen!")
    logger.info(f"Erfolgreiche Tests: {total_success}/{total_tests} ({total_success/total_tests*100:.0f}%)")
    logger.info("Ergebnisse gespeichert in: scraping_quick_test_results.json")


if __name__ == "__main__":
    asyncio.run(main())