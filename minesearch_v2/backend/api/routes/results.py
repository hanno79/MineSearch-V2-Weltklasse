"""
Author: rahn
Datum: 04.07.2025
Version: 1.0
Beschreibung: Suchergebnis-Management Routes
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/results")
async def get_results(
    mine_name: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    session_id: Optional[str] = Query(None),
    days_back: int = Query(30),
    limit: int = Query(50),
    offset: int = Query(0)
):
    """Hole gespeicherte Suchergebnisse mit Filtern"""
    from database import db_manager
    
    results = db_manager.get_search_results(
        limit=limit,
        offset=offset,
        mine_name=mine_name,
        country=country,
        session_id=session_id,
        days_back=days_back
    )
    
    # Total count für Pagination
    total = len(db_manager.get_search_results(limit=1000, days_back=days_back))
    
    return {
        "success": True,
        "data": {
            "results": [r.to_dict() for r in results],
            "total": total,
            "limit": limit,
            "offset": offset
        }
    }

@router.get("/results/stats")
async def get_result_statistics():
    """Hole Statistiken über gespeicherte Ergebnisse"""
    from database import db_manager
    
    stats = db_manager.get_result_statistics()
    return {
        "success": True,
        "data": stats
    }

@router.get("/results/sessions")
async def get_result_sessions(limit: int = Query(20)):
    """Hole gruppierte Such-Sessions"""
    from database import db_manager
    
    sessions = db_manager.get_sessions(limit=limit)
    return {
        "success": True,
        "data": sessions
    }

@router.get("/results/{result_id}")
async def get_result_by_id(result_id: int):
    """Hole einzelnes Suchergebnis nach ID"""
    from database import db_manager
    
    result = db_manager.get_search_result_by_id(result_id)
    if not result:
        raise HTTPException(status_code=404, detail="Ergebnis nicht gefunden")
    
    return {
        "success": True,
        "data": result.to_dict()
    }

@router.delete("/results/{result_id}")
async def delete_result(result_id: int):
    """Lösche einzelnes Suchergebnis"""
    from database import db_manager
    
    with db_manager.get_session() as session:
        result = session.query(db_manager.SearchResult).filter_by(id=result_id).first()
        if not result:
            raise HTTPException(status_code=404, detail="Ergebnis nicht gefunden")
        
        session.delete(result)
        session.commit()
    
    return {
        "success": True,
        "message": f"Ergebnis {result_id} gelöscht"
    }