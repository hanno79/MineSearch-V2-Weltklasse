"""
Author: rahn
Datum: 23.07.2025
Version: 1.0
Beschreibung: Comprehensive Test Suite für Source Performance Tracking System
"""

import unittest
import asyncio
import tempfile
import os
import logging
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, List, Any

# Test imports
import sys
sys.path.append(os.path.dirname(__file__))

# Konfiguriere Test-Logging (nur bei expliziter Aktivierung)
TEST_VERBOSE = os.getenv('TEST_VERBOSE', 'false').lower() == 'true'
if TEST_VERBOSE:
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
test_logger = logging.getLogger(__name__) if TEST_VERBOSE else None

from source_stats_manager import SourceStatsManager, SourcePerformanceMetrics
from source_auto_reset_service import SourceAutoResetService
from source_performance_logger import SourcePerformanceLogger


class TestSourcePerformanceMetrics(unittest.TestCase):
    """Tests für SourcePerformanceMetrics Klasse"""
    
    def setUp(self):
        """Setup für jeden Test"""
        self.metrics = SourcePerformanceMetrics(
            url="https://example.com/test",
            domain="example.com",
            source_type="industry"
        )
    
    def test_calculate_overall_score_no_attempts(self):
        """Test Overall Score Berechnung ohne Versuche"""
        score = self.metrics.calculate_overall_score()
        self.assertEqual(score, 0.0)
    
    def test_calculate_overall_score_with_data(self):
        """Test Overall Score Berechnung mit Daten"""
        self.metrics.total_attempts = 10
        self.metrics.successful_attempts = 8
        self.metrics.data_richness_score = 60.0
        self.metrics.reliability_score = 70.0
        self.metrics.last_success = datetime.now() - timedelta(days=1)
        
        score = self.metrics.calculate_overall_score()
        self.assertGreater(score, 50.0)
        self.assertLessEqual(score, 100.0)
    
    def test_should_auto_reset_consecutive_failures(self):
        """Test Auto-Reset bei consecutive failures"""
        self.metrics.consecutive_failures = 10
        self.assertTrue(self.metrics.should_auto_reset())
        self.assertIn("consecutive failures", self.metrics.reset_reason)
    
    def test_should_auto_reset_low_success_rate(self):
        """Test Auto-Reset bei niedriger Success Rate"""
        self.metrics.total_attempts = 25
        self.metrics.successful_attempts = 1  # 4% success rate
        self.assertTrue(self.metrics.should_auto_reset())
        self.assertIn("Success rate below 10%", self.metrics.reset_reason)
    
    def test_should_auto_reset_stale_source(self):
        """Test Auto-Reset bei veralteter Quelle"""
        self.metrics.last_success = datetime.now() - timedelta(days=200)
        self.assertTrue(self.metrics.should_auto_reset())
        self.assertIn("No success in 180+ days", self.metrics.reset_reason)
    
    def test_reset_statistics(self):
        """Test Reset der Statistiken"""
        self.metrics.total_attempts = 20
        self.metrics.successful_attempts = 5
        self.metrics.consecutive_failures = 8
        self.metrics.needs_reset = True
        self.metrics.reset_reason = "Test reset"
        
        self.metrics.reset_statistics()
        
        self.assertEqual(self.metrics.total_attempts, 0)
        self.assertEqual(self.metrics.successful_attempts, 0)
        self.assertEqual(self.metrics.consecutive_failures, 0)
        self.assertFalse(self.metrics.needs_reset)
        self.assertIsNotNone(self.metrics.last_reset)


