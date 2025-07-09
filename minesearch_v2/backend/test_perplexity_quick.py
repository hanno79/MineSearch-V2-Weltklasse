"""
Author: rahn
Datum: 09.07.2025
Version: 1.0
Beschreibung: Schneller Perplexity Test mit nur 1 Durchlauf pro Modell/Mine
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any
from collections import defaultdict

from model_benchmark_service import ModelBenchmarkService
from database import db_manager, ModelStatistics, FieldConsistency, ModelSummary, FieldStatistics, SearchResult, Source
from search_service_multi import MultiProviderSearchService
from sqlalchemy import func

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test-Minen
TEST_MINES = [
    {'name': 'Éléonore', 'country': 'Canada', 'region': 'Quebec', 'commodity': 'Gold'},
    {'name': 'Niobec', 'country': 'Canada', 'region': 'Quebec', 'commodity': 'Niobium'},
    {'name': 'LaRonde', 'country': 'Canada', 'region': 'Quebec', 'commodity': 'Gold'}
]

# Nur Perplexity Provider
PERPLEXITY_MODELS = ['sonar', 'sonar-pro', 'sonar-deep-research', 'sonar-reasoning']

async def quick_test():
    """Schneller Test mit nur 1 Durchlauf"""
    logger.info("=== SCHNELLER PERPLEXITY TEST ===")
    
    # Initiale Quellen-Anzahl
    with db_manager.get_session() as session:
        initial_sources = session.query(func.count(Source.id)).scalar()
        logger.info(f"Initiale Quellen: {initial_sources}")
    
    # Test jeden Modells mit jeder Mine (nur 1 Durchlauf)
    benchmark_service = ModelBenchmarkService()
    
    for model in PERPLEXITY_MODELS:
        model_id = f"perplexity:{model}"
        logger.info(f"\n{'='*50}")
        logger.info(f"Teste {model_id}")
        logger.info(f"{'='*50}")
        
        for mine_data in TEST_MINES:
            logger.info(f"\n📍 Mine: {mine_data['name']}")
            
            try:
                # Nur 1 Durchlauf
                result = await benchmark_service.benchmark_model(
                    model_id=model_id,
                    mine_data=mine_data,
                    runs=1
                )
                
                # Validierung
                with db_manager.get_session() as session:
                    # ModelStatistics für diese Kombination
                    stats = session.query(ModelStatistics).filter_by(
                        model_id=model_id,
                        mine_name=mine_data['name']
                    ).order_by(ModelStatistics.test_datetime.desc()).first()
                    
                    # ModelSummary
                    summary = session.query(ModelSummary).filter_by(model_id=model_id).first()
                    
                    # Aktuelle Quellen
                    current_sources = session.query(func.count(Source.id)).scalar()
                    
                    logger.info(f"✅ Ergebnis:")
                    logger.info(f"   - Erfolg: {result['success_rate']:.0%}")
                    logger.info(f"   - Felder: {result['avg_fields_found']}")
                    logger.info(f"   - Konsistenz: {result['consistency_analysis']['overall_consistency']:.2f}")
                    
                    if stats:
                        logger.info(f"   - DB Entry: Erfolg={stats.success}, Felder={stats.fields_found}")
                    else:
                        logger.error(f"   - ❌ Kein DB Entry gefunden!")
                    
                    if summary:
                        logger.info(f"   - Summary: Tests={summary.total_tests}, "
                                   f"Erfolg={summary.success_rate:.0%}, "
                                   f"Konsistenz={summary.overall_consistency:.2f}")
                    
                    logger.info(f"   - Quellen: {current_sources} (von 319)")
                    
                    # Warnung bei Problemen
                    if summary and summary.success_rate == 0:
                        logger.warning(f"⚠️  Erfolgsrate ist 0%!")
                    if summary and summary.overall_consistency == 0:
                        logger.warning(f"⚠️  Konsistenz ist 0!")
                    
            except Exception as e:
                logger.error(f"❌ Fehler: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
            
            # Kurze Pause
            await asyncio.sleep(1)
    
    # Finale Zusammenfassung
    with db_manager.get_session() as session:
        final_sources = session.query(func.count(Source.id)).scalar()
        
        logger.info(f"\n{'='*60}")
        logger.info("ZUSAMMENFASSUNG:")
        logger.info(f"  - Quellen: {initial_sources} → {final_sources} (+{final_sources - initial_sources})")
        
        # Alle Perplexity Summaries
        summaries = session.query(ModelSummary).filter(
            ModelSummary.model_id.like('perplexity:%')
        ).all()
        
        logger.info("\nPERPLEXITY MODELLE:")
        for summary in summaries:
            logger.info(f"\n{summary.model_id}:")
            logger.info(f"  - Tests: {summary.total_tests}")
            logger.info(f"  - Erfolgsrate: {summary.success_rate:.0%}")
            logger.info(f"  - Daten-Erfolgsrate: {summary.data_success_rate:.0%}")
            logger.info(f"  - Ø Felder: {summary.avg_fields_found:.1f}")
            logger.info(f"  - Konsistenz: {summary.overall_consistency:.2f}")
            
            # Prüfe auf 0-Werte
            if summary.success_rate == 0:
                logger.warning(f"  ⚠️  WARNUNG: Erfolgsrate ist 0%!")
            if summary.overall_consistency == 0:
                logger.warning(f"  ⚠️  WARNUNG: Konsistenz ist 0!")
        
        # Prüfe 319 Quellen
        if final_sources >= 319:
            logger.info(f"\n✅ ALLE 319 QUELLEN WERDEN GENUTZT!")
        else:
            logger.warning(f"\n⚠️  NUR {final_sources} VON 319 QUELLEN WERDEN GENUTZT!")

if __name__ == "__main__":
    asyncio.run(quick_test())