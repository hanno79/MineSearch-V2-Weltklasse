"""
Author: rahn
Datum: 24.07.2025
Version: 1.0
Beschreibung: Enhanced Statistics API - Erweiterte Statistik-Endpoints im Stil der konsolidierten Ergebnisse
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime, timedelta
from sqlalchemy import func, desc, asc, and_, or_

from minesearch.database import db_manager
from minesearch.database.models import ModelStatistics, ModelSummary, FieldStatistics, SearchResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/statistics", tags=["enhanced-statistics"])

@router.get("/models/detailed")
async def get_detailed_model_statistics(
    country: Optional[str] = Query(None, description="Filter nach Land"),
    region: Optional[str] = Query(None, description="Filter nach Region"),
    days_back: int = Query(30, description="Tage zurück"),
    sort_by: str = Query("success_rate", description="Sort by: model_id, success_rate, avg_fields_found, avg_response_time, total_tests"),
    order: str = Query("desc", description="Order: asc or desc"),
    exclude_failed: bool = Query(True, description="Exclude models with 0% success rate")
):
    """
    Detaillierte Modell-Statistiken im Stil der konsolidierten Ergebnisse
    """
    try:
        with db_manager.get_session() as session:
            # Basis-Query für ModelSummary mit erweiterten Statistiken
            query = session.query(ModelSummary)
            
            # Filter
            if exclude_failed:
                query = query.filter(ModelSummary.success_rate > 0)
            
            # Zeitfilter über ModelStatistics
            if days_back < 9999:
                cutoff_date = datetime.now() - timedelta(days=days_back)
                # Subquery für Modelle die in der Zeit aktiv waren
                recent_models = session.query(ModelStatistics.model_id).filter(
                    ModelStatistics.timestamp >= cutoff_date
                ).distinct().subquery()
                query = query.filter(ModelSummary.model_id.in_(
                    session.query(recent_models.c.model_id)
                ))
            
            # Sortierung
            sort_column = getattr(ModelSummary, sort_by, ModelSummary.success_rate)
            if order.lower() == 'desc':
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))
            
            results = query.all()
            
            # Erweitere mit zusätzlichen Statistiken
            enhanced_results = []
            for result in results:
                # Hole zusätzliche Statistiken aus ModelStatistics
                detailed_stats = session.query(
                    func.count(ModelStatistics.id).label('total_runs'),
                    func.sum(ModelStatistics.fields_found).label('total_fields'),
                    func.avg(ModelStatistics.response_time_ms).label('avg_response'),
                    func.count(ModelStatistics.id).filter(ModelStatistics.success == True).label('successful_runs')
                ).filter(
                    ModelStatistics.model_id == result.model_id
                ).first()
                
                # Hole Feld-spezifische Performance
                field_performance = session.query(
                    FieldStatistics.field_name,
                    FieldStatistics.success_rate,
                    FieldStatistics.times_found,
                    FieldStatistics.total_searches
                ).filter(
                    FieldStatistics.model_id == result.model_id
                ).order_by(desc(FieldStatistics.success_rate)).all()
                
                # Performance-Kategorie bestimmen
                performance_category = "Schlecht"
                if result.success_rate >= 0.8 and result.avg_fields_found >= 5:
                    performance_category = "Exzellent"
                elif result.success_rate >= 0.6 and result.avg_fields_found >= 3:
                    performance_category = "Gut"
                elif result.success_rate >= 0.4 and result.avg_fields_found >= 2:
                    performance_category = "Mittel"
                elif result.success_rate > 0:
                    performance_category = "Schwach"
                
                enhanced_results.append({
                    'model_id': result.model_id,
                    'model_name': result.model_id.replace(':', ' - ').title(),
                    'total_tests': result.total_tests or 0,
                    'total_mines_tested': result.total_mines_tested or 0,
                    'success_rate': round((result.success_rate or 0) * 100, 1),
                    'data_success_rate': round((result.data_success_rate or 0) * 100, 1),
                    'avg_fields_found': round(max(result.avg_fields_found or 0, 1), 2),
                    'avg_response_time_ms': round(result.avg_response_time_ms or 0, 0),
                    'avg_sources_count': round(max(result.avg_sources_count or 0, 1), 1),
                    'overall_consistency': round((result.overall_consistency or 0) * 100, 1),
                    'total_estimated_cost': round(result.total_estimated_cost or 0, 2),
                    'performance_category': performance_category,
                    'critical_fields_consistency': result.critical_fields_consistency or {},
                    'field_performance': [
                        {
                            'field_name': fp.field_name,
                            'success_rate': round(fp.success_rate, 1),
                            'times_found': fp.times_found,
                            'total_searches': fp.total_searches
                        } for fp in field_performance[:10]  # Top 10 Felder
                    ],
                    'last_test_at': result.last_test_at.isoformat() if result.last_test_at else None,
                    'days_since_test': (datetime.now() - result.last_test_at).days if result.last_test_at else 999
                })
            
            # Gesamtstatistiken
            total_models = len(enhanced_results)
            total_tests = sum(r['total_tests'] for r in enhanced_results)
            avg_success_rate = sum(r['success_rate'] for r in enhanced_results) / total_models if total_models > 0 else 0
            
            return {
                "success": True,
                "data": {
                    "model_statistics": enhanced_results,
                    "summary": {
                        "total_models": total_models,
                        "total_tests": total_tests,
                        "avg_success_rate": round(avg_success_rate, 1),
                        "last_updated": datetime.now().isoformat()
                    }
                },
                "message": f"Successfully loaded statistics for {total_models} models"
            }
            
    except Exception as e:
        logger.error(f"Error loading detailed model statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Error loading statistics: {str(e)}")


@router.get("/fields/performance")
async def get_field_performance_statistics(
    model_id: Optional[str] = Query(None, description="Filter nach Modell"),
    sort_by: str = Query("success_rate", description="Sort by: field_name, success_rate, times_found, total_searches"),
    order: str = Query("desc", description="Order: asc or desc"),
    min_searches: int = Query(1, description="Mindestanzahl Suchen")
):
    """
    Detaillierte Feld-Performance-Statistiken
    """
    try:
        with db_manager.get_session() as session:
            query = session.query(
                FieldStatistics.field_name,
                func.count(FieldStatistics.model_id).label('models_count'),
                func.avg(FieldStatistics.success_rate).label('avg_success_rate'),
                func.sum(FieldStatistics.times_found).label('total_found'),
                func.sum(FieldStatistics.total_searches).label('total_searches'),
                func.max(FieldStatistics.success_rate).label('best_success_rate'),
                func.min(FieldStatistics.success_rate).label('worst_success_rate')
            ).group_by(FieldStatistics.field_name)
            
            if model_id:
                query = query.filter(FieldStatistics.model_id == model_id)
            
            if min_searches > 1:
                query = query.having(func.sum(FieldStatistics.total_searches) >= min_searches)
            
            # Sortierung
            sort_mapping = {
                'field_name': FieldStatistics.field_name,
                'success_rate': 'avg_success_rate',
                'times_found': 'total_found',
                'total_searches': 'total_searches'
            }
            
            sort_column = sort_mapping.get(sort_by, 'avg_success_rate')
            if order.lower() == 'desc':
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))
            
            results = query.all()
            
            field_stats = []
            for result in results:
                avg_success = result.avg_success_rate or 0
                field_category = "Schlecht"
                if avg_success >= 0.8:
                    field_category = "Exzellent"
                elif avg_success >= 0.6:
                    field_category = "Gut"
                elif avg_success >= 0.4:
                    field_category = "Mittel"
                elif avg_success > 0:
                    field_category = "Schwach"
                
                field_stats.append({
                    'field_name': result.field_name,
                    'models_count': result.models_count,
                    'avg_success_rate': round(avg_success * 100, 1),
                    'total_found': result.total_found or 0,
                    'total_searches': result.total_searches or 0,
                    'best_success_rate': round((result.best_success_rate or 0) * 100, 1),
                    'worst_success_rate': round((result.worst_success_rate or 0) * 100, 1),
                    'category': field_category,
                    'find_rate': round((result.total_found / result.total_searches * 100) if result.total_searches > 0 else 0, 1)
                })
            
            return {
                "success": True,
                "data": {
                    "field_statistics": field_stats,
                    "summary": {
                        "total_fields": len(field_stats),
                        "avg_success_rate": round(sum(f['avg_success_rate'] for f in field_stats) / len(field_stats), 1) if field_stats else 0
                    }
                }
            }
            
    except Exception as e:
        logger.error(f"Error loading field performance statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Error loading field statistics: {str(e)}")


@router.get("/model/{model_id}/details")
async def get_model_details(
    model_id: str,
    days_back: int = Query(30, description="Tage zurück")
):
    """
    Detaillierte Informationen zu einem spezifischen Modell
    """
    try:
        with db_manager.get_session() as session:
            # Basis-Modell-Informationen
            model_summary = session.query(ModelSummary).filter(
                ModelSummary.model_id == model_id
            ).first()
            
            if not model_summary:
                raise HTTPException(status_code=404, detail=f"Model {model_id} not found")
            
            # Zeitfilter
            cutoff_date = datetime.now() - timedelta(days=days_back) if days_back < 9999 else datetime.min
            
            # Detaillierte Statistiken
            recent_stats = session.query(ModelStatistics).filter(
                and_(
                    ModelStatistics.model_id == model_id,
                    ModelStatistics.timestamp >= cutoff_date
                )
            ).order_by(desc(ModelStatistics.timestamp)).all()
            
            # Feld-Performance
            field_performance = session.query(FieldStatistics).filter(
                FieldStatistics.model_id == model_id
            ).order_by(desc(FieldStatistics.success_rate)).all()
            
            # Performance über Zeit (letzte 30 Tage)
            daily_performance = session.query(
                func.date(ModelStatistics.timestamp).label('date'),
                func.count(ModelStatistics.id).label('total_runs'),
                func.sum(ModelStatistics.fields_found).label('total_fields'),
                func.avg(ModelStatistics.response_time_ms).label('avg_response')
            ).filter(
                and_(
                    ModelStatistics.model_id == model_id,
                    ModelStatistics.timestamp >= cutoff_date
                )
            ).group_by(func.date(ModelStatistics.timestamp)).order_by('date').all()
            
            return {
                "success": True,
                "data": {
                    "model_id": model_id,
                    "model_name": model_id.replace(':', ' - ').title(),
                    "summary": model_summary.to_dict(),
                    "recent_runs": [stat.to_dict() for stat in recent_stats[:20]],
                    "field_performance": [fp.to_dict() for fp in field_performance],
                    "daily_performance": [
                        {
                            'date': str(dp.date),
                            'total_runs': dp.total_runs,
                            'total_fields': dp.total_fields or 0,
                            'avg_response_time': round(dp.avg_response or 0, 0)
                        } for dp in daily_performance
                    ]
                }
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading model details for {model_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error loading model details: {str(e)}")


@router.get("/export/csv")
async def export_statistics_csv(
    table: str = Query("models", description="Table to export: models, fields, detailed"),
    model_id: Optional[str] = Query(None, description="Filter nach Modell"),
    days_back: int = Query(30, description="Tage zurück")
):
    """
    Export Statistiken als CSV im Stil der konsolidierten Ergebnisse
    """
    try:
        from io import StringIO
        import csv
        from fastapi.responses import StreamingResponse
        
        if table == "models":
            # Export Modell-Statistiken
            response = await get_detailed_model_statistics(
                days_back=days_back, 
                sort_by="success_rate", 
                order="desc"
            )
            data = response["data"]["model_statistics"]
            
            output = StringIO()
            writer = csv.writer(output, delimiter='|')
            
            # Header
            writer.writerow([
                'Model ID', 'Model Name', 'Total Tests', 'Mines Tested',
                'Success Rate (%)', 'Data Success Rate (%)', 'Avg Fields Found',
                'Avg Response Time (ms)', 'Avg Sources', 'Consistency (%)',
                'Performance Category', 'Total Cost', 'Last Test'
            ])
            
            # Daten
            for item in data:
                writer.writerow([
                    item['model_id'], item['model_name'], item['total_tests'],
                    item['total_mines_tested'], item['success_rate'], 
                    item['data_success_rate'], item['avg_fields_found'],
                    item['avg_response_time_ms'], item['avg_sources_count'],
                    item['overall_consistency'], item['performance_category'],
                    item['total_estimated_cost'], item['last_test_at']
                ])
            
        elif table == "fields":
            # Export Feld-Statistiken
            response = await get_field_performance_statistics(
                model_id=model_id,
                sort_by="success_rate",
                order="desc"
            )
            data = response["data"]["field_statistics"]
            
            output = StringIO()
            writer = csv.writer(output, delimiter='|')
            
            # Header
            writer.writerow([
                'Field Name', 'Models Count', 'Avg Success Rate (%)',
                'Total Found', 'Total Searches', 'Best Success Rate (%)',
                'Worst Success Rate (%)', 'Category', 'Find Rate (%)'
            ])
            
            # Daten
            for item in data:
                writer.writerow([
                    item['field_name'], item['models_count'], item['avg_success_rate'],
                    item['total_found'], item['total_searches'], item['best_success_rate'],
                    item['worst_success_rate'], item['category'], item['find_rate']
                ])
        
        else:
            raise HTTPException(status_code=400, detail="Invalid table parameter. Use 'models' or 'fields'")
        
        output.seek(0)
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=minesearch_statistics_{table}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting statistics CSV: {e}")
        raise HTTPException(status_code=500, detail=f"Error exporting CSV: {str(e)}")