"""
Author: rahn
Datum: 23.07.2025
Version: 1.0
Beschreibung: API Routes für Source Performance Tracking
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field

from source_stats_manager import source_stats_manager
from source_auto_reset_service import auto_reset_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/source-performance", tags=["Source Performance"])


class SourcePerformanceResponse(BaseModel):
    """Response-Model für Source-Performance-Daten"""
    url: str
    domain: str
    source_type: str
    total_attempts: int
    successful_attempts: int
    failed_attempts: int
    success_rate: float = Field(..., ge=0, le=1)
    quality_score: float = Field(..., ge=0, le=100)
    reliability_score: float = Field(..., ge=0, le=100)
    data_richness_score: float = Field(..., ge=0, le=100)
    avg_response_time: float
    avg_data_fields_found: float
    consecutive_failures: int
    last_success: Optional[str] = None
    last_attempt: Optional[str] = None
    content_types_found: List[str]
    needs_reset: bool
    reset_reason: Optional[str] = None


class ManualResetRequest(BaseModel):
    """Request-Model für manuelles Reset"""
    url: str
    reason: str


class BulkResetRequest(BaseModel):
    """Request-Model für Bulk-Reset"""
    urls: List[str]
    reason: str


@router.get("/summary", response_model=Dict[str, Any])
async def get_performance_summary():
    """
    Holt umfassende Performance-Zusammenfassung des Source-Tracking Systems
    """
    try:
        summary = await source_stats_manager.get_performance_summary()
        
        # Erweitere um Auto-Reset Service Status
        auto_reset_status = auto_reset_service.get_service_status()
        summary['auto_reset_service'] = auto_reset_status
        
        return {
            "success": True,
            "data": summary,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"[API] Fehler beim Abrufen der Performance-Zusammenfassung: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/top-performers", response_model=Dict[str, Any])
async def get_top_performing_sources(
    limit: int = Query(20, ge=1, le=100),
    source_type: Optional[str] = Query(None, description="Filter nach Quellentyp"),
    min_attempts: int = Query(5, ge=1, description="Mindestanzahl Versuche")
):
    """
    Holt die Top-performing Quellen
    """
    try:
        top_sources = await source_stats_manager.get_top_performing_sources(
            limit=limit, 
            source_type=source_type, 
            min_attempts=min_attempts
        )
        
        # Konvertiere zu Response-Format
        sources_data = []
        for metrics in top_sources:
            success_rate = metrics.successful_attempts / max(metrics.total_attempts, 1)
            
            source_data = SourcePerformanceResponse(
                url=metrics.url,
                domain=metrics.domain,
                source_type=metrics.source_type,
                total_attempts=metrics.total_attempts,
                successful_attempts=metrics.successful_attempts,
                failed_attempts=metrics.failed_attempts,
                success_rate=success_rate,
                quality_score=metrics.quality_score,
                reliability_score=metrics.reliability_score,
                data_richness_score=metrics.data_richness_score,
                avg_response_time=metrics.avg_response_time,
                avg_data_fields_found=metrics.avg_data_fields_found,
                consecutive_failures=metrics.consecutive_failures,
                last_success=metrics.last_success.isoformat() if metrics.last_success else None,
                last_attempt=metrics.last_attempt.isoformat() if metrics.last_attempt else None,
                content_types_found=metrics.content_types_found,
                needs_reset=metrics.needs_reset,
                reset_reason=metrics.reset_reason
            )
            sources_data.append(source_data.dict())
        
        return {
            "success": True,
            "data": {
                "sources": sources_data,
                "count": len(sources_data),
                "filters": {
                    "limit": limit,
                    "source_type": source_type,
                    "min_attempts": min_attempts
                }
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"[API] Fehler beim Abrufen der Top-Performer: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/source/{url:path}", response_model=Dict[str, Any])
async def get_source_performance(url: str):
    """
    Holt Performance-Metriken für eine spezifische Quelle
    """
    try:
        metrics = await source_stats_manager.get_source_performance(url)
        
        if not metrics:
            raise HTTPException(status_code=404, detail="Quelle nicht gefunden")
        
        success_rate = metrics.successful_attempts / max(metrics.total_attempts, 1)
        
        source_data = SourcePerformanceResponse(
            url=metrics.url,
            domain=metrics.domain,
            source_type=metrics.source_type,
            total_attempts=metrics.total_attempts,
            successful_attempts=metrics.successful_attempts,
            failed_attempts=metrics.failed_attempts,
            success_rate=success_rate,
            quality_score=metrics.quality_score,
            reliability_score=metrics.reliability_score,
            data_richness_score=metrics.data_richness_score,
            avg_response_time=metrics.avg_response_time,
            avg_data_fields_found=metrics.avg_data_fields_found,
            consecutive_failures=metrics.consecutive_failures,
            last_success=metrics.last_success.isoformat() if metrics.last_success else None,
            last_attempt=metrics.last_attempt.isoformat() if metrics.last_attempt else None,
            content_types_found=metrics.content_types_found,
            needs_reset=metrics.needs_reset,
            reset_reason=metrics.reset_reason
        )
        
        return {
            "success": True,
            "data": source_data.dict(),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Fehler beim Abrufen der Source-Performance für {url}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reset-candidates", response_model=Dict[str, Any])
async def get_sources_needing_reset():
    """
    Identifiziert Quellen die ein Auto-Reset benötigen
    """
    try:
        reset_candidates = await source_stats_manager.get_sources_needing_reset()
        
        # Konvertiere zu Response-Format
        candidates_data = []
        for metrics in reset_candidates:
            success_rate = metrics.successful_attempts / max(metrics.total_attempts, 1)
            
            candidate_data = {
                "url": metrics.url,
                "domain": metrics.domain,
                "source_type": metrics.source_type,
                "success_rate": success_rate,
                "consecutive_failures": metrics.consecutive_failures,
                "quality_score": metrics.quality_score,
                "reliability_score": metrics.reliability_score,
                "total_attempts": metrics.total_attempts,
                "last_success": metrics.last_success.isoformat() if metrics.last_success else None,
                "reset_reason": metrics.reset_reason,
                "days_since_success": (datetime.now() - metrics.last_success).days if metrics.last_success else None
            }
            candidates_data.append(candidate_data)
        
        return {
            "success": True,
            "data": {
                "candidates": candidates_data,
                "count": len(candidates_data)
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"[API] Fehler beim Identifizieren der Reset-Kandidaten: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/manual-reset", response_model=Dict[str, Any])
async def manual_reset_source(request: ManualResetRequest):
    """
    Führt manuelles Reset einer Quelle durch
    """
    try:
        success = await auto_reset_service.manual_reset_source(
            url=request.url,
            reason=request.reason
        )
        
        if success:
            return {
                "success": True,
                "message": f"Quelle erfolgreich resettet: {request.url}",
                "data": {
                    "url": request.url,
                    "reason": request.reason,
                    "reset_timestamp": datetime.now().isoformat()
                }
            }
        else:
            raise HTTPException(status_code=400, detail="Reset fehlgeschlagen")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Fehler beim manuellen Reset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk-reset", response_model=Dict[str, Any])
async def bulk_reset_sources(request: BulkResetRequest):
    """
    Führt Bulk-Reset für mehrere Quellen durch
    """
    try:
        if len(request.urls) > 100:
            raise HTTPException(status_code=400, detail="Maximum 100 URLs pro Bulk-Reset")
        
        reset_count = await source_stats_manager.perform_bulk_reset(request.urls)
        
        # Dokumentiere Bulk-Reset in Historie
        for url in request.urls:
            await auto_reset_service.manual_reset_source(url, f"Bulk reset: {request.reason}")
        
        return {
            "success": True,
            "message": f"{reset_count} Quellen erfolgreich resettet",
            "data": {
                "reset_count": reset_count,
                "total_requested": len(request.urls),
                "reason": request.reason,
                "reset_timestamp": datetime.now().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Fehler beim Bulk-Reset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-update", response_model=Dict[str, Any])
async def trigger_batch_update():
    """
    Triggert manuell ein Batch-Update der Source-Statistiken
    """
    try:
        updated_count = await source_stats_manager.batch_update_sources()
        
        return {
            "success": True,
            "message": f"Batch-Update abgeschlossen",
            "data": {
                "updated_sources": updated_count,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"[API] Fehler beim Batch-Update: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reset-history", response_model=Dict[str, Any])
async def get_reset_history(limit: int = Query(50, ge=1, le=200)):
    """
    Holt Historie der Reset-Operationen
    """
    try:
        history = auto_reset_service.get_reset_history(limit=limit)
        
        return {
            "success": True,
            "data": {
                "operations": history,
                "count": len(history)
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"[API] Fehler beim Abrufen der Reset-Historie: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/auto-reset-status", response_model=Dict[str, Any])
async def get_auto_reset_status():
    """
    Holt Status des Auto-Reset Services
    """
    try:
        status = auto_reset_service.get_service_status()
        
        return {
            "success": True,
            "data": status,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"[API] Fehler beim Abrufen des Auto-Reset Status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auto-reset/start", response_model=Dict[str, Any])
async def start_auto_reset_service():
    """
    Startet den Auto-Reset Service
    """
    try:
        if auto_reset_service.running:
            return {
                "success": True,
                "message": "Auto-Reset Service läuft bereits",
                "data": {"running": True}
            }
        
        # Starte Service in Background Task
        import asyncio
        asyncio.create_task(auto_reset_service.start_service())
        
        return {
            "success": True,
            "message": "Auto-Reset Service gestartet",
            "data": {"running": True}
        }
        
    except Exception as e:
        logger.error(f"[API] Fehler beim Starten des Auto-Reset Service: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auto-reset/stop", response_model=Dict[str, Any])
async def stop_auto_reset_service():
    """
    Stoppt den Auto-Reset Service
    """
    try:
        auto_reset_service.stop_service()
        
        return {
            "success": True,
            "message": "Auto-Reset Service gestoppt",
            "data": {"running": False}
        }
        
    except Exception as e:
        logger.error(f"[API] Fehler beim Stoppen des Auto-Reset Service: {e}")
        raise HTTPException(status_code=500, detail=str(e))