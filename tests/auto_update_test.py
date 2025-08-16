"""
Author: rahn
Datum: 16.08.2025
Version: 1.0
Beschreibung: Test für Auto-Update Quick-Presets mit Top-Performern
"""

import asyncio
import json
from playwright.async_api import async_playwright

class AutoUpdateTest:
    def __init__(self):
        self.base_url = "http://localhost:8000"
    
    async def test_auto_update_initialization(self):
        """Test die Initialisierung des Auto-Update-Systems"""
        print("🧪 AUTO-UPDATE INITIALIZATION TEST")
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
            await asyncio.sleep(8)  # Wait for auto-update to initialize
            
            await browser.close()
            
            # Look for auto-update initialization logs
            auto_update_logs = [log for log in console_logs 
                              if any(keyword in log for keyword in ['AUTO-UPDATE', 'Quick presets', 'auto-update'])]
            
            print(f"📝 Auto-update logs ({len(auto_update_logs)}):")
            for log in auto_update_logs[:6]:
                print(f"   {log}")
            
            # Check if auto-update started
            started = any('auto-update system started' in log or 'AUTO-UPDATE' in log for log in auto_update_logs)
            print(f"\\n✅ Auto-update system started: {started}")
            
            return started
            
        except Exception as e:
            print(f"❌ Auto-update initialization test error: {e}")
            return False
    
    async def test_label_update_functionality(self):
        """Test die Label-Update-Funktionalität"""
        print("\\n🧪 LABEL UPDATE FUNCTIONALITY TEST")
        print("=" * 50)
        
        try:
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=False)
            page = await browser.new_page()
            
            await page.goto(f"{self.base_url}/static/index.html")
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(5)
            
            # Get initial button text
            initial_button = await page.query_selector('.quick-pill.recommended')
            initial_text = await initial_button.text_content() if initial_button else "Not found"
            print(f"📊 Initial button text: {initial_text}")
            
            # Manually trigger label update
            update_result = await page.evaluate("""
                async () => {
                    console.log('🔄 Manual label update test...');
                    
                    if (typeof updateQuickPresetLabels === 'undefined') {
                        return { error: 'updateQuickPresetLabels function not available' };
                    }
                    
                    try {
                        await updateQuickPresetLabels();
                        
                        // Get updated button text
                        const button = document.querySelector('.quick-pill.recommended');
                        const newText = button ? button.textContent : 'Not found';
                        const tooltip = button ? button.getAttribute('title') : 'No tooltip';
                        
                        return {
                            success: true,
                            newText: newText,
                            tooltip: tooltip,
                            hasTopPerformers: newText.includes('Top Performers')
                        };
                    } catch (error) {
                        return { error: error.message };
                    }
                }
            """)
            
            await browser.close()
            
            print("📊 Label update results:")
            if update_result.get('error'):
                print(f"   ❌ Error: {update_result['error']}")
                return False
            else:
                print(f"   ✅ Success: {update_result['success']}")
                print(f"   📋 New text: {update_result['newText']}")
                print(f"   💬 Tooltip: {update_result['tooltip']}")
                print(f"   🏆 Has top performers: {update_result['hasTopPerformers']}")
                
                return update_result['success'] and update_result['hasTopPerformers']
            
        except Exception as e:
            print(f"❌ Label update test error: {e}")
            return False
    
    async def test_manual_refresh_function(self):
        """Test die manuelle Refresh-Funktion"""
        print("\\n🧪 MANUAL REFRESH FUNCTION TEST")
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
            
            # Test manual refresh function
            refresh_result = await page.evaluate("""
                async () => {
                    console.log('🔄 Testing manual refresh function...');
                    
                    if (typeof refreshQuickPresets === 'undefined') {
                        return { error: 'refreshQuickPresets function not available' };
                    }
                    
                    try {
                        await refreshQuickPresets();
                        return { success: true };
                    } catch (error) {
                        return { error: error.message };
                    }
                }
            """)
            
            await browser.close()
            
            # Look for refresh logs
            refresh_logs = [log for log in console_logs 
                          if any(keyword in log for keyword in ['MANUAL-REFRESH', 'refresh', 'AUTO-UPDATE'])]
            
            print(f"📝 Refresh logs ({len(refresh_logs)}):")
            for log in refresh_logs[-4:]:  # Last 4 logs
                print(f"   {log}")
            
            print("📊 Manual refresh results:")
            if refresh_result.get('error'):
                print(f"   ❌ Error: {refresh_result['error']}")
                return False
            else:
                print(f"   ✅ Success: {refresh_result['success']}")
                has_refresh_logs = any('MANUAL-REFRESH' in log for log in refresh_logs)
                print(f"   📝 Has refresh logs: {has_refresh_logs}")
                
                return refresh_result['success'] and has_refresh_logs
            
        except Exception as e:
            print(f"❌ Manual refresh test error: {e}")
            return False
    
    async def test_provider_count_updates(self):
        """Test die Aktualisierung der Provider-Counts"""
        print("\\n🧪 PROVIDER COUNT UPDATE TEST")
        print("=" * 50)
        
        try:
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=False)
            page = await browser.new_page()
            
            await page.goto(f"{self.base_url}/static/index.html")
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(5)
            
            # Get button texts
            buttons_info = await page.evaluate("""
                () => {
                    const buttons = {
                        webSearch: document.querySelector('.quick-pill.web-focus'),
                        premium: document.querySelector('.quick-pill.premium'),
                        all: document.querySelector('.quick-pill.all')
                    };
                    
                    const result = {};
                    Object.entries(buttons).forEach(([key, button]) => {
                        if (button) {
                            result[key] = {
                                text: button.textContent,
                                hasCount: /\\(\\d+\\s+Modelle?\\)/.test(button.textContent)
                            };
                        }
                    });
                    
                    return result;
                }
            """)
            
            await browser.close()
            
            print("📊 Provider count results:")
            total_with_counts = 0
            for category, info in buttons_info.items():
                if info:
                    has_count = info['hasCount']
                    print(f"   {category}: {info['text']} - Count: {'✅' if has_count else '❌'}")
                    if has_count:
                        total_with_counts += 1
            
            success = total_with_counts >= 2  # At least 2 buttons should have counts
            print(f"\\n✅ Provider count update: {'PASSED' if success else 'FAILED'} ({total_with_counts}/3 buttons)")
            
            return success
            
        except Exception as e:
            print(f"❌ Provider count test error: {e}")
            return False
    
    async def run_auto_update_tests(self):
        """Run all auto-update tests"""
        print("🚀 COMPREHENSIVE AUTO-UPDATE TESTS")
        print("=" * 60)
        
        results = {}
        
        # Test 1: Auto-Update Initialization
        results['initialization'] = await self.test_auto_update_initialization()
        
        # Test 2: Label Update Functionality
        results['label_update'] = await self.test_label_update_functionality()
        
        # Test 3: Manual Refresh Function
        results['manual_refresh'] = await self.test_manual_refresh_function()
        
        # Test 4: Provider Count Updates
        results['count_updates'] = await self.test_provider_count_updates()
        
        # Final Summary
        passed = sum(1 for result in results.values() if result is True)
        total = len(results)
        
        print(f"\\n📊 AUTO-UPDATE TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Initialization: {'PASSED' if results.get('initialization') else 'FAILED'}")
        print(f"✅ Label Update: {'PASSED' if results.get('label_update') else 'FAILED'}")
        print(f"✅ Manual Refresh: {'PASSED' if results.get('manual_refresh') else 'FAILED'}")
        print(f"✅ Count Updates: {'PASSED' if results.get('count_updates') else 'FAILED'}")
        print(f"\\n🎯 TOTAL: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 AUTO-UPDATE SYSTEM FULLY OPERATIONAL!")
            print("✅ PHASE 2.2 erfolgreich abgeschlossen!")
        elif passed >= 3:
            print("🟡 AUTO-UPDATE SYSTEM MOSTLY WORKING!")
            print("✅ PHASE 2.2 weitgehend erfolgreich!")
        else:
            print("⚠️ Auto-update system needs improvements")
        
        return results

# Main execution
if __name__ == "__main__":
    async def main():
        tester = AutoUpdateTest()
        results = await tester.run_auto_update_tests()
        
        # Save results
        with open('/app/tests/auto_update_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\\n💾 Results saved: /app/tests/auto_update_results.json")
    
    asyncio.run(main())