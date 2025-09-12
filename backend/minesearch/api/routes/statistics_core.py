"""
Compact Statistics Core API Routes
Kompakte Version der Statistics Core API

Author: MineSearch Development Team
Date: 2025-01-11
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from minesearch.database import (
    db_manager,
    Source,
    SearchResult,
    Mine,
    ModelSummary,
    ModelStatisticsComprehensive,
    ModelFieldConsistency,
)
from minesearch.source_stats_manager import source_stats_manager
from minesearch.providers.registry import provider_registry
from minesearch.api.routes.statistics_utils import StatisticsCalculator, StatisticsAnalyzer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/statistics", tags=["Core Statistics"])

# Export alias for orchestrator compatibility
statistics_core_router = router

# Provide a minimal field order constant for compatibility
STATISTICS_FIELD_ORDER = [
    'Modell', 'Provider', 'Erfolgsrate', 'Durchschn. Response Zeit', 'Gefundene Felder'
]


class StatisticsResponse(BaseModel):
    """Response-Modell für Statistiken"""
    success: bool
    data: Dict[str, Any]
    timestamp: str
    message: Optional[str] = None


class StatisticsRequest(BaseModel):
    """Request-Modell für Statistiken"""
    mine_name: Optional[str] = None
    model: Optional[str] = None
    field: Optional[str] = None
    time_range_days: Optional[int] = Field(default=30, ge=1, le=365)


@router.get("/overview", response_model=StatisticsResponse)
async def get_statistics_overview():
    """Hole Übersichtsstatistiken"""
    try:
        calculator = StatisticsCalculator()
        analyzer = StatisticsAnalyzer()
        
        # Basis-Statistiken
        total_mines = await calculator.get_total_mines()
        total_sources = await calculator.get_total_sources()
        total_searches = await calculator.get_total_searches()
        
        # Modell-Statistiken
        model_stats = await analyzer.get_model_performance()
        
        # Feld-Statistiken
        field_stats = await analyzer.get_field_consistency()
        
        data = {
            'total_mines': total_mines,
            'total_sources': total_sources,
            'total_searches': total_searches,
            'model_performance': model_stats,
            'field_consistency': field_stats,
            'last_updated': datetime.now().isoformat()
        }
        
        return StatisticsResponse(
            success=True,
            data=data,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Fehler bei Übersichtsstatistiken: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mines", response_model=StatisticsResponse)
async def get_mine_statistics(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0)
):
    """Hole Minen-Statistiken"""
    try:
        calculator = StatisticsCalculator()
        
        mines = await calculator.get_mines_with_stats(limit, offset)
        total_count = await calculator.get_total_mines()
        
        data = {
            'mines': mines,
            'total_count': total_count,
            'limit': limit,
            'offset': offset
        }
        
        return StatisticsResponse(
            success=True,
            data=data,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Fehler bei Minen-Statistiken: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models", response_model=StatisticsResponse)
async def get_model_statistics():
    """Hole Modell-Statistiken"""
    try:
        analyzer = StatisticsAnalyzer()
        
        model_stats = await analyzer.get_model_performance()
        model_consistency = await analyzer.get_model_consistency()
        
        data = {
            'performance': model_stats,
            'consistency': model_consistency
        }
        
        return StatisticsResponse(
            success=True,
            data=data,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Fehler bei Modell-Statistiken: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fields", response_model=StatisticsResponse)
async def get_field_statistics(
    mine_name: Optional[str] = Query(default=None),
    model: Optional[str] = Query(default=None)
):
    """Hole Feld-Statistiken"""
    try:
        analyzer = StatisticsAnalyzer()
        
        field_stats = await analyzer.get_field_consistency(mine_name, model)
        field_completeness = await analyzer.get_field_completeness(mine_name, model)
        
        data = {
            'consistency': field_stats,
            'completeness': field_completeness
        }
        
        return StatisticsResponse(
            success=True,
            data=data,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Fehler bei Feld-Statistiken: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sources", response_model=StatisticsResponse)
async def get_source_statistics(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0)
):
    """Hole Quellen-Statistiken"""
    try:
        calculator = StatisticsCalculator()
        
        sources = await calculator.get_sources_with_stats(limit, offset)
        total_count = await calculator.get_total_sources()
        
        data = {
            'sources': sources,
            'total_count': total_count,
            'limit': limit,
            'offset': offset
        }
        
        return StatisticsResponse(
            success=True,
            data=data,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Fehler bei Quellen-Statistiken: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze", response_model=StatisticsResponse)
async def analyze_statistics(request: StatisticsRequest):
    """Führe detaillierte Statistik-Analyse durch"""
    try:
        analyzer = StatisticsAnalyzer()
        
        analysis = await analyzer.analyze_comprehensive(
            mine_name=request.mine_name,
            model=request.model,
            field=request.field,
            time_range_days=request.time_range_days
        )
        
        return StatisticsResponse(
            success=True,
            data=analysis,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Fehler bei Statistik-Analyse: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=StatisticsResponse)
async def get_statistics_health():
    """Hole Statistik-System-Gesundheit"""
    try:
        calculator = StatisticsCalculator()
        
        # Prüfe Datenbankverbindung
        db_health = await calculator.check_database_health()
        
        # Prüfe Provider-Status
        provider_health = provider_registry.get_status()
        
        data = {
            'database': db_health,
            'providers': provider_health,
            'status': 'healthy' if db_health['connected'] else 'unhealthy'
        }
        
        return StatisticsResponse(
            success=True,
            data=data,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Fehler bei Gesundheitsprüfung: {e}")
        raise HTTPException(status_code=500, detail=str(e))


__all__ = ["router", "statistics_core_router", "STATISTICS_FIELD_ORDER"]
