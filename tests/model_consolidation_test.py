"""
Author: rahn
Datum: 16.08.2025
Version: 1.0
Beschreibung: Test der Model-Konsolidierung - Eine Card pro Modell statt Duplikate
"""

import asyncio
import json
import time
from playwright.async_api import async_playwright

class ModelConsolidationTest:
    def __init__(self):
    """__init__ - TODO: Dokumentation hinzufügen"""
        self.base_url = "http://localhost:8000"

    async def test_model_consolidation(self):
        """Teste ob Model-Konsolidierung Duplikate eliminiert"""
        print("🔄 MODEL CONSOLIDATION TEST")
        print("=" * 60)

        try:
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=False)
            page = await browser.new_page()

            # Capture console logs for consolidation debug
            console_logs = []
            page.on("console", lambda msg: console_logs.append(f"{msg.type}: {msg.text}"))

            # Navigate to main page with cache bypass
            print("📍 [NAVIGATION] Loading main page with cache bypass...")
            await page.goto(f"{self.base_url}/static/index.html?cache_bust={int(time.time())}")
            await page.wait_for_load_state("networkidle")

            # Hard refresh to bypass cache
            await page.reload(wait_until="networkidle")
            await asyncio.sleep(3)

            # Navigate to Statistics Tab
            print("📍 [NAVIGATION] Navigating to Statistics...")
            stats_tab = await page.query_selector('nav.main-navigation a[data-tab="statistics"]')
            if not stats_tab:
                stats_tab = await page.query_selector('a[onclick*="statistics"]')

            await stats_tab.click()
            print("✅ [NAVIGATION] Statistics tab clicked")

            # No debug injection - let natural logging work

            # Wait for consolidation processing
            print("⏳ [LOADING] Waiting for model consolidation...")
            await asyncio.sleep(15)  # Wait for consolidation processing

            # Scroll down to see cards
            print("📜 [SCROLL] Scrolling to see model cards...")
            await page.evaluate("window.scrollTo(0, 600)")
            await asyncio.sleep(3)

            # Take screenshot for validation
            await page.screenshot(path='/app/tests/model_consolidation_result.png', full_page=True)
            print("📸 [SCREENSHOT] Model consolidation captured")

            # Extract consolidation data and check for duplicates
            consolidation_analysis = await page.evaluate("""
                () => {
                    console.log('🔍 [CONSOLIDATION-ANALYSIS] Analyzing model consolidation...');

                    // Find all model cards
                    const modelCards = document.querySelectorAll('.mine-data-card.model-stats-card, .model-stats-card');
                    console.log(`Found ${modelCards.length} model cards for consolidation analysis`);

                    const modelData = [];
                    const modelCounts = {};
                    let duplicatesFound = [];

                    modelCards.forEach((card, index) => {
                        const cardText = card.textContent;

                        // Extract model name
                        const modelMatch = cardText.match(/(openrouter|perplexity|abacus|exa):[\\w-]+/i);
                        if (!modelMatch) return;

                        const modelName = modelMatch[0];

                        // Count occurrences
                        if (!modelCounts[modelName]) {
                            modelCounts[modelName] = 0;
                        }
                        modelCounts[modelName]++;

                        // Extract basic stats
                        const scoreMatch = cardText.match(/Performance.*?(\\d+(?:\\.\\d+)?)\\s*\\/\\s*10/i);
                        const successMatch = cardText.match(/Erfolgsrate.*?(\\d+(?:\\.\\d+)?)\\s*%/i);
                        const searchMatch = cardText.match(/Gesamte Suchen.*?(\\d+)/i);

                        modelData.push({
                            index: index + 1,
                            modelName: modelName,
                            score: scoreMatch ? parseFloat(scoreMatch[1]) : 0,
                            successRate: successMatch ? parseFloat(successMatch[1]) : 0,
                            totalSearches: searchMatch ? parseInt(searchMatch[1]) : 0,
                            cardPreview: cardText.slice(0, 150) + '...'
                        });
                    });

                    // Find duplicates
                    Object.entries(modelCounts).forEach(([modelName, count]) => {
                        if (count > 1) {
                            duplicatesFound.push({
                                modelName: modelName,
                                count: count
                            });
                        }
                    });

                    const uniqueModels = Object.keys(modelCounts).length;
                    const totalCards = modelCards.length;
                    const consolidationSuccessful = duplicatesFound.length === 0;

                    console.log(`📊 [CONSOLIDATION-ANALYSIS] ${totalCards} cards, ${uniqueModels}
unique models, ${duplicatesFound.length} duplicates`);

                    return {
                        totalCards: totalCards,
                        uniqueModels: uniqueModels,
                        duplicatesFound: duplicatesFound,
                        consolidationSuccessful: consolidationSuccessful,
                        modelData: modelData.slice(0, 15), // First 15 for detailed analysis
                        modelCounts: modelCounts
                    };
                }
            """)

            await browser.close()

            # ANALYZE CONSOLIDATION RESULTS
            print("\\n📊 MODEL CONSOLIDATION ANALYSIS:")
            print("=" * 60)
            print(f"📋 Total Cards Found: {consolidation_analysis['totalCards']}")
            print(f"🎯 Unique Models: {consolidation_analysis['uniqueModels']}")
            print(f"🔁 Duplicates Found: {len(consolidation_analysis['duplicatesFound'])}")

            # DETAILED CONSOLIDATION ANALYSIS
            print(f"\\n🔍 DETAILED CONSOLIDATION ANALYSIS:")
            if consolidation_analysis['duplicatesFound']:
                print("❌ DUPLICATES DETECTED:")
                for duplicate in consolidation_analysis['duplicatesFound']:
                    print(f"   - {duplicate['modelName']}: {duplicate['count']} cards")
            else:
                print("✅ NO DUPLICATES - Perfect consolidation!")

            # SAMPLE MODEL DATA
            print(f"\\n📋 SAMPLE MODEL DATA:")
            for data in consolidation_analysis['modelData'][:10]:
                print(f"   Card {data['index']}: {data['modelName']}")
                print(f"      Score: {data['score']}/10, Success: {data['successRate']}%, Searches:
{data['totalSearches']}")

            # ANALYZE CONSOLE LOGS FOR CONSOLIDATION
            consolidation_logs = [log for log in console_logs
                                 if any(keyword in log.lower() for keyword in
['model-consolidation', 'consolidating', 'duplicate'])]

            print(f"\\n📝 CONSOLIDATION LOGS ({len(consolidation_logs)} entries):")
            for log in consolidation_logs[-10:]:  # Last 10 consolidation logs
                print(f"   {log}")

            # FINAL VERDICT
            print(f"\\n🎉 MODEL CONSOLIDATION TEST RESULT:")
            print(f"=" * 60)

            if consolidation_analysis['consolidationSuccessful']:
                print(f"✅ MODEL CONSOLIDATION: VOLLSTÄNDIG ERFOLGREICH!")
                print(f"   ✅ Keine Duplikate gefunden: {len(consolidation_analysis['duplicatesFound'])}")
                print(f"   ✅ Unique Models: {consolidation_analysis['uniqueModels']}")
                print(f"   ✅ Eine Card pro Modell erfolgreich implementiert!")
                consolidation_successful = True
            else:
                duplicates_count = len(consolidation_analysis['duplicatesFound'])
                print(f"❌ MODEL CONSOLIDATION: DUPLIKATE GEFUNDEN")
                print(f"   ❌ Duplikate: {duplicates_count}")
                print(f"   📊 Total Cards: {consolidation_analysis['totalCards']}")
                print(f"   📊 Unique Models: {consolidation_analysis['uniqueModels']}")
                print(f"   🔧 Konsolidierung unvollständig")
                consolidation_successful = False

            return {
                'consolidation_successful': consolidation_successful,
                'total_cards': consolidation_analysis['totalCards'],
                'unique_models': consolidation_analysis['uniqueModels'],
                'duplicates_found': consolidation_analysis['duplicatesFound'],
                'console_logs': consolidation_logs
            }

        except Exception as e:
            print(f"❌ Model consolidation test error: {e}")
            import traceback
            traceback.print_exc()
            return None

# Main execution
if __name__ == "__main__":
    async def main():
        tester = ModelConsolidationTest()
        result = await tester.test_model_consolidation()

        # Save results
        if result:
            with open('/app/tests/model_consolidation_results.json', 'w') as f:
                json.dump(result, f, indent=2)

            print(f"\\n💾 Results saved: /app/tests/model_consolidation_results.json")

        print(f"\\n📸 Screenshot available: /app/tests/model_consolidation_result.png")

    asyncio.run(main())
