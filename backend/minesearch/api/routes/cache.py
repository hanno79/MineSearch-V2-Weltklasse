"""
Author: rahn
Datum: 05.07.2025
Version: 1.0
Beschreibung: Cache-Management API Endpoints
"""

from fastapi import APIRouter, HTTPException
import logging

from cache_service import get_cache_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/cache/stats")
async def get_cache_stats():
    """Hole Cache-Statistiken"""
    try:
        cache = get_cache_service()
        stats = cache.get_stats()
        
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Cache-Statistiken: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/clear")
async def clear_cache(mine_name: str = None, model: str = None):
    """
    Leere Cache selektiv oder komplett
    
    Args:
        mine_name: Wenn angegeben, nur Einträge für diese Mine löschen
        model: Wenn angegeben, nur Einträge für dieses Modell löschen
    """
    try:
        cache = get_cache_service()
        count = cache.invalidate(mine_name=mine_name, model=model)
        
        message = "Cache geleert"
        if mine_name:
            message = f"Cache für Mine '{mine_name}' geleert"
        elif model:
            message = f"Cache für Modell '{model}' geleert"
        
        return {
            "success": True,
            "message": message,
            "cleared_entries": count
        }
    except Exception as e:
        logger.error(f"Fehler beim Leeren des Caches: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/cleanup")
async def cleanup_expired():
    """Entferne abgelaufene Cache-Einträge"""
    try:
        cache = get_cache_service()
        count = cache.cleanup_expired()
        
        return {
            "success": True,
            "message": f"{count} abgelaufene Einträge entfernt"
        }
    except Exception as e:
        logger.error(f"Fehler beim Cache-Cleanup: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))