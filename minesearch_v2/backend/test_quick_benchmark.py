"""
Author: rahn
Datum: 07.07.2025
Version: 1.0
Beschreibung: Schneller Benchmark-Test für Perplexity-Modell
"""

import asyncio
import logging
from model_benchmark_service import ModelBenchmarkService
from database import db_manager

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def quick_test():
    """Schneller Test mit einem Modell und einer Mine"""
    service = ModelBenchmarkService()
    
    # Test nur perplexity:sonar mit Canadian Malartic
    mine_data = {
        'name': 'Canadian Malartic',
        'country': 'Canada',
        'region': 'Quebec',
        'commodity': 'Gold'
    }
    
    logger.info("Starte schnellen Benchmark-Test...")
    
    # Nur 2 Durchläufe für schnellen Test
    result = await service.benchmark_model(
        model_id='perplexity:sonar',
        mine_data=mine_data,
        runs=2
    )
    
    logger.info("\n=== ERGEBNISSE ===")
    logger.info(f"Erfolgsrate: {result['success_rate']:.0%}")
    logger.info(f"Ø Response-Zeit: {result['avg_response_time_ms']:.0f}ms")
    logger.info(f"Ø Gefundene Felder: {result['avg_fields_found']:.1f}")
    logger.info(f"Konsistenz: {result['consistency_analysis']['overall_consistency']:.0%}")
    
    # Zeige gefundene Felder
    if result.get('detailed_results'):
        first_run = result['detailed_results'][0]
        if first_run.get('success') and first_run.get('structured_data'):
            filled_fields = {k: v for k, v in first_run['structured_data'].items() if v}
            logger.info(f"\nGefundene Felder ({len(filled_fields)}):")
            for field, value in list(filled_fields.items())[:10]:
                logger.info(f"  - {field}: {value}")
    
    # Teste Statistik-Abruf
    summary = await service.get_benchmark_summary('perplexity:sonar')
    if summary:
        logger.info(f"\nModell-Zusammenfassung aus DB:")
        logger.info(f"  - Gesamt-Tests: {summary['total_tests']}")
        logger.info(f"  - Erfolgsrate: {summary['success_rate']:.0%}")
        logger.info(f"  - Konsistenz: {summary['overall_consistency']:.0%}")

if __name__ == "__main__":
    asyncio.run(quick_test())