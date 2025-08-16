"""
Author: rahn
Datum: 16.08.2025
Version: 1.0
Beschreibung: Schneller Test für Performance-Score Funktionalität ohne Browser-Abhängigkeit
"""

import asyncio
import json
import time
from playwright.async_api import async_playwright

class QuickPerformanceScoreTest:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.results = []
    
    async def test_statistics_api_direct(self):
        """Test Statistics API direkt"""
        print("🧪 DIRECT API TEST: Statistics Endpoint")
        print("=" * 50)
        
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            try:
                # Test results endpoint
                async with session.get(f"{self.base_url}/api/results?exclude_exa=true&days_back=30&sort_by=mine_name") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Results API: {response.status} - {len(data.get('data', {}).get('results', []))} results")
                        
                        # Check model_used patterns
                        if data.get('success') and data.get('data', {}).get('results'):
                            models_found = set()
                            for result in data['data']['results'][:5]:  # First 5 only
                                model_used = result.get('model_used', 'unknown')
                                models_found.add(model_used)
                            
                            print(f"📊 Model patterns found: {len(models_found)}")
                            for model in sorted(models_found):
                                print(f"   - {model}")
                            
                            return True
                    else:
                        print(f"❌ Results API failed: {response.status}")
                        return False
                        
            except Exception as e:
                print(f"❌ API Error: {e}")
                return False
    
    async def test_browser_stats_tab(self):
        """Minimaler Browser-Test für Statistics Tab"""
        print("\n🧪 BROWSER TEST: Statistics Tab Score Display")
        print("=" * 50)
        
        try:
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=True, slow_mo=500)
            page = await browser.new_page()
            
            # Capture console logs for debugging
            console_logs = []
            page.on("console", lambda msg: console_logs.append(f"{msg.type}: {msg.text}"))
            
            # Navigate to page
            await page.goto(f"{self.base_url}/static/index.html")
            await page.wait_for_load_state("networkidle")
            
            # Wait a bit for initial load
            await asyncio.sleep(2)
            
            # Click Statistics tab
            print("📊 Switching to Statistics tab...")
            await page.click('header nav a[href="#statistics"]')
            await asyncio.sleep(5)  # More time for score calculations
            
            # Check for model cards
            cards = await page.query_selector_all(".model-stats-card")
            print(f"📋 Model cards found: {len(cards)}")
            
            # Check for score breakdown sections  
            breakdowns = await page.query_selector_all(".score-breakdown-section")
            print(f"📊 Score breakdowns found: {len(breakdowns)}")
            
            # Look for relevant console logs
            score_logs = [log for log in console_logs if 'SCORE' in log.upper()]
            split_logs = [log for log in console_logs if 'SPLIT' in log.upper()]
            
            print(f"\n📊 Score calculation logs: {len(score_logs)}")
            for log in score_logs[:3]:
                print(f"   {log}")
            
            print(f"\n🔧 Model splitting logs: {len(split_logs)}")
            for log in split_logs[:3]:
                print(f"   {log}")
            
            await browser.close()
            
            # Evaluate success
            success = len(cards) > 0 and len(breakdowns) > 0 and len(score_logs) > 0
            return success
            
        except Exception as e:
            print(f"❌ Browser test error: {e}")
            return False
    
    async def test_score_consistency_check(self):
        """Check for score consistency issues"""
        print("\n🧪 CONSISTENCY TEST: Score vs Success Rate Logic")
        print("=" * 50)
        
        try:
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=True)
            page = await browser.new_page()
            
            await page.goto(f"{self.base_url}/static/index.html")
            await page.wait_for_load_state("networkidle")
            
            # Go to Statistics
            await page.click('header nav a[href="#statistics"]')
            await asyncio.sleep(4)
            
            # Check model cards for inconsistencies
            inconsistencies = 0
            cards = await page.query_selector_all(".model-stats-card")
            
            for i, card in enumerate(cards[:3]):  # Check first 3 cards
                try:
                    # Get score and success rate
                    score_element = await card.query_selector(".performance-score")
                    success_element = await card.query_selector(".data-row:has-text('Erfolgsrate') .data-value")
                    
                    if score_element and success_element:
                        score_text = await score_element.text_content()
                        success_text = await success_element.text_content()
                        
                        print(f"   Card {i+1}: Score={score_text.strip()}, Success={success_text.strip()}")
                        
                        # Check for impossible combinations
                        if "10.0/10" in score_text and "0.0%" in success_text:
                            inconsistencies += 1
                            print(f"      ⚠️ INCONSISTENCY: Perfect score with 0% success!")
                        
                except Exception as e:
                    print(f"   Card {i+1}: Analysis error - {e}")
            
            await browser.close()
            
            print(f"\n📊 Inconsistencies found: {inconsistencies}")
            return inconsistencies == 0
            
        except Exception as e:
            print(f"❌ Consistency test error: {e}")
            return False
    
    async def run_quick_test_suite(self):
        """Run quick comprehensive test"""
        print("🚀 QUICK PERFORMANCE-SCORE TEST SUITE")
        print("=" * 60)
        start_time = time.time()
        
        results = {}
        
        # Test 1: Direct API
        results['api_test'] = await self.test_statistics_api_direct()
        
        # Test 2: Browser Stats Tab
        results['browser_test'] = await self.test_browser_stats_tab()
        
        # Test 3: Consistency Check
        results['consistency_test'] = await self.test_score_consistency_check()
        
        # Final Report
        elapsed = time.time() - start_time
        print(f"\n📊 QUICK TEST REPORT (completed in {elapsed:.1f}s)")
        print("=" * 60)
        
        passed = sum(1 for result in results.values() if result is True)
        total = len(results)
        
        print(f"✅ API Test: {'PASSED' if results.get('api_test') else 'FAILED'}")
        print(f"✅ Browser Test: {'PASSED' if results.get('browser_test') else 'FAILED'}")
        print(f"✅ Consistency Test: {'PASSED' if results.get('consistency_test') else 'FAILED'}")
        
        print(f"\n🎯 RESULT: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 PERFORMANCE-SCORE SYSTEM WORKING!")
        else:
            print("⚠️ Some issues detected - needs investigation")
        
        # Save results
        with open('/app/tests/quick_score_results.json', 'w') as f:
            json.dump({
                'results': results,
                'elapsed_time': elapsed,
                'timestamp': time.time()
            }, f, indent=2)
        
        return results

# Main execution
if __name__ == "__main__":
    async def main():
        tester = QuickPerformanceScoreTest()
        results = await tester.run_quick_test_suite()
        
        print(f"\n💾 Results saved: /app/tests/quick_score_results.json")
    
    asyncio.run(main())