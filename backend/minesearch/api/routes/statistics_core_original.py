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

from minesearch.database import (
    db_manager,
    Source,
    SearchResult,
    Mine,
    ModelSummary,
    ModelStatisticsComprehensive,
    ModelFieldConsistency,
)
from minesearch.source_stats_manager import source_stats_manager
from minesearch.providers.registry import provider_registry
from minesearch.api.routes.statistics_utils import StatisticsCalculator, StatisticsAnalyzer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/statistics", tags=["Core Statistics"])

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
                    'data_completeness_score': performance_summary.get("avg_data_completeness", 85)
                },
                'source_performance': performance_summary,
                'data_quality': {
                    'avg_field_coverage_percent': performance_summary.get("avg_field_coverage", 75),
                    'data_consistency_score': performance_summary.get("consistency_score", 88),
                    'source_reliability_score': performance_summary.get("reliability_score", 92),
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

            logger.info(f"[STATS-CORE] Statistics overview generiert - {total_searches} Suchen,
{active_sources} aktive Quellen")
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

@router.get("/models/overview", response_model=Dict[str, Any])
async def get_models_overview_table():
    """
    NEUE API: Modell-basierte Statistik-Übersicht für Tabellen-Darstellung
    Ersetzt die Mine-basierte Ansicht mit einer Modell-fokussierten Übersicht
    """
    try:
        with db_manager.get_session() as session:
            # Alle Search Results gruppiert nach Modellen
            search_results = session.query(SearchResult).all()

            if not search_results:
                return {
                    'success': True,
                    'models_overview': [],
                    'total_models': 0,
                    'summary': {
                        'message': 'Keine Suchresultate für Modell-Statistiken gefunden'
                    }
                }

            # Gruppiere nach Modellen
            models_data = {}
            for result in search_results:
                model_id = result.model_used
                if model_id not in models_data:
                    models_data[model_id] = []
                models_data[model_id].append(result)

            calculator = StatisticsCalculator()
            models_overview = []

            # Berechne Statistiken für jedes Modell
            for model_id, model_results in models_data.items():
                # Provider aus model_id extrahieren
                provider = model_id.split(':')[0] if ':' in model_id else model_id

                # Basis-Metriken
                total_searches = len(model_results)
                successful_searches = sum(1 for r in model_results if r.structured_data)
                success_rate = (successful_searches / total_searches * 100) if total_searches > 0 else 0

                # Erweiterte Metriken
                avg_fields_found = calculator.calculate_avg_field_coverage(model_results) * 8  #
Approximation: 8 wichtige Felder

                # NEUE: Konsistenz-Berechnung
                consistency_data = calculator.calculate_model_consistency(model_results, model_id)
                overall_consistency = consistency_data['overall_consistency']

                # NEUE: Meist gefundene Felder
                most_found_fields = calculator.identify_most_found_fields(model_results)
                top_3_fields = [field['field'] for field in most_found_fields['top_fields'][:3]]

                # Performance-Kategorie basierend auf Success Rate und Konsistenz
                performance_category = calculator._determine_performance_category(success_rate, overall_consistency)

                # Data Quality Score
                quality_score = calculator.calculate_data_quality_score(model_results)

                model_overview = {
                    'model_id': model_id,
                    'model_name': model_id.replace(':', ' - ').title(),  # Formatierte Anzeige
                    'provider': provider.title(),
                    'total_searches': total_searches,
                    'success_rate': round(success_rate, 1),
                    'avg_fields_found': round(avg_fields_found, 1),
                    'overall_consistency': round(overall_consistency, 1),
                    'consistency_grade': consistency_data['consistency_grade'],
                    'most_found_fields': top_3_fields,
                    'performance_category': performance_category,
                    'quality_score': round(quality_score, 1),
                    'last_used': max([r.search_timestamp for r in model_results if
r.search_timestamp]).isoformat() if any(r.search_timestamp for r in model_results) else None
                }

                models_overview.append(model_overview)

            # Sortiere nach Performance (Success Rate * Konsistenz)
            models_overview.sort(key=lambda x: (x['success_rate'] * x['overall_consistency']), reverse=True)

            # Summary-Statistiken
            summary = {
                'total_models_analyzed': len(models_overview),
                'avg_success_rate': round(sum([m['success_rate'] for m in models_overview]) / len(models_overview), 1),
                'avg_consistency': round(sum([m['overall_consistency'] for m in models_overview]) /
len(models_overview), 1),
                'best_performing_model': models_overview[0]['model_id'] if models_overview else None,
                'total_searches_analyzed': sum([m['total_searches'] for m in models_overview])
            }

            logger.info(f"[STATS-CORE] Models Overview Tabelle generiert - {len(models_overview)} Modelle analysiert")
            return {
                'success': True,
                'models_overview': models_overview,
                'total_models': len(models_overview),
                'summary': summary
            }

    except Exception as e:
        logger.error(f"[STATS-CORE] Fehler bei Models Overview: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Models Overview Fehler: {str(e)}")

@router.get("/models/{model_id}/details", response_model=Dict[str, Any])
async def get_model_detailed_stats(model_id: str):
    """
    ERWEITERTE MODELL-DETAILS: Detaillierte Statistiken für ein spezifisches Modell
    Jetzt mit Konsistenz-Analysen und Feld-spezifischen Metriken
    """
    try:
        with db_manager.get_session() as session:
            # Model Statistics aus der Datenbank (FIXED: Use ModelStatisticsComprehensive instead of ModelSummary)
            model_stats = session.query(ModelStatisticsComprehensive).filter(
                ModelStatisticsComprehensive.model_id == model_id
            ).first()

            if not model_stats:
                raise HTTPException(status_code=404, detail=f"Modell {model_id} nicht gefunden")

            # Search Results für dieses Modell
            search_results = session.query(SearchResult).filter(
                SearchResult.model_used == model_id
            ).all()

            # Detaillierte Berechnungen
            calculator = StatisticsCalculator()

            # Standardberechnung aus echten Suchergebnissen
            success_rate = calculator.calculate_success_rate(search_results)
            avg_response_time = calculator.calculate_avg_response_time(search_results)
            field_coverage = calculator.calculate_avg_field_coverage(search_results)
            consistency_analysis = calculator.calculate_model_consistency(search_results, model_id)
            most_found_fields = calculator.identify_most_found_fields(search_results)
            reliability_trend = calculator.calculate_reliability_trend(
                search_results[-30:] if len(search_results) > 30 else search_results
            )
            field_breakdown = calculator.calculate_field_breakdown(search_results)
            unique_sources = len(set(str(sr.sources) for sr in search_results if sr.sources))
            data_quality_score = calculator.calculate_data_quality_score(search_results)
            cost_per_query = calculator.calculate_cost_per_query(model_id, len(search_results))

            # Fallback-LOGIK: Wenn keine (oder offensichtlich leere) SearchResults verfügbar sind,
            # verwende die voraggregierten Werte aus ModelStatisticsComprehensive, damit die
            # Detailansicht realistische Zahlen anzeigt und nicht nur Nullen.
            if not search_results:
                # Mapping von Comprehensive -> Detailwerte
                total_searches_fallback = model_stats.total_searches or 0
                successful_searches_fallback = model_stats.successful_searches or 0
                success_rate = (model_stats.success_rate_percent or 0.0) / 100.0
                avg_response_time = (
                    model_stats.avg_response_time_ms
                    or model_stats.avg_search_duration_ms
                    or 0.0
                )
                field_coverage = (model_stats.completeness_score or 0.0) / 100.0
                unique_sources = model_stats.unique_sources_total or 0
                # Durchschnittliche Quellen pro Suche als Näherung für Ergebnisse/Suche
                avg_results_per_query_fallback = model_stats.avg_sources_per_search or 0.0

                # Datenqualität konservativ aus vorhandenen Scores mitteln
                data_quality_score = float(
                    (
                        (model_stats.completeness_score or 0.0)
                        + (model_stats.consistency_score or 0.0)
                        + (model_stats.source_diversity_score or 0.0)
                    )
                    / 3.0
                )
                # Konsistenzanalyse leer, wenn keine Rohdaten
                consistency_analysis = consistency_analysis or {
                    'overall_consistency': model_stats.consistency_score or 0.0,
                    'field_consistency': {},
                    'consistency_grade': model_stats.consistency_grade or 'Unbekannt',
                    'total_mine_comparisons': 0,
                    'total_field_comparisons': 0,
                }
                most_found_fields = most_found_fields or {'top_fields': [], 'field_success_rates': {}}
                reliability_trend = []
                field_breakdown = {}

            else:
                # Wenn es SearchResults gibt, verbleibt die Standardlogik oben. Für
                # die Berechnung "avg_results_per_query" nutzen wir die spezielle Utility-Funktion
                avg_results_per_query_fallback = None  # Nicht genutzt im Standardpfad

            # BUGFIX 07.08.2025: Provider aus model_id extrahieren da provider_name nicht existiert
            provider = model_id.split(':')[0] if ':' in model_id else "unknown"

            detailed_stats = ModelPerformanceStats(
                model_id=model_id,
                provider=provider,
                total_queries=(len(search_results) if search_results else total_searches_fallback),
                successful_queries=(
                    sum(1 for sr in search_results if sr.structured_data)
                    if search_results else successful_searches_fallback
                ),
                failed_queries=(
                    sum(1 for sr in search_results if not sr.structured_data)
                    if search_results else max(0, (total_searches_fallback - successful_searches_fallback))
                ),
                success_rate=success_rate,
                avg_response_time=avg_response_time,
                avg_results_per_query=(
                    calculator.calculate_avg_results_per_query(search_results)
                    if search_results else avg_results_per_query_fallback
                ),
                avg_field_coverage=field_coverage,
                unique_sources_found=unique_sources,
                data_quality_score=data_quality_score,
                cost_per_successful_query=cost_per_query,
                reliability_trend=reliability_trend,
                field_coverage_breakdown=field_breakdown
            )

            # ERWEITERTE Kontext-Informationen
            context = {
                'model_stats': detailed_stats.dict(),
                'consistency_analysis': consistency_analysis,  # NEU
                'most_found_fields_analysis': most_found_fields,  # NEU
                'recent_performance': {
                    'last_7_days': calculator.calculate_recent_performance(search_results, 7),
                    'last_30_days': calculator.calculate_recent_performance(search_results, 30)
                },
                'specialization_analysis': calculator.analyze_model_specialization(search_results),
                'comparison_to_average': calculator.compare_to_system_average(detailed_stats),
                'field_specific_performance': {  # NEU
                    field: {
                        'success_rate': data['success_rate'],
                        'avg_quality': data['avg_quality'],
                        'consistency': consistency_analysis['field_consistency'].get(field,
{}).get('consistency_percent', 0)
                    }
                    for field, data_dict in most_found_fields['field_success_rates'].items()
                }
            }

            logger.info(f"[STATS-CORE] Erweiterte Modell-Statistiken für {model_id} generiert")
            return context

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[STATS-CORE] Fehler bei detaillierten Modell-Statistiken: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Modell-Statistik-Fehler: {str(e)}")

@router.get("/models/comprehensive", response_model=Dict[str, Any])
async def get_models_comprehensive_statistics(
    sort_by: str = "overall_score",
    order: str = "desc",
    min_searches: int = 0,
    provider_filter: Optional[str] = None
):
    """
    NEUE HAUPTTABELLE: Umfassende Modell-Statistiken mit normiertem Gesamtscore
    Eine Zeile pro AI-Modell mit allen wichtigen Performance-Kennzahlen
    """
    try:
        logger.info(f"[STATS-CORE] Starting comprehensive statistics with sort_by={sort_by}, order={order}")
        with db_manager.get_session() as session:
            # Hole alle Modell-Statistiken
            logger.info("[STATS-CORE] Creating query for ModelStatisticsComprehensive")
            query = session.query(ModelStatisticsComprehensive)

            # Filter anwenden
            if min_searches > 0:
                query = query.filter(ModelStatisticsComprehensive.total_searches >= min_searches)

            if provider_filter:
                # Provider aus model_id extrahieren
                query = query.filter(ModelStatisticsComprehensive.model_id.like(f"{provider_filter}:%"))

            # Sortierung anwenden
            reverse_order = (order == "desc")

            if sort_by == "overall_score":
                if reverse_order:
                    query = query.order_by(ModelStatisticsComprehensive.overall_score.desc())
                else:
                    query = query.order_by(ModelStatisticsComprehensive.overall_score.asc())
            elif sort_by == "consistency_score":
                if reverse_order:
                    query = query.order_by(ModelStatisticsComprehensive.consistency_score.desc())
                else:
                    query = query.order_by(ModelStatisticsComprehensive.consistency_score.asc())
            elif sort_by == "completeness_score":
                if reverse_order:
                    query = query.order_by(ModelStatisticsComprehensive.completeness_score.desc())
                else:
                    query = query.order_by(ModelStatisticsComprehensive.completeness_score.asc())
            else:  # model_id
                if reverse_order:
                    query = query.order_by(ModelStatisticsComprehensive.model_id.desc())
                else:
                    query = query.order_by(ModelStatisticsComprehensive.model_id.asc())

            logger.info("[STATS-CORE] Executing query to get model statistics")
            model_stats = query.all()
            logger.info(f"[STATS-CORE] Found {len(model_stats)} model statistics from database")

            # Falls keine Daten vorhanden, aus SearchResults generieren
            if not model_stats:
                logger.info("[STATS-CORE] Keine comprehensive statistics vorhanden, generiere aus SearchResults...")
                await update_comprehensive_statistics()
                model_stats = query.all()
                logger.info(f"[STATS-CORE] After update: {len(model_stats)} model statistics")

            # CRITICAL FIX 19.08.2025: Hole alle verfügbaren Modelle aus Models API
            import httpx
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    models_response = await client.get("http://localhost:8000/api/models")
                    models_api_data = models_response.json()
            except Exception as e:
                logger.warning(f"[STATS-CORE] Could not fetch models from API: {e}")
                models_api_data = {'success': False}

            if models_api_data.get('success') and 'models' in models_api_data:
                all_available_models = []
                for model in models_api_data['models']:
                    if isinstance(model, dict):
                        model_id = model.get("model_id", str(model))
                    else:
                        model_id = str(model)
                    all_available_models.append(model_id)
            else:
                all_available_models = []

            tested_model_ids = {stat.model_id for stat in model_stats}

            logger.info(f"[STATS-CORE] Found {len(model_stats)} tested models,
{len(all_available_models)} total available")

            # Konvertiere getestete Modelle zu API-Response
            logger.info("[STATS-CORE] Converting model statistics to dict format")
            models_data = []
            for i, model in enumerate(model_stats):
                try:
                    model_dict = model.to_dict()
                    models_data.append(model_dict)
                    if i < 3:  # Debug first 3 models
                        logger.info(f"[STATS-CORE] Model {i}: {model_dict.get('model_id')} - keys:
{list(model_dict.keys())}")
                except Exception as model_error:
                    logger.error(f"[STATS-CORE] Error converting model {i}: {model_error}")
                    raise

            # ÄNDERUNG 23.08.2025: Nur Modelle mit tatsächlichen Daten zeigen (Nutzer-Request: Saubere Datenbank)
            # DEAKTIVIERT: Zeige nicht alle verfügbaren Modelle wenn keine Daten vorhanden
            # Grund: Bei leerer Datenbank sollen auch die Statistics leer sein
            logger.info(f"[STATS-CORE] Showing only tested models ({len(models_data)}) - untested
models hidden for clean database state")

            # LEGACY CODE (deaktiviert): Ungetestete Modelle hinzufügen
            # for model_id in all_available_models:
            #     if model_id not in tested_model_ids:
            #         provider = model_id.split(':')[0] if ':' in model_id else 'unknown'
            #         models_data.append({
            #             'model_id': model_id,
            #             'provider': provider,
            #             'overall_score': 0.0,
            #             'completeness_score': 0.0,
            #             'consistency_score': 0.0,
            #             'total_searches': 0,
            #             'successful_searches': 0,
            #             'score_category': 'Nicht getestet',
            #             'consistency_grade': 'N/A',
            #             'last_updated': None,
            #             'avg_search_duration_ms': 0,
            #             'unique_sources_total': 0,
            #             'note': 'Noch nicht in Batch-Suchen verwendet'
            #         })

            # Sortiere: Getestete Modelle zuerst (nach Score), dann verfügbare (alphabetisch)
            try:
                models_data.sort(key=lambda x: (
                    x.get('score_category') == 'Nicht getestet',  # FIXED: Nicht getestete nach hinten
                    -x.get("overall_score", 0),  # BUGFIX: Use get() to prevent KeyError
                    x.get("model_id", '')  # BUGFIX: Use get() to prevent KeyError
                ))
                logger.info(f"[STATS-CORE] Successfully sorted {len(models_data)} models")
            except Exception as sort_error:
                logger.error(f"[STATS-CORE] Sort error: {sort_error}")
                # Debug first few models to identify issue
                for i, model in enumerate(models_data[:3]):
                    logger.info(f"[STATS-CORE] Model {i}: {model.keys()} - score_category:
{model.get('score_category')} - overall_score: {model.get('overall_score')} - model_id:
{model.get('model_id')}")
                raise

            logger.info(f"[STATS-CORE] Showing ALL {len(models_data)} models ({len(model_stats)}
tested + {len(all_available_models) - len(tested_model_ids)} available)")

            # Summary-Statistiken für alle Modelle
            tested_models = [m for m in models_data if m.get("score_category", 'Nicht getestet') != 'Nicht getestet']
            available_models = [m for m in models_data if m.get("score_category", 'Nicht getestet') == 'Nicht getestet']

            if models_data:
                summary_stats = {
                    'total_models': len(models_data),
                    'tested_models': len(tested_models),
                    'available_untested_models': len(available_models),
                    # Durchschnitte nur von getesteten Modellen berechnen
                    'avg_overall_score': round(sum([m['overall_score'] for m in tested_models]) /
len(tested_models), 1) if tested_models else 0,
                    'avg_completeness': round(sum([m['completeness_score'] for m in tested_models])
/ len(tested_models), 1) if tested_models else 0,
                    'avg_consistency': round(sum([m['consistency_score'] for m in tested_models]) /
len(tested_models), 1) if tested_models else 0,
                    'best_model': max(tested_models, key=lambda x: x['overall_score'])['model_id']
if tested_models else None,
                    'score_distribution': {
                        'exzellent': len([m for m in tested_models if m.get('score_category') == 'Exzellent']),
                        'sehr_gut': len([m for m in tested_models if m.get('score_category') == 'Sehr Gut']),
                        'gut': len([m for m in tested_models if m.get('score_category') == 'Gut']),
                        'limitiert': len([m for m in tested_models if m.get('score_category') == 'Limitiert']),
                        'ungeeignet': len([m for m in tested_models if m.get('score_category') == 'Ungeeignet']),
                        'nicht_getestet': len(available_models)
                    },
                    'model_status_info': {
                        'tested_note': f"{len(tested_models)} Modelle wurden bereits in Batch-Suchen getestet",
                        'available_note': f"{len(available_models)} Modelle sind verfügbar aber noch nicht getestet"
                    }
                }
            else:
                summary_stats = {
                    'total_models': 0,
                    'message': 'Keine Modell-Statistiken verfügbar'
                }

            logger.info(f"[STATS-CORE] Comprehensive model statistics generiert - {len(models_data)} Modelle")
            return {
                'success': True,
                'data': {
                    'models': models_data,
                    'summary': summary_stats,
                    'sort_by': sort_by,
                    'order': order,
                    'filters_applied': {
                        'min_searches': min_searches,
                        'provider_filter': provider_filter
                    }
                }
            }

    except Exception as e:
        logger.error(f"[STATS-CORE] Fehler bei comprehensive model statistics: {str(e)}")
        import traceback
        logger.error(f"[STATS-CORE] Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Comprehensive statistics Fehler: {str(e)}")

@router.get("/models/{model_id}/field-consistency", response_model=Dict[str, Any])
async def get_model_field_consistency(model_id: str):
    """
    NEUE DETAILANSICHT: Feld-spezifische Konsistenz-Analysen für ein Modell
    Zeigt wie konsistent das Modell bei jedem einzelnen Feld ist
    """
    try:
        with db_manager.get_session() as session:
            # Hole Feld-Konsistenz-Daten für dieses Modell
            field_consistencies = session.query(ModelFieldConsistency).filter(
                ModelFieldConsistency.model_id == model_id
            ).all()

            if not field_consistencies:
                # Generiere Konsistenz-Daten aus SearchResults
                logger.info(f"[STATS-CORE] Generiere Feld-Konsistenz für Modell {model_id}...")
                await update_field_consistency_for_model(model_id)
                field_consistencies = session.query(ModelFieldConsistency).filter(
                    ModelFieldConsistency.model_id == model_id
                ).all()

            if not field_consistencies:
                raise HTTPException(status_code=404, detail=f"Keine Feld-Konsistenz-Daten für Modell
{model_id} gefunden")

            # Gruppiere nach Feld-Kategorien
            field_categories = {
                'Grunddaten': ['Mine', 'Land', 'Region', 'Rohstoffe', 'Aktivitätsstatus'],
                'Koordinaten': ['x-Koordinate', 'y-Koordinate', 'Minenfläche in qkm'],
                'Betriebsdaten': ['Betreiber', 'Eigentümer', 'Minentyp', 'Produktionsstart', 'Produktionsende'],
                'Produktionsdaten': ['Fördermenge/Jahr', 'Rohstoffe'],
                'Finanzdaten': ['Restaurationskosten', 'Kostenjahr', 'Dokumentenjahr']
            }

            # Konvertiere zu API-Response und gruppiere
            categorized_fields = {}
            uncategorized_fields = []

            for field_consistency in field_consistencies:
                field_data = field_consistency.to_dict()

                # Finde passende Kategorie
                found_category = None
                for category, field_names in field_categories.items():
                    if field_consistency.field_name in field_names:
                        found_category = category
                        break

                if found_category:
                    if found_category not in categorized_fields:
                        categorized_fields[found_category] = []
                    categorized_fields[found_category].append(field_data)
                else:
                    uncategorized_fields.append(field_data)

            # Berechne Kategorie-Scores
            category_scores = {}
            for category, fields in categorized_fields.items():
                if fields:
                    avg_score = sum([f['field_consistency_score'] for f in fields]) / len(fields)
                    category_scores[category] = {
                        'avg_consistency': round(avg_score, 1),
                        'field_count': len(fields),
                        'best_field': max(fields, key=lambda x: x['field_consistency_score'])['field_name'],
                        'worst_field': min(fields, key=lambda x: x['field_consistency_score'])['field_name']
                    }

            # Overall Model Field Performance
            all_fields = field_consistencies
            overall_consistency = sum([f.field_consistency_score for f in all_fields]) /
len(all_fields) if all_fields else 0

            response = {
                'success': True,
                'model_id': model_id,
                'data': {
                    'overall_field_consistency': round(overall_consistency, 1),
                    'total_fields_analyzed': len(all_fields),
                    'categorized_fields': categorized_fields,
                    'uncategorized_fields': uncategorized_fields,
                    'category_performance': category_scores,
                    'consistency_insights': {
                        'most_consistent_field': max(all_fields, key=lambda x:
x.field_consistency_score).field_name if all_fields else None,
                        'least_consistent_field': min(all_fields, key=lambda x:
x.field_consistency_score).field_name if all_fields else None,
                        'fields_with_high_consistency': len([f for f in all_fields if f.field_consistency_score >= 80]),
                        'fields_needing_improvement': len([f for f in all_fields if f.field_consistency_score < 50])
                    }
                }
            }

            logger.info(f"[STATS-CORE] Feld-Konsistenz für Modell {model_id} generiert - {len(all_fields)} Felder")
            return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[STATS-CORE] Fehler bei Feld-Konsistenz für {model_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Feld-Konsistenz-Fehler: {str(e)}")

@router.post("/models/update-comprehensive")
async def update_comprehensive_statistics():
    """
    UTILITY ENDPOINT: Aktualisiere umfassende Modell-Statistiken aus SearchResults
    Berechnet alle Scores und Metriken neu
    """
    try:
        with db_manager.get_session() as session:
            # Hole alle SearchResults gruppiert nach Modellen
            search_results = session.query(SearchResult).all()

            if not search_results:
                return {
                    'success': True,
                    'message': 'Keine SearchResults zum Verarbeiten gefunden',
                    'updated_models': 0
                }

            # Gruppiere nach Modellen
            models_data = {}
            for result in search_results:
                model_id = result.model_used
                if model_id not in models_data:
                    models_data[model_id] = []
                models_data[model_id].append(result)

            updated_count = 0

            # Erstelle oder aktualisiere ModelStatisticsComprehensive für jedes Modell
            for model_id, model_results in models_data.items():
                # Suche existierende Statistik oder erstelle neue
                model_stats = session.query(ModelStatisticsComprehensive).filter(
                    ModelStatisticsComprehensive.model_id == model_id
                ).first()

                if not model_stats:
                    model_stats = ModelStatisticsComprehensive(model_id=model_id)
                    session.add(model_stats)

                # Aktualisiere alle Statistiken
                model_stats.update_from_search_results(model_results)

                # Konsistenz-Score separat berechnen (komplexere Logik)
                consistency_score = await calculate_model_consistency_score(model_results, model_id)
                model_stats.consistency_score = consistency_score

                # Konsistenz-Grade zuweisen
                if consistency_score >= 90:
                    model_stats.consistency_grade = 'A'
                elif consistency_score >= 80:
                    model_stats.consistency_grade = 'B'
                elif consistency_score >= 70:
                    model_stats.consistency_grade = 'C'
                elif consistency_score >= 60:
                    model_stats.consistency_grade = 'D'
                else:
                    model_stats.consistency_grade = 'F'

                updated_count += 1

            # Speichere alle Änderungen
            session.commit()

            logger.info(f"[STATS-CORE] Comprehensive statistics updated - {updated_count} Modelle")
            return {
                'success': True,
                'message': f'Comprehensive statistics für {updated_count} Modelle aktualisiert',
                'updated_models': updated_count,
                'total_search_results_processed': len(search_results)
            }

    except Exception as e:
        logger.error(f"[STATS-CORE] Fehler beim Update der comprehensive statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Update-Fehler: {str(e)}")

async def calculate_model_consistency_score(search_results: List[SearchResult], model_id: str) -> float:
    """
    Hilfsfunktion: Berechne Konsistenz-Score für ein Modell über alle Felder
    CRITICAL-FIX 19.08.2025: Repariere Division-by-Zero und bessere Konsistenz-Logik
    """
    if not search_results:
        return 0.0

    field_values = {}  # field_name -> [value1, value2, ...]

    # Sammle alle Feldwerte - jetzt mit besserer Filterung
    for result in search_results:
        if result.structured_data:
            for field_name, field_value in result.structured_data.items():
                # Verbesserte Validierung: echte Werte sammeln, keine Template-Placeholder
                if (field_value and
                    str(field_value).strip() and
                    str(field_value).strip() not in ['X', 'nichts gefunden', 'k.A.', 'N/A', 'unknown']):

                    if field_name not in field_values:
                        field_values[field_name] = []
                    field_values[field_name].append(str(field_value).strip())

    if not field_values:
        return 0.0  # Keine validen Daten gefunden

    # Berechne Konsistenz pro Feld
    field_consistencies = []
    for field_name, values in field_values.items():
        if len(values) >= 1:  # FIXED: Auch einzelne Werte sind "konsistent"
            if len(values) == 1:
                # Einzelne Werte sind perfekt konsistent
                field_consistencies.append(100.0)
            else:
                # Multiple Werte: berechne Konsistenz
                unique_values = set(values)
                if unique_values:  # Sicherheitsprüfung
                    value_counts = [values.count(val) for value in unique_values]
                    if value_counts:  # Weitere Sicherheitsprüfung
                        most_common_count = max(value_counts)
                        consistency = (most_common_count / len(values)) * 100
                        field_consistencies.append(consistency)

    # Overall Konsistenz-Score
    if field_consistencies:
        avg_consistency = sum(field_consistencies) / len(field_consistencies)
        logger.debug(f"[STATS-CORE] Model {model_id} consistency: {avg_consistency:.1f}% across
{len(field_consistencies)} fields")
        return avg_consistency
    else:
        logger.debug(f"[STATS-CORE] Model {model_id} has no valid data_dict for consistency calculation")
        return 0.0

async def update_field_consistency_for_model(model_id: str):
    """
    Hilfsfunktion: Aktualisiere Feld-Konsistenz-Daten für ein spezifisches Modell
    """
    with db_manager.get_session() as session:
        # Hole SearchResults für dieses Modell
        search_results = session.query(SearchResult).filter(
            SearchResult.model_used == model_id
        ).all()

        if not search_results:
            return

        # Sammle Feldwerte
        field_values = {}
        for result in search_results:
            if result.structured_data:
                for field_name, field_value in result.structured_data.items():
                    if field_name not in field_values:
                        field_values[field_name] = []
                    if field_value and str(field_value).strip():
                        field_values[field_name].append(str(field_value).strip())

        # Erstelle oder aktualisiere ModelFieldConsistency für jedes Feld
        for field_name, values in field_values.items():
            if not values:
                continue

            # Suche existierende oder erstelle neue
            field_consistency = session.query(ModelFieldConsistency).filter(
                ModelFieldConsistency.model_id == model_id,
                ModelFieldConsistency.field_name == field_name
            ).first()

            if not field_consistency:
                field_consistency = ModelFieldConsistency(
                    model_id=model_id,
                    field_name=field_name
                )
                session.add(field_consistency)

            # Aktualisiere mit neuen Daten
            field_consistency.update_from_field_data(values)
            field_consistency.total_searches = len(search_results)

        session.commit()

# Globale Router-Instanz
statistics_core_router = router