class TestSourceStatsManager(unittest.IsolatedAsyncioTestCase):
    """Tests für SourceStatsManager Klasse"""
    
    def setUp(self):
        """Setup für jeden Test"""
        # Mock database manager
        self.mock_db = Mock()
        self.mock_session = Mock()
        self.mock_db.get_session.return_value.__enter__.return_value = self.mock_session
        
        # Mock performance logger
        self.mock_logger = Mock()
        
        # Create manager with mocked dependencies
        with patch('source_stats_manager.db_manager', self.mock_db), \
             patch('source_stats_manager.source_performance_logger', self.mock_logger):
            self.manager = SourceStatsManager()
    
    async def test_update_source_performance_success(self):
        """Test erfolgreiche Source Performance Update"""
        await self.manager.update_source_performance(
            url="https://test.com",
            success=True,
            search_duration=2.5,
            fields_found=8,
            content_type="html"
        )
        
        # Überprüfe ob Metriken erstellt wurden
        self.assertIn("https://test.com", self.manager._stats_cache)
        metrics = self.manager._stats_cache["https://test.com"]
        
        self.assertEqual(metrics.total_attempts, 1)
        self.assertEqual(metrics.successful_attempts, 1)
        self.assertEqual(metrics.avg_response_time, 2.5)
        self.assertIn("html", metrics.content_types_found)
        
        # Überprüfe Logging
        self.mock_logger.log_source_update.assert_called_once()
    
    async def test_update_source_performance_failure(self):
        """Test fehlgeschlagene Source Performance Update"""
        await self.manager.update_source_performance(
            url="https://test.com",
            success=False,
            search_duration=1.0
        )
        
        metrics = self.manager._stats_cache["https://test.com"]
        self.assertEqual(metrics.total_attempts, 1)
        self.assertEqual(metrics.successful_attempts, 0)
        self.assertEqual(metrics.consecutive_failures, 1)
        
        # Überprüfe Logging
        self.mock_logger.log_source_update.assert_called_once()
    
    async def test_batch_update_sources(self):
        """Test Batch-Update von Quellen"""
        # Bereite einige Updates vor
        await self.manager.update_source_performance("https://test1.com", True, 1.0, 5)
        await self.manager.update_source_performance("https://test2.com", False, 2.0, 0)
        
        # Mock Source objects
        mock_source1 = Mock()
        mock_source2 = Mock()
        self.mock_session.query.return_value.filter_by.side_effect = [
            Mock(first=Mock(return_value=mock_source1)),
            Mock(first=Mock(return_value=mock_source2))
        ]
        
        # Führe Batch-Update durch
        updated_count = await self.manager.batch_update_sources()
        
        # Überprüfe dass Updates geleert wurden
        self.assertEqual(len(self.manager._batch_updates), 0)
        self.assertEqual(updated_count, 2)
        
        # Überprüfe Logging
        self.mock_logger.log_batch_update.assert_called_once()
    
    async def test_get_top_performing_sources(self):
        """Test Top-performing Sources abrufen"""
        # Mock database response
        mock_sources = [
            Mock(url="https://good1.com", total_searches=20, successful_searches=18, 
                 reliability_score=85.0, domain="good1.com", source_type="government"),
            Mock(url="https://good2.com", total_searches=15, successful_searches=12,
                 reliability_score=80.0, domain="good2.com", source_type="database")
        ]
        
        self.mock_session.query.return_value.filter.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_sources
        
        # Teste Abruf
        top_sources = await self.manager.get_top_performing_sources(limit=2)
        
        self.assertEqual(len(top_sources), 2)
        self.assertEqual(top_sources[0].url, "https://good1.com")
        self.assertEqual(top_sources[1].url, "https://good2.com")
    
    async def test_performance_summary(self):
        """Test Performance Summary"""
        # Mock database statistics
        self.mock_session.query.return_value.count.return_value = 100
        self.mock_session.query.return_value.filter.return_value.count.return_value = 80
        self.mock_session.query.return_value.filter.return_value.all.return_value = []
        
        summary = await self.manager.get_performance_summary()
        
        self.assertIn('source_statistics', summary)
        self.assertIn('total_sources', summary['source_statistics'])
        self.assertIn('operation_stats', summary)


