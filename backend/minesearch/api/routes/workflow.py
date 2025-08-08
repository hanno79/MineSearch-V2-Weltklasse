"""
Author: rahn
Datum: 25.07.2025
Version: 1.0
Beschreibung: Workflow Orchestrator API Routes - Zentrale Workflow-Steuerung
"""

from fastapi import APIRouter, HTTPException, Form, Query
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime

from workflow_orchestrator import workflow_orchestrator, WorkflowMode

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/workflow/status")
async def get_workflow_status(workflow_id: Optional[str] = Query(None)):
    """
    Gibt Workflow-Status zurück
    
    Args:
        workflow_id: Spezifische Workflow-ID (optional)
        
    Returns:
        Workflow-Status oder System-Übersicht
    """
    try:
        status = workflow_orchestrator.get_workflow_status(workflow_id)
        return JSONResponse(content={
            'success': True,
            'status': status,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"[WORKFLOW-API] Fehler beim Abrufen des Workflow-Status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Workflow-Status Fehler: {str(e)}")

@router.post("/workflow/orchestrate/single-mine")
async def orchestrate_single_mine_workflow(
    mine_name: str = Form(...),
    selected_models: str = Form(..., description="Komma-getrennte Modell-Liste"),
    country: Optional[str] = Form(None),
    commodity: Optional[str] = Form(None),
    region: Optional[str] = Form(None),
    session_id: str = Form(...),
    priority: str = Form("normal", description="Priorität: high, normal, low"),
    allow_fallbacks: bool = Form(False),
    max_parallel: int = Form(10)
):
    """
    Orchestriert Single-Mine Search Workflow
    
    Args:
        mine_name: Name der Mine
        selected_models: Komma-getrennte Liste der Modelle
        country: Land (optional)
        commodity: Rohstoff (optional)
        region: Region (optional)
        session_id: Session ID
        priority: Workflow-Priorität
        allow_fallbacks: Fallbacks erlauben
        max_parallel: Maximale parallele Ausführungen
        
    Returns:
        Workflow-Orchestrierungsergebnis
    """
    try:
        logger.info(f"[WORKFLOW-API] Single-Mine Workflow angefordert für: {mine_name}")
        
        # Parse Modell-Liste
        models_list = [m.strip() for m in selected_models.split(',') if m.strip()]
        
        if not models_list:
            raise HTTPException(
                status_code=400,
                detail="Mindestens ein gültiges Modell muss ausgewählt werden"
            )
        
        # Bereite Workflow-Request vor
        workflow_request = {
            'mine_name': mine_name,
            'selected_models': models_list,
            'country': country,
            'commodity': commodity,
            'region': region,
            'allow_fallbacks': allow_fallbacks,
            'max_parallel': max_parallel
        }
        
        # Orchestriere Workflow
        orchestration_result = await workflow_orchestrator.orchestrate_workflow(
            workflow_mode=WorkflowMode.SINGLE_MINE_SEARCH,
            workflow_request=workflow_request,
            session_id=session_id,
            priority=priority
        )
        
        return JSONResponse(content=orchestration_result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[WORKFLOW-API] Single-Mine Workflow Fehler: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Single-Mine Workflow Fehler: {str(e)}")

@router.post("/workflow/orchestrate/batch")
async def orchestrate_batch_workflow(
    mines_data: str = Form(..., description="JSON-String mit Mine-Daten"),
    selected_models: str = Form(..., description="Komma-getrennte Modell-Liste"),
    session_id: str = Form(...),
    priority: str = Form("normal", description="Priorität: high, normal, low"),
    comprehensive_search: str = Form("false"),
    consistency_check: str = Form("false"),
    consistency_runs: int = Form(3)
):
    """
    Orchestriert Batch-Processing Workflow
    
    Args:
        mines_data: JSON-String mit Mine-Daten
        selected_models: Komma-getrennte Liste der Modelle
        session_id: Session ID
        priority: Workflow-Priorität
        comprehensive_search: Comprehensive Search aktivieren
        consistency_check: Consistency Check aktivieren
        consistency_runs: Anzahl Consistency Runs
        
    Returns:
        Batch-Workflow-Orchestrierungsergebnis
    """
    try:
        import json
        
        logger.info(f"[WORKFLOW-API] Batch Workflow angefordert für Session: {session_id}")
        
        # Parse Mine-Daten
        try:
            mines_list = json.loads(mines_data)
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Ungültiges JSON-Format für mines_data: {str(e)}"
            )
        
        # Parse Modell-Liste
        models_list = [m.strip() for m in selected_models.split(',') if m.strip()]
        
        if not models_list:
            raise HTTPException(
                status_code=400,
                detail="Mindestens ein gültiges Modell muss ausgewählt werden"
            )
        
        if not mines_list:
            raise HTTPException(
                status_code=400,
                detail="Mindestens eine Mine muss angegeben werden"
            )
        
        # Bereite Workflow-Request vor
        workflow_request = {
            'mines_data': mines_list,
            'selected_models': models_list,
            'batch_options': {
                'comprehensive_search': comprehensive_search,
                'consistency_check': consistency_check,
                'consistency_runs': consistency_runs
            }
        }
        
        # Orchestriere Batch-Workflow
        orchestration_result = await workflow_orchestrator.orchestrate_workflow(
            workflow_mode=WorkflowMode.BATCH_PROCESSING,
            workflow_request=workflow_request,
            session_id=session_id,
            priority=priority
        )
        
        return JSONResponse(content=orchestration_result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[WORKFLOW-API] Batch Workflow Fehler: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Batch Workflow Fehler: {str(e)}")

@router.post("/workflow/orchestrate/comprehensive")
async def orchestrate_comprehensive_workflow(
    mine_name: str = Form(...),
    selected_models: str = Form(..., description="Komma-getrennte Modell-Liste"),
    country: str = Form("Canada"),
    region: str = Form("Quebec"),
    commodity: Optional[str] = Form(None),
    session_id: str = Form(...),
    priority: str = Form("high")
):
    """
    Orchestriert Comprehensive Analysis Workflow
    
    Args:
        mine_name: Name der Mine
        selected_models: Komma-getrennte Liste der Modelle
        country: Land
        region: Region
        commodity: Rohstoff (optional)
        session_id: Session ID
        priority: Workflow-Priorität
        
    Returns:
        Comprehensive-Workflow-Orchestrierungsergebnis
    """
    try:
        logger.info(f"[WORKFLOW-API] Comprehensive Workflow angefordert für: {mine_name}")
        
        # Parse Modell-Liste
        models_list = [m.strip() for m in selected_models.split(',') if m.strip()]
        
        if not models_list:
            raise HTTPException(
                status_code=400,
                detail="Mindestens ein gültiges Modell muss ausgewählt werden"
            )
        
        # Bereite Workflow-Request vor
        workflow_request = {
            'mine_name': mine_name,
            'selected_models': models_list,
            'country': country,
            'region': region,
            'commodity': commodity
        }
        
        # Orchestriere Comprehensive-Workflow
        orchestration_result = await workflow_orchestrator.orchestrate_workflow(
            workflow_mode=WorkflowMode.COMPREHENSIVE_ANALYSIS,
            workflow_request=workflow_request,
            session_id=session_id,
            priority=priority
        )
        
        return JSONResponse(content=orchestration_result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[WORKFLOW-API] Comprehensive Workflow Fehler: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Comprehensive Workflow Fehler: {str(e)}")

@router.post("/workflow/orchestrate/benchmark")
async def orchestrate_benchmark_workflow(
    models_to_benchmark: str = Form(..., description="Komma-getrennte Modell-Liste für Benchmark"),
    test_mines_data: str = Form(..., description="JSON-String mit Test-Mine-Daten"),
    session_id: str = Form(...),
    benchmark_iterations: int = Form(1),
    max_parallel_models: int = Form(5)
):
    """
    Orchestriert Benchmark-Testing Workflow
    
    Args:
        models_to_benchmark: Komma-getrennte Liste der zu testenden Modelle
        test_mines_data: JSON-String mit Test-Mine-Daten
        session_id: Session ID
        benchmark_iterations: Anzahl Benchmark-Iterationen
        max_parallel_models: Maximale parallele Modell-Ausführungen
        
    Returns:
        Benchmark-Workflow-Orchestrierungsergebnis
    """
    try:
        import json
        
        logger.info(f"[WORKFLOW-API] Benchmark Workflow angefordert für Session: {session_id}")
        
        # Parse Test-Mine-Daten
        try:
            test_mines_list = json.loads(test_mines_data)
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Ungültiges JSON-Format für test_mines_data: {str(e)}"
            )
        
        # Parse Modell-Liste
        models_list = [m.strip() for m in models_to_benchmark.split(',') if m.strip()]
        
        if not models_list:
            raise HTTPException(
                status_code=400,
                detail="Mindestens ein Modell muss für Benchmark ausgewählt werden"
            )
        
        if not test_mines_list:
            raise HTTPException(
                status_code=400,
                detail="Mindestens eine Test-Mine muss angegeben werden"
            )
        
        # Bereite Workflow-Request vor
        workflow_request = {
            'models_to_benchmark': models_list,
            'test_mines': test_mines_list,
            'benchmark_options': {
                'iterations': benchmark_iterations,
                'max_parallel_models': max_parallel_models,
                'detailed_metrics': True
            }
        }
        
        # Orchestriere Benchmark-Workflow
        orchestration_result = await workflow_orchestrator.orchestrate_workflow(
            workflow_mode=WorkflowMode.BENCHMARK_TESTING,
            workflow_request=workflow_request,
            session_id=session_id,
            priority='high'  # Benchmarks haben immer hohe Priorität
        )
        
        return JSONResponse(content=orchestration_result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[WORKFLOW-API] Benchmark Workflow Fehler: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Benchmark Workflow Fehler: {str(e)}")

@router.post("/workflow/orchestrate/system-validation")
async def orchestrate_system_validation_workflow(
    validation_components: str = Form("model_selection,batch_processing,database", description="Komma-getrennte Liste der zu validierenden Komponenten"),
    session_id: str = Form(...),
    detailed_validation: bool = Form(True)
):
    """
    Orchestriert System-Validation Workflow
    
    Args:
        validation_components: Komma-getrennte Liste der zu validierenden Komponenten
        session_id: Session ID
        detailed_validation: Detaillierte Validierung aktivieren
        
    Returns:
        System-Validation-Workflow-Orchestrierungsergebnis
    """
    try:
        logger.info(f"[WORKFLOW-API] System-Validation Workflow angefordert für Session: {session_id}")
        
        # Parse Validierungs-Komponenten
        components_list = [c.strip() for c in validation_components.split(',') if c.strip()]
        
        valid_components = ['model_selection', 'batch_processing', 'database', 'comprehensive_search']
        invalid_components = [c for c in components_list if c not in valid_components]
        
        if invalid_components:
            raise HTTPException(
                status_code=400,
                detail=f"Ungültige Validierungs-Komponenten: {invalid_components}. Gültig: {valid_components}"
            )
        
        # Bereite Workflow-Request vor
        workflow_request = {
            'validation_components': components_list,
            'detailed_validation': detailed_validation
        }
        
        # Orchestriere System-Validation-Workflow
        orchestration_result = await workflow_orchestrator.orchestrate_workflow(
            workflow_mode=WorkflowMode.SYSTEM_VALIDATION,
            workflow_request=workflow_request,
            session_id=session_id,
            priority='high'  # System-Validierung hat hohe Priorität
        )
        
        return JSONResponse(content=orchestration_result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[WORKFLOW-API] System-Validation Workflow Fehler: {str(e)}")
        raise HTTPException(status_code=500, detail=f"System-Validation Workflow Fehler: {str(e)}")

@router.get("/workflow/system-performance")
async def get_system_performance():
    """
    Gibt System-Performance Metriken zurück
    
    Returns:
        Umfassende System-Performance Informationen
    """
    try:
        # Sammle Performance-Metriken von allen Coordinators
        from model_selection_coordinator import model_selection_coordinator
        from batch_priority_coordinator import batch_priority_coordinator
        from database import db_manager
        
        # Workflow Orchestrator Status
        orchestrator_status = workflow_orchestrator.get_workflow_status()
        
        # Batch Coordinator Stats
        batch_stats = batch_priority_coordinator.get_execution_statistics()
        
        # Database Stats
        db_stats = db_manager.get_statistics()
        
        system_performance = {
            'timestamp': datetime.now().isoformat(),
            'workflow_orchestrator': orchestrator_status,
            'batch_priority_coordinator': batch_stats,
            'database_manager': {
                'total_results': db_stats.get('total_results', 0),
                'successful_results': db_stats.get('successful_results', 0),
                'total_sources': db_stats.get('total_sources', 0),
                'results_by_model': db_stats.get('results_by_model', {}),
                'average_data_quality': db_stats.get('average_data_quality', 0)
            },
            'system_integration': {
                'coordinators_active': True,
                'thread_safe_operations': True,
                'database_coordinated': True,
                'workflow_orchestrated': True
            }
        }
        
        return JSONResponse(content={
            'success': True,
            'system_performance': system_performance
        })
        
    except Exception as e:
        logger.error(f"[WORKFLOW-API] System-Performance Fehler: {str(e)}")
        raise HTTPException(status_code=500, detail=f"System-Performance Fehler: {str(e)}")

@router.get("/workflow/health-check")
async def workflow_health_check():
    """
    Führt einen umfassenden Workflow-System Health Check durch
    
    Returns:
        Health Check Ergebnis für alle Workflow-Komponenten
    """
    try:
        logger.info("[WORKFLOW-API] Health Check angefordert")
        
        # Führe System-Validation Workflow für Health Check durch
        health_check_result = await workflow_orchestrator.orchestrate_workflow(
            workflow_mode=WorkflowMode.SYSTEM_VALIDATION,
            workflow_request={
                'validation_components': ['model_selection', 'batch_processing', 'database'],
                'detailed_validation': False
            },
            session_id=f"health_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            priority='high'
        )
        
        return JSONResponse(content={
            'success': True,
            'health_check': health_check_result,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"[WORKFLOW-API] Health Check Fehler: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Health Check Fehler: {str(e)}")