"""
Author: rahn
Datum: 06.08.2025
Version: 1.0
Beschreibung: Performance Benchmark Utilities - Helper-Funktionen und Datengeneration
ÄNDERUNG 06.08.2025: Refactoring gemäß REGEL 1 - Ausgelagerte Utility-Funktionen
"""

import logging
import json
from typing import Dict, List, Any
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class BenchmarkDataGenerator:
    """
    Datengeneration für Performance-Tests
    """
    
    def __init__(self):
        self.base_domains = [
            'mining.com', 'miningglobal.com', 'miningweekly.com',
            'infomine.com', 'government.ca', 'quebec.ca',
            'mining-technology.com', 'resourceworld.com'
        ]
        
        self.mine_names = [
            'Eleonore', 'Canadian Malartic', 'Raglan', 'Lac Shortt',
            'Goldex', 'Lapa', 'Beaufor', 'Bousquet', 'Kiena'
        ]
        
        self.models = [
            'abacus:deep-agent', 'perplexity:sonar-reasoning-pro', 'perplexity:sonar-pro',
            'openrouter:claude-3.5-sonnet', 'openrouter:deepseek-free', 'openrouter:kimi-k2'
        ]
        
        self.mine_data_variants = [
            {'mine_name': 'Eleonore Mine', 'commodity': 'Gold', 'country': 'Canada', 'region': 'Quebec'},
            {'mine_name': 'Éléonore', 'commodity': 'Au', 'country': 'Canada', 'region': 'Québec'},
            {'mine_name': 'eleonore', 'commodity': 'Or', 'country': 'Canada', 'region': 'Quebec'}
        ]
    
    def generate_realistic_sources(self, count: int, duplicate_rate: float = 0.2, variation_seed: int = 0) -> List[Dict[str, Any]]:
        """Generiert realistische Source-Daten für Tests"""
        import random
        random.seed(variation_seed)
        
        sources = []
        
        for i in range(count):
            # Erstelle Duplikate basierend auf duplicate_rate
            if i > 0 and random.random() < duplicate_rate:
                # Dupliziere bestehende Source mit Variationen
                base_source = sources[random.randint(0, len(sources) - 1)]
                url = base_source['url'] + f'?ref={i}'  # Query-Parameter Variation
                title = base_source['title'] + f' - Update {i}'
            else:
                # Erstelle neue Source
                domain = random.choice(self.base_domains)
                mine = random.choice(self.mine_names)
                url = f'https://{domain}/mines/{mine.lower().replace(" ", "-")}-{i}'
                title = f'{mine} Mine Report {i}'
            
            sources.append({
                'url': url,
                'title': title,
                'content': f'Mining report content for {mine} with details about operations...',
                'score': 0.5 + random.random() * 0.5,
                'timestamp': f'2025-07-{28 - (i % 10):02d}T{10 + (i % 12):02d}:00:00Z'
            })
        
        return sources
    
    def generate_realistic_structured_data(self, model_count: int, variation_seed: int = 0) -> Dict[str, Any]:
        """Generiert realistische Structured Data für Tests"""
        import random
        random.seed(variation_seed)
        
        results = {}
        
        for i in range(min(model_count, len(self.models))):
            model_id = self.models[i]
            base_data = self.mine_data_variants[i % len(self.mine_data_variants)]
            
            # Füge zufällige zusätzliche Felder hinzu
            structured_data = base_data.copy()
            if random.random() > 0.3:
                structured_data['latitude'] = f"{48.0 + random.random():.6f}"
            if random.random() > 0.4:
                structured_data['longitude'] = f"{-77.0 - random.random():.6f}"
            if random.random() > 0.5:
                structured_data['elevation'] = f"{300 + random.randint(0, 500)}m"
            
            results[model_id] = {
                'success': True,
                'data': {
                    'structured_data': structured_data,
                    'sources': [
                        {'url': f'https://source{j}.com/mine-{i}', 'title': f'Source {j}'}
                        for j in range(random.randint(1, 5))
                    ]
                }
            }
        
        return results

