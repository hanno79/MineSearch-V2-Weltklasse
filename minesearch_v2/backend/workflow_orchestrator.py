"""
Author: rahn
Datum: 25.07.2025
Version: 1.0
Beschreibung: Workflow Orchestrator - Zentrale Koordination aller System-Komponenten
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

from model_selection_coordinator import model_selection_coordinator
from batch_priority_coordinator import batch_priority_coordinator
from database import db_manager

logger = logging.getLogger(__name__)

class WorkflowMode(Enum):
    """Workflow-Modi für verschiedene Anwendungsfälle"""
    SINGLE_MINE_SEARCH = "single_mine"
    BATCH_PROCESSING = "batch_processing"
    COMPREHENSIVE_ANALYSIS = "comprehensive_analysis"
    BENCHMARK_TESTING = "benchmark_testing"
    SYSTEM_VALIDATION = "system_validation"

class WorkflowOrchestrator:
    """
    Zentrale Workflow-Orchestrierung für das MineSearch System
    
    KERNAUFGABEN:
    1. Koordiniert Model Selection Coordinator und Batch Priority Coordinator
    2. Verwaltet System-weite Workflows und Strategien
    3. Überwacht System-Performance und Ressourcen
    4. Bietet einheitliche API für alle Workflow-Operationen
    """
    
    def __init__(self):
        self.model_coordinator = model_selection_coordinator
        self.batch_coordinator = batch_priority_coordinator
        
        # Workflow-Status Tracking
        self._active_workflows = {}
        self._workflow_history = []
        self._system_metrics = {
            'total_workflows': 0,
            'successful_workflows': 0,
            'failed_workflows': 0,
            'average_workflow_duration': 0.0,
            'total_models_coordinated': 0,
            'total_mines_processed': 0
        }
        
        logger.info("[WORKFLOW-ORCHESTRATOR] Initialisiert mit Model Selection & Batch Priority Coordinators")
    
    async def orchestrate_workflow(
        self,
        workflow_mode: WorkflowMode,
        workflow_request: Dict[str, Any],
        session_id: str,
        priority: str = "normal"
    ) -> Dict[str, Any]:
        """
        Orchestriert komplette Workflows basierend auf Modus
        
        Args:
            workflow_mode: Workflow-Typ
            workflow_request: Workflow-spezifische Parameter
            session_id: Session ID
            priority: Workflow-Priorität
            
        Returns:
            Umfassender Workflow-Orchestrierungsbericht
        """
        workflow_id = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{session_id[:8]}"
        start_time = datetime.now()
        
        logger.info(f"[WORKFLOW-ORCHESTRATOR] Starte Workflow-Orchestrierung")
        logger.info(f"[WORKFLOW-ORCHESTRATOR] Workflow ID: {workflow_id}")
        logger.info(f"[WORKFLOW-ORCHESTRATOR] Modus: {workflow_mode.value}")
        logger.info(f"[WORKFLOW-ORCHESTRATOR] Session: {session_id}")
        logger.info(f"[WORKFLOW-ORCHESTRATOR] Priorität: {priority}")
        
        # Registriere aktiven Workflow
        self._active_workflows[workflow_id] = {
            'mode': workflow_mode,
            'session_id': session_id,
            'start_time': start_time,
            'status': 'orchestrating',
            'request': workflow_request
        }
        
        try:
            # Route zu entsprechendem Workflow-Handler
            if workflow_mode == WorkflowMode.SINGLE_MINE_SEARCH:
                result = await self._orchestrate_single_mine_workflow(
                    workflow_request, session_id, priority
                )
            elif workflow_mode == WorkflowMode.BATCH_PROCESSING:
                result = await self._orchestrate_batch_workflow(
                    workflow_request, session_id, priority
                )
            elif workflow_mode == WorkflowMode.COMPREHENSIVE_ANALYSIS:
                result = await self._orchestrate_comprehensive_workflow(
                    workflow_request, session_id, priority
                )
            elif workflow_mode == WorkflowMode.BENCHMARK_TESTING:
                result = await self._orchestrate_benchmark_workflow(
                    workflow_request, session_id, priority
                )
            elif workflow_mode == WorkflowMode.SYSTEM_VALIDATION:
                result = await self._orchestrate_validation_workflow(
                    workflow_request, session_id, priority
                )
            else:
                raise ValueError(f"Unbekannter Workflow-Modus: {workflow_mode}")
            
            execution_duration = (datetime.now() - start_time).total_seconds()
            
            # Erstelle umfassenden Orchestrierungsbericht
            orchestration_report = {
                'success': result.get('success', False),
                'workflow_id': workflow_id,
                'workflow_mode': workflow_mode.value,
                'orchestration_duration_seconds': execution_duration,
                'session_id': session_id,
                'priority': priority,
                
                # Workflow-spezifische Ergebnisse
                'workflow_result': result,
                
                # Orchestrierungs-Metadaten
                'orchestration_metadata': {
                    'coordinators_used': ['model_selection_coordinator', 'batch_priority_coordinator'],
                    'system_integration': True,
                    'thread_safe_operations': True,
                    'database_coordinated': True,
                    'workflow_strategy': result.get('execution_strategy', 'unknown')
                },
                
                # System-Performance Informationen
                'system_performance': await self._collect_system_performance_metrics(),
                
                'timestamp': datetime.now().isoformat()
            }
            
            # Update Workflow-Status
            self._active_workflows[workflow_id]['status'] = 'completed' if result.get('success') else 'failed'
            self._active_workflows[workflow_id]['result'] = orchestration_report
            
            # Archiviere in Workflow-Historie
            self._workflow_history.append({
                'workflow_id': workflow_id,
                'mode': workflow_mode.value,
                'success': result.get('success', False),
                'duration': execution_duration,
                'timestamp': datetime.now().isoformat()
            })
            
            # Update System-Metriken
            self._update_system_metrics(orchestration_report)
            
            # Cleanup
            del self._active_workflows[workflow_id]
            
            logger.info(f"[WORKFLOW-ORCHESTRATOR] Workflow-Orchestrierung abgeschlossen: {workflow_id}")
            logger.info(f"[WORKFLOW-ORCHESTRATOR] Erfolg: {result.get('success', False)}")
            logger.info(f"[WORKFLOW-ORCHESTRATOR] Dauer: {execution_duration:.1f}s")
            
            return orchestration_report
            
        except Exception as e:
            execution_duration = (datetime.now() - start_time).total_seconds()
            logger.error(f"[WORKFLOW-ORCHESTRATOR] Kritischer Fehler in Workflow {workflow_id}: {str(e)}")
            
            # Fehlgeschlagener Workflow
            error_report = {
                'success': False,
                'workflow_id': workflow_id,
                'workflow_mode': workflow_mode.value,
                'error': str(e),
                'orchestration_duration_seconds': execution_duration,
                'session_id': session_id,
                'timestamp': datetime.now().isoformat()
            }
            
            # Cleanup
            if workflow_id in self._active_workflows:
                self._active_workflows[workflow_id]['status'] = 'error'
                del self._active_workflows[workflow_id]
            
            return error_report
    
    async def _orchestrate_single_mine_workflow(
        self,
        workflow_request: Dict[str, Any],
        session_id: str,
        priority: str
    ) -> Dict[str, Any]:
        """
        Orchestriert Single-Mine-Search Workflow
        """
        logger.info("[WORKFLOW-ORCHESTRATOR] Orchestriere Single-Mine Workflow")
        
        mine_name = workflow_request.get('mine_name')
        selected_models = workflow_request.get('selected_models', [])
        country = workflow_request.get('country')
        commodity = workflow_request.get('commodity')
        region = workflow_request.get('region')
        
        if not mine_name or not selected_models:
            return {
                'success': False,
                'error': 'Single-Mine Workflow benötigt mine_name und selected_models',
                'execution_strategy': 'validation_failed'
            }
        
        # Verwende Model Selection Coordinator für garantierte Ausführung
        coordination_result = await self.model_coordinator.coordinate_guaranteed_execution(
            selected_models=selected_models,
            mine_name=mine_name,
            country=country,
            commodity=commodity,
            region=region,
            session_id=session_id,
            allow_fallbacks=workflow_request.get('allow_fallbacks', False),
            max_parallel=workflow_request.get('max_parallel', 10)
        )
        
        # Erweitere mit Workflow-spezifischen Informationen
        coordination_result.update({
            'execution_strategy': 'single_mine_coordinated',
            'workflow_type': 'single_mine_search',
            'orchestrated_by': 'workflow_orchestrator'
        })
        
        return coordination_result
    
    async def _orchestrate_batch_workflow(
        self,
        workflow_request: Dict[str, Any],
        session_id: str,
        priority: str
    ) -> Dict[str, Any]:
        """
        Orchestriert Batch-Processing Workflow
        """
        logger.info("[WORKFLOW-ORCHESTRATOR] Orchestriere Batch-Processing Workflow")
        
        mines_data = workflow_request.get('mines_data', [])
        selected_models = workflow_request.get('selected_models', [])
        batch_options = workflow_request.get('batch_options', {})
        
        if not mines_data or not selected_models:
            return {
                'success': False,
                'error': 'Batch Workflow benötigt mines_data und selected_models',
                'execution_strategy': 'validation_failed'
            }
        
        # Verwende Batch Priority Coordinator für optimierte Batch-Ausführung
        batch_result = await self.batch_coordinator.coordinate_priority_batch_execution(
            mines_data=mines_data,
            selected_models=selected_models,
            session_id=session_id,
            batch_options=batch_options,
            priority_level=priority
        )
        
        # Erweitere mit Workflow-spezifischen Informationen
        batch_result.update({
            'execution_strategy': 'batch_priority_coordinated',
            'workflow_type': 'batch_processing',
            'orchestrated_by': 'workflow_orchestrator'
        })
        
        return batch_result
    
    async def _orchestrate_comprehensive_workflow(
        self,
        workflow_request: Dict[str, Any],
        session_id: str,
        priority: str
    ) -> Dict[str, Any]:
        """
        Orchestriert Comprehensive Analysis Workflow
        """
        logger.info("[WORKFLOW-ORCHESTRATOR] Orchestriere Comprehensive Analysis Workflow")
        
        # Implementierung für comprehensive workflows
        # Könnte mehrere Phasen umfassen: Source Discovery -> Model Execution -> Quality Analysis
        
        try:
            from comprehensive_search_orchestrator import comprehensive_search_orchestrator
            
            mine_name = workflow_request.get('mine_name')
            country = workflow_request.get('country', 'Canada')
            region = workflow_request.get('region', 'Quebec')
            commodity = workflow_request.get('commodity')
            available_models = workflow_request.get('selected_models', [])
            
            comprehensive_result = await comprehensive_search_orchestrator.orchestrate_comprehensive_search(
                mine_name=mine_name,
                country=country,
                region=region,
                commodity=commodity,
                available_models=available_models
            )
            
            comprehensive_result.update({
                'execution_strategy': 'comprehensive_systematic',
                'workflow_type': 'comprehensive_analysis',
                'orchestrated_by': 'workflow_orchestrator'
            })
            
            return comprehensive_result
            
        except Exception as e:
            logger.error(f"[WORKFLOW-ORCHESTRATOR] Comprehensive Workflow Fehler: {str(e)}")
            return {
                'success': False,
                'error': f'Comprehensive Workflow Fehler: {str(e)}',
                'execution_strategy': 'comprehensive_failed'
            }
    
    async def _orchestrate_benchmark_workflow(
        self,
        workflow_request: Dict[str, Any],
        session_id: str,
        priority: str
    ) -> Dict[str, Any]:
        """
        Orchestriert Benchmark-Testing Workflow
        """
        logger.info("[WORKFLOW-ORCHESTRATOR] Orchestriere Benchmark-Testing Workflow")
        
        # Benchmark-spezifische Orchestrierung
        models_to_benchmark = workflow_request.get('models_to_benchmark', [])
        test_mines = workflow_request.get('test_mines', [])
        benchmark_options = workflow_request.get('benchmark_options', {})
        
        # Koordiniere Benchmark-Tests mit Batch Coordinator
        if test_mines and models_to_benchmark:
            benchmark_result = await self.batch_coordinator.coordinate_priority_batch_execution(
                mines_data=test_mines,
                selected_models=models_to_benchmark,
                session_id=session_id,
                batch_options={**benchmark_options, 'benchmark_mode': True},
                priority_level='high'  # Benchmarks haben hohe Priorität
            )
            
            benchmark_result.update({
                'execution_strategy': 'benchmark_coordinated',
                'workflow_type': 'benchmark_testing',
                'orchestrated_by': 'workflow_orchestrator'
            })
            
            return benchmark_result
        else:
            return {
                'success': False,
                'error': 'Benchmark Workflow benötigt models_to_benchmark und test_mines',
                'execution_strategy': 'benchmark_validation_failed'
            }
    
    async def _orchestrate_validation_workflow(
        self,
        workflow_request: Dict[str, Any],
        session_id: str,
        priority: str
    ) -> Dict[str, Any]:
        """
        Orchestriert System-Validation Workflow
        """
        logger.info("[WORKFLOW-ORCHESTRATOR] Orchestriere System-Validation Workflow")
        
        validation_components = workflow_request.get('validation_components', ['model_selection', 'batch_processing', 'database'])
        
        validation_results = {}
        overall_success = True
        
        # Validiere verschiedene System-Komponenten
        if 'model_selection' in validation_components:
            # Test Model Selection Coordinator
            test_result = await self._validate_model_selection_coordinator()
            validation_results['model_selection'] = test_result
            if not test_result.get('success'):
                overall_success = False
        
        if 'batch_processing' in validation_components:
            # Test Batch Priority Coordinator
            test_result = await self._validate_batch_priority_coordinator()
            validation_results['batch_processing'] = test_result
            if not test_result.get('success'):
                overall_success = False
        
        if 'database' in validation_components:
            # Test Database Integration
            test_result = await self._validate_database_integration()
            validation_results['database'] = test_result
            if not test_result.get('success'):
                overall_success = False
        
        return {
            'success': overall_success,
            'validation_results': validation_results,
            'execution_strategy': 'system_validation',
            'workflow_type': 'system_validation',
            'orchestrated_by': 'workflow_orchestrator'
        }
    
    async def _validate_model_selection_coordinator(self) -> Dict[str, Any]:
        """Validiert Model Selection Coordinator"""
        try:
            # Minimal-Test mit einem bekannten Modell
            test_result = await self.model_coordinator.coordinate_guaranteed_execution(
                selected_models=['openrouter:kimi-k2'],
                mine_name='Test Mine',
                country='Canada',
                session_id='validation_test',
                allow_fallbacks=False,
                max_parallel=1
            )
            
            return {
                'success': True,
                'test_result': test_result,
                'component': 'model_selection_coordinator'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'component': 'model_selection_coordinator'
            }
    
    async def _validate_batch_priority_coordinator(self) -> Dict[str, Any]:
        """Validiert Batch Priority Coordinator"""
        try:
            # Minimal-Batch-Test
            test_mines = [{'mine_name': 'Test Mine 1', 'country': 'Canada'}]
            test_models = ['openrouter:kimi-k2']
            
            test_result = await self.batch_coordinator.coordinate_priority_batch_execution(
                mines_data=test_mines,
                selected_models=test_models,
                session_id='validation_test',
                priority_level='high'
            )
            
            return {
                'success': True,
                'test_result': test_result,
                'component': 'batch_priority_coordinator'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'component': 'batch_priority_coordinator'
            }
    
    async def _validate_database_integration(self) -> Dict[str, Any]:
        """Validiert Database Integration"""
        try:
            # Test Database-Verbindung und -Operationen
            test_stats = db_manager.get_statistics()
            
            return {
                'success': True,
                'database_stats': test_stats,
                'component': 'database_integration'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'component': 'database_integration'
            }
    
    async def _collect_system_performance_metrics(self) -> Dict[str, Any]:
        """Sammelt System-Performance Metriken"""
        try:
            # Model Coordinator Stats
            model_coord_stats = self.model_coordinator.get_execution_statistics() if hasattr(self.model_coordinator, 'get_execution_statistics') else {}
            
            # Batch Coordinator Stats
            batch_coord_stats = self.batch_coordinator.get_execution_statistics()
            
            # Database Stats
            db_stats = db_manager.get_statistics()
            
            return {
                'model_coordinator': model_coord_stats,
                'batch_coordinator': batch_coord_stats,
                'database': {
                    'total_results': db_stats.get('total_results', 0),
                    'successful_results': db_stats.get('successful_results', 0),
                    'total_sources': db_stats.get('total_sources', 0)
                },
                'workflow_orchestrator': self._system_metrics
            }
        except Exception as e:
            logger.error(f"[WORKFLOW-ORCHESTRATOR] Fehler beim Sammeln von Performance-Metriken: {str(e)}")
            return {'error': str(e)}
    
    def _update_system_metrics(self, orchestration_report: Dict[str, Any]):
        """Update System-Metriken basierend auf Orchestrierungsbericht"""
        self._system_metrics['total_workflows'] += 1
        
        if orchestration_report.get('success'):
            self._system_metrics['successful_workflows'] += 1
        else:
            self._system_metrics['failed_workflows'] += 1
        
        duration = orchestration_report.get('orchestration_duration_seconds', 0)
        current_avg = self._system_metrics['average_workflow_duration']
        total_workflows = self._system_metrics['total_workflows']
        
        self._system_metrics['average_workflow_duration'] = (
            (current_avg * (total_workflows - 1)) + duration
        ) / total_workflows
        
        # Extrahiere weitere Metriken aus Workflow-Ergebnis
        workflow_result = orchestration_report.get('workflow_result', {})
        batch_stats = workflow_result.get('batch_statistics', {})
        
        self._system_metrics['total_mines_processed'] += batch_stats.get('total_mines', 0)
        self._system_metrics['total_models_coordinated'] += batch_stats.get('total_model_executions', 0)
    
    def get_workflow_status(self, workflow_id: Optional[str] = None) -> Dict[str, Any]:
        """Gibt Workflow-Status zurück"""
        if workflow_id:
            return self._active_workflows.get(workflow_id, {'error': 'Workflow nicht gefunden'})
        else:
            return {
                'active_workflows': len(self._active_workflows),
                'workflow_history_count': len(self._workflow_history),
                'system_metrics': self._system_metrics,
                'recent_workflows': self._workflow_history[-10:] if self._workflow_history else []
            }

# Globale Orchestrator-Instanz
workflow_orchestrator = WorkflowOrchestrator()