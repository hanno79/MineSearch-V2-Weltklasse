"""
Compact Benchmark API Routes
Kompakte Version der Benchmark API

Author: MineSearch Development Team
Date: 2025-01-11
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging
import uuid
from datetime import datetime

from model_benchmark_service import ModelBenchmarkService
from minesearch.database import db_manager
from model_summary_auto_updater import ModelSummaryAutoUpdater

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/benchmark", tags=["benchmark"])


class BenchmarkRequest(BaseModel):
    """Request-Modell für Benchmarks"""
    models: List[str] = Field(..., description="Liste der zu testenden Modelle")
    test_queries: List[str] = Field(..., description="Test-Queries")
    mine_names: Optional[List[str]] = Field(default=None, description="Minen-Namen für Tests")
    country: Optional[str] = Field(default=None, description="Land für Tests")


class BenchmarkResponse(BaseModel):
    """Response-Modell für Benchmarks"""
    benchmark_id: str
    status: str
    results: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    timestamp: str


@router.get("/recent")
async def get_recent_search_results(
    days_back: int = Query(7, description="Tage zurück"),
    limit: int = Query(50, description="Maximale Anzahl Ergebnisse"),
    sort_by: str = Query("search_timestamp", description="Sortierfeld"),
    order: str = Query("desc", description="Sortierreihenfolge (asc/desc)"),
    mine_name: Optional[str] = Query(None, description="Filter nach Mine"),
    country: Optional[str] = Query(None, description="Filter nach Land")
):
    """Hole aktuelle Suchergebnisse für Benchmarking"""
    try:
        benchmark_service = ModelBenchmarkService()
        
        results = await benchmark_service.get_recent_results(
            days_back=days_back,
            limit=limit,
            sort_by=sort_by,
            order=order,
            mine_name=mine_name,
            country=country
        )
        
        return {
            "success": True,
            "data": results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Fehler bei Abruf aktueller Ergebnisse: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/start", response_model=BenchmarkResponse)
async def start_benchmark(request: BenchmarkRequest, background_tasks: BackgroundTasks):
    """Starte neuen Benchmark"""
    try:
        benchmark_service = ModelBenchmarkService()
        
        # Generiere Benchmark-ID
        benchmark_id = str(uuid.uuid4())
        
        # Starte Benchmark im Hintergrund
        background_tasks.add_task(
            benchmark_service.run_benchmark,
            benchmark_id=benchmark_id,
            models=request.models,
            test_queries=request.test_queries,
            mine_names=request.mine_names,
            country=request.country
        )
        
        return BenchmarkResponse(
            benchmark_id=benchmark_id,
            status="started",
            message="Benchmark wurde gestartet",
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Fehler beim Starten des Benchmarks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{benchmark_id}", response_model=BenchmarkResponse)
async def get_benchmark_status(benchmark_id: str):
    """Hole Benchmark-Status"""
    try:
        benchmark_service = ModelBenchmarkService()
        
        status = await benchmark_service.get_benchmark_status(benchmark_id)
        
        return BenchmarkResponse(
            benchmark_id=benchmark_id,
            status=status.get("status", "unknown"),
            results=status.get("results"),
            message=status.get("message"),
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Fehler beim Abruf des Benchmark-Status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/results/{benchmark_id}")
async def get_benchmark_results(benchmark_id: str):
    """Hole Benchmark-Ergebnisse"""
    try:
        benchmark_service = ModelBenchmarkService()
        
        results = await benchmark_service.get_benchmark_results(benchmark_id)
        
        if not results:
            raise HTTPException(status_code=404, detail="Benchmark nicht gefunden")
        
        return {
            "success": True,
            "data": results,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fehler beim Abruf der Benchmark-Ergebnisse: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models")
async def get_available_models():
    """Hole verfügbare Modelle für Benchmarks"""
    try:
        benchmark_service = ModelBenchmarkService()
        
        models = await benchmark_service.get_available_models()
        
        return {
            "success": True,
            "data": models,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Fehler beim Abruf verfügbarer Modelle: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_benchmark_history(
    limit: int = Query(20, description="Maximale Anzahl Benchmarks"),
    offset: int = Query(0, description="Offset für Paginierung")
):
    """Hole Benchmark-Historie"""
    try:
        benchmark_service = ModelBenchmarkService()
        
        history = await benchmark_service.get_benchmark_history(limit, offset)
        
        return {
            "success": True,
            "data": history,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Fehler beim Abruf der Benchmark-Historie: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{benchmark_id}")
async def delete_benchmark(benchmark_id: str):
    """Lösche Benchmark"""
    try:
        benchmark_service = ModelBenchmarkService()
        
        success = await benchmark_service.delete_benchmark(benchmark_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Benchmark nicht gefunden")
        
        return {
            "success": True,
            "message": "Benchmark wurde gelöscht",
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fehler beim Löschen des Benchmarks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-summaries")
async def update_model_summaries(background_tasks: BackgroundTasks):
    """Aktualisiere Modell-Zusammenfassungen"""
    try:
        updater = ModelSummaryAutoUpdater()
        
        # Starte Update im Hintergrund
        background_tasks.add_task(updater.update_all_summaries)
        
        return {
            "success": True,
            "message": "Modell-Zusammenfassungen werden aktualisiert",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Fehler beim Aktualisieren der Modell-Zusammenfassungen: {e}")
        raise HTTPException(status_code=500, detail=str(e))


__all__ = ["router"]
