"""
Author: rahn
Datum: 13.07.2025
Version: 1.0
Beschreibung: Spezialisierter Test-Agent für VOLLSTÄNDIGE Perplexity Models Tests (60 Tests total)
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from provider_test_framework import ProviderTestFramework, TestMine, TestResult
from model_benchmark_service import ModelBenchmarkService
from database import db_manager
from database.models import ModelStatistics

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class PerplexityTestProgress:
    """Tracking für Perplexity Test Progress"""
    total_tests: int = 60  # 4 models × 3 mines × 5 runs
    completed_tests: int = 0
    successful_tests: int = 0
    failed_tests: int = 0
    current_model: str = ""
    current_mine: str = ""
    current_run: int = 0
    start_time: datetime = None
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.start_time is None:
            self.start_time = datetime.now()


class PerplexityTestRunner:
    """Spezialisierter Test-Runner für ALLE 4 Perplexity Models"""
    
    # ALLE 4 Perplexity Models zu testen
    PERPLEXITY_MODELS = [
        "perplexity:sonar",
        "perplexity:sonar-pro", 
        "perplexity:sonar-deep-research",
        "perplexity:sonar-reasoning"
    ]
    
    # Quebec Test-Minen (gleich wie im Framework)
    QUEBEC_MINES = [
        TestMine(
            name="Éléonore",
            country="Canada", 
            region="Quebec",
            commodity="Gold",
            expected_operator="Newmont",
            expected_status="Active"
        ),
        TestMine(
            name="Niobec", 
            country="Canada",
            region="Quebec", 
            commodity="Niobium",
            expected_operator="IAMGOLD",
            expected_status="Active"
        ),
        TestMine(
            name="LaRonde",
            country="Canada",
            region="Quebec",
            commodity="Gold", 
            expected_operator="Agnico Eagle",
            expected_status="Active"
        )
    ]
    
    RUNS_PER_MINE = 5  # 5 Durchläufe pro Mine pro Model
    
    def __init__(self):
        self.framework = ProviderTestFramework()
        self.benchmark_service = ModelBenchmarkService()
        self.progress = PerplexityTestProgress()
        self.all_results = []
        
    async def run_complete_perplexity_tests(self) -> Dict[str, Any]:
        """
        Führt ALLE 60 Perplexity Tests durch (4 Models × 3 Mines × 5 Runs)
        
        Returns:
            Vollständige Test-Ergebnisse und Database-Validierung
        """
        logger.info("🚀 STARTING COMPLETE PERPLEXITY TESTS")
        logger.info(f"📊 TESTING: {len(self.PERPLEXITY_MODELS)} models × {len(self.QUEBEC_MINES)} mines × {self.RUNS_PER_MINE} runs = {self.progress.total_tests} total tests")
        
        self.progress.start_time = datetime.now()
        
        try:
            # 1. Validiere Model-Verfügbarkeit
            await self._validate_perplexity_models()
            
            # 2. Führe systematische Tests durch
            await self._execute_all_perplexity_tests()
            
            # 3. Validiere Database-Vollständigkeit
            validation_results = await self._validate_database_completeness()
            
            # 4. Erstelle Final Report
            final_report = await self._create_final_report(validation_results)
            
            # 5. Log Final Status
            await self._log_final_status()
            
            return final_report
            
        except Exception as e:
            logger.error(f"💥 KRITISCHER FEHLER in Perplexity Tests: {e}")
            self.progress.errors.append(f"Critical Error: {e}")
            return {
                "success": False,
                "error": str(e),
                "progress": self.progress,
                "partial_results": self.all_results
            }
    
    async def _validate_perplexity_models(self):
        """Validiert dass alle Perplexity Models verfügbar sind"""
        logger.info("🔍 Validating Perplexity model availability...")
        
        for model_id in self.PERPLEXITY_MODELS:
            try:
                # Test verfügbar über Search Service
                from search_service import search_service
                model_name = model_id.split(':')[1]
                
                # Minimal test - nicht in DB speichern
                test_result = await search_service.search_mine(
                    "Test", "Canada", "Gold", model_name, "Quebec"
                )
                
                if test_result and test_result.get('success'):
                    logger.info(f"✅ {model_id} - AVAILABLE")
                else:
                    logger.warning(f"⚠️ {model_id} - PARTIAL AVAILABILITY")
                    
            except Exception as e:
                logger.error(f"❌ {model_id} - UNAVAILABLE: {e}")
                self.progress.errors.append(f"Model {model_id} validation failed: {e}")
    
    async def _execute_all_perplexity_tests(self):
        """Führt alle 60 Perplexity Tests systematisch durch"""
        logger.info("🎯 EXECUTING ALL 60 PERPLEXITY TESTS...")
        
        for model_idx, model_id in enumerate(self.PERPLEXITY_MODELS):
            self.progress.current_model = model_id
            logger.info(f"🔄 TESTING MODEL {model_idx + 1}/{len(self.PERPLEXITY_MODELS)}: {model_id}")
            
            for mine_idx, mine in enumerate(self.QUEBEC_MINES):
                self.progress.current_mine = mine.name
                logger.info(f"  ⛏️ TESTING MINE {mine_idx + 1}/{len(self.QUEBEC_MINES)}: {mine.name}")
                
                # 5 Runs für diese Mine
                for run in range(1, self.RUNS_PER_MINE + 1):
                    self.progress.current_run = run
                    
                    try:
                        # Verwende Framework._test_single_run für jeden Test
                        result = await self._execute_single_test_with_retry(model_id, mine, run)
                        self.all_results.append(result)
                        
                        if result.success:
                            self.progress.successful_tests += 1
                            logger.info(f"    ✅ RUN {run}/5: SUCCESS - {result.fields_found} fields, {result.response_time_ms:.0f}ms")
                        else:
                            self.progress.failed_tests += 1
                            logger.warning(f"    ❌ RUN {run}/5: FAILED - {result.error}")
                        
                        self.progress.completed_tests += 1
                        
                        # Progress Log
                        progress_pct = (self.progress.completed_tests / self.progress.total_tests) * 100
                        logger.info(f"📈 PROGRESS: {self.progress.completed_tests}/{self.progress.total_tests} ({progress_pct:.1f}%)")
                        
                        # Rate limit protection
                        await asyncio.sleep(2)
                        
                    except Exception as e:
                        logger.error(f"💥 ERROR in {model_id} {mine.name} Run {run}: {e}")
                        self.progress.errors.append(f"{model_id} {mine.name} Run {run}: {e}")
                        self.progress.failed_tests += 1
                        self.progress.completed_tests += 1
                
                # Pause zwischen Minen
                logger.info(f"  ⏸️ Mine {mine.name} completed, pausing 5s...")
                await asyncio.sleep(5)
            
            # Pause zwischen Models
            logger.info(f"🔄 Model {model_id} completed, pausing 10s...")
            await asyncio.sleep(10)
    
    async def _execute_single_test_with_retry(self, model_id: str, mine: TestMine, run_number: int) -> TestResult:
        """
        Führt einen einzelnen Test mit Retry-Logic durch
        """
        max_retries = 3
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                # Verwende Framework's _test_single_run Methode
                result = await self.framework._test_single_run(model_id, mine, run_number)
                
                # Erfolgreicher Test
                return result
                
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"🔄 RETRY {attempt + 1}/{max_retries} for {model_id} {mine.name} Run {run_number}: {e}")
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    # Final failure - create error result
                    logger.error(f"💥 FINAL FAILURE after {max_retries} attempts: {model_id} {mine.name} Run {run_number}")
                    
                    return TestResult(
                        model_id=model_id,
                        mine_name=mine.name,
                        run_number=run_number,
                        success=False,
                        response_time_ms=0,
                        fields_found=0,
                        sources_count=0,
                        data_quality=0.0,
                        structured_data={},
                        error=f"Failed after {max_retries} retries: {str(e)}",
                        timestamp=datetime.now()
                    )
    
    async def _validate_database_completeness(self) -> Dict[str, Any]:
        """
        Validiert dass ALLE 60 Tests in der Database gespeichert wurden
        """
        logger.info("🔍 VALIDATING DATABASE COMPLETENESS...")
        
        validation_results = {
            "timestamp": datetime.now().isoformat(),
            "expected_entries": 60,
            "found_entries": 0,
            "missing_entries": [],
            "model_completeness": {},
            "mine_completeness": {},
            "success": False
        }
        
        try:
            with db_manager.get_session() as session:
                # Check für jeden Model
                for model_id in self.PERPLEXITY_MODELS:
                    model_entries = session.query(ModelStatistics).filter_by(model_id=model_id).all()
                    model_count = len(model_entries)
                    expected_per_model = len(self.QUEBEC_MINES) * self.RUNS_PER_MINE  # 15
                    
                    validation_results["model_completeness"][model_id] = {
                        "found": model_count,
                        "expected": expected_per_model,
                        "complete": model_count == expected_per_model
                    }
                    
                    if model_count != expected_per_model:
                        validation_results["missing_entries"].append(
                            f"{model_id}: {model_count}/{expected_per_model} entries"
                        )
                    
                    # Check pro Mine für dieses Model
                    for mine in self.QUEBEC_MINES:
                        mine_entries = session.query(ModelStatistics).filter_by(
                            model_id=model_id, mine_name=mine.name
                        ).all()
                        
                        expected_runs = self.RUNS_PER_MINE  # 5
                        mine_key = f"{model_id}:{mine.name}"
                        
                        validation_results["mine_completeness"][mine_key] = {
                            "found": len(mine_entries),
                            "expected": expected_runs,
                            "run_numbers": [e.run_number for e in mine_entries],
                            "complete": len(mine_entries) == expected_runs
                        }
                
                # Gesamt-Zählung
                total_perplexity_entries = session.query(ModelStatistics).filter(
                    ModelStatistics.model_id.in_(self.PERPLEXITY_MODELS)
                ).count()
                
                validation_results["found_entries"] = total_perplexity_entries
                validation_results["success"] = total_perplexity_entries == 60
                
                logger.info(f"📊 DATABASE VALIDATION: {total_perplexity_entries}/60 entries found")
                
                if validation_results["success"]:
                    logger.info("✅ ALL 60 PERPLEXITY TESTS SUCCESSFULLY IN DATABASE")
                else:
                    logger.warning(f"⚠️ INCOMPLETE: {60 - total_perplexity_entries} entries missing")
                    for missing in validation_results["missing_entries"]:
                        logger.warning(f"  - {missing}")
                
        except Exception as e:
            logger.error(f"💥 DATABASE VALIDATION ERROR: {e}")
            validation_results["error"] = str(e)
        
        return validation_results
    
    async def _create_final_report(self, validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Erstellt Final Report für alle Perplexity Tests"""
        
        duration = (datetime.now() - self.progress.start_time).total_seconds()
        
        # Model Performance Analysis
        model_performance = {}
        for model_id in self.PERPLEXITY_MODELS:
            model_results = [r for r in self.all_results if r.model_id == model_id]
            successful_results = [r for r in model_results if r.success]
            
            if model_results:
                model_performance[model_id] = {
                    "total_tests": len(model_results),
                    "successful_tests": len(successful_results),
                    "success_rate": len(successful_results) / len(model_results),
                    "avg_response_time": sum(r.response_time_ms for r in successful_results) / len(successful_results) if successful_results else 0,
                    "avg_fields_found": sum(r.fields_found for r in successful_results) / len(successful_results) if successful_results else 0,
                    "avg_data_quality": sum(r.data_quality for r in successful_results) / len(successful_results) if successful_results else 0
                }
        
        # Mine Performance Analysis
        mine_performance = {}
        for mine in self.QUEBEC_MINES:
            mine_results = [r for r in self.all_results if r.mine_name == mine.name]
            successful_results = [r for r in mine_results if r.success]
            
            mine_performance[mine.name] = {
                "total_tests": len(mine_results),
                "successful_tests": len(successful_results),
                "success_rate": len(successful_results) / len(mine_results) if mine_results else 0,
                "avg_fields_found": sum(r.fields_found for r in successful_results) / len(successful_results) if successful_results else 0
            }
        
        final_report = {
            "success": True,
            "test_type": "COMPLETE_PERPLEXITY_TESTS",
            "execution_summary": {
                "total_tests_planned": self.progress.total_tests,
                "total_tests_executed": self.progress.completed_tests,
                "successful_tests": self.progress.successful_tests,
                "failed_tests": self.progress.failed_tests,
                "overall_success_rate": self.progress.successful_tests / self.progress.completed_tests if self.progress.completed_tests > 0 else 0,
                "duration_seconds": duration,
                "tests_per_second": self.progress.completed_tests / duration if duration > 0 else 0,
                "timestamp": datetime.now().isoformat()
            },
            "model_performance": model_performance,
            "mine_performance": mine_performance,
            "database_validation": validation_results,
            "errors": self.progress.errors,
            "completion_status": "✅ 60/60 Perplexity tests completed, all in database" if validation_results.get("success") else f"⚠️ {validation_results.get('found_entries', 0)}/60 tests in database"
        }
        
        return final_report
    
    async def _log_final_status(self):
        """Final Status Logging"""
        logger.info("=" * 80)
        logger.info("🏁 PERPLEXITY TESTS FINAL STATUS")
        logger.info("=" * 80)
        logger.info(f"📊 TESTS EXECUTED: {self.progress.completed_tests}/{self.progress.total_tests}")
        logger.info(f"✅ SUCCESSFUL: {self.progress.successful_tests}")
        logger.info(f"❌ FAILED: {self.progress.failed_tests}")
        logger.info(f"🎯 SUCCESS RATE: {self.progress.successful_tests/self.progress.completed_tests:.1%}")
        logger.info(f"⏱️ DURATION: {(datetime.now() - self.progress.start_time).total_seconds():.1f}s")
        
        if self.progress.errors:
            logger.warning(f"⚠️ ERRORS: {len(self.progress.errors)}")
            for error in self.progress.errors[-5:]:  # Last 5 errors
                logger.warning(f"  - {error}")
        
        logger.info("=" * 80)


async def main():
    """Main function to run complete Perplexity tests"""
    runner = PerplexityTestRunner()
    
    logger.info("🚀 STARTING COMPLETE PERPLEXITY MODEL TESTS")
    logger.info("📋 TESTING ALL 4 MODELS: perplexity:sonar, sonar-pro, sonar-deep-research, sonar-reasoning")
    logger.info("⛏️ TESTING ALL 3 MINES: Éléonore, Niobec, LaRonde")
    logger.info("🔄 TESTING 5 RUNS PER MINE PER MODEL")
    logger.info("📊 TOTAL: 60 TESTS")
    
    results = await runner.run_complete_perplexity_tests()
    
    # Final validation check
    if results.get("database_validation", {}).get("success"):
        logger.info("🎉 SUCCESS: ✅ 60/60 Perplexity tests completed, all in database")
    else:
        found = results.get("database_validation", {}).get("found_entries", 0)
        logger.warning(f"⚠️ INCOMPLETE: {found}/60 tests in database")
    
    return results


if __name__ == "__main__":
    asyncio.run(main())