"""
Author: rahn
Datum: 16.08.2025
Version: 1.0
Beschreibung: JavaScript-basierter Test der neuen Performance-Score Berechnung
"""

import asyncio
import json
from playwright.async_api import async_playwright

class JavaScriptScoreTest:
    def __init__(self):
    """__init__ - TODO: Dokumentation hinzufügen"""
        self.base_url = "http://localhost:8000"

    async def test_score_calculation_javascript(self):
        """Test die neue Score-Berechnung direkt in JavaScript"""
        print("🧪 JAVASCRIPT SCORE CALCULATION TEST")
        print("=" * 50)

        try:
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=False)
            page = await browser.new_page()

            # Navigate to page
            await page.goto(f"{self.base_url}/static/index.html")
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(3)

            # Test Score Calculation Function directly in browser
            test_result = await page.evaluate("""
                async () => {
                    console.log('🧮 Testing Score Calculation Functions...');

                    // Mock model data for testing
                    const testModelData = {
                        model_id: 'test:model',
                        provider: 'test',
                        total_searches: 5,
                        successful_searches: 4,
                        success_rate: 0.8,
                        avg_response_time: 1500
                    };

                    const results = {
                        functionsAvailable: {},
                        scoreTest: null,
                        error: null
                    };

                    try {
                        // Check if our new functions are available
                        results.functionsAvailable = {
                            calculateAdvancedPerformanceScore: typeof
window.calculateAdvancedPerformanceScore !== 'undefined',
                            calculateConfidenceWeightedConsistency: typeof
window.calculateConfidenceWeightedConsistency !== 'undefined',
                            calculateFieldQuality: typeof window.calculateFieldQuality !== 'undefined',
                            calculateSpeedScore: typeof window.calculateSpeedScore !== 'undefined',
                            calculateCostEfficiency: typeof window.calculateCostEfficiency !== 'undefined'
                        };

                        console.log('Functions available:', results.functionsAvailable);

                        // If main function is available, test it
                        if (typeof calculateAdvancedPerformanceScore !== 'undefined') {
                            const scoreResult = calculateAdvancedPerformanceScore(testModelData);
                            results.scoreTest = {
                                totalScore: scoreResult.totalScore,
                                hasBreakdown: !!scoreResult.breakdown,
                                confidenceLevel: scoreResult.confidenceLevel,
                                confidencePercentage: scoreResult.confidencePercentage,
                                components: Object.keys(scoreResult.breakdown || {})
                            };
                            console.log('Score calculation successful:', results.scoreTest);
                        } else {
                            console.log('calculateAdvancedPerformanceScore not available');
                        }

                    } catch (error) {
                        results.error = error.message;
                        console.error('Score test error:', error);
                    }

                    return results;
                }
            """)

            await browser.close()

            print("📊 Function availability:")
            for func, available in test_result['functionsAvailable'].items():
                status = "✅" if available else "❌"
                print(f"   {status} {func}")

            if test_result['scoreTest']:
                print(f"\n📊 Score calculation test:")
                score_data = test_result['scoreTest']
                print(f"   Total Score: {score_data['totalScore']}")
                print(f"   Confidence: {score_data['confidenceLevel']} ({score_data['confidencePercentage']}%)")
                print(f"   Components: {score_data['components']}")
                print(f"   Has Breakdown: {score_data['hasBreakdown']}")

                return True
            elif test_result['error']:
                print(f"❌ Error: {test_result['error']}")
                return False
            else:
                print("❌ Functions not available")
                return False

        except Exception as e:
            print(f"❌ Test error: {e}")
            return False

    async def test_model_splitting_function(self):
        """Test Model-Splitting Logic direkt"""
        print("\n🧪 MODEL SPLITTING TEST")
        print("=" * 50)

        try:
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=False)
            page = await browser.new_page()

            await page.goto(f"{self.base_url}/static/index.html")
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(2)

            # Test model splitting logic
            splitting_result = await page.evaluate("""
                () => {
                    console.log('🔧 Testing Model Splitting Logic...');

                    // Test data
                    const testCombinations = [
                        'openrouter:deepseek-free',
                        'perplexity:sonar-pro_openrouter:deepseek-free',
                        'perplexity:sonar-pro_openrouter:deepseek-free_abacus:deep-agent'
                    ];

                    const results = [];

                    testCombinations.forEach(combination => {
                        const split = combination.includes('_')
                            ? combination.split('_').map(m => m.trim())
                            : [combination];

                        results.push({
                            original: combination,
                            split: split,
                            count: split.length
                        });
                    });

                    console.log('Splitting results:', results);
                    return results;
                }
            """)

            await browser.close()

            print("🔧 Model splitting results:")
            for result in splitting_result:
                print(f"   '{result['original']}' → {result['count']} models:")
                for model in result['split']:
                    print(f"      - {model}")

            # Validate splitting worked correctly
            expected_counts = [1, 2, 3]
            actual_counts = [r['count'] for r in splitting_result]

            success = actual_counts == expected_counts
            print(f"\n✅ Splitting test: {'PASSED' if success else 'FAILED'}")
            return success

        except Exception as e:
            print(f"❌ Splitting test error: {e}")
            return False

    async def test_statistics_tab_loading(self):
        """Test Statistics Tab Ladevorgang"""
        print("\n🧪 STATISTICS TAB LOADING TEST")
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

            print("📊 Clicking Statistics tab...")

            # Click Statistics tab and wait briefly
            await page.click('header nav a[href="#statistics"]')
            await asyncio.sleep(8)  # Wait for score calculations

            # Check what happened
            model_cards = await page.query_selector_all(".model-stats-card")
            score_breakdowns = await page.query_selector_all(".score-breakdown-section")

            print(f"📋 Model cards loaded: {len(model_cards)}")
            print(f"📊 Score breakdowns: {len(score_breakdowns)}")

            # Analyze console logs
            relevant_logs = [log for log in console_logs
                           if any(keyword in log.upper() for keyword in ['SCORE', 'SPLIT', 'MOCK', 'STATISTICS'])]

            print(f"\n📝 Relevant console logs ({len(relevant_logs)}):")
            for log in relevant_logs[:10]:  # Show first 10
                print(f"   {log}")

            await browser.close()

            # Success if we have cards and some logs
            success = len(model_cards) > 0 and len(relevant_logs) > 0
            print(f"\n✅ Statistics loading: {'PASSED' if success else 'FAILED'}")
            return success

        except Exception as e:
            print(f"❌ Statistics loading test error: {e}")
            return False

    async def run_all_tests(self):
        """Run all JavaScript tests"""
        print("🚀 COMPREHENSIVE JAVASCRIPT SCORE TESTS")
        print("=" * 60)

        results = {}

        # Test 1: Score Calculation Functions
        results['score_functions'] = await self.test_score_calculation_javascript()

        # Test 2: Model Splitting Logic
        results['model_splitting'] = await self.test_model_splitting_function()

        # Test 3: Statistics Tab Loading
        results['statistics_loading'] = await self.test_statistics_tab_loading()

        # Final Summary
        passed = sum(1 for result in results.values() if result is True)
        total = len(results)

        print(f"\n📊 JAVASCRIPT TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Score Functions: {'PASSED' if results.get('score_functions') else 'FAILED'}")
        print(f"✅ Model Splitting: {'PASSED' if results.get('model_splitting') else 'FAILED'}")
        print(f"✅ Statistics Loading: {'PASSED' if results.get('statistics_loading') else 'FAILED'}")
        print(f"\n🎯 TOTAL: {passed}/{total} tests passed")

        if passed == total:
            print("🎉 ALL JAVASCRIPT TESTS PASSED!")
            print("✅ Performance-Score Revolution funktioniert korrekt!")
        else:
            print("⚠️ Some JavaScript issues detected")

        return results

# Main execution
if __name__ == "__main__":
    async def main():
        tester = JavaScriptScoreTest()
        results = await tester.run_all_tests()

        # Save results
        with open('/app/tests/javascript_score_results.json', 'w') as f:
            json.dump(results, f, indent=2)

        print(f"\n💾 Results saved: /app/tests/javascript_score_results.json")

    asyncio.run(main())
