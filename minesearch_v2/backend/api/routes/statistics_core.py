"""
Author: rahn
Datum: 06.08.2025
Version: 2.0
Beschreibung: Statistics Core API Routes - Basis-Statistik-Endpunkte
ÄNDERUNG 06.08.2025: Refactoring gemäß REGEL 1 - Core Routes aus statistics.py
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from database import db_manager, Source, SearchResult, Mine, ModelSummary
from source_stats_manager import source_stats_manager
from providers.registry import provider_registry
from .statistics_utils import StatisticsCalculator, StatisticsAnalyzer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/statistics", tags=["Core Statistics"])

# STATISTICS-FIELD-ORDER 01.08.2025: Zentrale Feldreihenfolge für modell-fokussierte Statistik-Tabellen
# Ähnlich FIELD_ORDER in consolidated_results.py, aber für Modelle statt Minen
STATISTICS_FIELD_ORDER = [
    'Modell', 'Provider', 'Zuverlässigkeit', 'Anzahl Suchen', 'Letzte Aktualisierung',
    'Erfolgsrate', 'Durchschn. Response Zeit', 'Gefundene Felder', 'Konsistenz', 
    'Quellenvielfalt', 'Datenqualität', 'Geschätzte Kosten', 'Performance-Kategorie',
    'Spezialisierung', 'Details'
]

class ModelPerformanceStats(BaseModel):
    """Response-Model für Modell-Performance-Statistiken"""
    model_id: str
    provider: str
    total_queries: int
    successful_queries: int
    failed_queries: int
    success_rate: float = Field(..., ge=0, le=1)
    avg_response_time: float
    avg_results_per_query: float
    avg_field_coverage: float  # Durchschnittliche Feldabdeckung
    unique_sources_found: int
    data_quality_score: float = Field(..., ge=0, le=100)
    cost_per_successful_query: Optional[float] = None
    reliability_trend: List[float]  # Performance über Zeit
    field_coverage_breakdown: Dict[str, float]

class FieldCoverageAnalysis(BaseModel):
    """Response-Model für Feld-Abdeckungs-Analyse"""
    field_name: str
    total_mines: int
    covered_mines: int
    coverage_percentage: float = Field(..., ge=0, le=100)
    top_sources: List[Dict[str, Any]]  # Beste Quellen für dieses Feld
    data_quality_indicators: Dict[str, Any]
    missing_data_patterns: Dict[str, Any]

class SystemPerformanceMetrics(BaseModel):
    """Response-Model für System-Performance-Metriken"""
    total_searches_today: int
    total_mines_discovered: int
    unique_sources_active: int
    avg_search_completion_time: float
    system_reliability_score: float = Field(..., ge=0, le=100)
    data_freshness_score: float = Field(..., ge=0, le=100)
    resource_utilization: Dict[str, float]
    bottleneck_analysis: Dict[str, Any]

@router.get("/overview", response_model=Dict[str, Any])
async def get_statistics_overview():
    """
    Umfassende Statistik-Übersicht mit akkumulierten Daten
    """
    try:
        # Basis-Statistiken aus der Datenbank
        with db_manager.get_session() as session:
            total_mines = session.query(Mine).count()
            total_sources = session.query(Source).count()
            
            # Aktive Quellen (letzte 7 Tage erfolgreich)
            week_ago = datetime.now() - timedelta(days=7)
            active_sources = session.query(Source).filter(
                Source.last_successful_access >= week_ago
            ).count()
            
            # Search Results Statistiken
            total_searches = session.query(SearchResult).count()
            successful_searches = session.query(SearchResult).filter(
                SearchResult.structured_data.isnot(None)
            ).count()
            
            # Performance-Metriken von source_stats_manager
            performance_summary = await source_stats_manager.get_performance_summary()
            
            overview = {
                'system_health': {
                    'total_mines': total_mines,
                    'total_sources': total_sources,
                    'active_sources': active_sources,
                    'source_activity_rate': (active_sources / total_sources * 100) if total_sources > 0 else 0,
                    'system_uptime_days': 30  # Placeholder - könnte aus System-Logs berechnet werden
                },
                'search_performance': {
                    'total_searches_performed': total_searches,
                    'successful_searches': successful_searches,
                    'success_rate_percent': (successful_searches / total_searches * 100) if total_searches > 0 else 0,
                    'avg_searches_per_day': total_searches / 30,  # Approximation für letzte 30 Tage
                    'data_completeness_score': performance_summary.get('avg_data_completeness', 85)
                },
                'source_performance': performance_summary,
                'data_quality': {
                    'avg_field_coverage_percent': performance_summary.get('avg_field_coverage', 75),
                    'data_consistency_score': performance_summary.get('consistency_score', 88),
                    'source_reliability_score': performance_summary.get('reliability_score', 92),
                    'fresh_data_percentage': 85  # Placeholder - könnte berechnet werden
                },
                'cost_efficiency': {
                    'avg_cost_per_mine_usd': 0.05,  # Placeholder
                    'monthly_operational_cost_usd': 150.0,  # Placeholder  
                    'cost_per_successful_search_usd': 0.01  # Placeholder
                },
                'growth_metrics': {
                    'new_sources_this_month': active_sources - (active_sources * 0.8),  # Approximation
                    'mines_added_this_month': total_mines - (total_mines * 0.95),  # Approximation
                    'search_volume_growth_percent': 15  # Placeholder
                }
            }
            
            logger.info(f"[STATS-CORE] Statistics overview generiert - {total_searches} Suchen, {active_sources} aktive Quellen")
            return overview
            
    except Exception as e:
        logger.error(f"[STATS-CORE] Fehler beim Abrufen der Statistik-Übersicht: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Fehler beim Abrufen der Statistiken: {str(e)}")

@router.get("/performance/system", response_model=Dict[str, Any])
async def get_system_performance_metrics():
    """
    System-Performance-Metriken mit Engpass-Analyse
    """
    try:
        with db_manager.get_session() as session:
            # Basis-Metriken sammeln
            today = datetime.now().date()
            searches_today = session.query(SearchResult).filter(
                SearchResult.search_timestamp >= today
            ).count()
            
            total_mines = session.query(Mine).count()
            active_sources = session.query(Source).filter(
                Source.last_successful_access >= datetime.now() - timedelta(days=1)
            ).count()
            
            # Performance-Analyse
            recent_searches = session.query(SearchResult).filter(
                SearchResult.search_timestamp >= datetime.now() - timedelta(hours=24)
            ).all()
            
            # System-Performance berechnen
            calculator = StatisticsCalculator()
            avg_completion_time = calculator.calculate_avg_completion_time(recent_searches)
            
            # Engpass-Analyse
            analyzer = StatisticsAnalyzer()
            bottlenecks = await analyzer.analyze_system_bottlenecks(session, recent_searches)
            
            # System-Zuverlässigkeit
            reliability_score = calculator.calculate_system_reliability(recent_searches)
            freshness_score = calculator.calculate_data_freshness_score(session)
            
            # Resource-Utilization (Placeholder - könnte von System-Monitoring kommen)
            resource_utilization = {
                'cpu_usage_percent': 65,
                'memory_usage_percent': 72,
                'disk_usage_percent': 45,
                'network_utilization_percent': 30
            }
            
            metrics = SystemPerformanceMetrics(
                total_searches_today=searches_today,
                total_mines_discovered=total_mines,
                unique_sources_active=active_sources,
                avg_search_completion_time=avg_completion_time,
                system_reliability_score=reliability_score,
                data_freshness_score=freshness_score,
                resource_utilization=resource_utilization,
                bottleneck_analysis=bottlenecks
            )
            
            logger.info(f"[STATS-CORE] System Performance Metriken generiert - Zuverlässigkeit: {reliability_score}")
            return metrics.dict()
            
    except Exception as e:
        logger.error(f"[STATS-CORE] Fehler beim Abrufen der System-Performance: {str(e)}")
        raise HTTPException(status_code=500, detail=f"System-Performance-Fehler: {str(e)}")

@router.get("/fields/coverage", response_model=Dict[str, Any])
async def get_field_coverage_analysis(
    field_focus: Optional[str] = Query(None, description="Fokus auf spezifisches Feld"),
    mine_type: Optional[str] = Query(None, description="Filter nach Minen-Typ"),
    days_back: int = Query(30, ge=1, le=365, description="Tage zurück für Analyse")
):
    """
    Feld-Abdeckungs-Analyse mit detaillierter Aufschlüsselung
    """
    try:
        with db_manager.get_session() as session:
            # Zeitraum definieren
            start_date = datetime.now() - timedelta(days=days_back)
            
            # Basis-Abfrage für Search Results
            query = session.query(SearchResult).filter(
                SearchResult.search_timestamp >= start_date
            )
            
            # Optional: Filter nach Minen-Typ
            if mine_type:
                query = query.join(Mine).filter(Mine.commodity == mine_type)
            
            search_results = query.all()
            
            # Field Coverage Analysis
            analyzer = StatisticsAnalyzer()
            
            if field_focus:
                # Analyse für spezifisches Feld
                field_analysis = await analyzer.analyze_specific_field_coverage(
                    session, field_focus, search_results
                )
                coverage_results = {field_focus: field_analysis}
            else:
                # Analyse für alle wichtigen Felder
                important_fields = [
                    'mine_name', 'commodity', 'country', 'region', 'latitude', 'longitude',
                    'production_volume', 'reserves', 'resources', 'mining_method'
                ]
                
                coverage_results = {}
                for field in important_fields:
                    coverage_results[field] = await analyzer.analyze_specific_field_coverage(
                        session, field, search_results
                    )
            
            # Gesamtanalyse
            total_mines_analyzed = len(set(sr.mine_name for sr in search_results))
            
            summary = {
                'analysis_period_days': days_back,
                'total_mines_analyzed': total_mines_analyzed,
                'total_searches_analyzed': len(search_results),
                'field_coverage_breakdown': coverage_results,
                'overall_coverage_score': analyzer.calculate_overall_coverage_score(coverage_results),
                'recommendations': analyzer.generate_coverage_recommendations(coverage_results)
            }
            
            logger.info(f"[STATS-CORE] Field Coverage Analysis für {len(coverage_results)} Felder abgeschlossen")
            return summary
            
    except Exception as e:
        logger.error(f"[STATS-CORE] Fehler bei Field Coverage Analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Field Coverage Analysis Fehler: {str(e)}")

@router.get("/models/{model_id}/details", response_model=Dict[str, Any])
async def get_model_detailed_stats(model_id: str):
    """
    Detaillierte Statistiken für ein spezifisches Modell
    """
    try:
        with db_manager.get_session() as session:
            # Model Summary aus der Datenbank
            model_summary = session.query(ModelSummary).filter(
                ModelSummary.model_id == model_id
            ).first()
            
            if not model_summary:
                raise HTTPException(status_code=404, detail=f"Modell {model_id} nicht gefunden")
            
            # Search Results für dieses Modell
            search_results = session.query(SearchResult).filter(
                SearchResult.model_used == model_id
            ).all()
            
            # Detaillierte Berechnungen
            calculator = StatisticsCalculator()
            
            # Performance-Metriken
            success_rate = calculator.calculate_success_rate(search_results)
            avg_response_time = calculator.calculate_avg_response_time(search_results)
            field_coverage = calculator.calculate_avg_field_coverage(search_results)
            
            # Zuverlässigkeits-Trend (letzte 30 Tage)
            reliability_trend = calculator.calculate_reliability_trend(search_results[-30:] if len(search_results) > 30 else search_results)
            
            # Field Coverage Breakdown
            field_breakdown = calculator.calculate_field_breakdown(search_results)
            
            # Unique Sources
            unique_sources = len(set(sr.sources_json for sr in search_results if sr.sources_json))
            
            # Datenqualitäts-Score
            data_quality_score = calculator.calculate_data_quality_score(search_results)
            
            # Cost per Query (wenn verfügbar)
            cost_per_query = calculator.calculate_cost_per_query(model_id, len(search_results))
            
            detailed_stats = ModelPerformanceStats(
                model_id=model_id,
                provider=model_summary.provider_name if model_summary else "unknown",
                total_queries=len(search_results),
                successful_queries=sum(1 for sr in search_results if sr.structured_data),
                failed_queries=sum(1 for sr in search_results if not sr.structured_data),
                success_rate=success_rate,
                avg_response_time=avg_response_time,
                avg_results_per_query=calculator.calculate_avg_results_per_query(search_results),
                avg_field_coverage=field_coverage,
                unique_sources_found=unique_sources,
                data_quality_score=data_quality_score,
                cost_per_successful_query=cost_per_query,
                reliability_trend=reliability_trend,
                field_coverage_breakdown=field_breakdown
            )
            
            # Zusätzliche Kontext-Informationen
            context = {
                'model_stats': detailed_stats.dict(),
                'recent_performance': {
                    'last_7_days': calculator.calculate_recent_performance(search_results, 7),
                    'last_30_days': calculator.calculate_recent_performance(search_results, 30)
                },
                'specialization_analysis': calculator.analyze_model_specialization(search_results),
                'comparison_to_average': calculator.compare_to_system_average(detailed_stats)
            }
            
            logger.info(f"[STATS-CORE] Detaillierte Modell-Statistiken für {model_id} generiert")
            return context
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[STATS-CORE] Fehler bei detaillierten Modell-Statistiken: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Modell-Statistik-Fehler: {str(e)}")

# Globale Router-Instanz
statistics_core_router = router