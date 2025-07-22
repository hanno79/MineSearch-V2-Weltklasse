"""
Author: rahn
Datum: 13.07.2025
Version: 1.0
Beschreibung: Spezialisierter Test-Agent für VOLLSTÄNDIGE OpenAI Models Tests
"""

import logging
import asyncio
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from provider_test_framework import ProviderTestFramework, TestMine, TestResult
from model_benchmark_service import ModelBenchmarkService
from database import db_manager
from database.models import ModelStatistics

logger = logging.getLogger(__name__)


@dataclass
class OpenAITestConfig:
    """Konfiguration für OpenAI Tests"""
    models_to_test: List[str]
    mines_to_test: List[TestMine]
    runs_per_mine: int
    max_retries: int = 3
    retry_delay: float = 5.0
    timeout_per_test: float = 180.0  # 3 Minuten pro Test


class OpenAITestAgent:
    """Spezialisierter Agent für vollständige OpenAI Model Tests"""
    
    # ALLE OpenAI Models die getestet werden sollen
    OPENAI_MODELS = [
        "openai:o3-deep-research",
        "openai:gpt-4.1", 
        "openai:o3",
        "openai:o4-mini"
    ]
    
    # Quebec Test-Minen (gleiche wie ProviderTestFramework)
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
        self.test_framework = ProviderTestFramework()
        self.benchmark_service = ModelBenchmarkService()
        
        # Test-Session Tracking
        self.session_id = f"openai_full_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.start_time = None
        self.progress_tracker = {
            'total_tests': 0,
            'completed_tests': 0,
            'successful_tests': 0,
            'failed_tests': 0,
            'current_model': None,
            'current_mine': None,
            'current_run': None
        }
        
        # Results Storage
        self.test_results = []
        self.failed_tests = []
    
    async def run_complete_openai_tests(self) -> Dict[str, Any]:
        """
        Führt ALLE 60 OpenAI Tests durch (4 models × 3 mines × 5 runs)
        
        Returns:
            Vollständiger Test-Report mit Database-Validierung
        """
        self.start_time = datetime.now()
        logger.info(f"[OPENAI-AGENT] 🚀 Starte vollständige OpenAI Tests - Session: {self.session_id}")
        
        # Initialisiere Progress-Tracker
        self.progress_tracker['total_tests'] = len(self.OPENAI_MODELS) * len(self.QUEBEC_MINES) * 5
        logger.info(f"[OPENAI-AGENT] 📊 {self.progress_tracker['total_tests']} Tests geplant")
        
        try:
            # 1. Validiere OpenAI Model-Verfügbarkeit
            available_models = await self._validate_openai_models()
            if not available_models:
                return {
                    "success": False,
                    "error": "Keine OpenAI Models verfügbar",
                    "session_id": self.session_id
                }
            
            logger.info(f"[OPENAI-AGENT] ✅ {len(available_models)} OpenAI Models verfügbar")
            
            # 2. Führe systematische Tests durch
            await self._execute_all_openai_tests(available_models)
            
            # 3. Validiere Database-Konsistenz
            db_validation = await self._validate_database_entries()
            
            # 4. Erstelle finalen Report
            final_report = await self._create_final_report(db_validation)
            
            duration = (datetime.now() - self.start_time).total_seconds()
            logger.info(f"[OPENAI-AGENT] 🎯 Alle Tests abgeschlossen in {duration:.1f}s")
            
            return final_report
            
        except Exception as e:
            logger.error(f"[OPENAI-AGENT] ❌ Kritischer Fehler: {e}")
            return {
                "success": False,
                "error": str(e),
                "session_id": self.session_id,
                "partial_results": self.test_results,
                "progress": self.progress_tracker
            }
    
    async def _validate_openai_models(self) -> List[str]:
        """Validiert verfügbare OpenAI Models"""
        available_models = []
        
        for model_id in self.OPENAI_MODELS:
            try:
                # Prüfe ob Model in Provider-Registry verfügbar
                if self.test_framework.provider_registry.is_model_available(model_id):
                    available_models.append(model_id)
                    logger.info(f"[OPENAI-AGENT] ✅ {model_id} verfügbar")
                else:
                    logger.warning(f"[OPENAI-AGENT] ⚠️  {model_id} nicht in Registry gefunden")
            except Exception as e:
                logger.error(f"[OPENAI-AGENT] ❌ Fehler bei {model_id}: {e}")
        
        return available_models
    
    async def _execute_all_openai_tests(self, model_ids: List[str]):
        """Führt alle OpenAI Tests mit Retry-Logic durch"""
        
        for model_index, model_id in enumerate(model_ids):
            self.progress_tracker['current_model'] = model_id
            logger.info(f"[OPENAI-AGENT] 🔄 Teste Model {model_id} ({model_index + 1}/{len(model_ids)})")
            
            for mine_index, mine in enumerate(self.QUEBEC_MINES):
                self.progress_tracker['current_mine'] = mine.name
                logger.info(f"[OPENAI-AGENT] ⛏️  Mine: {mine.name} ({mine_index + 1}/{len(self.QUEBEC_MINES)})")
                
                # 5 Runs für diese Model-Mine Kombination
                for run in range(1, 6):
                    self.progress_tracker['current_run'] = run
                    
                    # Test mit Retry-Logic durchführen
                    success = await self._execute_single_test_with_retry(model_id, mine, run)
                    
                    # Progress Update
                    self.progress_tracker['completed_tests'] += 1
                    if success:
                        self.progress_tracker['successful_tests'] += 1
                    else:
                        self.progress_tracker['failed_tests'] += 1
                    
                    # Progress-Logging
                    progress_pct = (self.progress_tracker['completed_tests'] / self.progress_tracker['total_tests']) * 100
                    logger.info(f"[OPENAI-AGENT] 📈 Progress: {progress_pct:.1f}% "
                              f"({self.progress_tracker['completed_tests']}/{self.progress_tracker['total_tests']}) "
                              f"- {model_id} {mine.name} Run {run}/5 {'✅' if success else '❌'}")
                    
                    # Kurze Pause zwischen Tests
                    await asyncio.sleep(2)
                
                # Pause zwischen Minen
                await asyncio.sleep(3)
            
            # Pause zwischen Models
            await asyncio.sleep(5)
        
        logger.info(f"[OPENAI-AGENT] 🎉 Alle {self.progress_tracker['completed_tests']} Tests abgeschlossen!")
    
    async def _execute_single_test_with_retry(self, model_id: str, mine: TestMine, run_number: int) -> bool:
        """Führt einzelnen Test mit Retry-Logic durch"""
        
        for attempt in range(1, 4):  # Max 3 Versuche
            try:
                # Verwende ProviderTestFramework._test_single_run für Konsistenz
                result = await asyncio.wait_for(
                    self.test_framework._test_single_run(model_id, mine, run_number),
                    timeout=180.0  # 3 Minuten Timeout
                )
                
                # Speichere Ergebnis
                self.test_results.append(result)
                
                if result.success:
                    logger.debug(f"[OPENAI-AGENT] ✅ {model_id} {mine.name} Run {run_number} - Erfolg")
                    return True
                else:
                    logger.warning(f"[OPENAI-AGENT] ⚠️  {model_id} {mine.name} Run {run_number} - Fehlgeschlagen")
                    if attempt < 3:
                        logger.info(f"[OPENAI-AGENT] 🔄 Retry {attempt + 1}/3 in 5s...")
                        await asyncio.sleep(5)
                        continue
                    else:
                        # Nach 3 Versuchen als Failed markieren
                        self.failed_tests.append({
                            'model_id': model_id,
                            'mine_name': mine.name,
                            'run_number': run_number,
                            'error': result.error or 'Test failed after 3 attempts',
                            'attempts': 3
                        })
                        return False
                        
            except asyncio.TimeoutError:
                logger.error(f"[OPENAI-AGENT] ⏰ Timeout bei {model_id} {mine.name} Run {run_number} (Versuch {attempt}/3)")
                if attempt < 3:
                    await asyncio.sleep(5)
                    continue
                else:
                    self.failed_tests.append({
                        'model_id': model_id,
                        'mine_name': mine.name,
                        'run_number': run_number,
                        'error': 'Timeout after 3 attempts',
                        'attempts': 3
                    })
                    return False
                    
            except Exception as e:
                logger.error(f"[OPENAI-AGENT] ❌ Exception bei {model_id} {mine.name} Run {run_number}: {e}")
                if attempt < 3:
                    await asyncio.sleep(5)
                    continue
                else:
                    self.failed_tests.append({
                        'model_id': model_id,
                        'mine_name': mine.name,
                        'run_number': run_number,
                        'error': str(e),
                        'attempts': 3
                    })
                    return False
        
        return False
    
    async def _validate_database_entries(self) -> Dict[str, Any]:
        """Validiert dass alle Tests in Database gespeichert wurden"""
        logger.info("[OPENAI-AGENT] 🔍 Validiere Database-Einträge...")
        
        validation_results = {
            "timestamp": datetime.now().isoformat(),
            "expected_total": 60,  # 4 models × 3 mines × 5 runs
            "found_entries": {},
            "missing_entries": [],
            "database_consistent": False,
            "total_found": 0
        }
        
        try:
            with db_manager.get_session() as session:
                for model_id in self.OPENAI_MODELS:
                    model_entries = {}
                    
                    for mine in self.QUEBEC_MINES:
                        # Prüfe alle 5 Runs für diese Model-Mine Kombination
                        entries = session.query(ModelStatistics).filter_by(
                            model_id=model_id,
                            mine_name=mine.name
                        ).all()
                        
                        model_entries[mine.name] = {
                            'expected_runs': 5,
                            'found_runs': len(entries),
                            'run_numbers': [e.run_number for e in entries],
                            'complete': len(entries) == 5 and set(e.run_number for e in entries) == {1, 2, 3, 4, 5}
                        }
                        
                        # Check for missing runs
                        if len(entries) < 5:
                            missing_runs = {1, 2, 3, 4, 5} - set(e.run_number for e in entries)
                            for missing_run in missing_runs:
                                validation_results["missing_entries"].append(
                                    f"{model_id} - {mine.name} - Run {missing_run}"
                                )
                    
                    validation_results["found_entries"][model_id] = model_entries
                
                # Berechne Gesamt-Statistik
                total_found = 0
                for model_data in validation_results["found_entries"].values():
                    for mine_data in model_data.values():
                        total_found += mine_data['found_runs']
                
                validation_results["total_found"] = total_found
                validation_results["database_consistent"] = (
                    total_found == 60 and len(validation_results["missing_entries"]) == 0
                )
                
                logger.info(f"[OPENAI-AGENT] 📊 Database-Validierung: {total_found}/60 Einträge gefunden")
                
                if validation_results["database_consistent"]:
                    logger.info("[OPENAI-AGENT] ✅ Database ist vollständig konsistent!")
                else:
                    logger.warning(f"[OPENAI-AGENT] ⚠️  Database-Inkonsistenzen: {len(validation_results['missing_entries'])} fehlende Einträge")
                
        except Exception as e:
            logger.error(f"[OPENAI-AGENT] ❌ Fehler bei Database-Validierung: {e}")
            validation_results["error"] = str(e)
        
        return validation_results
    
    async def _create_final_report(self, db_validation: Dict[str, Any]) -> Dict[str, Any]:
        """Erstellt finalen Test-Report"""
        
        # Berechne Test-Statistiken
        total_tests = len(self.test_results)
        successful_tests = len([r for r in self.test_results if r.success])
        success_rate = successful_tests / total_tests if total_tests > 0 else 0
        
        # Model-Performance berechnen
        model_performance = {}
        for model_id in self.OPENAI_MODELS:
            model_results = [r for r in self.test_results if r.model_id == model_id]
            model_successful = [r for r in model_results if r.success]
            
            if model_results:
                model_performance[model_id] = {
                    "total_tests": len(model_results),
                    "successful_tests": len(model_successful),
                    "success_rate": len(model_successful) / len(model_results),
                    "avg_response_time": sum(r.response_time_ms for r in model_successful) / len(model_successful) if model_successful else 0,
                    "avg_fields_found": sum(r.fields_found for r in model_successful) / len(model_successful) if model_successful else 0,
                    "avg_data_quality": sum(r.data_quality for r in model_successful) / len(model_successful) if model_successful else 0
                }
        
        # Finale Report-Struktur
        final_report = {
            "success": True,
            "session_id": self.session_id,
            "test_type": "COMPLETE_OPENAI_VALIDATION",
            "summary": {
                "total_tests_planned": 60,
                "total_tests_executed": total_tests,
                "successful_tests": successful_tests,
                "failed_tests": len(self.failed_tests),
                "overall_success_rate": success_rate,
                "test_duration_seconds": (datetime.now() - self.start_time).total_seconds(),
                "timestamp": datetime.now().isoformat()
            },
            "model_performance": model_performance,
            "database_validation": db_validation,
            "failed_tests": self.failed_tests,
            "progress_tracker": self.progress_tracker,
            "validation_status": "✅ 60/60 OpenAI tests completed, all in database" if db_validation.get("database_consistent") else f"⚠️ {db_validation.get('total_found', 0)}/60 tests in database"
        }
        
        # Log Final Results
        logger.info(f"[OPENAI-AGENT] 🎯 FINAL RESULTS:")
        logger.info(f"[OPENAI-AGENT]   Tests Executed: {total_tests}/60")
        logger.info(f"[OPENAI-AGENT]   Success Rate: {success_rate:.1%}")
        logger.info(f"[OPENAI-AGENT]   Database Entries: {db_validation.get('total_found', 0)}/60")
        logger.info(f"[OPENAI-AGENT]   Database Consistent: {db_validation.get('database_consistent', False)}")
        
        if db_validation.get("database_consistent"):
            logger.info("[OPENAI-AGENT] ✅ 60/60 OpenAI tests completed, all in database")
        else:
            logger.warning(f"[OPENAI-AGENT] ⚠️ Database validation failed - missing entries found")
        
        return final_report


# Standalone-Funktion für direkten Import
async def run_openai_full_tests() -> Dict[str, Any]:
    """
    Führt vollständige OpenAI Tests durch
    
    Returns:
        Test-Report mit Database-Validierung
    """
    agent = OpenAITestAgent()
    return await agent.run_complete_openai_tests()


if __name__ == "__main__":
    # Direkter Test-Aufruf
    import asyncio
    
    async def main():
        agent = OpenAITestAgent()
        result = await agent.run_complete_openai_tests()
        print(f"OpenAI Tests Result: {result.get('validation_status', 'Unknown')}")
    
    asyncio.run(main())