"""
Author: rahn
Datum: 25.07.2025
Version: 1.0
Beschreibung: Batch Priority Coordinator - Optimiert Batch-Service Priority und Database Integration
"""

import logging
import asyncio
import threading
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from contextlib import asynccontextmanager
from database import db_manager
from model_selection_coordinator import model_selection_coordinator
from cost_monitor import cost_monitor

logger = logging.getLogger(__name__)

class BatchPriorityCoordinator:
    """
    Coordinator für optimierte Batch-Service Prioritäten und Database Integration
    
    KERNPRINZIPIEN:
    1. Thread-Safe Batch-Operationen mit Locking
    2. Prioritäts-basierte Modell-Ausführung
    3. Optimierte Database-Integration ohne Race Conditions
    4. Umfassende Error Recovery und Retry-Logik
    """
    
    def __init__(self):
        # Thread-Safe Locks für verschiedene Operationen
        self._batch_execution_lock = asyncio.Lock()
        self._database_operation_lock = asyncio.Lock()
        self._priority_queue_lock = threading.RLock()
        
        # Priority Queue für Batch-Operationen
        self._priority_queue = []
        self._execution_stats = {
            'total_batches': 0,
            'successful_batches': 0,
            'failed_batches': 0,
            'average_batch_duration': 0.0,
            'total_mines_processed': 0,
            'total_models_executed': 0
        }
        
        logger.info("[BATCH-PRIORITY-COORDINATOR] Initialisiert mit Thread-Safe Locks")
    
    async def coordinate_priority_batch_execution(
        self,
        mines_data: List[Dict[str, Any]],
        selected_models: List[str],
        session_id: str,
        batch_options: Dict[str, Any] = None,
        priority_level: str = "normal"  # high, normal, low
    ) -> Dict[str, Any]:
        """
        Koordiniert prioritäts-basierte Batch-Ausführung
        
        Args:
            mines_data: Liste der Mine-Daten
            selected_models: Ausgewählte Modelle (ALLE werden ausgeführt)
            session_id: Session ID
            batch_options: Batch-spezifische Optionen
            priority_level: Prioritätslevel (high, normal, low)
            
        Returns:
            Umfassender Batch-Koordinationsbericht
        """
        batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{session_id[:8]}"
        start_time = datetime.now()
        
        logger.info(f"[BATCH-PRIORITY-COORDINATOR] Starte prioritäts-basierte Batch-Koordination")
        logger.info(f"[BATCH-PRIORITY-COORDINATOR] Batch ID: {batch_id}")
        logger.info(f"[BATCH-PRIORITY-COORDINATOR] Minen: {len(mines_data)}, Modelle: {len(selected_models)}")
        logger.info(f"[BATCH-PRIORITY-COORDINATOR] Priorität: {priority_level}")
        
        batch_options = batch_options or {}
        
        # STEP 1: Thread-Safe Batch-Execution Lock
        async with self._batch_execution_lock:
            logger.info(f"[BATCH-PRIORITY-COORDINATOR] Batch-Execution Lock erhalten für {batch_id}")
            
            try:
                # ENHANCED 25.07.2025: Cost-Monitoring Integration
                cost_analysis = await cost_monitor.monitor_batch_costs(
                    batch_id=batch_id,
                    models_list=selected_models,
                    mines_count=len(mines_data),
                    session_id=session_id,
                    priority_level=priority_level
                )
                logger.info(f"[BATCH-PRIORITY-COORDINATOR] Cost-Analyse abgeschlossen für {batch_id}")
                
                # STEP 2: Prioritäts-basierte Ausführungsplanung
                execution_plan = await self._create_priority_execution_plan(
                    mines_data=mines_data,
                    selected_models=selected_models,
                    priority_level=priority_level,
                    batch_options=batch_options
                )
                
                # STEP 3: Koordinierte Batch-Ausführung
                batch_results = await self._execute_coordinated_batch(
                    execution_plan=execution_plan,
                    session_id=session_id,
                    batch_id=batch_id,
                    batch_options=batch_options
                )
                
                # STEP 4: Thread-Safe Database-Batch-Operation
                async with self._database_operation_lock:
                    database_results = await self._coordinate_batch_database_operations(
                        batch_results=batch_results,
                        session_id=session_id,
                        batch_id=batch_id
                    )
                
                execution_duration = (datetime.now() - start_time).total_seconds()
                
                # ENHANCED 25.07.2025: Cost-Monitoring Final Analysis
                coordination_savings = await cost_monitor.calculate_coordination_savings(
                    batch_id=batch_id,
                    execution_duration=execution_duration,
                    successful_operations=batch_results['total_successful_model_executions'],
                    total_operations=len(mines_data) * len(selected_models)
                )
                logger.info(f"[BATCH-PRIORITY-COORDINATOR] Koordinations-Einsparungen berechnet für {batch_id}")
                
                # STEP 5: Umfassender Koordinationsbericht
                coordination_report = {
                    'success': batch_results['overall_success'],
                    'batch_id': batch_id,
                    'coordination_mode': 'priority_coordinated_batch',
                    'execution_duration_seconds': execution_duration,
                    'priority_level': priority_level,
                    
                    # Batch-spezifische Statistiken
                    'batch_statistics': {
                        'total_mines': len(mines_data),
                        'total_models_per_mine': len(selected_models),
                        'total_model_executions': len(mines_data) * len(selected_models),
                        'successful_mine_searches': batch_results['successful_mine_count'],
                        'failed_mine_searches': batch_results['failed_mine_count'],
                        'total_successful_model_executions': batch_results['total_successful_model_executions'],
                        'overall_success_rate': batch_results['overall_success_rate'],
                        'average_mine_processing_time': batch_results['average_mine_processing_time']
                    },
                    
                    # Model-spezifische Statistiken
                    'model_performance': batch_results['model_performance_summary'],
                    
                    # Database-Integration Ergebnisse
                    'database_operations': database_results,
                    
                    # ENHANCED 25.07.2025: Cost-Monitoring Integration
                    'cost_analysis': cost_analysis,
                    'coordination_savings': coordination_savings,
                    
                    # Individuelle Mine-Ergebnisse
                    'mine_results': batch_results['individual_mine_results'],
                    
                    # Koordinations-Metadata
                    'execution_plan': execution_plan['plan_summary'],
                    'coordination_locks_used': True,
                    'thread_safe_operations': True,
                    'cost_monitoring_enabled': True,
                    'timestamp': datetime.now().isoformat()
                }
                
                # Update globale Statistiken
                self._update_execution_stats(coordination_report)
                
                logger.info(f"[BATCH-PRIORITY-COORDINATOR] Batch-Koordination abgeschlossen: {batch_id}")
                logger.info(f"[BATCH-PRIORITY-COORDINATOR] Erfolgsrate: {batch_results['overall_success_rate']:.1f}%")
                logger.info(f"[BATCH-PRIORITY-COORDINATOR] Dauer: {execution_duration:.1f}s")
                
                return coordination_report
                
            except Exception as e:
                logger.error(f"[BATCH-PRIORITY-COORDINATOR] Kritischer Fehler in Batch-Koordination {batch_id}: {str(e)}")
                return {
                    'success': False,
                    'batch_id': batch_id,
                    'error': f'Batch-Koordinationsfehler: {str(e)}',
                    'coordination_mode': 'priority_coordinated_batch_failed',
                    'execution_duration_seconds': (datetime.now() - start_time).total_seconds(),
                    'timestamp': datetime.now().isoformat()
                }
    
    async def _create_priority_execution_plan(
        self,
        mines_data: List[Dict[str, Any]],
        selected_models: List[str],
        priority_level: str,
        batch_options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Erstellt prioritäts-basierte Ausführungsplanung
        """
        logger.info(f"[BATCH-PRIORITY-COORDINATOR] Erstelle Ausführungsplan mit Priorität: {priority_level}")
        
        # Prioritäts-basierte Konfiguration
        priority_config = {
            'high': {
                'max_parallel_mines': 3,
                'max_parallel_models_per_mine': 8,
                'retry_failed_models': True,
                'timeout_per_model': 120,
                'database_batch_size': 50
            },
            'normal': {
                'max_parallel_mines': 5,
                'max_parallel_models_per_mine': 6,
                'retry_failed_models': True,
                'timeout_per_model': 90,
                'database_batch_size': 100
            },
            'low': {
                'max_parallel_mines': 8,
                'max_parallel_models_per_mine': 4,
                'retry_failed_models': False,
                'timeout_per_model': 60,
                'database_batch_size': 200
            }
        }
        
        config = priority_config.get(priority_level, priority_config['normal'])
        
        # Mine-Batches basierend auf Parallelität erstellen
        mine_batches = []
        for i in range(0, len(mines_data), config['max_parallel_mines']):
            batch = mines_data[i:i + config['max_parallel_mines']]
            mine_batches.append(batch)
        
        execution_plan = {
            'priority_level': priority_level,
            'config': config,
            'mine_batches': mine_batches,
            'total_batches': len(mine_batches),
            'selected_models': selected_models,
            'estimated_duration_seconds': len(mines_data) * len(selected_models) * (config['timeout_per_model'] / config['max_parallel_models_per_mine']),
            'plan_summary': {
                'total_mines': len(mines_data),
                'batch_count': len(mine_batches),
                'max_parallel_mines': config['max_parallel_mines'],
                'max_parallel_models': config['max_parallel_models_per_mine'],
                'retry_enabled': config['retry_failed_models']
            }
        }
        
        logger.info(f"[BATCH-PRIORITY-COORDINATOR] Ausführungsplan erstellt: {len(mine_batches)} Batches")
        return execution_plan
    
    async def _execute_coordinated_batch(
        self,
        execution_plan: Dict[str, Any],
        session_id: str,
        batch_id: str,
        batch_options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Führt koordinierte Batch-Ausführung durch
        """
        mine_batches = execution_plan['mine_batches']
        selected_models = execution_plan['selected_models']
        config = execution_plan['config']
        
        logger.info(f"[BATCH-PRIORITY-COORDINATOR] Starte koordinierte Batch-Ausführung: {len(mine_batches)} Batches")
        
        all_mine_results = []
        model_performance_tracker = {model_id: {'successful': 0, 'failed': 0, 'total_duration': 0.0} for model_id in selected_models}
        
        # Führe Mine-Batches sequenziell aus (um Überlastung zu vermeiden)
        for batch_idx, mine_batch in enumerate(mine_batches):
            logger.info(f"[BATCH-PRIORITY-COORDINATOR] Verarbeite Mine-Batch {batch_idx + 1}/{len(mine_batches)}")
            
            # Erstelle Tasks für alle Minen im Batch
            mine_tasks = []
            for mine_data in mine_batch:
                task = self._execute_coordinated_mine_search(
                    mine_data=mine_data,
                    selected_models=selected_models,
                    session_id=session_id,
                    config=config,
                    model_performance_tracker=model_performance_tracker
                )
                mine_tasks.append(task)
            
            # Führe Mine-Batch parallel aus
            batch_results = await asyncio.gather(*mine_tasks, return_exceptions=True)
            
            # Verarbeite Batch-Ergebnisse
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"[BATCH-PRIORITY-COORDINATOR] Mine-Task Exception: {str(result)}")
                    all_mine_results.append({
                        'success': False,
                        'error': f'Task Exception: {str(result)}',
                        'mine_name': 'unknown'
                    })
                else:
                    all_mine_results.append(result)
        
        # Berechne Gesamtstatistiken
        successful_mines = [r for r in all_mine_results if r.get('success')]
        failed_mines = [r for r in all_mine_results if not r.get('success')]
        
        total_successful_model_executions = sum([
            r.get('coordination_report', {}).get('total_successful', 0) 
            for r in successful_mines
        ])
        
        total_mine_processing_time = sum([
            r.get('coordination_report', {}).get('coordination_duration_seconds', 0) 
            for r in all_mine_results
        ])
        
        return {
            'overall_success': len(successful_mines) > 0,
            'successful_mine_count': len(successful_mines),
            'failed_mine_count': len(failed_mines),
            'total_successful_model_executions': total_successful_model_executions,
            'overall_success_rate': len(successful_mines) / len(all_mine_results) * 100 if all_mine_results else 0,
            'average_mine_processing_time': total_mine_processing_time / len(all_mine_results) if all_mine_results else 0,
            'model_performance_summary': model_performance_tracker,
            'individual_mine_results': all_mine_results
        }
    
    async def _execute_coordinated_mine_search(
        self,
        mine_data: Dict[str, Any],
        selected_models: List[str],
        session_id: str,
        config: Dict[str, Any],
        model_performance_tracker: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Führt koordinierte Mine-Suche mit Model Selection Coordinator durch
        """
        mine_name = mine_data.get('mine_name', 'Unknown')
        logger.debug(f"[BATCH-PRIORITY-COORDINATOR] Starte koordinierte Mine-Suche: {mine_name}")
        
        try:
            # Verwende Model Selection Coordinator für garantierte Modell-Ausführung
            coordination_result = await model_selection_coordinator.coordinate_guaranteed_execution(
                selected_models=selected_models,
                mine_name=mine_name,
                country=mine_data.get('country'),
                commodity=mine_data.get('commodity'),
                region=mine_data.get('region'),
                session_id=session_id,
                allow_fallbacks=False,  # Strict mode
                max_parallel=config['max_parallel_models_per_mine']
            )
            
            # Update Model Performance Tracker
            for model_id in selected_models:
                if model_id in coordination_result.get('models_successful', []):
                    model_performance_tracker[model_id]['successful'] += 1
                else:
                    model_performance_tracker[model_id]['failed'] += 1
            
            # Erweitere Ergebnis um Mine-spezifische Informationen
            result = {
                'success': coordination_result.get('success', False),
                'mine_name': mine_name,
                'mine_data': mine_data,
                'coordination_report': coordination_result.get('statistics', {}),
                'individual_results': coordination_result.get('individual_results', {}),
                'combined_data': coordination_result.get('combined_data', {}),
                'models_successful': coordination_result.get('models_successful', []),
                'models_failed': coordination_result.get('models_failed', [])
            }
            
            return result
            
        except Exception as e:
            logger.error(f"[BATCH-PRIORITY-COORDINATOR] Fehler bei koordinierter Mine-Suche {mine_name}: {str(e)}")
            return {
                'success': False,
                'mine_name': mine_name,
                'mine_data': mine_data,
                'error': str(e),
                'coordination_report': {},
                'individual_results': {},
                'combined_data': {}
            }
    
    async def _coordinate_batch_database_operations(
        self,
        batch_results: Dict[str, Any],
        session_id: str,
        batch_id: str
    ) -> Dict[str, Any]:
        """
        Koordiniert Thread-Safe Batch-Database-Operationen
        """
        logger.info(f"[BATCH-PRIORITY-COORDINATOR] Starte koordinierte Database-Operationen für {batch_id}")
        
        successful_saves = 0
        failed_saves = 0
        database_errors = []
        
        # Sammle alle individuellen Modell-Ergebnisse für Database-Speicherung
        all_individual_results = []
        
        for mine_result in batch_results['individual_mine_results']:
            if mine_result.get('success') and mine_result.get('individual_results'):
                mine_name = mine_result['mine_name']
                mine_data = mine_result.get('mine_data', {})
                
                for model_id, model_result in mine_result['individual_results'].items():
                    if model_result.get('success') and model_result.get('data'):
                        all_individual_results.append({
                            'mine_name': mine_name,
                            'mine_data': mine_data,
                            'model_id': model_id,
                            'model_result': model_result
                        })
        
        logger.info(f"[BATCH-PRIORITY-COORDINATOR] Speichere {len(all_individual_results)} individuelle Modell-Ergebnisse")
        
        # Thread-Safe Database-Speicherung
        for result_data in all_individual_results:
            try:
                db_manager.save_search_result(
                    mine_name=result_data['mine_name'],
                    model_used=result_data['model_id'],
                    structured_data=result_data['model_result']['data'].get('structured_data', {}),
                    sources=result_data['model_result']['data'].get('sources', []),
                    session_id=session_id,
                    country=result_data['mine_data'].get('country'),
                    region=result_data['mine_data'].get('region'),
                    commodity=result_data['mine_data'].get('commodity'),
                    search_type='priority_coordinated_batch',
                    search_duration=result_data['model_result'].get('search_duration', 0),
                    success=True
                )
                successful_saves += 1
                
            except Exception as db_error:
                failed_saves += 1
                error_msg = f"DB-Save Fehler für {result_data['model_id']}/{result_data['mine_name']}: {str(db_error)}"
                database_errors.append(error_msg)
                logger.error(f"[BATCH-PRIORITY-COORDINATOR] {error_msg}")
        
        database_operation_result = {
            'total_individual_results': len(all_individual_results),
            'successful_saves': successful_saves,
            'failed_saves': failed_saves,
            'success_rate': successful_saves / len(all_individual_results) * 100 if all_individual_results else 0,
            'database_errors': database_errors,
            'thread_safe_operations': True
        }
        
        logger.info(f"[BATCH-PRIORITY-COORDINATOR] Database-Operationen abgeschlossen: {successful_saves}/{len(all_individual_results)} erfolgreich")
        
        return database_operation_result
    
    def _update_execution_stats(self, coordination_report: Dict[str, Any]):
        """
        Update globale Ausführungsstatistiken
        """
        with self._priority_queue_lock:
            self._execution_stats['total_batches'] += 1
            
            if coordination_report.get('success'):
                self._execution_stats['successful_batches'] += 1
            else:
                self._execution_stats['failed_batches'] += 1
            
            batch_stats = coordination_report.get('batch_statistics', {})
            self._execution_stats['total_mines_processed'] += batch_stats.get('total_mines', 0)
            self._execution_stats['total_models_executed'] += batch_stats.get('total_model_executions', 0)
            
            # Update durchschnittliche Batch-Dauer
            current_duration = coordination_report.get('execution_duration_seconds', 0)
            total_batches = self._execution_stats['total_batches']
            current_avg = self._execution_stats['average_batch_duration']
            self._execution_stats['average_batch_duration'] = ((current_avg * (total_batches - 1)) + current_duration) / total_batches
    
    def get_execution_statistics(self) -> Dict[str, Any]:
        """
        Gibt aktuelle Ausführungsstatistiken zurück
        """
        with self._priority_queue_lock:
            return {
                **self._execution_stats,
                'timestamp': datetime.now().isoformat()
            }

# Globale Coordinator-Instanz
batch_priority_coordinator = BatchPriorityCoordinator()