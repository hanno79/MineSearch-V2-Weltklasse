"""
Author: rahn
Datum: 06.08.2025
Version: 1.0
Beschreibung: Statistics Utilities - Helper-Klassen und Berechnungsfunktionen
ÄNDERUNG 06.08.2025: Refactoring gemäß REGEL 1 - Utilities aus statistics.py
"""

import logging
import json
import statistics
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union

logger = logging.getLogger(__name__)

class StatisticsCalculator:
    """
    Berechnungs-Engine für Statistik-Metriken
    """
    
    def calculate_success_rate(self, search_results: List) -> float:
        """Berechnet Erfolgsrate basierend auf structured_data"""
        if not search_results:
            return 0.0
        
        successful = sum(1 for result in search_results if result.structured_data)
        return successful / len(search_results)
    
    def calculate_avg_response_time(self, search_results: List) -> float:
        """Berechnet durchschnittliche Response-Zeit"""
        if not search_results:
            return 0.0
        
        # Placeholder - echte Response-Zeit müsste gespeichert werden
        # Hier simulieren wir basierend auf Datenvolumen
        response_times = []
        for result in search_results:
            if result.structured_data:
                data_size = len(str(result.structured_data))
                estimated_time = min(max(data_size / 10, 100), 5000)  # 100ms - 5s
                response_times.append(estimated_time)
        
        return statistics.mean(response_times) if response_times else 1000.0
    
    def calculate_avg_field_coverage(self, search_results: List) -> float:
        """Berechnet durchschnittliche Feldabdeckung"""
        if not search_results:
            return 0.0
        
        field_coverages = []
        important_fields = [
            'mine_name', 'commodity', 'country', 'region', 
            'latitude', 'longitude', 'production_volume', 'reserves'
        ]
        
        for result in search_results:
            if result.structured_data:
                try:
                    data = json.loads(result.structured_data) if isinstance(result.structured_data, str) else result.structured_data
                    if isinstance(data, dict):
                        present_fields = sum(1 for field in important_fields if field in data and data[field])
                        coverage = present_fields / len(important_fields)
                        field_coverages.append(coverage)
                except (json.JSONDecodeError, TypeError):
                    field_coverages.append(0.0)
        
        return statistics.mean(field_coverages) if field_coverages else 0.0
    
    def calculate_data_quality_score(self, search_results: List) -> float:
        """Berechnet Datenqualitäts-Score"""
        if not search_results:
            return 0.0
        
        quality_scores = []
        
        for result in search_results:
            if result.structured_data:
                try:
                    data = json.loads(result.structured_data) if isinstance(result.structured_data, str) else result.structured_data
                    if isinstance(data, dict):
                        # Qualitäts-Faktoren
                        completeness = len([v for v in data.values() if v and str(v).strip()]) / len(data)
                        accuracy = self._assess_data_accuracy(data)
                        consistency = self._assess_data_consistency(data)
                        
                        quality_score = (completeness + accuracy + consistency) / 3 * 100
                        quality_scores.append(quality_score)
                except (json.JSONDecodeError, TypeError):
                    quality_scores.append(0.0)
        
        return statistics.mean(quality_scores) if quality_scores else 0.0
    
    def _assess_data_accuracy(self, data: Dict) -> float:
        """Bewertet Datengenauigkeit"""
        accuracy_indicators = 0
        total_checks = 0
        
        # Koordinaten-Plausibilität
        if 'latitude' in data and 'longitude' in data:
            try:
                lat = float(data['latitude'])
                lon = float(data['longitude'])
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    accuracy_indicators += 1
                total_checks += 1
            except (ValueError, TypeError):
                total_checks += 1
        
        # Land-Region Konsistenz
        if 'country' in data and 'region' in data:
            # Placeholder für echte Validierung
            if data['country'] and data['region']:
                accuracy_indicators += 1
            total_checks += 1
        
        return accuracy_indicators / total_checks if total_checks > 0 else 1.0
    
    def _assess_data_consistency(self, data: Dict) -> float:
        """Bewertet Datenkonsistenz"""
        consistency_score = 1.0
        
        # Überprüfe Format-Konsistenz
        numeric_fields = ['latitude', 'longitude', 'production_volume', 'reserves']
        for field in numeric_fields:
            if field in data and data[field]:
                try:
                    float(data[field])
                except (ValueError, TypeError):
                    consistency_score -= 0.1
        
        return max(0.0, consistency_score)
    
    def calculate_reliability_trend(self, search_results: List) -> List[float]:
        """Berechnet Zuverlässigkeits-Trend über Zeit"""
        if len(search_results) < 2:
            return [1.0] if search_results else []
        
        # Gruppiere nach Tagen
        daily_results = {}
        for result in search_results:
            day_key = result.search_timestamp.date() if result.search_timestamp else datetime.now().date()
            if day_key not in daily_results:
                daily_results[day_key] = []
            daily_results[day_key].append(result)
        
        # Berechne tägliche Erfolgsraten
        trend = []
        for day in sorted(daily_results.keys()):
            day_success_rate = self.calculate_success_rate(daily_results[day])
            trend.append(day_success_rate)
        
        return trend
    
    def calculate_field_breakdown(self, search_results: List) -> Dict[str, float]:
        """Berechnet Field Coverage Breakdown"""
        if not search_results:
            return {}
        
        field_counts = {}
        total_results = 0
        
        important_fields = [
            'mine_name', 'commodity', 'country', 'region',
            'latitude', 'longitude', 'production_volume', 'reserves',
            'resources', 'mining_method', 'operator', 'status'
        ]
        
        for result in search_results:
            if result.structured_data:
                try:
                    data = json.loads(result.structured_data) if isinstance(result.structured_data, str) else result.structured_data
                    if isinstance(data, dict):
                        total_results += 1
                        for field in important_fields:
                            if field in data and data[field]:
                                field_counts[field] = field_counts.get(field, 0) + 1
                except (json.JSONDecodeError, TypeError):
                    pass
        
        # Konvertiere zu Prozentsätzen
        field_breakdown = {}
        for field in important_fields:
            coverage = (field_counts.get(field, 0) / total_results * 100) if total_results > 0 else 0
            field_breakdown[field] = coverage
        
        return field_breakdown
    
    def calculate_cost_per_query(self, model_id: str, successful_queries: int) -> Optional[float]:
        """Berechnet geschätzte Kosten pro Query"""
        # Placeholder - echte Kosten-Berechnung würde Provider-spezifische Preise verwenden
        provider_costs = {
            'openrouter': 0.002,  # $0.002 per successful query
            'perplexity': 0.001,  # $0.001 per successful query
            'abacus': 0.003,      # $0.003 per successful query
            'anthropic': 0.005    # $0.005 per successful query
        }
        
        provider = model_id.split(':')[0] if ':' in model_id else model_id
        return provider_costs.get(provider, 0.002)
    
    def calculate_avg_results_per_query(self, search_results: List) -> float:
        """Berechnet durchschnittliche Anzahl Ergebnisse pro Query"""
        if not search_results:
            return 0.0
        
        result_counts = []
        for result in search_results:
            if result.sources:
                try:
                    # BUGFIX 07.08.2025: Attribute heißt 'sources', nicht 'sources_json'
                    sources = result.sources if isinstance(result.sources, list) else []
                    if isinstance(sources, list):
                        result_counts.append(len(sources))
                except (json.JSONDecodeError, TypeError):
                    result_counts.append(0)
        
        return statistics.mean(result_counts) if result_counts else 0.0
    
    def calculate_model_consistency(self, search_results: List, model_id: str) -> Dict[str, Any]:
        """
        NEUE METHODE: Berechnet Modell-Konsistenz für mehrfache Suchen
        Analysiert wie oft ein Modell bei derselben Mine dieselben Werte zurückgibt
        """
        if not search_results:
            return {'overall_consistency': 0.0, 'field_consistency': {}, 'consistency_grade': 'Keine Daten'}
        
        # Gruppiere Ergebnisse nach Mine
        mine_results = {}
        for result in search_results:
            mine_name = result.mine_name if hasattr(result, 'mine_name') else 'unknown'
            if mine_name not in mine_results:
                mine_results[mine_name] = []
            mine_results[mine_name].append(result)
        
        # Berechne Konsistenz für Minen mit mehrfachen Suchen
        field_consistency_data = {}
        total_comparisons = 0
        total_matches = 0
        
        for mine_name, results in mine_results.items():
            if len(results) < 2:  # Brauchen mindestens 2 Ergebnisse für Vergleich
                continue
            
            # Vergleiche alle Paare von Ergebnissen für diese Mine
            for i in range(len(results)):
                for j in range(i + 1, len(results)):
                    result1, result2 = results[i], results[j]
                    
                    if result1.structured_data and result2.structured_data:
                        try:
                            data1 = json.loads(result1.structured_data) if isinstance(result1.structured_data, str) else result1.structured_data
                            data2 = json.loads(result2.structured_data) if isinstance(result2.structured_data, str) else result2.structured_data
                            
                            if isinstance(data1, dict) and isinstance(data2, dict):
                                # Vergleiche jedes Feld
                                common_fields = set(data1.keys()) & set(data2.keys())
                                for field in common_fields:
                                    if field not in field_consistency_data:
                                        field_consistency_data[field] = {'matches': 0, 'total': 0}
                                    
                                    field_consistency_data[field]['total'] += 1
                                    total_comparisons += 1
                                    
                                    # Normalisiere Werte für Vergleich (Groß-/Kleinschreibung, Whitespace)
                                    val1 = str(data1[field]).strip().lower() if data1[field] else ''
                                    val2 = str(data2[field]).strip().lower() if data2[field] else ''
                                    
                                    if val1 and val2 and val1 == val2:
                                        field_consistency_data[field]['matches'] += 1
                                        total_matches += 1
                                        
                        except (json.JSONDecodeError, TypeError):
                            continue
        
        # Berechne Konsistenz-Prozentsätze
        field_consistency = {}
        for field, data in field_consistency_data.items():
            if data['total'] > 0:
                consistency_pct = (data['matches'] / data['total']) * 100
                field_consistency[field] = {
                    'consistency_percent': consistency_pct,
                    'matches': data['matches'],
                    'total_comparisons': data['total'],
                    'grade': self._get_consistency_grade(consistency_pct)
                }
        
        # Gesamtkonsistenz
        overall_consistency = (total_matches / total_comparisons * 100) if total_comparisons > 0 else 0.0
        
        return {
            'overall_consistency': overall_consistency,
            'field_consistency': field_consistency,
            'consistency_grade': self._get_consistency_grade(overall_consistency),
            'total_mine_comparisons': len([m for m in mine_results.values() if len(m) >= 2]),
            'total_field_comparisons': total_comparisons
        }
    
    def identify_most_found_fields(self, search_results: List) -> Dict[str, Any]:
        """
        NEUE METHODE: Identifiziert welche Felder ein Modell am häufigsten/besten findet
        """
        if not search_results:
            return {'top_fields': [], 'field_success_rates': {}}
        
        field_stats = {}
        
        for result in search_results:
            if result.structured_data:
                try:
                    data = json.loads(result.structured_data) if isinstance(result.structured_data, str) else result.structured_data
                    if isinstance(data, dict):
                        for field, value in data.items():
                            if field not in field_stats:
                                field_stats[field] = {'found': 0, 'total': 0, 'quality_sum': 0}
                            
                            field_stats[field]['total'] += 1
                            
                            # Bewerte Qualität des gefundenen Wertes
                            if value and str(value).strip() and value not in ['X', '-', 'N/A', 'unknown']:
                                field_stats[field]['found'] += 1
                                
                                # Qualitäts-Score basierend auf Länge und Plausibilität
                                quality_score = min(len(str(value)) / 10, 1.0)  # Längere Antworten = höhere Qualität
                                field_stats[field]['quality_sum'] += quality_score
                                
                except (json.JSONDecodeError, TypeError):
                    continue
        
        # Berechne Success Rates und sortiere
        field_success_rates = {}
        for field, stats in field_stats.items():
            if stats['total'] > 0:
                success_rate = (stats['found'] / stats['total']) * 100
                avg_quality = (stats['quality_sum'] / stats['found']) if stats['found'] > 0 else 0
                field_success_rates[field] = {
                    'success_rate': success_rate,
                    'found_count': stats['found'],
                    'total_attempts': stats['total'],
                    'avg_quality': avg_quality,
                    'combined_score': success_rate * (1 + avg_quality)  # Kombinierter Score
                }
        
        # Sortiere nach combined_score
        top_fields = sorted(field_success_rates.items(), 
                          key=lambda x: x[1]['combined_score'], 
                          reverse=True)[:10]  # Top 10
        
        return {
            'top_fields': [{'field': field, **data} for field, data in top_fields],
            'field_success_rates': field_success_rates
        }
    
    def _get_consistency_grade(self, consistency_percent: float) -> str:
        """Bestimmt Konsistenz-Bewertung basierend auf Prozentsatz"""
        if consistency_percent >= 90:
            return 'Excellent'
        elif consistency_percent >= 80:
            return 'Good'
        elif consistency_percent >= 70:
            return 'Fair'
        elif consistency_percent >= 50:
            return 'Poor'
        else:
            return 'Very Poor'
    
    def _determine_performance_category(self, success_rate: float, consistency: float) -> str:
        """
        NEUE METHODE: Bestimmt Performance-Kategorie basierend auf Success Rate und Konsistenz
        """
        # Kombinierter Score aus Success Rate und Konsistenz
        combined_score = (success_rate + consistency) / 2
        
        if combined_score >= 85:
            return 'Excellent'
        elif combined_score >= 75:
            return 'Very Good'
        elif combined_score >= 65:
            return 'Good'
        elif combined_score >= 55:
            return 'Fair'
        elif combined_score >= 40:
            return 'Poor'
        else:
            return 'Very Poor'

    def analyze_model_specialization(self, search_results: List) -> Dict[str, Any]:
        """Analysiert Modell-Spezialisierung"""
        if not search_results:
            return {'specialization_score': 0, 'best_categories': [], 'performance_by_field': {}}
        
        # Analysiere Performance nach Commodity-Typen
        commodity_performance = {}
        field_performance = {}
        
        for result in search_results:
            if result.structured_data:
                try:
                    data = json.loads(result.structured_data) if isinstance(result.structured_data, str) else result.structured_data
                    if isinstance(data, dict):
                        # Commodity-basierte Analyse
                        commodity = data.get('commodity', 'unknown')
                        if commodity not in commodity_performance:
                            commodity_performance[commodity] = {'total': 0, 'successful': 0}
                        commodity_performance[commodity]['total'] += 1
                        if len([v for v in data.values() if v]) >= 3:  # Mindestens 3 Felder gefüllt
                            commodity_performance[commodity]['successful'] += 1
                        
                        # Field-basierte Analyse
                        for field, value in data.items():
                            if field not in field_performance:
                                field_performance[field] = {'total': 0, 'filled': 0}
                            field_performance[field]['total'] += 1
                            if value:
                                field_performance[field]['filled'] += 1
                except (json.JSONDecodeError, TypeError):
                    pass
        
        # Identifiziere Stärken
        best_commodities = []
        for commodity, stats in commodity_performance.items():
            if stats['total'] >= 3:  # Mindestens 3 Samples
                success_rate = stats['successful'] / stats['total']
                if success_rate >= 0.8:  # 80% Erfolgsrate
                    best_commodities.append(commodity)
        
        # Berechne Spezialisierungs-Score
        specialization_score = len(best_commodities) * 10  # Höhere Vielseitigkeit = höherer Score
        
        return {
            'specialization_score': min(100, specialization_score),
            'best_categories': best_commodities,
            'performance_by_field': field_performance,
            'commodity_performance': commodity_performance
        }
    
    def calculate_recent_performance(self, search_results: List, days: int) -> Dict[str, Any]:
        """Berechnet Performance für letzten X Tage"""
        if not search_results:
            return {'success_rate': 0, 'avg_response_time': 0, 'total_queries': 0}
        
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_results = [r for r in search_results if r.search_timestamp and r.search_timestamp >= cutoff_date]
        
        return {
            'success_rate': self.calculate_success_rate(recent_results),
            'avg_response_time': self.calculate_avg_response_time(recent_results),
            'field_coverage': self.calculate_avg_field_coverage(recent_results),
            'total_queries': len(recent_results),
            'data_quality': self.calculate_data_quality_score(recent_results)
        }
    
    def compare_to_system_average(self, model_stats) -> Dict[str, Any]:
        """Vergleicht Modell-Performance mit System-Durchschnitt"""
        # Placeholder - System-Durchschnitt würde aus globalen Statistiken kommen
        system_averages = {
            'success_rate': 0.85,
            'avg_response_time': 1200,  # ms
            'avg_field_coverage': 0.75,
            'data_quality_score': 88
        }
        
        comparison = {}
        for metric in system_averages:
            model_value = getattr(model_stats, metric, 0)
            system_avg = system_averages[metric]
            
            if metric == 'avg_response_time':  # Für Response Time: niedrigere Werte sind besser
                performance_ratio = system_avg / model_value if model_value > 0 else 1
            else:
                performance_ratio = model_value / system_avg if system_avg > 0 else 1
            
            comparison[metric] = {
                'model_value': model_value,
                'system_average': system_avg,
                'performance_ratio': performance_ratio,
                'status': 'above_average' if performance_ratio > 1.05 else 'below_average' if performance_ratio < 0.95 else 'average'
            }
        
        return comparison

