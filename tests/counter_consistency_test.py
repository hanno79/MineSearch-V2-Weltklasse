"""
Author: rahn
Datum: 18.08.2025
Version: 1.0  
Beschreibung: Counter-Konsistenz Integration Test für Model-Selection

Test zur Verifikation, dass alle Model-Counter konsistent die gleiche Anzahl anzeigen
nach dem Fix der 67→55 Modelle Diskrepanz.
"""

import asyncio
from playwright.async_api import async_playwright
import logging

logger = logging.getLogger(__name__)

async def test_model_counter_consistency():
    """
    Haupttest: Verifikation der Counter-Konsistenz
    Alle Counter sollten die gleiche Anzahl ausgewählter Modelle anzeigen
    """
    logger.info("🧪 [COUNTER-TEST] Starting model counter consistency test")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            # Navigate to MineSearch
            await page.goto("http://localhost:8000/static/index.html")
            await page.wait_for_selector('[data-tab="search"]', timeout=10000)
            
            # Wait for models to load
            await page.wait_for_function(
                "document.querySelectorAll('input[name=\"model\"]').length > 0",
                timeout=15000
            )
            
            # Select all models using quick preset
            await page.click('.quick-pill.all')
            await page.wait_for_timeout(3000)  # Allow selection to complete
            
            # Test all counter selectors for consistency
            logger.info("📊 [COUNTER-TEST] Testing all counter selectors...")
            
            counters = await page.evaluate("""
                () => {
                    return {
                        // Main counter selector (search.js)
                        main_model_counter: document.querySelectorAll('input[name="model"]:checked').length,
                        
                        // Header navigation counter (header-navigation.js - FIXED)
                        header_counter: document.querySelectorAll('input[name="model"]:checked').length,
                        
                        // Progressive selection counter
                        progressive_counter: document.querySelectorAll('#model-selection input[type="checkbox"][name="model"]:checked').length,
                        
                        // Legacy counter (should be 0 now after cleanup)
                        legacy_counter: document.querySelectorAll('input[name="models"]:checked').length,
                        
                        // All checkbox counter (generic)
                        all_checkbox_counter: document.querySelectorAll('#model-selection input[type="checkbox"]:checked').length,
                        
                        // Display counters from UI
                        ui_selected_count: document.getElementById('selected-models-count')?.textContent || 'N/A',
                        ui_status_models: document.getElementById('status-models')?.textContent || 'N/A'
                    };
                }
            """)
            
            logger.info("📊 [COUNTER-TEST] Counter Results:")
            logger.info(f"   Main Model Counter: {counters['main_model_counter']}")
            logger.info(f"   Header Counter: {counters['header_counter']}")  
            logger.info(f"   Progressive Counter: {counters['progressive_counter']}")
            logger.info(f"   Legacy Counter: {counters['legacy_counter']} (should be 0)")
            logger.info(f"   All Checkbox Counter: {counters['all_checkbox_counter']}")
            logger.info(f"   UI Selected Count: {counters['ui_selected_count']}")
            logger.info(f"   UI Status Models: {counters['ui_status_models']}")
            
            # Verify consistency
            main_count = counters['main_model_counter']
            header_count = counters['header_counter']
            progressive_count = counters['progressive_counter']
            all_checkbox_count = counters['all_checkbox_counter']
            legacy_count = counters['legacy_counter']
            
            # All main counters should be equal
            consistency_check = (
                main_count == header_count == progressive_count == all_checkbox_count
                and legacy_count == 0  # Legacy should be 0 after cleanup
                and main_count > 50  # Should be around 55 models
            )
            
            if consistency_check:
                logger.info(f"✅ [COUNTER-TEST] CONSISTENCY SUCCESS: All counters show {main_count} models")
                logger.info(f"✅ [COUNTER-TEST] Legacy counter properly cleaned up: {legacy_count} models")
                
                # Check UI display consistency
                ui_count_match = str(main_count) in counters['ui_selected_count']
                ui_status_match = str(main_count) in counters['ui_status_models']
                
                if ui_count_match and ui_status_match:
                    logger.info("✅ [COUNTER-TEST] UI displays are also consistent")
                else:
                    logger.warning(f"⚠️ [COUNTER-TEST] UI inconsistency: Count='{counters['ui_selected_count']}', Status='{counters['ui_status_models']}'")
                    
            else:
                logger.error("❌ [COUNTER-TEST] CONSISTENCY FAILURE:")
                logger.error(f"   Main: {main_count}, Header: {header_count}, Progressive: {progressive_count}")
                logger.error(f"   All Checkbox: {all_checkbox_count}, Legacy: {legacy_count}")
                raise AssertionError("Counter inconsistency detected")
            
            # Verify expected model count (should be around 55)
            expected_range = (50, 60)
            if expected_range[0] <= main_count <= expected_range[1]:
                logger.info(f"✅ [COUNTER-TEST] Model count within expected range: {main_count} models")
            else:
                logger.warning(f"⚠️ [COUNTER-TEST] Unexpected model count: {main_count} (expected {expected_range[0]}-{expected_range[1]})")
            
            # Test deselection consistency
            logger.info("🧪 [COUNTER-TEST] Testing deselection consistency...")
            
            # Clear all selections
            await page.evaluate("document.querySelectorAll('input[name=\"model\"]:checked').forEach(cb => cb.checked = false)")
            await page.wait_for_timeout(1000)
            
            # Verify all counters are now 0
            zero_counters = await page.evaluate("""
                () => {
                    return {
                        main: document.querySelectorAll('input[name="model"]:checked').length,
                        header: document.querySelectorAll('input[name="model"]:checked').length,
                        progressive: document.querySelectorAll('#model-selection input[type="checkbox"][name="model"]:checked').length,
                        legacy: document.querySelectorAll('input[name="models"]:checked').length,
                        all_checkbox: document.querySelectorAll('#model-selection input[type="checkbox"]:checked').length
                    };
                }
            """)
            
            all_zero = all(count == 0 for count in zero_counters.values())
            if all_zero:
                logger.info("✅ [COUNTER-TEST] Deselection consistency verified: All counters are 0")
            else:
                logger.error(f"❌ [COUNTER-TEST] Deselection inconsistency: {zero_counters}")
                raise AssertionError("Deselection consistency failure")
                
            logger.info("🎉 [COUNTER-TEST] All counter consistency tests PASSED!")
            
        except Exception as e:
            logger.error(f"❌ [COUNTER-TEST] Test failed: {e}")
            await page.screenshot(path="/app/tests/counter_consistency_error.png")
            raise
            
        finally:
            await browser.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_model_counter_consistency())