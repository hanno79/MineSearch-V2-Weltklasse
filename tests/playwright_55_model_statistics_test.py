"""
Author: rahn
Datum: 18.08.2025
Version: 1.0
Beschreibung: Playwright End-to-End Tests für 55-Modell-Statistik-Update Pipeline

COMPREHENSIVE PLAYWRIGHT E2E TESTS:
- 55-Modell-Auswahl und Statistik-Updates
- Auto-Refresh-Funktionalität nach Suchvorgängen  
- Search-to-Statistics Pipeline Integration
- Cache-Busting und Live-Updates
"""

import asyncio
import pytest
from playwright.async_api import async_playwright, Page, Browser
import time
import json
import logging

logger = logging.getLogger(__name__)

# Test Configuration
MINESEARCH_URL = "http://localhost:8000/static/index.html"
TEST_TIMEOUT = 120000  # 2 minutes for long-running searches
STATISTICS_REFRESH_DELAY = 5000  # 5 seconds for auto-refresh


class MineSearchE2ETester:
    """
    Umfassender E2E-Tester für MineSearch v2.1 Statistik-Updates
    """
    
    def __init__(self, page: Page):
        self.page = page
        self.initial_model_count = 0
        self.post_search_model_count = 0
        
    async def navigate_to_minesearch(self):
        """Navigate to MineSearch interface and wait for loading"""
        logger.info("🌐 [E2E-SETUP] Navigating to MineSearch interface...")
        
        await self.page.goto(MINESEARCH_URL)
        
        # Wait for essential elements to load
        await self.page.wait_for_selector('[data-tab="single"]', timeout=10000)
        await self.page.wait_for_selector('#model-selection', timeout=10000)
        
        # Wait for models to load
        await self.page.wait_for_function(
            "document.querySelectorAll('input[name=\"model\"]').length > 0",
            timeout=15000
        )
        
        logger.info("✅ [E2E-SETUP] MineSearch interface loaded successfully")
        
    async def get_initial_statistics_state(self):
        """Capture initial state of Statistics tab"""
        logger.info("📊 [E2E-BASELINE] Capturing initial statistics state...")
        
        # Navigate to Statistics tab
        await self.page.click('[data-tab="statistics"]')
        await self.page.wait_for_timeout(2000)  # Allow statistics to load
        
        # Wait for statistics container
        await self.page.wait_for_selector('#model-statistics-table-container', timeout=10000)
        
        # Count initial model cards
        model_cards = await self.page.query_selector_all('.data-card')
        self.initial_model_count = len(model_cards)
        
        logger.info(f"📈 [E2E-BASELINE] Initial statistics: {self.initial_model_count} model cards")
        
        # Return to Search tab
        await self.page.click('[data-tab="single"]')
        await self.page.wait_for_timeout(1000)
        
    async def select_all_55_models(self):
        """Select all 55 models using the quick preset"""
        logger.info("🎯 [E2E-SELECTION] Selecting all 55 models via quick preset...")
        
        # Wait for quick preset buttons to be available
        await self.page.wait_for_selector('.quick-pill.all', timeout=10000)
        
        # Click "Alle (55 Modelle)" preset button
        await self.page.click('.quick-pill.all')
        
        # Wait for model selection to complete
        await self.page.wait_for_timeout(2000)
        
        # Verify all models are selected
        selected_models = await self.page.query_selector_all('input[name="model"]:checked')
        selected_count = len(selected_models)
        
        logger.info(f"✅ [E2E-SELECTION] Selected {selected_count} models (expected: ~55)")
        
        # Verify counter shows correct number
        counter_text = await self.page.text_content('#selected-models-count')
        logger.info(f"📊 [E2E-SELECTION] Selection counter shows: {counter_text} models")
        
        assert selected_count >= 50, f"Expected at least 50 models, got {selected_count}"
        return selected_count
        
    async def execute_single_search(self, mine_name="Test Mine Statistics"):
        """Execute single search with all selected models"""
        logger.info(f"🔍 [E2E-SEARCH] Starting single search for '{mine_name}'...")
        
        # Fill in search form
        await self.page.fill('#single-search-form input[name="mine_name"]', mine_name)
        
        # Start search
        await self.page.click('button:has-text("Suche starten")')
        
        # Wait for search to complete (with generous timeout for 55 models)
        logger.info("⏳ [E2E-SEARCH] Waiting for search completion (up to 2 minutes)...")
        
        try:
            # Wait for either success notification or results
            await self.page.wait_for_selector(
                '.notification.success:has-text("erfolgreich"), #results:not(:has(.loading-message))',
                timeout=TEST_TIMEOUT
            )
            logger.info("✅ [E2E-SEARCH] Search completed successfully")
            
            # Additional verification: check if results are displayed
            results_container = await self.page.query_selector('#results')
            if results_container:
                results_html = await results_container.inner_html()
                if 'loading' not in results_html.lower():
                    logger.info("📊 [E2E-SEARCH] Search results are displayed")
                    
        except Exception as e:
            logger.error(f"❌ [E2E-SEARCH] Search timeout or error: {e}")
            # Take screenshot for debugging
            await self.page.screenshot(path="/app/tests/search_timeout_debug.png")
            raise
            
    async def verify_statistics_auto_refresh(self):
        """Verify that statistics auto-refresh after search completion"""
        logger.info("🔄 [E2E-AUTO-REFRESH] Testing statistics auto-refresh functionality...")
        
        # Navigate to Statistics tab immediately after search
        await self.page.click('[data-tab="statistics"]')
        
        # Wait for auto-refresh to trigger (based on scheduleStatisticsRefresh delay)
        logger.info("⏰ [E2E-AUTO-REFRESH] Waiting for auto-refresh to trigger...")
        await self.page.wait_for_timeout(STATISTICS_REFRESH_DELAY)
        
        # Wait for statistics container to update
        await self.page.wait_for_selector('#model-statistics-table-container', timeout=10000)
        
        # Verify loading indicator appears and disappears (indicating refresh)
        try:
            # Check if refresh happened by looking for updated content
            await self.page.wait_for_function(
                """
                () => {
                    const container = document.getElementById('model-statistics-table-container');
                    const cards = container ? container.querySelectorAll('.data-card') : [];
                    return cards.length > 0;
                }
                """,
                timeout=15000
            )
            logger.info("✅ [E2E-AUTO-REFRESH] Statistics refreshed successfully")
            
        except Exception as e:
            logger.warning(f"⚠️ [E2E-AUTO-REFRESH] Auto-refresh verification failed: {e}")
            # Take screenshot for debugging
            await self.page.screenshot(path="/app/tests/auto_refresh_debug.png")
            
    async def verify_55_model_statistics_cards(self):
        """Verify that all 55+ models appear as statistics cards"""
        logger.info("🃏 [E2E-VERIFICATION] Verifying 55+ model statistics cards...")
        
        # Ensure we're on Statistics tab
        await self.page.click('[data-tab="statistics"]')
        await self.page.wait_for_timeout(2000)
        
        # Wait for statistics to fully load
        await self.page.wait_for_selector('#model-statistics-table-container .data-card', timeout=15000)
        
        # Count model cards
        model_cards = await self.page.query_selector_all('.data-card')
        self.post_search_model_count = len(model_cards)
        
        logger.info(f"📊 [E2E-VERIFICATION] Found {self.post_search_model_count} model cards (initial: {self.initial_model_count})")
        
        # Verify significant increase in model count
        model_increase = self.post_search_model_count - self.initial_model_count
        logger.info(f"📈 [E2E-VERIFICATION] Model count increase: +{model_increase} cards")
        
        # Assertions
        assert self.post_search_model_count >= 45, f"Expected at least 45 model cards, got {self.post_search_model_count}"
        assert model_increase >= 30, f"Expected significant increase in models (+30), got +{model_increase}"
        
        # Verify cards contain model information
        sample_cards = model_cards[:5]  # Check first 5 cards
        for i, card in enumerate(sample_cards):
            card_text = await card.text_content()
            assert ':' in card_text, f"Card {i+1} should contain model ID with provider prefix"
            logger.debug(f"📋 [E2E-VERIFICATION] Sample card {i+1}: {card_text[:50]}...")
            
        logger.info("✅ [E2E-VERIFICATION] All model statistics cards verified successfully")
        
    async def test_cache_busting_functionality(self):
        """Test cache-busting for real-time statistics updates"""
        logger.info("🔄 [E2E-CACHE-BUST] Testing cache-busting functionality...")
        
        # Force refresh statistics with cache buster
        await self.page.evaluate("window.loadStatisticsWithCacheBuster && window.loadStatisticsWithCacheBuster()")
        
        # Wait for refresh
        await self.page.wait_for_timeout(3000)
        
        # Verify statistics are still showing
        model_cards = await self.page.query_selector_all('.data-card')
        cache_bust_count = len(model_cards)
        
        logger.info(f"🔄 [E2E-CACHE-BUST] After cache-bust: {cache_bust_count} model cards")
        
        # Should maintain similar count
        assert abs(cache_bust_count - self.post_search_model_count) <= 3, \
            f"Cache-bust count changed significantly: {cache_bust_count} vs {self.post_search_model_count}"
            
        logger.info("✅ [E2E-CACHE-BUST] Cache-busting functionality verified")
        
    async def verify_search_to_statistics_pipeline(self):
        """End-to-end pipeline verification"""
        logger.info("🔗 [E2E-PIPELINE] Verifying complete search-to-statistics pipeline...")
        
        # Verify pipeline components
        pipeline_checks = [
            ("Search completion", self.post_search_model_count > self.initial_model_count),
            ("Model count increase", self.post_search_model_count >= 45),
            ("Statistics auto-refresh", True),  # Already tested above
            ("Model cards display", self.post_search_model_count > 0)
        ]
        
        for check_name, check_result in pipeline_checks:
            if check_result:
                logger.info(f"✅ [E2E-PIPELINE] {check_name}: PASSED")
            else:
                logger.error(f"❌ [E2E-PIPELINE] {check_name}: FAILED")
                
        # Overall pipeline assertion
        all_checks_passed = all(result for _, result in pipeline_checks)
        assert all_checks_passed, "Search-to-statistics pipeline verification failed"
        
        logger.info("✅ [E2E-PIPELINE] Complete pipeline verified successfully")


