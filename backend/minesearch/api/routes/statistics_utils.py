"""
Compact Statistics Utilities
Kompakte Version der Statistics Utilities

Author: MineSearch Development Team
Date: 2025-01-11
"""

import logging
import json
import statistics
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union

logger = logging.getLogger(__name__)


class StatisticsTimeAnalyzer:
    """Zeitanalyse für Statistik-Metriken"""

    def analyze_response_times(self, search_results: List) -> Dict[str, Any]:
        """Analysiert Antwortzeiten der Suchergebnisse"""
        if not search_results:
            return {
                'average_response_time': 0.0,
                'median_response_time': 0.0,
                'min_response_time': 0.0,
                'max_response_time': 0.0,
                'total_requests': 0
            }

        response_times = []
        for result in search_results:
            if hasattr(result, 'response_time') and result.response_time:
                response_times.append(result.response_time)

        if not response_times:
            return {
                'average_response_time': 0.0,
                'median_response_time': 0.0,
                'min_response_time': 0.0,
                'max_response_time': 0.0,
                'total_requests': len(search_results)
            }

        return {
            'average_response_time': statistics.mean(response_times),
            'median_response_time': statistics.median(response_times),
            'min_response_time': min(response_times),
            'max_response_time': max(response_times),
            'total_requests': len(search_results)
        }

    def analyze_timeframe_performance(self, search_results: List, hours: int = 24) -> Dict[str, Any]:
        """Analysiert Performance in einem Zeitraum"""
        if not search_results:
            return {'timeframe_hours': hours, 'performance_data': []}

        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_results = []

        for result in search_results:
            if hasattr(result, 'created_at'):
                if isinstance(result.created_at, str):
                    try:
                        result_time = datetime.fromisoformat(result.created_at.replace('Z', '+00:00'))
                    except ValueError:
                        continue
                elif isinstance(result.created_at, datetime):
                    result_time = result.created_at
                else:
                    continue

                if result_time >= cutoff_time:
                    recent_results.append(result)

        return {
            'timeframe_hours': hours,
            'total_requests_in_timeframe': len(recent_results),
            'performance_data': self.analyze_response_times(recent_results)
        }