class TestSourceAutoResetService(unittest.IsolatedAsyncioTestCase):
    """Tests für SourceAutoResetService Klasse"""
    
    def setUp(self):
        """Setup für jeden Test"""
        # Mock stats manager
        self.mock_stats_manager = Mock()
        
        with patch('source_auto_reset_service.source_stats_manager', self.mock_stats_manager):
            self.service = SourceAutoResetService()
    
    def test_categorize_reset_candidates(self):
        """Test Kategorisierung von Reset-Kandidaten"""
        # Erstelle Test-Metriken
        high_failure_metrics = SourcePerformanceMetrics(
            url="https://failing.com",
            domain="failing.com", 
            source_type="industry",
            total_attempts=20,
            successful_attempts=1,
            consecutive_failures=12
        )
        
        stale_metrics = SourcePerformanceMetrics(
            url="https://stale.com",
            domain="stale.com",
            source_type="government",
            total_attempts=5,
            successful_attempts=3,
            last_success=datetime.now() - timedelta(days=200)
        )
        
        candidates = [high_failure_metrics, stale_metrics]
        categorized = self.service._categorize_reset_candidates(candidates)
        
        self.assertIn('consecutive_failures', categorized)
        self.assertIn('stale_sources', categorized)
        self.assertEqual(len(categorized['consecutive_failures']), 1)
        self.assertEqual(len(categorized['stale_sources']), 1)
    
    async def test_manual_reset_source(self):
        """Test manuelles Reset einer Quelle"""
        # Mock Metriken
        test_metrics = SourcePerformanceMetrics(
            url="https://manual-reset.com",
            domain="manual-reset.com",
            source_type="industry",
            total_attempts=10,
            successful_attempts=2
        )
        
        self.mock_stats_manager.get_source_performance.return_value = test_metrics
        self.mock_stats_manager.perform_bulk_reset.return_value = 1
        
        # Teste manuelles Reset
        success = await self.service.manual_reset_source(
            url="https://manual-reset.com",
            reason="Manual test reset"
        )
        
        self.assertTrue(success)
        self.mock_stats_manager.perform_bulk_reset.assert_called_once_with(["https://manual-reset.com"])
        
        # Überprüfe Historie
        self.assertEqual(len(self.service.reset_history), 1)
        self.assertEqual(self.service.reset_history[0].url, "https://manual-reset.com")
    
    def test_get_service_status(self):
        """Test Service-Status abrufen"""
        status = self.service.get_service_status()
        
        self.assertIn('running', status)
        self.assertIn('check_interval_hours', status)
        self.assertIn('configuration', status)
        self.assertIn('total_resets_performed', status)


