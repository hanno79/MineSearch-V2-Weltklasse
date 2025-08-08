#!/usr/bin/env python3
"""
Author: rahn
Datum: 24.07.2025
Version: 1.0
Beschreibung: Optimierte Multi-Model-Batch-Service für echte parallele Modell-Ausführung
ÄNDERUNG 24.07.2025: Behebt kritische Multi-Model-Aggregationsfehler
"""

import asyncio
import logging
import threading
import uuid
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from services_container import services
from database import db_manager
from cost_monitor import cost_monitor
from auto_stats_updater import auto_stats_updater

logger = logging.getLogger(__name__)

# Debug-Logger Setup für intensive Debug-Integration
debug_logger = logging.getLogger(f"{__name__}.debug")
debug_logger.setLevel(logging.DEBUG)

# Session-ID-Generator für umfassendes Tracking
def generate_debug_session_id():
    return f"debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"

class EnhancedMultiModelBatchService:
    """
    Optimierte Multi-Model-Batch-Service Klasse
    
    VERBESSERUNGEN:
    - Echte parallele Modell-Ausführung pro Mine
    - Individuelle Datenbank-Speicherung pro Modell
    - Keine Ergebnis-Aggregation die Daten verliert
    - Verbesserte Fallback-Logik
    """
    
    def __init__(self):
        self.multi_search_service = services.multi_search_service
        self._db_lock = asyncio.Lock()  # Async lock für DB-Operations
    
    async def enhanced_batch_search_per_mine(
        self,
        mine_data: Dict[str, str],
        selected_models: List[str],
        session_id: str,
        search_options: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Führt optimierte Multi-Model-Suche für eine Mine durch
        
        WICHTIG: Jedes Modell wird INDIVIDUELL ausgeführt und gespeichert
        
        Args:
            mine_data: Mine-Informationen (name, country, commodity, region)
            selected_models: Liste der ausgewählten Modelle
            session_id: Session-ID für Tracking
            search_options: Zusätzliche Such-Optionen
            
        Returns:
            Dict mit individuellen Modell-Ergebnissen
        """
        mine_name = mine_data.get('mine_name', '')
        country = mine_data.get('country', '')
        commodity = mine_data.get('commodity', '')
        region = mine_data.get('region', '')
        
        # ENHANCED: Robuste Input-Validierung
        if not mine_name or not mine_name.strip():
            logger.error("[ENHANCED-BATCH] Kein gültiger Minenname angegeben")
            return {'success': False, 'error': 'Kein gültiger Minenname angegeben', 'mine_name': mine_name}
        
        if not selected_models or not isinstance(selected_models, list):
            logger.error(f"[ENHANCED-BATCH] Ungültige Modell-Liste für {mine_name}: {selected_models}")
            return {'success': False, 'error': 'Keine gültigen Modelle angegeben', 'mine_name': mine_name}
        
        if not session_id or not session_id.strip():
            logger.warning(f"[ENHANCED-BATCH] Keine Session ID für {mine_name}, verwende Fallback")
            session_id = f"enhanced_batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        search_options = search_options or {}
        
        logger.info(f"[ENHANCED-BATCH] Starte individuelle Multi-Model-Suche für {mine_name}")
        logger.info(f"[ENHANCED-BATCH] Modelle: {selected_models}")
        
        # ENHANCED 25.07.2025: Cost-Monitoring für individuelle Mine
        mine_batch_id = f"mine_{mine_name}_{session_id}_{datetime.now().strftime('%H%M%S')}"
        try:
            cost_analysis = await cost_monitor.monitor_batch_costs(
                batch_id=mine_batch_id,
                models_list=selected_models,
                mines_count=1,  # Einzelne Mine
                session_id=session_id,
                priority_level="normal"
            )
            logger.info(f"[ENHANCED-BATCH-COST] Cost-Analyse für {mine_name}: ${cost_analysis.get('cost_breakdown', {}).get('estimated_premium_cost_usd', 0):.3f}")
        except Exception as cost_error:
            logger.warning(f"[ENHANCED-BATCH-COST] Cost-Monitoring Fehler für {mine_name}: {str(cost_error)}")
            cost_analysis = None
        
        # STEP 1: Führe jedes Modell INDIVIDUELL aus
        individual_results = {}
        successful_models = []
        failed_models = []
        
        # Erstelle individuelle Tasks für echte Parallelität
        model_tasks = []
        for model_id in selected_models:
            task = self._execute_single_model_search(
                model_id=model_id,
                mine_name=mine_name,
                country=country,
                commodity=commodity,
                region=region,
                search_options=search_options
            )
            model_tasks.append((model_id, task))
        
        # FIXED: Echte Parallelität mit asyncio.gather statt for-loop
        logger.info(f"[ENHANCED-BATCH] Starte {len(model_tasks)} parallele Modell-Ausführungen mit asyncio.gather")
        start_time = datetime.now()
        
        # Extrahiere nur die Tasks für asyncio.gather
        tasks_only = [task for model_id, task in model_tasks]
        
        try:
            # ENHANCED EXCEPTION HANDLING: Führe alle Tasks WIRKLICH parallel aus
            results = await asyncio.gather(*tasks_only, return_exceptions=True)
            
            # VERBESSERTE Ergebnis-Verarbeitung mit detailliertem Error Handling
            for i, (model_id, _) in enumerate(model_tasks):
                result = results[i]
                
                # Handle exceptions from asyncio.gather mit erweiterten Details
                if isinstance(result, Exception):
                    error_type = type(result).__name__
                    error_msg = f"Exception bei {model_id} [{error_type}]: {str(result)}"
                    logger.error(f"[ENHANCED-BATCH-EXCEPTION] {error_msg}")
                    
                    # Bestimme ob Retry sinnvoll wäre
                    retry_candidates = ['TimeoutError', 'ConnectionError', 'RequestException']
                    should_retry = any(candidate in error_type for candidate in retry_candidates)
                    
                    individual_results[model_id] = {
                        'success': False,
                        'error': error_msg,
                        'error_type': error_type,
                        'retry_candidate': should_retry,
                        'data': {},
                        'execution_attempted': True,
                        'failure_timestamp': datetime.now().isoformat()
                    }
                    failed_models.append(model_id)
                    logger.warning(f"[ENHANCED-BATCH-EXCEPTION] Model {model_id} FAILED aber wurde versucht - kein Model-Verlust")
                    continue
                
                individual_results[model_id] = result
                
                if result.get('success'):
                    successful_models.append(model_id)
                    
                    # STEP 2: GUARANTEED DATABASE STORAGE - JEDES Modell-Ergebnis INDIVIDUELL in DB
                    db_save_success = False
                    try:
                        db_save_success = await self._save_individual_model_result(
                            model_id=model_id,
                            mine_name=mine_name,
                            country=country,
                            region=region,
                            commodity=commodity,
                            session_id=session_id,
                            result=result
                        )
                        
                        if db_save_success:
                            logger.info(f"[ENHANCED-BATCH-DB] ✅ {model_id} erfolgreich in DB gespeichert")
                        else:
                            logger.error(f"[ENHANCED-BATCH-DB] ❌ {model_id} DB-Speicherung fehlgeschlagen")
                            
                    except Exception as db_error:
                        logger.error(f"[ENHANCED-BATCH-DB] DB-Exception für {model_id}: {str(db_error)}")
                        db_save_success = False
                    
                    # Erweitere Result mit DB-Status
                    result['database_saved'] = db_save_success
                    result['save_timestamp'] = datetime.now().isoformat()
                else:
                    failed_models.append(model_id)
                    error_details = result.get('error', 'Unbekannter Fehler')
                    logger.warning(f"[ENHANCED-BATCH] {model_id} fehlgeschlagen: {error_details}")
                    
                    # Auch fehlgeschlagene Ergebnisse in DB dokumentieren für Debugging
                    try:
                        await self._save_failed_model_attempt(
                            model_id=model_id,
                            mine_name=mine_name,
                            error=error_details,
                            session_id=session_id
                        )
                    except Exception as db_error:
                        logger.error(f"[ENHANCED-BATCH-DB] Fehler beim Speichern des fehlgeschlagenen Attempts: {str(db_error)}")
                    
        except Exception as e:
            logger.error(f"[ENHANCED-BATCH] Fehler bei asyncio.gather: {str(e)}")
            # Fallback für den Fall dass asyncio.gather komplett fehlschlägt
            for model_id, _ in model_tasks:
                individual_results[model_id] = {
                    'success': False,
                    'error': f"Gather-Fehler: {str(e)}",
                    'data': {}
                }
                failed_models.append(model_id)
        
        search_duration = (datetime.now() - start_time).total_seconds()
        
        # ENHANCED 25.07.2025: Cost-Monitoring Final Analysis
        try:
            if cost_analysis:
                coordination_savings = await cost_monitor.calculate_coordination_savings(
                    batch_id=mine_batch_id,
                    execution_duration=search_duration,
                    successful_operations=len(successful_models),
                    total_operations=len(selected_models)
                )
                logger.info(f"[ENHANCED-BATCH-COST] Koordinations-Einsparungen für {mine_name}: {coordination_savings.get('performance_metrics', {}).get('time_savings_seconds', 0):.1f}s")
            else:
                coordination_savings = None
        except Exception as savings_error:
            logger.warning(f"[ENHANCED-BATCH-COST] Koordinations-Einsparungen Fehler für {mine_name}: {str(savings_error)}")
            coordination_savings = None
        
        # STEP 3: Erstelle umfassende Multi-Model-Antwort
        enhanced_result = {
            'success': len(successful_models) > 0,
            'mine_name': mine_name,
            'country': country,
            'commodity': commodity,
            'region': region,
            'search_duration_seconds': search_duration,
            'models_requested': selected_models,
            'models_successful': successful_models,
            'models_failed': failed_models,
            'individual_results': individual_results,
            'statistics': {
                'total_models': len(selected_models),
                'successful_count': len(successful_models),
                'failed_count': len(failed_models),
                'success_rate': len(successful_models) / len(selected_models) if selected_models else 0
            },
            # ENHANCED 25.07.2025: Cost-Monitoring Integration
            'cost_analysis': cost_analysis,
            'coordination_savings': coordination_savings,
            'cost_monitoring_enabled': cost_analysis is not None,
            'timestamp': datetime.now().isoformat()
        }
        
        # STEP 4: Erstelle kombinierte Daten für Frontend (ohne Datenverlust)
        enhanced_result['combined_data'] = self._create_combined_data_view(individual_results)
        
        logger.info(f"[ENHANCED-BATCH] Abgeschlossen für {mine_name}: {len(successful_models)}/{len(selected_models)} Modelle erfolgreich in {search_duration:.1f}s")
        
        return enhanced_result
    
    async def _execute_single_model_search(
        self,
        model_id: str,
        mine_name: str,
        country: str,
        commodity: str,
        region: str,
        search_options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Führt Suche mit einem einzelnen Modell durch
        
        WICHTIG: Verwendet die originale single-model Methode für maximale Kompatibilität
        """
        try:
            logger.debug(f"[ENHANCED-BATCH] Starte Einzelmodell-Suche: {model_id} für {mine_name}")
            
            # Verwende die bewährte single-model Suche
            result = await self.multi_search_service.search_with_model(
                model_id=model_id,
                mine_name=mine_name,
                country=country,
                commodity=commodity,
                region=region
            )
            
            # Erweitere das Ergebnis um Modell-spezifische Informationen
            if isinstance(result, dict):
                result['model_id'] = model_id
                result['search_timestamp'] = datetime.now().isoformat()
                
                # Analysiere Feldabdeckung
                if result.get('success') and result.get('data'):
                    structured_data = result['data'].get('structured_data', {})
                    filled_fields = [k for k, v in structured_data.items() if v and str(v).strip()]
                    result['field_coverage'] = {
                        'total_fields': len(structured_data),
                        'filled_fields': len(filled_fields),
                        'coverage_percentage': len(filled_fields) / len(structured_data) * 100 if structured_data else 0,
                        'filled_field_names': filled_fields
                    }
                    
                    # Spezielle Restaurationskosten-Prüfung
                    has_restoration_costs = bool(structured_data.get('Restaurationskosten', '').strip())
                    result['found_restoration_costs'] = has_restoration_costs
                    if has_restoration_costs:
                        logger.info(f"[ENHANCED-BATCH] ✅ {model_id} fand Restaurationskosten für {mine_name}: {structured_data['Restaurationskosten']}")
            
            return result
            
        except Exception as e:
            logger.error(f"[ENHANCED-BATCH] Fehler bei Einzelmodell-Suche {model_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'data': {},
                'model_id': model_id,
                'search_timestamp': datetime.now().isoformat()
            }
    
    async def _save_individual_model_result(
        self,
        model_id: str,
        mine_name: str,
        country: str,
        region: str,
        commodity: str,
        session_id: str,
        result: Dict[str, Any],
        debug_session_id: str = None
    ) -> bool:
        """
        Speichert individuelles Modell-Ergebnis in der Datenbank
        
        WICHTIG: Ein separater DB-Eintrag pro Modell!
        FIXED: Verbessertes Exception-Handling
        ENHANCED: Intensive Debug-Integration
        """
        # Debug Session Tracking
        if not debug_session_id:
            debug_session_id = generate_debug_session_id()
        
        debug_logger.critical(f"[DB-SAVE-DEBUG] {debug_session_id} - INDIVIDUAL MODEL SAVE INITIATED")
        debug_logger.critical(f"[DB-SAVE-DEBUG] {debug_session_id} - Model: {model_id}")
        debug_logger.critical(f"[DB-SAVE-DEBUG] {debug_session_id} - Mine: {mine_name}")
        debug_logger.critical(f"[DB-SAVE-DEBUG] {debug_session_id} - Country: {country}")
        debug_logger.critical(f"[DB-SAVE-DEBUG] {debug_session_id} - Region: {region}")
        debug_logger.critical(f"[DB-SAVE-DEBUG] {debug_session_id} - Commodity: {commodity}")
        debug_logger.critical(f"[DB-SAVE-DEBUG] {debug_session_id} - Session ID: {session_id}")
        
        # Debug: Analyze result structure
        debug_logger.info(f"[DB-SAVE-STRUCTURE] {debug_session_id} - Result type: {type(result)}")
        debug_logger.info(f"[DB-SAVE-STRUCTURE] {debug_session_id} - Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        
        try:
            # ENHANCED: Validierung der Input-Parameter mit intensivem Debug-Logging
            if not model_id or not mine_name:
                debug_logger.critical(f"[DB-SAVE-ERROR] {debug_session_id} - CRITICAL PARAMETER MISSING")
                debug_logger.critical(f"[DB-SAVE-ERROR] {debug_session_id} - model_id present: {bool(model_id)}")
                debug_logger.critical(f"[DB-SAVE-ERROR] {debug_session_id} - model_id value: '{model_id}'")
                debug_logger.critical(f"[DB-SAVE-ERROR] {debug_session_id} - mine_name present: {bool(mine_name)}")
                debug_logger.critical(f"[DB-SAVE-ERROR] {debug_session_id} - mine_name value: '{mine_name}'")
                logger.error(f"[ENHANCED-BATCH] Kritische Parameter fehlen: model_id={model_id}, mine_name={mine_name}")
                return False
                
            if not result.get('success') or not result.get('data'):
                logger.warning(f"[ENHANCED-BATCH] Kein erfolgreiches Ergebnis für {model_id} ({mine_name})")
                return False
            
            structured_data = result['data'].get('structured_data', {})
            sources = result['data'].get('sources', [])
            
            if not structured_data:
                logger.warning(f"[ENHANCED-BATCH] Keine structured_data für {model_id} ({mine_name})")
                return False
            
            # ENHANCED: Datenvalidierung vor DB-Speicherung
            try:
                # Validiere structured_data Format
                if not isinstance(structured_data, dict):
                    logger.error(f"[ENHANCED-BATCH] structured_data ist kein Dict für {model_id}: {type(structured_data)}")
                    return False
                
                # Validiere sources Format
                if not isinstance(sources, list):
                    logger.warning(f"[ENHANCED-BATCH] sources ist keine Liste für {model_id}, korrigiere zu []")
                    sources = []
                
            except Exception as validation_error:
                logger.error(f"[ENHANCED-BATCH] Datenvalidierungsfehler für {model_id}: {str(validation_error)}")
                return False
            
            # ENHANCED: DB-Speicherung mit robustem Error Handling
            try:
                db_manager.save_search_result(
                    mine_name=mine_name,
                    model_used=model_id,  # Individuelles Modell!
                    structured_data=structured_data,
                    sources=sources,
                    session_id=session_id,
                    country=country or 'Unknown',  # Fallback für leere Werte
                    region=region or 'Unknown',
                    commodity=commodity or 'Unknown',
                    search_type='enhanced_batch_individual',  # Markierung für neue Implementierung
                    search_duration=result.get('search_duration', 0),
                    success=True
                )
                
                logger.info(f"[ENHANCED-BATCH] ✅ DB-Eintrag gespeichert für Modell {model_id} ({mine_name})")
                
                # ÄNDERUNG 26.07.2025: Automatische ModelStatistics Updates für Batch-Services
                try:
                    search_result_for_stats = {
                        "success": True,
                        "data": {
                            "structured_data": structured_data,
                            "sources": sources
                        }
                    }
                    
                    await auto_stats_updater.update_statistics_after_search(
                        mine_name=mine_name,
                        model_used=model_id,
                        search_result=search_result_for_stats,
                        response_time_ms=result.get('search_duration', 0) * 1000,  # Convert to ms
                        country=country,
                        commodity=commodity,
                        region=region
                    )
                    logger.info(f"[AUTO-STATS-BATCH] ModelStatistics automatisch aktualisiert für {model_id}/{mine_name}")
                except Exception as stats_e:
                    logger.warning(f"[AUTO-STATS-BATCH] Fehler bei automatischem Statistics-Update: {stats_e}")
                
                return True
                
            except Exception as db_error:
                logger.error(f"[ENHANCED-BATCH] Datenbank-Speicherfehler für {model_id}: {str(db_error)}")
                logger.error(f"[ENHANCED-BATCH] DB-Error Details - Mine: {mine_name}, Session: {session_id}")
                return False
            
        except Exception as e:
            logger.error(f"[ENHANCED-BATCH] Unerwarteter Fehler bei _save_individual_model_result für {model_id}: {str(e)}")
            logger.error(f"[ENHANCED-BATCH] Exception Details - Mine: {mine_name}, Result Keys: {list(result.keys()) if result else 'None'}")
            return False
    
    async def _save_failed_model_attempt(
        self,
        model_id: str,
        mine_name: str,
        error: str,
        session_id: str
    ) -> bool:
        """
        Speichert fehlgeschlagene Model-Attempts für Debugging und Statistiken
        
        Args:
            model_id: ID des fehlgeschlagenen Modells
            mine_name: Name der Mine
            error: Fehlermeldung
            session_id: Session-ID
            
        Returns:
            True wenn erfolgreich gespeichert, False sonst
        """
        try:
            # Verwende das DB-Lock für Thread-Safety
            async with self._db_lock:
                db_manager.save_search_result(
                    mine_name=mine_name,
                    model_used=model_id,
                    structured_data={},  # Leere Daten für fehlgeschlagene Attempts
                    sources=[],
                    session_id=session_id,
                    country='Unknown',
                    region='Unknown',
                    commodity='Unknown',
                    search_type='failed_batch_attempt',
                    search_duration=0,
                    success=False,
                    error_message=error
                )
                
                logger.info(f"[ENHANCED-BATCH-FAILED] Fehlgeschlagener Attempt für {model_id} dokumentiert")
                
                # ÄNDERUNG 26.07.2025: Automatische ModelStatistics Updates für fehlgeschlagene Batch-Versuche
                try:
                    failed_search_result = {
                        "success": False,
                        "error": error,
                        "data": {}
                    }
                    
                    await auto_stats_updater.update_statistics_after_search(
                        mine_name=mine_name,
                        model_used=model_id,
                        search_result=failed_search_result,
                        response_time_ms=None,
                        country='Unknown'
                    )
                    logger.info(f"[AUTO-STATS-BATCH-FAILED] Fehlgeschlagene Batch-Suche in ModelStatistics vermerkt für {model_id}/{mine_name}")
                except Exception as stats_e:
                    logger.warning(f"[AUTO-STATS-BATCH-FAILED] Fehler bei Statistics-Update für fehlgeschlagene Batch-Suche: {stats_e}")
                
                return True
                
        except Exception as e:
            logger.error(f"[ENHANCED-BATCH-FAILED] Fehler beim Speichern des fehlgeschlagenen Attempts: {str(e)}")
            return False
    
    def _create_combined_data_view(self, individual_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Erstellt kombinierte Datenansicht ohne Datenverlust
        
        ANSATZ: Sammelt Daten von ALLEN erfolgreichen Modellen
        """
        combined_structured_data = {}
        combined_sources = []
        model_contributions = {}
        
        successful_results = {
            k: v for k, v in individual_results.items() 
            if v.get('success') and v.get('data')
        }
        
        if not successful_results:
            return {'structured_data': {}, 'sources': [], 'model_contributions': {}}
        
        # Sammle Daten von allen erfolgreichen Modellen
        for model_id, result in successful_results.items():
            structured_data = result['data'].get('structured_data', {})
            sources = result['data'].get('sources', [])
            
            # Verfolge welches Modell welche Felder beigetragen hat
            model_contributions[model_id] = []
            
            for field, value in structured_data.items():
                if value and str(value).strip():
                    # Wenn Feld noch nicht vorhanden oder leer, verwende diesen Wert
                    if not combined_structured_data.get(field):
                        combined_structured_data[field] = value
                        model_contributions[model_id].append(field)
                    else:
                        # Optional: Erweiterte Logik für konkurrierende Werte
                        # Hier könntest du Modell-Prioritäten implementieren
                        pass
            
            # Sammle alle Quellen
            for source in sources:
                if source not in combined_sources:
                    combined_sources.append(source)
        
        return {
            'structured_data': combined_structured_data,
            'sources': combined_sources,
            'model_contributions': model_contributions,
            'contributing_models': list(successful_results.keys())
        }

# Service-Instanz für globale Verwendung
enhanced_batch_service = EnhancedMultiModelBatchService()