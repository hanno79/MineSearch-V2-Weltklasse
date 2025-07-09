"""
Author: rahn
Datum: 09.07.2025
Version: 1.0
Beschreibung: Test der verbleibenden Grok-Modelle (grok-3-mini und grok-3-fast)
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import json
import os

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

# Nur die verbleibenden Grok-Modelle
GROK_MODELS_TO_TEST = ['grok-3-mini', 'grok-3-fast']


class GrokRemainingTester:
    def __init__(self):
        self.benchmark_service = ModelBenchmarkService()
        self.results = {}
        
    def save_results(self):
        """Speichere Ergebnisse"""
        with open('grok_remaining_results.json', 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False, default=str)
    
    async def test_single_model(self, model: str, mine_data: Dict) -> Optional[Dict]:
        """Teste ein einzelnes Modell"""
        model_id = f"grok:{model}"
        
        logger.info(f"\nTeste {model_id} mit {mine_data['name']}...")
        
        try:
            # Timeout für langsame Provider
            result = await asyncio.wait_for(
                self.benchmark_service.benchmark_model(
                    model_id=model_id,
                    mine_data=mine_data,
                    runs=5
                ),
                timeout=600  # 10 Minuten max
            )
            
            # Validierung
            with db_manager.get_session() as session:
                summary = session.query(ModelSummary).filter_by(model_id=model_id).first()
                
                if summary:
                    logger.info(f"✅ {model_id}: {summary.success_rate:.0%} Erfolg, "
                               f"{summary.avg_fields_found:.1f} Felder, "
                               f"{summary.overall_consistency:.2f} Konsistenz")
                else:
                    logger.warning(f"⚠️  Keine Summary für {model_id}")
            
            return {
                'success': True,
                'result': result,
                'timestamp': datetime.now().isoformat()
            }
            
        except asyncio.TimeoutError:
            logger.error(f"❌ Timeout bei {model_id}")
            return {'success': False, 'error': 'Timeout', 'timestamp': datetime.now().isoformat()}
        except Exception as e:
            logger.error(f"❌ Fehler bei {model_id}: {str(e)}")
            return {'success': False, 'error': str(e), 'timestamp': datetime.now().isoformat()}
    
    async def run_tests(self):
        """Führe Tests für die verbleibenden Grok-Modelle durch"""
        logger.info("=== TESTE VERBLEIBENDE GROK-MODELLE ===")
        logger.info(f"Modelle: {', '.join(GROK_MODELS_TO_TEST)}")
        logger.info(f"Minen: {', '.join([m['name'] for m in TEST_MINES])}")
        
        # Initiale Statistiken
        with db_manager.get_session() as session:
            initial_sources = session.query(func.count(Source.id)).scalar()
            initial_tests = session.query(func.count(ModelStatistics.id)).scalar()
            logger.info(f"\nStart: {initial_sources} Quellen, {initial_tests} Tests")
        
        # Teste alle Modelle
        for model in GROK_MODELS_TO_TEST:
            self.results[model] = {}
            
            for mine_data in TEST_MINES:
                result = await self.test_single_model(model, mine_data)
                self.results[model][mine_data['name']] = result
                
                # Speichere Zwischenergebnisse
                self.save_results()
                
                # Kurze Pause zwischen Tests
                await asyncio.sleep(2)
        
        # Finale Statistiken
        with db_manager.get_session() as session:
            final_sources = session.query(func.count(Source.id)).scalar()
            final_tests = session.query(func.count(ModelStatistics.id)).scalar()
            
            # Grok-spezifische Statistiken
            grok_models = session.query(
                ModelSummary.model_id,
                ModelSummary.success_rate,
                ModelSummary.avg_fields_found,
                ModelSummary.overall_consistency,
                ModelSummary.total_tests
            ).filter(
                ModelSummary.model_id.like('grok:%')
            ).order_by(
                ModelSummary.avg_fields_found.desc()
            ).all()
            
            logger.info(f"\n{'='*60}")
            logger.info("FINALE STATISTIKEN:")
            logger.info(f"Quellen: {initial_sources} → {final_sources} (+{final_sources - initial_sources})")
            logger.info(f"Tests: {initial_tests} → {final_tests} (+{final_tests - initial_tests})")
            
            logger.info("\nALLE GROK-MODELLE (nach Feldern sortiert):")
            for model_id, success_rate, avg_fields, consistency, total_tests in grok_models:
                logger.info(f"- {model_id}: {avg_fields:.1f} Felder, "
                           f"{success_rate:.0%} Erfolg, {consistency:.2f} Konsistenz "
                           f"({total_tests} Tests)")
        
        return self.results


async def main():
    """Hauptfunktion"""
    tester = GrokRemainingTester()
    
    # Führe Tests durch
    results = await tester.run_tests()
    
    # Erstelle Zusammenfassung
    logger.info("\n✅ Alle Grok-Tests abgeschlossen!")
    logger.info("Ergebnisse gespeichert in: grok_remaining_results.json")
    
    # Zeige Zusammenfassung
    successful_tests = 0
    failed_tests = 0
    
    for model, mines in results.items():
        for mine, result in mines.items():
            if result and result.get('success'):
                successful_tests += 1
            else:
                failed_tests += 1
    
    logger.info(f"\nZUSAMMENFASSUNG:")
    logger.info(f"✅ Erfolgreiche Tests: {successful_tests}")
    logger.info(f"❌ Fehlgeschlagene Tests: {failed_tests}")
    
    # Detaillierte Ergebnisse
    logger.info(f"\nDETAILLIERTE ERGEBNISSE:")
    for model in GROK_MODELS_TO_TEST:
        model_id = f"grok:{model}"
        if model in results:
            successes = sum(1 for r in results[model].values() if r and r.get('success'))
            total = len(results[model])
            logger.info(f"{model_id}: {successes}/{total} erfolgreich ({successes/total*100:.0f}%)")


if __name__ == "__main__":
    asyncio.run(main())