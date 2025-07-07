"""
Author: rahn
Datum: 04.07.2025
Version: 1.0
Beschreibung: Quellen-Management Routes
"""

from fastapi import APIRouter, HTTPException, Query, Body
from typing import Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/sources")
async def get_sources(
    country: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    source_type: Optional[str] = Query(None),
    min_reliability: float = Query(0.0),
    limit: int = Query(100),
    offset: int = Query(0)
):
    """Hole alle Quellen aus der Datenbank mit Filtern"""
    from database import db_manager
    
    sources = db_manager.get_sources_for_search(
        country=country,
        region=region,
        source_type=source_type,
        min_reliability=min_reliability,
        limit=limit,
        offset=offset
    )
    
    # Total count für Pagination
    total = len(db_manager.get_sources_for_search(
        country=country,
        region=region,
        source_type=source_type,
        min_reliability=min_reliability,
        limit=1000
    ))
    
    return {
        "success": True,
        "data": {
            "sources": [source.to_dict() for source in sources],
            "total": total,
            "limit": limit,
            "offset": offset
        }
    }

@router.get("/sources/stats")
async def get_source_statistics():
    """Hole Statistiken über die Quellen-Datenbank"""
    from database import db_manager
    
    stats = db_manager.get_source_statistics()
    return {
        "success": True,
        "data": stats
    }

@router.get("/sources/{source_id}")
async def get_source_by_id(source_id: int):
    """Hole einzelne Quelle nach ID"""
    from database import db_manager
    
    with db_manager.get_session() as session:
        source = session.query(db_manager.MiningSource).filter_by(id=source_id).first()
        if not source:
            raise HTTPException(status_code=404, detail="Quelle nicht gefunden")
        
        return {
            "success": True,
            "data": source.to_dict()
        }

@router.post("/sources/search")
async def search_sources_for_mine(
    mine_name: str = Body(...),
    country: Optional[str] = Body(None),
    region: Optional[str] = Body(None)
):
    """Suche relevante Quellen für eine spezifische Mine"""
    from database import db_manager
    
    sources = db_manager.get_sources_for_search(
        country=country,
        region=region,
        min_reliability=30.0,
        limit=100
    )
    
    return {
        "success": True,
        "data": {
            "mine_name": mine_name,
            "country": country,
            "region": region,
            "sources": [source.to_dict() for source in sources],
            "total": len(sources)
        }
    }