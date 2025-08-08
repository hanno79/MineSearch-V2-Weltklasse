"""
Author: rahn
Datum: 06.08.2025
Version: 1.0
Beschreibung: Mine-spezifische API Endpunkte (früher results/mines und results/statistics)
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import logging
from sqlalchemy import text

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/mines")
async def get_mines_list(
    country: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    limit: int = Query(50),
    offset: int = Query(0)
):
    """
    Hole Liste aller Minen mit Basis-Informationen
    FIXED API Route: /api/mines statt /api/results/mines
    """
    from database import db_manager
    
    try:
        with db_manager.get_session() as session:
            # Verwende direkte SQL-Abfrage für bessere Performance
            query_str = """
                SELECT DISTINCT 
                    mine_name,
                    country,
                    region,
                    COUNT(*) as search_count,
                    MAX(search_timestamp) as last_search
                FROM search_results 
                WHERE mine_name IS NOT NULL AND mine_name != ''
            """
            
            params = []
            if country:
                query_str += " AND country = :country"
                params.append(('country', country))
            
            if region:
                query_str += " AND region = :region"  
                params.append(('region', region))
            
            query_str += " GROUP BY mine_name, country, region ORDER BY mine_name LIMIT :limit OFFSET :offset"
            params.extend([('limit', limit), ('offset', offset)])
            
            # Convert params to dict
            params_dict = dict(params)
            
            result = session.execute(text(query_str), params_dict)
            mines = []
            
            for row in result.fetchall():
                last_search = row[4]
                if last_search and hasattr(last_search, 'isoformat'):
                    last_search_str = last_search.isoformat()
                else:
                    last_search_str = str(last_search) if last_search else None
                    
                mines.append({
                    'mine_name': row[0],
                    'country': row[1] or '',
                    'region': row[2] or '',
                    'search_count': row[3],
                    'last_search': last_search_str
                })
            
            return {
                "success": True,
                "data": mines,
                "count": len(mines)
            }
            
    except Exception as e:
        logger.error(f"Error getting mines list: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/mines/statistics")
async def get_mines_statistics(
    days_back: int = Query(30),
    exclude_exa: bool = Query(True)
):
    """
    Hole Statistiken über alle Minen
    FIXED API Route: /api/mines/statistics statt /api/results/statistics
    """
    from database import db_manager
    from datetime import datetime, timedelta
    
    try:
        with db_manager.get_session() as session:
            # Base query conditions
            where_conditions = ["mine_name IS NOT NULL"]
            params_dict = {}
            
            if exclude_exa:
                where_conditions.append("model_used NOT LIKE :exa_pattern")
                params_dict['exa_pattern'] = 'exa:%'
            
            if days_back > 0:
                cutoff = datetime.now() - timedelta(days=days_back)
                where_conditions.append("search_timestamp >= :cutoff_date")
                params_dict['cutoff_date'] = cutoff
            
            base_where = " AND ".join(where_conditions)
            
            # Total mines
            total_mines_query = f"SELECT COUNT(DISTINCT mine_name) FROM search_results WHERE {base_where}"
            total_mines = session.execute(text(total_mines_query), params_dict).scalar()
            
            # Total searches
            total_searches_query = f"SELECT COUNT(*) FROM search_results WHERE {base_where}"
            total_searches = session.execute(text(total_searches_query), params_dict).scalar()
            
            # Successful searches
            success_query = f"SELECT COUNT(*) FROM search_results WHERE {base_where} AND success = 1"
            successful_searches = session.execute(text(success_query), params_dict).scalar()
            
            # Countries
            countries_query = f"SELECT COUNT(DISTINCT country) FROM search_results WHERE {base_where} AND country IS NOT NULL"
            total_countries = session.execute(text(countries_query), params_dict).scalar()
            
            # Models used
            models_query = f"SELECT COUNT(DISTINCT model_used) FROM search_results WHERE {base_where}"
            total_models = session.execute(text(models_query), params_dict).scalar()
            
            # Success rate
            success_rate = (successful_searches / total_searches * 100) if total_searches > 0 else 0
            
            statistics = {
                'total_mines': total_mines,
                'total_searches': total_searches,
                'successful_searches': successful_searches,
                'success_rate': round(success_rate, 1),
                'total_countries': total_countries,
                'total_models': total_models,
                'days_analyzed': days_back
            }
            
            return {
                "success": True,
                "data": statistics
            }
            
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/mines/{mine_name}")
async def get_mine_details(
    mine_name: str,
    include_results: bool = Query(False),
    limit: int = Query(10)
):
    """
    Hole Details zu einer spezifischen Mine
    """
    from database import db_manager
    
    try:
        with db_manager.get_session() as session:
            # Basic mine info
            mine_query = """
                SELECT 
                    mine_name,
                    country,
                    region,
                    COUNT(*) as total_searches,
                    COUNT(CASE WHEN success = 1 THEN 1 END) as successful_searches,
                    MAX(search_timestamp) as last_search,
                    MIN(search_timestamp) as first_search
                FROM search_results 
                WHERE mine_name = :mine_name
                GROUP BY mine_name, country, region
            """
            
            result = session.execute(text(mine_query), {'mine_name': mine_name}).fetchone()
            
            if not result:
                raise HTTPException(status_code=404, detail=f"Mine '{mine_name}' not found")
            
            # Safe datetime handling
            def safe_isoformat(dt_obj):
                if dt_obj and hasattr(dt_obj, 'isoformat'):
                    return dt_obj.isoformat()
                elif dt_obj:
                    return str(dt_obj)
                else:
                    return None
                    
            mine_info = {
                'mine_name': result[0],
                'country': result[1] or '',
                'region': result[2] or '',
                'total_searches': result[3],
                'successful_searches': result[4],
                'success_rate': round((result[4] / result[3] * 100) if result[3] > 0 else 0, 1),
                'last_search': safe_isoformat(result[5]),
                'first_search': safe_isoformat(result[6])
            }
            
            # Include recent results if requested
            recent_results = []
            if include_results:
                results_query = """
                    SELECT id, model_used, search_timestamp, success, structured_data
                    FROM search_results 
                    WHERE mine_name = :mine_name
                    ORDER BY search_timestamp DESC
                    LIMIT :limit
                """
                
                results = session.execute(text(results_query), {
                    'mine_name': mine_name, 
                    'limit': limit
                }).fetchall()
                
                for res in results:
                    recent_results.append({
                        'id': res[0],
                        'model_used': res[1],
                        'timestamp': safe_isoformat(res[2]),
                        'success': bool(res[3]),
                        'fields_found': len([v for v in (res[4] or {}).values() if v]) if res[4] else 0
                    })
            
            return {
                "success": True,
                "data": {
                    "mine_info": mine_info,
                    "recent_results": recent_results if include_results else None
                }
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting mine details: {e}")
        raise HTTPException(status_code=500, detail=str(e))