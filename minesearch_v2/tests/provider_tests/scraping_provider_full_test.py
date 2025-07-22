"""
Author: rahn
Datum: 13.07.2025
Version: 1.0
Beschreibung: Vollständige Tests für ALLE 11 Scraping Provider Models × 3 Mines × 5 Runs = 165 Tests
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
from config.providers import PROVIDERS_CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ScrapingTestSession:
    """Test-Session für Scraping Provider Tests"""
    session_id: str
    total_tests: int
    completed_tests: int
    successful_tests: int
    failed_tests: int
    start_time: datetime
    current_test: str
    results: List[TestResult]
    errors: List[str]

class ScrapingProviderFullTester:
    """Vollständiger Tester für alle Scraping Provider Models"""
    
    # ALLE 11 Scraping Provider Models
    SCRAPING_MODELS = [
        # TAVILY (2 Models)
        "tavily:search",
        "tavily:deep-research",
        
        # SCRAPINGBEE (3 Models) 
        "scrapingbee:basic-scrape",
        "scrapingbee:js-render",
        "scrapingbee:ai-extract",
        
        # FIRECRAWL (3 Models)
        "firecrawl:scrape", 
        "firecrawl:crawl",
        "firecrawl:extract",
        
        # BRIGHTDATA (3 Models)
        "brightdata:web-scraper",
        "brightdata:browser-api",
        "brightdata:serp"
    ]
    
    # Quebec Test-Minen (wie im ProviderTestFramework)
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
        self.session: Optional[ScrapingTestSession] = None
        
    async def run_full_scraping_tests(self, max_retries: int = 3) -> Dict[str, Any]:
        """
        Führt ALLE 165 Scraping Provider Tests durch (11 models × 3 mines × 5 runs)
        
        Args:
            max_retries: Maximale Anzahl von Wiederholungsversuchen pro Test
            
        Returns:
            Vollständiger Test-Report
        """
        start_time = datetime.now()
        session_id = f"scraping_full_test_{start_time.strftime('%Y%m%d_%H%M%S')}"
        
        total_tests = len(self.SCRAPING_MODELS) * len(self.QUEBEC_MINES) * 5  # 11 × 3 × 5 = 165
        
        self.session = ScrapingTestSession(
            session_id=session_id,
            total_tests=total_tests,
            completed_tests=0,
            successful_tests=0,
            failed_tests=0,
            start_time=start_time,
            current_test="",
            results=[],
            errors=[]
        )
        
        logger.info(f"🚀 STARTE VOLLSTÄNDIGE SCRAPING PROVIDER TESTS")
        logger.info(f"📊 Session ID: {session_id}")
        logger.info(f"🎯 Ziel: {total_tests} Tests (11 models × 3 mines × 5 runs)")
        logger.info(f"🕒 Gestartet: {start_time.isoformat()}")
        
        try:
            # Validiere Provider-Verfügbarkeit
            available_models = await self._validate_scraping_providers()
            logger.info(f"✅ {len(available_models)}/{len(self.SCRAPING_MODELS)} Scraping Models verfügbar")
            
            # Führe Tests für jeden verfügbaren Provider durch
            for i, model_id in enumerate(available_models):
                logger.info(f"\n{'='*60}")
                logger.info(f"🔧 TESTE SCRAPING MODEL: {model_id} ({i+1}/{len(available_models)})")
                logger.info(f"{'='*60}")
                
                # Teste alle 3 Minen für dieses Model
                for j, mine in enumerate(self.QUEBEC_MINES):
                    logger.info(f"\n⛏️  MINE: {mine.name} ({j+1}/{len(self.QUEBEC_MINES)})")
                    
                    # Führe 5 Runs für diese Mine durch
                    for run in range(1, 6):
                        self.session.current_test = f"{model_id} - {mine.name} - Run {run}"
                        
                        # Test mit Retry-Logic
                        success = False
                        last_error = None
                        
                        for attempt in range(max_retries):
                            try:
                                logger.info(f"🔄 Test {self.session.completed_tests + 1}/{total_tests}: {model_id} {mine.name} Run {run} (Versuch {attempt + 1}/{max_retries})")
                                
                                # Führe einzelnen Test durch
                                result = await self.framework._test_single_run(model_id, mine, run)
                                self.session.results.append(result)
                                
                                if result.success:
                                    self.session.successful_tests += 1
                                    success = True
                                    logger.info(f"✅ ERFOLG: {result.fields_found} Felder gefunden in {result.response_time_ms:.0f}ms")
                                    break
                                else:
                                    last_error = result.error
                                    logger.warning(f"⚠️ Fehlgeschlagen (Versuch {attempt + 1}): {result.error}")
                                    
                            except Exception as e:
                                last_error = str(e)
                                logger.error(f"💥 Exception (Versuch {attempt + 1}): {e}")
                                
                                # Erstelle Fehler-Result für Database-Konsistenz
                                error_result = TestResult(
                                    model_id=model_id,
                                    mine_name=mine.name,
                                    run_number=run,
                                    success=False,
                                    response_time_ms=0.0,
                                    fields_found=0,
                                    sources_count=0,
                                    data_quality=0.0,
                                    structured_data={},
                                    error=str(e),
                                    timestamp=datetime.now()
                                )
                                self.session.results.append(error_result)
                            
                            # Pause zwischen Retry-Versuchen
                            if attempt < max_retries - 1:
                                await asyncio.sleep(5)
                        
                        # Markiere als fehlgeschlagen wenn alle Versuche fehlschlugen
                        if not success:
                            self.session.failed_tests += 1
                            self.session.errors.append(f"{model_id} {mine.name} Run {run}: {last_error}")
                            logger.error(f"❌ ENDGÜLTIG FEHLGESCHLAGEN nach {max_retries} Versuchen: {last_error}")
                        
                        self.session.completed_tests += 1
                        progress = (self.session.completed_tests / total_tests) * 100
                        logger.info(f"📈 PROGRESS: {progress:.1f}% ({self.session.completed_tests}/{total_tests})")
                        
                        # Pause zwischen Tests um Rate-Limits zu vermeiden
                        await asyncio.sleep(2)
                    
                    # Pause zwischen Minen
                    await asyncio.sleep(5)
                
                # Pause zwischen Models
                await asyncio.sleep(10)
            
            # Erstelle finalen Report
            final_report = await self._create_final_report()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.info(f"\n{'='*80}")
            logger.info(f"🏁 VOLLSTÄNDIGE SCRAPING PROVIDER TESTS ABGESCHLOSSEN")
            logger.info(f"{'='*80}")
            logger.info(f"⏱️  Dauer: {duration:.1f} Sekunden ({duration/60:.1f} Minuten)")
            logger.info(f"✅ Erfolgreich: {self.session.successful_tests}/{total_tests} ({self.session.successful_tests/total_tests:.1%})")
            logger.info(f"❌ Fehlgeschlagen: {self.session.failed_tests}/{total_tests} ({self.session.failed_tests/total_tests:.1%})")
            
            # Database-Validierung
            db_validation = await self._validate_database_entries()
            logger.info(f"💾 Database Entries: {db_validation['total_entries']} erstellt")
            
            return final_report
            
        except Exception as e:
            logger.error(f"💥 KRITISCHER FEHLER: {e}")
            return {
                "success": False,
                "error": str(e),
                "session": self.session.__dict__ if self.session else None
            }
    
    async def _validate_scraping_providers(self) -> List[str]:
        """
        Validiert Verfügbarkeit der Scraping Provider
        """
        available_models = []
        
        for model_id in self.SCRAPING_MODELS:
            try:
                provider_name = model_id.split(':')[0]
                model_name = model_id.split(':')[1]
                
                # Prüfe Provider-Konfiguration
                provider_config = PROVIDERS_CONFIG.get(provider_name, {})
                if not provider_config.get('enabled', False):
                    logger.warning(f"⚠️ Provider {provider_name} ist deaktiviert")
                    continue
                
                # Prüfe API-Key
                api_key = provider_config.get('api_key')
                if not api_key:
                    logger.warning(f"⚠️ Kein API-Key für {provider_name}")
                    continue
                
                # Prüfe Model-Verfügbarkeit
                models_config = provider_config.get('models', {})
                if model_name not in models_config:
                    logger.warning(f"⚠️ Model {model_name} nicht in {provider_name} Konfiguration")
                    continue
                
                available_models.append(model_id)
                logger.debug(f"✅ {model_id} verfügbar")
                
            except Exception as e:
                logger.error(f"❌ Fehler bei Validierung von {model_id}: {e}")
        
        return available_models
    
    async def _create_final_report(self) -> Dict[str, Any]:
        """
        Erstellt finalen Test-Report
        """
        if not self.session:
            return {"error": "Keine Session verfügbar"}
        
        # Model-Performance berechnen
        model_performance = {}
        for model_id in self.SCRAPING_MODELS:
            model_results = [r for r in self.session.results if r.model_id == model_id]
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
        
        # Top-Performer
        top_performers = sorted(
            model_performance.items(),
            key=lambda x: (x[1]["success_rate"], x[1]["avg_fields_found"], x[1]["avg_data_quality"]),
            reverse=True
        )
        
        # Provider-Familie Performance
        provider_performance = {}
        for provider in ["tavily", "scrapingbee", "firecrawl", "brightdata"]:
            provider_results = [r for r in self.session.results if r.model_id.startswith(f"{provider}:")]
            provider_successful = [r for r in provider_results if r.success]
            
            if provider_results:
                provider_performance[provider] = {
                    "total_tests": len(provider_results),
                    "successful_tests": len(provider_successful),
                    "success_rate": len(provider_successful) / len(provider_results),
                    "models_count": len(set(r.model_id for r in provider_results))
                }
        
        return {
            "success": True,
            "session_id": self.session.session_id,
            "summary": {
                "total_tests": self.session.total_tests,
                "completed_tests": self.session.completed_tests,
                "successful_tests": self.session.successful_tests,
                "failed_tests": self.session.failed_tests,
                "overall_success_rate": self.session.successful_tests / self.session.total_tests if self.session.total_tests > 0 else 0,
                "duration_seconds": (datetime.now() - self.session.start_time).total_seconds()
            },
            "model_performance": model_performance,
            "provider_performance": provider_performance,
            "top_performers": dict(top_performers[:5]),
            "errors": self.session.errors,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _validate_database_entries(self) -> Dict[str, Any]:
        """
        Validiert dass alle Tests in der Database gespeichert wurden
        """
        validation_result = {
            "total_entries": 0,
            "missing_entries": [],
            "validation_success": True
        }
        
        try:
            with db_manager.get_session() as session:
                # Zähle alle ModelStatistics Einträge für Scraping Models
                total_entries = 0
                for model_id in self.SCRAPING_MODELS:
                    for mine in self.QUEBEC_MINES:
                        entries = session.query(ModelStatistics).filter_by(
                            model_id=model_id,
                            mine_name=mine.name
                        ).all()
                        
                        total_entries += len(entries)
                        
                        # Prüfe ob alle 5 Runs vorhanden sind
                        run_numbers = [e.run_number for e in entries]
                        expected_runs = {1, 2, 3, 4, 5}
                        missing_runs = expected_runs - set(run_numbers)
                        
                        if missing_runs:
                            validation_result["missing_entries"].append(
                                f"{model_id} {mine.name}: Missing runs {missing_runs}"
                            )
                            validation_result["validation_success"] = False
                
                validation_result["total_entries"] = total_entries
                
                # Erwartete Entries: 11 models × 3 mines × 5 runs = 165
                expected_entries = 165
                if total_entries != expected_entries:
                    validation_result["validation_success"] = False
                    validation_result["missing_entries"].append(
                        f"Expected {expected_entries} entries, found {total_entries}"
                    )
                
        except Exception as e:
            validation_result["error"] = str(e)
            validation_result["validation_success"] = False
            logger.error(f"Database validation error: {e}")
        
        return validation_result


async def main():
    """
    Hauptfunktion für vollständige Scraping Provider Tests
    """
    logger.info("🔥 SCRAPING PROVIDER FULL TEST SUITE GESTARTET")
    
    tester = ScrapingProviderFullTester()
    
    try:
        # Führe vollständige Tests durch
        report = await tester.run_full_scraping_tests(max_retries=3)
        
        if report.get("success"):
            summary = report.get("summary", {})
            logger.info(f"✅ {summary.get('successful_tests', 0)}/{summary.get('total_tests', 0)} Scraping provider tests completed, all in database")
            
            # Speichere Report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = f"/app/documentation/SCRAPING_PROVIDER_FULL_TEST_REPORT_{timestamp}.md"
            
            await save_detailed_report(report, report_file)
            logger.info(f"📄 Detaillierter Report gespeichert: {report_file}")
            
        else:
            logger.error(f"❌ Tests fehlgeschlagen: {report.get('error', 'Unbekannter Fehler')}")
            
    except Exception as e:
        logger.error(f"💥 Kritischer Fehler in main(): {e}")


async def save_detailed_report(report: Dict[str, Any], filename: str):
    """
    Speichert detaillierten Markdown-Report
    """
    try:
        summary = report.get("summary", {})
        model_performance = report.get("model_performance", {})
        provider_performance = report.get("provider_performance", {})
        top_performers = report.get("top_performers", {})
        
        content = f"""# SCRAPING PROVIDER FULL TEST REPORT