class BenchmarkAnalysisTools:
    """
    Analyse-Tools für Benchmark-Ergebnisse
    """
    
    @staticmethod
    def identify_strengths(suite_results: Dict[str, Any]) -> List[str]:
        """Identifiziert Performance-Stärken"""
        strengths = []
        test_results = suite_results['test_results']
        
        # Prüfe jede Test-Kategorie
        if test_results.get('cache_performance', {}).get('cache_analysis', {}).get('cache_effectiveness_rating') == 'EXCELLENT':
            strengths.append("Excellent cache performance")
        
        if test_results.get('synonym_matching', {}).get('matching_analysis', {}).get('success_rate_percent', 0) > 90:
            strengths.append("Highly effective synonym matching")
        
        if test_results.get('integration_compatibility', {}).get('integration_health', {}).get('integration_ready'):
            strengths.append("Full integration compatibility")
        
        if test_results.get('real_time_performance', {}).get('performance_analysis', {}).get('overall_real_time_ready'):
            strengths.append("Real-time performance ready")
        
        if test_results.get('memory_efficiency', {}).get('efficiency_metrics', {}).get('memory_efficiency_rating') in ['EXCELLENT', 'GOOD']:
            strengths.append("Good memory efficiency")
        
        return strengths
    
    @staticmethod
    def identify_weaknesses(suite_results: Dict[str, Any]) -> List[str]:
        """Identifiziert Performance-Schwächen"""
        weaknesses = []
        test_results = suite_results['test_results']
        
        if test_results.get('real_time_performance', {}).get('performance_analysis', {}).get('time_criteria_pass_rate', 100) < 80:
            weaknesses.append("Inconsistent real-time performance")
        
        if test_results.get('memory_efficiency', {}).get('efficiency_metrics', {}).get('memory_efficiency_rating') == 'POOR':
            weaknesses.append("Poor memory efficiency")
        
        if test_results.get('cache_performance', {}).get('cache_analysis', {}).get('cache_effectiveness_rating') in ['POOR', 'ACCEPTABLE']:
            weaknesses.append("Cache performance needs improvement")
        
        return weaknesses
    
    @staticmethod
    def identify_critical_issues(suite_results: Dict[str, Any]) -> List[str]:
        """Identifiziert kritische Performance-Probleme"""
        critical = []
        test_results = suite_results['test_results']
        
        if test_results.get('auto_refresh_simulation', {}).get('auto_refresh_analysis', {}).get('memory_leak_detected'):
            critical.append("Memory leak detected during auto-refresh simulation")
        
        if not test_results.get('integration_compatibility', {}).get('integration_health', {}).get('integration_ready'):
            critical.append("Integration compatibility issues detected")
        
        # Check für kritische Performance-Probleme
        if test_results.get('real_time_performance', {}).get('performance_analysis', {}).get('max_total_time_ms', 0) > 10000:
            critical.append("Real-time performance exceeds acceptable limits (>10 seconds)")
        
        if test_results.get('memory_efficiency', {}).get('efficiency_metrics', {}).get('average_memory_per_cache_item_kb', 0) > 20:
            critical.append("Excessive memory usage per cache item (>20KB)")
        
        return critical
    
    @staticmethod
    def generate_performance_recommendations(suite_results: Dict[str, Any]) -> List[str]:
        """Generiert Performance-Empfehlungen"""
        recommendations = []
        overall_score = suite_results['overall_performance']['score']
        
        if overall_score < 75:
            recommendations.append("System needs optimization before production deployment")
        
        # Spezifische Empfehlungen basierend auf Test-Ergebnissen
        if 'real_time_performance' in suite_results['test_results']:
            rt_results = suite_results['test_results']['real_time_performance']
            if not rt_results['performance_analysis'].get('overall_real_time_ready', True):
                recommendations.append("Optimize real-time performance for 30-second auto-refresh cycles")
        
        if 'memory_efficiency' in suite_results['test_results']:
            mem_results = suite_results['test_results']['memory_efficiency']
            mem_rating = mem_results['efficiency_metrics'].get('memory_efficiency_rating', 'GOOD')
            if mem_rating in ['POOR', 'ACCEPTABLE']:
                recommendations.append("Improve memory efficiency - consider reducing cache sizes or optimizing data structures")
        
        if 'cache_performance' in suite_results['test_results']:
            cache_results = suite_results['test_results']['cache_performance']
            cache_rating = cache_results['cache_analysis'].get('cache_effectiveness_rating', 'GOOD')
            if cache_rating in ['POOR', 'ACCEPTABLE']:
                recommendations.append("Optimize cache configuration - current hit rates are below optimal")
        
        if not recommendations:
            recommendations.append("System performance is excellent - ready for production")
        
        return recommendations

