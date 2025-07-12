"""
Author: rahn
Datum: 12.07.2025
Version: 1.0
Beschreibung: Health-Check Endpoints für MineSearch v2 System
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
import logging
from datetime import datetime, timedelta
import asyncio

from providers.registry import provider_registry
from config import PROVIDERS_CONFIG
from model_benchmark_service import ModelBenchmarkService

logger = logging.getLogger(__name__)
router = APIRouter()

benchmark_service = ModelBenchmarkService()

@router.get("/health")
async def system_health():
    """
    System-weiter Health-Check
    """
    return {
        "status": "healthy",
        "service": "MineSearch v2.1",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "providers_available": len(provider_registry._providers),
        "models_available": len(provider_registry._available_models)
    }

@router.get("/health/providers")
async def providers_health():
    """
    Detaillierter Health-Check für alle Provider
    
    ÄNDERUNG 12.07.2025: Umfassender Provider-Status mit Performance-Metriken
    """
    try:
        health_data = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "overall_status": "healthy",
            "providers": {},
            "summary": {
                "total_providers": 0,
                "healthy_providers": 0,
                "degraded_providers": 0,
                "failed_providers": 0,
                "total_models": 0
            }
        }
        
        # Prüfe jeden Provider
        for provider_name, provider_config in PROVIDERS_CONFIG.items():
            provider_health = await check_provider_health(provider_name, provider_config)
            health_data["providers"][provider_name] = provider_health
            
            # Update Summary
            health_data["summary"]["total_providers"] += 1
            if provider_health["status"] == "healthy":
                health_data["summary"]["healthy_providers"] += 1
            elif provider_health["status"] == "degraded":
                health_data["summary"]["degraded_providers"] += 1
            else:
                health_data["summary"]["failed_providers"] += 1
            
            health_data["summary"]["total_models"] += provider_health.get("models_count", 0)
        
        # Overall Status bestimmen
        if health_data["summary"]["failed_providers"] > 2:
            health_data["overall_status"] = "degraded"
        elif health_data["summary"]["failed_providers"] > 0:
            health_data["overall_status"] = "warning"
        
        return health_data
        
    except Exception as e:
        logger.error(f"Error in providers health check: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

async def check_provider_health(provider_name: str, provider_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Überprüft Gesundheit eines einzelnen Providers
    """
    health_status = {
        "name": provider_name,
        "status": "unknown",
        "enabled": provider_config.get("enabled", False),
        "api_key_configured": bool(provider_config.get("api_key")),
        "models_count": 0,
        "timeout_config": provider_config.get("timeout", "not_configured"),
        "retry_config": provider_config.get("retry_attempts", "not_configured"),
        "performance": {},
        "recent_tests": {},
        "issues": []
    }
    
    try:
        # Basis-Status
        if not health_status["enabled"]:
            health_status["status"] = "disabled"
            return health_status
        
        if not health_status["api_key_configured"]:
            health_status["status"] = "failed"
            health_status["issues"].append("API-Key nicht konfiguriert")
            return health_status
        
        # Modell-Anzahl aus Registry
        if provider_name in provider_registry._providers:
            provider_instance = provider_registry._providers[provider_name]
            health_status["models_count"] = len(provider_instance.get_models())
        
        # Performance-Daten aus Datenbank (letzte 24h)
        performance_data = await get_provider_performance(provider_name)
        health_status["performance"] = performance_data
        
        # Recent Tests (letzte 1h)
        recent_tests = await get_recent_tests(provider_name)
        health_status["recent_tests"] = recent_tests
        
        # Status basierend auf Performance bestimmen
        if performance_data.get("success_rate", 0) >= 0.8:
            health_status["status"] = "healthy"
        elif performance_data.get("success_rate", 0) >= 0.5:
            health_status["status"] = "degraded"
            health_status["issues"].append(f"Niedrige Erfolgsrate: {performance_data.get('success_rate', 0):.1%}")
        else:
            health_status["status"] = "failed"
            health_status["issues"].append("Kritisch niedrige Erfolgsrate")
        
        # Timeout-Warnungen
        avg_response_time = performance_data.get("avg_response_time", 0)
        timeout_limit = provider_config.get("timeout", 120) * 1000  # Convert to ms
        
        if avg_response_time > timeout_limit * 0.8:
            health_status["issues"].append(f"Langsame Response-Zeit: {avg_response_time:.0f}ms")
            if health_status["status"] == "healthy":
                health_status["status"] = "degraded"
        
    except Exception as e:
        health_status["status"] = "failed"
        health_status["issues"].append(f"Health-Check Fehler: {str(e)}")
        logger.error(f"Error checking health for {provider_name}: {e}")
    
    return health_status

async def get_provider_performance(provider_name: str) -> Dict[str, Any]:
    """
    Holt Performance-Daten für Provider aus der Datenbank (letzte 24h)
    """
    try:
        from database import db_manager
        
        # Get models for this provider
        provider_models = [model_id for model_id in provider_registry._available_models.keys() 
                         if model_id.startswith(f"{provider_name}:")]
        
        if not provider_models:
            return {"success_rate": 0, "avg_response_time": 0, "total_tests": 0}
        
        # Query last 24h
        since = datetime.now() - timedelta(hours=24)
        
        with db_manager.get_session() as session:
            from database.models import ModelStatistics
            
            stats = session.query(ModelStatistics).filter(
                ModelStatistics.model_id.in_(provider_models),
                ModelStatistics.timestamp >= since
            ).all()
            
            if not stats:
                return {"success_rate": 0, "avg_response_time": 0, "total_tests": 0}
            
            total_tests = len(stats)
            successful_tests = sum(1 for s in stats if s.success)
            success_rate = successful_tests / total_tests if total_tests > 0 else 0
            
            # Average response time für erfolgreiche Tests
            successful_stats = [s for s in stats if s.success and s.response_time_ms > 0]
            avg_response_time = (sum(s.response_time_ms for s in successful_stats) / len(successful_stats) 
                               if successful_stats else 0)
            
            return {
                "success_rate": success_rate,
                "avg_response_time": avg_response_time,
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "period": "24h"
            }
            
    except Exception as e:
        logger.error(f"Error getting performance for {provider_name}: {e}")
        return {"success_rate": 0, "avg_response_time": 0, "total_tests": 0, "error": str(e)}

