"""
Author: rahn
Datum: 13.07.2025
Version: 1.0
Beschreibung: Spezialisierter Test-Agent für VOLLSTÄNDIGE Gemini Models Validierung
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
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class GeminiTestSession:
    """Spezialisierte Test-Session für Gemini Models"""
    total_tests: int = 45  # 3 models × 3 mines × 5 runs
    completed_tests: int = 0
    failed_tests: int = 0
    successful_tests: int = 0
    database_entries: int = 0
    start_time: datetime = None
    end_time: datetime = None
    results: List[TestResult] = None


class GeminiTestAgent:
    """
    Spezialisierter Test-Agent für VOLLSTÄNDIGE Gemini Models Validierung
    
    ZIEL: 45/45 Tests durchführen und in Database speichern
    - gemini:gemini-2.5-pro
    - gemini:gemini-2.5-flash  
    - gemini:gemini-2.5-flash-lite
    """
    
    # Gemini Models zu testen
    GEMINI_MODELS = [
        "gemini:gemini-2.5-pro",
        "gemini:gemini-2.5-flash", 
        "gemini:gemini-2.5-flash-lite"
    ]
    
    # Quebec Test-Minen (gleich wie ProviderTestFramework)
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
        self.session = GeminiTestSession()
        self.session.results = []
        
        # Retry-Konfiguration für robuste Tests
        self.max_retries = 3
        self.retry_delay = 5
        
    async def run_comprehensive_gemini_tests(self) -> Dict[str, Any]:
        """
        Führt VOLLSTÄNDIGE Gemini Tests durch - 45 Tests total
        
        Returns:
            Detaillierte Test-Ergebnisse mit Database-Validation
        """
        self.session.start_time = datetime.now()
        logger.info("🚀 [GEMINI-AGENT] Starte VOLLSTÄNDIGE Gemini Models Validierung")
        logger.info(f"📊 [GEMINI-AGENT] Ziel: {self.session.total_tests} Tests (3 Models × 3 Mines × 5 Runs)")
        
        try:
            # 1. Vorab-Validierung der Gemini-Provider
            await self._validate_gemini_availability()
            
            # 2. Führe systematische Tests durch
            await self._execute_all_gemini_tests()
            
            # 3. Validiere Database-Einträge
            await self._validate_database_completeness()
            
            # 4. Erstelle finalen Report
            final_report = await self._create_final_report()
            
            self.session.end_time = datetime.now()
            duration = (self.session.end_time - self.session.start_time).total_seconds()
            
            logger.info(f"✅ [GEMINI-AGENT] Tests abgeschlossen in {duration:.1f}s")
            logger.info(f"📈 [GEMINI-AGENT] Erfolg: {self.session.successful_tests}/{self.session.total_tests}")
            
            return final_report
            
        except Exception as e:
            logger.error(f"💥 [GEMINI-AGENT] Kritischer Fehler: {e}")
            return {
                "success": False,
                "error": str(e),
                "completed_tests": self.session.completed_tests,
                "partial_results": self.session.results
            }
    
    async def _validate_gemini_availability(self) -> bool:
        """Validiert dass alle Gemini Models verfügbar sind"""
        logger.info("🔍 [GEMINI-AGENT] Validiere Gemini Models Verfügbarkeit...")
        
        available_models = await self.test_framework._validate_provider_availability(self.GEMINI_MODELS)
        
        if len(available_models) != len(self.GEMINI_MODELS):
            missing_models = set(self.GEMINI_MODELS) - set(available_models)
            raise Exception(f"Gemini Models nicht verfügbar: {missing_models}")
        
        logger.info(f"✅ [GEMINI-AGENT] Alle {len(available_models)} Gemini Models verfügbar")
        return True
    
    async def _execute_all_gemini_tests(self):
        """Führt ALLE 45 Gemini Tests systematisch durch"""
        logger.info("🎯 [GEMINI-AGENT] Starte systematische Test-Durchführung...")
        
        test_counter = 0
        
        for model_idx, model_id in enumerate(self.GEMINI_MODELS):
            logger.info(f"🔬 [GEMINI-AGENT] Modell {model_id} ({model_idx + 1}/3)")
            
            for mine_idx, mine in enumerate(self.QUEBEC_MINES):
                logger.info(f"⛏️  [GEMINI-AGENT] Mine: {mine.name} ({mine_idx + 1}/3)")
                
                # 5 Runs pro Mine
                for run in range(1, 6):
                    test_counter += 1
                    
                    try:
                        # Führe einzelnen Test durch mit Retry-Mechanismus
                        result = await self._execute_single_test_with_retry(
                            model_id, mine, run, test_counter
                        )
                        
                        self.session.results.append(result)
                        
                        if result.success:
                            self.session.successful_tests += 1
                        else:
                            self.session.failed_tests += 1
                            
                        self.session.completed_tests += 1
                        
                        # Progress-Logging
                        progress = (self.session.completed_tests / self.session.total_tests) * 100
                        logger.info(f"📊 [GEMINI-AGENT] Progress: {progress:.1f}% - Test {test_counter}/45 {'✅' if result.success else '❌'}")
                        
                        # Rate-Limiting zwischen Tests
                        await asyncio.sleep(2)
                        
                    except Exception as e:
                        logger.error(f"💥 [GEMINI-AGENT] Test {test_counter} fehlgeschlagen: {e}")
                        self.session.failed_tests += 1
                        self.session.completed_tests += 1
                
                # Pause zwischen Minen
                await asyncio.sleep(5)
            
            # Pause zwischen Modellen  
            await asyncio.sleep(10)
        
        logger.info(f"🏁 [GEMINI-AGENT] Alle Tests durchgeführt: {self.session.completed_tests}/45")
    
    async def _execute_single_test_with_retry(self, model_id: str, mine: TestMine, 
                                            run_number: int, test_number: int) -> TestResult:
        """
        Führt einzelnen Test mit Retry-Mechanismus durch
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"🔄 [GEMINI-AGENT] Test {test_number}: {model_id} {mine.name} Run {run_number} (Versuch {attempt + 1})")
                
                # Nutze das bewährte ProviderTestFramework für einzelne Tests
                result = await self.test_framework._test_single_run(model_id, mine, run_number)
                
                logger.debug(f"✅ [GEMINI-AGENT] Test {test_number} erfolgreich: {result.fields_found} Felder gefunden")
                return result
                
            except Exception as e:
                last_error = e
                logger.warning(f"⚠️ [GEMINI-AGENT] Test {test_number} Versuch {attempt + 1} fehlgeschlagen: {e}")
                
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                else:
                    logger.error(f"💥 [GEMINI-AGENT] Test {test_number} final fehlgeschlagen nach {self.max_retries} Versuchen")
        
        # Erstelle failed TestResult
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
            error=str(last_error),
            timestamp=datetime.now()
        )
    
    async def _validate_database_completeness(self):
        """Validiert dass ALLE 45 Tests in der Database gespeichert wurden"""
        logger.info("🗄️ [GEMINI-AGENT] Validiere Database-Completeness...")
        
        try:
            with db_manager.get_session() as session:
                # Zähle Gemini-Einträge in ModelStatistics
                for model_id in self.GEMINI_MODELS:
                    for mine in self.QUEBEC_MINES:
                        entries = session.query(ModelStatistics).filter_by(
                            model_id=model_id,
                            mine_name=mine.name
                        ).all()
                        
                        logger.debug(f"📊 [DB-CHECK] {model_id} {mine.name}: {len(entries)} Einträge")
                        self.session.database_entries += len(entries)
                
                # Validiere erwartete Anzahl
                expected_entries = 45  # 3 models × 3 mines × 5 runs
                
                if self.session.database_entries < expected_entries:
                    logger.warning(f"⚠️ [GEMINI-AGENT] Database unvollständig: {self.session.database_entries}/{expected_entries}")
                else:
                    logger.info(f"✅ [GEMINI-AGENT] Database vollständig: {self.session.database_entries}/{expected_entries}")
                    
        except Exception as e:
            logger.error(f"💥 [GEMINI-AGENT] Database-Validierung fehlgeschlagen: {e}")
            self.session.database_entries = -1
    
    async def _create_final_report(self) -> Dict[str, Any]:
        """Erstellt finalen Test-Report"""
        duration = (self.session.end_time - self.session.start_time).total_seconds()
        
        # Model-Performance berechnen
        model_performance = {}
        for model_id in self.GEMINI_MODELS:
            model_results = [r for r in self.session.results if r.model_id == model_id]
            successful = [r for r in model_results if r.success]
            
            if model_results:
                model_performance[model_id] = {
                    "total_tests": len(model_results),
                    "successful_tests": len(successful),
                    "success_rate": len(successful) / len(model_results),
                    "avg_fields_found": sum(r.fields_found for r in successful) / len(successful) if successful else 0,
                    "avg_response_time": sum(r.response_time_ms for r in successful) / len(successful) if successful else 0,
                    "avg_data_quality": sum(r.data_quality for r in successful) / len(successful) if successful else 0
                }
        
        # Mine-Performance berechnen
        mine_performance = {}
        for mine in self.QUEBEC_MINES:
            mine_results = [r for r in self.session.results if r.mine_name == mine.name]
            successful = [r for r in mine_results if r.success]
            
            mine_performance[mine.name] = {
                "total_tests": len(mine_results),
                "successful_tests": len(successful),
                "success_rate": len(successful) / len(mine_results) if mine_results else 0,
                "avg_fields_found": sum(r.fields_found for r in successful) / len(successful) if successful else 0
            }
        
        # Status-Bestimmung
        is_complete = (self.session.completed_tests == self.session.total_tests and 
                      self.session.database_entries >= 45)
        
        final_status = "✅ 45/45 Gemini tests completed, all in database" if is_complete else f"⚠️ {self.session.completed_tests}/45 tests completed, {self.session.database_entries} database entries"
        
        return {
            "success": is_complete,
            "status": final_status,
            "summary": {
                "total_tests_planned": self.session.total_tests,
                "total_tests_completed": self.session.completed_tests,
                "successful_tests": self.session.successful_tests,
                "failed_tests": self.session.failed_tests,
                "database_entries": self.session.database_entries,
                "overall_success_rate": self.session.successful_tests / self.session.total_tests,
                "test_duration_seconds": duration,
                "timestamp": datetime.now().isoformat()
            },
            "gemini_models_tested": self.GEMINI_MODELS,
            "model_performance": model_performance,
            "mine_performance": mine_performance,
            "database_validation": {
                "expected_entries": 45,
                "actual_entries": self.session.database_entries,
                "is_complete": self.session.database_entries >= 45
            },
            "recommendations": self._generate_gemini_recommendations(model_performance)
        }
    
    def _generate_gemini_recommendations(self, model_performance: Dict) -> List[str]:
        """Generiert spezifische Empfehlungen für Gemini Models"""
        recommendations = []
        
        # Ranking der Gemini Models
        ranked_models = sorted(
            model_performance.items(),
            key=lambda x: (x[1]["success_rate"], x[1]["avg_fields_found"]),
            reverse=True
        )
        
        if ranked_models:
            best_model = ranked_models[0]
            recommendations.append(f"Bestes Gemini Model: {best_model[0]} ({best_model[1]['success_rate']:.1%} Erfolg, {best_model[1]['avg_fields_found']:.1f} Felder)")
        
        # Performance-Analyse
        high_performers = [m for m, p in model_performance.items() if p["success_rate"] > 0.8]
        if high_performers:
            recommendations.append(f"Hochperformante Gemini Models (>80%): {', '.join(high_performers)}")
        
        poor_performers = [m for m, p in model_performance.items() if p["success_rate"] < 0.5]
        if poor_performers:
            recommendations.append(f"Problematische Gemini Models (<50%): {', '.join(poor_performers)}")
        
        # Speed-Analyse
        speed_ranking = sorted(
            [(m, p["avg_response_time"]) for m, p in model_performance.items() if p["avg_response_time"] > 0],
            key=lambda x: x[1]
        )
        if speed_ranking:
            fastest = speed_ranking[0]
            recommendations.append(f"Schnellstes Gemini Model: {fastest[0]} ({fastest[1]:.0f}ms durchschnittlich)")
        
        return recommendations


