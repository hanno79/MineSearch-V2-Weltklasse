"""
Author: rahn
Datum: 09.07.2025
Version: 1.0
Beschreibung: Test der OpenRouter Provider
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

# OpenRouter Modelle
OPENROUTER_MODELS = ['deepseek-free', 'deepseek-chat', 'deepseek-reasoner']


class OpenRouterTester:
    def __init__(self):
        self.benchmark_service = ModelBenchmarkService()
        self.results = {}
        
    async def test_model(self, model: str) -> Dict:
        """Teste ein OpenRouter Modell mit allen Minen"""
        model_id = f"openrouter:{model}"
        model_results = {}
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Teste {model_id}")
        logger.info(f"{'='*60}")
        
        for mine_data in TEST_MINES:
            logger.info(f"\nTeste {model_id} mit {mine_data['name']}...")
            
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
                
                # Hole Statistiken
                with db_manager.get_session() as session:
                    summary = session.query(ModelSummary).filter_by(model_id=model_id).first()
                    
                    if summary:
                        logger.info(f"✅ Ergebnisse für {mine_data['name']}:")
                        logger.info(f"   - Erfolgsrate: {result['success_rate']:.0%}")
                        logger.info(f"   - Ø Felder: {result['avg_fields_found']:.1f}")
                        logger.info(f"   - Konsistenz: {result['consistency_analysis']['overall_consistency']:.2f}")
                        logger.info(f"   - DB Tests gesamt: {summary.total_tests}")
                
                model_results[mine_data['name']] = {
                    'success': True,
                    'result': result,
                    'timestamp': datetime.now().isoformat()
                }
                
            except asyncio.TimeoutError:
                logger.error(f"❌ Timeout bei {model_id} - {mine_data['name']}")
                model_results[mine_data['name']] = {
                    'success': False,
                    'error': 'Timeout nach 10 Minuten',
                    'timestamp': datetime.now().isoformat()
                }
            except Exception as e:
                logger.error(f"❌ Fehler bei {model_id} - {mine_data['name']}: {str(e)}")
                model_results[mine_data['name']] = {
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
            
            # Pause zwischen Tests
            await asyncio.sleep(2)
        
        return model_results
    
    async def run_all_tests(self):
        """Teste alle OpenRouter Modelle"""
        logger.info("=== STARTE OPENROUTER TESTS ===")
        logger.info(f"Modelle: {', '.join(OPENROUTER_MODELS)}")
        logger.info(f"Minen: {', '.join([m['name'] for m in TEST_MINES])}")
        
        # Initiale Statistiken
        with db_manager.get_session() as session:
            initial_sources = session.query(func.count(Source.id)).scalar()
            initial_tests = session.query(func.count(ModelStatistics.id)).scalar()
            logger.info(f"\nStart-Statistiken:")
            logger.info(f"  - Quellen: {initial_sources}")
            logger.info(f"  - Tests: {initial_tests}")
        
        # Teste alle Modelle
        for model in OPENROUTER_MODELS:
            self.results[model] = await self.test_model(model)
        
        # Speichere Ergebnisse
        with open('openrouter_results.json', 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False, default=str)
        
        # Finale Statistiken und Zusammenfassung
        with db_manager.get_session() as session:
            final_sources = session.query(func.count(Source.id)).scalar()
            final_tests = session.query(func.count(ModelStatistics.id)).scalar()
            
            logger.info(f"\n{'='*60}")
            logger.info("FINALE STATISTIKEN:")
            logger.info(f"  - Quellen: {initial_sources} → {final_sources}")
            logger.info(f"  - Tests: {initial_tests} → {final_tests}")
            
            # OpenRouter Zusammenfassung
            openrouter_summaries = session.query(ModelSummary).filter(
                ModelSummary.model_id.like('openrouter:%')
            ).all()
            
            logger.info("\nOPENROUTER MODELL-ÜBERSICHT:")
            for summary in openrouter_summaries:
                logger.info(f"\n{summary.model_id}:")
                logger.info(f"  - Total Tests: {summary.total_tests}")
                logger.info(f"  - Erfolgsrate: {summary.success_rate:.0%}")
                logger.info(f"  - Daten-Erfolgsrate: {summary.data_success_rate:.0%}")
                logger.info(f"  - Ø Felder: {summary.avg_fields_found:.1f}")
                logger.info(f"  - Konsistenz: {summary.overall_consistency:.2f}")
                logger.info(f"  - Ø Zeit: {summary.avg_response_time_ms:.0f}ms")
        
        return self.results


async def main():
    """Hauptfunktion"""
    tester = OpenRouterTester()
    
    # Führe Tests durch
    results = await tester.run_all_tests()
    
    logger.info("\n✅ OpenRouter Tests abgeschlossen!")
    logger.info("Ergebnisse gespeichert in: openrouter_results.json")
    
    # Zeige Zusammenfassung
    total_tests = 0
    successful_tests = 0
    
    for model, mines in results.items():
        for mine, result in mines.items():
            total_tests += 1
            if result.get('success'):
                successful_tests += 1
    
    logger.info(f"\nGESAMT-ZUSAMMENFASSUNG:")
    logger.info(f"  - Modelle getestet: {len(results)}")
    logger.info(f"  - Tests durchgeführt: {total_tests}")
    logger.info(f"  - Erfolgreiche Tests: {successful_tests} ({successful_tests/total_tests*100:.0f}%)")


if __name__ == "__main__":
    asyncio.run(main())