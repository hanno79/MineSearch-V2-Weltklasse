"""
Author: rahn
Datum: 04.07.2025
Version: 1.0
Beschreibung: Quellen-Management Routes
"""

from fastapi import APIRouter, HTTPException, Query, Body
from typing import Optional, Dict, List, Any
import logging
from minesearch.database.models import Source
from collections import defaultdict

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/sources/grouped")
async def get_grouped_sources(
    country: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    source_type: Optional[str] = Query(None),
    min_reliability: float = Query(0.0),
    sort_by: str = Query("count", description="Sort by: count, domain, avg_score, success_rate, searches"),
    order: str = Query("desc", description="Order: asc or desc")
):
    """
    ÄNDERUNG 09.07.2025: Neuer Endpoint für gruppierte Quellen-Darstellung
    Gruppiert Quellen nach Domain für bessere Übersichtlichkeit
    """
    from minesearch.database import db_manager
    
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
    
    # ÄNDERUNG 09.07.2025: Erweiterte Sortierung mit auf-/absteigender Reihenfolge
    reverse_order = (order == "desc")
    
    if sort_by == "count":
        result.sort(key=lambda x: x["count"], reverse=reverse_order)
    elif sort_by == "domain":
        result.sort(key=lambda x: x["domain"], reverse=reverse_order)
    elif sort_by == "avg_score":
        result.sort(key=lambda x: x["avg_reliability_score"], reverse=reverse_order)
    elif sort_by == "success_rate":
        result.sort(key=lambda x: x["avg_success_rate"], reverse=reverse_order)
    elif sort_by == "searches":
        result.sort(key=lambda x: x["total_searches"], reverse=reverse_order)
    
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
    from minesearch.database import db_manager
    
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
    from minesearch.database import db_manager
    
    stats = db_manager.get_statistics()
    return {
        "success": True,
        "data": stats
    }

@router.get("/sources/{source_id}")
async def get_source_by_id(source_id: int):
    """Hole einzelne Quelle nach ID"""
    from minesearch.database import db_manager
    
    with db_manager.get_session() as session:
        source = session.query(Source).filter_by(id=source_id).first()
        if not source:
            raise HTTPException(status_code=404, detail="Quelle nicht gefunden")
        
        return {
            "success": True,
            "data": source.to_dict()
        }

@router.get("/sources/by-domain/{domain}")
async def get_sources_by_domain(domain: str):
    """
    ÄNDERUNG 10.08.2025: Neuer Endpoint für Domain-spezifische Quellen-Details
    Hole alle Quellen und detaillierte Informationen für eine spezifische Domain
    """
    from minesearch.database import db_manager
    
    # Input-Validierung
    if not domain or domain.strip() == "":
        raise HTTPException(status_code=400, detail="Domain darf nicht leer sein")
    
    domain = domain.strip()
    logger.info(f"[SOURCES BY DOMAIN] Fetching details for domain: {domain}")
    
    try:
        with db_manager.get_session() as session:
            # Hole alle Quellen für die Domain
            sources_query = session.query(Source).filter(Source.domain == domain)
            sources = sources_query.all()
            
            if not sources:
                logger.warning(f"[SOURCES BY DOMAIN] No sources found for domain: {domain}")
                raise HTTPException(status_code=404, detail=f"Keine Quellen für Domain '{domain}' gefunden")
            
            # Berechne detaillierte Domain-Statistiken
            total_sources = len(sources)
            total_searches = sum(s.total_searches for s in sources)
            successful_searches = sum(s.successful_searches for s in sources) 
            avg_reliability = sum(s.reliability_score for s in sources) / total_sources
            success_rate = (successful_searches / total_searches * 100) if total_searches > 0 else 0
            
            # Sammle zusätzliche Metadaten
            countries = list(set(s.country for s in sources if s.country))
            source_types = list(set(s.source_type for s in sources))
            recent_access = any(s.last_successful_access for s in sources)
            
            # Erstelle detaillierte Response - optimiert für Performance bei großen Domains
            sources_data = []
            for source in sources:
                source_dict = source.to_dict()
                
                # Berechne spezifische Metriken pro Quelle (optimiert)
                source_dict['individual_success_rate'] = round(
                    source.successful_searches / source.total_searches * 100 
                    if source.total_searches > 0 else 0, 2
                )
                
                # Optimiere last_access_days_ago Berechnung
                if source.last_successful_access and source.created_at:
                    try:
                        source_dict['last_access_days_ago'] = (source.last_successful_access - source.created_at).days
                    except (TypeError, AttributeError):
                        source_dict['last_access_days_ago'] = None
                else:
                    source_dict['last_access_days_ago'] = None
                    
                # Entferne potentiell große/unnötige Felder für bessere Performance
                if 'typical_content_types' in source_dict and not source_dict['typical_content_types']:
                    source_dict['typical_content_types'] = []
                    
                sources_data.append(source_dict)
            
            # Sortiere Quellen nach Zuverlässigkeit
            sources_data.sort(key=lambda x: x['reliability_score'], reverse=True)
            
            result = {
                "domain": domain,
                "summary": {
                    "total_sources": total_sources,
                    "total_searches": total_searches,
                    "successful_searches": successful_searches,
                    "avg_reliability_score": round(avg_reliability, 2),
                    "success_rate_percent": round(success_rate, 2),
                    "countries_covered": countries,
                    "source_types": source_types,
                    "has_recent_access": recent_access
                },
                "sources": sources_data,
                "metadata": {
                    "best_source": sources_data[0] if sources_data else None,
                    "worst_source": sources_data[-1] if sources_data else None,
                    "total_countries": len(countries),
                    "total_source_types": len(source_types)
                }
            }
            
            logger.info(f"[SOURCES BY DOMAIN] Successfully fetched {total_sources} sources for domain: {domain}")
            
            return {
                "success": True,
                "data": result
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[SOURCES BY DOMAIN] Error fetching sources for domain {domain}: {e}")
        raise HTTPException(status_code=500, detail=f"Interner Server-Fehler: {str(e)}")

@router.post("/sources/search")
async def search_sources_for_mine(
    mine_name: str = Body(...),
    country: Optional[str] = Body(None),
    region: Optional[str] = Body(None)
):
    """Suche relevante Quellen für eine spezifische Mine"""
    from database.manager import DatabaseManager
    db_manager = DatabaseManager()
    
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

@router.post("/sources/seed")
async def seed_sources_database(
    force: bool = Body(False, description="Force seeding even if sources already exist")
):
    """
    ÄNDERUNG 15.07.2025: Neuer Endpoint zum Befüllen der Quellen-Datenbank
    Befüllt die leere Datenbank mit Standard-Mining-Quellen
    """
    try:
        from seed_sources import seed_database_sources
        
        logger.info(f"[SOURCES SEED] Starting database seeding, force={force}")
        
        result = seed_database_sources(force=force)
        
        if result["success"]:
            logger.info(f"[SOURCES SEED] Success: {result['statistics']['final_database_count']} sources")
            return {
                "success": True,
                "message": "Sources database seeded successfully",
                "data": result["statistics"]
            }
        else:
            logger.warning(f"[SOURCES SEED] Skipped: {result['message']}")
            return {
                "success": False,
                "message": result["message"],
                "data": {
                    "existing_count": result.get("existing_count", 0),
                    "action": result.get("action", "skipped")
                }
            }
            
    except Exception as e:
        logger.error(f"[SOURCES SEED] Error: {e}")
        return {
            "success": False,
            "message": f"Error seeding sources database: {str(e)}",
            "error": str(e)
        }