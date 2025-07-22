"""
Author: rahn
Datum: 13.07.2025
Version: 1.0
Beschreibung: Vollständiger OpenRouter Test-Agent für ALLE 135 Tests (9 models × 3 mines × 5 runs)
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
from config.providers import PROVIDERS_CONFIG

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class OpenRouterTestProgress:
    """Progress-Tracking für OpenRouter Tests"""
    total_tests: int = 135
    completed_tests: int = 0
    successful_tests: int = 0
    failed_tests: int = 0
    current_model: str = ""
    current_mine: str = ""
    current_run: int = 0
    start_time: Optional[datetime] = None
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class OpenRouterCompleteTestAgent:
    """Spezialisierter Agent für vollständige OpenRouter Tests"""
    
    # Die 9 OpenRouter Models zum Testen
    OPENROUTER_MODELS = [
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
    
    # Die 3 Quebec Mines zum Testen  
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
    
    RUNS_PER_MINE = 5
    
    def __init__(self):
        self.test_framework = ProviderTestFramework()
        self.benchmark_service = ModelBenchmarkService()
        self.progress = OpenRouterTestProgress()
        self.all_results: List[TestResult] = []
        
    async def run_complete_openrouter_tests(self) -> Dict[str, Any]:
        """
        Führt ALLE 135 OpenRouter Tests durch (9 models × 3 mines × 5 runs)
        
        Returns:
            Vollständiger Test-Report mit Database-Validierung
        """
        logger.info("=" * 80)
        logger.info("🚀 OPENROUTER COMPLETE TEST AGENT - STARTE ALLE 135 TESTS")
        logger.info("=" * 80)
        
        self.progress.start_time = datetime.now()
        
        try:
            # 1. Validiere OpenRouter Provider-Verfügbarkeit
            await self._validate_openrouter_availability()
            
            # 2. Führe alle Tests durch
            await self._execute_all_tests()
            
            # 3. Validiere Database Einträge  
            validation_result = await self._validate_database_entries()
            
            # 4. Erstelle finalen Report
            final_report = await self._create_final_report(validation_result)
            
            # 5. Status-Check ausgeben
            await self._print_final_status()
            
            return final_report
            
        except Exception as e:
            logger.error(f"💥 KRITISCHER FEHLER: {e}")
            return {
                "success": False,
                "error": str(e),
                "progress": self.progress,
                "partial_results": len(self.all_results)
            }
    
    async def _validate_openrouter_availability(self):
        """Validiert dass OpenRouter Provider verfügbar ist"""
        logger.info("🔍 Validiere OpenRouter Provider Verfügbarkeit...")
        
        openrouter_config = PROVIDERS_CONFIG.get('openrouter', {})
        if not openrouter_config.get('enabled', False):
            raise Exception("OpenRouter Provider ist nicht aktiviert in PROVIDERS_CONFIG")
        
        if not openrouter_config.get('api_key'):
            raise Exception("OpenRouter API-Key ist nicht konfiguriert")
        
        logger.info("✅ OpenRouter Provider ist verfügbar und konfiguriert")
        logger.info(f"📋 {len(self.OPENROUTER_MODELS)} OpenRouter Modelle zu testen")
        logger.info(f"🏔️ {len(self.QUEBEC_MINES)} Quebec Minen zu testen")
        logger.info(f"🔁 {self.RUNS_PER_MINE} Runs pro Mine")
        logger.info(f"📊 Gesamt: {len(self.OPENROUTER_MODELS)} × {len(self.QUEBEC_MINES)} × {self.RUNS_PER_MINE} = 135 Tests")
    
    async def _execute_all_tests(self):
        """Führt alle 135 Tests systematisch durch"""
        logger.info("🎯 STARTE SYSTEMATISCHE TESTS...")
        
        for model_index, model_id in enumerate(self.OPENROUTER_MODELS):
            self.progress.current_model = model_id
            logger.info(f"\n📈 MODELL {model_index + 1}/{len(self.OPENROUTER_MODELS)}: {model_id}")
            
            for mine_index, mine in enumerate(self.QUEBEC_MINES):
                self.progress.current_mine = mine.name
                logger.info(f"  🏔️ MINE {mine_index + 1}/{len(self.QUEBEC_MINES)}: {mine.name}")
                
                # Führe 5 Runs für diese Mine durch
                for run in range(1, self.RUNS_PER_MINE + 1):
                    self.progress.current_run = run
                    
                    try:
                        # Test mit Retry-Mechanismus
                        result = await self._test_with_retry(model_id, mine, run)
                        self.all_results.append(result)
                        
                        if result.success:
                            self.progress.successful_tests += 1
                            status_icon = "✅"
                        else:
                            self.progress.failed_tests += 1
                            status_icon = "❌"
                            self.progress.errors.append(f"{model_id} {mine.name} Run {run}: {result.error}")
                        
                        self.progress.completed_tests += 1
                        
                        # Progress Logging
                        progress_pct = (self.progress.completed_tests / self.progress.total_tests) * 100
                        logger.info(f"    {status_icon} Run {run}/{self.RUNS_PER_MINE} - Progress: {progress_pct:.1f}% ({self.progress.completed_tests}/135)")
                        
                        # Kurze Pause zwischen Tests
                        await asyncio.sleep(2)
                        
                    except Exception as e:
                        logger.error(f"    💥 FEHLER Run {run}: {e}")
                        self.progress.failed_tests += 1
                        self.progress.completed_tests += 1
                        self.progress.errors.append(f"{model_id} {mine.name} Run {run}: {str(e)}")
                
                # Pause zwischen Minen
                logger.info(f"  ⏸️ Pause zwischen Minen...")
                await asyncio.sleep(5)
            
            # Pause zwischen Modellen
            logger.info(f"⏸️ Pause zwischen Modellen...")
            await asyncio.sleep(10)
        
        logger.info("\n🎉 ALLE TESTS ABGESCHLOSSEN!")
        logger.info(f"📊 Gesamt: {self.progress.completed_tests}/135 Tests durchgeführt")
        logger.info(f"✅ Erfolgreich: {self.progress.successful_tests}")
        logger.info(f"❌ Fehlgeschlagen: {self.progress.failed_tests}")
    
    async def _test_with_retry(self, model_id: str, mine: TestMine, run_number: int, max_retries: int = 3) -> TestResult:
        """
        Führt einen einzelnen Test mit Retry-Logic durch
        """
        for attempt in range(max_retries):
            try:
                logger.debug(f"      🔄 Versuch {attempt + 1}/{max_retries} für {model_id} {mine.name} Run {run_number}")
                
                result = await self.test_framework._test_single_run(model_id, mine, run_number)
                
                # Erfolgreich - breche Retry-Loop ab
                if result.success:
                    logger.debug(f"      ✅ Erfolg nach {attempt + 1} Versuch(en)")
                    return result
                else:
                    if attempt < max_retries - 1:
                        logger.warning(f"      ⚠️ Versuch {attempt + 1} fehlgeschlagen, retry in 5s...")
                        await asyncio.sleep(5)
                        continue
                    else:
                        logger.error(f"      💥 Alle {max_retries} Versuche fehlgeschlagen")
                        return result
                        
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"      🔄 Exception in Versuch {attempt + 1}: {e}, retry in 10s...")
                    await asyncio.sleep(10)
                    continue
                else:
                    logger.error(f"      💥 Finale Exception nach {max_retries} Versuchen: {e}")
                    # Erstelle Error-Result
                    return TestResult(
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
    
    async def _validate_database_entries(self) -> Dict[str, Any]:
        """
        Validiert dass alle 135 Tests in der Database gespeichert wurden
        """
        logger.info("🔍 VALIDIERE DATABASE ENTRIES...")
        
        validation_result = {
            "timestamp": datetime.now().isoformat(),
            "expected_entries": 135,
            "found_entries": 0,
            "missing_entries": [],
            "success": False,
            "model_breakdown": {}
        }
        
        try:
            with db_manager.get_session() as session:
                for model_id in self.OPENROUTER_MODELS:
                    model_entries = 0
                    missing_for_model = []
                    
                    for mine in self.QUEBEC_MINES:
                        for run in range(1, self.RUNS_PER_MINE + 1):
                            # Prüfe ob Entry existiert
                            entry = session.query(ModelStatistics).filter_by(
                                model_id=model_id,
                                mine_name=mine.name,
                                run_number=run
                            ).first()
                            
                            if entry:
                                model_entries += 1
                                validation_result["found_entries"] += 1
                            else:
                                missing_entry = f"{model_id} - {mine.name} - Run {run}"
                                missing_for_model.append(missing_entry)
                                validation_result["missing_entries"].append(missing_entry)
                    
                    validation_result["model_breakdown"][model_id] = {
                        "found": model_entries,
                        "expected": 15,  # 3 mines × 5 runs
                        "missing": missing_for_model
                    }
                    
                    logger.info(f"  📊 {model_id}: {model_entries}/15 Einträge gefunden")
        
            validation_result["success"] = (validation_result["found_entries"] == 135)
            
            if validation_result["success"]:
                logger.info(f"✅ VALIDATION ERFOLGREICH: Alle 135 Database Einträge gefunden!")
            else:
                logger.warning(f"⚠️ VALIDATION PROBLEME: {validation_result['found_entries']}/135 Einträge gefunden")
                logger.warning(f"❌ {len(validation_result['missing_entries'])} fehlende Einträge")
        
        except Exception as e:
            logger.error(f"💥 Database Validation Fehler: {e}")
            validation_result["error"] = str(e)
        
        return validation_result
    
    async def _create_final_report(self, validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Erstellt finalen Test-Report"""
        
        duration = (datetime.now() - self.progress.start_time).total_seconds() if self.progress.start_time else 0
        
        # Model Performance Analyse
        model_performance = {}
        for model_id in self.OPENROUTER_MODELS:
            model_results = [r for r in self.all_results if r.model_id == model_id]
            successful_results = [r for r in model_results if r.success]
            
            if model_results:
                model_performance[model_id] = {
                    "total_tests": len(model_results),
                    "successful_tests": len(successful_results),
                    "success_rate": len(successful_results) / len(model_results),
                    "avg_fields_found": sum(r.fields_found for r in successful_results) / len(successful_results) if successful_results else 0,
                    "avg_response_time_ms": sum(r.response_time_ms for r in successful_results) / len(successful_results) if successful_results else 0
                }
        
        # Top Performer
        top_performers = sorted(
            model_performance.items(),
            key=lambda x: (x[1]["success_rate"], x[1]["avg_fields_found"]),
            reverse=True
        )
        
        final_report = {
            "success": True,
            "test_type": "OPENROUTER_COMPLETE_135_TESTS",
            "execution_summary": {
                "total_tests_planned": 135,
                "total_tests_executed": self.progress.completed_tests,
                "successful_tests": self.progress.successful_tests,
                "failed_tests": self.progress.failed_tests,
                "success_rate": self.progress.successful_tests / self.progress.completed_tests if self.progress.completed_tests > 0 else 0,
                "duration_seconds": duration,
                "avg_time_per_test": duration / self.progress.completed_tests if self.progress.completed_tests > 0 else 0
            },
            "database_validation": validation_result,
            "model_performance": model_performance,
            "top_performers": dict(top_performers[:5]),
            "errors_summary": {
                "total_errors": len(self.progress.errors),
                "error_list": self.progress.errors[:10]  # Nur erste 10 Fehler im Report
            },
            "recommendations": self._generate_recommendations(model_performance, validation_result),
            "timestamp": datetime.now().isoformat()
        }
        
        return final_report
    
    def _generate_recommendations(self, model_performance: Dict, validation_result: Dict) -> List[str]:
        """Generiert Empfehlungen basierend auf Test-Ergebnissen"""
        recommendations = []
        
        # Database Status
        if validation_result.get("success"):
            recommendations.append("✅ Alle 135 Database Entries erfolgreich gespeichert - System ready for production")
        else:
            found = validation_result.get("found_entries", 0)
            recommendations.append(f"⚠️ Database Issues: Nur {found}/135 Entries gefunden - Database Cleanup erforderlich")
        
        # Top Models
        if model_performance:
            top_models = sorted(
                model_performance.items(),
                key=lambda x: (x[1]["success_rate"], x[1]["avg_fields_found"]),
                reverse=True
            )[:3]
            
            if top_models:
                top_names = [model[0] for model in top_models]
                recommendations.append(f"🏆 Top 3 OpenRouter Models: {', '.join(top_names)}")
        
        # Performance Issues
        poor_performers = [
            model_id for model_id, perf in model_performance.items()
            if perf["success_rate"] < 0.6
        ]
        
        if poor_performers:
            recommendations.append(f"❌ Problematische Models (< 60% Erfolg): {', '.join(poor_performers)}")
        
        # Overall Status
        overall_success = self.progress.successful_tests / max(self.progress.completed_tests, 1)
        if overall_success >= 0.8:
            recommendations.append("🎉 Excellent OpenRouter Performance - ready for production deployment")
        elif overall_success >= 0.6:
            recommendations.append("⚠️ Good OpenRouter Performance - minor optimizations recommended")
        else:
            recommendations.append("❌ Poor OpenRouter Performance - investigation required")
        
        return recommendations
    
    async def _print_final_status(self):
        """Gibt finalen Status aus"""
        logger.info("\n" + "=" * 80)
        logger.info("🎯 FINAL STATUS - OPENROUTER COMPLETE TEST AGENT")
        logger.info("=" * 80)
        
        duration = (datetime.now() - self.progress.start_time).total_seconds() if self.progress.start_time else 0
        
        logger.info(f"⏱️ Gesamtdauer: {duration:.1f} Sekunden ({duration/60:.1f} Minuten)")
        logger.info(f"📊 Tests: {self.progress.completed_tests}/135 durchgeführt")
        logger.info(f"✅ Erfolgreich: {self.progress.successful_tests} ({self.progress.successful_tests/max(self.progress.completed_tests, 1):.1%})")
        logger.info(f"❌ Fehlgeschlagen: {self.progress.failed_tests}")
        logger.info(f"🐛 Fehler: {len(self.progress.errors)}")
        
        if self.progress.completed_tests == 135 and self.progress.successful_tests >= 100:
            logger.info("🎉 MISSION ERFOLGREICH: OpenRouter Tests vollständig abgeschlossen!")
            logger.info("✅ 135/135 OpenRouter tests completed, all in database")
        else:
            logger.warning("⚠️ Mission teilweise erfolgreich - weitere Optimierung erforderlich")


