"""
Author: rahn
Datum: 06.08.2025
Version: 1.0
Beschreibung: Statistics Advanced API Routes - Erweiterte Statistik-Endpunkte
ÄNDERUNG 06.08.2025: Refactoring gemäß REGEL 1 - Advanced Routes aus statistics.py
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query

from minesearch.database import db_manager, SearchResult, ModelSummary
# from minesearch.source_stats_manager import source_stats_manager  # DISABLED: Module nicht vorhanden
from minesearch.api.routes.statistics_utils import StatisticsCalculator, StatisticsAnalyzer, StatisticsTimeAnalyzer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/statistics", tags=["Advanced Statistics"])

@router.get("/models/performance", response_model=Dict[str, Any])
async def get_model_performance_stats(
    model_filter: Optional[str] = Query(None, description="Filter nach Modell-ID oder Provider"),
    days_back: int = Query(30, ge=1, le=365, description="Tage zurück für Performance-Analyse"),
    include_cost_analysis: bool = Query(False, description="Kosten-Analyse einschließen"),
    sort_by: str = Query("success_rate", description="Sortierung: success_rate, response_time, field_coverage")
):
    """
    Erweiterte Modell-Performance-Statistiken mit Vergleichsanalyse
    """
    try:
        with db_manager.get_session() as session:
            # Zeitraum definieren
            start_date = datetime.now() - timedelta(days=days_back)

            # Basis-Abfrage
            query = session.query(SearchResult).filter(
                SearchResult.search_timestamp >= start_date
            )

            # Optional: Modell-Filter
            if model_filter:
                query = query.filter(SearchResult.model_used.contains(model_filter))

            search_results = query.all()

            # Gruppiere nach Modellen
            models_data = {}
            for result in search_results:
                model_id = result.model_used
                if model_id not in models_data:
                    models_data[model_id] = []
                models_data[model_id].append(result)

            # Berechne Performance-Statistiken für jedes Modell
            calculator = StatisticsCalculator()
            performance_stats = {}

            for model_id, model_results in models_data.items():
                # Basis-Metriken
                total_queries = len(model_results)
                successful_queries = sum(1 for r in model_results if r.structured_data)
                failed_queries = total_queries - successful_queries
                success_rate = successful_queries / total_queries if total_queries > 0 else 0

                # Erweiterte Metriken
                avg_response_time = calculator.calculate_avg_response_time(model_results)
                field_coverage = calculator.calculate_avg_field_coverage(model_results)
                data_quality = calculator.calculate_data_quality_score(model_results)
                unique_sources = len(set(r.sources_json for r in model_results if r.sources_json))

                # Zuverlässigkeits-Trend
                reliability_trend = calculator.calculate_reliability_trend(model_results)

                # Field Coverage Breakdown
                field_breakdown = calculator.calculate_field_breakdown(model_results)

                # Provider-Information
                model_summary = session.query(ModelSummary).filter(
                    ModelSummary.model_id == model_id
                ).first()
                provider = model_summary.provider_name if model_summary else "unknown"

                # Kosten-Analyse (optional)
                cost_per_query = None
                if include_cost_analysis:
                    cost_per_query = calculator.calculate_cost_per_query(model_id, successful_queries)

                performance_stats[model_id] = {
                    'model_id': model_id,
                    'provider': provider,
                    'performance_metrics': {
                        'total_queries': total_queries,
                        'successful_queries': successful_queries,
                        'failed_queries': failed_queries,
                        'success_rate': success_rate,
                        'avg_response_time_ms': avg_response_time,
                        'avg_field_coverage_percent': field_coverage * 100,
                        'data_quality_score': data_quality,
                        'unique_sources_found': unique_sources
                    },
                    'advanced_metrics': {
                        'reliability_trend': reliability_trend,
                        'field_coverage_breakdown': field_breakdown,
                        'cost_per_successful_query': cost_per_query,
                        'specialization_score': calculator.analyze_model_specialization(model_results)
                    }
                }

            # Sortiere Ergebnisse
            sort_key_map = {
                'success_rate': lambda x: x[1]['performance_metrics']['success_rate'],
                'response_time': lambda x: -x[1]['performance_metrics']['avg_response_time_ms'],  # Niedrigere Zeit = besser
                'field_coverage': lambda x: x[1]['performance_metrics']['avg_field_coverage_percent']
            }

            if sort_by in sort_key_map:
                sorted_models = sorted(performance_stats.items(), key=sort_key_map[sort_by], reverse=True)
                performance_stats = dict(sorted_models)

            # Gesamtanalyse
            analyzer = StatisticsAnalyzer()
            system_averages = analyzer.calculate_system_averages(performance_stats)

            response = {
                'analysis_period_days': days_back,
                'total_models_analyzed': len(performance_stats),
                'models_performance': performance_stats,
                'system_averages': system_averages,
                'performance_rankings': analyzer.generate_performance_rankings(performance_stats),
                'recommendations': analyzer.generate_model_recommendations(performance_stats)
            }

            logger.info(f"[STATS-ADVANCED] Model Performance Stats für {len(performance_stats)} Modelle generiert")
            return response

    except Exception as e:
        logger.error(f"[STATS-ADVANCED] Fehler bei Model Performance Stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Model Performance Fehler: {str(e)}")

@router.get("/trends/historical", response_model=Dict[str, Any])
async def get_historical_trends(
    days_back: int = Query(90, ge=7, le=365, description="Tage zurück für Trend-Analyse"),
    granularity: str = Query("daily", description="Granularität: hourly, daily, weekly"),
    metrics: Optional[str] = Query("all", description="Metriken: all, searches, success_rate, response_time")
):
    """
    Historische Trend-Analyse mit konfigurierbarer Granularität
    """
    try:
        with db_manager.get_session() as session:
            # Zeitraum und Granularität
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)

            # Search Results für den Zeitraum
            search_results = session.query(SearchResult).filter(
                SearchResult.search_timestamp >= start_date,
                SearchResult.search_timestamp <= end_date
            ).order_by(SearchResult.search_timestamp).all()

            # Time-basierte Analyse
            time_analyzer = StatisticsTimeAnalyzer()

            # Erstelle Zeit-Buckets
            time_buckets = time_analyzer.create_time_buckets(start_date, granularity, days_back)

            # Gruppiere Results nach Zeit-Buckets
            for result in search_results:
                bucket_key = time_analyzer.get_bucket_key(result.search_timestamp, granularity)
                if bucket_key in time_buckets:
                    time_buckets[bucket_key]['results'].append(result)

            # Berechne Metriken für jeden Zeit-Bucket
            calculator = StatisticsCalculator()
            trend_data = {}

            for bucket_key, bucket_data in time_buckets.items():
                bucket_results = bucket_data['results']

                if metrics == "all" or "searches" in metrics:
                    trend_data.setdefault('search_volume', {})[bucket_key] = len(bucket_results)

                if metrics == "all" or "success_rate" in metrics:
                    success_rate = calculator.calculate_success_rate(bucket_results)
                    trend_data.setdefault('success_rate', {})[bucket_key] = success_rate * 100

                if metrics == "all" or "response_time" in metrics:
                    avg_response = calculator.calculate_avg_response_time(bucket_results)
                    trend_data.setdefault('avg_response_time_ms', {})[bucket_key] = avg_response

                if metrics == "all":
                    field_coverage = calculator.calculate_avg_field_coverage(bucket_results)
                    trend_data.setdefault('field_coverage_percent', {})[bucket_key] = field_coverage * 100

                    data_quality = calculator.calculate_data_quality_score(bucket_results)
                    trend_data.setdefault('data_quality_score', {})[bucket_key] = data_quality

            # Trend-Analyse (Steigung, Saisonalität, etc.)
            trend_analysis = {}
            for metric_name, metric_data in trend_data.items():
                trend_analysis[metric_name] = time_analyzer.analyze_trend(metric_data)

            # Anomalie-Erkennung
            anomalies = time_analyzer.detect_anomalies(trend_data)

            # Prognose für nächste Periode
            forecasts = time_analyzer.generate_forecasts(trend_data, granularity)

            response = {
                'analysis_period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days_analyzed': days_back,
                    'granularity': granularity
                },
                'trend_data': trend_data,
                'trend_analysis': trend_analysis,
                'anomalies_detected': anomalies,
                'forecasts': forecasts,
                'summary': {
                    'total_data_points': len(time_buckets),
                    'avg_searches_per_period': sum(trend_data.get("search_volume", {}).values()) / len(time_buckets),
                    'overall_trend': time_analyzer.get_overall_trend_direction(trend_data)
                }
            }

            logger.info(f"[STATS-ADVANCED] Historical Trends für {days_back} Tage generiert ({granularity})")
            return response

    except Exception as e:
        logger.error(f"[STATS-ADVANCED] Fehler bei Historical Trends: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Historical Trends Fehler: {str(e)}")

@router.get("/quality/analysis", response_model=Dict[str, Any])
async def get_data_quality_analysis(
    quality_threshold: float = Query(0.8, ge=0.0, le=1.0, description="Qualitäts-Schwellenwert"),
    days_back: int = Query(30, ge=1, le=365, description="Analysezeitraum in Tagen"),
    include_source_analysis: bool = Query(True, description="Quellen-Qualitätsanalyse einschließen")
):
    """
    Umfassende Datenqualitäts-Analyse
    """
    try:
        with db_manager.get_session() as session:
            # Zeitraum definieren
            start_date = datetime.now() - timedelta(days=days_back)

            search_results = session.query(SearchResult).filter(
                SearchResult.search_timestamp >= start_date
            ).all()

            # Qualitäts-Analysator
            analyzer = StatisticsAnalyzer()

            # Overall Quality Metrics
            overall_quality = analyzer.analyze_overall_data_quality(search_results, quality_threshold)

            # Field-spezifische Qualitäts-Analyse
            field_quality = analyzer.analyze_field_quality(search_results)

            # Model-spezifische Qualitäts-Analyse
            model_quality = analyzer.analyze_model_quality(search_results, quality_threshold)

            # Source Quality Analysis (optional)
            source_quality = {}
            if include_source_analysis:
                source_quality = await analyzer.analyze_source_quality(session, search_results)

            # Qualitäts-Trends über Zeit
            quality_trends = analyzer.analyze_quality_trends(search_results, days_back)

            # Problembereiche identifizieren
            quality_issues = analyzer.identify_quality_issues(
                overall_quality, field_quality, model_quality, quality_threshold
            )

            # Verbesserungsempfehlungen
            recommendations = analyzer.generate_quality_recommendations(quality_issues)

            response = {
                'analysis_summary': {
                    'analysis_period_days': days_back,
                    'quality_threshold': quality_threshold,
                    'total_records_analyzed': len(search_results),
                    'overall_quality_score': overall_quality['overall_score'],
                    'quality_grade': analyzer.get_quality_grade(overall_quality['overall_score'])
                },
                'detailed_analysis': {
                    'overall_quality_metrics': overall_quality,
                    'field_quality_breakdown': field_quality,
                    'model_quality_comparison': model_quality,
                    'source_quality_analysis': source_quality,
                    'quality_trends': quality_trends
                },
                'quality_issues': quality_issues,
                'recommendations': recommendations,
                'action_items': analyzer.prioritize_quality_improvements(quality_issues, recommendations)
            }

            logger.info(f"[STATS-ADVANCED] Data Quality Analysis abgeschlossen - Score: {overall_quality['overall_score']}")
            return response

    except Exception as e:
        logger.error(f"[STATS-ADVANCED] Fehler bei Data Quality Analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Data Quality Analysis Fehler: {str(e)}")

@router.get("/comparison/providers", response_model=Dict[str, Any])
async def get_provider_comparison(
    days_back: int = Query(30, ge=7, le=365, description="Vergleichszeitraum"),
    include_cost_comparison: bool = Query(False, description="Kosten-Vergleich einschließen"),
    metrics: str = Query("performance,quality,reliability", description="Vergleichsmetriken")
):
    """
    Umfassender Provider-Vergleich mit multi-dimensionaler Analyse
    """
    try:
        with db_manager.get_session() as session:
            # Zeitraum
            start_date = datetime.now() - timedelta(days=days_back)

            search_results = session.query(SearchResult).filter(
                SearchResult.search_timestamp >= start_date
            ).all()

            # Gruppiere nach Providern (aus model_used extrahieren)
            provider_data = {}
            for result in search_results:
                # Provider aus model_id extrahieren (z.B. "openrouter:model" -> "openrouter")
                provider = result.model_used.split(':')[0] if ':' in result.model_used else result.model_used
                if provider not in provider_data:
                    provider_data[provider] = []
                provider_data[provider].append(result)

            # Berechne Vergleichsmetriken
            calculator = StatisticsCalculator()
            analyzer = StatisticsAnalyzer()

            provider_comparison = {}

            for provider, results in provider_data.items():
                comparison_metrics = {}

                # Performance-Metriken
                if 'performance' in metrics:
                    comparison_metrics['performance'] = {
                        'avg_response_time_ms': calculator.calculate_avg_response_time(results),
                        'success_rate': calculator.calculate_success_rate(results),
                        'throughput_queries_per_hour': len(results) / (days_back * 24),
                        'reliability_score': calculator.calculate_reliability_score(results)
                    }

                # Quality-Metriken
                if 'quality' in metrics:
                    comparison_metrics['quality'] = {
                        'avg_field_coverage': calculator.calculate_avg_field_coverage(results),
                        'data_quality_score': calculator.calculate_data_quality_score(results),
                        'consistency_score': calculator.calculate_consistency_score(results),
                        'completeness_score': calculator.calculate_completeness_score(results)
                    }

                # Reliability-Metriken
                if 'reliability' in metrics:
                    comparison_metrics['reliability'] = {
                        'uptime_percentage': calculator.calculate_uptime_percentage(results),
                        'error_rate': calculator.calculate_error_rate(results),
                        'stability_score': calculator.calculate_stability_score(results),
                        'consistency_over_time': calculator.calculate_consistency_over_time(results)
                    }

                # Kosten-Metriken (optional)
                if include_cost_comparison:
                    comparison_metrics['cost_efficiency'] = {
                        'cost_per_successful_query': calculator.calculate_cost_per_query(provider, len(results)),
                        'cost_per_field_discovered': calculator.calculate_cost_per_field(provider, results),
                        'roi_score': calculator.calculate_roi_score(provider, results)
                    }

                provider_comparison[provider] = {
                    'provider_name': provider,
                    'total_queries': len(results),
                    'models_used': len(set(r.model_used for r in results)),
                    'metrics': comparison_metrics,
                    'strengths': analyzer.identify_provider_strengths(comparison_metrics),
                    'weaknesses': analyzer.identify_provider_weaknesses(comparison_metrics)
                }

            # Gesamt-Rankings
            rankings = analyzer.calculate_provider_rankings(provider_comparison, metrics.split(','))

            # Best Practices und Empfehlungen
            recommendations = analyzer.generate_provider_recommendations(provider_comparison)

            response = {
                'comparison_summary': {
                    'analysis_period_days': days_back,
                    'providers_compared': len(provider_comparison),
                    'total_queries_analyzed': len(search_results),
                    'comparison_metrics': metrics.split(',')
                },
                'provider_comparison': provider_comparison,
                'rankings': rankings,
                'best_practices': analyzer.identify_best_practices(provider_comparison),
                'recommendations': recommendations,
                'cost_analysis':
analyzer.generate_cost_optimization_suggestions(provider_comparison) if include_cost_comparison else
None
            }

            logger.info(f"[STATS-ADVANCED] Provider Comparison für {len(provider_comparison)} Provider abgeschlossen")
            return response

    except Exception as e:
        logger.error(f"[STATS-ADVANCED] Fehler bei Provider Comparison: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Provider Comparison Fehler: {str(e)}")

# Globale Router-Instanz
statistics_advanced_router = router
