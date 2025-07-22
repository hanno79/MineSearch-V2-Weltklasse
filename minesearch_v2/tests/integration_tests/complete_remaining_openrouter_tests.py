"""
Author: rahn
Datum: 13.07.2025  
Version: 1.0
Beschreibung: Komplettiert die fehlenden OpenRouter Tests für 135/135 Einträge
"""

import asyncio
import logging
from datetime import datetime
from database import db_manager
from database.models import ModelStatistics
from provider_test_framework import ProviderTestFramework, TestMine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def complete_remaining_tests():
    """Komplettiert die fehlenden OpenRouter Tests"""
    
    # Test Framework initialisieren
    framework = ProviderTestFramework()
    
    # OpenRouter Models
    openrouter_models = [
        'openrouter:deepseek-free',
        'openrouter:deepseek-chat', 
        'openrouter:deepseek-reasoner',
        'openrouter:deepseek-chimera-free',
        'openrouter:mistral-small-free',
        'openrouter:cypher-alpha-free',
        'openrouter:minimax-m1',
        'openrouter:llama-3.3-nemotron-super',
        'openrouter:llama-3.1-nemotron-ultra'
    ]
    
    # Quebec Mines
    mines = [
        TestMine(name="Éléonore", country="Canada", region="Quebec", commodity="Gold"),
        TestMine(name="Niobec", country="Canada", region="Quebec", commodity="Niobium"),
        TestMine(name="LaRonde", country="Canada", region="Quebec", commodity="Gold")
    ]
    
    # Finde fehlende Tests
    missing_tests = []
    
    with db_manager.get_session() as session:
        for model_id in openrouter_models:
            for mine in mines:
                for run in range(1, 6):  # Runs 1-5
                    existing = session.query(ModelStatistics).filter_by(
                        model_id=model_id,
                        mine_name=mine.name,
                        run_number=run
                    ).first()
                    
                    if not existing:
                        missing_tests.append((model_id, mine, run))
    
    logger.info(f"🔍 Gefunden: {len(missing_tests)} fehlende Tests")
    
    # Führe fehlende Tests durch
    for i, (model_id, mine, run) in enumerate(missing_tests):
        logger.info(f"🧪 Test {i+1}/{len(missing_tests)}: {model_id} - {mine.name} - Run {run}")
        
        try:
            result = await framework._test_single_run(model_id, mine, run)
            
            if result.success:
                logger.info(f"  ✅ Erfolgreich: {result.fields_found} Felder")
            else:
                logger.warning(f"  ❌ Fehlgeschlagen: {result.error}")
                
        except Exception as e:
            logger.error(f"  💥 Exception: {e}")
        
        # Kurze Pause
        await asyncio.sleep(1)
    
    # Final Count
    with db_manager.get_session() as session:
        total_count = 0
        for model_id in openrouter_models:
            count = session.query(ModelStatistics).filter_by(model_id=model_id).count()
            total_count += count
        
        logger.info(f"🎯 FINAL RESULT: {total_count}/135 OpenRouter tests in database")
        
        if total_count == 135:
            print("✅ 135/135 OpenRouter tests completed, all in database")
            return True
        else:
            print(f"⚠️ {total_count}/135 OpenRouter tests completed, {135-total_count} still missing")
            return False

if __name__ == "__main__":
    asyncio.run(complete_remaining_tests())