"""
Author: rahn
Datum: 13.07.2025
Version: 1.0
Beschreibung: Spezialisierter Test-Agent für VOLLSTÄNDIGE Grok Models Validierung

ZIEL: 60 Tests (4 Grok models × 3 mines × 5 runs) mit 100% Abdeckung
"""

import asyncio
import time
import logging
from datetime import datetime
from typing import Dict, List, Any
from dataclasses import dataclass

from provider_test_framework import ProviderTestFramework, TestResult, TestMine
from model_benchmark_service import ModelBenchmarkService
from database import db_manager
from database.models import ModelStatistics

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class GrokTestProgress:
    """Tracking für Grok Test-Progress"""
    total_tests: int = 60
    completed_tests: int = 0
    successful_tests: int = 0
    failed_tests: int = 0
    start_time: datetime = None
    current_test: str = ""

class GrokComprehensiveTestAgent:
    """
    Spezialisierter Test-Agent für VOLLSTÄNDIGE Grok Models Validierung
    
    TESTS:
    - grok:grok-4 (4 models)
    - grok:grok-3
    - grok:grok-3-mini  
    - grok:grok-3-fast
    
    MINES:
    - Éléonore (Gold-Mine, Quebec, Canada)
    - Niobec (Niobium-Mine, Quebec, Canada)
    - LaRonde (Gold-Mine, Quebec, Canada)
    
    RUNS: 5 Durchläufe pro Mine pro Model = 60 TOTAL TESTS
    """
    
    # Grok Models zu testen
    GROK_MODELS = [
        "grok:grok-4",
        "grok:grok-3", 
        "grok:grok-3-mini",
        "grok:grok-3-fast"
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
    
    def __init__(self):
        self.framework = ProviderTestFramework()
        self.benchmark_service = ModelBenchmarkService()
        self.progress = GrokTestProgress()
        self.test_results = []
        self.session_id = f"grok_comprehensive_{int(time.time())}"
        
    async def run_comprehensive_grok_tests(self) -> Dict[str, Any]:
        """
        Führt VOLLSTÄNDIGE Grok Tests durch - 60 Tests garantiert
        
        Returns:
            Umfassende Test-Ergebnisse mit Database-Validierung
        """
        self.progress.start_time = datetime.now()
        logger.info("🚀 STARTE GROK COMPREHENSIVE TEST AGENT")
        logger.info(f"📊 GEPLANT: {self.progress.total_tests} Tests (4 models × 3 mines × 5 runs)")
        logger.info(f"🎯 ZIEL: ✅ 60/60 Grok tests completed, all in database")
        
        try:
            # 1. Validiere Grok Provider Verfügbarkeit
            available_models = await self._validate_grok_availability()
            if len(available_models) != 4:
                logger.error(f"❌ Nur {len(available_models)}/4 Grok models verfügbar!")
                return self._create_failure_report("Nicht alle Grok models verfügbar")
            
            # 2. Führe systematische 60 Tests durch
            await self._execute_all_60_tests()
            
            # 3. Validiere Database-Einträge
            validation_result = await self._validate_database_entries()
            
            # 4. Erstelle finalen Report
            final_report = await self._create_final_report(validation_result)
            
            # 5. Progress-Summary
            elapsed_time = (datetime.now() - self.progress.start_time).total_seconds()
            logger.info(f"🏁 GROK TESTS COMPLETED in {elapsed_time:.1f}s")
            logger.info(f"✅ {self.progress.completed_tests}/60 tests completed")
            logger.info(f"🎯 SUCCESS: {self.progress.successful_tests} | FAILED: {self.progress.failed_tests}")
            
            return final_report
            
        except Exception as e:
            logger.error(f"💥 CRITICAL ERROR in Grok Test Agent: {e}")
            return self._create_failure_report(str(e))
    
    async def _validate_grok_availability(self) -> List[str]:
        """Validiert alle 4 Grok Models"""
        logger.info("🔍 Validiere Grok Provider Verfügbarkeit...")
        
        available_models = []
        for model_id in self.GROK_MODELS:
            try:
                # Prüfe Provider-Konfiguration
                from config.providers import PROVIDERS_CONFIG
                provider_config = PROVIDERS_CONFIG.get('grok', {})
                
                if not provider_config.get('enabled', False):
                    logger.error(f"❌ Grok Provider ist deaktiviert!")
                    continue
                    
                if not provider_config.get('api_key'):
                    logger.error(f"❌ Grok API Key fehlt!")
                    continue
                
                # Model in Konfiguration verfügbar?
                model_name = model_id.split(':')[1]
                if model_name in provider_config.get('models', {}):
                    available_models.append(model_id)
                    logger.info(f"✅ {model_id} verfügbar")
                else:
                    logger.error(f"❌ {model_id} nicht in Konfiguration")
                    
            except Exception as e:
                logger.error(f"❌ Error checking {model_id}: {e}")
        
        logger.info(f"📋 {len(available_models)}/4 Grok models verfügbar")
        return available_models
    
    async def _execute_all_60_tests(self):
        """Führt ALLE 60 Tests systematisch durch"""
        logger.info("🎯 Starte systematische Ausführung aller 60 Tests...")
        
        for model_idx, model_id in enumerate(self.GROK_MODELS):
            logger.info(f"🤖 Teste Model {model_idx + 1}/4: {model_id}")
            
            for mine_idx, mine in enumerate(self.QUEBEC_MINES):
                logger.info(f"⛏️ Mine {mine_idx + 1}/3: {mine.name}")
                
                # 5 Runs für diese Mine
                for run in range(1, 6):
                    test_number = (model_idx * 15) + (mine_idx * 5) + run
                    self.progress.current_test = f"{model_id} {mine.name} Run {run}"
                    
                    logger.info(f"🔄 Test {test_number}/60: {self.progress.current_test}")
                    
                    # Führe Test durch mit Retry-Logic
                    success = await self._execute_single_test_with_retry(model_id, mine, run)
                    
                    self.progress.completed_tests += 1
                    if success:
                        self.progress.successful_tests += 1
                    else:
                        self.progress.failed_tests += 1
                    
                    # Progress Update
                    progress_percent = (self.progress.completed_tests / self.progress.total_tests) * 100
                    logger.info(f"📈 Progress: {progress_percent:.1f}% ({self.progress.completed_tests}/60)")
                    
                    # Rate-Limiting Pause
                    await asyncio.sleep(2)
                
                # Pause zwischen Minen
                logger.info(f"⏸️ Pause zwischen Minen (3s)...")
                await asyncio.sleep(3)
            
            # Pause zwischen Models
            logger.info(f"⏸️ Pause zwischen Models (5s)...")
            await asyncio.sleep(5)
        
        logger.info(f"🏆 ALLE 60 TESTS ABGESCHLOSSEN!")
        logger.info(f"✅ Erfolgreiche: {self.progress.successful_tests}")
        logger.info(f"❌ Fehlgeschlagene: {self.progress.failed_tests}")
    
    async def _execute_single_test_with_retry(self, model_id: str, mine: TestMine, run_number: int) -> bool:
        """
        Führt einen einzelnen Test mit 3-fach Retry-Logic durch
        
        Returns:
            True wenn erfolgreich, False wenn alle 3 Versuche fehlschlagen
        """
        max_retries = 3
        
        for attempt in range(1, max_retries + 1):
            try:
                logger.debug(f"🔄 Versuch {attempt}/{max_retries}: {model_id} {mine.name} Run {run_number}")
                
                # Führe Test durch (nutzt Framework Funktion)
                result = await self.framework._test_single_run(model_id, mine, run_number)
                
                # Speichere Ergebnis
                self.test_results.append(result)
                
                if result.success:
                    logger.debug(f"✅ Erfolg auf Versuch {attempt}: {result.fields_found} Felder gefunden")
                    return True
                else:
                    logger.warning(f"⚠️ Versuch {attempt} fehlgeschlagen: {result.error}")
                    if attempt < max_retries:
                        await asyncio.sleep(5)  # Retry-Delay
                    
            except Exception as e:
                logger.error(f"💥 Exception auf Versuch {attempt}: {e}")
                if attempt < max_retries:
                    await asyncio.sleep(5)  # Exception-Delay
        
        # Alle 3 Versuche fehlgeschlagen
        logger.error(f"❌ FINAL FAILURE nach {max_retries} Versuchen: {model_id} {mine.name} Run {run_number}")
        
        # Erstelle Failure-Result für Database-Konsistenz
        failure_result = TestResult(
            model_id=model_id,
            mine_name=mine.name,
            run_number=run_number,
            success=False,
            response_time_ms=0.0,
            fields_found=0,
            sources_count=0,
            data_quality=0.0,
            structured_data={},
            error="Failed after 3 retry attempts",
            timestamp=datetime.now()
        )
        self.test_results.append(failure_result)
        
        return False
    
    async def _validate_database_entries(self) -> Dict[str, Any]:
        """
        Validiert dass ALLE 60 Tests in der Database gespeichert wurden
        
        Returns:
            Validation results mit detaillierter Analyse
        """
        logger.info("🔍 Validiere Database-Einträge für alle 60 Grok Tests...")
        
        validation_result = {
            "timestamp": datetime.now().isoformat(),
            "expected_entries": 60,
            "found_entries": 0,
            "missing_entries": [],
            "success": False,
            "model_breakdown": {},
            "mine_breakdown": {}
        }
        
        try:
            with db_manager.get_session() as session:
                # Zähle alle Grok-Einträge
                total_grok_entries = session.query(ModelStatistics).filter(
                    ModelStatistics.model_id.like('grok:%')
                ).count()
                
                validation_result["found_entries"] = total_grok_entries
                logger.info(f"📊 {total_grok_entries} Grok-Einträge in Database gefunden")
                
                # Detaillierte Analyse pro Model
                for model_id in self.GROK_MODELS:
                    model_entries = session.query(ModelStatistics).filter_by(
                        model_id=model_id
                    ).count()
                    
                    validation_result["model_breakdown"][model_id] = model_entries
                    
                    if model_entries != 15:  # 3 mines × 5 runs = 15
                        logger.warning(f"⚠️ {model_id}: {model_entries}/15 Einträge")
                    else:
                        logger.info(f"✅ {model_id}: {model_entries}/15 Einträge komplett")
                
                # Detaillierte Analyse pro Mine
                for mine in self.QUEBEC_MINES:
                    mine_entries = session.query(ModelStatistics).filter(
                        ModelStatistics.model_id.like('grok:%'),
                        ModelStatistics.mine_name == mine.name
                    ).count()
                    
                    validation_result["mine_breakdown"][mine.name] = mine_entries
                    
                    if mine_entries != 20:  # 4 models × 5 runs = 20
                        logger.warning(f"⚠️ {mine.name}: {mine_entries}/20 Einträge")
                    else:
                        logger.info(f"✅ {mine.name}: {mine_entries}/20 Einträge komplett")
                
                # Prüfe fehlende run_numbers
                for model_id in self.GROK_MODELS:
                    for mine in self.QUEBEC_MINES:
                        entries = session.query(ModelStatistics).filter_by(
                            model_id=model_id,
                            mine_name=mine.name
                        ).all()
                        
                        run_numbers = {entry.run_number for entry in entries}
                        expected_runs = {1, 2, 3, 4, 5}
                        missing_runs = expected_runs - run_numbers
                        
                        if missing_runs:
                            missing_key = f"{model_id} {mine.name}"
                            validation_result["missing_entries"].append({
                                "model": model_id,
                                "mine": mine.name,
                                "missing_runs": list(missing_runs),
                                "found_runs": list(run_numbers)
                            })
                
                # Erfolgs-Status bestimmen
                validation_result["success"] = (
                    validation_result["found_entries"] == 60 and
                    len(validation_result["missing_entries"]) == 0
                )
                
                if validation_result["success"]:
                    logger.info("🎉 ✅ VALIDATION SUCCESS: Alle 60 Grok-Tests in Database!")
                else:
                    logger.error(f"❌ VALIDATION FAILED: {len(validation_result['missing_entries'])} fehlende Einträge")
                
        except Exception as e:
            logger.error(f"💥 Database validation error: {e}")
            validation_result["error"] = str(e)
        
        return validation_result
    
    async def _create_final_report(self, validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Erstellt finalen umfassenden Report"""
        elapsed_time = (datetime.now() - self.progress.start_time).total_seconds()
        
        # Erfolgs-Status bestimmen
        all_tests_completed = self.progress.completed_tests == 60
        database_valid = validation_result.get("success", False)
        overall_success = all_tests_completed and database_valid
        
        report = {
            "agent_type": "Grok Comprehensive Test Agent",
            "version": "1.0",
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            
            "test_execution": {
                "planned_tests": 60,
                "completed_tests": self.progress.completed_tests,
                "successful_tests": self.progress.successful_tests,
                "failed_tests": self.progress.failed_tests,
                "execution_time_seconds": elapsed_time,
                "tests_per_minute": (self.progress.completed_tests / elapsed_time) * 60 if elapsed_time > 0 else 0
            },
            
            "grok_models_tested": {
                model_id: {
                    "tests_executed": len([r for r in self.test_results if r.model_id == model_id]),
                    "tests_successful": len([r for r in self.test_results if r.model_id == model_id and r.success]),
                    "avg_fields_found": sum(r.fields_found for r in self.test_results if r.model_id == model_id and r.success) / 
                                     len([r for r in self.test_results if r.model_id == model_id and r.success]) 
                                     if any(r.model_id == model_id and r.success for r in self.test_results) else 0,
                    "avg_response_time": sum(r.response_time_ms for r in self.test_results if r.model_id == model_id and r.success) / 
                                       len([r for r in self.test_results if r.model_id == model_id and r.success]) 
                                       if any(r.model_id == model_id and r.success for r in self.test_results) else 0
                }
                for model_id in self.GROK_MODELS
            },
            
            "mine_performance": {
                mine.name: {
                    "tests_executed": len([r for r in self.test_results if r.mine_name == mine.name]),
                    "tests_successful": len([r for r in self.test_results if r.mine_name == mine.name and r.success]),
                    "success_rate": len([r for r in self.test_results if r.mine_name == mine.name and r.success]) / 
                                  len([r for r in self.test_results if r.mine_name == mine.name]) 
                                  if any(r.mine_name == mine.name for r in self.test_results) else 0
                }
                for mine in self.QUEBEC_MINES
            },
            
            "database_validation": validation_result,
            
            "final_status": {
                "all_tests_completed": all_tests_completed,
                "database_valid": database_valid,
                "overall_success": overall_success,
                "status_message": "✅ 60/60 Grok tests completed, all in database" if overall_success 
                                else f"❌ Issues found: Tests={self.progress.completed_tests}/60, DB_Valid={database_valid}"
            }
        }
        
        # Top Performer ermitteln
        if self.test_results:
            successful_results = [r for r in self.test_results if r.success]
            if successful_results:
                best_model = max(
                    self.GROK_MODELS,
                    key=lambda m: sum(r.fields_found for r in successful_results if r.model_id == m)
                )
                report["top_performer"] = {
                    "model": best_model,
                    "total_fields": sum(r.fields_found for r in successful_results if r.model_id == best_model),
                    "success_rate": len([r for r in successful_results if r.model_id == best_model]) / 15  # 15 tests per model
                }
        
        return report
    
    def _create_failure_report(self, error_message: str) -> Dict[str, Any]:
        """Erstellt Failure-Report bei kritischen Fehlern"""
        return {
            "agent_type": "Grok Comprehensive Test Agent",
            "version": "1.0",
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "success": False,
            "error": error_message,
            "progress_at_failure": {
                "completed_tests": self.progress.completed_tests,
                "successful_tests": self.progress.successful_tests,
                "failed_tests": self.progress.failed_tests
            },
            "final_status": {
                "all_tests_completed": False,
                "database_valid": False,
                "overall_success": False,
                "status_message": f"❌ FAILURE: {error_message}"
            }
        }

# Main execution function
async def main():
    """Hauptfunktion für Grok Comprehensive Tests"""
    agent = GrokComprehensiveTestAgent()
    
    print("🚀 GROK COMPREHENSIVE TEST AGENT v1.0")
    print("=" * 60)
    print("🎯 ZIEL: 60 Tests (4 Grok models × 3 mines × 5 runs)")
    print("📊 EXPECTED: ✅ 60/60 Grok tests completed, all in database")
    print("=" * 60)
    
    try:
        result = await agent.run_comprehensive_grok_tests()
        
        # Finaler Status
        print("\n" + "=" * 60)
        print("🏁 GROK COMPREHENSIVE TEST RESULTS")
        print("=" * 60)
        
        final_status = result.get("final_status", {})
        status_message = final_status.get("status_message", "Unknown status")
        
        print(f"STATUS: {status_message}")
        
        if final_status.get("overall_success", False):
            print("🎉 SUCCESS: Alle Grok Tests erfolgreich abgeschlossen!")
        else:
            print("❌ ISSUES: Nicht alle Tests erfolgreich")
        
        test_exec = result.get("test_execution", {})
        print(f"TESTS: {test_exec.get('completed_tests', 0)}/60 completed")
        print(f"SUCCESS: {test_exec.get('successful_tests', 0)} tests")
        print(f"TIME: {test_exec.get('execution_time_seconds', 0):.1f}s")
        
        return result
        
    except Exception as e:
        print(f"💥 CRITICAL ERROR: {e}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    asyncio.run(main())