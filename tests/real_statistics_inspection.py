"""
Author: rahn
Datum: 16.08.2025
Version: 1.0
Beschreibung: ECHTE Statistics-Seite Inspektion - Was wird TATSÄCHLICH angezeigt?
"""

import asyncio
import json
from playwright.async_api import async_playwright

class RealStatisticsInspection:
    def __init__(self):
    """__init__ - TODO: Dokumentation hinzufügen"""
        self.base_url = "http://localhost:8000"

    async def inspect_real_statistics_page(self):
        """Inspiziere was WIRKLICH auf der Statistics-Seite angezeigt wird"""
        print("🔍 ECHTE STATISTICS-SEITE INSPEKTION")
        print("=" * 60)

        try:
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=False)
            page = await browser.new_page()

            # Capture console logs
            console_logs = []
            page.on("console", lambda msg: console_logs.append(f"{msg.type}: {msg.text}"))

            # Navigate to main page
            print("📍 [NAVIGATION] Loading main page...")
            await page.goto(f"{self.base_url}/static/index.html")
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(3)

            # Navigate to Statistics Tab
            print("📍 [NAVIGATION] Clicking Statistics tab...")
            stats_tab = await page.query_selector('nav.main-navigation a[data-tab="statistics"]')
            if not stats_tab:
                stats_tab = await page.query_selector('a[onclick*="statistics"]')

            await stats_tab.click()
            print("✅ [NAVIGATION] Statistics tab clicked")

            # Wait for statistics to load
            print("⏳ [LOADING] Waiting for statistics to load...")
            await asyncio.sleep(10)  # Longer wait to ensure everything loads

            # Scroll down to see cards
            print("📜 [SCROLL] Scrolling down to see cards...")
            await page.evaluate("window.scrollTo(0, 400)")
            await asyncio.sleep(2)

            # Take a screenshot for debugging
            await page.screenshot(path='/app/tests/statistics_page_screenshot.png')

            # DETAILED INSPECTION of what's actually displayed
            inspection_result = await page.evaluate("""
                () => {
                    console.log('🔍 [REAL-INSPECTION] Starting detailed inspection...');

                    // Look for any statistics containers
                    const containers = [
                        document.querySelector('#model-statistics-table-container'),
                        document.querySelector('#statistics-content'),
                        document.querySelector('.statistics-container'),
                        document.querySelector('#statistics'),
                        ...document.querySelectorAll('[id*="stat"]'),
                        ...document.querySelectorAll('[class*="stat"]'),
                        ...document.querySelectorAll('[class*="card"]'),
                        ...document.querySelectorAll('[class*="model"]')
                    ].filter(el => el !== null);

                    console.log(`Found ${containers.length} potential statistics containers`);

                    // Inspect all cards
                    const allCards = document.querySelectorAll('.card, .data-card, .model-card,
.model-stats-card, .statistics-card, [class*="card"]');
                    console.log(`Found ${allCards.length} cards of any type`);

                    const cardDetails = [];

                    allCards.forEach((card, index) => {
                        try {
                            const cardInfo = {
                                index: index,
                                className: card.className,
                                innerHTML: card.innerHTML.slice(0, 500), // First 500 chars
                                textContent: card.textContent.slice(0, 200), // First 200 chars
                                hasPerformanceScore: card.textContent.includes('Performance') ||
card.textContent.includes('Score'),
                                hasSuccessRate: card.textContent.includes('Erfolgsrate') ||
card.textContent.includes('Success'),
                                hasModelName: card.textContent.includes('openrouter') ||
card.textContent.includes('perplexity') || card.textContent.includes('abacus'),
                                visible: card.offsetHeight > 0 && card.offsetWidth > 0
                            };

                            // Extract specific values if visible
                            if (cardInfo.visible && cardInfo.hasModelName) {
                                const text = card.textContent;

                                // Look for performance score
                                const scoreMatch = text.match(/Performance.*?(\d+(?:\.\d+)?)\s*\/\s*10/i) ||
                                                 text.match(/Score.*?(\d+(?:\.\d+)?)\s*\/\s*10/i) ||
                                                 text.match(/(\d+(?:\.\d+)?)\s*\/\s*10/);
                                if (scoreMatch) {
                                    cardInfo.extractedScore = parseFloat(scoreMatch[1]);
                                }

                                // Look for success rate
                                const rateMatch = text.match(/Erfolgsrate.*?(\d+(?:\.\d+)?)\s*%/i) ||
                                               text.match(/Success.*?(\d+(?:\.\d+)?)\s*%/i);
                                if (rateMatch) {
                                    cardInfo.extractedSuccessRate = parseFloat(rateMatch[1]);
                                }

                                // Look for model name
                                const modelMatch = text.match(/(openrouter|perplexity|abacus):[\\w-]+/i);
                                if (modelMatch) {
                                    cardInfo.extractedModelName = modelMatch[0];
                                }
                            }

                            cardDetails.push(cardInfo);

                        } catch (error) {
                            console.error(`Error inspecting card ${index}:`, error.message);
                        }
                    });

                    // Get the first visible model card details
                    const firstModelCard = cardDetails.find(card =>
                        card.visible && card.hasModelName &&
                        (card.hasPerformanceScore || card.hasSuccessRate)
                    );

                    // Check what's in the main statistics container
                    const mainContainer = document.querySelector('#model-statistics-table-container');
                    let containerContent = 'Not found';
                    if (mainContainer) {
                        containerContent = mainContainer.innerHTML.slice(0, 1000);
                    }

                    // Look for any error messages
                    const errorElements = document.querySelectorAll('[style*="color: red"], .error,
[class*="error"], [class*="fail"]');
                    const errors = Array.from(errorElements).map(el => el.textContent.slice(0, 100));

                    return {
                        totalCards: allCards.length,
                        visibleCards: cardDetails.filter(c => c.visible).length,
                        modelCards: cardDetails.filter(c => c.hasModelName).length,
                        cardsWithScores: cardDetails.filter(c => c.hasPerformanceScore).length,
                        cardsWithSuccessRates: cardDetails.filter(c => c.hasSuccessRate).length,
                        cardDetails: cardDetails.filter(c => c.visible && c.hasModelName).slice(0,
5), // First 5 model cards
                        firstModelCard: firstModelCard,
                        containerContent: containerContent,
                        errors: errors,
                        pageTitle: document.title,
                        currentUrl: window.location.href,
                        statisticsTabActive:
document.querySelector('.nav-item[data-tab="statistics"]')?.classList.contains('active')
                    };
                }
            """)

            await browser.close()

            # DETAILED ANALYSIS AND REPORTING
            print("\n📊 ECHTE STATISTICS-SEITE ANALYSE:")
            print("=" * 60)
            print(f"📋 Total Cards Found: {inspection_result['totalCards']}")
            print(f"👁️ Visible Cards: {inspection_result['visibleCards']}")
            print(f"🤖 Model Cards: {inspection_result['modelCards']}")
            print(f"🎯 Cards with Performance Scores: {inspection_result['cardsWithScores']}")
            print(f"📈 Cards with Success Rates: {inspection_result['cardsWithSuccessRates']}")
            print(f"🎛️ Statistics Tab Active: {inspection_result['statisticsTabActive']}")

            if inspection_result['errors']:
                print(f"\n❌ ERRORS FOUND: {len(inspection_result['errors'])}")
                for error in inspection_result['errors']:
                    print(f"   - {error}")

            print(f"\n📄 Container Content Preview:")
            print(f"   {inspection_result['containerContent'][:200]}...")

            if inspection_result['firstModelCard']:
                print(f"\n🔍 ERSTE MODEL CARD DETAILS:")
                first_card = inspection_result['firstModelCard']
                print(f"   📛 Model Name: {first_card.get("extractedModelName", 'Not found')}")
                print(f"   🎯 Performance Score: {first_card.get("extractedScore", 'Not found')}")
                print(f"   📈 Success Rate: {first_card.get("extractedSuccessRate", 'Not found')}%")
                print(f"   📝 Class: {first_card.get("className", 'Not found')}")
                print(f"   📄 Text Preview: {first_card.get("textContent", 'No text')[:150]}...")

                # CHECK FOR LOGIC ERRORS IN FIRST CARD
                if (first_card.get('extractedScore') is not None and
                    first_card.get('extractedSuccessRate') is not None):
                    score = first_card['extractedScore']
                    success_rate = first_card['extractedSuccessRate']

                    print(f"\n🚨 LOGIC ERROR CHECK:")
                    if score >= 9.0 and success_rate == 0.0:
                        print(f"   ❌ CRITICAL: Score {score}/10 with {success_rate}% success rate")
                    elif score > (success_rate / 10 + 3):
                        print(f"   ⚠️ SUSPICIOUS: Score {score}/10 seems high for {success_rate}% success rate")
                    else:
                        print(f"   ✅ LOGIC OK: Score {score}/10 with {success_rate}% success rate")

            print(f"\n📋 ALLE SICHTBAREN MODEL CARDS:")
            for i, card in enumerate(inspection_result['cardDetails']):
                print(f"   Card {i+1}: {card.get("extractedModelName", 'Unknown')} - "
                      f"Score: {card.get("extractedScore", 'N/A')} - "
                      f"Success: {card.get("extractedSuccessRate", 'N/A')}%")

            # Check relevant console logs
            score_logs = [log for log in console_logs
                         if any(keyword in log.lower() for keyword in ['score', 'success',
'performance', 'statistics', 'field-quality'])]

            if score_logs:
                print(f"\n📝 RELEVANTE CONSOLE LOGS ({len(score_logs)} entries):")
                for log in score_logs[-15:]:  # Last 15 relevant logs
                    print(f"   {log}")

            return inspection_result

        except Exception as e:
            print(f"❌ Real statistics inspection error: {e}")
            return None

# Main execution
if __name__ == "__main__":
    async def main():
        inspector = RealStatisticsInspection()
        result = await inspector.inspect_real_statistics_page()

        # Save results
        if result:
            with open('/app/tests/real_statistics_inspection_results.json', 'w') as f:
                json.dump(result, f, indent=2)

            print(f"\n💾 Results saved: /app/tests/real_statistics_inspection_results.json")

        print(f"\n📸 Screenshot available: /app/tests/statistics_page_screenshot.png")

    asyncio.run(main())