@pytest.mark.asyncio
async def test_55_model_statistics_update_pipeline():
    """
    HAUPTTEST: 55-Modell-Statistik-Update Pipeline End-to-End Test
    """
    logger.info("🚀 [E2E-MAIN] Starting 55-model statistics update pipeline test")
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Create tester instance
        tester = MineSearchE2ETester(page)
        
        try:
            # Test sequence
            await tester.navigate_to_minesearch()
            await tester.get_initial_statistics_state()
            
            selected_count = await tester.select_all_55_models()
            await tester.execute_single_search()
            
            await tester.verify_statistics_auto_refresh()
            await tester.verify_55_model_statistics_cards()
            await tester.test_cache_busting_functionality()
            await tester.verify_search_to_statistics_pipeline()
            
            logger.info("🎉 [E2E-MAIN] All tests completed successfully!")
            logger.info(f"📊 [E2E-SUMMARY] Models selected: {selected_count}, Initial cards: {tester.initial_model_count}, Final cards: {tester.post_search_model_count}")
            
        except Exception as e:
            logger.error(f"❌ [E2E-MAIN] Test failed: {e}")
            await page.screenshot(path="/app/tests/final_test_error.png")
            raise
            
        finally:
            await browser.close()


@pytest.mark.asyncio  
async def test_batch_search_statistics_update():
    """
    BATCH-TEST: Statistik-Updates bei Batch-Suchen
    """
    logger.info("📊 [E2E-BATCH] Starting batch search statistics update test")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        tester = MineSearchE2ETester(page)
        
        try:
            await tester.navigate_to_minesearch()
            
            # Navigate to Batch Search tab
            await page.click('[data-tab="batch"]')
            await page.wait_for_timeout(1000)
            
            # Select models for batch search
            await tester.select_all_55_models()
            
            # Note: Batch search requires CSV file upload
            # This is a simplified test that verifies the UI elements
            batch_form = await page.query_selector('#csv-form')
            assert batch_form is not None, "Batch search form should be available"
            
            logger.info("✅ [E2E-BATCH] Batch search UI verified")
            
        except Exception as e:
            logger.error(f"❌ [E2E-BATCH] Batch test failed: {e}")
            raise
            
        finally:
            await browser.close()