class StatisticsCalculator:
    """Berechnungs-Engine für Statistik-Metriken"""

    def calculate_success_rate(self, search_results: List) -> float:
        """Berechnet Erfolgsrate basierend auf structured_data"""
        if not search_results:
            return 0.0

        successful = sum(1 for result in search_results if result.structured_data)
        return successful / len(search_results)

    def calculate_avg_response_time(self, search_results: List) -> float:
        """Berechnet durchschnittliche Antwortzeit"""
        if not search_results:
            return 0.0

        response_times = [result.response_time for result in search_results if hasattr(result, 'response_time')]
        return statistics.mean(response_times) if response_times else 0.0

    def calculate_field_completeness(self, search_results: List, field_name: str) -> float:
        """Berechnet Vollständigkeit eines Feldes"""
        if not search_results:
            return 0.0

        complete = 0
        for result in search_results:
            if result.structured_data and field_name in result.structured_data:
                value = result.structured_data[field_name]
                if value and str(value).strip() and not self._is_template_value(value):
                    complete += 1

        return complete / len(search_results)

    def calculate_model_performance(self, search_results: List) -> Dict[str, Any]:
        """Berechnet Modell-Performance"""
        if not search_results:
            return {}

        model_stats = {}
        for result in search_results:
            model = result.model_used
            if model not in model_stats:
                model_stats[model] = {
                    'total_searches': 0,
                    'successful_searches': 0,
                    'avg_response_time': 0,
                    'field_completeness': {}
                }

            model_stats[model]['total_searches'] += 1
            if result.structured_data:
                model_stats[model]['successful_searches'] += 1

        # Berechne Erfolgsraten
        for model, stats in model_stats.items():
            stats['success_rate'] = stats['successful_searches'] / stats['total_searches']

        return model_stats

    def calculate_source_effectiveness(self, search_results: List) -> Dict[str, Any]:
        """Berechnet Quellen-Effektivität"""
        if not search_results:
            return {}

        source_stats = {}
        for result in search_results:
            if hasattr(result, 'sources') and result.sources:
                for source in result.sources:
                    source_url = source.get('url', 'unknown')
                    if source_url not in source_stats:
                        source_stats[source_url] = {
                            'usage_count': 0,
                            'success_count': 0,
                            'avg_relevance': 0
                        }

                    source_stats[source_url]['usage_count'] += 1
                    if result.structured_data:
                        source_stats[source_url]['success_count'] += 1

        # Berechne Effektivität
        for source, stats in source_stats.items():
            stats['effectiveness'] = stats['success_count'] / stats['usage_count']

        return source_stats

    def _is_template_value(self, value: Any) -> bool:
        """Prüft ob Wert ein Template ist"""
        if not value:
            return True

        value_str = str(value).lower().strip()
        template_indicators = [
            'template:', 'not specified', 'no data', 'n/a', 'unknown',
            'not available', 'not found', 'tbd', 'to be determined'
        ]

        return any(indicator in value_str for indicator in template_indicators)

    async def get_total_mines(self) -> int:
        """Hole Gesamtanzahl Minen"""
        try:
            from minesearch.database import db_manager
            return await db_manager.count_mines()
        except Exception as e:
            logger.error(f"Fehler beim Zählen der Minen: {e}")
            return 0

    async def get_total_sources(self) -> int:
        """Hole Gesamtanzahl Quellen"""
        try:
            from minesearch.database import db_manager
            return await db_manager.count_sources()
        except Exception as e:
            logger.error(f"Fehler beim Zählen der Quellen: {e}")
            return 0

    async def get_total_searches(self) -> int:
        """Hole Gesamtanzahl Suchen"""
        try:
            from minesearch.database import db_manager
            return await db_manager.count_searches()
        except Exception as e:
            logger.error(f"Fehler beim Zählen der Suchen: {e}")
            return 0


    async def get_mines_with_stats(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Hole Minen mit Statistiken"""
        try:
            from minesearch.database import db_manager
            mines = await db_manager.get_mines_with_stats(limit, offset)
            return mines
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Minen: {e}")
            return []

    async def get_sources_with_stats(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Hole Quellen mit Statistiken"""
        try:
            from minesearch.database import db_manager
            sources = await db_manager.get_sources_with_stats(limit, offset)
            return sources
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Quellen: {e}")
            return []

    async def check_database_health(self) -> Dict[str, Any]:
        """Prüfe Datenbank-Gesundheit"""
        try:
            from minesearch.database import db_manager
            return await db_manager.health_check()
        except Exception as e:
            logger.error(f"Fehler bei Gesundheitsprüfung: {e}")
            return {'connected': False, 'error': str(e)}


class StatisticsAnalyzer:
    """Analyse-Engine für erweiterte Statistiken"""

    def analyze_model_consistency(self, search_results: List) -> Dict[str, Any]:
        """Analysiere Modell-Konsistenz"""
        if not search_results:
            return {}

        model_consistency = {}
        for result in search_results:
            model = result.model_used
            if model not in model_consistency:
                model_consistency[model] = {
                    'total_results': 0,
                    'consistent_results': 0,
                    'inconsistent_results': 0
                }

            model_consistency[model]['total_results'] += 1
            if self._is_consistent_result(result):
                model_consistency[model]['consistent_results'] += 1
            else:
                model_consistency[model]['inconsistent_results'] += 1

        # Berechne Konsistenz-Raten
        for model, stats in model_consistency.items():
            stats['consistency_rate'] = stats['consistent_results'] / stats['total_results']

        return model_consistency

    def analyze_field_quality(self, search_results: List) -> Dict[str, Any]:
        """Analysiere Feld-Qualität"""
        if not search_results:
            return {}

        field_quality = {}
        for result in search_results:
            if result.structured_data:
                for field, value in result.structured_data.items():
                    if field not in field_quality:
                        field_quality[field] = {
                            'total_occurrences': 0,
                            'high_quality': 0,
                            'medium_quality': 0,
                            'low_quality': 0
                        }

                    field_quality[field]['total_occurrences'] += 1
                    quality = self._assess_field_quality(value)
                    field_quality[field][f'{quality}_quality'] += 1

        return field_quality

    def analyze_temporal_trends(self, search_results: List) -> Dict[str, Any]:
        """Analysiere zeitliche Trends"""
        if not search_results:
            return {}

        # Gruppiere nach Zeiträumen
        daily_stats = {}
        for result in search_results:
            if hasattr(result, 'search_timestamp'):
                date = result.search_timestamp.date()
                if date not in daily_stats:
                    daily_stats[date] = {
                        'total_searches': 0,
                        'successful_searches': 0,
                        'models_used': set()
                    }

                daily_stats[date]['total_searches'] += 1
                if result.structured_data:
                    daily_stats[date]['successful_searches'] += 1
                daily_stats[date]['models_used'].add(result.model_used)

        # Konvertiere Sets zu Listen für JSON-Serialisierung
        for date, stats in daily_stats.items():
            stats['models_used'] = list(stats['models_used'])
            stats['success_rate'] = stats['successful_searches'] / stats['total_searches']

        return daily_stats

    def _is_consistent_result(self, result) -> bool:
        """Prüft ob Ergebnis konsistent ist"""
        if not result.structured_data:
            return False

        # Prüfe auf Widersprüche in den Daten
        for field, value in result.structured_data.items():
            if self._is_template_value(value):
                return False

        return True

    def _assess_field_quality(self, value: Any) -> str:
        """Bewerte Feld-Qualität"""
        if not value:
            return 'low'

        value_str = str(value).strip()
        if len(value_str) < 3:
            return 'low'

        if self._is_template_value(value):
            return 'low'

        if len(value_str) > 100:
            return 'high'
        elif len(value_str) > 20:
            return 'medium'
        else:
            return 'low'

    async def get_model_performance(self) -> Dict[str, Any]:
        """Hole Modell-Performance"""
        try:
            from minesearch.database import db_manager
            results = await db_manager.get_recent_search_results(limit=1000)
            return self.analyze_model_consistency(results)
        except Exception as e:
            logger.error(f"Fehler bei Modell-Performance-Analyse: {e}")
            return {}

    async def get_field_consistency(self, mine_name: str = None, model: str = None) -> Dict[str, Any]:
        """Hole Feld-Konsistenz"""
        try:
            from minesearch.database import db_manager
            results = await db_manager.get_search_results(mine_name=mine_name, model=model, limit=1000)
            return self.analyze_field_quality(results)
        except Exception as e:
            logger.error(f"Fehler bei Feld-Konsistenz-Analyse: {e}")
            return {}

    async def get_field_completeness(self, mine_name: str = None, model: str = None) -> Dict[str, Any]:
        """Hole Feld-Vollständigkeit"""
        try:
            from minesearch.database import db_manager
            results = await db_manager.get_search_results(mine_name=mine_name, model=model, limit=1000)
            
            calculator = StatisticsCalculator()
            completeness = {}
            
            # Standard-Felder
            standard_fields = ['mine_name', 'country', 'commodity', 'production_capacity', 'ownership']
            
            for field in standard_fields:
                completeness[field] = calculator.calculate_field_completeness(results, field)
            
            return completeness
        except Exception as e:
            logger.error(f"Fehler bei Feld-Vollständigkeits-Analyse: {e}")
            return {}

    async def get_model_consistency(self) -> Dict[str, Any]:
        """Hole Modell-Konsistenz"""
        try:
            from minesearch.database import db_manager
            results = await db_manager.get_recent_search_results(limit=1000)
            return self.analyze_model_consistency(results)
        except Exception as e:
            logger.error(f"Fehler bei Modell-Konsistenz-Analyse: {e}")
            return {}

    async def analyze_comprehensive(
        self,
        mine_name: str = None,
        model: str = None,
        field: str = None,
        time_range_days: int = 30
    ) -> Dict[str, Any]:
        """Führe umfassende Analyse durch"""
        try:
            from minesearch.database import db_manager
            
            # Hole relevante Daten
            results = await db_manager.get_search_results(
                mine_name=mine_name,
                model=model,
                limit=1000
            )
            
            # Führe Analysen durch
            analysis = {
                'model_performance': self.analyze_model_consistency(results),
                'field_quality': self.analyze_field_quality(results),
                'temporal_trends': self.analyze_temporal_trends(results),
                'summary': {
                    'total_results': len(results),
                    'analysis_timestamp': datetime.now().isoformat(),
                    'parameters': {
                        'mine_name': mine_name,
                        'model': model,
                        'field': field,
                        'time_range_days': time_range_days
                    }
                }
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Fehler bei umfassender Analyse: {e}")
            return {'error': str(e)}


# Instanziiere Utility-Klassen für globale Verwendung
statistics_time_analyzer = StatisticsTimeAnalyzer()
statistics_calculator = StatisticsCalculator()
statistics_analyzer = StatisticsCalculator()  # Alias für Kompatibilität

__all__ = ["StatisticsCalculator", "StatisticsTimeAnalyzer", "statistics_calculator", "statistics_analyzer", "statistics_time_analyzer"]
