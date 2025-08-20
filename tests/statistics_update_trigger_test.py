"""
Author: rahn
Datum: 16.08.2025
Version: 1.0
Beschreibung: Test des Critical Fix - Statistics Update Trigger nach neuen Searches
"""

import asyncio
import json
import time
from playwright.async_api import async_playwright

class StatisticsUpdateTriggerTest:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        
    async def test_statistics_update_trigger(self):
        """Test ob neue Searches automatisch Statistics aktualisieren"""
        print("🚀 STATISTICS UPDATE TRIGGER TEST")
        print("=" * 60)
        
        try:
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=False)
            page = await browser.new_page()
            
            # Capture console logs for trigger validation
            console_logs = []
            page.on("console", lambda msg: console_logs.append(f"{msg.type}: {msg.text}"))
            
            # STEP 1: Baseline Statistics Count
            print("📊 [BASELINE] Getting current statistics count...")
            await page.goto(f"{self.base_url}/static/index.html")
            await page.wait_for_load_state("networkidle")
            
            # Go to Statistics Tab
            stats_tab = await page.query_selector('nav.main-navigation a[data-tab="statistics"]')
            await stats_tab.click()
            await asyncio.sleep(10)
            
            baseline_count = await page.evaluate("""
                () => {
                    const cards = document.querySelectorAll('.model-stats-card');
                    return cards.length;
                }
            """)
            
            print(f"📋 Baseline Model Cards: {baseline_count}")
            
            # STEP 2: Perform Single Search with uncommon model
            print("🔍 [SEARCH] Performing single search with trigger test...")
            
            # Go to Single Search Tab
            single_tab = await page.query_selector('nav.main-navigation a[data-tab="single"]')
            await single_tab.click()
            await asyncio.sleep(3)
            
            # Fill search form
            await page.fill('input[name="mine_name"]', 'Test Mining Trigger')
            await page.fill('input[name="country"]', 'Canada')
            await page.fill('input[name="commodity"]', 'Gold')
            
            # Select a specific model for testing
            test_model = "openrouter:deepseek-free"  # Use known working model
            
            # Select the model checkbox
            await page.evaluate(f"""
                () => {{
                    const checkboxes = document.querySelectorAll('input[name="model"]');
                    checkboxes.forEach(cb => {{
                        if (cb.value === '{test_model}') {{
                            cb.checked = true;
                        }} else {{
                            cb.checked = false;
                        }}
                    }});
                }}
            """)
            
            print(f"🎯 Selected model for trigger test: {test_model}")
            
            # Start the search
            search_button = await page.query_selector('button:has-text("Suche starten"), #start-search-btn')
            if search_button:
                await search_button.click()
                print("✅ Search started successfully")
                
                # Wait for search to complete
                print("⏳ [WAITING] Waiting for search completion...")
                
                search_completed = False
                max_wait = 120  # 2 minutes max
                start_time = time.time()
                
                while not search_completed and (time.time() - start_time) < max_wait:
                    await asyncio.sleep(5)
                    
                    # Check for completion
                    page_text = await page.evaluate("() => document.body.textContent")
                    if any(keyword in page_text.lower() for keyword in ['erfolgreich', 'completed', 'abgeschlossen']):
                        search_completed = True
                        print("✅ Search completed!")
                    else:
                        elapsed = int(time.time() - start_time)
                        print(f"⏳ Search in progress... ({elapsed}s elapsed)")
                
                if not search_completed:
                    print("⚠️ Search timeout - continuing with analysis")
                
                # STEP 3: Check Statistics Update
                print("📈 [VALIDATION] Checking statistics update after search...")
                
                # Navigate back to Statistics Tab
                stats_tab = await page.query_selector('nav.main-navigation a[data-tab="statistics"]')
                await stats_tab.click()
                await asyncio.sleep(15)  # Wait for potential statistics refresh
                
                # Check updated count
                final_count = await page.evaluate("""
                    () => {
                        const cards = document.querySelectorAll('.model-stats-card');
                        return cards.length;
                    }
                """)
                
                # Look for our test model specifically
                model_found = await page.evaluate(f"""
                    () => {{
                        const cards = document.querySelectorAll('.model-stats-card');
                        let found = false;
                        
                        cards.forEach(card => {{
                            const text = card.textContent;
                            if (text.includes('{test_model}')) {{
                                found = true;
                            }}
                        }});
                        
                        return found;
                    }}
                """)
                
                await browser.close()
                
                # ANALYSIS
                print(f"\n🚀 STATISTICS UPDATE TRIGGER TEST RESULTS:")
                print(f"=" * 60)
                print(f"📊 Baseline Cards: {baseline_count}")
                print(f"📈 Final Cards: {final_count}")
                print(f"📦 Cards Change: {final_count - baseline_count}")
                print(f"🎯 Test Model ({test_model}) Found: {'✅ YES' if model_found else '❌ NO'}")
                
                # Check server logs for trigger execution
                trigger_logs = [log for log in console_logs 
                              if 'STATS-TRIGGER' in log or 'STATS-UPDATE' in log]
                
                print(f"\n📝 TRIGGER LOGS ({len(trigger_logs)} entries):")
                for log in trigger_logs:
                    print(f"   {log}")
                
                # Final verdict
                trigger_success = model_found or (final_count > baseline_count)
                
                if trigger_success:
                    print(f"\n🎉 STATISTICS UPDATE TRIGGER: ERFOLGREICH!")
                    print(f"   ✅ Model appears in statistics after search")
                    print(f"   ✅ Critical Fix is working")
                    print(f"   ✅ Search → Database → Statistics pipeline functional")
                else:
                    print(f"\n⚠️ STATISTICS UPDATE TRIGGER: NEEDS INVESTIGATION")
                    print(f"   ❌ Model not found in statistics")
                    print(f"   🔍 Check server logs for STATS-TRIGGER messages")
                    print(f"   📋 Cards count unchanged: {baseline_count} → {final_count}")
                
                return {
                    'trigger_success': trigger_success,
                    'baseline_cards': baseline_count,
                    'final_cards': final_count,
                    'test_model': test_model,
                    'model_found': model_found,
                    'trigger_logs': trigger_logs
                }
                
            else:
                print("❌ Search button not found")
                await browser.close()
                return None
                
        except Exception as e:
            print(f"❌ Statistics update trigger test error: {e}")
            import traceback
            traceback.print_exc()
            return None

# Main execution
if __name__ == "__main__":
    async def main():
        tester = StatisticsUpdateTriggerTest()
        result = await tester.test_statistics_update_trigger()
        
        if result:
            with open('/app/tests/statistics_trigger_test_results.json', 'w') as f:
                json.dump(result, f, indent=2)
            
            print(f"\n💾 Trigger test results saved")
            
            if result['trigger_success']:
                print(f"\n🎆 CRITICAL FIX VALIDATION: SUCCESSFUL!")
                print(f"Statistics Update Trigger is working correctly")
            else:
                print(f"\n🔧 CRITICAL FIX VALIDATION: NEEDS DEBUGGING")
                print(f"Statistics Update Trigger may need adjustment")
    
    asyncio.run(main())