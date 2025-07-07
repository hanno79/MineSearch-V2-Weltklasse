"""
Author: rahn
Datum: 07.07.2025
Version: 1.0
Beschreibung: API-Endpoints für Modell-Benchmarks und Statistiken
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging
import uuid
from datetime import datetime

from model_benchmark_service import ModelBenchmarkService
from database import db_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/benchmark", tags=["benchmark"])

# Benchmark-Service Instanz
benchmark_service = ModelBenchmarkService()

# Laufende Benchmark-Sessions
benchmark_sessions = {}


class BenchmarkRequest(BaseModel):
    """Request-Model für Benchmark-Start"""
    model_ids: List[str] = Field(..., description="Liste der zu testenden Modell-IDs")
    mine_name: str = Field(..., description="Name der Mine")
    country: Optional[str] = Field(None, description="Land")
    region: Optional[str] = Field(None, description="Region")
    commodity: Optional[str] = Field(None, description="Rohstoff")
    runs: int = Field(5, ge=1, le=10, description="Anzahl Durchläufe pro Modell")


class BenchmarkStatus(BaseModel):
    """Status einer Benchmark-Session"""
    session_id: str
    status: str  # running, completed, failed
    progress: float  # 0.0 bis 1.0
    current_model: Optional[str]
    models_completed: int
    total_models: int
    started_at: str
    completed_at: Optional[str]
    error: Optional[str]


async def run_benchmark_task(
    session_id: str,
    model_ids: List[str],
    mine_data: Dict[str, str],
    runs: int
):
    """Background-Task für Benchmark-Durchführung"""
    session = benchmark_sessions[session_id]
    
    try:
        session['status'] = 'running'
        session['started_at'] = datetime.now().isoformat()
        
        for i, model_id in enumerate(model_ids):
            session['current_model'] = model_id
            session['progress'] = i / len(model_ids)
            
            logger.info(f"[BENCHMARK] Session {session_id}: Teste {model_id}")
            
            try:
                result = await benchmark_service.benchmark_model(
                    model_id=model_id,
                    mine_data=mine_data,
                    runs=runs,
                    session_id=session_id
                )
                
                session['results'][model_id] = result
                session['models_completed'] += 1
                
            except Exception as e:
                logger.error(f"[BENCHMARK] Fehler bei {model_id}: {str(e)}")
                session['results'][model_id] = {
                    'error': str(e),
                    'success': False
                }
        
        session['status'] = 'completed'
        session['progress'] = 1.0
        session['completed_at'] = datetime.now().isoformat()
        
    except Exception as e:
        logger.error(f"[BENCHMARK] Session {session_id} fehlgeschlagen: {str(e)}")
        session['status'] = 'failed'
        session['error'] = str(e)


@router.post("/start", response_model=Dict[str, str])
async def start_benchmark(
    request: BenchmarkRequest,
    background_tasks: BackgroundTasks
):
    """
    Startet einen neuen Benchmark-Durchlauf
    
    Returns:
        Dict mit session_id
    """
    # Erstelle Session-ID
    session_id = str(uuid.uuid4())
    
    # Erstelle Mine-Daten
    mine_data = {
        'name': request.mine_name,
        'country': request.country or '',
        'region': request.region or '',
        'commodity': request.commodity or ''
    }
    
    # Initialisiere Session
    benchmark_sessions[session_id] = {
        'session_id': session_id,
        'status': 'pending',
        'progress': 0.0,
        'current_model': None,
        'models_completed': 0,
        'total_models': len(request.model_ids),
        'model_ids': request.model_ids,
        'mine_data': mine_data,
        'runs': request.runs,
        'results': {},
        'started_at': None,
        'completed_at': None,
        'error': None
    }
    
    # Starte Background-Task
    background_tasks.add_task(
        run_benchmark_task,
        session_id,
        request.model_ids,
        mine_data,
        request.runs
    )
    
    logger.info(f"[BENCHMARK] Session {session_id} gestartet für {len(request.model_ids)} Modelle")
    
    return {"session_id": session_id}


@router.get("/status/{session_id}", response_model=BenchmarkStatus)
async def get_benchmark_status(session_id: str):
    """
    Ruft den Status einer Benchmark-Session ab
    
    Args:
        session_id: ID der Benchmark-Session
        
    Returns:
        BenchmarkStatus
    """
    if session_id not in benchmark_sessions:
        raise HTTPException(status_code=404, detail="Session nicht gefunden")
    
    session = benchmark_sessions[session_id]
    
    return BenchmarkStatus(
        session_id=session_id,
        status=session['status'],
        progress=session['progress'],
        current_model=session['current_model'],
        models_completed=session['models_completed'],
        total_models=session['total_models'],
        started_at=session['started_at'] or datetime.now().isoformat(),
        completed_at=session.get('completed_at'),
        error=session.get('error')
    )


@router.get("/results")
async def get_all_benchmark_results(
    model_id: Optional[str] = Query(None, description="Filtere nach Modell-ID"),
    mine_name: Optional[str] = Query(None, description="Filtere nach Mine"),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Ruft alle Benchmark-Ergebnisse ab
    
    Args:
        model_id: Optional Filter nach Modell
        mine_name: Optional Filter nach Mine
        limit: Maximale Anzahl Ergebnisse
        
    Returns:
        Liste von Benchmark-Ergebnissen
    """
    with db_manager.get_session() as session:
        from database import ModelStatistics
        
        query = session.query(ModelStatistics)
        
        if model_id:
            query = query.filter_by(model_id=model_id)
        if mine_name:
            query = query.filter_by(mine_name=mine_name)
        
        results = query.order_by(
            ModelStatistics.timestamp.desc()
        ).limit(limit).all()
        
        return {
            'total': len(results),
            'results': [r.to_dict() for r in results]
        }


