"""
Author: rahn
Datum: 06.08.2025
Version: 2.0
Beschreibung: Performance Benchmarks Orchestrator - Koordiniert alle Benchmark-Tests
ÄNDERUNG 06.08.2025: Refactoring gemäß REGEL 1 - Orchestrator-Pattern implementiert
"""

import logging
import asyncio
from typing import Dict, List, Any
from datetime import datetime
from pathlib import Path

# Refactored Module imports
from performance_benchmarks_core import CorePerformanceBenchmarks, BenchmarkResult
from performance_benchmarks_advanced import AdvancedPerformanceBenchmarks
from performance_benchmarks_utils import BenchmarkReportGenerator, BenchmarkAnalysisTools

logger = logging.getLogger(__name__)

class ComprehensivePerformanceBenchmarks:
    """
    Orchestrator für umfassende Performance-Benchmarks
    
    KOORDINIERT:
    1. Core Performance Tests (Real-Time, Memory, Cache)
    2. Advanced Performance Tests (Large Dataset, Synonym Matching, Integration, Auto-Refresh)
    3. Unified Reporting und Analysis
    """
    
    def __init__(self, output_dir: str = "/app/minesearch_v2/backend/benchmark_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize refactored components
        self.core_benchmarks = CorePerformanceBenchmarks(str(self.output_dir))
        self.advanced_benchmarks = AdvancedPerformanceBenchmarks(str(self.output_dir))
        self.report_generator = BenchmarkReportGenerator(str(self.output_dir))
        self.analysis_tools = BenchmarkAnalysisTools()
        
        self.benchmark_results: List[BenchmarkResult] = []
        
        logger.info(f"[PERF-ORCHESTRATOR] Comprehensive Benchmark Orchestrator initialisiert - Output: {self.output_dir}")
    
    async def run_comprehensive_benchmark_suite(self) -> Dict[str, Any]:
        """
        Orchestriert komplette Benchmark-Suite durch alle Module
        
        Returns:
            Umfassender Benchmark-Bericht mit Core + Advanced Tests
        """
        logger.info("[PERF-ORCHESTRATOR] Starte umfassende Benchmark-Suite...")
        start_time = datetime.now()
        
        # Führe Core Benchmarks durch
        logger.info("[PERF-ORCHESTRATOR] Phase 1: Core Performance Tests")
        core_results = await self.core_benchmarks.run_core_benchmark_suite()
        
        # Führe Advanced Benchmarks durch
        logger.info("[PERF-ORCHESTRATOR] Phase 2: Advanced Performance Tests")
        advanced_results = await self.advanced_benchmarks.run_advanced_benchmark_suite()
        
        # Kombiniere Ergebnisse
        combined_results = self._combine_benchmark_results(core_results, advanced_results)
        
        # Unified Analysis
        overall_performance = self._calculate_unified_performance(combined_results)
        combined_results['overall_performance'] = overall_performance
        
        # Unified Summary
        summary = self._generate_unified_summary(combined_results)
        combined_results['summary'] = summary
        combined_results['recommendations'] = self.analysis_tools.generate_performance_recommendations(combined_results)
        
        # Speichere kombinierte Ergebnisse
        end_time = datetime.now()
        combined_results['total_benchmark_duration_seconds'] = (end_time - start_time).total_seconds()
        
        await self.report_generator.save_benchmark_results(combined_results, "comprehensive_benchmark")
        
        logger.info(f"[PERF-ORCHESTRATOR] Comprehensive Benchmark-Suite abgeschlossen: {overall_performance['grade']} "
                   f"({overall_performance['score']}/100)")
        
        return combined_results
    
    def _combine_benchmark_results(self, core_results: Dict[str, Any], advanced_results: Dict[str, Any]) -> Dict[str, Any]:
        """Kombiniert Core und Advanced Benchmark Ergebnisse"""
        combined = {
            'benchmark_timestamp': datetime.now().isoformat(),
            'system_info': core_results.get('system_info', {}),
            'test_results': {},
            'test_phases': {
                'core_phase': core_results,
                'advanced_phase': advanced_results
            }
        }
        
        # Kombiniere alle Test-Ergebnisse
        combined['test_results'].update(core_results.get('test_results', {}))
        combined['test_results'].update(advanced_results.get('test_results', {}))
        
        return combined
    
    def _calculate_unified_performance(self, combined_results: Dict[str, Any]) -> Dict[str, Any]:
        """Berechnet unified Performance Score über alle Tests"""
        test_results = combined_results['test_results']
        
        # Core Tests (50% Gewichtung)
        core_score = 0
        
        # Real-Time Performance (20%)
        if 'real_time_performance' in test_results:
            rt_ready = test_results['real_time_performance']['performance_analysis'].get('overall_real_time_ready', False)
            core_score += 20 if rt_ready else 10
        
        # Memory Efficiency (15%)
        if 'memory_efficiency' in test_results:
            mem_rating = test_results['memory_efficiency']['efficiency_metrics'].get('memory_efficiency_rating', 'POOR')
            mem_score = {'EXCELLENT': 15, 'GOOD': 12, 'ACCEPTABLE': 9, 'POOR': 6}.get(mem_rating, 6)
            core_score += mem_score
        
        # Cache Performance (15%)
        if 'cache_performance' in test_results:
            cache_rating = test_results['cache_performance']['cache_analysis'].get('cache_effectiveness_rating', 'POOR')
            cache_score = {'EXCELLENT': 15, 'GOOD': 12, 'ACCEPTABLE': 9, 'POOR': 6}.get(cache_rating, 6)
            core_score += cache_score
        
        # Advanced Tests (50% Gewichtung)
        advanced_score = 0
        
        # Large Dataset Stress (20%)
        if 'large_dataset_stress' in test_results:
            stress_good = test_results['large_dataset_stress']['scalability_analysis'].get('linear_scalability_achieved', False)
            advanced_score += 20 if stress_good else 8
        
        # Synonym Matching (10%)
        if 'synonym_matching' in test_results:
            synonym_rate = test_results['synonym_matching']['matching_analysis'].get('success_rate_percent', 0)
            advanced_score += min(10, synonym_rate / 10)
        
        # Integration Compatibility (10%)
        if 'integration_compatibility' in test_results:
            compat_ready = test_results['integration_compatibility']['integration_health'].get('integration_ready', False)
            advanced_score += 10 if compat_ready else 4
        
        # Auto-Refresh (10%)
        if 'auto_refresh_simulation' in test_results:
            refresh_ready = test_results['auto_refresh_simulation']['auto_refresh_analysis'].get('auto_refresh_ready', False)
            advanced_score += 10 if refresh_ready else 4
        
        total_score = core_score + advanced_score
        
        return {
            'score': total_score,
            'max_score': 100,
            'grade': self._get_performance_grade(total_score),
            'core_component_score': core_score,
            'advanced_component_score': advanced_score,
            'test_breakdown': {
                'core_tests_weight': 50,
                'advanced_tests_weight': 50,
                'core_actual_score': core_score,
                'advanced_actual_score': advanced_score
            }
        }
    
    def _generate_unified_summary(self, combined_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generiert unified Summary über alle Tests"""
        overall = combined_results['overall_performance']
        
        return {
            'overall_grade': overall['grade'],
            'overall_score': overall['score'],
            'production_ready': overall['score'] >= 75,
            'core_component_score': overall['core_component_score'],
            'advanced_component_score': overall['advanced_component_score'],
            'key_strengths': self.analysis_tools.identify_strengths(combined_results),
            'key_weaknesses': self.analysis_tools.identify_weaknesses(combined_results),
            'critical_issues': self.analysis_tools.identify_critical_issues(combined_results),
            'test_coverage': {
                'core_tests_completed': len(combined_results['test_phases']['core_phase'].get('test_results', {})),
                'advanced_tests_completed': len(combined_results['test_phases']['advanced_phase'].get('test_results', {})),
                'total_tests_completed': len(combined_results['test_results'])
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
    
    # Backward Compatibility Methods
    async def run_core_tests_only(self) -> Dict[str, Any]:
        """Führt nur Core Performance Tests durch"""
        return await self.core_benchmarks.run_core_benchmark_suite()
    
    async def run_advanced_tests_only(self) -> Dict[str, Any]:
        """Führt nur Advanced Performance Tests durch"""
        return await self.advanced_benchmarks.run_advanced_benchmark_suite()

# Globale Benchmark-Instanz (Backward Compatibility)
performance_benchmarks = ComprehensivePerformanceBenchmarks()