class StatisticsAnalyzer:
    """
    Erweiterte Analyse-Engine für komplexe Statistik-Auswertungen
    """
    
    async def analyze_system_bottlenecks(self, session, search_results: List) -> Dict[str, Any]:
        """Analysiert System-Engpässe"""
        bottlenecks = {
            'identified_bottlenecks': [],
            'performance_impact': {},
            'recommendations': []
        }
        
        # Response Time Analyse
        response_times = [1200, 800, 1500, 900, 2000]  # Placeholder
        if statistics.mean(response_times) > 1500:
            bottlenecks['identified_bottlenecks'].append('high_response_times')
            bottlenecks['performance_impact']['response_time'] = 'HIGH'
            bottlenecks['recommendations'].append('Optimize model response times')
        
        # Success Rate Analyse
        calculator = StatisticsCalculator()
        success_rate = calculator.calculate_success_rate(search_results)
        if success_rate < 0.8:
            bottlenecks['identified_bottlenecks'].append('low_success_rate')
            bottlenecks['performance_impact']['success_rate'] = 'HIGH'
            bottlenecks['recommendations'].append('Improve model reliability')
        
        # Database Performance
        if len(search_results) > 10000:  # Große Datenmenge
            bottlenecks['identified_bottlenecks'].append('database_performance')
            bottlenecks['performance_impact']['database'] = 'MEDIUM'
            bottlenecks['recommendations'].append('Consider database optimization')
        
        return bottlenecks
    
    def calculate_overall_coverage_score(self, coverage_results: Dict) -> float:
        """Berechnet Gesamt-Coverage-Score"""
        if not coverage_results:
            return 0.0
        
        field_scores = []
        for field_data in coverage_results.values():
            if isinstance(field_data, dict) and 'coverage_percentage' in field_data:
                field_scores.append(field_data['coverage_percentage'])
        
        return statistics.mean(field_scores) if field_scores else 0.0
    
    def generate_coverage_recommendations(self, coverage_results: Dict) -> List[str]:
        """Generiert Coverage-Empfehlungen"""
        recommendations = []
        
        for field_name, field_data in coverage_results.items():
            if isinstance(field_data, dict):
                coverage = field_data.get('coverage_percentage', 0)
                if coverage < 50:
                    recommendations.append(f"Improve {field_name} field coverage (currently {coverage:.1f}%)")
                elif coverage < 80:
                    recommendations.append(f"Consider optimizing {field_name} data collection")
        
        if not recommendations:
            recommendations.append("Field coverage is excellent across all analyzed fields")
        
        return recommendations

