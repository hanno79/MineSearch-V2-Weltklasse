"""
Author: rahn
Datum: 16.08.2025
Version: 1.0
Beschreibung: Test für dynamische 'Beste Auswahl' basierend auf Performance-Statistiken
"""

import asyncio
import json
from playwright.async_api import async_playwright

class DynamicSelectionTest:
    def __init__(self):
        self.base_url = "http://localhost:8000"
    
    async def test_get_best_performing_models_function(self):
        """Test die neue getBestPerformingModels Funktion"""
        print("🧪 GET BEST PERFORMING MODELS TEST")
        print("=" * 50)
        
        try:
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=False)
            page = await browser.new_page()
            
            # Capture console logs
            console_logs = []
            page.on("console", lambda msg: console_logs.append(f"{msg.type}: {msg.text}"))
            
            await page.goto(f"{self.base_url}/static/index.html")
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(2)
            
            # Test getBestPerformingModels function directly
            test_result = await page.evaluate("""
                async () => {
                    console.log('🏆 Testing getBestPerformingModels function...');
                    
                    try {
                        // Check if function is available
                        if (typeof getBestPerformingModels === 'undefined') {
                            return { error: 'getBestPerformingModels function not available' };
                        }
                        
                        // Call the function
                        const bestModels = await getBestPerformingModels();
                        
                        return {
                            success: true,
                            modelCount: bestModels.length,
                            models: bestModels,
                            hasValidModels: bestModels.length > 0 && bestModels.every(m => m.includes(':'))
                        };
                    } catch (error) {
                        return { error: error.message };
                    }
                }
            """)
            
            await browser.close()
            
            print("📊 getBestPerformingModels Results:")
            if test_result.get('error'):
                print(f"   ❌ Error: {test_result['error']}")
                return False
            else:
                print(f"   ✅ Success: {test_result['success']}")
                print(f"   📊 Model count: {test_result['modelCount']}")
                print(f"   🎯 Valid models: {test_result['hasValidModels']}")
                if test_result['models']:
                    print("   📋 Selected models:")
                    for i, model in enumerate(test_result['models'], 1):
                        print(f"      {i}. {model}")
                
                return test_result['success'] and test_result['hasValidModels']
            
        except Exception as e:
            print(f"❌ getBestPerformingModels test error: {e}")
            return False
    
    async def test_dynamic_quick_preset_selection(self):
        """Test die dynamische Quick-Preset Auswahl"""
        print("\\n🧪 DYNAMIC QUICK PRESET SELECTION TEST")
        print("=" * 50)
        
        try:
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=False)
            page = await browser.new_page()
            
            # Capture console logs
            console_logs = []
            page.on("console", lambda msg: console_logs.append(f"{msg.type}: {msg.text}"))
            
            await page.goto(f"{self.base_url}/static/index.html")
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(3)
            
            print("🎯 Clicking 'Dynamische Beste Auswahl' button...")
            
            # Click the dynamic selection button
            button = await page.query_selector('.quick-pill.recommended')
            if button:
                await button.click()
                await asyncio.sleep(5)  # Wait for async selection to complete
                
                # Check selected models
                selected_checkboxes = await page.query_selector_all('input[name="model"]:checked')
                selected_models = []
                for checkbox in selected_checkboxes:
                    value = await checkbox.get_attribute('value')
                    if value:
                        selected_models.append(value)
                
                print(f"📊 Selected models: {len(selected_models)}")
                for i, model in enumerate(selected_models, 1):
                    print(f"   {i}. {model}")
                
                # Check if button is active
                button_classes = await button.get_attribute('class')
                is_active = 'active' in button_classes
                
                print(f"🎯 Button active: {is_active}")
                
                # Look for dynamic selection logs
                dynamic_logs = [log for log in console_logs 
                              if any(keyword in log for keyword in ['DYNAMIC-SELECTION', 'Dynamic', 'getBestPerforming'])]
                
                print(f"\\n📝 Dynamic selection logs ({len(dynamic_logs)}):")
                for log in dynamic_logs[:8]:
                    print(f"   {log}")
                
                success = len(selected_models) > 0 and is_active
                return success
            else:
                print("❌ Quick preset button not found")
                return False
            
        except Exception as e:
            print(f"❌ Dynamic preset test error: {e}")
            return False
    
    async def test_fallback_mechanism(self):
        """Test das Fallback-System bei API-Fehlern"""
        print("\\n🧪 FALLBACK MECHANISM TEST")
        print("=" * 50)
        
        try:
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=False)
            page = await browser.new_page()
            
            # Simulate API failure by blocking the API call
            await page.route("**/api/results*", lambda route: route.abort())
            
            await page.goto(f"{self.base_url}/static/index.html")
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(2)
            
            # Capture console logs
            console_logs = []
            page.on("console", lambda msg: console_logs.append(f"{msg.type}: {msg.text}"))
            
            print("🚫 API blocked - testing fallback selection...")
            
            # Test fallback by calling getBestPerformingModels
            fallback_result = await page.evaluate("""
                async () => {
                    try {
                        const models = await getBestPerformingModels();
                        return { fallbackWorked: models.length === 0 }; // Should return empty array
                    } catch (error) {
                        return { error: error.message };
                    }
                }
            """)
            
            await browser.close()
            
            print("📊 Fallback test results:")
            if fallback_result.get('error'):
                print(f"   ❌ Error: {fallback_result['error']}")
                return False
            else:
                print(f"   ✅ Fallback worked: {fallback_result['fallbackWorked']}")
                return fallback_result['fallbackWorked']
            
        except Exception as e:
            print(f"❌ Fallback test error: {e}")
            return False
    
    async def run_dynamic_selection_tests(self):
        """Run all dynamic selection tests"""
        print("🚀 COMPREHENSIVE DYNAMIC SELECTION TESTS")
        print("=" * 60)
        
        results = {}
        
        # Test 1: getBestPerformingModels Function
        results['function_test'] = await self.test_get_best_performing_models_function()
        
        # Test 2: Dynamic Quick Preset Selection
        results['preset_selection'] = await self.test_dynamic_quick_preset_selection()
        
        # Test 3: Fallback Mechanism
        results['fallback_mechanism'] = await self.test_fallback_mechanism()
        
        # Final Summary
        passed = sum(1 for result in results.values() if result is True)
        total = len(results)
        
        print(f"\\n📊 DYNAMIC SELECTION TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Function Test: {'PASSED' if results.get('function_test') else 'FAILED'}")
        print(f"✅ Preset Selection: {'PASSED' if results.get('preset_selection') else 'FAILED'}")
        print(f"✅ Fallback Mechanism: {'PASSED' if results.get('fallback_mechanism') else 'FAILED'}")
        print(f"\\n🎯 TOTAL: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 DYNAMIC SELECTION FULLY OPERATIONAL!")
            print("✅ PHASE 2.1 erfolgreich abgeschlossen!")
        elif passed >= 2:
            print("🟡 DYNAMIC SELECTION MOSTLY WORKING!")
            print("✅ PHASE 2.1 weitgehend erfolgreich!")
        else:
            print("⚠️ Dynamic selection needs improvements")
        
        return results

# Main execution
if __name__ == "__main__":
    async def main():
        tester = DynamicSelectionTest()
        results = await tester.run_dynamic_selection_tests()
        
        # Save results
        with open('/app/tests/dynamic_selection_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\\n💾 Results saved: /app/tests/dynamic_selection_results.json")
    
    asyncio.run(main())