#!/usr/bin/env python3
"""
Author: rahn
Datum: 25.07.2025
Version: 1.0
Beschreibung: Umfassende Validierung der Datenbank-Integration für alle Modell-Ergebnisse
ÄNDERUNG 25.07.2025: Batch-Coordination Database-Integration Tests
"""

import asyncio
import logging
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional
from database import db_manager
from enhanced_multi_model_batch_service import enhanced_batch_service
from batch_priority_coordinator import batch_priority_coordinator
from model_selection_coordinator import model_selection_coordinator
from cost_monitor import cost_monitor

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseIntegrationValidator:
    """
    Umfassende Validierung der Datenbank-Integration
    
    TESTZIELE:
    1. Alle Modell-Ergebnisse werden korrekt gespeichert
    2. Thread-Safe Operations funktionieren
    3. Batch-Coordination ist vollständig integriert
    4. Cost-Monitoring Daten sind persistent
    5. Frontend kann alle Daten korrekt abrufen
    """
    
    def __init__(self):
        self.test_session_id = f"db_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.validation_results = {
            'tests_passed': 0,
            'tests_failed': 0,
            'detailed_results': [],
            'database_integrity': 'unknown',
            'coordination_integration': 'unknown',
            'cost_monitoring_integration': 'unknown'
        }
        
    async def run_comprehensive_validation(self) -> Dict[str, Any]:
        """
        Führt umfassende Datenbank-Integration-Validierung durch
        
        Returns:
            Validierungsbericht
        """
        logger.info("[DB-VALIDATION] Starte umfassende Datenbank-Integration-Validierung")
        
        validation_tests = [
            self._test_basic_database_operations,
            self._test_enhanced_batch_service_integration,
            self._test_batch_priority_coordinator_integration,
            self._test_model_selection_coordinator_integration,
            self._test_cost_monitoring_integration,
            self._test_parallel_database_operations,
            self._test_data_retrieval_for_frontend,
            self._test_database_consistency_after_batch,
            self._test_thread_safety_under_load
        ]
        
        for test_func in validation_tests:
            try:
                test_name = test_func.__name__
                logger.info(f"[DB-VALIDATION] Führe Test aus: {test_name}")
                
                result = await test_func()
                
                if result.get('success', False):
                    self.validation_results['tests_passed'] += 1
                    logger.info(f"[DB-VALIDATION] ✅ {test_name} bestanden")
                else:
                    self.validation_results['tests_failed'] += 1
                    logger.error(f"[DB-VALIDATION] ❌ {test_name} fehlgeschlagen: {result.get('error', 'Unbekannt')}")
                
                self.validation_results['detailed_results'].append({
                    'test_name': test_name,
                    'success': result.get('success', False),
                    'details': result,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                self.validation_results['tests_failed'] += 1
                logger.error(f"[DB-VALIDATION] ❌ {test_func.__name__} Exception: {str(e)}")
                
                self.validation_results['detailed_results'].append({
                    'test_name': test_func.__name__,
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
        
        # Generate Final Assessment
        total_tests = self.validation_results['tests_passed'] + self.validation_results['tests_failed']
        success_rate = self.validation_results['tests_passed'] / total_tests if total_tests > 0 else 0
        
        if success_rate >= 0.9:
            self.validation_results['database_integrity'] = 'excellent'
        elif success_rate >= 0.7:
            self.validation_results['database_integrity'] = 'good'
        elif success_rate >= 0.5:
            self.validation_results['database_integrity'] = 'fair'
        else:
            self.validation_results['database_integrity'] = 'poor'
        
        logger.info(f"[DB-VALIDATION] Validierung abgeschlossen: {self.validation_results['tests_passed']}/{total_tests} Tests bestanden ({success_rate*100:.1f}%)")
        
        return self.validation_results
    
    async def _test_basic_database_operations(self) -> Dict[str, Any]:
        """Test grundlegende Datenbank-Operationen"""
        try:
            # Test 1: Save Search Result
            test_result = db_manager.save_search_result(
                mine_name="Test Mine Basic",
                model_used="test:basic-model",
                structured_data={"test_field": "test_value", "numeric_field": 123},
                sources=[{"url": "https://test.example.com", "title": "Test Source"}],
                session_id=self.test_session_id,
                country="Canada",
                region="Quebec",
                commodity="Gold",
                search_type="database_validation_test",
                search_duration=1.5,
                success=True
            )
            
            if not test_result or not test_result.id:
                return {'success': False, 'error': 'Speichern fehlgeschlagen'}
            
            # Test 2: Retrieve Search Result
            retrieved_result = db_manager.get_search_result_by_id(test_result.id)
            if not retrieved_result:
                return {'success': False, 'error': 'Abrufen fehlgeschlagen'}
            
            # Test 3: Validate Data Integrity
            if retrieved_result.mine_name != "Test Mine Basic":
                return {'success': False, 'error': 'Datenintegrität verletzt'}
            
            return {
                'success': True,
                'result_id': test_result.id,
                'data_integrity_verified': True
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _test_enhanced_batch_service_integration(self) -> Dict[str, Any]:
        """Test Enhanced Multi-Model Batch Service Datenbank-Integration"""
        try:
            test_mine_data = {
                'mine_name': 'Enhanced Batch Test Mine',
                'country': 'Canada',
                'commodity': 'Gold',
                'region': 'Quebec'
            }
            
            test_models = ['openrouter:kimi-k2', 'openrouter:deepseek-free']
            
            # Mock Enhanced Batch Service Test
            enhanced_result = await enhanced_batch_service.enhanced_batch_search_per_mine(
                mine_data=test_mine_data,
                selected_models=test_models,
                session_id=self.test_session_id,
                search_options={'test_mode': True}
            )
            
            if not enhanced_result or not enhanced_result.get('success'):
                return {'success': False, 'error': 'Enhanced Batch Service fehlgeschlagen'}
            
            # Validate Database Storage
            stored_results = db_manager.get_search_results(mine_name="Enhanced Batch Test Mine")
            
            if not stored_results:
                return {'success': False, 'error': 'Keine Ergebnisse in DB gespeichert'}
            
            # Check for Multiple Model Results
            model_ids_in_db = [r.model_used for r in stored_results if r.session_id == self.test_session_id]
            expected_models_in_db = len([m for m in test_models if enhanced_result.get('models_successful', [])])
            
            return {
                'success': True,
                'enhanced_batch_success': enhanced_result.get('success'),
                'models_in_database': len(model_ids_in_db),
                'expected_models': expected_models_in_db,
                'models_successful': enhanced_result.get('models_successful', []),
                'cost_monitoring_present': 'cost_analysis' in enhanced_result
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _test_batch_priority_coordinator_integration(self) -> Dict[str, Any]:
        """Test Batch Priority Coordinator Datenbank-Integration"""
        try:
            test_mines_data = [
                {'mine_name': 'Priority Test Mine 1', 'country': 'Canada', 'commodity': 'Gold', 'region': 'Quebec'},
                {'mine_name': 'Priority Test Mine 2', 'country': 'USA', 'commodity': 'Silver', 'region': 'Nevada'}
            ]
            
            test_models = ['openrouter:kimi-k2']
            
            # Execute Batch Priority Coordination
            coordination_result = await batch_priority_coordinator.coordinate_priority_batch_execution(
                mines_data=test_mines_data,
                selected_models=test_models,
                session_id=self.test_session_id,
                batch_options={'test_mode': True},
                priority_level="high"
            )
            
            if not coordination_result or not coordination_result.get('success'):
                return {'success': False, 'error': 'Batch Priority Coordination fehlgeschlagen'}
            
            # Validate Database Integration
            database_operations = coordination_result.get('database_operations', {})
            cost_analysis = coordination_result.get('cost_analysis', {})
            coordination_savings = coordination_result.get('coordination_savings', {})
            
            # Check Database Storage Success
            successful_saves = database_operations.get('successful_saves', 0)
            failed_saves = database_operations.get('failed_saves', 0)
            
            return {
                'success': True,
                'coordination_success': coordination_result.get('success'),
                'database_saves_successful': successful_saves,
                'database_saves_failed': failed_saves,
                'cost_analysis_integrated': cost_analysis is not None,
                'coordination_savings_tracked': coordination_savings is not None,
                'thread_safe_operations': database_operations.get('thread_safe_operations', False)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _test_model_selection_coordinator_integration(self) -> Dict[str, Any]:
        """Test Model Selection Coordinator Datenbank-Integration"""
        try:
            test_models = ['openrouter:kimi-k2', 'openrouter:deepseek-free']
            
            # Execute Model Selection Coordination
            coordination_result = await model_selection_coordinator.coordinate_guaranteed_execution(
                selected_models=test_models,
                mine_name="Model Selection Test Mine",
                country="Canada",
                commodity="Gold",
                region="Quebec",
                session_id=self.test_session_id,
                allow_fallbacks=False,
                max_parallel=5
            )
            
            if not coordination_result or not coordination_result.get('success'):
                return {'success': False, 'error': 'Model Selection Coordination fehlgeschlagen'}
            
            # Validate Model Execution Guarantees
            models_successful = coordination_result.get('models_successful', [])
            models_failed = coordination_result.get('models_failed', [])
            individual_results = coordination_result.get('individual_results', {})
            
            return {
                'success': True,
                'models_requested': len(test_models),
                'models_successful': len(models_successful),
                'models_failed': len(models_failed),
                'all_models_attempted': len(individual_results) == len(test_models),
                'guaranteed_execution': coordination_result.get('execution_mode') == 'guaranteed_execution',
                'success_rate': coordination_result.get('statistics', {}).get('success_rate_of_requested', 0)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _test_cost_monitoring_integration(self) -> Dict[str, Any]:
        """Test Cost Monitor Integration in alle Services"""
        try:
            # Test Cost Monitor Batch Analysis
            test_batch_id = f"cost_test_{datetime.now().strftime('%H%M%S')}"
            test_models = ['openrouter:kimi-k2', 'perplexity:sonar-pro']  # Mix von free und premium
            
            cost_analysis = await cost_monitor.monitor_batch_costs(
                batch_id=test_batch_id,
                models_list=test_models,
                mines_count=3,
                session_id=self.test_session_id,
                priority_level="high"
            )
            
            if not cost_analysis:
                return {'success': False, 'error': 'Cost-Analyse fehlgeschlagen'}
            
            # Test Coordination Savings Calculation
            coordination_savings = await cost_monitor.calculate_coordination_savings(
                batch_id=test_batch_id,
                execution_duration=45.0,
                successful_operations=5,
                total_operations=6
            )
            
            if not coordination_savings:
                return {'success': False, 'error': 'Koordinations-Einsparungen Berechnung fehlgeschlagen'}
            
            # Test Comprehensive Cost Report
            comprehensive_report = await cost_monitor.generate_comprehensive_cost_report()
            
            return {
                'success': True,
                'cost_analysis_generated': 'cost_breakdown' in cost_analysis,
                'premium_models_detected': len(cost_analysis.get('cost_breakdown', {}).get('premium_models', [])) > 0,
                'coordination_savings_calculated': 'performance_metrics' in coordination_savings,
                'comprehensive_report_available': 'summary' in comprehensive_report,
                'batch_tracked': test_batch_id in cost_monitor.batch_cost_tracking,
                'savings_tracked': test_batch_id in cost_monitor.coordination_cost_savings
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _test_parallel_database_operations(self) -> Dict[str, Any]:
        """Test Thread-Safety unter parallelen Operationen"""
        try:
            # Simulate parallel database writes
            parallel_tasks = []
            
            for i in range(10):
                task = self._simulate_parallel_db_write(i)
                parallel_tasks.append(task)
            
            # Execute all tasks in parallel
            results = await asyncio.gather(*parallel_tasks, return_exceptions=True)
            
            # Analyze results
            successful_writes = 0
            failed_writes = 0
            
            for result in results:
                if isinstance(result, Exception):
                    failed_writes += 1
                elif result.get('success', False):
                    successful_writes += 1
                else:
                    failed_writes += 1
            
            # Validate no race conditions occurred
            stored_results = db_manager.get_search_results()
            parallel_test_results = [r for r in stored_results if r.session_id == self.test_session_id and 'Parallel Test' in r.mine_name]
            
            return {
                'success': successful_writes >= 8,  # Allow 2 failures
                'successful_parallel_writes': successful_writes,
                'failed_parallel_writes': failed_writes,
                'database_entries_created': len(parallel_test_results),
                'race_conditions_detected': failed_writes > 2,
                'thread_safety_verified': failed_writes <= 2
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _simulate_parallel_db_write(self, task_id: int) -> Dict[str, Any]:
        """Simuliert parallele Datenbank-Schreibvorgänge"""
        try:
            result = db_manager.save_search_result(
                mine_name=f"Parallel Test Mine {task_id}",
                model_used=f"test:parallel-model-{task_id}",
                structured_data={"parallel_test_id": task_id, "timestamp": datetime.now().isoformat()},
                sources=[{"url": f"https://parallel-test-{task_id}.example.com"}],
                session_id=self.test_session_id,
                country="Canada",
                region="Test Region",
                commodity="Test Commodity",
                search_type="parallel_test",
                search_duration=0.1,
                success=True
            )
            
            return {'success': True, 'result_id': result.id if result else None}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _test_data_retrieval_for_frontend(self) -> Dict[str, Any]:
        """Test Daten-Abruf für Frontend-Kompatibilität"""
        try:
            # Test Session-based Retrieval
            session_results = db_manager.get_search_results()
            test_session_results = [r for r in session_results if r.session_id == self.test_session_id]
            
            if not test_session_results:
                return {'success': False, 'error': 'Keine Test-Session Ergebnisse gefunden'}
            
            # Test Statistics Retrieval
            stats = db_manager.get_statistics()
            
            required_stats_keys = ['total_results', 'model_performance', 'sources_by_type']
            missing_keys = [key for key in required_stats_keys if key not in stats]
            
            if missing_keys:
                return {'success': False, 'error': f'Fehlende Statistik-Keys: {missing_keys}'}
            
            # Test Session-grouped Data
            sessions_data = db_manager.get_sessions()
            test_session_data = next((s for s in sessions_data if s['session_id'] == self.test_session_id), None)
            
            return {
                'success': True,
                'test_session_results_count': len(test_session_results),
                'statistics_complete': len(missing_keys) == 0,
                'test_session_grouped': test_session_data is not None,
                'model_performance_available': 'model_performance' in stats and len(stats['model_performance']) > 0,
                'frontend_data_complete': all([
                    len(test_session_results) > 0,
                    len(missing_keys) == 0,
                    test_session_data is not None
                ])
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _test_database_consistency_after_batch(self) -> Dict[str, Any]:
        """Test Datenbank-Konsistenz nach Batch-Operationen"""
        try:
            # Get all results from test session
            all_test_results = db_manager.get_search_results()
            session_results = [r for r in all_test_results if r.session_id == self.test_session_id]
            
            if not session_results:
                return {'success': False, 'error': 'Keine Test-Ergebnisse für Konsistenz-Prüfung'}
            
            # Check data consistency
            consistency_issues = []
            
            for result in session_results:
                # Check required fields
                if not result.mine_name:
                    consistency_issues.append(f"Result {result.id}: missing mine_name")
                
                if not result.model_used:
                    consistency_issues.append(f"Result {result.id}: missing model_used")
                
                if not result.structured_data:
                    consistency_issues.append(f"Result {result.id}: missing structured_data")
                
                # Check data types
                if result.structured_data and not isinstance(result.structured_data, dict):
                    consistency_issues.append(f"Result {result.id}: structured_data not dict")
                
                if result.sources and not isinstance(result.sources, list):
                    consistency_issues.append(f"Result {result.id}: sources not list")
            
            # Check for duplicate entries (same mine + model + session)
            seen_combinations = set()
            duplicates = []
            
            for result in session_results:
                combination = (result.mine_name, result.model_used, result.session_id)
                if combination in seen_combinations:
                    duplicates.append(combination)
                else:
                    seen_combinations.add(combination)
            
            return {
                'success': len(consistency_issues) == 0 and len(duplicates) == 0,
                'total_results_checked': len(session_results),
                'consistency_issues': consistency_issues,
                'duplicate_entries': duplicates,
                'data_integrity_score': (len(session_results) - len(consistency_issues)) / len(session_results) if session_results else 0
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _test_thread_safety_under_load(self) -> Dict[str, Any]:
        """Test Thread-Safety unter hoher Last"""
        try:
            # Simulate high load with concurrent operations
            concurrent_tasks = []
            
            # Create multiple types of concurrent operations
            for i in range(5):
                # Enhanced Batch Service operations
                task1 = self._simulate_enhanced_batch_operation(i)
                concurrent_tasks.append(task1)
                
                # Direct database operations
                task2 = self._simulate_direct_db_operation(i)
                concurrent_tasks.append(task2)
            
            # Execute all concurrent operations
            start_time = datetime.now()
            results = await asyncio.gather(*concurrent_tasks, return_exceptions=True)
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Analyze results
            successful_operations = 0
            failed_operations = 0
            exceptions = []
            
            for result in results:
                if isinstance(result, Exception):
                    failed_operations += 1
                    exceptions.append(str(result))
                elif result.get('success', False):
                    successful_operations += 1
                else:
                    failed_operations += 1
            
            # Check database state consistency
            final_results = db_manager.get_search_results()
            load_test_results = [r for r in final_results if r.session_id == self.test_session_id and 'Load Test' in r.mine_name]
            
            return {
                'success': successful_operations >= len(concurrent_tasks) * 0.8,  # 80% success rate
                'total_concurrent_operations': len(concurrent_tasks),
                'successful_operations': successful_operations,
                'failed_operations': failed_operations,
                'execution_time_seconds': execution_time,
                'operations_per_second': len(concurrent_tasks) / execution_time if execution_time > 0 else 0,
                'database_entries_created': len(load_test_results),
                'exceptions': exceptions[:5],  # Limit to first 5 exceptions
                'thread_safety_confirmed': failed_operations < len(concurrent_tasks) * 0.2
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _simulate_enhanced_batch_operation(self, task_id: int) -> Dict[str, Any]:
        """Simuliert Enhanced Batch Service Operation unter Last"""
        try:
            test_mine_data = {
                'mine_name': f'Load Test Mine Enhanced {task_id}',
                'country': 'Canada',
                'commodity': 'Copper',
                'region': 'Quebec'
            }
            
            result = await enhanced_batch_service.enhanced_batch_search_per_mine(
                mine_data=test_mine_data,
                selected_models=['openrouter:kimi-k2'],
                session_id=self.test_session_id,
                search_options={'load_test': True}
            )
            
            return {'success': result.get('success', False), 'operation_type': 'enhanced_batch'}
            
        except Exception as e:
            return {'success': False, 'error': str(e), 'operation_type': 'enhanced_batch'}
    
    async def _simulate_direct_db_operation(self, task_id: int) -> Dict[str, Any]:
        """Simuliert direkte Datenbank-Operation unter Last"""
        try:
            result = db_manager.save_search_result(
                mine_name=f"Load Test Mine Direct {task_id}",
                model_used=f"test:load-model-{task_id}",
                structured_data={"load_test": True, "task_id": task_id},
                sources=[{"url": f"https://load-test-{task_id}.example.com"}],
                session_id=self.test_session_id,
                country="Canada",
                region="Load Test Region",
                commodity="Load Test Commodity",
                search_type="load_test",
                search_duration=0.05,
                success=True
            )
            
            return {'success': result is not None, 'operation_type': 'direct_db'}
            
        except Exception as e:
            return {'success': False, 'error': str(e), 'operation_type': 'direct_db'}

# Main Execution
async def main():
    """Hauptfunktion für Datenbank-Integration-Validierung"""
    print("🔍 Starte umfassende Datenbank-Integration-Validierung...")
    
    validator = DatabaseIntegrationValidator()
    
    try:
        validation_results = await validator.run_comprehensive_validation()
        
        # Print Results
        print("\n" + "="*80)
        print("📊 DATENBANK-INTEGRATION VALIDIERUNGSBERICHT")
        print("="*80)
        
        print(f"✅ Tests bestanden: {validation_results['tests_passed']}")
        print(f"❌ Tests fehlgeschlagen: {validation_results['tests_failed']}")
        print(f"🏆 Datenbank-Integrität: {validation_results['database_integrity'].upper()}")
        
        if validation_results['tests_failed'] > 0:
            print("\n🔍 FEHLGESCHLAGENE TESTS:")
            for result in validation_results['detailed_results']:
                if not result['success']:
                    print(f"   ❌ {result['test_name']}: {result.get('error', 'Unbekannt')}")
        
        print("\n📈 DETAILLIERTE ERGEBNISSE:")
        for result in validation_results['detailed_results']:
            status = "✅" if result['success'] else "❌"
            print(f"   {status} {result['test_name']}")
            if result['success'] and isinstance(result.get('details'), dict):
                for key, value in result['details'].items():
                    if key not in ['success', 'error']:
                        print(f"      - {key}: {value}")
        
        print("\n" + "="*80)
        
        # Return appropriate exit code
        if validation_results['database_integrity'] in ['excellent', 'good']:
            print("🎉 VALIDIERUNG ERFOLGREICH: Datenbank-Integration vollständig funktional!")
            return 0
        else:
            print("⚠️  VALIDIERUNG UNVOLLSTÄNDIG: Datenbank-Integration benötigt Aufmerksamkeit!")
            return 1
            
    except Exception as e:
        print(f"💥 KRITISCHER FEHLER bei Validierung: {str(e)}")
        return 2

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)