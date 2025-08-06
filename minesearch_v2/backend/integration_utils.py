"""
Author: rahn
Datum: 06.08.2025
Version: 1.0
Beschreibung: Integration Test Utilities - Helper-Funktionen und Analysetools
ÄNDERUNG 06.08.2025: Refactoring gemäß REGEL 1 - Utilities aus final_system_integration_validation.py
"""

import asyncio
import logging
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# Import für Performance und Monitoring
from cost_monitor import cost_monitor
from database import db_manager

logger = logging.getLogger(__name__)

class IntegrationAnalysisTools:
    """
    Analyse-Tools für Integration Tests
    """
    
    @staticmethod
    def analyze_system_readiness(validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analysiert System-Bereitschaft basierend auf Validierungsergebnissen"""
        total_tests = validation_results['tests_passed'] + validation_results['tests_failed']
        success_rate = validation_results['tests_passed'] / total_tests if total_tests > 0 else 0
        
        # System Readiness Kriterien
        readiness_criteria = {
            'minimum_success_rate': 0.8,  # 80% Tests müssen bestehen
            'critical_tests_passed': True,  # Kritische Tests müssen bestehen
            'no_blocking_issues': True  # Keine blockierenden Probleme
        }
        
        # Prüfe kritische Tests
        critical_test_names = [
            '_test_critical_issue_resolution',
            '_test_all_models_all_mines_guarantee',
            '_test_database_completeness_guarantee'
        ]
        
        critical_tests_status = []
        for test_result in validation_results['detailed_results']:
            if test_result['test_name'] in critical_test_names:
                critical_tests_status.append(test_result['success'])
        
        critical_tests_passed = all(critical_tests_status) if critical_tests_status else False
        
        # Prüfe auf blockierende Probleme
        blocking_issues = []
        for test_result in validation_results['detailed_results']:
            if not test_result['success'] and test_result['test_name'] in critical_test_names:
                blocking_issues.append(test_result['test_name'])
        
        no_blocking_issues = len(blocking_issues) == 0
        
        # Gesamtbewertung
        system_ready = (
            success_rate >= readiness_criteria['minimum_success_rate'] and
            critical_tests_passed and
            no_blocking_issues
        )
        
        readiness_level = 'PRODUCTION_READY' if system_ready else (
            'TESTING_READY' if success_rate >= 0.6 else 'NOT_READY'
        )
        
        return {
            'system_ready': system_ready,
            'readiness_level': readiness_level,
            'success_rate': success_rate,
            'critical_tests_passed': critical_tests_passed,
            'blocking_issues': blocking_issues,
            'total_tests': total_tests,
            'tests_passed': validation_results['tests_passed'],
            'readiness_criteria': readiness_criteria,
            'readiness_score': min(100, success_rate * 100 + (10 if critical_tests_passed else 0))
        }
    
    @staticmethod
    def analyze_production_readiness(validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analysiert Produktionsbereitschaft"""
        production_criteria = {
            'all_critical_tests_pass': False,
            'performance_acceptable': False,
            'stability_verified': False,
            'error_handling_robust': False,
            'cost_monitoring_active': False
        }
        
        # Analysiere Test-Ergebnisse für Produktionskriterien
        for test_result in validation_results['detailed_results']:
            test_name = test_result['test_name']
            success = test_result['success']
            details = test_result.get('details', {})
            
            # Kritische Tests
            if test_name in ['_test_critical_issue_resolution', '_test_all_models_all_mines_guarantee']:
                if success:
                    production_criteria['all_critical_tests_pass'] = True
            
            # Performance Tests
            elif test_name == '_test_performance_under_production_load':
                if success and details.get('performance_acceptable', False):
                    production_criteria['performance_acceptable'] = True
            
            # Stabilitäts Tests
            elif test_name == '_test_system_stability_over_time':
                if success and details.get('stability_verified', False):
                    production_criteria['stability_verified'] = True
            
            # Error Handling Tests
            elif test_name == '_test_comprehensive_error_handling':
                if success and details.get('error_handling_robust', False):
                    production_criteria['error_handling_robust'] = True
        
        # Cost Monitoring Check (separat)
        try:
            cost_status = cost_monitor.get_current_cost_status()
            production_criteria['cost_monitoring_active'] = isinstance(cost_status, dict)
        except:
            production_criteria['cost_monitoring_active'] = False
        
        # Produktionsbereitschaft bewerten
        criteria_met = sum(production_criteria.values())
        total_criteria = len(production_criteria)
        
        production_ready = criteria_met >= (total_criteria * 0.8)  # 80% Kriterien erfüllt
        
        production_level = 'PRODUCTION_READY' if production_ready else (
            'PRE_PRODUCTION' if criteria_met >= (total_criteria * 0.6) else 'DEVELOPMENT'
        )
        
        return {
            'production_ready': production_ready,
            'production_level': production_level,
            'criteria_met': criteria_met,
            'total_criteria': total_criteria,
            'criteria_details': production_criteria,
            'production_score': (criteria_met / total_criteria) * 100,
            'recommendations': IntegrationAnalysisTools._generate_production_recommendations(production_criteria)
        }
    
    @staticmethod
    def _generate_production_recommendations(criteria: Dict[str, bool]) -> List[str]:
        """Generiert Empfehlungen für Produktionsbereitschaft"""
        recommendations = []
        
        if not criteria['all_critical_tests_pass']:
            recommendations.append("Kritische Tests müssen alle bestehen vor Produktionsfreigabe")
        
        if not criteria['performance_acceptable']:
            recommendations.append("Performance-Optimierung erforderlich für Produktionslast")
        
        if not criteria['stability_verified']:
            recommendations.append("Langzeit-Stabilitätstests durchführen")
        
        if not criteria['error_handling_robust']:
            recommendations.append("Error Handling robuster gestalten")
        
        if not criteria['cost_monitoring_active']:
            recommendations.append("Cost Monitoring System aktivieren und testen")
        
        if not recommendations:
            recommendations.append("System ist bereit für Produktionsfreigabe")
        
        return recommendations

class IntegrationPerformanceMonitor:
    """
    Performance Monitoring für Integration Tests
    """
    
    def __init__(self):
        self.performance_metrics = {
            'test_start_time': None,
            'test_end_time': None,
            'individual_test_times': {},
            'database_operation_times': {},
            'batch_operation_times': {},
            'memory_usage': {},
            'cost_tracking': {}
        }
    
    def start_monitoring(self):
        """Startet Performance Monitoring"""
        self.performance_metrics['test_start_time'] = time.time()
        logger.info("[INTEGRATION-MONITOR] Performance Monitoring gestartet")
    
    def end_monitoring(self):
        """Beendet Performance Monitoring"""
        self.performance_metrics['test_end_time'] = time.time()
        logger.info("[INTEGRATION-MONITOR] Performance Monitoring beendet")
    
    def record_test_time(self, test_name: str, start_time: float, end_time: float):
        """Zeichnet Test-Zeiten auf"""
        self.performance_metrics['individual_test_times'][test_name] = {
            'duration_seconds': end_time - start_time,
            'start_time': start_time,
            'end_time': end_time
        }
    
    def record_database_operation(self, operation: str, duration: float):
        """Zeichnet Datenbank-Operationen auf"""
        if operation not in self.performance_metrics['database_operation_times']:
            self.performance_metrics['database_operation_times'][operation] = []
        
        self.performance_metrics['database_operation_times'][operation].append(duration)
    
    def record_batch_operation(self, batch_type: str, duration: float, item_count: int):
        """Zeichnet Batch-Operationen auf"""
        self.performance_metrics['batch_operation_times'][batch_type] = {
            'duration_seconds': duration,
            'items_processed': item_count,
            'items_per_second': item_count / duration if duration > 0 else 0
        }
    
    async def record_memory_usage(self, checkpoint: str):
        """Zeichnet Memory Usage auf"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            
            self.performance_metrics['memory_usage'][checkpoint] = {
                'rss_mb': memory_info.rss / 1024 / 1024,
                'vms_mb': memory_info.vms / 1024 / 1024,
                'timestamp': time.time()
            }
        except ImportError:
            logger.warning("[INTEGRATION-MONITOR] psutil nicht verfügbar für Memory Monitoring")
    
    async def record_cost_tracking(self, checkpoint: str):
        """Zeichnet Cost Tracking auf"""
        try:
            cost_status = await cost_monitor.get_current_cost_status()
            self.performance_metrics['cost_tracking'][checkpoint] = cost_status
        except Exception as e:
            logger.warning(f"[INTEGRATION-MONITOR] Cost Tracking Fehler: {str(e)}")
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """Generiert Performance Report"""
        total_duration = 0
        if self.performance_metrics['test_start_time'] and self.performance_metrics['test_end_time']:
            total_duration = self.performance_metrics['test_end_time'] - self.performance_metrics['test_start_time']
        
        # Analyse der Test-Zeiten
        test_times = self.performance_metrics['individual_test_times']
        slowest_tests = sorted(test_times.items(), key=lambda x: x[1]['duration_seconds'], reverse=True)[:3]
        fastest_tests = sorted(test_times.items(), key=lambda x: x[1]['duration_seconds'])[:3]
        
        # Database Performance
        db_operations = self.performance_metrics['database_operation_times']
        avg_db_times = {}
        for operation, times in db_operations.items():
            avg_db_times[operation] = sum(times) / len(times) if times else 0
        
        # Memory Analysis
        memory_usage = self.performance_metrics['memory_usage']
        memory_growth = 0
        if len(memory_usage) >= 2:
            checkpoints = sorted(memory_usage.keys())
            initial_memory = memory_usage[checkpoints[0]]['rss_mb']
            final_memory = memory_usage[checkpoints[-1]]['rss_mb']
            memory_growth = final_memory - initial_memory
        
        return {
            'total_test_duration_seconds': total_duration,
            'total_test_duration_minutes': total_duration / 60,
            'individual_test_count': len(test_times),
            'slowest_tests': slowest_tests,
            'fastest_tests': fastest_tests,
            'average_database_operation_times': avg_db_times,
            'memory_growth_mb': memory_growth,
            'memory_usage_checkpoints': memory_usage,
            'batch_operation_performance': self.performance_metrics['batch_operation_times'],
            'cost_tracking_checkpoints': self.performance_metrics['cost_tracking'],
            'performance_grade': self._calculate_performance_grade(total_duration, len(test_times))
        }
    
    def _calculate_performance_grade(self, total_duration: float, test_count: int) -> str:
        """Berechnet Performance Grade"""
        if test_count == 0:
            return "N/A"
        
        avg_test_time = total_duration / test_count
        
        # Performance Bewertung
        if avg_test_time < 5:
            return "A+ (Excellent)"
        elif avg_test_time < 10:
            return "A (Very Good)"
        elif avg_test_time < 20:
            return "B (Good)"
        elif avg_test_time < 30:
            return "C (Acceptable)"
        else:
            return "D (Needs Optimization)"

class IntegrationReportGenerator:
    """
    Report Generation für Integration Tests
    """
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True)
    
    def generate_final_integration_report(self, validation_results: Dict[str, Any], 
                                        performance_report: Dict[str, Any],
                                        analysis_results: Dict[str, Any]) -> str:
        """Generiert finalen Integration Report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.output_dir / f"final_integration_report_{timestamp}.json"
        
        comprehensive_report = {
            'report_metadata': {
                'generated_at': datetime.now().isoformat(),
                'report_type': 'final_system_integration_validation',
                'version': '2.0'
            },
            'validation_summary': validation_results,
            'performance_analysis': performance_report,
            'system_analysis': analysis_results,
            'overall_assessment': self._generate_overall_assessment(validation_results, analysis_results)
        }
        
        # Save JSON Report
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(comprehensive_report, f, indent=2, default=str)
        
        # Generate HTML Report
        html_report = self._generate_html_report(comprehensive_report)
        html_file = self.output_dir / f"final_integration_report_{timestamp}.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_report)
        
        logger.info(f"[INTEGRATION-REPORT] Reports generiert: {report_file}, {html_file}")
        
        return str(report_file)
    
    def _generate_overall_assessment(self, validation_results: Dict[str, Any], 
                                   analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generiert Gesamtbewertung"""
        system_readiness = analysis_results.get('system_readiness', {})
        production_readiness = analysis_results.get('production_readiness', {})
        
        total_tests = validation_results['tests_passed'] + validation_results['tests_failed']
        success_rate = validation_results['tests_passed'] / total_tests if total_tests > 0 else 0
        
        overall_grade = 'A' if success_rate >= 0.9 else (
            'B' if success_rate >= 0.8 else (
            'C' if success_rate >= 0.7 else 'D'
            )
        )
        
        return {
            'overall_grade': overall_grade,
            'success_rate_percent': success_rate * 100,
            'system_ready': system_readiness.get('system_ready', False),
            'production_ready': production_readiness.get('production_ready', False),
            'critical_issues_resolved': self._check_critical_issues_resolved(validation_results),
            'recommendation': self._generate_final_recommendation(overall_grade, system_readiness, production_readiness),
            'next_steps': self._generate_next_steps(analysis_results)
        }
    
    def _check_critical_issues_resolved(self, validation_results: Dict[str, Any]) -> bool:
        """Prüft ob kritische Probleme behoben wurden"""
        for test_result in validation_results['detailed_results']:
            if test_result['test_name'] == '_test_critical_issue_resolution':
                return test_result.get('success', False)
        return False
    
    def _generate_final_recommendation(self, grade: str, system_readiness: Dict, production_readiness: Dict) -> str:
        """Generiert finale Empfehlung"""
        if grade == 'A' and system_readiness.get('system_ready', False) and production_readiness.get('production_ready', False):
            return "RECOMMENDED FOR PRODUCTION DEPLOYMENT"
        elif grade in ['A', 'B'] and system_readiness.get('system_ready', False):
            return "READY FOR STAGING ENVIRONMENT - MINOR OPTIMIZATIONS NEEDED"
        elif grade in ['B', 'C']:
            return "REQUIRES ADDITIONAL TESTING AND FIXES BEFORE DEPLOYMENT"
        else:
            return "NOT READY FOR DEPLOYMENT - SIGNIFICANT ISSUES NEED RESOLUTION"
    
    def _generate_next_steps(self, analysis_results: Dict[str, Any]) -> List[str]:
        """Generiert nächste Schritte"""
        next_steps = []
        
        production_readiness = analysis_results.get('production_readiness', {})
        recommendations = production_readiness.get('recommendations', [])
        
        if recommendations:
            next_steps.extend(recommendations)
        else:
            next_steps.append("System ist bereit für den nächsten Entwicklungsschritt")
        
        return next_steps
    
    def _generate_html_report(self, report_data: Dict[str, Any]) -> str:
        """Generiert HTML Report"""
        overall = report_data['overall_assessment']
        validation = report_data['validation_summary']
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Final System Integration Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #f0f0f0; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
        .grade-a {{ color: green; font-weight: bold; }}
        .grade-b {{ color: orange; font-weight: bold; }}
        .grade-c {{ color: red; font-weight: bold; }}
        .grade-d {{ color: darkred; font-weight: bold; }}
        .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
        .success {{ color: green; }}
        .failure {{ color: red; }}
        .test-result {{ margin: 10px 0; padding: 10px; background: #f9f9f9; border-radius: 3px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Final System Integration Validation Report</h1>
        <p><strong>Generated:</strong> {report_data['report_metadata']['generated_at']}</p>
        <p><strong>Overall Grade:</strong> <span class="grade-{overall['overall_grade'].lower()}">{overall['overall_grade']}</span></p>
        <p><strong>Success Rate:</strong> {overall['success_rate_percent']:.1f}%</p>
        <p><strong>Recommendation:</strong> {overall['recommendation']}</p>
    </div>
    
    <div class="section">
        <h2>Test Summary</h2>
        <p><span class="success">Tests Passed: {validation['tests_passed']}</span></p>
        <p><span class="failure">Tests Failed: {validation['tests_failed']}</span></p>
        <p><strong>System Ready:</strong> {'✓ Yes' if overall['system_ready'] else '✗ No'}</p>
        <p><strong>Production Ready:</strong> {'✓ Yes' if overall['production_ready'] else '✗ No'}</p>
        <p><strong>Critical Issues Resolved:</strong> {'✓ Yes' if overall['critical_issues_resolved'] else '✗ No'}</p>
    </div>
    
    <div class="section">
        <h2>Next Steps</h2>
        <ul>
        {''.join(f'<li>{step}</li>' for step in overall['next_steps'])}
        </ul>
    </div>
    
    <div class="section">
        <h2>Detailed Test Results</h2>
        {''.join(f'''
        <div class="test-result">
            <strong>{test['test_name']}</strong>: 
            <span class="{'success' if test['success'] else 'failure'}">
                {'✓ PASS' if test['success'] else '✗ FAIL'}
            </span>
            {f"<br><small>Error: {test.get('error', '')}</small>" if not test['success'] and 'error' in test else ""}
        </div>
        ''' for test in validation['detailed_results'])}
    </div>
</body>
</html>
        """
        
        return html

# Globale Utility-Instanzen
integration_analysis_tools = IntegrationAnalysisTools()
integration_performance_monitor = IntegrationPerformanceMonitor()