"""
Author: rahn
Datum: 13.07.2025
Version: 1.0
Beschreibung: Vollständiger Test-Agent für ALLE Anthropic Models (45 Tests total)
"""

import logging
import asyncio
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import json

from provider_test_framework import ProviderTestFramework, TestMine, TestResult
from model_benchmark_service import ModelBenchmarkService
from database import db_manager
from database.models import ModelStatistics, FieldStatistics
from config.providers import PROVIDERS_CONFIG

logger = logging.getLogger(__name__)


@dataclass
class AnthropicTestConfig:
    """Konfiguration für Anthropic Tests"""
    models: List[str]
    mines: List[TestMine]
    runs_per_mine: int
    total_tests: int


class AnthropicCompleteTestAgent:
    """Spezialisierter Test-Agent für vollständige Anthropic Model-Tests"""
    
    # Die 3 Anthropic Models zu testen
    ANTHROPIC_MODELS = [
        "anthropic:claude-sonnet-4",
        "anthropic:claude-opus-4", 
        "anthropic:claude-3.7-sonnet"
    ]
    
    # Quebec Test-Minen (gleich wie im ProviderTestFramework)
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
        self.provider_framework = ProviderTestFramework()
        self.benchmark_service = ModelBenchmarkService()
        
        # Test-Tracking
        self.test_config = AnthropicTestConfig(
            models=self.ANTHROPIC_MODELS,
            mines=self.QUEBEC_MINES,
            runs_per_mine=5,
            total_tests=len(self.ANTHROPIC_MODELS) * len(self.QUEBEC_MINES) * 5  # 3 × 3 × 5 = 45
        )
        
        self.completed_tests = 0
        self.test_results = []
        self.failed_tests = []
        self.start_time = None
        
    async def run_complete_anthropic_tests(self) -> Dict[str, Any]:
        """
        Führt ALLE 45 Anthropic Tests durch: 3 models × 3 mines × 5 runs
        
        Returns:
            Vollständiger Test-Report mit Database-Validierung
        """
        self.start_time = datetime.now()
        logger.info(f"[ANTHROPIC-AGENT] 🚀 Starte VOLLSTÄNDIGE Anthropic Tests: {self.test_config.total_tests} Tests")
        
        try:
            # 1. Validiere Anthropic Provider-Verfügbarkeit
            available_models = await self._validate_anthropic_availability()
            
            if not available_models:
                return {
                    "success": False,
                    "error": "Keine Anthropic Modelle verfügbar - API-Key oder Konfiguration prüfen",
                    "total_tests": 0
                }
            
            logger.info(f"[ANTHROPIC-AGENT] ✅ {len(available_models)} Anthropic Modelle verfügbar")
            
            # 2. Führe alle 45 Tests systematisch durch
            await self._execute_all_anthropic_tests(available_models)
            
            # 3. Validiere Database-Konsistenz
            validation_results = await self._validate_database_entries()
            
            # 4. Erstelle finalen Report
            final_report = await self._create_final_report(validation_results)
            
            # 5. Log final status
            elapsed_time = (datetime.now() - self.start_time).total_seconds()
            logger.info(f"[ANTHROPIC-AGENT] ✅ VOLLSTÄNDIG: {self.completed_tests}/{self.test_config.total_tests} Tests in {elapsed_time:.1f}s")
            
            return final_report
            
        except Exception as e:
            logger.error(f"[ANTHROPIC-AGENT] 💥 Kritischer Fehler: {e}")
            return {
                "success": False,
                "error": str(e),
                "completed_tests": self.completed_tests,
                "total_tests": self.test_config.total_tests,
                "partial_results": self.test_results
            }
    
    async def _validate_anthropic_availability(self) -> List[str]:
        """Validiert dass alle Anthropic Modelle verfügbar sind"""
        available_models = []
        
        # Prüfe Anthropic Provider Konfiguration
        anthropic_config = PROVIDERS_CONFIG.get('anthropic', {})
        
        if not anthropic_config.get('enabled', False):
            logger.error("[ANTHROPIC-AGENT] ❌ Anthropic Provider ist deaktiviert")
            return []
        
        if not anthropic_config.get('api_key'):
            logger.error("[ANTHROPIC-AGENT] ❌ ANTHROPIC_API_KEY fehlt")
            return []
        
        # Validiere jedes Modell
        configured_models = anthropic_config.get('models', {})
        
        for model_id in self.ANTHROPIC_MODELS:
            model_name = model_id.split(':')[1]
            
            if model_name in configured_models:
                available_models.append(model_id)
                logger.info(f"[ANTHROPIC-AGENT] ✅ {model_id} verfügbar")
            else:
                logger.warning(f"[ANTHROPIC-AGENT] ⚠️ {model_id} nicht in Konfiguration")
        
        return available_models
    
    async def _execute_all_anthropic_tests(self, available_models: List[str]):
        """Führt alle 45 Tests systematisch durch"""
        
        for model_idx, model_id in enumerate(available_models):
            logger.info(f"[ANTHROPIC-AGENT] 🔍 Teste {model_id} ({model_idx + 1}/{len(available_models)})")
            
            for mine_idx, mine in enumerate(self.test_config.mines):
                logger.info(f"[ANTHROPIC-AGENT] ⛏️ Mine: {mine.name} ({mine_idx + 1}/{len(self.test_config.mines)})")
                
                # Führe 5 Runs für diese Kombination durch
                for run in range(1, self.test_config.runs_per_mine + 1):
                    await self._execute_single_test_with_retry(model_id, mine, run)
                    
                    # Progress-Update
                    progress = (self.completed_tests / self.test_config.total_tests) * 100
                    logger.info(f"[ANTHROPIC-AGENT] 📊 Progress: {progress:.1f}% ({self.completed_tests}/{self.test_config.total_tests})")
                    
                    # Kurze Pause zwischen Tests
                    await asyncio.sleep(2)
                
                # Pause zwischen Minen
                await asyncio.sleep(5)
            
            # Pause zwischen Modellen  
            await asyncio.sleep(10)
    
    async def _execute_single_test_with_retry(self, model_id: str, mine: TestMine, run_number: int):
        """Führt einen einzelnen Test mit 3-Versuch Retry-Logic durch"""
        max_retries = 3
        retry_delay = 10
        
        for attempt in range(max_retries):
            try:
                logger.info(f"[ANTHROPIC-AGENT] 🧪 {model_id} - {mine.name} - Run {run_number} (Versuch {attempt + 1})")
                
                # Nutze das ProviderTestFramework für einzelne Tests
                result = await self.provider_framework._test_single_run(model_id, mine, run_number)
                
                # Test erfolgreich
                self.test_results.append(result)
                self.completed_tests += 1
                
                if result.success:
                    logger.info(f"[ANTHROPIC-AGENT] ✅ {model_id} {mine.name} Run {run_number}: {result.fields_found} Felder gefunden")
                else:
                    logger.warning(f"[ANTHROPIC-AGENT] ❌ {model_id} {mine.name} Run {run_number}: Fehlgeschlagen")
                
                return  # Erfolgreich, beende Retry-Loop
                
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"[ANTHROPIC-AGENT] 🔄 Retry {attempt + 1}/{max_retries} für {model_id} {mine.name} Run {run_number}: {e}")
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    # Finaler Fehler nach allen Versuchen
                    logger.error(f"[ANTHROPIC-AGENT] 💥 FINAL FAIL {model_id} {mine.name} Run {run_number}: {e}")
                    
                    # Erstelle Fehler-Result
                    failed_result = TestResult(
                        model_id=model_id,
                        mine_name=mine.name,
                        run_number=run_number,
                        success=False,
                        response_time_ms=0.0,
                        fields_found=0,
                        sources_count=0,
                        data_quality=0.0,
                        structured_data={},
                        error=str(e),
                        timestamp=datetime.now()
                    )
                    
                    self.test_results.append(failed_result)
                    self.failed_tests.append({
                        "model_id": model_id,
                        "mine_name": mine.name,
                        "run_number": run_number,
                        "error": str(e)
                    })
                    self.completed_tests += 1
    
    async def _validate_database_entries(self) -> Dict[str, Any]:
        """Validiert dass alle 45 Tests in der Database gespeichert wurden"""
        validation_results = {
            "timestamp": datetime.now().isoformat(),
            "expected_total": self.test_config.total_tests,
            "models_expected": len(self.test_config.models),
            "mines_expected": len(self.test_config.mines),
            "runs_per_mine": self.test_config.runs_per_mine,
            "database_entries": {},
            "missing_entries": [],
            "validation_passed": False
        }
        
        try:
            with db_manager.get_session() as session:
                total_db_entries = 0
                
                for model_id in self.test_config.models:
                    model_entries = {}
                    
                    for mine in self.test_config.mines:
                        # Hole alle Einträge für diese Kombination
                        entries = session.query(ModelStatistics).filter_by(
                            model_id=model_id,
                            mine_name=mine.name
                        ).all()
                        
                        entry_count = len(entries)
                        total_db_entries += entry_count
                        model_entries[mine.name] = {
                            "entries_found": entry_count,
                            "expected_runs": self.test_config.runs_per_mine,
                            "run_numbers": [e.run_number for e in entries],
                            "missing_runs": []
                        }
                        
                        # Prüfe auf fehlende Run-Nummern
                        expected_runs = set(range(1, self.test_config.runs_per_mine + 1))
                        actual_runs = set(e.run_number for e in entries)
                        missing_runs = expected_runs - actual_runs
                        
                        if missing_runs:
                            model_entries[mine.name]["missing_runs"] = list(missing_runs)
                            validation_results["missing_entries"].extend([
                                f"{model_id} - {mine.name} - Run {run}" for run in missing_runs
                            ])
                        
                        # Log Details
                        if entry_count == self.test_config.runs_per_mine:
                            logger.info(f"[ANTHROPIC-AGENT] ✅ {model_id} - {mine.name}: {entry_count}/5 entries")
                        else:
                            logger.warning(f"[ANTHROPIC-AGENT] ❌ {model_id} - {mine.name}: {entry_count}/5 entries (Missing: {missing_runs})")
                    
                    validation_results["database_entries"][model_id] = model_entries
                
                # Gesamtvalidierung
                validation_results["total_db_entries"] = total_db_entries
                validation_results["validation_passed"] = (
                    total_db_entries == self.test_config.total_tests and 
                    len(validation_results["missing_entries"]) == 0
                )
                
                if validation_results["validation_passed"]:
                    logger.info(f"[ANTHROPIC-AGENT] ✅ DATABASE VALIDATION PASSED: {total_db_entries}/45 entries")
                else:
                    logger.error(f"[ANTHROPIC-AGENT] ❌ DATABASE VALIDATION FAILED: {total_db_entries}/45 entries, {len(validation_results['missing_entries'])} missing")
                
        except Exception as e:
            validation_results["error"] = str(e)
            logger.error(f"[ANTHROPIC-AGENT] 💥 Database validation error: {e}")
        
        return validation_results
    
    async def _create_final_report(self, validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Erstellt finalen umfassenden Report"""
        
        # Basis-Statistiken
        successful_tests = len([r for r in self.test_results if r.success])
        
        # Performance-Analyse pro Modell
        model_performance = {}
        for model_id in self.test_config.models:
            model_results = [r for r in self.test_results if r.model_id == model_id]
            model_successful = [r for r in model_results if r.success]
            
            if model_results:
                model_performance[model_id] = {
                    "total_tests": len(model_results),
                    "successful_tests": len(model_successful),
                    "success_rate": len(model_successful) / len(model_results),
                    "avg_fields_found": sum(r.fields_found for r in model_successful) / len(model_successful) if model_successful else 0,
                    "avg_response_time": sum(r.response_time_ms for r in model_successful) / len(model_successful) if model_successful else 0,
                    "avg_data_quality": sum(r.data_quality for r in model_successful) / len(model_successful) if model_successful else 0
                }
        
        # Top-Performer
        top_performers = sorted(
            model_performance.items(),
            key=lambda x: (x[1]["success_rate"], x[1]["avg_fields_found"]),
            reverse=True
        )
        
        # Test-Dauer
        elapsed_time = (datetime.now() - self.start_time).total_seconds()
        
        # Final Report
        final_report = {
            "success": validation_results.get("validation_passed", False),
            "anthropic_test_summary": {
                "total_tests_executed": self.completed_tests,
                "expected_tests": self.test_config.total_tests,
                "successful_tests": successful_tests,
                "failed_tests": len(self.failed_tests),
                "overall_success_rate": successful_tests / self.completed_tests if self.completed_tests > 0 else 0,
                "test_duration_seconds": elapsed_time,
                "tests_per_minute": (self.completed_tests / elapsed_time) * 60 if elapsed_time > 0 else 0
            },
            "model_performance": model_performance,
            "top_anthropic_performers": dict(top_performers),
            "database_validation": validation_results,
            "failed_tests_details": self.failed_tests,
            "completion_status": {
                "all_45_tests_completed": self.completed_tests == 45,
                "all_database_entries_present": validation_results.get("validation_passed", False),
                "ready_for_production": validation_results.get("validation_passed", False) and successful_tests > 35
            },
            "timestamp": datetime.now().isoformat()
        }
        
        # Finale Status-Meldung
        if validation_results.get("validation_passed", False):
            final_status = f"✅ {self.completed_tests}/45 Anthropic tests completed, all in database"
            logger.info(f"[ANTHROPIC-AGENT] {final_status}")
            final_report["final_status"] = final_status
        else:
            missing_count = len(validation_results.get("missing_entries", []))
            final_status = f"❌ {self.completed_tests}/45 tests completed, {missing_count} database entries missing"
            logger.error(f"[ANTHROPIC-AGENT] {final_status}")
            final_report["final_status"] = final_status
        
        return final_report
    
    async def get_anthropic_test_status(self) -> Dict[str, Any]:
        """Holt aktuellen Status der Anthropic Tests"""
        return {
            "completed_tests": self.completed_tests,
            "total_tests": self.test_config.total_tests,
            "progress_percentage": (self.completed_tests / self.test_config.total_tests) * 100,
            "failed_tests_count": len(self.failed_tests),
            "started_at": self.start_time.isoformat() if self.start_time else None,
            "models_config": self.test_config.models,
            "mines_config": [mine.name for mine in self.test_config.mines]
        }


# Hauptfunktion für direkte Ausführung
async def main():
    """Hauptfunktion für direkte Script-Ausführung"""
    
    # Logging konfigurieren
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🚀 ANTHROPIC COMPLETE TEST AGENT v1.0")
    print("=" * 50)
    print("ZIEL: 45 vollständige Tests (3 models × 3 mines × 5 runs)")
    print("MODELS: claude-sonnet-4, claude-opus-4, claude-3.7-sonnet")
    print("MINES: Éléonore, Niobec, LaRonde (Quebec)")
    print("=" * 50)
    
    # Erstelle Agent und führe Tests durch
    agent = AnthropicCompleteTestAgent()
    
    try:
        result = await agent.run_complete_anthropic_tests()
        
        print("\n" + "=" * 50)
        print("🏁 TEST-ERGEBNISSE:")
        print("=" * 50)
        
        if result.get("success"):
            print("✅ ALLE TESTS ERFOLGREICH")
            print(f"📊 {result['final_status']}")
        else:
            print("❌ TESTS UNVOLLSTÄNDIG")
            print(f"❌ Fehler: {result.get('error', 'Unbekannt')}")
        
        # Performance Summary
        summary = result.get("anthropic_test_summary", {})
        print(f"\n📈 PERFORMANCE:")
        print(f"   Tests ausgeführt: {summary.get('total_tests_executed', 0)}/45")
        print(f"   Erfolgsrate: {summary.get('overall_success_rate', 0):.1%}")
        print(f"   Dauer: {summary.get('test_duration_seconds', 0):.1f}s")
        
        # Top-Performer
        top_performers = result.get("top_anthropic_performers", {})
        if top_performers:
            print(f"\n🏆 TOP-PERFORMER:")
            for i, (model_id, perf) in enumerate(list(top_performers.items())[:3]):
                print(f"   {i+1}. {model_id}: {perf['avg_fields_found']:.1f} Felder ({perf['success_rate']:.1%})")
        
        return result
        
    except Exception as e:
        print(f"💥 KRITISCHER FEHLER: {e}")
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    asyncio.run(main())