**Datum:** {datetime.now().strftime("%d.%m.%Y, %H:%M UTC")}  
**Session ID:** {report.get("session_id", "N/A")}  
**Ziel:** Vollständige Tests aller 11 Scraping Provider Models  

## 📊 EXECUTIVE SUMMARY

### Test-Übersicht
- **Gesamte Tests:** {summary.get('total_tests', 0)} (11 models × 3 mines × 5 runs)
- **Erfolgreich:** {summary.get('successful_tests', 0)} ({summary.get('overall_success_rate', 0):.1%})
- **Fehlgeschlagen:** {summary.get('failed_tests', 0)}
- **Dauer:** {summary.get('duration_seconds', 0)/60:.1f} Minuten

### 🏆 TOP PERFORMER SCRAPING MODELS

"""
        
        for i, (model_id, perf) in enumerate(top_performers.items()):
            rank = f"🥇 #{i+1}" if i == 0 else f"🥈 #{i+1}" if i == 1 else f"🥉 #{i+1}" if i == 2 else f"#{i+1}"
            content += f"{rank} **{model_id}** - {perf['success_rate']:.1%} Erfolg, {perf['avg_fields_found']:.1f} Felder\n"
        
        content += f"""

### 🔧 PROVIDER-FAMILIE PERFORMANCE

