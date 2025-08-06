"""
Author: rahn
Datum: 06.08.2025
Version: 1.0
Beschreibung: Integration Test Suites - Einzelne Test-Implementierungen
ÄNDERUNG 06.08.2025: Refactoring gemäß REGEL 1 - Test-Suites aus final_system_integration_validation.py
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

# Import aller kritischen Services
from enhanced_multi_model_batch_service import enhanced_batch_service
from batch_priority_coordinator import batch_priority_coordinator
from model_selection_coordinator import model_selection_coordinator
from cost_monitor import cost_monitor
from database import db_manager
from html_utils import create_batch_results_table, create_comprehensive_results_page

logger = logging.getLogger(__name__)

class IntegrationTestSuites:
    """
    Integration Test Suites für das MineSearch System
    
    EINZELNE TESTSZENARIEN:
    1. Critical Issue Resolution Tests
    2. CSV Workflow Integration Tests
    3. Database Completeness Tests
    4. Frontend Display Tests
    5. System Coordination Tests
    """
    
    def __init__(self, session_id: str):
        self.session_id = session_id
    
    async def test_critical_issue_resolution(self) -> Dict[str, Any]:
        """Test dass das kritische Problem 'nur der letzte eintrag übernommen wird' behoben ist"""
        try:
            # Original Problem: Nur der letzte CSV-Eintrag wurde verarbeitet
            # Test mit mehreren Minen und mehreren Modellen
            
            critical_test_mines = [
                {'mine_name': 'Critical Issue Test Mine 1', 'country': 'Canada', 'commodity': 'Gold', 'region': 'Quebec'},
                {'mine_name': 'Critical Issue Test Mine 2', 'country': 'USA', 'commodity': 'Silver', 'region': 'Nevada'},
                {'mine_name': 'Critical Issue Test Mine 3', 'country': 'Canada', 'commodity': 'Copper', 'region': 'Ontario'},
                {'mine_name': 'Critical Issue Test Mine 4', 'country': 'Australia', 'commodity': 'Iron', 'region': 'Western Australia'}
            ]
            
            critical_test_models = ['openrouter:kimi-k2', 'openrouter:deepseek-free']
            
            # Get initial database state
            initial_db_results = db_manager.get_search_results(limit=200)
            initial_count = len([r for r in initial_db_results if r.session_id == self.session_id])
            
            # Execute the workflow that previously failed
            critical_result = await batch_priority_coordinator.coordinate_priority_batch_execution(
                mines_data=critical_test_mines,
                selected_models=critical_test_models,
                session_id=self.session_id,
                batch_options={'critical_issue_resolution_test': True},
                priority_level="high"
            )
            
            # Wait for all operations to complete
            await asyncio.sleep(5)
            
            # Validate that ALL mines were processed, not just the last one
            final_db_results = db_manager.get_search_results(limit=200)
            final_count = len([r for r in final_db_results if r.session_id == self.session_id])
            
            # Check which specific mines were processed
            processed_mines = set()
            model_mine_combinations = set()
            
            for db_result in final_db_results:
                if db_result.session_id == self.session_id:
                    processed_mines.add(db_result.mine_name)
                    model_mine_combinations.add((db_result.mine_name, db_result.model_used))
            
            expected_mine_names = {mine['mine_name'] for mine in critical_test_mines}
            expected_combinations = len(critical_test_mines) * len(critical_test_models)
            
            # Critical Issue Resolution Analysis
            critical_resolution_analysis = {
                'batch_coordinator_success': critical_result.get('success', False),
                'all_mines_processed': expected_mine_names.issubset(processed_mines),
                'first_mine_processed': 'Critical Issue Test Mine 1' in processed_mines,
                'middle_mines_processed': all(name in processed_mines for name in ['Critical Issue Test Mine 2', 'Critical Issue Test Mine 3']),
                'last_mine_processed': 'Critical Issue Test Mine 4' in processed_mines,
                'not_only_last_mine': len(processed_mines) > 1,
                'expected_mine_count': len(critical_test_mines),
                'actual_mines_processed': len(processed_mines),
                'expected_model_combinations': expected_combinations,
                'actual_model_combinations': len(model_mine_combinations),
                'all_model_mine_combinations': len(model_mine_combinations) >= len(critical_test_mines)
            }
            
            # The critical issue is resolved if ALL mines are processed, not just the last one
            critical_issue_resolved = (
                critical_resolution_analysis['all_mines_processed'] and
                critical_resolution_analysis['not_only_last_mine'] and
                critical_resolution_analysis['first_mine_processed'] and
                critical_resolution_analysis['middle_mines_processed']
            )
            
            return {
                'success': True,
                'critical_issue_resolved': critical_issue_resolved,
                'batch_success': critical_result.get('success', False),
                'mines_in_test': len(critical_test_mines),
                'mines_processed': len(processed_mines),
                'models_tested': len(critical_test_models),
                'database_entries_added': final_count - initial_count,
                'expected_combinations': expected_combinations,
                'actual_combinations': len(model_mine_combinations),
                'processed_mine_names': list(processed_mines),
                'critical_resolution_analysis': critical_resolution_analysis,
                'original_problem_fixed': critical_issue_resolved
            }
            
        except Exception as e:
            logger.error(f"[INTEGRATION-TESTS] Critical issue resolution test failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def test_complete_csv_workflow_integration(self) -> Dict[str, Any]:
        """Test der kompletten CSV-zu-Database-zu-Frontend Workflow"""
        try:
            # CSV-ähnliche Daten (simuliert Upload)
            csv_workflow_mines = [
                {'mine_name': 'CSV Workflow Mine A', 'country': 'Canada', 'commodity': 'Uranium', 'region': 'Saskatchewan'},
                {'mine_name': 'CSV Workflow Mine B', 'country': 'Chile', 'commodity': 'Lithium', 'region': 'Atacama'},
                {'mine_name': 'CSV Workflow Mine C', 'country': 'Brazil', 'commodity': 'Iron', 'region': 'Minas Gerais'},
            ]
            
            csv_workflow_models = ['perplexity:sonar-pro', 'openrouter:claude-3.5-sonnet']
            
            # Execute complete CSV workflow
            workflow_result = await enhanced_batch_service.process_csv_batch_workflow(
                mines_data=csv_workflow_mines,
                selected_models=csv_workflow_models,
                session_id=self.session_id,
                csv_source_name="workflow_integration_test.csv"
            )
            
            # Validate database integration
            db_results = db_manager.get_search_results(limit=100)
            workflow_entries = [r for r in db_results if r.session_id == self.session_id and 'CSV Workflow Mine' in r.mine_name]
            
            # Validate HTML generation
            try:
                html_results = create_batch_results_table(workflow_entries)
                html_generated = len(html_results) > 100  # Basic HTML structure check
            except Exception as html_e:
                logger.warning(f"[INTEGRATION-TESTS] HTML generation warning: {str(html_e)}")
                html_generated = False
            
            workflow_success = (
                workflow_result.get('success', False) and
                len(workflow_entries) >= len(csv_workflow_mines) and
                html_generated
            )
            
            return {
                'success': workflow_success,
                'batch_processing_success': workflow_result.get('success', False),
                'database_entries_created': len(workflow_entries),
                'html_generation_success': html_generated,
                'models_per_mine': len(csv_workflow_models),
                'expected_total_entries': len(csv_workflow_mines) * len(csv_workflow_models),
                'workflow_complete': workflow_success
            }
            
        except Exception as e:
            logger.error(f"[INTEGRATION-TESTS] CSV workflow integration test failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def test_all_models_all_mines_guarantee(self) -> Dict[str, Any]:
        """Test dass für alle Minen alle Modelle verwendet werden"""
        try:
            guarantee_test_mines = [
                {'mine_name': 'Guarantee Mine Alpha', 'country': 'Peru', 'commodity': 'Zinc', 'region': 'Ancash'},
                {'mine_name': 'Guarantee Mine Beta', 'country': 'Mexico', 'commodity': 'Silver', 'region': 'Zacatecas'},
            ]
            
            guarantee_test_models = ['abacus:deep-agent', 'openrouter:kimi-k2', 'perplexity:sonar-reasoning-pro']
            
            # Execute with guarantee
            guarantee_result = await batch_priority_coordinator.coordinate_priority_batch_execution(
                mines_data=guarantee_test_mines,
                selected_models=guarantee_test_models,
                session_id=self.session_id,
                batch_options={'guarantee_all_models_all_mines': True},
                priority_level="high"
            )
            
            await asyncio.sleep(3)
            
            # Validate guarantee compliance
            db_results = db_manager.get_search_results(limit=150)
            guarantee_entries = [r for r in db_results if r.session_id == self.session_id and 'Guarantee Mine' in r.mine_name]
            
            # Check if each mine has results from each model
            mine_model_matrix = {}
            for entry in guarantee_entries:
                mine_name = entry.mine_name
                model_name = entry.model_used
                if mine_name not in mine_model_matrix:
                    mine_model_matrix[mine_name] = set()
                mine_model_matrix[mine_name].add(model_name)
            
            # Validate matrix completeness
            expected_models_per_mine = set(guarantee_test_models)
            matrix_complete = True
            missing_combinations = []
            
            for mine_data in guarantee_test_mines:
                mine_name = mine_data['mine_name']
                if mine_name not in mine_model_matrix:
                    matrix_complete = False
                    missing_combinations.extend([(mine_name, model) for model in guarantee_test_models])
                else:
                    missing_models = expected_models_per_mine - mine_model_matrix[mine_name]
                    if missing_models:
                        matrix_complete = False
                        missing_combinations.extend([(mine_name, model) for model in missing_models])
            
            return {
                'success': matrix_complete,
                'guarantee_batch_success': guarantee_result.get('success', False),
                'expected_combinations': len(guarantee_test_mines) * len(guarantee_test_models),
                'actual_combinations': len(guarantee_entries),
                'mine_model_matrix_complete': matrix_complete,
                'missing_combinations': missing_combinations,
                'mines_tested': len(guarantee_test_mines),
                'models_tested': len(guarantee_test_models),
                'guarantee_fulfilled': matrix_complete
            }
            
        except Exception as e:
            logger.error(f"[INTEGRATION-TESTS] All models all mines guarantee test failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def test_database_completeness_guarantee(self) -> Dict[str, Any]:
        """Test dass Datenbank vollständig und konsistent befüllt wird"""
        try:
            completeness_test_mines = [
                {'mine_name': 'DB Completeness Mine 1', 'country': 'South Africa', 'commodity': 'Platinum', 'region': 'Rustenburg'},
                {'mine_name': 'DB Completeness Mine 2', 'country': 'Russia', 'commodity': 'Palladium', 'region': 'Norilsk'},
            ]
            
            completeness_test_models = ['openrouter:deepseek-free', 'perplexity:sonar-pro']
            
            # Get database state before test
            initial_db_state = db_manager.get_search_results(limit=200)
            initial_test_entries = [r for r in initial_db_state if r.session_id == self.session_id and 'DB Completeness Mine' in r.mine_name]
            
            # Execute batch with database completeness guarantee
            completeness_result = await enhanced_batch_service.process_batch_with_database_guarantee(
                mines_data=completeness_test_mines,
                selected_models=completeness_test_models,
                session_id=self.session_id,
                guarantee_options={'ensure_database_completeness': True}
            )
            
            await asyncio.sleep(4)
            
            # Validate database completeness
            final_db_state = db_manager.get_search_results(limit=200)
            final_test_entries = [r for r in final_db_state if r.session_id == self.session_id and 'DB Completeness Mine' in r.mine_name]
            
            # Check data integrity
            completeness_analysis = {
                'entries_before': len(initial_test_entries),
                'entries_after': len(final_test_entries),
                'entries_added': len(final_test_entries) - len(initial_test_entries),
                'expected_entries': len(completeness_test_mines) * len(completeness_test_models),
                'all_required_fields_present': True,
                'no_duplicate_entries': True,
                'all_entries_have_session_id': True
            }
            
            # Validate required fields and consistency
            required_fields = ['mine_name', 'model_used', 'session_id', 'search_timestamp']
            seen_combinations = set()
            
            for entry in final_test_entries:
                # Check required fields
                for field in required_fields:
                    if not hasattr(entry, field) or getattr(entry, field) is None:
                        completeness_analysis['all_required_fields_present'] = False
                
                # Check for duplicates
                combination_key = (entry.mine_name, entry.model_used)
                if combination_key in seen_combinations:
                    completeness_analysis['no_duplicate_entries'] = False
                seen_combinations.add(combination_key)
                
                # Check session ID consistency
                if entry.session_id != self.session_id:
                    completeness_analysis['all_entries_have_session_id'] = False
            
            database_completeness_achieved = (
                completeness_analysis['entries_added'] >= completeness_analysis['expected_entries'] and
                completeness_analysis['all_required_fields_present'] and
                completeness_analysis['no_duplicate_entries'] and
                completeness_analysis['all_entries_have_session_id']
            )
            
            return {
                'success': database_completeness_achieved,
                'batch_success': completeness_result.get('success', False),
                'completeness_analysis': completeness_analysis,
                'database_integrity_check': database_completeness_achieved,
                'mines_tested': len(completeness_test_mines),
                'models_tested': len(completeness_test_models)
            }
            
        except Exception as e:
            logger.error(f"[INTEGRATION-TESTS] Database completeness guarantee test failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def test_frontend_display_completeness(self) -> Dict[str, Any]:
        """Test dass Frontend alle Daten vollständig anzeigt"""
        try:
            frontend_test_mines = [
                {'mine_name': 'Frontend Display Mine X', 'country': 'Kazakhstan', 'commodity': 'Uranium', 'region': 'Kyzylorda'},
            ]
            
            frontend_test_models = ['openrouter:claude-3.5-sonnet', 'abacus:deep-agent']
            
            # Execute batch for frontend testing
            frontend_result = await batch_priority_coordinator.coordinate_priority_batch_execution(
                mines_data=frontend_test_mines,
                selected_models=frontend_test_models,
                session_id=self.session_id,
                batch_options={'optimize_for_frontend_display': True},
                priority_level="medium"
            )
            
            await asyncio.sleep(3)
            
            # Get data for frontend display
            frontend_db_entries = db_manager.get_search_results(limit=100)
            frontend_entries = [r for r in frontend_db_entries if r.session_id == self.session_id and 'Frontend Display Mine' in r.mine_name]
            
            # Test HTML generation with all entries
            try:
                comprehensive_html = create_comprehensive_results_page(frontend_entries)
                batch_html = create_batch_results_table(frontend_entries)
                
                html_generation_success = (
                    len(comprehensive_html) > 500 and  # Substantial HTML content
                    len(batch_html) > 200 and  # Table HTML content
                    'Frontend Display Mine X' in comprehensive_html and
                    'Frontend Display Mine X' in batch_html
                )
                
                html_error = None
            except Exception as html_e:
                html_generation_success = False
                html_error = str(html_e)
                comprehensive_html = ""
                batch_html = ""
            
            frontend_display_complete = (
                frontend_result.get('success', False) and
                len(frontend_entries) >= len(frontend_test_models) and
                html_generation_success
            )
            
            return {
                'success': frontend_display_complete,
                'batch_success': frontend_result.get('success', False),
                'database_entries_for_display': len(frontend_entries),
                'html_generation_success': html_generation_success,
                'html_error': html_error,
                'comprehensive_html_length': len(comprehensive_html),
                'batch_html_length': len(batch_html),
                'frontend_ready': frontend_display_complete
            }
            
        except Exception as e:
            logger.error(f"[INTEGRATION-TESTS] Frontend display completeness test failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def test_system_coordination_effectiveness(self) -> Dict[str, Any]:
        """Test der Koordination zwischen allen System-Komponenten"""
        try:
            coordination_test_mines = [
                {'mine_name': 'System Coordination Mine Alpha', 'country': 'Norway', 'commodity': 'Cobalt', 'region': 'Finnmark'},
                {'mine_name': 'System Coordination Mine Beta', 'country': 'DRC', 'commodity': 'Cobalt', 'region': 'Katanga'},
            ]
            
            coordination_test_models = ['perplexity:sonar-reasoning-pro', 'openrouter:kimi-k2']
            
            # Test coordination between all major components
            coordination_results = {}
            
            # 1. Model Selection Coordinator
            try:
                model_selection = await model_selection_coordinator.select_optimal_models_for_batch(
                    mines_data=coordination_test_mines,
                    available_models=coordination_test_models,
                    selection_criteria={'priority': 'balanced', 'cost_limit': 1000}
                )
                coordination_results['model_selection_coordinator'] = {'success': True, 'selected_models': model_selection}
            except Exception as e:
                coordination_results['model_selection_coordinator'] = {'success': False, 'error': str(e)}
            
            # 2. Enhanced Batch Service
            try:
                batch_execution = await enhanced_batch_service.execute_enhanced_batch(
                    mines_data=coordination_test_mines,
                    selected_models=coordination_test_models,
                    session_id=self.session_id,
                    batch_options={'coordination_test': True}
                )
                coordination_results['enhanced_batch_service'] = {'success': batch_execution.get('success', False)}
            except Exception as e:
                coordination_results['enhanced_batch_service'] = {'success': False, 'error': str(e)}
            
            # 3. Cost Monitor Integration
            try:
                cost_status = await cost_monitor.get_current_cost_status()
                cost_valid = isinstance(cost_status, dict) and 'total_cost' in cost_status
                coordination_results['cost_monitor'] = {'success': cost_valid, 'cost_status': cost_status}
            except Exception as e:
                coordination_results['cost_monitor'] = {'success': False, 'error': str(e)}
            
            # 4. Database Manager Integration
            try:
                db_health = db_manager.check_database_health()
                coordination_results['database_manager'] = {'success': True, 'health_status': db_health}
            except Exception as e:
                coordination_results['database_manager'] = {'success': False, 'error': str(e)}
            
            await asyncio.sleep(2)
            
            # Evaluate overall coordination effectiveness
            successful_components = sum(1 for comp in coordination_results.values() if comp['success'])
            total_components = len(coordination_results)
            coordination_effectiveness = successful_components / total_components
            
            system_coordination_effective = coordination_effectiveness >= 0.8  # 80% success rate
            
            return {
                'success': system_coordination_effective,
                'coordination_effectiveness_percent': coordination_effectiveness * 100,
                'successful_components': successful_components,
                'total_components': total_components,
                'component_results': coordination_results,
                'coordination_threshold_met': system_coordination_effective
            }
            
        except Exception as e:
            logger.error(f"[INTEGRATION-TESTS] System coordination effectiveness test failed: {str(e)}")
            return {'success': False, 'error': str(e)}

# Globale Test Suite Instanz
integration_test_suites = IntegrationTestSuites