async def get_recent_tests(provider_name: str) -> Dict[str, Any]:
    """
    Holt aktuelle Test-Ergebnisse (letzte 1h)
    """
    try:
        from database import db_manager
        
        provider_models = [model_id for model_id in provider_registry._available_models.keys() 
                         if model_id.startswith(f"{provider_name}:")]
        
        if not provider_models:
            return {"recent_tests": 0, "recent_successes": 0}
        
        # Query last 1h
        since = datetime.now() - timedelta(hours=1)
        
        with db_manager.get_session() as session:
            from database.models import ModelStatistics
            
            recent_stats = session.query(ModelStatistics).filter(
                ModelStatistics.model_id.in_(provider_models),
                ModelStatistics.timestamp >= since
            ).all()
            
            recent_tests = len(recent_stats)
            recent_successes = sum(1 for s in recent_stats if s.success)
            
            return {
                "recent_tests": recent_tests,
                "recent_successes": recent_successes,
                "period": "1h"
            }
            
    except Exception as e:
        logger.error(f"Error getting recent tests for {provider_name}: {e}")
        return {"recent_tests": 0, "recent_successes": 0, "error": str(e)}

@router.get("/health/models")
async def models_health():
    """
    Health-Check für alle verfügbaren Modelle
    """
    try:
        models_data = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_models": len(provider_registry._available_models),
            "models": {}
        }
        
        # Gehe durch alle Modelle
        for model_id, model_config in provider_registry._available_models.items():
            provider_name = model_id.split(":")[0]
            
            model_health = {
                "name": model_config.name,
                "provider": provider_name,
                "timeout": model_config.timeout,
                "supports_web_search": getattr(model_config, 'supports_web_search', False),
                "status": "unknown"
            }
            
            # Hol Performance-Daten für dieses Modell
            try:
                model_stats = await benchmark_service.get_model_summary(model_id)
                
                if model_stats.get("total_tests", 0) > 0:
                    success_rate = model_stats.get("success_rate", 0)
                    if success_rate >= 0.8:
                        model_health["status"] = "healthy"
                    elif success_rate >= 0.5:
                        model_health["status"] = "degraded"
                    else:
                        model_health["status"] = "failed"
                    
                    model_health["performance"] = {
                        "success_rate": success_rate,
                        "avg_response_time": model_stats.get("avg_response_time_ms", 0),
                        "total_tests": model_stats.get("total_tests", 0)
                    }
                else:
                    model_health["status"] = "untested"
                    
            except Exception as e:
                model_health["status"] = "error"
                model_health["error"] = str(e)
            
            models_data["models"][model_id] = model_health
        
        return models_data
        
    except Exception as e:
        logger.error(f"Error in models health check: {e}")
        raise HTTPException(status_code=500, detail=f"Models health check failed: {str(e)}")

@router.get("/health/database")
async def database_health():
    """
    Health-Check für Datenbank-Komponenten
    """
    try:
        from database import db_manager
        
        health_data = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "unknown",
            "tables": {},
            "recent_activity": {}
        }
        
        with db_manager.get_session() as session:
            # Prüfe Tabellen
            tables_to_check = [
                ("model_statistics", "ModelStatistics"),
                ("field_statistics", "FieldStatistics"), 
                ("sources", "Sources"),
                ("search_results", "SearchResults")
            ]
            
            for table_name, model_name in tables_to_check:
                try:
                    # Count entries
                    count_query = f"SELECT COUNT(*) FROM {table_name}"
                    result = session.execute(count_query).fetchone()
                    count = result[0] if result else 0
                    
                    # Recent entries (last 24h)
                    recent_query = f"SELECT COUNT(*) FROM {table_name} WHERE DATE(timestamp) = DATE('now')" if table_name != "sources" else f"SELECT COUNT(*) FROM {table_name}"
                    recent_result = session.execute(recent_query).fetchone()
                    recent_count = recent_result[0] if recent_result else 0
                    
                    health_data["tables"][table_name] = {
                        "total_entries": count,
                        "recent_entries": recent_count,
                        "status": "healthy" if count > 0 else "empty"
                    }
                    
                except Exception as e:
                    health_data["tables"][table_name] = {
                        "status": "error",
                        "error": str(e)
                    }
        
        # Overall database status
        table_statuses = [t.get("status") for t in health_data["tables"].values()]
        if all(s == "healthy" for s in table_statuses):
            health_data["status"] = "healthy"
        elif any(s == "error" for s in table_statuses):
            health_data["status"] = "degraded"
        else:
            health_data["status"] = "warning"
        
        return health_data
        
    except Exception as e:
        logger.error(f"Error in database health check: {e}")
        raise HTTPException(status_code=500, detail=f"Database health check failed: {str(e)}")