"""
Author: rahn
Datum: 12.07.2025  
Version: 1.0
Beschreibung: Model Benchmark Service für systematische Provider-Tests
"""

import logging
import asyncio
import time
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict

from database import db_manager
from database.models import ModelStatistics, FieldStatistics, FieldConsistency, ModelSummary
from search_service_multi import multi_search_service
from search_service import search_service
from search_service_multi_enhanced import enhanced_search_service
from providers.registry import provider_registry
from config import CSV_COLUMNS

logger = logging.getLogger(__name__)


class ModelBenchmarkService:
    """Service für systematische Modell-Benchmarks und Tests"""
    
    def __init__(self):
        self.running_sessions = {}
        self.provider_registry = provider_registry
    
    async def start_benchmark_session(self, model_ids: List[str], mine_name: str,
                                    country: Optional[str] = None, region: Optional[str] = None,
                                    commodity: Optional[str] = None, runs: int = 5) -> str:
        """
        Startet eine neue Benchmark-Session
        
        Args:
            model_ids: Liste der zu testenden Modell-IDs
            mine_name: Name der Mine
            country: Land (optional)
            region: Region (optional)  
            commodity: Rohstoff (optional)
            runs: Anzahl Durchläufe pro Modell
            
        Returns:
            Session-ID
        """
        session_id = str(uuid.uuid4())
        
        session_data = {
            'session_id': session_id,
            'status': 'running',
            'progress': 0.0,
            'current_model': None,
            'models_completed': 0,
            'total_models': len(model_ids),
            'started_at': datetime.now().isoformat(),
            'completed_at': None,
            'error': None,
            'results': []
        }
        
        self.running_sessions[session_id] = session_data
        
        # Starte Benchmark im Hintergrund
        asyncio.create_task(self._run_benchmark(session_id, model_ids, mine_name, country, region, commodity, runs))
        
        logger.info(f"[BENCHMARK] Session {session_id} gestartet für {len(model_ids)} Modelle mit Mine {mine_name}")
        return session_id
    
    async def _run_benchmark(self, session_id: str, model_ids: List[str], mine_name: str,
                           country: Optional[str], region: Optional[str], 
                           commodity: Optional[str], runs: int):
        """
        Führt Benchmark-Session durch
        """
        session = self.running_sessions[session_id]
        
        try:
            total_tests = len(model_ids) * runs
            completed_tests = 0
            
            for i, model_id in enumerate(model_ids):
                session['current_model'] = model_id
                session['progress'] = i / len(model_ids)
                
                logger.info(f"[BENCHMARK] {session_id}: Teste Modell {model_id} ({i+1}/{len(model_ids)})")
                
                # Führe mehrere Durchläufe durch
                model_results = []
                for run in range(1, runs + 1):
                    try:
                        result = await self._test_single_model(model_id, mine_name, country, region, commodity, run)
                        model_results.append(result)
                        completed_tests += 1
                        
                        # Aktualisiere Progress
                        session['progress'] = completed_tests / total_tests
                        
                        logger.debug(f"[BENCHMARK] {session_id}: {model_id} Run {run}/{runs} - Erfolg: {result.get('success', False)}")
                        
                    except Exception as e:
                        logger.error(f"[BENCHMARK] {session_id}: Fehler bei {model_id} Run {run}: {e}")
                        model_results.append({
                            'success': False,
                            'error': str(e),
                            'model_id': model_id,
                            'mine_name': mine_name,
                            'run_number': run
                        })
                        completed_tests += 1
                
                session['results'].extend(model_results)
                session['models_completed'] = i + 1
            
            # Session als abgeschlossen markieren
            session['status'] = 'completed'
            session['completed_at'] = datetime.now().isoformat()
            session['progress'] = 1.0
            
            # Erstelle Zusammenfassung
            await self._create_session_summary(session_id)
            
            logger.info(f"[BENCHMARK] Session {session_id} erfolgreich abgeschlossen")
            
        except Exception as e:
            session['status'] = 'failed'
            session['error'] = str(e)
            session['completed_at'] = datetime.now().isoformat()
            logger.error(f"[BENCHMARK] Session {session_id} fehlgeschlagen: {e}")
    
    async def _test_single_model(self, model_id: str, mine_name: str, country: Optional[str],
                               region: Optional[str], commodity: Optional[str], run_number: int) -> Dict[str, Any]:
        """
        Testet ein einzelnes Modell
        """
        start_time = time.time()
        
        try:
            # Bestimme welchen Service zu verwenden
            if self.provider_registry.is_model_available(model_id):
                # Verwende Enhanced Multi-Provider Service
                result = await enhanced_search_service.search_single_model(
                    model_id, mine_name, country, commodity, region
                )
            elif model_id.startswith('perplexity:'):
                # Fallback auf Legacy Perplexity Service
                model_name = model_id.split(':')[1]
                result = await search_service.search_mine(
                    mine_name, country, commodity, model_name, region
                )
            else:
                # Fallback auf Multi-Provider Service
                result = await multi_search_service.search_with_model(
                    model_id, mine_name, country, commodity, region
                )
            
            response_time = (time.time() - start_time) * 1000  # in ms
            
            # Analysiere Ergebnis
            success = result.get('success', False)
            data = result.get('data', {})
            structured_data = data.get('structured_data', {})
            sources = data.get('sources', []) or []  # KORRIGIERT: Ensure not None
            
            # Zähle gefüllte Felder - KORRIGIERT: Nutze count_filled_fields
            from search_utils import count_filled_fields
            fields_found = count_filled_fields(structured_data)
            sources_count = len(sources) if sources else 0  # KORRIGIERT: Safe source counting
            
            # Speichere in Datenbank
            await self._save_test_result(
                model_id, mine_name, country, region, commodity, run_number,
                success, response_time, fields_found, sources_count,
                structured_data, result.get('raw_content', ''), result.get('error')
            )
            
            # Update Sources table if successful and sources found
            if success and sources:
                await self._update_sources_from_result(sources, country, region)
            
            return {
                'success': success,
                'model_id': model_id,
                'mine_name': mine_name,
                'run_number': run_number,
                'response_time_ms': response_time,
                'fields_found': fields_found,
                'sources_count': sources_count,
                'data': data
            }
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"[BENCHMARK] Fehler bei {model_id}: {e}")
            
            # Speichere Fehler in Datenbank
            await self._save_test_result(
                model_id, mine_name, country, region, commodity, run_number,
                False, response_time, 0, 0, {}, '', str(e)
            )
            
            return {
                'success': False,
                'error': str(e),
                'model_id': model_id,
                'mine_name': mine_name,
                'run_number': run_number,
                'response_time_ms': response_time
            }
    
    def _count_filled_fields(self, structured_data: Dict[str, Any]) -> int:
        """
        DEPRECATED: Ersetzt durch count_filled_fields() aus search_utils.py
        Kept for backwards compatibility
        """
        from search_utils import count_filled_fields
        return count_filled_fields(structured_data)
    
    async def _save_test_result(self, model_id: str, mine_name: str, country: Optional[str],
                              region: Optional[str], commodity: Optional[str], run_number: int,
                              success: bool, response_time_ms: float, fields_found: int,
                              sources_count: int, structured_data: Dict, raw_result: str, error: Optional[str]):
        """
        Speichert Test-Ergebnis in der Datenbank
        """
        try:
            with db_manager.get_session() as session:
                # ModelStatistics Eintrag
                stat_entry = ModelStatistics(
                    model_id=model_id,
                    mine_name=mine_name,
                    country=country,
                    region=region,
                    commodity=commodity,
                    run_number=run_number,
                    success=success,
                    response_time_ms=response_time_ms,
                    fields_found=fields_found,
                    sources_count=sources_count,
                    raw_result=raw_result,
                    structured_data=structured_data,
                    error_message=error,
                    timestamp=datetime.now()
                )
                session.add(stat_entry)
                
                # Aktualisiere Feld-Statistiken
                if success and structured_data:
                    self._update_field_statistics_sync(session, model_id, structured_data)
                
                session.commit()
                
        except Exception as e:
            logger.error(f"[BENCHMARK] Fehler beim Speichern der Test-Ergebnisse: {e}")
    
    def _should_exclude_field_for_status(self, field_name: str, activity_status: str) -> bool:
        """
        CONDITIONAL-FIELDS-FIX 15.07.2025: Logische Ausschlüsse für unmögliche Daten
        
        Felder werden ausgeschlossen wenn sie logisch unmöglich sind:
        - "Produktionsende" bei aktiven Minen: Logisch unmöglich
        - "Fördermenge/Jahr" bei geschlossenen Minen: Logisch unmöglich
        
        Diese Felder werden mit aussagekräftigen Status-Markern gefüllt.
        """
        # Conditional logic für logisch unmögliche Felder
        CONDITIONAL_FIELDS = {
            "Produktionsende": ["aktiv", "explorativ", "geplant", "entwicklung"],
            "Fördermenge/Jahr": ["geschlossen", "explorativ", "geplant", "entwicklung"]
        }
        
        if field_name not in CONDITIONAL_FIELDS:
            return False
            
        if not activity_status:
            return False
            
        excluded_statuses = CONDITIONAL_FIELDS[field_name]
        activity_lower = activity_status.lower()
        
        return any(status in activity_lower for status in excluded_statuses)

    async def _update_field_statistics(self, session, model_id: str, structured_data: Dict):
        """
        Aktualisiert Feld-spezifische Statistiken mit conditional logic
        
        ÄNDERUNG 13.07.2025: Conditional statistics für regulatorik-bewusste Auswertung
        """
        activity_status = structured_data.get("Aktivitätsstatus", "")
        
        for field_name in CSV_COLUMNS:
            value = structured_data.get(field_name)
            found = bool(value and str(value).strip() and str(value).strip().lower() not in ['n/a', 'k.a', 'keine daten'])
            
            # Prüfe ob Feld für diesen Status ausgeschlossen werden soll
            should_exclude = self._should_exclude_field_for_status(field_name, activity_status)
            
            # Suche existierenden Eintrag
            field_stat = session.query(FieldStatistics).filter_by(
                model_id=model_id,
                field_name=field_name
            ).first()
            
            # Bestimme ob conditional logic für dieses Feld angewendet wird
            is_conditional_field = field_name in ["Produktionsende", "Fördermenge/Jahr"]
            
            if field_stat:
                # Aktualisiere existierenden Eintrag
                if should_exclude:
                    # Zähle als ausgeschlossen, aber tracke für Transparenz
                    field_stat.excluded_count = getattr(field_stat, 'excluded_count', 0) + 1
                    field_stat.conditional_logic_applied = True
                else:
                    # Normale Statistik-Aktualisierung
                    field_stat.total_searches += 1
                    if found:
                        field_stat.times_found += 1
                    else:
                        field_stat.times_empty += 1
                    field_stat.success_rate = field_stat.times_found / field_stat.total_searches if field_stat.total_searches > 0 else 0.0
                    
                    # Markiere conditional fields auch bei normalen Updates
                    if is_conditional_field:
                        field_stat.conditional_logic_applied = True
                
                field_stat.last_updated = datetime.now()
            else:
                # Erstelle neuen Eintrag
                if should_exclude:
                    # Erstelle Eintrag mit Ausschluss-Zählung
                    field_stat = FieldStatistics(
                        model_id=model_id,
                        field_name=field_name,
                        total_searches=0,
                        times_found=0,
                        times_empty=0,
                        success_rate=0.0,
                        avg_confidence=0.0,
                        excluded_count=1,
                        conditional_logic_applied=True,
                        last_updated=datetime.now()
                    )
                else:
                    # Normale Erstellung
                    field_stat = FieldStatistics(
                        model_id=model_id,
                        field_name=field_name,
                        total_searches=1,
                        times_found=1 if found else 0,
                        times_empty=0 if found else 1,
                        success_rate=1.0 if found else 0.0,
                        avg_confidence=1.0 if found else 0.0,
                        excluded_count=0,
                        conditional_logic_applied=is_conditional_field,
                        last_updated=datetime.now()
                    )
                session.add(field_stat)
    
    async def _update_sources_from_result(self, sources: List[Dict], country: Optional[str], region: Optional[str]):
        """Update Sources table from test result sources"""
        if not sources:
            return
            
        from database import db_manager
        from urllib.parse import urlparse
        
        # Update max 5 sources to avoid spam
        for source in sources[:5]:
            try:
                url = source.get('url', '')
                if not url or not url.startswith('http'):
                    continue
                    
                domain = urlparse(url).netloc
                if domain:
                    db_manager.add_or_update_source(
                        url=url,
                        domain=domain,
                        country=country,
                        region=region,
                        source_type='url'
                    )
                    logger.debug(f"[SOURCES] Updated source: {domain}")
                    
            except Exception as e:
                logger.debug(f"[SOURCES] Source update failed: {e}")
                continue  # Silent fail for source updates

    async def get_all_benchmarks(self) -> List[Dict[str, Any]]:
        """
        Ruft alle Benchmark-Zusammenfassungen ab
        
        Returns:
            Liste mit Benchmark-Zusammenfassungen für alle Modelle
        """
        try:
            with db_manager.get_session() as session:
                # Hole alle ModelStatistics Einträge
                all_stats = session.query(ModelStatistics).all()
                
                if not all_stats:
                    return []
                
                # Gruppiere nach Modell-ID
                model_groups = defaultdict(list)
                for stat in all_stats:
                    model_groups[stat.model_id].append(stat)
                
                summaries = []
                
                for model_id, stats in model_groups.items():
                    # Berechne Statistiken für dieses Modell
                    total_tests = len(stats)
                    successful_tests = len([s for s in stats if s.success])
                    success_rate = successful_tests / total_tests if total_tests > 0 else 0.0
                    
                    # Durchschnittliche Response-Zeit
                    successful_stats = [s for s in stats if s.success and s.response_time_ms > 0]
                    avg_response_time = sum(s.response_time_ms for s in successful_stats) / len(successful_stats) if successful_stats else 0.0
                    
                    # Durchschnittliche Feldanzahl
                    avg_fields = sum(s.fields_found for s in successful_stats) / len(successful_stats) if successful_stats else 0.0
                    
                    # Hole Feld-Statistiken für Konsistenz
                    field_stats = session.query(FieldStatistics).filter_by(model_id=model_id).all()
                    overall_consistency = sum(fs.success_rate for fs in field_stats) / len(field_stats) if field_stats else 0.0
                    
                    # Getestete Minen
                    tested_mines = list(set(s.mine_name for s in stats))
                    
                    # Letzter Test
                    last_test = max(s.timestamp for s in stats) if stats else None
                    
                    summary = {
                        "model_id": model_id,
                        "total_tests": total_tests,
                        "successful_tests": successful_tests,
                        "success_rate": success_rate,
                        "avg_response_time": avg_response_time,
                        "avg_fields_found": avg_fields,
                        "overall_consistency": overall_consistency,
                        "tested_mines": tested_mines,
                        "mine_count": len(tested_mines),
                        "last_test": last_test.isoformat() if last_test else None,
                        "provider": model_id.split(":")[0] if ":" in model_id else "unknown"
                    }
                    
                    summaries.append(summary)
                
                return summaries
                
        except Exception as e:
            logger.error(f"[BENCHMARK] Fehler beim Abrufen der Benchmarks: {e}")
            return []
    
    async def _create_session_summary(self, session_id: str):
        """
        Erstellt Zusammenfassung nach Abschluss einer Session
        """
        try:
            session = self.running_sessions.get(session_id)
            if not session:
                return
            
            results = session.get('results', [])
            successful_results = [r for r in results if r.get('success', False)]
            
            # Berechne Session-Statistiken
            total_tests = len(results)
            successful_tests = len(successful_results)
            success_rate = successful_tests / total_tests if total_tests > 0 else 0
            
            avg_response_time = 0
            avg_fields_found = 0
            
            if successful_results:
                avg_response_time = sum(r.get('response_time_ms', 0) for r in successful_results) / len(successful_results)
                avg_fields_found = sum(r.get('fields_found', 0) for r in successful_results) / len(successful_results)
            
            # Speichere Session-Summary
            session['summary'] = {
                'total_tests': total_tests,
                'successful_tests': successful_tests,
                'success_rate': success_rate,
                'avg_response_time_ms': avg_response_time,
                'avg_fields_found': avg_fields_found,
                'models_tested': session['total_models']
            }
            
            logger.info(f"[BENCHMARK] Session {session_id} Summary: {successful_tests}/{total_tests} erfolgreich "
                       f"({success_rate:.1%}), ⌀{avg_response_time:.0f}ms, ⌀{avg_fields_found:.1f} Felder")
            
        except Exception as e:
            logger.error(f"[BENCHMARK] Fehler beim Erstellen der Session-Summary: {e}")
    
    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Holt Status einer Benchmark-Session
        """
        return self.running_sessions.get(session_id)
    
    def get_all_sessions(self) -> List[Dict[str, Any]]:
        """
        Holt alle Session-Daten
        """
        return list(self.running_sessions.values())
    
    async def get_model_summary(self, model_id: str) -> Dict[str, Any]:
        """
        Holt aggregierte Statistiken für ein Modell
        """
        try:
            with db_manager.get_session() as session:
                # Hole alle Tests für dieses Modell
                stats = session.query(ModelStatistics).filter_by(model_id=model_id).all()
                
                if not stats:
                    return {"model_id": model_id, "total_tests": 0}
                
                total_tests = len(stats)
                successful_tests = len([s for s in stats if s.success])
                success_rate = successful_tests / total_tests
                
                avg_response_time = sum(s.response_time_ms for s in stats if s.success) / successful_tests if successful_tests > 0 else 0
                avg_fields_found = sum(s.fields_found for s in stats if s.success) / successful_tests if successful_tests > 0 else 0
                
                return {
                    "model_id": model_id,
                    "total_tests": total_tests,
                    "successful_tests": successful_tests,
                    "success_rate": success_rate,
                    "avg_response_time_ms": avg_response_time,
                    "avg_fields_found": avg_fields_found,
                    "last_test": max(s.timestamp for s in stats).isoformat()
                }
                
        except Exception as e:
            logger.error(f"[BENCHMARK] Fehler beim Abrufen der Modell-Summary: {e}")
            return {"model_id": model_id, "error": str(e)}
    
    async def validate_database_consistency(self, model_id: str, mine_name: str) -> Dict[str, Any]:
        """
        Validiert Datenbank-Konsistenz für spezifisches Modell und Mine
        """
        validation_results = {
            "model_id": model_id,
            "mine_name": mine_name,
            "checks": {},
            "issues": [],
            "overall_status": "OK"
        }
        
        try:
            with db_manager.get_session() as session:
                # Prüfe ModelStatistics
                stats = session.query(ModelStatistics).filter_by(
                    model_id=model_id, mine_name=mine_name
                ).all()
                
                validation_results["checks"]["model_statistics_count"] = len(stats)
                
                if stats:
                    # Prüfe run_numbers
                    run_numbers = [s.run_number for s in stats]
                    expected_runs = set(range(1, max(run_numbers) + 1))
                    actual_runs = set(run_numbers)
                    
                    if expected_runs != actual_runs:
                        validation_results["issues"].append(f"Fehlende run_numbers: {expected_runs - actual_runs}")
                    
                    # Prüfe Timestamps
                    timestamps = [s.timestamp for s in stats if s.timestamp]
                    if len(timestamps) != len(stats):
                        validation_results["issues"].append("Fehlende Timestamps gefunden")
                    
                    # Prüfe Success-Rate
                    success_count = len([s for s in stats if s.success])
                    if success_count == 0 and len(stats) > 0:
                        validation_results["issues"].append("Alle Tests fehlgeschlagen - Konfigurationsproblem?")
                    
                    validation_results["checks"]["success_rate"] = success_count / len(stats)
                
                # Prüfe FieldStatistics
                field_stats = session.query(FieldStatistics).filter_by(model_id=model_id).all()
                validation_results["checks"]["field_statistics_count"] = len(field_stats)
                
                zero_success_fields = [fs for fs in field_stats if fs.success_rate == 0.0]
                if len(zero_success_fields) == len(field_stats) and field_stats:
                    validation_results["issues"].append("Alle Felder haben 0% Erfolgsrate")
                
                validation_results["checks"]["zero_success_fields"] = len(zero_success_fields)
                
                # Setze Overall-Status
                if validation_results["issues"]:
                    validation_results["overall_status"] = "ISSUES_FOUND"
                
        except Exception as e:
            validation_results["overall_status"] = "ERROR"
            validation_results["error"] = str(e)
            logger.error(f"[BENCHMARK] Fehler bei Datenbank-Validierung: {e}")
        
        return validation_results
    
    async def save_model_statistics(self, model_id: str, mine_name: str, country: Optional[str],
                                   region: Optional[str], commodity: Optional[str], run_number: int,
                                   success: bool, response_time_ms: float, fields_found: int,
                                   sources_count: int, raw_result: Optional[Dict] = None,
                                   structured_data: Optional[Dict] = None, error_message: Optional[str] = None):
        """
        Speichert Model-Statistiken für API-Calls
        
        ÄNDERUNG 12.07.2025: Neue Methode für Standard-API Integration
        """
        try:
            with db_manager.get_session() as session:
                stat_entry = ModelStatistics(
                    model_id=model_id,
                    mine_name=mine_name,
                    country=country,
                    region=region,
                    commodity=commodity,
                    run_number=run_number,
                    timestamp=datetime.now(),
                    success=success,
                    response_time_ms=response_time_ms,
                    fields_found=fields_found,
                    sources_count=sources_count,
                    raw_result=raw_result,
                    structured_data=structured_data,
                    error_message=error_message
                )
                session.add(stat_entry)
                session.commit()
                
                logger.debug(f"[BENCHMARK] Model statistics saved: {model_id}, success={success}, fields={fields_found}")
                
        except Exception as e:
            logger.error(f"[BENCHMARK] Error saving model statistics: {e}")
            raise
    
    async def update_field_statistics(self, model_id: str, structured_data: Dict[str, Any]):
        """
        Aktualisiert Field-Statistiken für ein Modell
        
        ÄNDERUNG 12.07.2025: Neue Methode für Field-Tracking
        """
        try:
            with db_manager.get_session() as session:
                for field_name in CSV_COLUMNS:
                    value = structured_data.get(field_name, '')
                    is_found = bool(value and str(value).strip() and 
                                  str(value).lower() not in ['n/a', 'unknown', '', 'null', 'none'])
                    
                    # Hole oder erstelle FieldStatistics
                    field_stat = session.query(FieldStatistics).filter_by(
                        model_id=model_id, 
                        field_name=field_name
                    ).first()
                    
                    if not field_stat:
                        field_stat = FieldStatistics(
                            model_id=model_id,
                            field_name=field_name,
                            total_searches=0,
                            times_found=0,
                            times_empty=0,
                            success_rate=0.0,
                            avg_confidence=0.0,
                            last_updated=datetime.now()
                        )
                        session.add(field_stat)
                    
                    # Update Statistiken
                    field_stat.total_searches += 1
                    if is_found:
                        field_stat.times_found += 1
                    else:
                        field_stat.times_empty += 1
                    
                    # Berechne neue Success-Rate
                    field_stat.success_rate = field_stat.times_found / field_stat.total_searches
                    field_stat.last_updated = datetime.now()
                
                session.commit()
                logger.debug(f"[BENCHMARK] Field statistics updated for {model_id}")
                
        except Exception as e:
            logger.error(f"[BENCHMARK] Error updating field statistics: {e}")
            raise
    
    def _update_field_statistics_sync(self, session, model_id: str, structured_data: Dict[str, Any]):
        """
        Synchrone Version der Feld-Statistik-Aktualisierung
        """
        try:
            for field_name in CSV_COLUMNS:
                value = structured_data.get(field_name, '')
                is_found = bool(value and str(value).strip() and 
                              str(value).lower() not in ['n/a', 'unknown', '', 'null', 'none'])
                
                # Hole oder erstelle FieldStatistics
                field_stat = session.query(FieldStatistics).filter_by(
                    model_id=model_id, 
                    field_name=field_name
                ).first()
                
                if not field_stat:
                    field_stat = FieldStatistics(
                        model_id=model_id,
                        field_name=field_name,
                        total_searches=0,
                        times_found=0,
                        times_empty=0,
                        success_rate=0.0,
                        avg_confidence=0.0,
                        last_updated=datetime.now()
                    )
                    session.add(field_stat)
                
                # Update Statistiken
                field_stat.total_searches += 1
                if is_found:
                    field_stat.times_found += 1
                else:
                    field_stat.times_empty += 1
                
                # Berechne neue Success-Rate
                field_stat.success_rate = field_stat.times_found / field_stat.total_searches
                field_stat.last_updated = datetime.now()
                
            logger.debug(f"[BENCHMARK] Field statistics updated for {model_id}")
                
        except Exception as e:
            logger.error(f"[BENCHMARK] Error updating field statistics: {e}")
            # Kein raise, da dies eine Hilfsfunktion ist
    
    async def benchmark_model(self, model_id: str, mine_data: Dict[str, str], runs: int, session_id: str) -> Dict[str, Any]:
        """
        Führt Benchmark für ein einzelnes Modell durch
        
        Args:
            model_id: ID des zu testenden Modells
            mine_data: Dictionary mit Mine-Daten (name, country, region, commodity)
            runs: Anzahl der Durchläufe
            session_id: ID der Benchmark-Session
            
        Returns:
            Dictionary mit Benchmark-Ergebnissen
        """
        logger.info(f"[BENCHMARK] Starte Benchmark für {model_id} mit {runs} Runs")
        
        mine_name = mine_data.get('name', '')
        country = mine_data.get('country', '')
        region = mine_data.get('region', '')
        commodity = mine_data.get('commodity', '')
        
        results = []
        total_success = 0
        total_fields = 0
        total_response_time = 0
        
        try:
            for run in range(1, runs + 1):
                logger.info(f"[BENCHMARK] {model_id}: Run {run}/{runs} für {mine_name}")
                
                # Führe einzelnen Test durch
                result = await self._test_single_model(
                    model_id, mine_name, country, region, commodity, run
                )
                
                results.append(result)
                
                if result.get('success'):
                    total_success += 1
                    total_fields += result.get('fields_found', 0)
                    total_response_time += result.get('response_time_ms', 0)
                
                # Kurze Pause zwischen den Runs
                await asyncio.sleep(1)
            
            # Berechne Aggregate
            success_rate = total_success / runs if runs > 0 else 0
            avg_fields = total_fields / total_success if total_success > 0 else 0
            avg_response_time = total_response_time / total_success if total_success > 0 else 0
            
            # MIKRO-TASK 3 FIX 15.07.2025: Entferne fehlenden _update_model_summary Aufruf
            # await self._update_model_summary(model_id, results)  # Methode nicht implementiert, deaktiviert
            
            benchmark_result = {
                'model_id': model_id,
                'mine_name': mine_name,
                'session_id': session_id,
                'total_runs': runs,
                'successful_runs': total_success,
                'success_rate': success_rate,
                'avg_fields_found': avg_fields,
                'avg_response_time_ms': avg_response_time,
                'results': results,
                'completed_at': datetime.now().isoformat()
            }
            
            logger.info(f"[BENCHMARK] {model_id} abgeschlossen: {total_success}/{runs} erfolgreich, {avg_fields:.1f} Felder im Schnitt")
            
            return benchmark_result
            
        except Exception as e:
            logger.error(f"[BENCHMARK] Fehler bei {model_id}: {str(e)}")
            return {
                'model_id': model_id,
                'mine_name': mine_name,
                'session_id': session_id,
                'error': str(e),
                'success': False,
                'completed_at': datetime.now().isoformat()
            }