@router.get("/model/{model_id}")
async def get_model_benchmark_summary(model_id: str):
    """
    Ruft Benchmark-Zusammenfassung für ein Modell ab
    
    Args:
        model_id: ID des Modells
        
    Returns:
        Modell-Zusammenfassung mit Statistiken
    """
    summary = await benchmark_service.get_benchmark_summary(model_id)
    
    if not summary:
        raise HTTPException(status_code=404, detail="Keine Benchmark-Daten für dieses Modell")
    
    return summary


@router.get("/field-consistency")
async def get_field_consistency_data(
    model_id: Optional[str] = Query(None, description="Filtere nach Modell-ID"),
    mine_name: Optional[str] = Query(None, description="Filtere nach Mine"),
    field_name: Optional[str] = Query(None, description="Filtere nach Feld")
):
    """
    Ruft Feld-Konsistenz-Daten ab
    
    Args:
        model_id: Optional Filter nach Modell
        mine_name: Optional Filter nach Mine
        field_name: Optional Filter nach Feld
        
    Returns:
        Liste von Feld-Konsistenz-Daten
    """
    consistencies = await benchmark_service.get_field_consistencies(
        model_id=model_id,
        mine_name=mine_name
    )
    
    # Filtere nach Feld wenn gewünscht
    if field_name:
        consistencies = [c for c in consistencies if c['field_name'] == field_name]
    
    return {
        'total': len(consistencies),
        'results': consistencies
    }


@router.get("/summary")
async def get_benchmark_summary():
    """
    Ruft Gesamt-Zusammenfassung aller Benchmarks ab
    
    Returns:
        Zusammenfassung mit Top-Modellen und Statistiken
    """
    summaries = await benchmark_service.get_all_benchmarks()
    
    # Sortiere nach verschiedenen Kriterien
    by_success_rate = sorted(summaries, key=lambda x: x['success_rate'], reverse=True)
    by_consistency = sorted(summaries, key=lambda x: x['overall_consistency'], reverse=True)
    by_fields = sorted(summaries, key=lambda x: x['avg_fields_found'], reverse=True)
    by_speed = sorted(summaries, key=lambda x: x['avg_response_time_ms'])
    
    return {
        'total_models': len(summaries),
        'top_by_success_rate': by_success_rate[:5],
        'top_by_consistency': by_consistency[:5],
        'top_by_fields': by_fields[:5],
        'fastest_models': by_speed[:5],
        'all_models': summaries
    }


@router.delete("/session/{session_id}")
async def delete_benchmark_session(session_id: str):
    """
    Löscht eine Benchmark-Session aus dem Speicher
    
    Args:
        session_id: ID der zu löschenden Session
        
    Returns:
        Bestätigung
    """
    if session_id not in benchmark_sessions:
        raise HTTPException(status_code=404, detail="Session nicht gefunden")
    
    del benchmark_sessions[session_id]
    
    return {"message": "Session gelöscht", "session_id": session_id}


@router.post("/capture")
async def capture_search_statistics(stats_data: Dict[str, Any]):
    """
    Erfasst Statistiken von normalen Suchen
    
    ÄNDERUNG 07.07.2025: Normale Suchen werden auch für Statistiken erfasst
    
    Args:
        stats_data: Statistik-Daten von einer normalen Suche
        
    Returns:
        Bestätigung
    """
    try:
        # Erstelle ModelStatistics-Eintrag
        with db_manager.get_session() as session:
            from database import ModelStatistics
            
            stat = ModelStatistics(
                model_id=stats_data['model_id'],
                mine_name=stats_data['mine_name'],
                country=stats_data.get('country'),
                region=stats_data.get('region'),
                commodity=stats_data.get('commodity'),
                run_number=stats_data.get('run_number', 1),
                success=stats_data.get('success', False),
                response_time_ms=stats_data.get('response_time_ms'),
                fields_found=stats_data.get('fields_found', 0),
                sources_count=stats_data.get('sources_count', 0),
                structured_data=stats_data.get('structured_data'),
                error_message=None if stats_data.get('success') else 'Normal search failed'
            )
            session.add(stat)
            session.commit()
            
            logger.info(f"[BENCHMARK] Statistiken erfasst für {stats_data['model_id']} - {stats_data['mine_name']}")
        
        # Aktualisiere Modell-Zusammenfassung im Hintergrund
        await benchmark_service._update_model_summary(
            stats_data['model_id'], 
            [stats_data]  # Als Liste übergeben
        )
        
        return {"success": True, "message": "Statistiken erfasst"}
        
    except Exception as e:
        logger.error(f"[BENCHMARK] Fehler beim Erfassen der Statistiken: {str(e)}")
        # Keine Exception werfen, da dies eine fire-and-forget Operation ist
        return {"success": False, "error": str(e)}