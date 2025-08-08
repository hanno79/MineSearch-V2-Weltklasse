#!/usr/bin/env python3
"""
Author: rahn
Datum: 25.07.2025
Version: 1.0
Beschreibung: Comprehensive Workflow Integration Test - Validiert alle Coordinator-Komponenten
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, Any, List

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def comprehensive_workflow_integration_test():
    """
    Führt umfassende Integration Tests für alle Workflow-Komponenten durch
    """
    logger.info("=" * 80)
    logger.info("🚀 COMPREHENSIVE WORKFLOW INTEGRATION TEST GESTARTET")
    logger.info("=" * 80)
    
    test_results = {
        'start_time': datetime.now().isoformat(),
        'tests': {},
        'overall_success': True,
        'summary': {}
    }
    
    try:
        # TEST 1: Model Selection Coordinator
        logger.info("\n📋 TEST 1: Model Selection Coordinator Validation")
        model_coordinator_result = await test_model_selection_coordinator()
        test_results['tests']['model_selection_coordinator'] = model_coordinator_result
        if not model_coordinator_result.get('success'):
            test_results['overall_success'] = False
        
        # TEST 2: Batch Priority Coordinator
        logger.info("\n📋 TEST 2: Batch Priority Coordinator Validation")
        batch_coordinator_result = await test_batch_priority_coordinator()
        test_results['tests']['batch_priority_coordinator'] = batch_coordinator_result
        if not batch_coordinator_result.get('success'):
            test_results['overall_success'] = False
        
        # TEST 3: Workflow Orchestrator
        logger.info("\n📋 TEST 3: Workflow Orchestrator Validation")
        workflow_orchestrator_result = await test_workflow_orchestrator()
        test_results['tests']['workflow_orchestrator'] = workflow_orchestrator_result
        if not workflow_orchestrator_result.get('success'):
            test_results['overall_success'] = False
        
        # TEST 4: Database Integration
        logger.info("\n📋 TEST 4: Database Integration Validation")
        database_integration_result = await test_database_integration()
        test_results['tests']['database_integration'] = database_integration_result
        if not database_integration_result.get('success'):
            test_results['overall_success'] = False
        
        # TEST 5: End-to-End Workflow
        logger.info("\n📋 TEST 5: End-to-End Workflow Integration")
        e2e_workflow_result = await test_end_to_end_workflow()
        test_results['tests']['e2e_workflow'] = e2e_workflow_result
        if not e2e_workflow_result.get('success'):
            test_results['overall_success'] = False
        
    except Exception as e:
        logger.error(f"❌ KRITISCHER FEHLER beim Integration Test: {str(e)}")
        test_results['overall_success'] = False
        test_results['critical_error'] = str(e)
    
    # Erstelle Zusammenfassung
    test_results['end_time'] = datetime.now().isoformat()
    test_results['duration_seconds'] = (
        datetime.fromisoformat(test_results['end_time']) - 
        datetime.fromisoformat(test_results['start_time'])
    ).total_seconds()
    
    # Erstelle Summary
    successful_tests = len([t for t in test_results['tests'].values() if t.get('success')])
    total_tests = len(test_results['tests'])
    
    test_results['summary'] = {
        'total_tests': total_tests,
        'successful_tests': successful_tests,
        'failed_tests': total_tests - successful_tests,
        'success_rate': successful_tests / total_tests * 100 if total_tests > 0 else 0,
        'overall_success': test_results['overall_success']
    }
    
    # Log Endergebnis
    logger.info("\n" + "=" * 80)
    logger.info("📊 COMPREHENSIVE WORKFLOW INTEGRATION TEST ERGEBNISSE")
    logger.info("=" * 80)
    logger.info(f"✅ Erfolgreiche Tests: {successful_tests}/{total_tests}")
    logger.info(f"📈 Erfolgsrate: {test_results['summary']['success_rate']:.1f}%")
    logger.info(f"⏱️  Gesamtdauer: {test_results['duration_seconds']:.1f}s")
    logger.info(f"🎯 Gesamtergebnis: {'✅ ERFOLGREICH' if test_results['overall_success'] else '❌ FEHLGESCHLAGEN'}")
    logger.info("=" * 80)
    
    # Speichere Testergebnisse
    with open(f'/app/minesearch_v2/backend/workflow_integration_test_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json', 'w') as f:
        json.dump(test_results, f, indent=2, default=str)
    
    return test_results

async def test_model_selection_coordinator():
    """Test Model Selection Coordinator"""
    try:
        from model_selection_coordinator import model_selection_coordinator
        
        logger.info("🔍 Teste Model Selection Coordinator...")
        
        # Test mit mehreren Modellen
        test_models = ['openrouter:kimi-k2', 'openrouter:deepseek-r1-lite']
        
        result = await model_selection_coordinator.coordinate_guaranteed_execution(
            selected_models=test_models,
            mine_name='Test Mine for Coordinator',
            country='Canada',
            commodity='Gold',
            region='Quebec',
            session_id='integration_test_model_coordinator',
            allow_fallbacks=False,
            max_parallel=2
        )
        
        # Validiere Ergebnis
        success = (
            result.get('success', False) and
            len(result.get('models_requested', [])) == len(test_models) and
            result.get('execution_mode') == 'guaranteed_execution'
        )
        
        return {
            'success': success,
            'test_name': 'model_selection_coordinator',
            'test_models': test_models,
            'result_summary': {
                'models_requested': len(result.get('models_requested', [])),
                'models_successful': len(result.get('models_successful', [])),
                'execution_mode': result.get('execution_mode'),
                'coordination_duration': result.get('coordination_duration_seconds', 0)
            },
            'full_result': result if success else {'error': 'Test validation failed'}
        }
        
    except Exception as e:
        logger.error(f"❌ Model Selection Coordinator Test fehlgeschlagen: {str(e)}")
        return {
            'success': False,
            'test_name': 'model_selection_coordinator',
            'error': str(e)
        }

async def test_batch_priority_coordinator():
    """Test Batch Priority Coordinator"""
    try:
        from batch_priority_coordinator import batch_priority_coordinator
        
        logger.info("🔍 Teste Batch Priority Coordinator...")
        
        # Test mit mehreren Minen
        test_mines = [
            {'mine_name': 'Integration Test Mine 1', 'country': 'Canada', 'commodity': 'Gold'},
            {'mine_name': 'Integration Test Mine 2', 'country': 'Canada', 'commodity': 'Silver'}
        ]
        test_models = ['openrouter:kimi-k2']
        
        result = await batch_priority_coordinator.coordinate_priority_batch_execution(
            mines_data=test_mines,
            selected_models=test_models,
            session_id='integration_test_batch_coordinator',
            batch_options={'test_mode': True},
            priority_level='high'
        )
        
        # Validiere Ergebnis
        batch_stats = result.get('batch_statistics', {})
        success = (
            result.get('success', False) and
            batch_stats.get('total_mines', 0) == len(test_mines) and
            result.get('coordination_mode') == 'priority_coordinated_batch'
        )
        
        return {
            'success': success,
            'test_name': 'batch_priority_coordinator',
            'test_mines_count': len(test_mines),
            'test_models': test_models,
            'result_summary': {
                'total_mines': batch_stats.get('total_mines', 0),
                'successful_mine_searches': batch_stats.get('successful_mine_searches', 0),
                'overall_success_rate': batch_stats.get('overall_success_rate', 0),
                'coordination_duration': result.get('execution_duration_seconds', 0)
            },
            'full_result': result if success else {'error': 'Test validation failed'}
        }
        
    except Exception as e:
        logger.error(f"❌ Batch Priority Coordinator Test fehlgeschlagen: {str(e)}")
        return {
            'success': False,
            'test_name': 'batch_priority_coordinator',
            'error': str(e)
        }

async def test_workflow_orchestrator():
    """Test Workflow Orchestrator"""
    try:
        from workflow_orchestrator import workflow_orchestrator, WorkflowMode
        
        logger.info("🔍 Teste Workflow Orchestrator...")
        
        # Test Single Mine Workflow
        workflow_request = {
            'mine_name': 'Orchestrator Test Mine',
            'selected_models': ['openrouter:kimi-k2'],
            'country': 'Canada',
            'commodity': 'Copper',
            'region': 'Quebec',
            'allow_fallbacks': False,
            'max_parallel': 1
        }
        
        result = await workflow_orchestrator.orchestrate_workflow(
            workflow_mode=WorkflowMode.SINGLE_MINE_SEARCH,
            workflow_request=workflow_request,
            session_id='integration_test_workflow_orchestrator',
            priority='high'
        )
        
        # Validiere Ergebnis
        workflow_result = result.get('workflow_result', {})
        success = (
            result.get('success', False) and
            result.get('workflow_mode') == 'single_mine' and
            workflow_result.get('execution_strategy') == 'single_mine_coordinated'
        )
        
        return {
            'success': success,
            'test_name': 'workflow_orchestrator',
            'workflow_mode': 'single_mine_search',
            'result_summary': {
                'workflow_mode': result.get('workflow_mode'),
                'orchestration_duration': result.get('orchestration_duration_seconds', 0),
                'execution_strategy': workflow_result.get('execution_strategy'),
                'coordinators_used': result.get('orchestration_metadata', {}).get('coordinators_used', [])
            },
            'full_result': result if success else {'error': 'Test validation failed'}
        }
        
    except Exception as e:
        logger.error(f"❌ Workflow Orchestrator Test fehlgeschlagen: {str(e)}")
        return {
            'success': False,
            'test_name': 'workflow_orchestrator',
            'error': str(e)
        }

async def test_database_integration():
    """Test Database Integration"""
    try:
        from database import db_manager
        
        logger.info("🔍 Teste Database Integration...")
        
        # Test Database Statistics
        db_stats = db_manager.get_statistics()
        
        # Test Database Connection
        test_result = db_manager.save_search_result(
            mine_name='Integration Test Database Mine',
            model_used='integration_test_model',
            structured_data={'test_field': 'test_value'},
            sources=[],
            session_id='integration_test_database',
            country='Canada',
            region='Quebec',
            commodity='Test',
            search_type='integration_test',
            search_duration=1.0,
            success=True
        )
        
        # Validiere Database-Funktionalität
        success = (
            isinstance(db_stats, dict) and
            'total_results' in db_stats and
            test_result is not None
        )
        
        return {
            'success': success,
            'test_name': 'database_integration',
            'result_summary': {
                'total_results': db_stats.get('total_results', 0),
                'successful_results': db_stats.get('successful_results', 0),
                'total_sources': db_stats.get('total_sources', 0),
                'test_save_successful': test_result is not None
            },
            'db_stats': db_stats if success else {'error': 'Database test failed'}
        }
        
    except Exception as e:
        logger.error(f"❌ Database Integration Test fehlgeschlagen: {str(e)}")
        return {
            'success': False,
            'test_name': 'database_integration',
            'error': str(e)
        }

async def test_end_to_end_workflow():
    """Test End-to-End Workflow Integration"""
    try:
        from workflow_orchestrator import workflow_orchestrator, WorkflowMode
        
        logger.info("🔍 Teste End-to-End Workflow Integration...")
        
        # Test komplettes Batch-Workflow mit mehreren Komponenten
        test_mines = [
            {'mine_name': 'E2E Test Mine Alpha', 'country': 'Canada', 'commodity': 'Gold', 'region': 'Quebec'},
            {'mine_name': 'E2E Test Mine Beta', 'country': 'Canada', 'commodity': 'Silver', 'region': 'Ontario'}
        ]
        test_models = ['openrouter:kimi-k2', 'openrouter:deepseek-r1-lite']
        
        workflow_request = {
            'mines_data': test_mines,
            'selected_models': test_models,
            'batch_options': {
                'comprehensive_search': 'false',
                'consistency_check': 'false',
                'e2e_test_mode': True
            }
        }
        
        result = await workflow_orchestrator.orchestrate_workflow(
            workflow_mode=WorkflowMode.BATCH_PROCESSING,
            workflow_request=workflow_request,
            session_id='integration_test_e2e_workflow',
            priority='high'
        )
        
        # Validiere End-to-End Integration
        workflow_result = result.get('workflow_result', {})
        batch_stats = workflow_result.get('batch_statistics', {})
        
        success = (
            result.get('success', False) and
            result.get('workflow_mode') == 'batch_processing' and
            batch_stats.get('total_mines', 0) == len(test_mines) and
            batch_stats.get('total_models_per_mine', 0) == len(test_models)
        )
        
        return {
            'success': success,
            'test_name': 'e2e_workflow_integration',
            'workflow_components': ['workflow_orchestrator', 'batch_priority_coordinator', 'model_selection_coordinator', 'database_manager'],
            'result_summary': {
                'total_mines_processed': batch_stats.get('total_mines', 0),
                'total_model_executions': batch_stats.get('total_model_executions', 0),
                'successful_mine_searches': batch_stats.get('successful_mine_searches', 0),
                'overall_success_rate': batch_stats.get('overall_success_rate', 0),
                'orchestration_duration': result.get('orchestration_duration_seconds', 0),
                'database_operations': workflow_result.get('database_operations', {})
            },
            'full_result': result if success else {'error': 'E2E test validation failed'}
        }
        
    except Exception as e:
        logger.error(f"❌ End-to-End Workflow Test fehlgeschlagen: {str(e)}")
        return {
            'success': False,
            'test_name': 'e2e_workflow_integration',
            'error': str(e)
        }

if __name__ == "__main__":
    # Führe comprehensive integration test aus
    asyncio.run(comprehensive_workflow_integration_test())