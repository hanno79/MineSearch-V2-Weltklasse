"""
Author: rahn
Datum: 12.07.2025  
Version: 1.0
Beschreibung: Umfassendes Test-Framework für systematische Provider-Tests
"""

import logging
import asyncio
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import json

from providers.registry import provider_registry
from model_benchmark_service import ModelBenchmarkService
from search_service_multi import multi_search_service
from search_service import search_service
from search_service_multi_enhanced import enhanced_search_service
from database import db_manager
from database.models import ModelStatistics, FieldStatistics, Source
from config import CSV_COLUMNS
from config.providers import PROVIDERS_CONFIG
from search_utils import count_filled_fields

logger = logging.getLogger(__name__)


@dataclass
class TestMine:
    """Test-Mine Definition"""
    name: str
    country: str
    region: str
    commodity: str
    expected_operator: Optional[str] = None
    expected_status: Optional[str] = None


@dataclass
class TestResult:
    """Test-Ergebnis für einen einzelnen Durchlauf"""
    model_id: str
    mine_name: str
    run_number: int
    success: bool
    response_time_ms: float
    fields_found: int
    sources_count: int
    data_quality: float
    structured_data: Dict[str, Any]
    error: Optional[str] = None
    timestamp: datetime = None


class ProviderTestFramework:
    """Framework für umfassende Provider-Tests"""
    
    # Quebec Test-Minen
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
    
    # Provider-Familien
    PROVIDER_FAMILIES = {
        'perplexity': ['perplexity:sonar', 'perplexity:sonar-pro', 'perplexity:sonar-deep-research', 'perplexity:sonar-reasoning'],
        'openrouter': ['openrouter:deepseek-free', 'openrouter:deepseek-chimera-free', 'openrouter:mistral-small-free', 
                       'openrouter:cypher-alpha-free', 'openrouter:minimax-m1', 'openrouter:llama-3.3-nemotron-super',
                       'openrouter:llama-3.1-nemotron-ultra', 'openrouter:deepseek-chat', 'openrouter:deepseek-reasoner'],
        'anthropic': ['anthropic:claude-sonnet-4', 'anthropic:claude-3.7-sonnet', 'anthropic:claude-opus-4'],
        'gemini': ['gemini:gemini-2.5-pro', 'gemini:gemini-2.5-flash', 'gemini:gemini-2.5-flash-lite'],
        'grok': ['grok:grok-4', 'grok:grok-3', 'grok:grok-3-mini', 'grok:grok-3-fast'],
        'openai': ['openai:o3-deep-research', 'openai:gpt-4.1', 'openai:o3', 'openai:o4-mini'],
        'tavily': ['tavily:search', 'tavily:deep-research'],
        'scrapingbee': ['scrapingbee:basic-scrape', 'scrapingbee:js-render', 'scrapingbee:ai-extract'],
        'firecrawl': ['firecrawl:scrape', 'firecrawl:crawl', 'firecrawl:extract'],
        'brightdata': ['brightdata:web-scraper', 'brightdata:browser-api', 'brightdata:serp']
    }
    
    def __init__(self):
        self.benchmark_service = ModelBenchmarkService()
        self.provider_registry = provider_registry
        
        # Test-Session Tracking
        self.current_session_id = None
        self.test_results = []
        self.start_time = None
        
        # Validierung
        self.validation_results = {}
        
    async def run_comprehensive_tests(self, provider_filter: str = "all", runs_per_mine: int = 5) -> Dict[str, Any]:
        """
        Führt umfassende Provider-Tests durch
        
        Args:
            provider_filter: 'all', Provider-Familie oder spezifische Modell-ID
            runs_per_mine: Anzahl Durchläufe pro Mine (Standard: 5)
            
        Returns:
            Umfassende Test-Ergebnisse
        """
        self.start_time = datetime.now()
        logger.info(f"[TEST-FRAMEWORK] Starte umfassende Provider-Tests - Filter: {provider_filter}")
        
        try:
            # 1. Bestimme zu testende Modelle
            models_to_test = self._get_models_for_filter(provider_filter)
            
            if not models_to_test:
                return {
                    "success": False,
                    "error": f"Keine verfügbaren Modelle für Filter: {provider_filter}",
                    "models_found": 0
                }
            
            logger.info(f"[TEST-FRAMEWORK] {len(models_to_test)} Modelle für Tests ausgewählt")
            
            # 2. Validiere Provider-Verfügbarkeit
            available_models = await self._validate_provider_availability(models_to_test)
            logger.info(f"[TEST-FRAMEWORK] {len(available_models)} Modelle verfügbar")
            
            # 3. Führe systematische Tests durch
            test_results = await self._execute_systematic_tests(available_models, runs_per_mine)
            
            # 4. Validiere Datenbank-Konsistenz
            validation_results = await self._validate_database_consistency(available_models)
            
            # 5. Erstelle umfassenden Report
            final_report = self._create_comprehensive_report(
                available_models, test_results, validation_results
            )
            
            logger.info(f"[TEST-FRAMEWORK] Tests abgeschlossen in {(datetime.now() - self.start_time).total_seconds():.1f}s")
            return final_report
            
        except Exception as e:
            logger.error(f"[TEST-FRAMEWORK] Kritischer Fehler: {e}")
            return {
                "success": False,
                "error": str(e),
                "partial_results": getattr(self, 'test_results', [])
            }
    
    def _get_models_for_filter(self, provider_filter: str) -> List[str]:
        """
        Bestimmt Modelle basierend auf Filter
        """
        if provider_filter == "all":
            # Alle verfügbaren Modelle
            models = []
            for family_models in self.PROVIDER_FAMILIES.values():
                models.extend(family_models)
            return models
        elif provider_filter in self.PROVIDER_FAMILIES:
            # Spezifische Provider-Familie
            return self.PROVIDER_FAMILIES[provider_filter]
        elif ":" in provider_filter:
            # Einzelnes Modell
            return [provider_filter]
        else:
            # Unbekannter Filter
            logger.warning(f"[TEST-FRAMEWORK] Unbekannter Filter: {provider_filter}")
            return []
    
    async def _validate_provider_availability(self, model_ids: List[str]) -> List[str]:
        """
        Validiert welche Provider tatsächlich verfügbar sind
        """
        available_models = []
        
        for model_id in model_ids:
            try:
                if self.provider_registry.is_model_available(model_id):
                    provider = self.provider_registry.get_provider_for_model(model_id)
                    if provider:
                        available_models.append(model_id)
                        logger.debug(f"[TEST-FRAMEWORK] ✅ {model_id} verfügbar")
                    else:
                        logger.warning(f"[TEST-FRAMEWORK] ⚠️ {model_id} konfiguriert aber Provider nicht verfügbar")
                else:
                    logger.warning(f"[TEST-FRAMEWORK] ❌ {model_id} nicht verfügbar")
            except Exception as e:
                logger.error(f"[TEST-FRAMEWORK] Fehler bei {model_id}: {e}")
        
        return available_models
    
    async def _execute_systematic_tests(self, model_ids: List[str], runs_per_mine: int) -> List[TestResult]:
        """
        Führt systematische Tests für alle Modelle durch
        """
        all_results = []
        total_tests = len(model_ids) * len(self.QUEBEC_MINES) * runs_per_mine
        completed_tests = 0
        
        logger.info(f"[TEST-FRAMEWORK] Starte {total_tests} Tests ({len(model_ids)} Modelle × {len(self.QUEBEC_MINES)} Minen × {runs_per_mine} Runs)")
        
        for i, model_id in enumerate(model_ids):
            logger.info(f"[TEST-FRAMEWORK] Teste Modell {model_id} ({i+1}/{len(model_ids)})")
            
            for mine in self.QUEBEC_MINES:
                logger.info(f"[TEST-FRAMEWORK] Mine: {mine.name}")
                
                # Führe mehrere Durchläufe für diese Mine durch
                mine_results = []
                for run in range(1, runs_per_mine + 1):
                    try:
                        result = await self._test_single_run(model_id, mine, run)
                        mine_results.append(result)
                        all_results.append(result)
                        completed_tests += 1
                        
                        # Progress-Logging
                        progress = completed_tests / total_tests * 100
                        logger.info(f"[TEST-FRAMEWORK] Progress: {progress:.1f}% - {model_id} {mine.name} Run {run}/{runs_per_mine}")
                        
                        # Kurze Pause zwischen Tests um Rate-Limits zu vermeiden
                        if run < runs_per_mine:
                            await asyncio.sleep(1)
                            
                    except Exception as e:
                        logger.error(f"[TEST-FRAMEWORK] Fehler bei {model_id} {mine.name} Run {run}: {e}")
                        completed_tests += 1
                
                # Konsistenz-Analyse für diese Mine
                if mine_results:
                    await self._analyze_mine_consistency(model_id, mine, mine_results)
                
                # Pause zwischen Minen
                await asyncio.sleep(2)
            
            # Pause zwischen Modellen
            await asyncio.sleep(5)
        
        logger.info(f"[TEST-FRAMEWORK] Alle Tests abgeschlossen: {len(all_results)} Ergebnisse")
        return all_results
    
    async def _test_single_run(self, model_id: str, mine: TestMine, run_number: int) -> TestResult:
        """
        Führt einen einzelnen Test-Durchlauf durch
        KORRIGIERT: Provider-spezifische Timeouts werden nun berücksichtigt
        """
        start_time = time.time()
        
        # Bestimme Provider-spezifische Konfiguration
        provider_name = model_id.split(':')[0]
        provider_config = PROVIDERS_CONFIG.get(provider_name, {})
        model_timeout = provider_config.get('timeout', 120)  # Default 120s
        retry_attempts = provider_config.get('retry_attempts', 2)
        retry_delay = provider_config.get('retry_delay', 5)
        
        # Retry-Mechanismus mit provider-spezifischer Konfiguration
        for attempt in range(retry_attempts + 1):
            try:
                # Bestimme Search-Service
                if self.provider_registry.is_model_available(model_id):
                    # Enhanced Multi-Provider Service mit Timeout
                    result = await asyncio.wait_for(
                        enhanced_search_service.search_single_model(
                            model_id, mine.name, mine.country, mine.commodity, mine.region
                        ),
                        timeout=model_timeout
                    )
                elif model_id.startswith('perplexity:'):
                    # Legacy Perplexity Service mit Timeout
                    model_name = model_id.split(':')[1]
                    result = await asyncio.wait_for(
                        search_service.search_mine(
                            mine.name, mine.country, mine.commodity, model_name, mine.region
                        ),
                        timeout=model_timeout
                    )
                else:
                    # Fallback Multi-Provider Service mit Timeout
                    result = await asyncio.wait_for(
                        multi_search_service.search_with_model(
                            model_id, mine.name, mine.country, mine.commodity, mine.region
                        ),
                        timeout=model_timeout
                    )
                
                # Erfolgreicher Test - beende Retry-Loop
                break
                
            except asyncio.TimeoutError:
                if attempt < retry_attempts:
                    logger.warning(f"⏰ Timeout bei {model_id} (Versuch {attempt + 1}/{retry_attempts + 1}), retry in {retry_delay}s")
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    logger.error(f"💥 Finaler Timeout bei {model_id} nach {retry_attempts + 1} Versuchen")
                    raise
            except Exception as e:
                if attempt < retry_attempts:
                    logger.warning(f"🔄 Fehler bei {model_id} (Versuch {attempt + 1}/{retry_attempts + 1}): {e}")
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    logger.error(f"💥 Finaler Fehler bei {model_id}: {e}")
                    raise
        
        response_time = (time.time() - start_time) * 1000
        
        try:
            # Analysiere Ergebnis
            success = result.get('success', False)
            data = result.get('data', {})
            structured_data = data.get('structured_data', {})
            sources = data.get('sources', [])
            
            # Validiere Datenqualität - KORRIGIERT: Nutze neue count_filled_fields Funktion
            fields_found = count_filled_fields(structured_data)
            data_quality = self._calculate_data_quality(structured_data, mine)
            
            # ERWEITERT: Speichere auch model_statistics und field_statistics in Datenbank
            try:
                benchmark_service = ModelBenchmarkService()
                
                # Save model statistics
                await benchmark_service.save_model_statistics(
                    model_id=model_id,
                    mine_name=mine.name,
                    country=mine.country,
                    region=mine.region,
                    commodity=mine.commodity,
                    run_number=run_number,
                    success=success,
                    response_time_ms=response_time,
                    fields_found=fields_found,
                    sources_count=len(sources),
                    raw_result=result,
                    structured_data=structured_data
                )
                
                # Update field statistics if successful
                if success and structured_data:
                    await benchmark_service.update_field_statistics(model_id, structured_data)
                    
                logger.debug(f"[DB-INTEGRATION] Statistics saved for {model_id} - {mine.name}")
                
            except Exception as db_error:
                logger.warning(f"[DB-INTEGRATION] Database save failed for {model_id}: {db_error}")
                # Continue with test result even if DB save fails
            
            return TestResult(
                model_id=model_id,
                mine_name=mine.name,
                run_number=run_number,
                success=success,
                response_time_ms=response_time,
                fields_found=fields_found,
                sources_count=len(sources),
                data_quality=data_quality,
                structured_data=structured_data,
                error=result.get('error'),
                timestamp=datetime.now()
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"[TEST-FRAMEWORK] Fehler bei {model_id} {mine.name} Run {run_number}: {e}")
            
            return TestResult(
                model_id=model_id,
                mine_name=mine.name,
                run_number=run_number,
                success=False,
                response_time_ms=response_time,
                fields_found=0,
                sources_count=0,
                data_quality=0.0,
                structured_data={},
                error=str(e),
                timestamp=datetime.now()
            )
    
    def _count_real_fields(self, structured_data: Dict[str, Any]) -> int:
        """
        DEPRECATED: Ersetzt durch count_filled_fields() aus search_utils.py
        Kept for backwards compatibility, redirects to new function
        """
        return count_filled_fields(structured_data)
    
    def _calculate_data_quality(self, structured_data: Dict[str, Any], mine: TestMine) -> float:
        """
        Berechnet Datenqualitäts-Score basierend auf erwarteten Werten
        """
        if not structured_data:
            return 0.0
        
        quality_score = 0.0
        total_checks = 0
        
        # Basis-Qualität: Anteil gefüllter Felder - KORRIGIERT: count_filled_fields verwenden
        filled_fields = count_filled_fields(structured_data)
        quality_score += (filled_fields / len(CSV_COLUMNS)) * 0.5
        
        # Erwartete Werte prüfen
        if mine.expected_operator:
            operator_field = structured_data.get('Betreiber', '') or structured_data.get('Eigentümer', '')
            if mine.expected_operator.lower() in str(operator_field).lower():
                quality_score += 0.2
        
        if mine.expected_status:
            status_field = structured_data.get('Aktivitätsstatus', '')
            if mine.expected_status.lower() in str(status_field).lower():
                quality_score += 0.1
        
        # Koordinaten-Plausibilität für Quebec
        x_coord = structured_data.get('x-Koordinate', '')
        y_coord = structured_data.get('y-Koordinate', '')
        if x_coord and y_coord:
            try:
                x_val = float(str(x_coord).replace(',', '.'))
                y_val = float(str(y_coord).replace(',', '.'))
                # Quebec liegt etwa zwischen -79° bis -57° (Länge) und 45° bis 62° (Breite)
                if -79 <= x_val <= -57 and 45 <= y_val <= 62:
                    quality_score += 0.2
            except:
                pass
        
        return min(1.0, quality_score)
    
    async def _analyze_mine_consistency(self, model_id: str, mine: TestMine, results: List[TestResult]):
        """
        Analysiert Konsistenz der Ergebnisse für eine Mine
        """
        if len(results) < 2:
            return
        
        # Sammle Werte für jedes Feld
        field_values = {}
        for result in results:
            if result.success and result.structured_data:
                for field, value in result.structured_data.items():
                    if value and str(value).strip():
                        if field not in field_values:
                            field_values[field] = []
                        field_values[field].append(str(value).strip())
        
        # Berechne Konsistenz-Scores
        for field, values in field_values.items():
            if len(values) >= 2:
                # Häufigster Wert
                value_counts = {}
                for val in values:
                    value_counts[val] = value_counts.get(val, 0) + 1
                
                most_common_value = max(value_counts, key=value_counts.get)
                consistency_score = value_counts[most_common_value] / len(values)
                
                # Speichere in Datenbank
                try:
                    with db_manager.get_session() as session:
                        from database.models import FieldConsistency
                        
                        consistency_entry = FieldConsistency(
                            model_id=model_id,
                            field_name=field,
                            mine_name=mine.name,
                            total_runs=len(results),
                            consistent_runs=value_counts[most_common_value],
                            consistency_score=consistency_score,
                            most_common_value=most_common_value,
                            values_found=list(set(values)),
                            is_consistent=consistency_score >= 0.8,
                            last_updated=datetime.now()
                        )
                        session.merge(consistency_entry)
                        session.commit()
                        
                except Exception as e:
                    logger.error(f"[TEST-FRAMEWORK] Fehler beim Speichern der Konsistenz-Daten: {e}")
    
    async def _validate_database_consistency(self, model_ids: List[str]) -> Dict[str, Any]:
        """
        Validiert Datenbank-Konsistenz nach Tests
        """
        validation_results = {
            "timestamp": datetime.now().isoformat(),
            "models_checked": len(model_ids),
            "issues_found": [],
            "statistics": {}
        }
        
        try:
            with db_manager.get_session() as session:
                # Prüfe ModelStatistics
                for model_id in model_ids:
                    for mine in self.QUEBEC_MINES:
                        stats = session.query(ModelStatistics).filter_by(
                            model_id=model_id, mine_name=mine.name
                        ).all()
                        
                        if len(stats) != 5:  # Erwarte 5 Runs
                            validation_results["issues_found"].append(
                                f"{model_id} {mine.name}: {len(stats)} Einträge statt 5"
                            )
                        
                        # Prüfe run_numbers
                        run_numbers = [s.run_number for s in stats]
                        expected_runs = {1, 2, 3, 4, 5}
                        if set(run_numbers) != expected_runs:
                            validation_results["issues_found"].append(
                                f"{model_id} {mine.name}: Fehlende run_numbers {expected_runs - set(run_numbers)}"
                            )
                        
                        # Prüfe auf null Erfolgsraten
                        success_count = len([s for s in stats if s.success])
                        if success_count == 0 and len(stats) > 0:
                            validation_results["issues_found"].append(
                                f"{model_id} {mine.name}: Alle 5 Tests fehlgeschlagen"
                            )
                
                # Sammle Gesamt-Statistiken
                total_stats = session.query(ModelStatistics).count()
                successful_stats = session.query(ModelStatistics).filter_by(success=True).count()
                
                validation_results["statistics"] = {
                    "total_entries": total_stats,
                    "successful_entries": successful_stats,
                    "success_rate": successful_stats / total_stats if total_stats > 0 else 0
                }
                
        except Exception as e:
            validation_results["error"] = str(e)
            logger.error(f"[TEST-FRAMEWORK] Fehler bei Datenbank-Validierung: {e}")
        
        return validation_results
    
    def _create_comprehensive_report(self, models_tested: List[str], 
                                   test_results: List[TestResult],
                                   validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Erstellt umfassenden Test-Report
        """
        # Basis-Statistiken
        total_tests = len(test_results)
        successful_tests = len([r for r in test_results if r.success])
        
        # Modell-Performance
        model_performance = {}
        for model_id in models_tested:
            model_results = [r for r in test_results if r.model_id == model_id]
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
            key=lambda x: (x[1]["success_rate"], x[1]["avg_data_quality"], x[1]["avg_fields_found"]),
            reverse=True
        )[:5]
        
        # Minen-Performance
        mine_performance = {}
        for mine in self.QUEBEC_MINES:
            mine_results = [r for r in test_results if r.mine_name == mine.name]
            mine_successful = [r for r in mine_results if r.success]
            
            mine_performance[mine.name] = {
                "total_tests": len(mine_results),
                "successful_tests": len(mine_successful),
                "success_rate": len(mine_successful) / len(mine_results) if mine_results else 0,
                "avg_fields_found": sum(r.fields_found for r in mine_successful) / len(mine_successful) if mine_successful else 0
            }
        
        # Finale Report-Struktur
        report = {
            "success": True,
            "test_summary": {
                "total_models_tested": len(models_tested),
                "total_tests_executed": total_tests,
                "successful_tests": successful_tests,
                "overall_success_rate": successful_tests / total_tests if total_tests > 0 else 0,
                "test_duration_seconds": (datetime.now() - self.start_time).total_seconds(),
                "timestamp": datetime.now().isoformat()
            },
            "model_performance": model_performance,
            "top_performers": dict(top_performers),
            "mine_performance": mine_performance,
            "database_validation": validation_results,
            "recommendations": self._generate_recommendations(model_performance, validation_results)
        }
        
        return report
    
    def _generate_recommendations(self, model_performance: Dict, validation_results: Dict) -> List[str]:
        """
        Generiert Empfehlungen basierend auf Test-Ergebnissen
        """
        recommendations = []
        
        # Modell-Empfehlungen
        best_models = sorted(
            model_performance.items(),
            key=lambda x: x[1]["success_rate"],
            reverse=True
        )[:3]
        
        if best_models:
            recommendations.append(f"Top-Modelle für Mining-Recherche: {', '.join([m[0] for m in best_models])}")
        
        # Performance-Warnungen
        poor_performers = [
            model_id for model_id, perf in model_performance.items()
            if perf["success_rate"] < 0.3
        ]
        
        if poor_performers:
            recommendations.append(f"Problematische Modelle (< 30% Erfolg): {', '.join(poor_performers)}")
        
        # Datenbank-Issues
        if validation_results.get("issues_found"):
            recommendations.append(f"Datenbank-Probleme gefunden: {len(validation_results['issues_found'])} Issues")
        
        # Allgemeine Empfehlungen
        overall_success = validation_results.get("statistics", {}).get("success_rate", 0)
        if overall_success < 0.6:
            recommendations.append("Niedrige Gesamt-Erfolgsrate - API-Keys und Provider-Status prüfen")
        
        return recommendations