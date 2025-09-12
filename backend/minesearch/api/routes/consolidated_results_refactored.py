"""
Author: rahn
Datum: 11.09.2025
Version: 2.0
Beschreibung: Konsolidierte Ergebnis-Management Routes für Mine-basierte Ansicht (Refactored)
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, List, Any
import logging
from minesearch.database import SearchResult
from collections import defaultdict

# Import field mappings from separated utility module
from .consolidated_field_utils import (
    FIELD_CONSOLIDATION_MAP, 
    FIELD_RENAME_MAP, 
    FIELD_ORDER,
    consolidate_and_rename_field
)

# Import refactored modules
from .consolidated_utils import (
    _normalize_placeholder_value,
    _analyze_field_values,
    _calculate_best_value
)
from .consolidated_validators import (
    validate_and_score_field_values,
    create_result_metadata,
    create_structured_fields_response,
    create_quality_metrics,
    filter_best_values_for_legacy_compatibility
)
from .consolidated_processors import (
    process_mine_data_grouping,
    select_display_names,
    process_best_value_algorithm,
    create_global_source_index
)
from .consolidated_exporters import router as export_router

logger = logging.getLogger(__name__)
router = APIRouter()

# Include CSV export routes from consolidated_exporters
router.include_router(export_router)


@router.get("/results")
async def get_consolidated_results(
    country: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    days_back: int = Query(30),
    sort_by: str = Query("mine_name"),
    order: str = Query("asc"),
    exclude_exa: bool = Query(True)
):
    """
    Hole konsolidierte Suchergebnisse pro Mine mit allen Modell-Daten
    
    PHASE 1.2: Gruppierung nach Mine + vollständige Feldkonsolidierung
    
    Returns strukturierte Daten mit:
    - Mine-basierte Gruppierung  
    - Best-Value Algorithmus für alle Felder
    - Globaler Quellenindex
    - Konfidenz-Scoring für jeden Wert
    """
    try:
        from minesearch.database import db_manager
        from datetime import datetime, timedelta
        
        cutoff = datetime.now() - timedelta(days=days_back)
        
        with db_manager.get_session() as session:
            query = session.query(SearchResult).filter(
                SearchResult.search_timestamp >= cutoff
            )
            
            if exclude_exa:
                query = query.filter(~SearchResult.ai_model.like('%exa%'))
            
            if country:
                query = query.filter(SearchResult.country.ilike(f'%{country}%'))
                
            if region:
                query = query.filter(SearchResult.region.ilike(f'%{region}%'))
                
            all_results = query.all()
            
            if not all_results:
                return {
                    "success": True,
                    "data": {
                        "consolidated_results": [],
                        "total_count": 0,
                        "global_source_index": {},
                        "metadata": {
                            "days_back": days_back,
                            "country_filter": country,
                            "region_filter": region,
                            "exclude_exa": exclude_exa,
                            "sort_by": sort_by,
                            "order": order
                        }
                    }
                }
        
        # Process data using refactored modules
        global_source_index_func = lambda: create_global_source_index(all_results)
        grouped_data = process_mine_data_grouping(all_results, global_source_index_func)
        
        consolidated_results = []
        for mine_name, mine_data in grouped_data.items():
            # Process using new validation system
            detailed_breakdown = {}
            best_values = {}
            
            for field_name, field_data in mine_data.get('all_fields', {}).items():
                if field_name.startswith('_'):
                    continue
                    
                field_result = validate_and_score_field_values(field_data, field_name)
                detailed_breakdown[field_name] = field_result
                
                if field_result['validation_passed']:
                    best_values[field_name] = field_result['best_value_info']['display_value']
            
            # Filter best values for legacy compatibility
            filtered_best_values = filter_best_values_for_legacy_compatibility(best_values, detailed_breakdown)
            
            # Create result metadata
            result_metadata = create_result_metadata(mine_data, filtered_best_values, detailed_breakdown)
            
            # Create structured fields response
            structured_fields = create_structured_fields_response(
                detailed_breakdown, 
                filtered_best_values, 
                mine_data, 
                global_source_index_func()
            )
            
            # Create quality metrics
            quality_metrics = create_quality_metrics(detailed_breakdown)
            
            consolidated_result = {
                **result_metadata['metadata'],
                'best_values': filtered_best_values,
                'detailed_breakdown': detailed_breakdown,
                'structured_fields': structured_fields,
                'overall_confidence': result_metadata['overall_confidence'],
                'quality_metrics': quality_metrics,
                'validation_summary': result_metadata['validation_summary']
            }
            
            consolidated_results.append(consolidated_result)
        
        # Sort results
        if sort_by in ["mine_name", "country", "region"]:
            reverse = order.lower() == "desc"
            consolidated_results.sort(
                key=lambda x: x.get(sort_by, "").lower(),
                reverse=reverse
            )
        elif sort_by == "overall_confidence":
            reverse = order.lower() == "desc"
            consolidated_results.sort(
                key=lambda x: x.get("overall_confidence", 0),
                reverse=reverse
            )
        
        return {
            "success": True,
            "data": {
                "consolidated_results": consolidated_results,
                "total_count": len(consolidated_results),
                "global_source_index": global_source_index_func(),
                "metadata": {
                    "days_back": days_back,
                    "country_filter": country,
                    "region_filter": region,
                    "exclude_exa": exclude_exa,
                    "sort_by": sort_by,
                    "order": order,
                    "processing_summary": {
                        "raw_results": len(all_results),
                        "consolidated_mines": len(consolidated_results),
                        "source_index_size": len(global_source_index_func())
                    }
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error in get_consolidated_results: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Serverfehler: {str(e)}")


@router.get("/results/{mine_name}/details")
async def get_mine_details(mine_name: str, days_back: int = Query(30)):
    """
    Hole detaillierte Informationen zu einer spezifischen Mine
    """
    try:
        from minesearch.database import db_manager
        from datetime import datetime, timedelta
        
        cutoff = datetime.now() - timedelta(days=days_back)
        
        with db_manager.get_session() as session:
            results = session.query(SearchResult).filter(
                SearchResult.mine_name.ilike(f'%{mine_name}%'),
                SearchResult.search_timestamp >= cutoff
            ).all()
        
        if not results:
            raise HTTPException(status_code=404, detail=f"Mine '{mine_name}' nicht gefunden")
        
        # Process using new system
        mine_data = process_mine_data_grouping(results, lambda: create_global_source_index(results))
        if mine_name not in mine_data:
            # Try finding by partial match
            matching_mine = None
            for key in mine_data.keys():
                if mine_name.lower() in key.lower():
                    matching_mine = key
                    break
            
            if not matching_mine:
                raise HTTPException(status_code=404, detail=f"Mine '{mine_name}' nicht gefunden")
            
            mine_name = matching_mine
        
        detailed_mine = mine_data[mine_name]
        
        # Process detailed breakdown
        detailed_breakdown = {}
        best_values = {}
        
        for field_name, field_data in detailed_mine.get('all_fields', {}).items():
            if field_name.startswith('_'):
                continue
                
            field_result = validate_and_score_field_values(field_data, field_name)
            detailed_breakdown[field_name] = field_result
            
            if field_result['validation_passed']:
                best_values[field_name] = field_result['best_value_info']['display_value']
        
        result_metadata = create_result_metadata(detailed_mine, best_values, detailed_breakdown)
        
        return {
            "success": True,
            "data": {
                "mine_name": mine_name,
                "details": detailed_breakdown,
                "best_values": best_values,
                "metadata": result_metadata,
                "raw_data_summary": {
                    "total_searches": len(results),
                    "models_used": len(set(r.ai_model for r in results)),
                    "date_range": {
                        "from": min(r.search_timestamp for r in results).isoformat(),
                        "to": max(r.search_timestamp for r in results).isoformat()
                    }
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting mine details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Serverfehler: {str(e)}")


@router.get("/mine/{mine_name}")
async def get_mine_consolidated_data(mine_name: str, days_back: int = Query(30)):
    """
    Shortcut-Route für Mine-spezifische konsolidierte Daten
    """
    return await get_mine_details(mine_name, days_back)


@router.get("/normalized/results")
async def get_normalized_consolidated_results(
    country: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    days_back: int = Query(30),
    sort_by: str = Query("mine_name"),
    order: str = Query("asc"),
    exclude_exa: bool = Query(True)
):
    """
    Alternative Route für normalisierte konsolidierte Ergebnisse
    Verwendet atomische Werte wenn verfügbar
    """
    try:
        # Use atomic value service if available
        from minesearch.atomic_value_service import calculate_best_atomic_value
        from minesearch.database import db_manager
        from datetime import datetime, timedelta
        
        # Get base results
        base_results = await get_consolidated_results(
            country=country,
            region=region, 
            days_back=days_back,
            sort_by=sort_by,
            order=order,
            exclude_exa=exclude_exa
        )
        
        if not base_results["success"]:
            return base_results
        
        # Enhance with atomic values
        consolidated_results = base_results["data"]["consolidated_results"]
        
        with db_manager.get_session() as session:
            for result in consolidated_results:
                mine_name = result["mine_name"]
                enhanced_values = {}
                
                for field_name in result.get("best_values", {}):
                    try:
                        atomic_result = calculate_best_atomic_value(
                            session, mine_name, field_name, fallback_to_json=True
                        )
                        
                        if atomic_result.get('method') == 'atomic_normalized':
                            enhanced_values[field_name] = atomic_result.get('display_value')
                    except Exception as e:
                        logger.debug(f"Atomic value lookup failed for {mine_name}.{field_name}: {e}")
                
                # Update with enhanced values
                result["normalized_values"] = enhanced_values
                result["enhancement_status"] = {
                    "atomic_values_found": len(enhanced_values),
                    "total_fields": len(result.get("best_values", {}))
                }
        
        return base_results
        
    except Exception as e:
        logger.error(f"Error in normalized results: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Serverfehler: {str(e)}")


@router.get("/normalized/schema/comparison")
async def get_schema_comparison():
    """
    Vergleiche Schema zwischen JSON-basierten und normalisierten Ergebnissen
    """
    try:
        from minesearch.database import db_manager
        
        with db_manager.get_session() as session:
            # Get sample of recent results
            recent_results = session.query(SearchResult).limit(100).all()
            
            json_fields = set()
            for result in recent_results:
                try:
                    if result.structured_data:
                        import json
                        data = json.loads(result.structured_data) if isinstance(result.structured_data, str) else result.structured_data
                        json_fields.update(data.keys())
                except Exception:
                    continue
            
            # Get atomic table fields
            try:
                from minesearch.database import AtomicValue
                atomic_fields = set()
                sample_atomic = session.query(AtomicValue.field_name).distinct().limit(100).all()
                atomic_fields = set(field[0] for field in sample_atomic)
            except Exception:
                atomic_fields = set()
            
            return {
                "success": True,
                "data": {
                    "schema_comparison": {
                        "json_only_fields": sorted(json_fields - atomic_fields),
                        "atomic_only_fields": sorted(atomic_fields - json_fields),
                        "common_fields": sorted(json_fields & atomic_fields),
                        "json_total": len(json_fields),
                        "atomic_total": len(atomic_fields),
                        "overlap_percentage": round((len(json_fields & atomic_fields) / max(len(json_fields), 1)) * 100, 1)
                    }
                }
            }
    
    except Exception as e:
        logger.error(f"Error in schema comparison: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Serverfehler: {str(e)}")


@router.get("/mine/{mine_name}/statistics")
async def get_mine_statistics(mine_name: str, days_back: int = Query(30)):
    """
    Hole erweiterte Statistiken für eine Mine
    """
    try:
        from minesearch.database import db_manager
        from datetime import datetime, timedelta
        
        cutoff = datetime.now() - timedelta(days=days_back)
        
        with db_manager.get_session() as session:
            results = session.query(SearchResult).filter(
                SearchResult.mine_name.ilike(f'%{mine_name}%'),
                SearchResult.search_timestamp >= cutoff
            ).all()
        
        if not results:
            raise HTTPException(status_code=404, detail=f"Keine Daten für Mine '{mine_name}' gefunden")
        
        # Statistical analysis
        total_searches = len(results)
        models_used = list(set(r.ai_model for r in results))
        search_dates = [r.search_timestamp for r in results if r.search_timestamp]
        
        # Field analysis
        analyzed_fields = {}
        for result in results:
            try:
                import json
                data = json.loads(result.structured_data) if isinstance(result.structured_data, str) else result.structured_data
                if data:
                    for field, value in data.items():
                        if field not in analyzed_fields:
                            analyzed_fields[field] = {
                                'values': [],
                                'models': [],
                                'consistency_rate': 0
                            }
                        
                        analyzed_fields[field]['values'].append(value)
                        analyzed_fields[field]['models'].append(result.ai_model)
            except Exception:
                continue
        
        # Calculate consistency rates
        for field, data in analyzed_fields.items():
            unique_values = len(set(str(v).lower() for v in data['values'] if v))
            total_values = len([v for v in data['values'] if v])
            
            if total_values > 0:
                consistency_rate = ((total_values - unique_values + 1) / total_values) * 100
                analyzed_fields[field]['consistency_rate'] = round(consistency_rate, 1)
                analyzed_fields[field]['unique_values'] = unique_values
                analyzed_fields[field]['total_occurrences'] = total_values
        
        # Model performance
        model_performance = {}
        for model in models_used:
            model_results = [r for r in results if r.ai_model == model]
            if model_results:
                total_fields = sum(len(json.loads(r.structured_data) if isinstance(r.structured_data, str) else r.structured_data if r.structured_data else {}) for r in model_results)
                avg_response_time = sum(r.search_duration for r in model_results if r.search_duration) / len(model_results)
                
                model_performance[model] = {
                    'searches': len(model_results),
                    'avg_fields_found': round(total_fields / len(model_results), 1) if model_results else 0,
                    'avg_response_time': round(avg_response_time, 2) if avg_response_time else 0,
                    'success_rate': round(len([r for r in model_results if r.structured_data]) / len(model_results) * 100, 1)
                }
        
        # Quality score calculation
        quality_indicators = []
        for field_data in analyzed_fields.values():
            if field_data['consistency_rate'] > 80:
                quality_indicators.append(1.0)
            elif field_data['consistency_rate'] > 60:
                quality_indicators.append(0.7)
            else:
                quality_indicators.append(0.3)
        
        overall_quality = round(sum(quality_indicators) / len(quality_indicators) * 100, 1) if quality_indicators else 0
        
        return {
            'success': True,
            'data': {
                'mine_name': mine_name,
                'analysis_period': {
                    'days_back': days_back,
                    'from_date': cutoff.strftime('%Y-%m-%d'),
                    'to_date': datetime.now().strftime('%Y-%m-%d'),
                    'total_searches': total_searches
                },
                'field_statistics': analyzed_fields,
                'model_performance': model_performance,
                'quality_metrics': {
                    'overall_quality_score': overall_quality,
                    'total_fields_analyzed': len(analyzed_fields),
                    'models_used_count': len(models_used),
                    'consistency_rating': 'Hoch' if overall_quality > 80 else 'Mittel' if overall_quality > 60 else 'Niedrig'
                },
                'timeline': {
                    'first_search': min(search_dates).strftime('%Y-%m-%d %H:%M') if search_dates else None,
                    'last_search': max(search_dates).strftime('%Y-%m-%d %H:%M') if search_dates else None,
                    'search_frequency': f"{len(search_dates) / days_back:.1f} Suchen pro Tag"
                }
            }
        }

    except Exception as e:
        logger.error(f"[STATISTICS] Error getting mine statistics: {e}")
        return {
            'success': False,
            'error': f'Fehler beim Laden der Mine-Statistiken: {str(e)}',
            'mine_name': mine_name
        }