class TestSourcePerformanceLogger(unittest.TestCase):
    """Tests für SourcePerformanceLogger Klasse"""
    
    def setUp(self):
        """Setup für jeden Test"""
        self.logger = SourcePerformanceLogger(max_events_memory=100)
    
    def test_log_source_update(self):
        """Test Source Update Logging"""
        self.logger.log_source_update(
            url="https://test.com",
            domain="test.com",
            success=True,
            duration=1.5,
            fields_found=5,
            content_type="html"
        )
        
        self.assertEqual(len(self.logger.recent_events), 1)
        event = self.logger.recent_events[0]
        self.assertEqual(event.event_type, 'source_update')
        self.assertEqual(event.url, "https://test.com")
        self.assertTrue(event.success)
        self.assertEqual(event.duration, 1.5)
    
    def test_log_batch_update(self):
        """Test Batch Update Logging"""
        self.logger.log_batch_update(
            processed_count=10,
            duration=3.2,
            errors=["Error 1", "Error 2"]
        )
        
        self.assertEqual(len(self.logger.recent_events), 1)
        event = self.logger.recent_events[0]
        self.assertEqual(event.event_type, 'batch_update')
        self.assertFalse(event.success)  # wegen Errors
        self.assertEqual(event.metadata['processed_count'], 10)
    
    def test_log_source_reset(self):
        """Test Source Reset Logging"""
        pre_reset_stats = {
            'total_attempts': 20,
            'successful_attempts': 2,
            'quality_score': 15.0
        }
        
        self.logger.log_source_reset(
            url="https://reset.com",
            reason="Low performance",
            pre_reset_stats=pre_reset_stats
        )
        
        self.assertEqual(len(self.logger.recent_events), 1)
        event = self.logger.recent_events[0]
        self.assertEqual(event.event_type, 'reset')
        self.assertEqual(event.url, "https://reset.com")
        self.assertEqual(event.metadata['reason'], "Low performance")
    
    def test_log_error(self):
        """Test Error Logging"""
        test_exception = ValueError("Test error")
        
        self.logger.log_error(
            error_type="test_error",
            message="Test error message",
            url="https://error.com",
            exception=test_exception
        )
        
        self.assertEqual(len(self.logger.recent_events), 1)
        event = self.logger.recent_events[0]
        self.assertEqual(event.event_type, 'error')
        self.assertFalse(event.success)
        self.assertEqual(event.metadata['error_type'], "test_error")
        self.assertEqual(event.metadata['exception_type'], "ValueError")
    
    def test_get_real_time_metrics(self):
        """Test Real-Time Metriken"""
        # Füge Test-Events hinzu
        self.logger.log_source_update("https://test1.com", "test1.com", True, 1.0, 5)
        self.logger.log_source_update("https://test2.com", "test2.com", False, 2.0, 0)
        self.logger.log_batch_update(2, 1.5, [])
        
        metrics = self.logger.get_real_time_metrics(time_window_minutes=60)
        
        self.assertEqual(metrics['total_events'], 3)
        self.assertIn('success_rate', metrics)
        self.assertIn('metrics', metrics)
        self.assertIn('event_types', metrics['metrics'])
    
    def test_get_dashboard_data(self):
        """Test Dashboard-Daten"""
        # Füge Test-Events hinzu
        self.logger.log_source_update("https://test.com", "test.com", True, 1.0, 5)
        self.logger.log_error("test_error", "Test error", "https://error.com")
        
        dashboard_data = self.logger.get_dashboard_data()
        
        self.assertIn('system_health', dashboard_data)
        self.assertIn('metrics', dashboard_data)
        self.assertIn('alerts', dashboard_data)
        self.assertIn('error_analysis', dashboard_data)
        self.assertIn('system_info', dashboard_data)


class TestIntegration(unittest.IsolatedAsyncioTestCase):
    """Integration Tests für das komplette System"""
    
    def setUp(self):
        """Setup für Integration Tests"""
        # Erstelle temporäre Test-Umgebung
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock dependencies
        self.mock_db = Mock()
        self.mock_session = Mock()
        self.mock_db.get_session.return_value.__enter__.return_value = self.mock_session
        
        # Setup manager mit mocks
        with patch('source_stats_manager.db_manager', self.mock_db):
            self.manager = SourceStatsManager()
            self.auto_reset_service = SourceAutoResetService()
    
    async def test_end_to_end_workflow(self):
        """Test kompletter End-to-End Workflow"""
        # 1. Update Source Performance
        await self.manager.update_source_performance(
            url="https://integration-test.com",
            success=True,
            search_duration=1.5,
            fields_found=8,
            content_type="html"
        )
        
        # 2. Weitere Updates um schlechte Performance zu simulieren
        for i in range(5):
            await self.manager.update_source_performance(
                url="https://integration-test.com",
                success=False,
                search_duration=5.0
            )
        
        # 3. Überprüfe dass Quelle für Reset markiert ist
        metrics = await self.manager.get_source_performance("https://integration-test.com")
        self.assertIsNotNone(metrics)
        self.assertEqual(metrics.consecutive_failures, 5)
        
        # 4. Batch-Update
        mock_source = Mock()
        self.mock_session.query.return_value.filter_by.return_value.first.return_value = mock_source
        
        updated_count = await self.manager.batch_update_sources()
        self.assertGreater(updated_count, 0)
        
        # 5. Performance Summary
        summary = await self.manager.get_performance_summary()
        self.assertIn('source_statistics', summary)
    
    async def test_auto_reset_workflow(self):
        """Test Auto-Reset Workflow"""
        # Erstelle schlechte Performance-Metriken
        bad_metrics = SourcePerformanceMetrics(
            url="https://bad-source.com",
            domain="bad-source.com",
            source_type="industry",
            total_attempts=15,
            successful_attempts=1,
            consecutive_failures=12
        )
        
        # Mock get_sources_needing_reset
        self.manager.get_sources_needing_reset = AsyncMock(return_value=[bad_metrics])
        self.manager.perform_bulk_reset = AsyncMock(return_value=1)
        
        # Teste Reset-Kandidaten finden
        candidates = await self.manager.get_sources_needing_reset()
        self.assertEqual(len(candidates), 1)
        self.assertTrue(candidates[0].should_auto_reset())
        
        # Teste manuelles Reset
        success = await self.auto_reset_service.manual_reset_source(
            url="https://bad-source.com",
            reason="Integration test"
        )
        self.assertTrue(success)


