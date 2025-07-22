"""
Author: rahn
Datum: 13.07.2025
Version: 1.0
Beschreibung: Optimierter Perplexity Test-Runner mit DB-Bereinigung und zielgerichteten Tests
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any
from sqlalchemy import func

from database import db_manager
from database.models import ModelStatistics
from provider_test_framework import ProviderTestFramework, TestMine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PerplexityTestOptimizer:
    """Optimierter Test-Runner für präzise 60 Perplexity Tests"""
    
    PERPLEXITY_MODELS = [
        "perplexity:sonar",
        "perplexity:sonar-pro", 
        "perplexity:sonar-deep-research",
        "perplexity:sonar-reasoning"
    ]
    
    QUEBEC_MINES = [
        TestMine(
            name="Éléonore",
            country="Canada", 
            region="Quebec",
            commodity="Gold"
        ),
        TestMine(
            name="Niobec", 
            country="Canada",
            region="Quebec", 
            commodity="Niobium"
        ),
        TestMine(
            name="LaRonde",
            country="Canada",
            region="Quebec",
            commodity="Gold"
        )
    ]
    
    def __init__(self):
        self.framework = ProviderTestFramework()
    
    def clean_perplexity_database(self):
        """Bereinigt Perplexity-Einträge für saubere Tests"""
        logger.info("🧹 CLEANING PERPLEXITY DATABASE ENTRIES...")
        
        try:
            with db_manager.get_session() as session:
                # Lösche alle Perplexity-Einträge
                deleted = session.query(ModelStatistics).filter(
                    ModelStatistics.model_id.in_(self.PERPLEXITY_MODELS)
                ).delete(synchronize_session=False)
                
                session.commit()
                logger.info(f"🗑️ {deleted} Perplexity entries deleted from database")
                
        except Exception as e:
            logger.error(f"💥 DATABASE CLEANUP ERROR: {e}")
    
    def get_missing_tests(self) -> List[Dict[str, Any]]:
        """Bestimmt welche Tests noch fehlen für komplette Abdeckung"""
        missing_tests = []
        
        try:
            with db_manager.get_session() as session:
                for model_id in self.PERPLEXITY_MODELS:
                    for mine in self.QUEBEC_MINES:
                        # Prüfe welche run_numbers fehlen
                        existing_runs = session.query(ModelStatistics.run_number).filter_by(
                            model_id=model_id, mine_name=mine.name
                        ).all()
                        
                        existing_run_numbers = {r[0] for r in existing_runs}
                        expected_runs = {1, 2, 3, 4, 5}
                        missing_runs = expected_runs - existing_run_numbers
                        
                        for run_number in missing_runs:
                            missing_tests.append({
                                "model_id": model_id,
                                "mine": mine,
                                "run_number": run_number
                            })
                
                logger.info(f"📋 {len(missing_tests)} tests missing for complete coverage")
                return missing_tests
                
        except Exception as e:
            logger.error(f"💥 ERROR CHECKING MISSING TESTS: {e}")
            return []
    
    def get_current_status(self) -> Dict[str, Any]:
        """Aktueller Status der Perplexity Tests"""
        try:
            with db_manager.get_session() as session:
                status = {"models": {}, "total": 0}
                
                for model_id in self.PERPLEXITY_MODELS:
                    model_count = session.query(ModelStatistics).filter_by(model_id=model_id).count()
                    status["models"][model_id] = model_count
                    status["total"] += model_count
                
                status["progress_pct"] = (status["total"] / 60) * 100
                status["complete"] = status["total"] == 60
                
                return status
                
        except Exception as e:
            logger.error(f"💥 STATUS CHECK ERROR: {e}")
            return {"error": str(e)}
    
    async def run_missing_tests_only(self) -> Dict[str, Any]:
        """Führt nur die fehlenden Tests durch"""
        missing_tests = self.get_missing_tests()
        
        if not missing_tests:
            logger.info("✅ ALL 60 PERPLEXITY TESTS ALREADY COMPLETED")
            return {"success": True, "message": "All tests completed", "total": 60}
        
        logger.info(f"🎯 RUNNING {len(missing_tests)} MISSING TESTS...")
        
        completed = 0
        errors = []
        
        for i, test in enumerate(missing_tests):
            try:
                logger.info(f"🔄 {i+1}/{len(missing_tests)}: {test['model_id']} {test['mine'].name} Run {test['run_number']}")
                
                # Führe einzelnen Test durch
                result = await self.framework._test_single_run(
                    test['model_id'], test['mine'], test['run_number']
                )
                
                if result.success:
                    completed += 1
                    logger.info(f"    ✅ SUCCESS - {result.fields_found} fields")
                else:
                    logger.warning(f"    ❌ FAILED - {result.error}")
                    errors.append(f"{test['model_id']} {test['mine'].name} Run {test['run_number']}: {result.error}")
                
                # Rate limiting
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"💥 ERROR: {e}")
                errors.append(f"{test['model_id']} {test['mine'].name} Run {test['run_number']}: {str(e)}")
        
        # Final status check
        final_status = self.get_current_status()
        
        return {
            "success": True,
            "tests_attempted": len(missing_tests),
            "tests_completed": completed,
            "errors": errors,
            "final_status": final_status
        }
    
    async def ensure_60_tests_complete(self) -> str:
        """Stellt sicher dass exakt 60 Perplexity Tests completed sind"""
        
        # 1. Status prüfen
        status = self.get_current_status()
        logger.info(f"📊 CURRENT STATUS: {status['total']}/60 tests ({status['progress_pct']:.1f}%)")
        
        if status.get("complete"):
            return "✅ 60/60 Perplexity tests completed, all in database"
        
        # 2. Zu viele? Bereinigen
        if status["total"] > 60:
            logger.warning(f"⚠️ TOO MANY TESTS ({status['total']}), cleaning database...")
            self.clean_perplexity_database()
            status = self.get_current_status()
        
        # 3. Fehlende Tests durchführen
        if status["total"] < 60:
            logger.info(f"🔄 MISSING {60 - status['total']} tests, running them...")
            await self.run_missing_tests_only()
            status = self.get_current_status()
        
        # 4. Final validation
        if status.get("complete"):
            return "✅ 60/60 Perplexity tests completed, all in database"
        else:
            return f"⚠️ {status['total']}/60 tests in database"


async def main():
    """Main function für optimierte Perplexity Tests"""
    optimizer = PerplexityTestOptimizer()
    
    logger.info("🚀 PERPLEXITY TEST OPTIMIZER STARTING...")
    
    result = await optimizer.ensure_60_tests_complete()
    
    logger.info("🏁 FINAL RESULT:")
    logger.info(result)
    
    return result


if __name__ == "__main__":
    asyncio.run(main())