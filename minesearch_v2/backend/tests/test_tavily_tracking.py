#!/usr/bin/env python3
"""
Test für Tavily Provider und Source Tracking
"""

import asyncio
import logging
from datetime import datetime
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from search_service_multi import multi_search_service
from database import db_manager, Source
from sqlalchemy.sql import func

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_multiple_providers_tracking():
    """Teste mehrere Provider und Source Tracking"""
    
    # Test-Mine
    mine_name = "Canadian Malartic"
    country = "Canada"
    
    # Teste verschiedene Provider
    test_models = [
        "tavily:search",
        "perplexity:sonar",
        "perplexity:sonar-pro",
        "openrouter:deepseek-free",
        "exa:neural-search",
        "grok:grok-3",
        "anthropic:claude-sonnet-4",
        "gemini:gemini-2.5-flash"
    ]
    
    for model_id in test_models:
        logger.info(f"\n{'='*60}")
        logger.info(f"=== Test {model_id} für {mine_name} ===")
        logger.info(f"{'='*60}")
        
        # Vorher: Zeige bestehende Quellen
        with db_manager.get_session() as session:
            total_sources_before = session.query(Source).count()
            today_sources_before = session.query(Source).filter(
                func.date(Source.last_attempted_access) == datetime.now().date()
            ).count()
            logger.info(f"Quellen in DB: {total_sources_before} (heute: {today_sources_before})")
        
        try:
            # Führe Suche durch
            result = await multi_search_service.search_with_model(
                model_id=model_id,
                mine_name=mine_name,
                country=country
            )
    
            # Zeige Ergebnis
            if result.get('success'):
                logger.info(f"✅ Suche erfolgreich!")
                logger.info(f"Gefundene Felder: {result.get('filled_fields', 0)}")
                sources = result.get('sources', [])
                logger.info(f"Anzahl Sources im Result: {len(sources)}")
                
                if sources and len(sources) > 0:
                    logger.info(f"Erste Source: {sources[0].get('url', sources[0].get('value', 'N/A'))}")
            else:
                logger.error(f"❌ Suche fehlgeschlagen: {result.get('error', 'Unbekannter Fehler')}")
            
            # Warte kurz damit async tasks abgeschlossen werden
            await asyncio.sleep(1)
            
            # Nachher: Zeige Quellen-Status
            with db_manager.get_session() as session:
                total_sources_after = session.query(Source).count()
                today_sources_after = session.query(Source).filter(
                    func.date(Source.last_attempted_access) == datetime.now().date()
                ).count()
                logger.info(f"Nach Suche: {total_sources_after} Quellen (heute: {today_sources_after})")
                logger.info(f"Neue mit heutigem Datum: {today_sources_after - today_sources_before}")
                
        except Exception as e:
            logger.error(f"❌ Fehler bei {model_id}: {str(e)}")
            
    # Finale Zusammenfassung
    logger.info(f"\n{'='*60}")
    logger.info("=== ZUSAMMENFASSUNG ===")
    logger.info(f"{'='*60}")
    
    with db_manager.get_session() as session:
        # Zeige alle Quellen mit heutigem Datum
        today = datetime.now().date()
        today_sources = session.query(Source).filter(
            func.date(Source.last_attempted_access) == today
        ).all()
        
        total_sources = session.query(Source).count()
        
        logger.info(f"\nGesamt-Quellen in DB: {total_sources}")
        logger.info(f"Quellen mit heutigem Datum ({today}): {len(today_sources)}")
        logger.info(f"Prozentsatz heute aktualisiert: {len(today_sources)/total_sources*100:.1f}%")
        
        # Zeige Statistik nach Typ
        type_stats = {}
        for source in today_sources:
            source_type = source.source_type or 'unknown'
            if source_type not in type_stats:
                type_stats[source_type] = 0
            type_stats[source_type] += 1
        
        logger.info("\nHeute aktualisierte Quellen nach Typ:")
        for source_type, count in sorted(type_stats.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"  - {source_type}: {count}")

if __name__ == "__main__":
    asyncio.run(test_multiple_providers_tracking())