async def main():
    """Hauptfunktion für vollständige Gemini Tests"""
    try:
        # Erstelle Test-Agent
        agent = GeminiTestAgent()
        
        # Führe vollständige Tests durch
        report = await agent.run_comprehensive_gemini_tests()
        
        # Ausgabe der Ergebnisse
        print("\n" + "="*80)
        print("🎯 GEMINI COMPREHENSIVE TEST RESULTS")
        print("="*80)
        
        if report["success"]:
            print(f"✅ STATUS: {report['status']}")
        else:
            print(f"❌ STATUS: {report.get('status', 'Tests failed')}")
        
        summary = report.get("summary", {})
        print(f"\n📊 SUMMARY:")
        print(f"   • Tests Completed: {summary.get('total_tests_completed', 0)}/45")
        print(f"   • Success Rate: {summary.get('overall_success_rate', 0):.1%}")
        print(f"   • Database Entries: {summary.get('database_entries', 0)}")
        print(f"   • Duration: {summary.get('test_duration_seconds', 0):.1f}s")
        
        print(f"\n🏆 MODEL PERFORMANCE:")
        for model_id, perf in report.get("model_performance", {}).items():
            print(f"   • {model_id}: {perf['success_rate']:.1%} success, {perf['avg_fields_found']:.1f} fields avg")
        
        print(f"\n💡 RECOMMENDATIONS:")
        for rec in report.get("recommendations", []):
            print(f"   • {rec}")
        
        print("\n" + "="*80)
        return report
        
    except Exception as e:
        print(f"💥 CRITICAL ERROR: {e}")
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    # Führe Tests aus
    asyncio.run(main())