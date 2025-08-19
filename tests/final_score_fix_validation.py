"""
Author: rahn
Datum: 16.08.2025
Version: 1.0
Beschreibung: Finale Validierung - Score-Fix funktioniert (5.5/10 statt 10/10)
"""

import asyncio
from playwright.async_api import async_playwright

class FinalScoreFixValidation:
    def __init__(self):
        self.base_url = "http://localhost:8000"
    
    async def validate_final_fix(self):
        """Finale Validierung: Score-Transformation-Fix erfolgreich"""
        print("🎉 FINALE SCORE-FIX VALIDIERUNG")
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
            print("📍 [NAVIGATION] Navigating to Statistics tab...")
            stats_tab = await page.query_selector('nav.main-navigation a[data-tab="statistics"]')
            if not stats_tab:
                # Try alternative selector
                stats_tab = await page.query_selector('a[onclick*="statistics"]')
                if not stats_tab:
                    # Try clicking statistics link in navigation
                    await page.click('text=Statistiken')
            
            if stats_tab:
                await stats_tab.click()
                print("✅ [NAVIGATION] Statistics tab clicked")
            else:
                print("⚠️ [NAVIGATION] Direct statistics navigation, trying hash...")
                await page.goto(f"{self.base_url}/static/index.html#statistics")
            
            # Wait for statistics to load
            print("⏳ [LOADING] Waiting for statistics to load...")
            await asyncio.sleep(10)
            
            # Scroll down to see cards
            print("📜 [SCROLL] Scrolling down to see model cards...")
            await page.evaluate("window.scrollTo(0, 600)")
            await asyncio.sleep(3)
            
            # Take screenshot of Statistics page
            await page.screenshot(path='/app/tests/final_statistics_validation.png', full_page=True)
            print("📸 [SCREENSHOT] Statistics page captured")
            
            # Extract score information from model cards
            score_data = await page.evaluate("""
                () => {
                    console.log('🔍 [VALIDATION] Extracting score data from model cards...');
                    
                    // Look for model cards with scores
                    const modelCards = document.querySelectorAll('.mine-data-card.model-stats-card, .model-stats-card, .data-card');
                    console.log(`Found ${modelCards.length} potential model cards`);
                    
                    const cardData = [];
                    
                    modelCards.forEach((card, index) => {
                        const cardText = card.textContent;
                        
                        // Extract model name
                        const modelMatch = cardText.match(/(openrouter|perplexity|abacus|exa):[\\w-]+/i);
                        
                        // Extract score patterns
                        const scorePatterns = [
                            cardText.match(/Performance.*?(\\d+(?:\\.\\d+)?)\\s*\\/\\s*10/i),
                            cardText.match(/Score.*?(\\d+(?:\\.\\d+)?)\\s*\\/\\s*10/i),
                            cardText.match(/(\\d+(?:\\.\\d+)?)\\s*\\/\\s*10/),
                            cardText.match(/Score:\\s*(\\d+(?:\\.\\d+)?)/i)
                        ];
                        
                        // Extract success rate
                        const rateMatch = cardText.match(/Erfolgsrate.*?(\\d+(?:\\.\\d+)?)\\s*%/i) ||
                                       cardText.match(/Success.*?(\\d+(?:\\.\\d+)?)\\s*%/i);
                        
                        // Extract performance level
                        const levelMatch = cardText.match(/Performance-Level\\s+(\\w+)/i) ||
                                        cardText.match(/Level:\\s+(\\w+)/i);
                        
                        if (modelMatch) {
                            const scoreMatch = scorePatterns.find(match => match !== null);
                            
                            cardData.push({
                                index: index + 1,
                                modelName: modelMatch[0],
                                displayedScore: scoreMatch ? parseFloat(scoreMatch[1]) : null,
                                scorePattern: scoreMatch ? scoreMatch[0] : 'No score found',
                                successRate: rateMatch ? parseFloat(rateMatch[1]) : null,
                                performanceLevel: levelMatch ? levelMatch[1] : null,
                                cardText: cardText.slice(0, 200) + '...',
                                visible: card.offsetHeight > 0 && card.offsetWidth > 0
                            });
                        }
                    });
                    
                    console.log(`Extracted data from ${cardData.length} model cards`);
                    
                    return {
                        totalCards: modelCards.length,
                        modelCardsWithData: cardData.length,
                        cardData: cardData.slice(0, 5), // First 5 cards
                        pageUrl: window.location.href,
                        statisticsActive: window.location.hash.includes('statistics')
                    };
                }
            """)
            
            await browser.close()
            
            # DETAILED ANALYSIS
            print("\\n📊 SCORE-FIX VALIDIERUNG:")
            print("=" * 60)
            print(f"📄 Page URL: {score_data['pageUrl']}")
            print(f"📊 Statistics Active: {score_data['statisticsActive']}")
            print(f"🎯 Total Cards Found: {score_data['totalCards']}")
            print(f"🤖 Model Cards with Data: {score_data['modelCardsWithData']}")
            
            if score_data['cardData']:
                print(f"\\n🔍 MODEL CARDS SCORE ANALYSIS:")
                
                scores_found = []
                logic_errors = []
                
                for i, card in enumerate(score_data['cardData']):
                    print(f"\\n   Card {card['index']}: {card['modelName']}")
                    print(f"      🎯 Score: {card['displayedScore']}/10 ({card['scorePattern']})")
                    print(f"      📈 Success Rate: {card['successRate']}%")
                    print(f"      📊 Performance Level: {card['performanceLevel']}")
                    print(f"      👁️ Visible: {card['visible']}")
                    
                    if card['displayedScore'] is not None:
                        scores_found.append(card['displayedScore'])
                        
                        # Check for logic errors
                        if card['displayedScore'] >= 9.0 and card['successRate'] == 0.0:
                            logic_errors.append(f"{card['modelName']}: {card['displayedScore']}/10 + {card['successRate']}%")
                        elif card['displayedScore'] >= 9.0 and card['successRate'] and card['successRate'] < 10.0:
                            logic_errors.append(f"{card['modelName']}: {card['displayedScore']}/10 + {card['successRate']}% (suspicious)")
                
                print(f"\\n📈 SCORE-TRANSFORMATION ASSESSMENT:")
                if scores_found:
                    print(f"   ✅ Scores found: {len(scores_found)} cards")
                    print(f"   📊 Score range: {min(scores_found):.1f} - {max(scores_found):.1f}/10")
                    
                    # Check if we still have the 10/10 problem
                    max_scores = [s for s in scores_found if s >= 9.9]
                    if max_scores:
                        print(f"   ⚠️ High scores (9.9+/10): {len(max_scores)} cards")
                        print(f"      Scores: {max_scores}")
                    else:
                        print(f"   ✅ No unrealistic 10/10 scores found!")
                    
                    # Check for expected scores (like 5.5 from our fix)
                    realistic_scores = [s for s in scores_found if 3.0 <= s <= 8.0]
                    if realistic_scores:
                        print(f"   ✅ Realistic scores (3-8/10): {len(realistic_scores)} cards")
                        print(f"      Examples: {realistic_scores[:3]}")
                        
                        # Specific check for our 5.5 score from the fix
                        if 5.5 in scores_found:
                            print(f"   🎉 SCORE-FIX CONFIRMED: 5.5/10 score found!")
                            print(f"      This proves the transformation 54.5/100 → 5.5/10 works!")
                        
                else:
                    print(f"   ❌ No scores found in model cards")
                
                print(f"\\n🚨 LOGIC ERROR CHECK:")
                if logic_errors:
                    print(f"   ❌ Logic errors found: {len(logic_errors)}")
                    for error in logic_errors:
                        print(f"      - {error}")
                else:
                    print(f"   ✅ No logic errors detected!")
                    print(f"      All score/success-rate combinations seem reasonable")
                
                # FINAL VERDICT
                print(f"\\n🎉 FINAL VERDICT:")
                print(f"=" * 60)
                
                fix_successful = (
                    len(scores_found) > 0 and  # Scores are displayed
                    5.5 in scores_found and   # Our specific fix is working
                    len([s for s in scores_found if s >= 9.9]) == 0 and  # No more 10/10 scores
                    len(logic_errors) == 0  # No logic errors
                )
                
                if fix_successful:
                    print(f"✅ SCORE-TRANSFORMATION-FIX: VOLLSTÄNDIG ERFOLGREICH!")
                    print(f"   ✅ Score-Skalierung funktioniert: 54.5/100 → 5.5/10")
                    print(f"   ✅ Keine 10/10 + 0% Logic-Errors mehr")
                    print(f"   ✅ Realistic score distribution")
                    print(f"   ✅ {len(scores_found)} model cards zeigen korrekte Scores")
                else:
                    print(f"⚠️ SCORE-TRANSFORMATION-FIX: TEILWEISE ERFOLGREICH")
                    if 5.5 in scores_found:
                        print(f"   ✅ Core fix working: 5.5/10 score confirmed")
                    if len(logic_errors) == 0:
                        print(f"   ✅ Logic errors resolved")
                    else:
                        print(f"   ❌ Some issues remain")
                        
                return fix_successful
                
            else:
                print(f"❌ No model card data found")
                return False
            
        except Exception as e:
            print(f"❌ Final score fix validation error: {e}")
            import traceback
            traceback.print_exc()
            return False

# Main execution
if __name__ == "__main__":
    async def main():
        validator = FinalScoreFixValidation()
        success = await validator.validate_final_fix()
        
        print(f"\\n📸 Screenshot saved: /app/tests/final_statistics_validation.png")
        
        if success:
            print(f"\\n🚀 MISSION ACCOMPLISHED: Score-Transformation-Fix funktioniert!")
        else:
            print(f"\\n❌ Additional fixes may be needed")
    
    asyncio.run(main())