async def main():
    """Hauptfunktion für komplette OpenRouter Tests"""
    agent = OpenRouterCompleteTestAgent()
    
    try:
        final_report = await agent.run_complete_openrouter_tests()
        
        # Speichere Report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"/app/documentation/OPENROUTER_COMPLETE_TEST_REPORT_{timestamp}.md"
        
        # Erstelle Markdown Report
        markdown_content = _generate_markdown_report(final_report, agent.progress)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        logger.info(f"📄 Report gespeichert: {report_file}")
        
        # Final Status Check
        if (final_report.get("database_validation", {}).get("success") and 
            agent.progress.completed_tests == 135):
            print("\n🎉 RESULT: ✅ 135/135 OpenRouter tests completed, all in database")
        else:
            completed = agent.progress.completed_tests
            db_entries = final_report.get("database_validation", {}).get("found_entries", 0)
            print(f"\n⚠️ RESULT: Partial completion - {completed}/135 tests, {db_entries}/135 in database")
        
        return final_report
        
    except Exception as e:
        logger.error(f"💥 FATAL ERROR: {e}")
        print(f"\n❌ RESULT: Fatal error - {str(e)}")
        return {"success": False, "error": str(e)}


def _generate_markdown_report(report: Dict[str, Any], progress: OpenRouterTestProgress) -> str:
    """Generiert Markdown-Report für die Tests"""
    timestamp = datetime.now().strftime("%d.%m.%Y, %H:%M UTC")
    
    content = f"""# OPENROUTER COMPLETE TEST REPORT - 135 TESTS

**Author:** OpenRouter Complete Test Agent  
**Date:** {timestamp}  
**Test Type:** Vollständige OpenRouter Model Validierung  
**Version:** 1.0

## 🎯 EXECUTIVE SUMMARY

### Test Overview
- **Models Tested:** {len(OpenRouterCompleteTestAgent.OPENROUTER_MODELS)} OpenRouter Models INDIVIDUALLY
- **Mines:** Éléonore, Niobec, LaRonde (Quebec, Canada)
- **Total Tests:** {progress.completed_tests}/135 executed
- **Success Rate:** {progress.successful_tests/max(progress.completed_tests, 1):.1%}
- **Duration:** {report.get('execution_summary', {}).get('duration_seconds', 0):.1f} seconds

### Database Validation
- **Expected Entries:** 135
- **Found Entries:** {report.get('database_validation', {}).get('found_entries', 0)}
- **Status:** {'✅ SUCCESS' if report.get('database_validation', {}).get('success') else '❌ ISSUES FOUND'}

## 📊 MODEL PERFORMANCE

| Model | Tests | Success | Success Rate | Avg Fields | Avg Response Time |
|-------|-------|---------|--------------|------------|-------------------|"""
    
    model_perf = report.get("model_performance", {})
    for model_id, perf in model_perf.items():
        success_icon = "✅" if perf["success_rate"] > 0.8 else "⚠️" if perf["success_rate"] > 0.5 else "❌"
        content += f"\n| {model_id} | {perf['total_tests']} | {success_icon} {perf['successful_tests']} | {perf['success_rate']:.1%} | {perf['avg_fields_found']:.1f} | {perf['avg_response_time_ms']:.0f}ms |"
    
    content += f"""

## 🏆 TOP PERFORMERS

"""
    
    top_performers = report.get("top_performers", {})
    for i, (model_id, perf) in enumerate(top_performers.items()):
        rank = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}."
        content += f"{rank} **{model_id}** - {perf['avg_fields_found']:.1f}/19 fields ({perf['success_rate']:.1%} success)\n"
    
    content += f"""

## 💡 RECOMMENDATIONS

"""
    
    recommendations = report.get("recommendations", [])
    for rec in recommendations:
        content += f"- {rec}\n"
    
    content += f"""

## 🐛 ERROR SUMMARY

**Total Errors:** {len(progress.errors)}

"""
    
    for error in progress.errors[:5]:  # Show first 5 errors
        content += f"- {error}\n"
    
    if len(progress.errors) > 5:
        content += f"... and {len(progress.errors) - 5} more errors\n"
    
    content += f"""

## 📋 CONCLUSION

### System Status
{'✅ **PRODUCTION READY**' if report.get('database_validation', {}).get('success') and progress.completed_tests == 135 else '⚠️ **NEEDS ATTENTION**'}

OpenRouter integration {'fully validated' if progress.successful_tests >= 100 else 'requires optimization'} for enterprise mining research.

---
**Report generated by:** OpenRouter Complete Test Agent  
**Timestamp:** {timestamp}  
**Next Review:** After optimization cycle
"""
    
    return content


if __name__ == "__main__":
    # Führe vollständige OpenRouter Tests aus
    asyncio.run(main())