class BenchmarkReportGenerator:
    """
    Report-Generation für Benchmark-Ergebnisse
    """
    
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    async def save_benchmark_results(self, results: Dict[str, Any], report_type: str = "benchmark"):
        """Speichert Benchmark-Ergebnisse"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON-Ergebnisse
        json_file = self.output_dir / f"{report_type}_results_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)
        
        # HTML-Report
        html_file = self.output_dir / f"{report_type}_report_{timestamp}.html"
        html_content = self.generate_html_report(results, report_type)
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"[BENCHMARK-UTILS] {report_type} Ergebnisse gespeichert: {json_file}, {html_file}")
        
        return {
            'json_file': str(json_file),
            'html_file': str(html_file),
            'timestamp': timestamp
        }
    
    def generate_html_report(self, results: Dict[str, Any], report_type: str = "benchmark") -> str:
        """Generiert HTML-Report für Benchmark-Ergebnisse"""
        overall = results.get('overall_performance', {})
        summary = results.get('summary', {})
        
        # Verwende BenchmarkAnalysisTools für Analyse
        analysis_tools = BenchmarkAnalysisTools()
        strengths = analysis_tools.identify_strengths(results)
        weaknesses = analysis_tools.identify_weaknesses(results)
        critical_issues = analysis_tools.identify_critical_issues(results)
        recommendations = analysis_tools.generate_performance_recommendations(results)
        
        grade = overall.get('grade', 'N/A')
        score = overall.get('score', 0)
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{report_type.title()} Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .grade-{grade.replace('+', 'plus').lower()} {{ color: {'green' if grade in ['A+', 'A'] else 'orange' if grade == 'B' else 'red'}; }}
        .test-section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
        .metric {{ margin: 10px 0; }}
        .recommendation {{ background: #fff3cd; padding: 10px; margin: 10px 0; border-radius: 3px; }}
        .strength {{ color: green; }}
        .weakness {{ color: orange; }}
        .critical {{ color: red; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{report_type.title()} Report</h1>
        <p><strong>Timestamp:</strong> {results.get('benchmark_timestamp', 'N/A')}</p>
        <p><strong>Overall Grade:</strong> <span class="grade-{grade.replace('+', 'plus').lower()}">{grade}</span> ({score}/100)</p>
        <p><strong>Production Ready:</strong> {'✓ Yes' if summary.get('production_ready', False) else '✗ No'}</p>
    </div>
    
    <div class="test-section">
        <h2>Summary</h2>
        <div class="metric"><strong>Strengths:</strong></div>
        <ul>{''.join(f'<li class="strength">{s}</li>' for s in strengths) or '<li>None identified</li>'}</ul>
        
        <div class="metric"><strong>Weaknesses:</strong></div>
        <ul>{''.join(f'<li class="weakness">{w}</li>' for w in weaknesses) or '<li>None identified</li>'}</ul>
        
        <div class="metric"><strong>Critical Issues:</strong></div>
        <ul>{''.join(f'<li class="critical">{c}</li>' for c in critical_issues) or '<li>None detected</li>'}</ul>
    </div>
    
    <div class="test-section">
        <h2>Recommendations</h2>
        {''.join(f'<div class="recommendation">{r}</div>' for r in recommendations)}
    </div>
    
    <div class="test-section">
        <h2>Test Results Overview</h2>
        <p>Detailed test results are available in the JSON file.</p>
        <ul>"""
        
        # Dynamische Test-Ergebnisse basierend auf verfügbaren Tests
        test_results = results.get('test_results', {})
        for test_name, test_data in test_results.items():
            status = "✓ PASS" if self._determine_test_pass(test_name, test_data) else "✗ FAIL"
            html += f'<li>{test_name.replace("_", " ").title()}: {status}</li>'
        
        html += f"""
        </ul>
    </div>
    
    <div class="test-section">
        <h2>System Information</h2>
        <ul>"""
        
        system_info = results.get('system_info', {})
        if system_info:
            html += f"""
            <li><strong>Platform:</strong> {system_info.get('platform', 'N/A')}</li>
            <li><strong>Python Version:</strong> {system_info.get('python_version', 'N/A')}</li>
            <li><strong>CPU Count:</strong> {system_info.get('cpu_count', 'N/A')}</li>
            <li><strong>Total Memory:</strong> {system_info.get('memory_total_mb', 0):.1f} MB</li>"""
            
            optimizer_config = system_info.get('optimizer_config', {})
            if optimizer_config:
                html += f'<li><strong>Cache Size:</strong> {optimizer_config.get("cache_size", "N/A")}</li>'
        
        html += """
        </ul>
    </div>
</body>
</html>
        """
        
        return html
    
    def _determine_test_pass(self, test_name: str, test_data: Dict[str, Any]) -> bool:
        """Bestimmt ob ein Test erfolgreich war"""
        if test_name == 'real_time_performance':
            return test_data.get('performance_analysis', {}).get('overall_real_time_ready', False)
        elif test_name == 'large_dataset_stress':
            return test_data.get('scalability_analysis', {}).get('linear_scalability_achieved', False)
        elif test_name == 'memory_efficiency':
            rating = test_data.get('efficiency_metrics', {}).get('memory_efficiency_rating', 'POOR')
            return rating in ['EXCELLENT', 'GOOD']
        elif test_name == 'cache_performance':
            rating = test_data.get('cache_analysis', {}).get('cache_effectiveness_rating', 'POOR')
            return rating in ['EXCELLENT', 'GOOD']
        elif test_name == 'integration_compatibility':
            return test_data.get('integration_health', {}).get('integration_ready', False)
        else:
            # Default: Prüfe ob Test erfolgreich ausgeführt wurde
            return test_data.get('success', True)