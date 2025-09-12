"""
Author: rahn
Datum: 16.08.2025
Version: 1.0
Beschreibung: Score-Transformation-Fix Validierung - Korrigiert 54.5 -> 10/10 zu 54.5 -> 5.5/10
"""

import asyncio
import json
from playwright.async_api import async_playwright

class ScoreTransformationFixTest:
    def __init__(self):
    """__init__ - TODO: Dokumentation hinzufügen"""
        self.base_url = "http://localhost:8000"

    async def test_score_transformation_fix(self):
        """Teste ob Score-Transformation korrekt funktioniert nach Fix"""
        print("🔧 SCORE-TRANSFORMATION-FIX TEST")
        print("=" * 60)

        try:
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=False)
            page = await browser.new_page()

            # Navigate to main page
            print("📍 [NAVIGATION] Loading main page...")
            await page.goto(f"{self.base_url}/static/index.html")
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(3)

            # Navigate to Statistics Tab
            print("📍 [NAVIGATION] Navigating to Statistics...")
            stats_tab = await page.query_selector('nav.main-navigation a[data-tab="statistics"]')
            if not stats_tab:
                stats_tab = await page.query_selector('a[onclick*="statistics"]')

            await stats_tab.click()
            print("✅ [NAVIGATION] Statistics tab clicked")

            # Wait for statistics to load
            print("⏳ [LOADING] Waiting for statistics to load...")
            await asyncio.sleep(8)

            # Scroll down to see cards
            print("📜 [SCROLL] Scrolling down to see cards...")
            await page.evaluate("window.scrollTo(0, 400)")
            await asyncio.sleep(2)

            # Take screenshot of current state
            await page.screenshot(path='/app/tests/score_fix_before_refresh.png')

            # FORCE CACHE CLEAR + REFRESH to get new JavaScript
            print("🔄 [CACHE-CLEAR] Force refresh to get new data-cards.js...")
            await page.evaluate("""
                // Clear all caches and force reload
                if ('caches' in window) {
                    caches.keys().then(names => {
                        names.forEach(name => caches.delete(name));
                    });
                }
                // Force reload from server
                window.location.reload(true);
            """)
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(5)

            # Navigate back to Statistics after refresh
            print("📍 [REFRESH] Navigating back to Statistics after cache clear...")
            stats_tab = await page.query_selector('nav.main-navigation a[data-tab="statistics"]')
            await stats_tab.click()
            await asyncio.sleep(8)
            await page.evaluate("window.scrollTo(0, 400)")
            await asyncio.sleep(2)

            # Take screenshot after refresh
            await page.screenshot(path='/app/tests/score_fix_after_refresh.png')

            # TEST 1: Check first model card for correct score transformation
            first_card_data = await page.evaluate("""
                () => {
                    const cards = document.querySelectorAll('.mine-data-card.model-stats-card');
                    if (cards.length === 0) return null;

                    const firstCard = cards[0];
                    const cardText = firstCard.textContent;

                    // Extract score
                    const scoreMatch = cardText.match(/Performance.*?(\\d+(?:\\.\\d+)?)\\s*\\/\\s*10/i) ||
                                    cardText.match(/Score.*?(\\d+(?:\\.\\d+)?)\\s*\\/\\s*10/i) ||
                                    cardText.match(/(\\d+(?:\\.\\d+)?)\\s*\\/\\s*10/);

                    // Extract success rate
                    const rateMatch = cardText.match(/Erfolgsrate.*?(\\d+(?:\\.\\d+)?)\\s*%/i);

                    // Extract model name
                    const modelMatch = cardText.match(/(openrouter|perplexity|abacus):[\\w-]+/i);

                    return {
                        modelName: modelMatch ? modelMatch[0] : 'Not found',
                        displayedScore: scoreMatch ? parseFloat(scoreMatch[1]) : null,
                        successRate: rateMatch ? parseFloat(rateMatch[1]) : null,
                        cardText: cardText.slice(0, 300),
                        scorePattern: scoreMatch ? scoreMatch[0] : 'No score pattern found'
                    };
                }
            """)

            # TEST 2: Get backend data for comparison
            backend_response = await page.evaluate("""
                async () => {
                    try {
                        const response = await fetch('/api/results/statistics');
                        const data = await response.json();

                        if (data.success && data.data.model_statistics.length > 0) {
                            const firstModel = data.data.model_statistics[0];
                            return {
                                modelId: firstModel.model_id,
                                backendScore: firstModel.overall_score,
                                backendSuccessRate: firstModel.success_rate_percent || firstModel.success_rate,
                                provider: firstModel.provider
                            };
                        }
                        return null;
                    } catch (error) {
                        return {error: error.message};
                    }
                }
            """)

            await browser.close()

            # ANALYSIS AND VALIDATION
            print("\\n📊 SCORE-TRANSFORMATION-FIX ANALYSE:")
            print("=" * 60)

            if first_card_data:
                print(f"🎯 Frontend Card Data:")
                print(f"   📛 Model: {first_card_data['modelName']}")
                print(f"   🎯 Displayed Score: {first_card_data['displayedScore']}/10")
                print(f"   📈 Success Rate: {first_card_data['successRate']}%")
                print(f"   📝 Score Pattern: {first_card_data['scorePattern']}")
            else:
                print("❌ Frontend Card Data: NOT FOUND")

            if backend_response and 'error' not in backend_response:
                print(f"\\n🔙 Backend API Data:")
                print(f"   📛 Model: {backend_response['modelId']}")
                print(f"   🎯 Backend Score: {backend_response['backendScore']}/100")
                print(f"   📈 Backend Success Rate: {backend_response['backendSuccessRate']}%")
                print(f"   🏢 Provider: {backend_response['provider']}")

                # CALCULATE EXPECTED TRANSFORMATION
                expected_score = (backend_response['backendScore'] / 100) * 10
                print(f"\\n🧮 SCORE-TRANSFORMATION VALIDATION:")
                print(f"   🔙 Backend Score: {backend_response['backendScore']}/100")
                print(f"   ➡️ Expected Frontend: {expected_score:.1f}/10")
                print(f"   🎯 Actual Frontend: {first_card_data['displayedScore']}/10")

                # VALIDATION
                if first_card_data and first_card_data['displayedScore'] is not None:
                    score_diff = abs(expected_score - first_card_data['displayedScore'])
                    if score_diff < 0.1:
                        print(f"   ✅ SCORE-TRANSFORMATION: KORREKT! (Diff: {score_diff:.2f})")
                        transformation_correct = True
                    else:
                        print(f"   ❌ SCORE-TRANSFORMATION: FEHLER! (Diff: {score_diff:.2f})")
                        transformation_correct = False
                else:
                    print(f"   ❌ SCORE-TRANSFORMATION: Frontend Score nicht extrahierbar")
                    transformation_correct = False

                # CHECK FOR 10/10 + 0% LOGIC ERROR
                if (first_card_data and first_card_data['displayedScore'] is not None and
                    first_card_data['successRate'] is not None):
                    score = first_card_data['displayedScore']
                    rate = first_card_data['successRate']

                    print(f"\\n🚨 LOGIC-ERROR CHECK:")
                    if score >= 9.0 and rate == 0.0:
                        print(f"   ❌ CRITICAL: {score}/10 Score with {rate}% Success Rate!")
                        logic_consistent = False
                    elif score > 8.0 and rate < 10.0:
                        print(f"   ⚠️ SUSPICIOUS: {score}/10 Score with {rate}% Success Rate")
                        logic_consistent = False
                    else:
                        print(f"   ✅ LOGIC OK: {score}/10 Score with {rate}% Success Rate")
                        logic_consistent = True
                else:
                    print(f"   ❓ LOGIC CHECK: Insufficient data")
                    logic_consistent = None

            else:
                print(f"❌ Backend API Data: ERROR or NOT FOUND")
                if backend_response and 'error' in backend_response:
                    print(f"   Error: {backend_response['error']}")
                transformation_correct = False
                logic_consistent = False

            # FINAL RESULT
            print(f"\\n🎉 FINAL RESULT:")
            print(f"=" * 60)
            if transformation_correct and logic_consistent:
                print(f"✅ SCORE-TRANSFORMATION-FIX: VOLLSTÄNDIG ERFOLGREICH!")
                print(f"   ✅ Score korrekt skaliert: {backend_response['backendScore']}/100 →
{first_card_data['displayedScore']}/10")
                print(f"   ✅ Logic-Error behoben: Keine 10/10 + 0% Kombinationen")
                overall_success = True
            else:
                print(f"❌ SCORE-TRANSFORMATION-FIX: FEHLGESCHLAGEN!")
                if not transformation_correct:
                    print(f"   ❌ Score-Transformation immer noch falsch")
                if not logic_consistent:
                    print(f"   ❌ Logic-Error immer noch vorhanden")
                overall_success = False

            return {
                'frontend_data': first_card_data,
                'backend_data': backend_response,
                'transformation_correct': transformation_correct,
                'logic_consistent': logic_consistent,
                'overall_success': overall_success
            }

        except Exception as e:
            print(f"❌ Score transformation fix test error: {e}")
            return None

# Main execution
if __name__ == "__main__":
    async def main():
        tester = ScoreTransformationFixTest()
        result = await tester.test_score_transformation_fix()

        # Save results
        if result:
            with open('/app/tests/score_transformation_fix_results.json', 'w') as f:
                json.dump(result, f, indent=2)

            print(f"\\n💾 Results saved: /app/tests/score_transformation_fix_results.json")

        print(f"\\n📸 Screenshots available:")
        print(f"   - Before refresh: /app/tests/score_fix_before_refresh.png")
        print(f"   - After refresh: /app/tests/score_fix_after_refresh.png")

    asyncio.run(main())
