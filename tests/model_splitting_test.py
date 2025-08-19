"""
Author: rahn
Datum: 16.08.2025
Version: 1.0
Beschreibung: Test des Model-Splitting Fix - Kombinierte Modell-Namen sollten aufgesplittet werden
"""

import asyncio
import json
from playwright.async_api import async_playwright

class ModelSplittingTest:
    def __init__(self):
        self.base_url = "http://localhost:8000"
    
    async def test_model_splitting_fix(self):
        """Teste ob Model-Splitting funktioniert - kombinierte Namen → Einzelmodelle"""
        print("🔧 MODEL-SPLITTING FIX TEST")
        print("=" * 60)
        
        try:
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=False)
            page = await browser.new_page()
            
            # Capture console logs for model splitting debug
            console_logs = []
            page.on("console", lambda msg: console_logs.append(f"{msg.type}: {msg.text}"))
            
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
            
            # Wait for statistics to load and model splitting to process
            print("⏳ [LOADING] Waiting for statistics and model splitting...")
            await asyncio.sleep(12)  # Longer wait for backend processing
            
            # Scroll down to see cards
            print("📜 [SCROLL] Scrolling to see model cards...")
            await page.evaluate("window.scrollTo(0, 600)")
            await asyncio.sleep(3)
            
            # Take screenshot for validation
            await page.screenshot(path='/app/tests/model_splitting_result.png', full_page=True)
            print("📸 [SCREENSHOT] Model splitting result captured")
            
            # Extract all model cards and analyze for combinations
            model_analysis = await page.evaluate("""
                () => {
                    console.log('🔍 [MODEL-ANALYSIS] Analyzing model cards for splitting...');
                    
                    // Find all model cards
                    const modelCards = document.querySelectorAll('.mine-data-card.model-stats-card, .model-stats-card, [data-model]');
                    console.log(`Found ${modelCards.length} potential model cards`);
                    
                    const cardData = [];
                    let combinationsFound = 0;
                    let individualModelsFound = 0;
                    
                    modelCards.forEach((card, index) => {
                        const cardText = card.textContent;
                        
                        // Extract model name from different possible locations
                        let modelName = null;
                        
                        // Method 1: data-model attribute
                        if (card.hasAttribute('data-model')) {
                            modelName = card.getAttribute('data-model');
                        }
                        
                        // Method 2: Extract from text content
                        if (!modelName) {
                            const modelMatch = cardText.match(/(openrouter|perplexity|abacus|exa):[\\w-]+(?:_[^\\s]*)?/i);
                            if (modelMatch) {
                                modelName = modelMatch[0];
                            }
                        }
                        
                        // Method 3: Look for model names in headers
                        if (!modelName) {
                            const header = card.querySelector('h3, .card-title');
                            if (header) {
                                const headerMatch = header.textContent.match(/(openrouter|perplexity|abacus|exa):[\\w-]+/i);
                                if (headerMatch) {
                                    modelName = headerMatch[0];
                                }
                            }
                        }
                        
                        if (modelName) {
                            const isVisible = card.offsetHeight > 0 && card.offsetWidth > 0;
                            
                            // Check if this is a combination (contains underscore)
                            const isCombination = modelName.includes('_');
                            if (isCombination) {
                                combinationsFound++;
                                console.log(`🚨 [COMBINATION] Found: ${modelName}`);
                            } else {
                                individualModelsFound++;
                                console.log(`✅ [INDIVIDUAL] Found: ${modelName}`);
                            }
                            
                            cardData.push({
                                index: index + 1,
                                modelName: modelName,
                                isCombination: isCombination,
                                visible: isVisible,
                                cardText: cardText.slice(0, 150) + '...'
                            });
                        }
                    });
                    
                    console.log(`📊 [ANALYSIS] ${combinationsFound} combinations, ${individualModelsFound} individual models`);
                    
                    return {
                        totalCards: modelCards.length,
                        cardsWithModels: cardData.length,
                        combinationsFound: combinationsFound,
                        individualModelsFound: individualModelsFound,
                        cardData: cardData.slice(0, 10), // First 10 for analysis
                        splitSuccessful: combinationsFound === 0 && individualModelsFound > 0
                    };
                }
            """)
            
            await browser.close()
            
            # ANALYZE RESULTS
            print("\\n📊 MODEL-SPLITTING ANALYSIS:")
            print("=" * 60)
            print(f"📋 Total Cards Found: {model_analysis['totalCards']}")
            print(f"🤖 Cards with Model Names: {model_analysis['cardsWithModels']}")
            print(f"🔗 Combinations Found: {model_analysis['combinationsFound']}")
            print(f"🎯 Individual Models Found: {model_analysis['individualModelsFound']}")
            
            # CHECK FOR MODEL SPLITTING SUCCESS
            combinations_found = model_analysis['combinationsFound']
            individuals_found = model_analysis['individualModelsFound']
            
            print(f"\\n🔍 DETAILED MODEL ANALYSIS:")
            for card in model_analysis['cardData']:
                status = "🚨 COMBINATION" if card['isCombination'] else "✅ INDIVIDUAL"
                print(f"   Card {card['index']}: {status} - {card['modelName']}")
            
            # ANALYZE CONSOLE LOGS FOR MODEL SPLITTING ACTIVITY
            splitting_logs = [log for log in console_logs 
                             if any(keyword in log.lower() for keyword in ['model-splitting', 'combination', 'splitting'])]
            
            print(f"\\n📝 MODEL-SPLITTING CONSOLE LOGS ({len(splitting_logs)} entries):")
            for log in splitting_logs[-10:]:  # Last 10 splitting logs
                print(f"   {log}")
            
            # FINAL VERDICT
            print(f"\\n🎉 MODEL-SPLITTING TEST RESULT:")
            print(f"=" * 60)
            
            if combinations_found == 0 and individuals_found > 0:
                print(f"✅ MODEL-SPLITTING: VOLLSTÄNDIG ERFOLGREICH!")
                print(f"   ✅ Keine Kombinationen mehr vorhanden: {combinations_found}")
                print(f"   ✅ Individual Models gefunden: {individuals_found}")
                print(f"   ✅ Alle Backend-Kombinationen wurden aufgesplittet!")
                splitting_successful = True
            elif combinations_found > 0:
                print(f"⚠️ MODEL-SPLITTING: TEILWEISE ERFOLGREICH")
                print(f"   ❌ Kombinationen noch vorhanden: {combinations_found}")
                print(f"   ✅ Individual Models gefunden: {individuals_found}")
                print(f"   🔧 Zusätzliche Fixes erforderlich")
                splitting_successful = False
            else:
                print(f"❌ MODEL-SPLITTING: FEHLGESCHLAGEN")
                print(f"   ❌ Keine Model-Namen gefunden oder schwerwiegender Fehler")
                splitting_successful = False
            
            return {
                'splitting_successful': splitting_successful,
                'combinations_found': combinations_found,
                'individuals_found': individuals_found,
                'total_cards': model_analysis['totalCards'],
                'console_logs': splitting_logs
            }
            
        except Exception as e:
            print(f"❌ Model splitting test error: {e}")
            import traceback
            traceback.print_exc()
            return None

# Main execution
if __name__ == "__main__":
    async def main():
        tester = ModelSplittingTest()
        result = await tester.test_model_splitting_fix()
        
        # Save results
        if result:
            with open('/app/tests/model_splitting_results.json', 'w') as f:
                json.dump(result, f, indent=2)
            
            print(f"\\n💾 Results saved: /app/tests/model_splitting_results.json")
        
        print(f"\\n📸 Screenshot available: /app/tests/model_splitting_result.png")
    
    asyncio.run(main())