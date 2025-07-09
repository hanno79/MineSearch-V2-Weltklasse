"""
Author: rahn
Datum: 09.07.2025
Version: 1.0
Beschreibung: Schneller Test der OpenRouter Provider
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

# Test-Mine (nur eine für schnellen Test)
TEST_MINE = {'name': 'Éléonore', 'country': 'Canada', 'region': 'Quebec', 'commodity': 'Gold'}

# OpenRouter Modelle
OPENROUTER_MODELS = ['deepseek-free', 'deepseek-chat', 'deepseek-reasoner']


class OpenRouterQuickTester:
    def __init__(self):
        self.benchmark_service = ModelBenchmarkService()
        self.results = {}
        
    async def test_model(self, model: str) -> Dict:
        """Teste ein OpenRouter Modell mit einer Mine"""
        model_id = f"openrouter:{model}"
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Teste {model_id}")
        logger.info(f"{'='*60}")
        
        try:
            # Führe nur 1 Benchmark durch für schnellen Test
            result = await asyncio.wait_for(
                self.benchmark_service.benchmark_model(
                    model_id=model_id,
                    mine_data=TEST_MINE,
                    runs=1  # Nur 1 Durchlauf
                ),
                timeout=120  # 2 Minuten Timeout
            )
            
            # Hole Statistiken
            with db_manager.get_session() as session:
                summary = session.query(ModelSummary).filter_by(model_id=model_id).first()
                
                if summary:
                    logger.info(f"✅ Ergebnisse für {TEST_MINE['name']}:")
                    logger.info(f"   - Erfolgsrate: {result['success_rate']:.0%}")
                    logger.info(f"   - Felder gefunden: {result['avg_fields_found']:.0f}")
                    logger.info(f"   - Response Zeit: {result['avg_response_time_ms']:.0f}ms")
                    logger.info(f"   - DB Tests gesamt: {summary.total_tests}")
            
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
    
    async def run_all_tests(self):
        """Teste alle OpenRouter Modelle"""
        logger.info("=== STARTE OPENROUTER SCHNELLTEST ===")
        logger.info(f"Modelle: {', '.join(OPENROUTER_MODELS)}")
        logger.info(f"Test-Mine: {TEST_MINE['name']}")
        
        # Teste alle Modelle
        for model in OPENROUTER_MODELS:
            self.results[model] = await self.test_model(model)
            await asyncio.sleep(1)  # Kurze Pause zwischen Tests
        
        # Zeige Zusammenfassung
        logger.info(f"\n{'='*60}")
        logger.info("ZUSAMMENFASSUNG:")
        
        for model, result in self.results.items():
            status = "✅ OK" if result['success'] else "❌ FEHLER"
            logger.info(f"\n{model}: {status}")
            if result['success']:
                r = result['result']
                logger.info(f"  - Felder: {r['avg_fields_found']:.0f}")
                logger.info(f"  - Zeit: {r['avg_response_time_ms']:.0f}ms")
            else:
                logger.info(f"  - Fehler: {result['error']}")
        
        # Speichere Ergebnisse
        with open('openrouter_quick_results.json', 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False, default=str)
        
        return self.results


async def main():
    """Hauptfunktion"""
    tester = OpenRouterQuickTester()
    
    # Führe Tests durch
    results = await tester.run_all_tests()
    
    logger.info("\n✅ OpenRouter Schnelltest abgeschlossen!")
    logger.info("Ergebnisse gespeichert in: openrouter_quick_results.json")
    
    # Zeige finale Statistik
    successful = sum(1 for r in results.values() if r['success'])
    total = len(results)
    
    logger.info(f"\nFINALE STATISTIK:")
    logger.info(f"  - Modelle getestet: {total}")
    logger.info(f"  - Erfolgreich: {successful}/{total} ({successful/total*100:.0f}%)")


if __name__ == "__main__":
    asyncio.run(main())