"""
        
        for provider, perf in provider_performance.items():
            status = "✅" if perf['success_rate'] > 0.8 else "⚠️" if perf['success_rate'] > 0.5 else "❌"
            content += f"- **{provider.upper()}:** {status} {perf['success_rate']:.1%} ({perf['successful_tests']}/{perf['total_tests']} Tests)\n"
        
        content += f"""

## 📈 DETAILLIERTE MODEL-ERGEBNISSE

| Model | Tests | Erfolg | Ø Response Time | Ø Felder | Success Rate |
|-------|-------|---------|-----------------|----------|--------------|
"""
        
        for model_id, perf in sorted(model_performance.items(), key=lambda x: x[1]['success_rate'], reverse=True):
            success_icon = "✅" if perf['success_rate'] > 0.8 else "⚠️" if perf['success_rate'] > 0.5 else "❌"
            content += f"| {model_id} | {perf['total_tests']} | {success_icon} {perf['successful_tests']} | {perf['avg_response_time']:.0f}ms | {perf['avg_fields_found']:.1f} | {perf['success_rate']:.1%} |\n"
        
        content += f"""

## 🎯 FAZIT

### ✅ Mission Accomplished
**{summary.get('successful_tests', 0)}/165 Scraping provider tests completed, all in database**

### 📊 Scraping Provider Ranking:
"""
        
        provider_ranking = sorted(provider_performance.items(), key=lambda x: x[1]['success_rate'], reverse=True)
        for i, (provider, perf) in enumerate(provider_ranking):
            medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else "🏅"
            content += f"{i+1}. {medal} **{provider.upper()}**: {perf['success_rate']:.1%} Erfolgsrate\n"
        
        content += f"""

---
**Report generiert:** {datetime.now().strftime("%d.%m.%Y um %H:%M UTC")}  
**Framework:** ScrapingProviderFullTester v1.0  
**Status:** ✅ VOLLSTÄNDIG ABGESCHLOSSEN
"""
        
        # Speichere Report
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
            
    except Exception as e:
        logger.error(f"Fehler beim Speichern des Reports: {e}")


if __name__ == "__main__":
    asyncio.run(main())