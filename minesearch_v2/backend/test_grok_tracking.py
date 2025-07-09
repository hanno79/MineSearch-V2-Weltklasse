"""
Author: rahn
Datum: 09.07.2025
Version: 1.0
Beschreibung: Grok Provider Test mit Quellen-Tracking
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

# Grok Modelle
GROK_MODELS = ['grok-3', 'grok-3-mini', 'grok-3-fast']

async def test_grok():
    """Test Grok Provider mit Quellen-Tracking"""
    logger.info("=== GROK PROVIDER TEST ===")
    
    # Initiale Quellen-Anzahl
    with db_manager.get_session() as session:
        initial_sources = session.query(func.count(Source.id)).scalar()
        logger.info(f"Initiale Quellen: {initial_sources}")
    
    # Test jeden Modells mit jeder Mine
    benchmark_service = ModelBenchmarkService()
    
    for model in GROK_MODELS:
        model_id = f"grok:{model}"
        logger.info(f"\n{'='*50}")
        logger.info(f"Teste {model_id}")
        logger.info(f"{'='*50}")
        
        for mine_data in TEST_MINES:
            logger.info(f"\n📍 Mine: {mine_data['name']}")
            
            try:
                # 3 Durchläufe für Konsistenz
                result = await benchmark_service.benchmark_model(
                    model_id=model_id,
                    mine_data=mine_data,
                    runs=3
                )
                
                # Validierung
                with db_manager.get_session() as session:
                    # ModelSummary
                    summary = session.query(ModelSummary).filter_by(model_id=model_id).first()
                    
                    # Aktuelle Quellen
                    current_sources = session.query(func.count(Source.id)).scalar()
                    
                    logger.info(f"✅ Ergebnis:")
                    logger.info(f"   - Erfolg: {result['success_rate']:.0%}")
                    logger.info(f"   - Felder: {result['avg_fields_found']}")
                    logger.info(f"   - Konsistenz: {result['consistency_analysis']['overall_consistency']:.2f}")
                    
                    if summary:
                        logger.info(f"   - Summary: Tests={summary.total_tests}, "
                                   f"Erfolg={summary.success_rate:.0%}, "
                                   f"Konsistenz={summary.overall_consistency:.2f}")
                    
                    logger.info(f"   - Quellen: {current_sources} (von 333)")
                    
                    # Warnung bei Problemen
                    if summary and summary.success_rate == 0:
                        logger.warning(f"⚠️  Erfolgsrate ist 0%!")
                    if summary and summary.overall_consistency == 0:
                        logger.warning(f"⚠️  Konsistenz ist 0!")
                    
            except Exception as e:
                logger.error(f"❌ Fehler: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
            
            # Pause zwischen Tests
            await asyncio.sleep(2)
    
    # Finale Zusammenfassung
    with db_manager.get_session() as session:
        final_sources = session.query(func.count(Source.id)).scalar()
        
        logger.info(f"\n{'='*60}")
        logger.info("GROK ZUSAMMENFASSUNG:")
        logger.info(f"  - Quellen: {initial_sources} → {final_sources} (+{final_sources - initial_sources})")
        
        # Alle Grok Summaries
        summaries = session.query(ModelSummary).filter(
            ModelSummary.model_id.like('grok:%')
        ).all()
        
        logger.info("\nGROK MODELLE:")
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
        
        # Prüfe 333 Quellen
        if final_sources >= 333:
            logger.info(f"\n✅ ALLE 333+ QUELLEN WERDEN GENUTZT!")
        else:
            logger.warning(f"\n⚠️  NUR {final_sources} VON 333 QUELLEN WERDEN GENUTZT!")

if __name__ == "__main__":
    asyncio.run(test_grok())