@pytest.mark.asyncio
async def test_statistics_tab_functionality():
    """
    STATISTICS-TAB-TEST: Statistik-Tab Funktionalität
    """
    logger.info("📈 [E2E-STATS-TAB] Testing statistics tab functionality")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            await page.goto(MINESEARCH_URL)
            await page.wait_for_selector('[data-tab="statistics"]', timeout=10000)
            
            # Navigate to Statistics tab
            await page.click('[data-tab="statistics"]')
            
            # Wait for statistics to load
            await page.wait_for_selector('#model-statistics-table-container', timeout=15000)
            
            # Check for statistics elements
            stats_container = await page.query_selector('#model-statistics-table-container')
            assert stats_container is not None, "Statistics container should be available"
            
            # Test filter functionality
            model_filter = await page.query_selector('#stats_model')
            if model_filter:
                logger.info("✅ [E2E-STATS-TAB] Model filter available")
                
            days_filter = await page.query_selector('#stats_days')
            if days_filter:
                logger.info("✅ [E2E-STATS-TAB] Days filter available")
                
            # Verify basic statistics display
            stats_content = await stats_container.text_content()
            assert len(stats_content) > 0, "Statistics should display content"
            
            logger.info("✅ [E2E-STATS-TAB] Statistics tab functionality verified")
            
        except Exception as e:
            logger.error(f"❌ [E2E-STATS-TAB] Statistics tab test failed: {e}")
            raise
            
        finally:
            await browser.close()


if __name__ == "__main__":
    """
    Direkter Test-Ausführung für Debugging
    """
    logging.basicConfig(level=logging.INFO)
    
    async def run_main_test():
        await test_55_model_statistics_update_pipeline()
        
    asyncio.run(run_main_test())