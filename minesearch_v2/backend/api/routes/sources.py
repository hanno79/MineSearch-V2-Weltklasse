"""
Author: rahn
Datum: 04.07.2025
Version: 1.0
Beschreibung: Quellen-Management Routes
"""

from fastapi import APIRouter, HTTPException, Query, Body
from typing import Optional, Dict, List, Any
import logging
from database import Source
from collections import defaultdict

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/sources/grouped")
async def get_grouped_sources(
    country: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    source_type: Optional[str] = Query(None),
    min_reliability: float = Query(0.0),
    sort_by: str = Query("count", description="Sort by: count, domain, avg_score")
):
    """
    ÄNDERUNG 09.07.2025: Neuer Endpoint für gruppierte Quellen-Darstellung
    Gruppiert Quellen nach Domain für bessere Übersichtlichkeit
    """
    from database import db_manager
    
    # Hole alle Quellen mit Filtern
    sources = db_manager.get_sources_for_search(
        country=country,
        region=region,
        source_type=source_type,
        min_reliability=min_reliability,
        limit=1000  # Hole alle für Gruppierung
    )
    
    # Gruppiere nach Domain
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    domain_stats: Dict[str, Dict[str, Any]] = {}
    
    for source in sources:
        source_dict = source.to_dict()
        domain = source.domain
        grouped[domain].append(source_dict)
        
        # Berechne Domain-Statistiken
        if domain not in domain_stats:
            domain_stats[domain] = {
                "count": 0,
                "total_score": 0,
                "total_searches": 0,
                "total_successful": 0,
                "countries": set(),
                "source_types": set(),
                "has_recent_access": False
            }
        
        stats = domain_stats[domain]
        stats["count"] += 1
        stats["total_score"] += source.reliability_score
        stats["total_searches"] += source.total_searches
        stats["total_successful"] += source.successful_searches
        if source.country:
            stats["countries"].add(source.country)
        stats["source_types"].add(source.source_type)
        if source.last_successful_access:
            stats["has_recent_access"] = True
    
    # Erstelle finale Struktur
    result = []
    for domain, sources_list in grouped.items():
        stats = domain_stats[domain]
        avg_score = stats["total_score"] / stats["count"] if stats["count"] > 0 else 0
        success_rate = (stats["total_successful"] / stats["total_searches"] * 100) if stats["total_searches"] > 0 else 0
        
        domain_group = {
            "domain": domain,
            "count": stats["count"],
            "avg_reliability_score": round(avg_score, 1),
            "total_searches": stats["total_searches"],
            "avg_success_rate": round(success_rate, 1),
            "countries": list(stats["countries"]),
            "source_types": list(stats["source_types"]),
            "has_recent_access": stats["has_recent_access"],
            "sources": sorted(sources_list, key=lambda x: x["reliability_score"], reverse=True)
        }
        result.append(domain_group)
    
    # Sortierung
    if sort_by == "count":
        result.sort(key=lambda x: x["count"], reverse=True)
    elif sort_by == "domain":
        result.sort(key=lambda x: x["domain"])
    elif sort_by == "avg_score":
        result.sort(key=lambda x: x["avg_reliability_score"], reverse=True)
    
    return {
        "success": True,
        "data": {
            "grouped_sources": result,
            "total_domains": len(result),
            "total_sources": sum(g["count"] for g in result)
        }
    }

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
        source = session.query(Source).filter_by(id=source_id).first()
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