def run_comprehensive_tests():
    """
    Führt alle Tests aus und erstellt einen detaillierten Report
    Ausgabe nur bei TEST_VERBOSE=true Environment Variable
    """
    def log_or_print(message):
        """Zeige Ausgabe nur wenn TEST_VERBOSE aktiviert ist"""
        if TEST_VERBOSE:
            if test_logger:
                test_logger.info(message)
            else:
                print(message)
    
    log_or_print("=" * 60)
    log_or_print("SOURCE PERFORMANCE TRACKING SYSTEM - TEST SUITE")
    log_or_print("=" * 60)
    
    # Test Loader
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Lade alle Test-Klassen
    test_classes = [
        TestSourcePerformanceMetrics,
        TestSourceStatsManager, 
        TestSourceAutoResetService,
        TestSourcePerformanceLogger,
        TestIntegration
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Test Runner - verbosity abhängig von TEST_VERBOSE
    runner = unittest.TextTestRunner(
        verbosity=2 if TEST_VERBOSE else 1,
        stream=sys.stdout if TEST_VERBOSE else open(os.devnull, 'w'),
        descriptions=TEST_VERBOSE,
        failfast=False
    )
    
    log_or_print(f"\nStarting {suite.countTestCases()} tests...\n")
    
    # Führe Tests aus
    result = runner.run(suite)
    
    # Test-Zusammenfassung nur bei Verbose oder wenn Fehler auftreten
    if TEST_VERBOSE or result.failures or result.errors:
        log_or_print("\n" + "=" * 60)
        log_or_print("TEST SUMMARY")
        log_or_print("=" * 60)
        log_or_print(f"Total Tests: {result.testsRun}")
        log_or_print(f"Successful: {result.testsRun - len(result.failures) - len(result.errors)}")
        log_or_print(f"Failures: {len(result.failures)}")
        log_or_print(f"Errors: {len(result.errors)}")
        
        if result.failures:
            log_or_print(f"\nFAILURES ({len(result.failures)}):")
            for test, traceback in result.failures:
                log_or_print(f"- {test}: {traceback.split('AssertionError:')[-1].strip() if 'AssertionError:' in traceback else 'See details above'}")
        
        if result.errors:
            log_or_print(f"\nERRORS ({len(result.errors)}):")
            for test, traceback in result.errors:
                log_or_print(f"- {test}: {traceback.split('Exception:')[-1].strip() if 'Exception:' in traceback else 'See details above'}")
        
        success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0
        log_or_print(f"\nOverall Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 95:
            log_or_print("🟢 EXCELLENT - System ready for production!")
        elif success_rate >= 90:
            log_or_print("🟡 GOOD - Minor issues to address")
        elif success_rate >= 75:
            log_or_print("🟠 ACCEPTABLE - Several issues need fixing")
        else:
            log_or_print("🔴 CRITICAL - Major issues require attention")
        
        log_or_print("=" * 60)
    
    return result


if __name__ == "__main__":
    """
    Führe Tests aus wenn Skript direkt ausgeführt wird
    """
    success = run_comprehensive_tests()
    
    # Exit Code setzen
    sys.exit(0 if success else 1)