class StatisticsTimeAnalyzer:
    """
    Zeit-basierte Analyse-Engine
    """
    
    def create_time_buckets(self, start_date: datetime, granularity: str, days_back: int) -> Dict[str, Dict]:
        """Erstellt Zeit-Buckets für Trend-Analyse"""
        buckets = {}
        
        if granularity == "hourly":
            for i in range(days_back * 24):
                bucket_time = start_date + timedelta(hours=i)
                bucket_key = bucket_time.strftime("%Y-%m-%d %H:00")
                buckets[bucket_key] = {'timestamp': bucket_time, 'results': []}
        
        elif granularity == "daily":
            for i in range(days_back):
                bucket_time = start_date + timedelta(days=i)
                bucket_key = bucket_time.strftime("%Y-%m-%d")
                buckets[bucket_key] = {'timestamp': bucket_time, 'results': []}
        
        elif granularity == "weekly":
            weeks = days_back // 7
            for i in range(weeks):
                bucket_time = start_date + timedelta(weeks=i)
                bucket_key = f"Week-{bucket_time.strftime('%Y-%W')}"
                buckets[bucket_key] = {'timestamp': bucket_time, 'results': []}
        
        return buckets
    
    def get_bucket_key(self, timestamp: datetime, granularity: str) -> str:
        """Bestimmt Bucket-Key für Timestamp"""
        if granularity == "hourly":
            return timestamp.strftime("%Y-%m-%d %H:00")
        elif granularity == "daily":
            return timestamp.strftime("%Y-%m-%d")
        elif granularity == "weekly":
            return f"Week-{timestamp.strftime('%Y-%W')}"
        return timestamp.strftime("%Y-%m-%d")
    
    def analyze_trend(self, metric_data: Dict[str, float]) -> Dict[str, Any]:
        """Analysiert Trend in Metrik-Daten"""
        if len(metric_data) < 2:
            return {'trend_direction': 'insufficient_data', 'trend_strength': 0}
        
        values = list(metric_data.values())
        
        # Einfache Trend-Analyse (lineare Regression wäre genauer)
        if len(values) >= 3:
            recent_avg = statistics.mean(values[-3:])
            early_avg = statistics.mean(values[:3])
            
            if recent_avg > early_avg * 1.1:
                trend_direction = 'increasing'
                trend_strength = (recent_avg - early_avg) / early_avg
            elif recent_avg < early_avg * 0.9:
                trend_direction = 'decreasing'  
                trend_strength = (early_avg - recent_avg) / early_avg
            else:
                trend_direction = 'stable'
                trend_strength = 0
        else:
            trend_direction = 'stable'
            trend_strength = 0
        
        return {
            'trend_direction': trend_direction,
            'trend_strength': abs(trend_strength),
            'volatility': statistics.stdev(values) if len(values) > 1 else 0,
            'min_value': min(values),
            'max_value': max(values),
            'current_value': values[-1]
        }
    
    def detect_anomalies(self, trend_data: Dict[str, Dict]) -> Dict[str, List]:
        """Erkennt Anomalien in Trend-Daten"""
        anomalies = {}
        
        for metric_name, metric_values in trend_data.items():
            if not isinstance(metric_values, dict):
                continue
                
            values = list(metric_values.values())
            if len(values) < 3:
                continue
            
            mean_val = statistics.mean(values)
            stdev_val = statistics.stdev(values) if len(values) > 1 else 0
            
            metric_anomalies = []
            for timestamp, value in metric_values.items():
                if abs(value - mean_val) > 2 * stdev_val:  # 2-Sigma Regel
                    metric_anomalies.append({
                        'timestamp': timestamp,
                        'value': value,
                        'deviation': abs(value - mean_val),
                        'severity': 'high' if abs(value - mean_val) > 3 * stdev_val else 'medium'
                    })
            
            if metric_anomalies:
                anomalies[metric_name] = metric_anomalies
        
        return anomalies
    
    def generate_forecasts(self, trend_data: Dict[str, Dict], granularity: str) -> Dict[str, Any]:
        """Generiert einfache Prognosen basierend auf Trends"""
        forecasts = {}
        
        for metric_name, metric_values in trend_data.items():
            if not isinstance(metric_values, dict) or len(metric_values) < 3:
                continue
            
            values = list(metric_values.values())
            trend_analysis = self.analyze_trend(metric_values)
            
            # Einfache lineare Extrapolation
            recent_trend = statistics.mean(values[-3:]) - statistics.mean(values[-6:-3]) if len(values) >= 6 else 0
            current_value = values[-1]
            
            # Prognose für nächste Periode
            next_period_forecast = current_value + recent_trend
            
            forecasts[metric_name] = {
                'next_period_forecast': max(0, next_period_forecast),  # Keine negativen Prognosen
                'confidence_level': 'low' if trend_analysis['volatility'] > statistics.mean(values) * 0.3 else 'medium',
                'trend_basis': trend_analysis['trend_direction'],
                'forecast_change_percent': (recent_trend / current_value * 100) if current_value > 0 else 0
            }
        
        return forecasts
    
    def get_overall_trend_direction(self, trend_data: Dict[str, Dict]) -> str:
        """Bestimmt übergeordnete Trend-Richtung"""
        trend_directions = []
        
        for metric_values in trend_data.values():
            if isinstance(metric_values, dict):
                trend_analysis = self.analyze_trend(metric_values)
                trend_directions.append(trend_analysis['trend_direction'])
        
        if not trend_directions:
            return 'unknown'
        
        # Mehrheitsentscheidung
        increasing_count = trend_directions.count('increasing')
        decreasing_count = trend_directions.count('decreasing')
        
        if increasing_count > decreasing_count:
            return 'generally_improving'
        elif decreasing_count > increasing_count:
            return 'generally_declining'
        else:
            return 'mixed_trends'

# Globale Utility-Instanzen
statistics_calculator = StatisticsCalculator()
statistics_analyzer = StatisticsAnalyzer()
statistics_time_analyzer = StatisticsTimeAnalyzer()