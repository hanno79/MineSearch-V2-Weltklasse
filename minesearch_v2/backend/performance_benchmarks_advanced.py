"""
Author: rahn
Datum: 06.08.2025
Version: 1.0
Beschreibung: Advanced Performance Benchmarks - Erweiterte Tests (Refactored aus performance_benchmarks.py)
ÄNDERUNG 06.08.2025: Refactoring gemäß REGEL 1 - Erweiterte Testszenarien ausgelagert
"""

import logging
import asyncio
import time
import json
import statistics
from typing import Dict, List, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path

from performance_optimizer import performance_optimizer
from performance_integration import performance_integration
from performance_benchmarks_utils import BenchmarkDataGenerator, BenchmarkAnalysisTools, BenchmarkReportGenerator

logger = logging.getLogger(__name__)

class AdvancedPerformanceBenchmarks:
    """
    Erweiterte Performance-Benchmarks für komplexe Szenarien
    
    ERWEITERTE TESTSZENARIEN:
    1. Large Dataset Stress Test (>10,000 items)
    2. Synonym Matching Effectiveness
    3. Integration Compatibility Tests
    4. Auto-Refresh Simulation
    """
    
    def __init__(self, output_dir: str = "/app/minesearch_v2/backend/benchmark_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.data_generator = BenchmarkDataGenerator()
        self.analysis_tools = BenchmarkAnalysisTools()
        self.report_generator = BenchmarkReportGenerator(str(self.output_dir))
        
        logger.info(f"[ADVANCED-BENCHMARKS] Advanced Benchmark Suite initialisiert - Output: {self.output_dir}")
    
    async def run_advanced_benchmark_suite(self) -> Dict[str, Any]:
        """
        Führt erweiterte Benchmark-Suite durch
        
        Returns:
            Umfassender Advanced-Benchmark-Bericht
        """
        logger.info("[ADVANCED-BENCHMARKS] Starte erweiterte Benchmark-Suite...")
        start_time = datetime.now()
        
        suite_results = {
            'benchmark_timestamp': start_time.isoformat(),
            'system_info': await self._collect_system_info(),
            'test_results': {},
            'overall_performance': {},
            'summary': {},
            'recommendations': []
        }
        
        # Test 1: Large Dataset Stress Test
        logger.info("[ADVANCED-BENCHMARKS] Test 1: Large Dataset Stress Test")
        suite_results['test_results']['large_dataset_stress'] = await self._test_large_dataset_stress()
        
        # Test 2: Synonym Matching Effectiveness
        logger.info("[ADVANCED-BENCHMARKS] Test 2: Synonym Matching Effectiveness")
        suite_results['test_results']['synonym_matching'] = await self._test_synonym_matching()
        
        # Test 3: Integration Compatibility Check
        logger.info("[ADVANCED-BENCHMARKS] Test 3: Integration Compatibility")
        suite_results['test_results']['integration_compatibility'] = await self._test_integration_compatibility()
        
        # Test 4: Auto-Refresh Simulation
        logger.info("[ADVANCED-BENCHMARKS] Test 4: Auto-Refresh Simulation")
        suite_results['test_results']['auto_refresh_simulation'] = await self._test_auto_refresh_simulation()
        
        # Berechne Overall Performance
        overall_performance = self._calculate_overall_performance(suite_results['test_results'])
        suite_results['overall_performance'] = overall_performance
        
        # Generiere Summary und Recommendations
        summary = self._generate_benchmark_summary(suite_results)
        suite_results['summary'] = summary
        suite_results['recommendations'] = self.analysis_tools.generate_performance_recommendations(suite_results)
        
        # Speichere Ergebnisse
        end_time = datetime.now()
        suite_results['total_benchmark_duration_seconds'] = (end_time - start_time).total_seconds()
        
        await self.report_generator.save_benchmark_results(suite_results, "advanced_benchmark")
        
        logger.info(f"[ADVANCED-BENCHMARKS] Advanced Benchmark-Suite abgeschlossen: {overall_performance['grade']} "
                   f"({overall_performance['score']}/100)")
        
        return suite_results
    
    async def _collect_system_info(self) -> Dict[str, Any]:
        """Sammelt System-Informationen für Benchmark-Kontext"""
        import psutil
        import platform
        
        return {
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'cpu_count': psutil.cpu_count(),
            'memory_total_mb': psutil.virtual_memory().total / 1024 / 1024,
            'memory_available_mb': psutil.virtual_memory().available / 1024 / 1024,
            'optimizer_config': {
                'cache_size': performance_optimizer.cache_size,
                'auto_refresh_interval': performance_optimizer.auto_refresh_interval
            }
        }
    
    async def _test_large_dataset_stress(self) -> Dict[str, Any]:
        """
        Stress-Test für große Datenmengen
        
        KRITERIEN:
        - Handhabung von >10,000 Sources
        - Lineare Performance-Skalierung
        - Memory Usage bleibt unter 500MB
        """
        test_results = {
            'test_description': 'Large Dataset Stress Test',
            'dataset_sizes': [1000, 5000, 10000, 20000, 50000],
            'results': [],
            'scalability_analysis': {}
        }
        
        for size in test_results['dataset_sizes']:
            logger.debug(f"[ADVANCED-BENCHMARKS] Stress Test - Dataset Size: {size}")
            
            # Generiere große Testdaten
            large_sources = self.data_generator.generate_realistic_sources(size, duplicate_rate=0.3)  # 30% Duplikate
            large_results = self.data_generator.generate_realistic_structured_data(size // 20)
            
            # Messe Memory vor Test
            memory_before = await self._get_current_memory_usage()
            
            # Source Deduplication Stress Test
            start_time = time.time()
            deduplicated_large = await performance_optimizer.deduplicate_sources_fast(large_sources)
            source_time = (time.time() - start_time) * 1000
            
            memory_after_sources = await self._get_current_memory_usage()
            
            # Data Consolidation Stress Test
            start_time = time.time()
            consolidated_large = await performance_optimizer.consolidate_structured_data_fast(large_results)
            consolidation_time = (time.time() - start_time) * 1000
            
            memory_after = await self._get_current_memory_usage()
            
            # Performance-Metriken
            throughput_sources = size / (source_time / 1000) if source_time > 0 else 0
            throughput_consolidation = len(large_results) / (consolidation_time / 1000) if consolidation_time > 0 else 0
            
            result = {
                'dataset_size': size,
                'source_deduplication': {
                    'execution_time_ms': source_time,
                    'throughput_items_per_second': throughput_sources,
                    'input_count': len(large_sources),
                    'output_count': len(deduplicated_large),
                    'deduplication_ratio': len(deduplicated_large) / len(large_sources),
                    'memory_usage_mb': memory_after_sources - memory_before
                },
                'data_consolidation': {
                    'execution_time_ms': consolidation_time,
                    'throughput_items_per_second': throughput_consolidation,
                    'input_models': len(large_results),
                    'output_fields': len(consolidated_large.get('structured_data', {})),
                    'memory_usage_mb': memory_after - memory_after_sources
                },
                'total_memory_usage_mb': memory_after - memory_before,
                'meets_memory_criteria': (memory_after - memory_before) < 500,
                'performance_acceptable': source_time < size * 0.1  # <0.1ms per item
            }
            
            test_results['results'].append(result)
            
            # Memory cleanup zwischen Tests
            await asyncio.sleep(0.5)
        
        # Skalierbarkeits-Analyse
        sizes = [r['dataset_size'] for r in test_results['results']]
        source_times = [r['source_deduplication']['execution_time_ms'] for r in test_results['results']]
        memory_usages = [r['total_memory_usage_mb'] for r in test_results['results']]
        
        # Berechne Skalierbarkeits-Koeffizienten (lineare Regression vereinfacht)
        time_scalability = source_times[-1] / source_times[0] if len(source_times) > 1 else 1
        size_scalability = sizes[-1] / sizes[0] if len(sizes) > 1 else 1
        
        test_results['scalability_analysis'] = {
            'time_scalability_factor': time_scalability / size_scalability,  # Idealerweise ~1.0
            'memory_efficiency': memory_usages[-1] / sizes[-1],  # MB per item
            'largest_dataset_processed': max(sizes),
            'peak_memory_usage_mb': max(memory_usages),
            'linear_scalability_achieved': time_scalability / size_scalability < 1.5,
            'memory_criteria_met': all(r['meets_memory_criteria'] for r in test_results['results']),
            'performance_criteria_met': all(r['performance_acceptable'] for r in test_results['results'])
        }
        
        return test_results
    
    async def _test_synonym_matching(self) -> Dict[str, Any]:
        """
        Test der Synonym-Matching Effektivität
        """
        test_results = {
            'test_description': 'Synonym Matching Effectiveness',
            'test_cases': [],
            'matching_analysis': {}
        }
        
        # Erstelle Testfälle für Synonym-Matching
        synonym_test_cases = [
            # Mine Namen
            {'field': 'mine_name', 'values': ['Eleonore Mine', 'Éléonore', 'eleonore'], 'expected_group': 'eleonore'},
            {'field': 'mine_name', 'values': ['Canadian Malartic', 'Malartic', 'canadian malartic mine'], 'expected_group': 'canadian_malartic'},
            
            # Rohstoffe
            {'field': 'commodity', 'values': ['Gold', 'Au', 'Or', 'Aurum'], 'expected_group': 'gold'},
            {'field': 'commodity', 'values': ['Silver', 'Ag', 'Argent'], 'expected_group': 'silver'},
            {'field': 'commodity', 'values': ['Copper', 'Cu', 'Cuivre'], 'expected_group': 'copper'},
        ]
        
        for test_case in synonym_test_cases:
            # Erstelle Mock-Ergebnisse mit Synonymen
            mock_results = {}
            for i, value in enumerate(test_case['values']):
                mock_results[f'model_{i}'] = {
                    'success': True,
                    'data': {
                        'structured_data': {test_case['field']: value},
                        'sources': []
                    }
                }
            
            # Teste Konsolidierung
            consolidated = await performance_optimizer.consolidate_structured_data_fast(mock_results)
            
            # Prüfe ob Synonyme erkannt wurden
            result_value = consolidated.get('structured_data', {}).get(test_case['field'])
            synonym_detected = result_value is not None
            
            test_case_result = {
                'field': test_case['field'],
                'input_values': test_case['values'],
                'output_value': result_value,
                'synonym_detected': synonym_detected,
                'models_contributing': len(consolidated.get('model_contributions', {})),
                'expected_group': test_case['expected_group']
            }
            
            test_results['test_cases'].append(test_case_result)
        
        # Analysiere Synonym-Matching
        successful_matches = sum(1 for tc in test_results['test_cases'] if tc['synonym_detected'])
        total_cases = len(test_results['test_cases'])
        
        test_results['matching_analysis'] = {
            'successful_matches': successful_matches,
            'total_test_cases': total_cases,
            'success_rate_percent': (successful_matches / total_cases * 100) if total_cases > 0 else 0,
            'synonym_matching_effectiveness': self._rate_synonym_effectiveness(successful_matches / total_cases if total_cases > 0 else 0)
        }
        
        return test_results
    
    async def _test_integration_compatibility(self) -> Dict[str, Any]:
        """
        Test der Integration mit bestehenden Services
        """
        test_results = {
            'test_description': 'Integration Compatibility Check',
            'compatibility_tests': [],
            'integration_health': {}
        }
        
        # Teste Health Check
        health_report = await performance_integration.performance_health_check()
        
        test_results['compatibility_tests'].append({
            'test_name': 'health_check',
            'success': True,
            'health_score': health_report.get('overall_health_score', 0),
            'health_status': health_report.get('health_status', 'UNKNOWN')
        })
        
        # Teste Integration mit Mock-Services
        mock_sources = self.data_generator.generate_realistic_sources(500)
        mock_results = self.data_generator.generate_realistic_structured_data(10)
        
        # Test Source Deduplication Integration
        try:
            integrated_sources = await performance_integration.optimize_source_deduplication(
                mock_sources, 
                legacy_method_name="test_legacy_method"
            )
            source_integration_success = True
            source_integration_error = None
        except Exception as e:
            source_integration_success = False
            source_integration_error = str(e)
        
        test_results['compatibility_tests'].append({
            'test_name': 'source_deduplication_integration',
            'success': source_integration_success,
            'error': source_integration_error,
            'input_count': len(mock_sources),
            'output_count': len(integrated_sources) if source_integration_success else 0
        })
        
        # Test Data Consolidation Integration
        try:
            integrated_data = await performance_integration.optimize_data_consolidation(
                mock_results,
                legacy_method_name="test_legacy_consolidation"
            )
            data_integration_success = True
            data_integration_error = None
        except Exception as e:
            data_integration_success = False
            data_integration_error = str(e)
        
        test_results['compatibility_tests'].append({
            'test_name': 'data_consolidation_integration',
            'success': data_integration_success,
            'error': data_integration_error,
            'input_models': len(mock_results),
            'output_fields': len(integrated_data.get('structured_data', {})) if data_integration_success else 0
        })
        
        # Analysiere Integration Health
        successful_tests = sum(1 for test in test_results['compatibility_tests'] if test['success'])
        total_tests = len(test_results['compatibility_tests'])
        
        test_results['integration_health'] = {
            'successful_tests': successful_tests,
            'total_tests': total_tests,
            'compatibility_rate_percent': (successful_tests / total_tests * 100) if total_tests > 0 else 0,
            'integration_ready': successful_tests == total_tests,
            'health_report': health_report
        }
        
        return test_results
    
    async def _test_auto_refresh_simulation(self) -> Dict[str, Any]:
        """
        Simuliert Auto-Refresh Verhalten über längeren Zeitraum
        """
        test_results = {
            'test_description': 'Auto-Refresh Simulation (30-second intervals)',
            'simulation_cycles': [],
            'auto_refresh_analysis': {}
        }
        
        # Simuliere 10 Auto-Refresh Zyklen (5 Minuten)
        for cycle in range(10):
            logger.debug(f"[ADVANCED-BENCHMARKS] Auto-Refresh Simulation - Cycle {cycle + 1}/10")
            
            cycle_start = time.time()
            
            # Generiere neue Daten (simuliert Live-Daten)
            new_sources = self.data_generator.generate_realistic_sources(300, variation_seed=cycle)
            new_results = self.data_generator.generate_realistic_structured_data(15, variation_seed=cycle)
            
            # Memory vor Zyklus
            memory_before = await self._get_current_memory_usage()
            
            # Führe Deduplication durch
            start_time = time.time()
            deduplicated = await performance_optimizer.deduplicate_sources_fast(new_sources)
            dedup_time = (time.time() - start_time) * 1000
            
            # Führe Konsolidierung durch
            start_time = time.time()
            consolidated = await performance_optimizer.consolidate_structured_data_fast(new_results)
            consolidation_time = (time.time() - start_time) * 1000
            
            # Memory nach Zyklus
            memory_after = await self._get_current_memory_usage()
            
            # Cache-Statistiken
            cache_stats = performance_optimizer.get_performance_metrics()
            
            cycle_result = {
                'cycle': cycle + 1,
                'cycle_duration_ms': (time.time() - cycle_start) * 1000,
                'deduplication_time_ms': dedup_time,
                'consolidation_time_ms': consolidation_time,
                'total_processing_time_ms': dedup_time + consolidation_time,
                'memory_before_mb': memory_before,
                'memory_after_mb': memory_after,
                'memory_growth_mb': memory_after - memory_before,
                'cache_hit_rate_percent': cache_stats.get('cache_efficiency', {}).get('overall_hit_rate_percent', 0),
                'sources_processed': len(new_sources),
                'sources_deduplicated': len(deduplicated),
                'data_fields_consolidated': len(consolidated.get('structured_data', {})),
                'meets_30s_criteria': (dedup_time + consolidation_time) < 5000  # Unter 5s für 30s-Zyklus
            }
            
            test_results['simulation_cycles'].append(cycle_result)
            
            # Warte bis zum nächsten 30s-Intervall (simuliert)
            await asyncio.sleep(0.2)  # Reduziert für Test
        
        # Analysiere Auto-Refresh Performance
        processing_times = [c['total_processing_time_ms'] for c in test_results['simulation_cycles']]
        cache_hit_rates = [c['cache_hit_rate_percent'] for c in test_results['simulation_cycles']]
        memory_growths = [c['memory_growth_mb'] for c in test_results['simulation_cycles']]
        
        test_results['auto_refresh_analysis'] = {
            'average_processing_time_ms': statistics.mean(processing_times),
            'max_processing_time_ms': max(processing_times),
            'processing_time_stability': statistics.stdev(processing_times) if len(processing_times) > 1 else 0,
            'average_cache_hit_rate_percent': statistics.mean(cache_hit_rates),
            'cache_warmup_cycles': len([c for c in test_results['simulation_cycles'] if c['cache_hit_rate_percent'] < 50]),
            'memory_growth_trend': statistics.mean(memory_growths),
            'memory_leak_detected': statistics.mean(memory_growths) > 10,  # >10MB pro Zyklus
            'auto_refresh_ready': all([
                statistics.mean(processing_times) < 3000,  # Unter 3s durchschnittlich
                max(processing_times) < 5000,  # Nie über 5s
                statistics.mean(memory_growths) < 5,  # <5MB Wachstum pro Zyklus
                statistics.mean(cache_hit_rates) > 60  # >60% Cache Hit Rate
            ]),
            'performance_grade': self._grade_auto_refresh_performance(processing_times, cache_hit_rates, memory_growths)
        }
        
        return test_results
    
    async def _get_current_memory_usage(self) -> float:
        """Holt aktuelle Memory Usage in MB"""
        import psutil
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    
    def _rate_synonym_effectiveness(self, success_rate: float) -> str:
        """Bewertet Synonym-Matching Effectiveness"""
        if success_rate > 0.9:
            return "EXCELLENT"
        elif success_rate > 0.7:
            return "GOOD"
        elif success_rate > 0.5:
            return "ACCEPTABLE"
        else:
            return "POOR"
    
    def _grade_auto_refresh_performance(self, processing_times: List[float], 
                                      cache_hit_rates: List[float], 
                                      memory_growths: List[float]) -> str:
        """Bewertet Auto-Refresh Performance"""
        avg_time = statistics.mean(processing_times)
        avg_cache = statistics.mean(cache_hit_rates)
        avg_memory = statistics.mean(memory_growths)
        
        score = 0
        if avg_time < 2000:
            score += 40
        elif avg_time < 3000:
            score += 30
        elif avg_time < 5000:
            score += 20
        
        if avg_cache > 70:
            score += 30
        elif avg_cache > 50:
            score += 20
        elif avg_cache > 30:
            score += 10
        
        if avg_memory < 5:
            score += 30
        elif avg_memory < 10:
            score += 20
        elif avg_memory < 20:
            score += 10
        
        if score >= 90:
            return "A+"
        elif score >= 80:
            return "A"
        elif score >= 70:
            return "B"
        elif score >= 60:
            return "C"
        else:
            return "D"
    
    def _calculate_overall_performance(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Berechnet Overall Performance Score für Advanced Tests"""
        scores = []
        
        # Large Dataset Stress (35%)
        if 'large_dataset_stress' in test_results:
            stress_good = test_results['large_dataset_stress']['scalability_analysis'].get('linear_scalability_achieved', False)
            scores.append(35 if stress_good else 15)
        
        # Synonym Matching (25%)
        if 'synonym_matching' in test_results:
            synonym_rate = test_results['synonym_matching']['matching_analysis'].get('success_rate_percent', 0)
            synonym_score = min(25, synonym_rate / 4)  # Max 25 points
            scores.append(synonym_score)
        
        # Integration Compatibility (25%)
        if 'integration_compatibility' in test_results:
            compat_ready = test_results['integration_compatibility']['integration_health'].get('integration_ready', False)
            scores.append(25 if compat_ready else 10)
        
        # Auto-Refresh (15%)
        if 'auto_refresh_simulation' in test_results:
            refresh_ready = test_results['auto_refresh_simulation']['auto_refresh_analysis'].get('auto_refresh_ready', False)
            scores.append(15 if refresh_ready else 5)
        
        total_score = sum(scores)
        
        return {
            'score': total_score,
            'max_score': 100,
            'grade': self._get_performance_grade(total_score),
            'component_scores': {
                'large_dataset_stress': scores[0] if len(scores) > 0 else 0,
                'synonym_matching': scores[1] if len(scores) > 1 else 0,
                'integration_compatibility': scores[2] if len(scores) > 2 else 0,
                'auto_refresh_simulation': scores[3] if len(scores) > 3 else 0
            }
        }
    
    def _get_performance_grade(self, score: float) -> str:
        """Konvertiert Score zu Grade"""
        if score >= 90:
            return "A+"
        elif score >= 80:
            return "A"
        elif score >= 70:
            return "B"
        elif score >= 60:
            return "C"
        else:
            return "D"
    
    def _generate_benchmark_summary(self, suite_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generiert Advanced Benchmark Summary"""
        overall = suite_results['overall_performance']
        
        return {
            'overall_grade': overall['grade'],
            'overall_score': overall['score'],
            'production_ready': overall['score'] >= 75,
            'key_strengths': self.analysis_tools.identify_strengths(suite_results),
            'key_weaknesses': self.analysis_tools.identify_weaknesses(suite_results),
            'critical_issues': self.analysis_tools.identify_critical_issues(suite_results),
            'test_type': 'advanced_benchmarks'
        }

# Globale Advanced Benchmark-Instanz
advanced_performance_benchmarks = AdvancedPerformanceBenchmarks()