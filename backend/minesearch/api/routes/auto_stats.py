"""
Author: rahn
Datum: 26.07.2025
Version: 1.0
Beschreibung: API-Routen für automatische Statistics und Performance-Tracking
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from auto_stats_updater import auto_stats_updater
from ...database import db_manager
from database.models import ModelStatistics, ModelSummary
from sqlalchemy import func, Integer, cast

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auto-stats", tags=["Auto Statistics"])


class PerformanceMetrics(BaseModel):
    """Response-Model für Performance-Metriken"""
    total_searches: int
    successful_searches: int
    success_rate: float = Field(..., ge=0, le=100)
    unique_models: int
    unique_mines: int
    hours_analyzed: int
    model_performance: Dict[str, Dict[str, float]]
    timestamp: str


class RealtimeStatsUpdate(BaseModel):
    """Request-Model für manuelle Statistics-Updates"""
    mine_name: str
    model_used: str
    search_result: Dict[str, Any]
    response_time_ms: Optional[float] = None
    country: Optional[str] = None
    commodity: Optional[str] = None
    region: Optional[str] = None


@router.get("/performance/realtime", response_model=PerformanceMetrics)
async def get_realtime_performance_metrics(
    hours: int = Query(1, ge=1, le=168, description="Zeitraum in Stunden (max. 1 Woche)")
):
    """
    Holt Echtzeit-Performance-Metriken für automatische Statistics
    """
    try:
        summary = auto_stats_updater.get_recent_statistics_summary(hours=hours)
        
        if "error" in summary:
            raise HTTPException(status_code=500, detail=summary["error"])
        
        return PerformanceMetrics(
            total_searches=summary.get("total_searches", 0),
            successful_searches=summary.get("successful_searches", 0),
            success_rate=summary.get("success_rate", 0),
            unique_models=summary.get("unique_models", 0),
            unique_mines=summary.get("unique_mines", 0),
            hours_analyzed=summary.get("hours_analyzed", hours),
            model_performance=summary.get("model_performance", {}),
            timestamp=summary.get("timestamp", datetime.now().isoformat())
        )
        
    except Exception as e:
        logger.error(f"[AUTO-STATS API] Fehler bei Realtime-Metriken: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard")
async def get_auto_stats_dashboard():
    """
    Dashboard-Übersicht für automatische Statistics
    """
    try:
        # Hole verschiedene Zeiträume
        metrics_1h = auto_stats_updater.get_recent_statistics_summary(hours=1)
        metrics_24h = auto_stats_updater.get_recent_statistics_summary(hours=24)
        metrics_7d = auto_stats_updater.get_recent_statistics_summary(hours=168)
        
        # Hole ModelSummary Status
        with db_manager.get_session() as session:
            total_summaries = session.query(ModelSummary).count()
            recent_summaries = session.query(ModelSummary).filter(
                ModelSummary.last_updated >= datetime.now() - timedelta(hours=24)
            ).count()
            
            # Top-Performing Modelle (letzte 24h) - Vereinfachte Query
            top_models_query = session.query(
                ModelStatistics.model_id,
                func.count(ModelStatistics.id).label('total_searches'),
                func.sum(cast(ModelStatistics.success, Integer)).label('successful_searches')
            ).filter(
                ModelStatistics.timestamp >= datetime.now() - timedelta(hours=24)
            ).group_by(ModelStatistics.model_id).order_by(
                func.sum(cast(ModelStatistics.success, Integer)).desc()
            ).limit(5).all()
            
            top_models = [(row[0], row[2]) for row in top_models_query]
        
        return {
            "success": True,
            "data": {
                "overview": {
                    "auto_stats_active": True,
                    "total_model_summaries": total_summaries,
                    "recent_summaries_generated": recent_summaries,
                    "last_updated": datetime.now().isoformat()
                },
                "realtime_metrics": {
                    "1_hour": {
                        "searches": metrics_1h.get("total_searches", 0),
                        "success_rate": metrics_1h.get("success_rate", 0),
                        "models_active": metrics_1h.get("unique_models", 0)
                    },
                    "24_hours": {
                        "searches": metrics_24h.get("total_searches", 0),
                        "success_rate": metrics_24h.get("success_rate", 0),
                        "models_active": metrics_24h.get("unique_models", 0)
                    },
                    "7_days": {
                        "searches": metrics_7d.get("total_searches", 0),
                        "success_rate": metrics_7d.get("success_rate", 0),
                        "models_active": metrics_7d.get("unique_models", 0)
                    }
                },
                "top_performing_models": [
                    {"model_id": model[0], "successful_searches": model[1]}
                    for model in top_models
                ],
                "trending": {
                    "activity_trend": "increasing" if metrics_1h.get("total_searches", 0) > 0 else "stable",
                    "quality_trend": "improving" if metrics_24h.get("success_rate", 0) > 50 else "stable",
                    "model_diversity": len(metrics_24h.get("model_performance", {}))
                }
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"[AUTO-STATS API] Fehler bei Dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update/manual")
async def manual_statistics_update(update_data: RealtimeStatsUpdate):
    """
    Manueller Statistics-Update für externe Integration
    """
    try:
        result = await auto_stats_updater.update_statistics_after_search(
            mine_name=update_data.mine_name,
            model_used=update_data.model_used,
            search_result=update_data.search_result,
            response_time_ms=update_data.response_time_ms,
            country=update_data.country,
            commodity=update_data.commodity,
            region=update_data.region
        )
        
        return {
            "success": True,
            "data": result,
            "message": f"Statistics aktualisiert für {update_data.model_used}/{update_data.mine_name}"
        }
        
    except Exception as e:
        logger.error(f"[AUTO-STATS API] Fehler bei manuellem Update: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trends/model/{model_id}")
async def get_model_trend_analysis(
    model_id: str,
    days: int = Query(7, ge=1, le=30, description="Anzahl Tage für Trend-Analyse")
):
    """
    Trend-Analyse für spezifisches Modell
    """
    try:
        start_date = datetime.now() - timedelta(days=days)
        
        with db_manager.get_session() as session:
            # Hole alle Statistics für das Modell
            model_stats = session.query(ModelStatistics).filter(
                ModelStatistics.model_id == model_id,
                ModelStatistics.timestamp >= start_date
            ).order_by(ModelStatistics.timestamp).all()
            
            if not model_stats:
                return {
                    "success": False,
                    "error": f"Keine Daten für Modell {model_id} in den letzten {days} Tagen gefunden"
                }
            
            # Berechne tägliche Aggregationen
            daily_stats = {}
            for stat in model_stats:
                day_key = stat.timestamp.date().isoformat()
                if day_key not in daily_stats:
                    daily_stats[day_key] = {
                        "total": 0,
                        "successful": 0,
                        "fields_sum": 0,
                        "response_times": []
                    }
                
                daily_stats[day_key]["total"] += 1
                if stat.success:
                    daily_stats[day_key]["successful"] += 1
                daily_stats[day_key]["fields_sum"] += stat.fields_found
                if stat.response_time_ms:
                    daily_stats[day_key]["response_times"].append(stat.response_time_ms)
            
            # Konvertiere zu Trend-Daten
            trend_data = []
            for day, stats in sorted(daily_stats.items()):
                success_rate = (stats["successful"] / stats["total"]) * 100 if stats["total"] > 0 else 0
                avg_fields = stats["fields_sum"] / stats["total"] if stats["total"] > 0 else 0
                avg_response_time = sum(stats["response_times"]) / len(stats["response_times"]) if stats["response_times"] else 0
                
                trend_data.append({
                    "date": day,
                    "searches": stats["total"],
                    "success_rate": success_rate,
                    "avg_fields_found": avg_fields,
                    "avg_response_time_ms": avg_response_time
                })
            
            # Berechne Trend-Indikatoren
            if len(trend_data) >= 2:
                recent_success = sum(d["success_rate"] for d in trend_data[-3:]) / min(3, len(trend_data))
                early_success = sum(d["success_rate"] for d in trend_data[:3]) / min(3, len(trend_data))
                trend_direction = "improving" if recent_success > early_success else "declining" if recent_success < early_success else "stable"
            else:
                trend_direction = "insufficient_data"
        
        return {
            "success": True,
            "data": {
                "model_id": model_id,
                "analysis_period": f"{days} days",
                "total_searches": len(model_stats),
                "trend_direction": trend_direction,
                "daily_data": trend_data,
                "summary": {
                    "overall_success_rate": (sum(1 for s in model_stats if s.success) / len(model_stats)) * 100,
                    "avg_fields_found": sum(s.fields_found for s in model_stats) / len(model_stats),
                    "most_productive_day": max(daily_stats.items(), key=lambda x: x[1]["total"])[0] if daily_stats else None
                }
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"[AUTO-STATS API] Fehler bei Modell-Trend-Analyse: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def get_auto_stats_health():
    """
    Health-Check für automatische Statistics
    """
    try:
        # Prüfe ob Updates in den letzten 5 Minuten stattgefunden haben
        cutoff_time = datetime.now() - timedelta(minutes=5)
        
        with db_manager.get_session() as session:
            recent_updates = session.query(ModelStatistics).filter(
                ModelStatistics.timestamp >= cutoff_time
            ).count()
            
            total_stats = session.query(ModelStatistics).count()
            total_summaries = session.query(ModelSummary).count()
        
        # Bestimme Health-Status
        is_healthy = True
        issues = []
        
        if total_stats == 0:
            is_healthy = False
            issues.append("Keine ModelStatistics in der Datenbank")
        
        if total_summaries == 0:
            is_healthy = False
            issues.append("Keine ModelSummaries in der Datenbank")
        
        if recent_updates == 0:
            issues.append("Keine Updates in den letzten 5 Minuten")
        
        health_status = "healthy" if is_healthy else "degraded" if issues else "critical"
        
        return {
            "success": True,
            "status": health_status,
            "data": {
                "auto_stats_enabled": True,
                "recent_updates_5min": recent_updates,
                "total_statistics": total_stats,
                "total_summaries": total_summaries,
                "issues": issues,
                "last_check": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"[AUTO-STATS API] Fehler bei Health-Check: {e}")
        return {
            "success": False,
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }