"""
Author: rahn
Datum: 06.08.2025
Version: 1.0
Beschreibung: Core Performance Benchmarks - Basis-Funktionalitäten (Refactored aus performance_benchmarks.py)
ÄNDERUNG 06.08.2025: Refactoring gemäß REGEL 1 - Datei-Größenbeschränkung unter 500 Zeilen
"""

import logging
import asyncio
import time
import statistics
from typing import Dict, List, Any, Tuple
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict

from performance_optimizer import performance_optimizer
from performance_integration import performance_integration

logger = logging.getLogger(__name__)

@dataclass
class BenchmarkResult:
    """Datenklasse für einzelne Benchmark-Ergebnisse"""
    test_name: str
    dataset_size: int
    execution_time_ms: float
    throughput_items_per_second: float
    memory_usage_mb: float
    cache_hit_rate_percent: float
    deduplication_ratio: float
    success_rate_percent: float
    performance_grade: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class CorePerformanceBenchmarks:
    """
    Basis Performance-Benchmarks für das Deduplication-System
    
    KERN-TESTSZENARIEN:
    1. Real-Time Performance (30-Sekunden Auto-Refresh)
    2. Memory Efficiency Tests
    3. Cache Performance Analysis
    """
    
    def __init__(self, output_dir: str = "/app/minesearch_v2/backend/benchmark_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.benchmark_results: List[BenchmarkResult] = []
        self.test_data_cache = {}
        
        logger.info(f"[CORE-BENCHMARKS] Core Benchmark Suite initialisiert - Output: {self.output_dir}")
    
    async def run_core_benchmark_suite(self) -> Dict[str, Any]:
        """
        Führt Kern-Benchmark-Suite durch
        
        Returns:
            Basis-Benchmark-Bericht
        """
        logger.info("[CORE-BENCHMARKS] Starte Kern-Benchmark-Suite...")
        start_time = datetime.now()
        
        suite_results = {
            'benchmark_timestamp': start_time.isoformat(),
            'system_info': await self._collect_system_info(),
            'test_results': {},
            'overall_performance': {},
            'summary': {}
        }
        
        # Test 1: Real-Time Performance Test
        logger.info("[CORE-BENCHMARKS] Test 1: Real-Time Performance")
        suite_results['test_results']['real_time_performance'] = await self._test_real_time_performance()
        
        # Test 2: Memory Efficiency Analysis
        logger.info("[CORE-BENCHMARKS] Test 2: Memory Efficiency Analysis")
        suite_results['test_results']['memory_efficiency'] = await self._test_memory_efficiency()
        
        # Test 3: Cache Performance Deep Dive
        logger.info("[CORE-BENCHMARKS] Test 3: Cache Performance Deep Dive")
        suite_results['test_results']['cache_performance'] = await self._test_cache_performance()
        
        # Berechne Overall Performance
        overall_performance = self._calculate_overall_performance(suite_results['test_results'])
        suite_results['overall_performance'] = overall_performance
        
        # Generiere Summary
        summary = self._generate_benchmark_summary(suite_results)
        suite_results['summary'] = summary
        
        end_time = datetime.now()
        suite_results['total_benchmark_duration_seconds'] = (end_time - start_time).total_seconds()
        
        logger.info(f"[CORE-BENCHMARKS] Kern-Benchmark-Suite abgeschlossen: {overall_performance['grade']} "
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
    
    async def _test_real_time_performance(self) -> Dict[str, Any]:
        """
        Test für Real-Time Performance Requirements (30-Sekunden Zyklus)
        
        KRITERIEN:
        - Deduplication muss unter 5 Sekunden für typische Datasets
        - Memory Usage konstant bei wiederholten Operationen
        - Cache Hit Rate >70% nach Warm-up Phase
        """
        test_results = {
            'test_description': 'Real-Time Performance für 30-Sekunden Auto-Refresh',
            'test_criteria': {
                'max_deduplication_time_ms': 5000,
                'min_cache_hit_rate_percent': 70,
                'max_memory_growth_mb': 50
            },
            'iterations': [],
            'performance_analysis': {}
        }
        
        # Simuliere typische Real-Time Datenmengen
        dataset_sizes = [100, 250, 500, 750, 1000]  # Realistische Größen für 30s-Intervalle
        
        for size in dataset_sizes:
            logger.debug(f"[CORE-BENCHMARKS] Real-Time Test - Dataset Size: {size}")
            
            # Generiere Testdaten
            from performance_benchmarks_utils import BenchmarkDataGenerator
            generator = BenchmarkDataGenerator()
            
            test_sources = generator.generate_realistic_sources(size)
            test_results_data = generator.generate_realistic_structured_data(size // 10)
            
            # Messe Performance über mehrere Zyklen
            iteration_results = []
            for cycle in range(5):  # 5 Zyklen simulieren 2.5 Minuten Auto-Refresh
                start_memory = await self._get_current_memory_usage()
                
                # Source Deduplication Test
                start_time = time.time()
                deduplicated_sources = await performance_optimizer.deduplicate_sources_fast(test_sources)
                source_dedup_time = (time.time() - start_time) * 1000
                
                # Data Consolidation Test
                start_time = time.time()
                consolidated_data = await performance_optimizer.consolidate_structured_data_fast(test_results_data)
                consolidation_time = (time.time() - start_time) * 1000
                
                end_memory = await self._get_current_memory_usage()
                
                # Cache-Statistiken
                cache_stats = performance_optimizer.get_performance_metrics()
                cache_hit_rate = cache_stats.get('cache_efficiency', {}).get('overall_hit_rate_percent', 0)
                
                iteration_result = {
                    'cycle': cycle,
                    'dataset_size': size,
                    'source_deduplication_time_ms': source_dedup_time,
                    'data_consolidation_time_ms': consolidation_time,
                    'total_time_ms': source_dedup_time + consolidation_time,
                    'memory_usage_start_mb': start_memory,
                    'memory_usage_end_mb': end_memory,
                    'memory_growth_mb': end_memory - start_memory,
                    'cache_hit_rate_percent': cache_hit_rate,
                    'meets_time_criteria': (source_dedup_time + consolidation_time) < 5000,
                    'meets_cache_criteria': cache_hit_rate > 70 or cycle < 2,  # Allow warmup
                    'deduplicated_count': len(deduplicated_sources),
                    'deduplication_ratio': len(deduplicated_sources) / len(test_sources) if test_sources else 1
                }
                
                iteration_results.append(iteration_result)
                
                # Kurze Pause zwischen Zyklen
                await asyncio.sleep(0.1)
            
            test_results['iterations'].extend(iteration_results)
        
        # Analysiere Gesamtperformance
        all_times = [it['total_time_ms'] for it in test_results['iterations']]
        all_cache_rates = [it['cache_hit_rate_percent'] for it in test_results['iterations'] if it['cycle'] >= 2]
        memory_growths = [it['memory_growth_mb'] for it in test_results['iterations']]
        
        test_results['performance_analysis'] = {
            'average_total_time_ms': statistics.mean(all_times),
            'max_total_time_ms': max(all_times),
            'min_total_time_ms': min(all_times),
            'average_cache_hit_rate_percent': statistics.mean(all_cache_rates) if all_cache_rates else 0,
            'average_memory_growth_mb': statistics.mean(memory_growths),
            'max_memory_growth_mb': max(memory_growths),
            'time_criteria_pass_rate': sum(1 for it in test_results['iterations'] if it['meets_time_criteria']) / len(test_results['iterations']) * 100,
            'cache_criteria_pass_rate': sum(1 for it in test_results['iterations'] if it['meets_cache_criteria']) / len(test_results['iterations']) * 100,
            'overall_real_time_ready': all([
                statistics.mean(all_times) < 3000,  # Unter 3s durchschnittlich
                max(all_times) < 5000,  # Nie über 5s
                statistics.mean(all_cache_rates) > 70 if all_cache_rates else True,
                max(memory_growths) < 50
            ])
        }
        
        return test_results
    
    async def _test_memory_efficiency(self) -> Dict[str, Any]:
        """Detaillierte Memory Efficiency Analysis"""
        test_results = {
            'test_description': 'Memory Efficiency Analysis',
            'memory_tracking': [],
            'efficiency_metrics': {}
        }
        
        # Baseline Memory
        baseline_memory = await self._get_current_memory_usage()
        
        # Teste Memory Usage bei verschiedenen Cache-Größen
        cache_sizes = [1000, 5000, 10000, 20000]
        
        for cache_size in cache_sizes:
            # Erstelle neuen Optimizer mit spezifischer Cache-Größe
            from performance_optimizer import FastDeduplicationEngine
            test_optimizer = FastDeduplicationEngine(cache_size=cache_size)
            
            # Fülle Cache mit Testdaten
            from performance_benchmarks_utils import BenchmarkDataGenerator
            generator = BenchmarkDataGenerator()
            
            for i in range(cache_size):
                test_sources = generator.generate_realistic_sources(100)
                await test_optimizer.deduplicate_sources_fast(test_sources)
            
            current_memory = await self._get_current_memory_usage()
            memory_usage = current_memory - baseline_memory
            
            test_results['memory_tracking'].append({
                'cache_size': cache_size,
                'memory_usage_mb': memory_usage,
                'memory_per_cache_item_kb': (memory_usage * 1024) / cache_size if cache_size > 0 else 0
            })
        
        # Analysiere Memory Efficiency
        memory_data = test_results['memory_tracking']
        avg_memory_per_item = statistics.mean([m['memory_per_cache_item_kb'] for m in memory_data])
        
        test_results['efficiency_metrics'] = {
            'average_memory_per_cache_item_kb': avg_memory_per_item,
            'memory_efficiency_rating': self._rate_memory_efficiency(avg_memory_per_item),
            'memory_scalability_linear': self._check_memory_linearity(memory_data),
            'optimal_cache_size_recommendation': self._recommend_optimal_cache_size(memory_data)
        }
        
        return test_results
    
    async def _test_cache_performance(self) -> Dict[str, Any]:
        """Umfassende Cache Performance Analysis"""
        test_results = {
            'test_description': 'Cache Performance Deep Dive',
            'cache_scenarios': [],
            'cache_analysis': {}
        }
        
        # Verschiedene Cache-Szenarien testen
        scenarios = [
            {'name': 'cold_start', 'description': 'Cache Cold Start Performance'},
            {'name': 'warm_cache', 'description': 'Warmed Cache Performance'}
        ]
        
        for scenario in scenarios:
            scenario_result = await self._run_cache_scenario(scenario)
            test_results['cache_scenarios'].append(scenario_result)
        
        # Gesamtanalyse
        hit_rates = [s['cache_hit_rate_percent'] for s in test_results['cache_scenarios']]
        performance_gains = [s['performance_gain_percent'] for s in test_results['cache_scenarios']]
        
        test_results['cache_analysis'] = {
            'average_hit_rate_percent': statistics.mean(hit_rates),
            'average_performance_gain_percent': statistics.mean(performance_gains),
            'cache_effectiveness_rating': self._rate_cache_effectiveness(statistics.mean(hit_rates)),
            'cache_optimization_potential': 100 - statistics.mean(hit_rates)
        }
        
        return test_results
    
    async def _get_current_memory_usage(self) -> float:
        """Holt aktuelle Memory Usage in MB"""
        import psutil
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    
    async def _run_cache_scenario(self, scenario: Dict[str, str]) -> Dict[str, Any]:
        """Führt spezifisches Cache-Szenario durch"""
        from performance_benchmarks_utils import BenchmarkDataGenerator
        generator = BenchmarkDataGenerator()
        scenario_name = scenario['name']
        
        if scenario_name == 'cold_start':
            # Clear cache und teste Performance
            performance_optimizer._url_hash_cache.clear()
            performance_optimizer._content_hash_cache.clear()
            performance_optimizer._consolidated_data_cache.clear()
            
            test_sources = generator.generate_realistic_sources(1000)
            start_time = time.time()
            await performance_optimizer.deduplicate_sources_fast(test_sources)
            execution_time = (time.time() - start_time) * 1000
            
            return {
                'scenario': scenario_name,
                'execution_time_ms': execution_time,
                'cache_hit_rate_percent': 0,  # Cold start
                'performance_gain_percent': 0  # Baseline
            }
        
        elif scenario_name == 'warm_cache':
            # Fülle Cache und teste warme Performance
            warm_sources = generator.generate_realistic_sources(500)
            # Einmal durchlaufen zum Aufwärmen
            await performance_optimizer.deduplicate_sources_fast(warm_sources)
            
            # Jetzt testen mit teilweise gecachten Daten
            start_time = time.time()
            await performance_optimizer.deduplicate_sources_fast(warm_sources)
            execution_time = (time.time() - start_time) * 1000
            
            cache_stats = performance_optimizer.get_performance_metrics()
            cache_hit_rate = cache_stats.get('cache_efficiency', {}).get('overall_hit_rate_percent', 0)
            
            return {
                'scenario': scenario_name,
                'execution_time_ms': execution_time,
                'cache_hit_rate_percent': cache_hit_rate,
                'performance_gain_percent': max(0, (200 - execution_time) / 200 * 100)  # Gegen 200ms Baseline
            }
        
        # Default
        return {
            'scenario': scenario_name,
            'execution_time_ms': 0,
            'cache_hit_rate_percent': 0,
            'performance_gain_percent': 0
        }
    
    def _rate_memory_efficiency(self, memory_per_item_kb: float) -> str:
        """Bewertet Memory Efficiency"""
        if memory_per_item_kb < 1:
            return "EXCELLENT"
        elif memory_per_item_kb < 5:
            return "GOOD"
        elif memory_per_item_kb < 10:
            return "ACCEPTABLE"
        else:
            return "POOR"
    
    def _check_memory_linearity(self, memory_data: List[Dict]) -> bool:
        """Prüft ob Memory Usage linear skaliert"""
        if len(memory_data) < 2:
            return True
        
        # Einfache Linearitätsprüfung
        ratios = []
        for i in range(1, len(memory_data)):
            size_ratio = memory_data[i]['cache_size'] / memory_data[i-1]['cache_size']
            memory_ratio = memory_data[i]['memory_usage_mb'] / memory_data[i-1]['memory_usage_mb']
            ratios.append(abs(size_ratio - memory_ratio))
        
        avg_deviation = statistics.mean(ratios)
        return avg_deviation < 0.5  # Akzeptable Abweichung
    
    def _recommend_optimal_cache_size(self, memory_data: List[Dict]) -> int:
        """Empfiehlt optimale Cache-Größe basierend auf Memory Efficiency"""
        if not memory_data:
            return 10000  # Default
        
        # Finde Cache-Größe mit bester Memory Efficiency
        best_efficiency = float('inf')
        optimal_size = 10000
        
        for data in memory_data:
            efficiency = data['memory_per_cache_item_kb']
            if efficiency < best_efficiency:
                best_efficiency = efficiency
                optimal_size = data['cache_size']
        
        return optimal_size
    
    def _rate_cache_effectiveness(self, hit_rate: float) -> str:
        """Bewertet Cache Effectiveness"""
        if hit_rate > 80:
            return "EXCELLENT"
        elif hit_rate > 60:
            return "GOOD"
        elif hit_rate > 40:
            return "ACCEPTABLE"
        else:
            return "POOR"
    
    def _calculate_overall_performance(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Berechnet Overall Performance Score (vereinfacht für Core Tests)"""
        scores = []
        
        # Real-Time Performance (40%)
        if 'real_time_performance' in test_results:
            rt_ready = test_results['real_time_performance']['performance_analysis'].get('overall_real_time_ready', False)
            scores.append(40 if rt_ready else 20)
        
        # Memory Efficiency (30%)
        if 'memory_efficiency' in test_results:
            mem_rating = test_results['memory_efficiency']['efficiency_metrics'].get('memory_efficiency_rating', 'POOR')
            mem_score = {'EXCELLENT': 30, 'GOOD': 24, 'ACCEPTABLE': 18, 'POOR': 12}.get(mem_rating, 12)
            scores.append(mem_score)
        
        # Cache Performance (30%)
        if 'cache_performance' in test_results:
            cache_rating = test_results['cache_performance']['cache_analysis'].get('cache_effectiveness_rating', 'POOR')
            cache_score = {'EXCELLENT': 30, 'GOOD': 24, 'ACCEPTABLE': 18, 'POOR': 12}.get(cache_rating, 12)
            scores.append(cache_score)
        
        total_score = sum(scores)
        
        return {
            'score': total_score,
            'max_score': 100,
            'grade': self._get_performance_grade(total_score)
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
        """Generiert Core Benchmark Summary"""
        overall = suite_results['overall_performance']
        
        return {
            'overall_grade': overall['grade'],
            'overall_score': overall['score'],
            'production_ready': overall['score'] >= 75,
            'test_type': 'core_benchmarks'
        }

# Globale Core Benchmark-Instanz
core_performance_benchmarks = CorePerformanceBenchmarks()