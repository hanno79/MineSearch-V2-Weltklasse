"""
Author: rahn
Datum: 24.07.2025
Version: 1.0
Beschreibung: API-Implementierungs-Vorlage für MineSearch V2 Statistics Service
"""

from fastapi import APIRouter, Query, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, date
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from database.manager import DatabaseManager
from database.models import (
    ModelStatistics, FieldStatistics, ModelSummary, 
    SearchResult, FieldConsistency
)

# Router für Statistics API
router = APIRouter(prefix="/api/v2/statistics", tags=["statistics"])

class StatisticsService:
    """Zentraler Service für alle Statistik-Operationen"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def _parse_timeframe(self, timeframe: str) -> datetime:
        """Konvertiere Timeframe-String zu datetime"""
        now = datetime.now()
        timeframe_map = {
            '1h': now - timedelta(hours=1),
            '24h': now - timedelta(hours=24),
            '7d': now - timedelta(days=7),
            '30d': now - timedelta(days=30),
            '90d': now - timedelta(days=90),
            '1y': now - timedelta(days=365),
            'all': datetime(2020, 1, 1)  # Sehr weit zurück
        }
        return timeframe_map.get(timeframe, now - timedelta(days=30))
    
    # =========================================
    # MODEL STATISTICS METHODS
    # =========================================
    
    async def get_model_performance(
        self,
        model_id: Optional[str] = None,
        timeframe: str = '30d'
    ) -> Dict[str, Any]:
        """Hole detaillierte Model-Performance Metriken"""
        
        start_date = self._parse_timeframe(timeframe)
        
        with self.db.get_session() as session:
            query = session.query(ModelStatistics).filter(
                ModelStatistics.timestamp >= start_date
            )
            
            if model_id:
                query = query.filter(ModelStatistics.model_id == model_id)
            
            stats = query.all()
            
            if not stats:
                return {"error": "No statistics found for the given criteria"}
            
            # Gruppiere nach Model ID
            model_data = {}
            for stat in stats:
                if stat.model_id not in model_data:
                    model_data[stat.model_id] = {
                        'total_tests': 0,
                        'successful_tests': 0,
                        'total_response_time': 0,
                        'total_fields_found': 0,
                        'total_sources_count': 0,
                        'tests': []
                    }
                
                model_data[stat.model_id]['total_tests'] += 1
                if stat.success:
                    model_data[stat.model_id]['successful_tests'] += 1
                    model_data[stat.model_id]['total_response_time'] += stat.response_time_ms or 0
                    model_data[stat.model_id]['total_fields_found'] += stat.fields_found
                    model_data[stat.model_id]['total_sources_count'] += stat.sources_count
                
                model_data[stat.model_id]['tests'].append({
                    'timestamp': stat.timestamp.isoformat(),
                    'mine_name': stat.mine_name,
                    'success': stat.success,
                    'response_time_ms': stat.response_time_ms,
                    'fields_found': stat.fields_found,
                    'sources_count': stat.sources_count
                })
            
            # Berechne aggregierte Metriken
            result = {}
            for model_id, data in model_data.items():
                successful_tests = data['successful_tests']
                
                result[model_id] = {
                    'model_id': model_id,
                    'total_tests': data['total_tests'],
                    'successful_tests': successful_tests,
                    'success_rate': successful_tests / data['total_tests'] if data['total_tests'] > 0 else 0,
                    'avg_response_time_ms': data['total_response_time'] / successful_tests if successful_tests > 0 else 0,
                    'avg_fields_found': data['total_fields_found'] / successful_tests if successful_tests > 0 else 0,
                    'avg_sources_count': data['total_sources_count'] / successful_tests if successful_tests > 0 else 0,
                    'tests': data['tests'][-10:] if len(data['tests']) > 10 else data['tests']  # Letzte 10 Tests
                }
            
            return {
                'timeframe': timeframe,
                'start_date': start_date.isoformat(),
                'models': result,
                'summary': {
                    'total_models': len(result),
                    'total_tests': sum(data['total_tests'] for data in result.values()),
                    'avg_success_rate': sum(data['success_rate'] for data in result.values()) / len(result) if result else 0
                }
            }
    
    async def get_model_comparison(
        self,
        model_ids: List[str],
        metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Vergleiche mehrere Modelle"""
        
        if not model_ids:
            raise ValueError("At least one model_id must be provided")
        
        if metrics is None:
            metrics = ['success_rate', 'avg_response_time_ms', 'avg_fields_found', 'consistency_score']
        
        with self.db.get_session() as session:
            # Hole Model Summary Daten
            summaries = session.query(ModelSummary).filter(
                ModelSummary.model_id.in_(model_ids)
            ).all()
            
            # Hole Field Consistency Daten
            consistencies = session.query(FieldConsistency).filter(
                FieldConsistency.model_id.in_(model_ids)
            ).all()
            
            result = {}
            for summary in summaries:
                # Berechne durchschnittliche Konsistenz
                model_consistencies = [
                    c.consistency_score for c in consistencies 
                    if c.model_id == summary.model_id
                ]
                avg_consistency = sum(model_consistencies) / len(model_consistencies) if model_consistencies else 0
                
                result[summary.model_id] = {
                    'model_id': summary.model_id,
                    'success_rate': summary.success_rate,
                    'data_success_rate': summary.data_success_rate,
                    'avg_response_time_ms': summary.avg_response_time_ms,
                    'avg_fields_found': summary.avg_fields_found,
                    'avg_sources_count': summary.avg_sources_count,
                    'consistency_score': avg_consistency,
                    'total_tests': summary.total_tests,
                    'total_mines_tested': summary.total_mines_tested,
                    'estimated_cost_per_request': summary.estimated_cost_per_request,
                    'last_updated': summary.last_updated.isoformat()
                }
            
            return {
                'models': result,
                'comparison_matrix': self._generate_comparison_matrix(result, metrics),
                'rankings': self._generate_model_rankings(result, metrics)
            }
    
    def _generate_comparison_matrix(self, models: Dict[str, Any], metrics: List[str]) -> Dict[str, Any]:
        """Generiere Vergleichsmatrix für Chart.js"""
        labels = list(models.keys())
        datasets = []
        
        for metric in metrics:
            data = [models[model_id].get(metric, 0) for model_id in labels]
            datasets.append({
                'label': metric.replace('_', ' ').title(),
                'data': data,
                'backgroundColor': self._get_metric_color(metric)
            })
        
        return {
            'labels': labels,
            'datasets': datasets
        }
    
    def _generate_model_rankings(self, models: Dict[str, Any], metrics: List[str]) -> Dict[str, List[str]]:
        """Generiere Rankings für verschiedene Metriken"""
        rankings = {}
        
        for metric in metrics:
            # Sortiere Modelle nach Metrik (höher = besser für die meisten Metriken)
            reverse = True
            if metric in ['avg_response_time_ms', 'estimated_cost_per_request']:
                reverse = False  # Niedrigere Werte sind besser
            
            sorted_models = sorted(
                models.items(),
                key=lambda x: x[1].get(metric, 0),
                reverse=reverse
            )
            
            rankings[metric] = [model_id for model_id, _ in sorted_models]
        
        return rankings
    
    def _get_metric_color(self, metric: str) -> str:
        """Hole Farbe für Metrik-Visualisierung"""
        color_map = {
            'success_rate': '#4CAF50',
            'avg_response_time_ms': '#2196F3',
            'avg_fields_found': '#FF9800',
            'consistency_score': '#9C27B0',
            'avg_sources_count': '#F44336',
            'estimated_cost_per_request': '#795548'
        }
        return color_map.get(metric, '#607D8B')
    
    # =========================================
    # FIELD STATISTICS METHODS
    # =========================================
    
    async def get_field_coverage(
        self,
        field_names: Optional[List[str]] = None,
        models: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Hole Field Coverage Statistiken"""
        
        with self.db.get_session() as session:
            query = session.query(FieldStatistics)
            
            if field_names:
                query = query.filter(FieldStatistics.field_name.in_(field_names))
            
            if models:
                query = query.filter(FieldStatistics.model_id.in_(models))
            
            field_stats = query.all()
            
            # Gruppiere nach Field und Model
            coverage_matrix = {}
            field_summaries = {}
            
            for stat in field_stats:
                # Field Summary
                if stat.field_name not in field_summaries:
                    field_summaries[stat.field_name] = {
                        'field_name': stat.field_name,
                        'models': {},
                        'avg_success_rate': 0,
                        'best_model': None,
                        'worst_model': None,
                        'total_searches': 0
                    }
                
                field_summaries[stat.field_name]['models'][stat.model_id] = {
                    'success_rate': stat.success_rate,
                    'times_found': stat.times_found,
                    'times_empty': stat.times_empty,
                    'total_searches': stat.total_searches,
                    'excluded_count': getattr(stat, 'excluded_count', 0),
                    'conditional_logic_applied': getattr(stat, 'conditional_logic_applied', False)
                }
                
                field_summaries[stat.field_name]['total_searches'] += stat.total_searches
                
                # Coverage Matrix für Heatmap
                if stat.field_name not in coverage_matrix:
                    coverage_matrix[stat.field_name] = {}
                coverage_matrix[stat.field_name][stat.model_id] = stat.success_rate
            
            # Berechne Field Summaries
            for field_name, summary in field_summaries.items():
                model_success_rates = [
                    data['success_rate'] for data in summary['models'].values()
                ]
                
                if model_success_rates:
                    summary['avg_success_rate'] = sum(model_success_rates) / len(model_success_rates)
                    
                    # Beste und schlechteste Modelle
                    best_model = max(summary['models'].items(), key=lambda x: x[1]['success_rate'])
                    worst_model = min(summary['models'].items(), key=lambda x: x[1]['success_rate'])
                    
                    summary['best_model'] = {
                        'model_id': best_model[0],
                        'success_rate': best_model[1]['success_rate']
                    }
                    summary['worst_model'] = {
                        'model_id': worst_model[0],
                        'success_rate': worst_model[1]['success_rate']
                    }
            
            return {
                'field_summaries': field_summaries,
                'coverage_matrix': coverage_matrix,
                'heatmap_data': self._generate_heatmap_data(coverage_matrix)
            }
    
    def _generate_heatmap_data(self, coverage_matrix: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
        """Generiere Heatmap-Daten für Chart.js"""
        
        field_names = list(coverage_matrix.keys())
        model_names = set()
        for field_data in coverage_matrix.values():
            model_names.update(field_data.keys())
        model_names = sorted(list(model_names))
        
        # Generiere Matrix-Daten
        matrix_data = []
        for y, field_name in enumerate(field_names):
            for x, model_name in enumerate(model_names):
                coverage_rate = coverage_matrix[field_name].get(model_name, 0)
                matrix_data.append({
                    'x': x,
                    'y': y,
                    'v': coverage_rate,
                    'field_name': field_name,
                    'model_name': model_name
                })
        
        return {
            'data': matrix_data,
            'xLabels': model_names,
            'yLabels': field_names,
            'maxValue': 100  # Prozentsatz
        }
    
    # =========================================
    # DASHBOARD METHODS
    # =========================================
    
    async def get_dashboard_summary(self) -> Dict[str, Any]:
        """Hole Dashboard Summary Daten"""
        
        with self.db.get_session() as session:
            # Model Summaries
            model_summaries = session.query(ModelSummary).all()
            
            # Recent Search Results (letzte 24h)
            yesterday = datetime.now() - timedelta(days=1)
            recent_searches = session.query(SearchResult).filter(
                SearchResult.search_timestamp >= yesterday
            ).all()
            
            # Field Statistics
            field_stats = session.query(FieldStatistics).all()
            
            # Berechne Summary Metriken
            total_models = len(model_summaries)
            total_recent_searches = len(recent_searches)
            successful_recent_searches = len([s for s in recent_searches if s.success])
            
            avg_success_rate = sum(ms.success_rate for ms in model_summaries) / total_models if total_models > 0 else 0
            avg_response_time = sum(ms.avg_response_time_ms for ms in model_summaries) / total_models if total_models > 0 else 0
            
            # Top/Bottom Performers
            if model_summaries:
                best_model = max(model_summaries, key=lambda x: x.success_rate)
                worst_model = min(model_summaries, key=lambda x: x.success_rate)
            else:
                best_model = worst_model = None
            
            # Field Coverage Summary
            field_coverage_avg = sum(fs.success_rate for fs in field_stats) / len(field_stats) if field_stats else 0
            
            return {
                'summary_cards': {
                    'total_models': total_models,
                    'avg_success_rate': round(avg_success_rate * 100, 1),
                    'recent_searches': total_recent_searches,
                    'recent_success_rate': round(successful_recent_searches / total_recent_searches * 100, 1) if total_recent_searches > 0 else 0,
                    'avg_response_time': round(avg_response_time, 0),
                    'field_coverage_avg': round(field_coverage_avg * 100, 1)
                },
                'top_performers': {
                    'best_model': {
                        'model_id': best_model.model_id,
                        'success_rate': round(best_model.success_rate * 100, 1)
                    } if best_model else None,
                    'worst_model': {
                        'model_id': worst_model.model_id,
                        'success_rate': round(worst_model.success_rate * 100, 1)
                    } if worst_model else None
                },
                'recent_activity': {
                    'total_searches': total_recent_searches,
                    'successful_searches': successful_recent_searches,
                    'unique_mines': len(set(s.mine_name for s in recent_searches)),
                    'models_used': len(set(s.model_used for s in recent_searches))
                },
                'trends': await self._get_trend_data()
            }
    
    async def _get_trend_data(self) -> Dict[str, Any]:
        """Hole Trend-Daten für Dashboard Charts"""
        
        with self.db.get_session() as session:
            # Letzte 7 Tage Trend
            week_ago = datetime.now() - timedelta(days=7)
            
            recent_stats = session.query(ModelStatistics).filter(
                ModelStatistics.timestamp >= week_ago
            ).order_by(ModelStatistics.timestamp).all()
            
            # Gruppiere nach Tag
            daily_data = {}
            for stat in recent_stats:
                day = stat.timestamp.date()
                if day not in daily_data:
                    daily_data[day] = {
                        'total_tests': 0,
                        'successful_tests': 0,
                        'total_response_time': 0,
                        'successful_response_time_count': 0
                    }
                
                daily_data[day]['total_tests'] += 1
                if stat.success:
                    daily_data[day]['successful_tests'] += 1
                    if stat.response_time_ms:
                        daily_data[day]['total_response_time'] += stat.response_time_ms
                        daily_data[day]['successful_response_time_count'] += 1
            
            # Formatiere für Chart.js
            labels = []
            success_rates = []
            response_times = []
            
            for day in sorted(daily_data.keys()):
                data = daily_data[day]
                labels.append(day.strftime('%Y-%m-%d'))
                success_rates.append(
                    (data['successful_tests'] / data['total_tests'] * 100) if data['total_tests'] > 0 else 0
                )
                response_times.append(
                    (data['total_response_time'] / data['successful_response_time_count']) if data['successful_response_time_count'] > 0 else 0
                )
            
            return {
                'labels': labels,
                'success_rates': success_rates,
                'response_times': response_times
            }


# =========================================
# API ROUTE HANDLERS
# =========================================

def get_statistics_service() -> StatisticsService:
    """Dependency für StatisticsService"""
    from database.manager import DatabaseManager
    return StatisticsService(DatabaseManager())


@router.get("/dashboard/summary")
async def get_dashboard_summary(
    stats_service: StatisticsService = Depends(get_statistics_service)
):
    """Haupt-Dashboard Daten"""
    try:
        summary = await stats_service.get_dashboard_summary()
        return JSONResponse(content=summary)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard summary: {str(e)}")


@router.get("/models")
async def get_all_models_performance(
    timeframe: str = Query('30d', regex='^(1h|24h|7d|30d|90d|1y|all)$'),
    stats_service: StatisticsService = Depends(get_statistics_service)
):
    """Alle Modelle Performance-Übersicht"""
    try:
        performance = await stats_service.get_model_performance(timeframe=timeframe)
        return JSONResponse(content=performance)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get models performance: {str(e)}")


@router.get("/models/{model_id}")
async def get_model_performance(
    model_id: str,
    timeframe: str = Query('30d', regex='^(1h|24h|7d|30d|90d|1y|all)$'),
    stats_service: StatisticsService = Depends(get_statistics_service)
):
    """Detaillierte Model-Performance"""
    try:
        performance = await stats_service.get_model_performance(model_id=model_id, timeframe=timeframe)
        return JSONResponse(content=performance)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get model performance: {str(e)}")


@router.get("/models/comparison")
async def get_models_comparison(
    models: str = Query(..., description="Comma-separated list of model IDs"),
    metrics: Optional[str] = Query(None, description="Comma-separated list of metrics"),
    stats_service: StatisticsService = Depends(get_statistics_service)
):
    """Vergleiche mehrere Modelle"""
    try:
        model_ids = [m.strip() for m in models.split(',')]
        metric_list = [m.strip() for m in metrics.split(',')] if metrics else None
        
        comparison = await stats_service.get_model_comparison(model_ids=model_ids, metrics=metric_list)
        return JSONResponse(content=comparison)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compare models: {str(e)}")


@router.get("/fields")
async def get_field_coverage(
    fields: Optional[str] = Query(None, description="Comma-separated list of field names"),
    models: Optional[str] = Query(None, description="Comma-separated list of model IDs"),
    stats_service: StatisticsService = Depends(get_statistics_service)
):
    """Field Coverage Statistiken"""
    try:
        field_names = [f.strip() for f in fields.split(',')] if fields else None
        model_ids = [m.strip() for m in models.split(',')] if models else None
        
        coverage = await stats_service.get_field_coverage(field_names=field_names, models=model_ids)
        return JSONResponse(content=coverage)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get field coverage: {str(e)}")


@router.get("/fields/{field_name}")
async def get_field_details(
    field_name: str,
    models: Optional[str] = Query(None, description="Comma-separated list of model IDs"),
    stats_service: StatisticsService = Depends(get_statistics_service)
):
    """Detaillierte Field-Statistiken"""
    try:
        model_ids = [m.strip() for m in models.split(',')] if models else None
        
        coverage = await stats_service.get_field_coverage(field_names=[field_name], models=model_ids)
        
        if field_name not in coverage['field_summaries']:
            raise HTTPException(status_code=404, detail=f"Field '{field_name}' not found")
        
        return JSONResponse(content={
            'field_name': field_name,
            'details': coverage['field_summaries'][field_name],
            'coverage_by_model': coverage['coverage_matrix'].get(field_name, {})
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get field details: {str(e)}")


# =========================================
# EXPORT ENDPOINTS
# =========================================

@router.get("/export/csv")
async def export_statistics_csv(
    type: str = Query(..., regex='^(models|fields|searches)$'),
    stats_service: StatisticsService = Depends(get_statistics_service)
):
    """Export Statistiken als CSV"""
    try:
        # TODO: Implementiere CSV Export
        return JSONResponse(content={"message": "CSV export not yet implemented"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export CSV: {str(e)}")


@router.get("/health")
async def statistics_health_check():
    """Health Check für Statistics API"""
    return JSONResponse(content={
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "statistics-api",
        "version": "1.0"
    })