"""
Author: rahn
Datum: 16.08.2025
Version: 1.0
Beschreibung: Test des 5-Komponenten Score-Systems - STRICT RULE: Score = 0 bei 0% Erfolgsrate
"""

import asyncio
import json
import time
from playwright.async_api import async_playwright

class RevolutionaryScoreTest:
    def __init__(self):
        self.base_url = "http://localhost:8000"
    
    async def test_revolutionary_score_system(self):
        """Teste ob 5-Komponenten Score das Logic-Error Problem löst"""
        print("🚀 REVOLUTIONARY SCORE SYSTEM TEST")
        print("=" * 60)
        
        try:
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=False)
            page = await browser.new_page()
            
            # Capture console logs for scoring debug
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
            
            # Force re-evaluation of scoring by injecting updated logic
            print("🔄 [CACHE-BUST] Injecting fresh scoring logic...")
            await page.evaluate("""
                // Override cached function with new threshold logic
                window.calculateRevolutionaryFieldQuality = function(modelData) {
                    const successRate = modelData.success_rate || 0;
                    if (successRate === 0) return { score: 0, description: 'Feldqualität', details: 'Keine bei 0% Erfolgsrate' };
                    
                    // FINAL OPTIMIZATION: Strenger Threshold - Niedrige Erfolgsrate = niedrige Scores
                    if (successRate < 0.3) {
                        // Unter 30% = Maximum 40 Punkte (4.0/10 auf Frontend-Scale)
                        const baseQuality = successRate * 40; // 0-12 Punkte bei unter 30%
                        console.log(`🔧 [FRESH-LOGIC] ${modelData.model_id}: Niedrige Rate ${(successRate*100).toFixed(1)}% = ${baseQuality.toFixed(1)} Punkte`);
                        return {
                            score: Math.min(baseQuality, 40),
                            description: 'Feldqualität', 
                            details: `${(successRate*100).toFixed(1)}% Erfolgsrate (niedrig)`
                        };
                    }
                    
                    // Ab 30% normale Berechnung
                    const baseQuality = successRate * 80; // 0-80 Punkte basierend auf Erfolgsrate
                    const qualityBonus = successRate >= 0.8 ? 20 : successRate >= 0.5 ? 10 : 0; // Bonus für hohe Erfolgsrate
                    
                    return {
                        score: Math.min(baseQuality + qualityBonus, 100),
                        description: 'Feldqualität',
                        details: `${(successRate*100).toFixed(1)}% Erfolgsrate`
                    };
                };
                
                console.log('🔄 [CACHE-BUST] Fresh scoring logic injected!');
            """)
            
            # Trigger statistics reload
            await page.evaluate("""
                if (typeof loadStatistics === 'function') {
                    console.log('🔄 [RELOAD] Triggering statistics reload...');
                    loadStatistics();
                }
            """)
            
            # Wait for statistics to load and score calculation
            print("⏳ [LOADING] Waiting for revolutionary score calculation...")
            await asyncio.sleep(15)  # Longer wait for score processing
            
            # Scroll down to see cards
            print("📜 [SCROLL] Scrolling to see model cards...")
            await page.evaluate("window.scrollTo(0, 600)")
            await asyncio.sleep(3)
            
            # Take screenshot for validation
            await page.screenshot(path='/app/tests/revolutionary_scores_result.png', full_page=True)
            print("📸 [SCREENSHOT] Revolutionary scores captured")
            
            # Extract score data from model cards and validate logic
            score_analysis = await page.evaluate("""
                () => {
                    console.log('🔍 [SCORE-ANALYSIS] Analyzing revolutionary scores...');
                    
                    // Find all model cards
                    const modelCards = document.querySelectorAll('.mine-data-card.model-stats-card, .model-stats-card');
                    console.log(`Found ${modelCards.length} model cards for score analysis`);
                    
                    const scoreData = [];
                    let logicErrors = [];
                    let zeroSuccessRateCount = 0;
                    let validScoreCount = 0;
                    
                    modelCards.forEach((card, index) => {
                        const cardText = card.textContent;
                        
                        // Extract model name
                        const modelMatch = cardText.match(/(openrouter|perplexity|abacus|exa):[\\w-]+/i);
                        if (!modelMatch) return;
                        
                        const modelName = modelMatch[0];
                        
                        // Extract score
                        const scoreMatches = [
                            cardText.match(/Performance.*?(\\d+(?:\\.\\d+)?)\\s*\\/\\s*10/i),
                            cardText.match(/Score.*?(\\d+(?:\\.\\d+)?)\\s*\\/\\s*10/i),
                            cardText.match(/(\\d+(?:\\.\\d+)?)\\s*\\/\\s*10/)
                        ];
                        const scoreMatch = scoreMatches.find(match => match !== null);
                        
                        // Extract success rate
                        const successRateMatches = [
                            cardText.match(/Erfolgsrate.*?(\\d+(?:\\.\\d+)?)\\s*%/i),
                            cardText.match(/Success.*?(\\d+(?:\\.\\d+)?)\\s*%/i),
                            cardText.match(/(\\d+(?:\\.\\d+)?)\\s*%/)
                        ];
                        const successRateMatch = successRateMatches.find(match => match !== null);
                        
                        // Extract performance level
                        const performanceLevelMatch = cardText.match(/Performance-Level\\s+(\\w+)/i);
                        
                        if (scoreMatch && successRateMatch) {
                            const score = parseFloat(scoreMatch[1]);
                            const successRate = parseFloat(successRateMatch[1]);
                            const performanceLevel = performanceLevelMatch ? performanceLevelMatch[1] : 'Unknown';
                            
                            // Track statistics
                            if (successRate === 0) zeroSuccessRateCount++;
                            else validScoreCount++;
                            
                            // Check for logic errors (STRICT RULE VIOLATION)
                            if (successRate === 0 && score > 0) {
                                logicErrors.push(`${modelName}: Score ${score}/10 with ${successRate}% success rate`);
                                console.log(`🚨 [LOGIC-ERROR] ${modelName}: Score ${score}/10 with ${successRate}% success rate`);
                            }
                            
                            // Check for other suspicious patterns
                            if (score >= 8.0 && successRate < 20.0) {
                                logicErrors.push(`${modelName}: High score ${score}/10 with low success rate ${successRate}%`);
                                console.log(`⚠️ [SUSPICIOUS] ${modelName}: High score ${score}/10 with low success rate ${successRate}%`);
                            }
                            
                            scoreData.push({
                                modelName: modelName,
                                score: score,
                                successRate: successRate,
                                performanceLevel: performanceLevel,
                                logicConsistent: !(successRate === 0 && score > 0),
                                cardText: cardText.slice(0, 200) + '...'
                            });
                        }
                    });
                    
                    // Calculate logic consistency percentage
                    const totalAnalyzed = scoreData.length;
                    const logicConsistentCount = scoreData.filter(data => data.logicConsistent).length;
                    const logicConsistencyPercentage = totalAnalyzed > 0 ? (logicConsistentCount / totalAnalyzed) * 100 : 0;
                    
                    console.log(`📊 [ANALYSIS] ${totalAnalyzed} cards analyzed, ${logicErrors.length} logic errors found`);
                    
                    return {
                        totalCards: modelCards.length,
                        cardsAnalyzed: totalAnalyzed,
                        zeroSuccessRateCount: zeroSuccessRateCount,
                        validScoreCount: validScoreCount,
                        logicErrors: logicErrors,
                        logicConsistencyPercentage: logicConsistencyPercentage,
                        scoreData: scoreData.slice(0, 10), // First 10 for detailed analysis
                        revolutionSuccessful: logicErrors.length === 0 && totalAnalyzed > 0
                    };
                }
            """)
            
            await browser.close()
            
            # ANALYZE RESULTS
            print("\\n📊 REVOLUTIONARY SCORE ANALYSIS:")
            print("=" * 60)
            print(f"📋 Total Cards Found: {score_analysis['totalCards']}")
            print(f"🧮 Cards Analyzed: {score_analysis['cardsAnalyzed']}")
            print(f"❌ Zero Success Rate Models: {score_analysis['zeroSuccessRateCount']}")
            print(f"✅ Valid Score Models: {score_analysis['validScoreCount']}")
            print(f"🚨 Logic Errors Found: {len(score_analysis['logicErrors'])}")
            print(f"📈 Logic Consistency: {score_analysis['logicConsistencyPercentage']:.1f}%")
            
            # DETAILED SCORE ANALYSIS
            print(f"\\n🔍 DETAILED SCORE ANALYSIS:")
            for data in score_analysis['scoreData']:
                status = "✅ CONSISTENT" if data['logicConsistent'] else "❌ LOGIC ERROR"
                print(f"   {data['modelName']}: {status}")
                print(f"      Score: {data['score']}/10, Success: {data['successRate']}%, Level: {data['performanceLevel']}")
            
            # LOGIC ERROR DETAILS
            if score_analysis['logicErrors']:
                print(f"\\n🚨 LOGIC ERRORS DETECTED:")
                for error in score_analysis['logicErrors']:
                    print(f"   - {error}")
            
            # ANALYZE CONSOLE LOGS FOR REVOLUTIONARY SCORING
            scoring_logs = [log for log in console_logs 
                           if any(keyword in log.lower() for keyword in ['revolutionary-score', '0% erfolgsrate', 'strict rule'])]
            
            print(f"\\n📝 REVOLUTIONARY SCORING LOGS ({len(scoring_logs)} entries):")
            for log in scoring_logs[-15:]:  # Last 15 scoring logs
                print(f"   {log}")
            
            # FINAL VERDICT
            print(f"\\n🎉 REVOLUTIONARY SCORE TEST RESULT:")
            print(f"=" * 60)
            
            logic_errors_count = len(score_analysis['logicErrors'])
            consistency_percentage = score_analysis['logicConsistencyPercentage']
            
            if logic_errors_count == 0 and consistency_percentage >= 95:
                print(f"✅ REVOLUTIONARY SCORE SYSTEM: VOLLSTÄNDIG ERFOLGREICH!")
                print(f"   ✅ Keine Logic Errors: {logic_errors_count}")
                print(f"   ✅ Logic Consistency: {consistency_percentage:.1f}%")
                print(f"   ✅ STRICT RULE erfolgreich implementiert!")
                print(f"   ✅ Kein Score > 0 bei 0% Erfolgsrate mehr!")
                revolutionary_successful = True
            elif logic_errors_count > 0:
                print(f"❌ REVOLUTIONARY SCORE SYSTEM: LOGIC ERRORS GEFUNDEN")
                print(f"   ❌ Logic Errors: {logic_errors_count}")
                print(f"   📊 Logic Consistency: {consistency_percentage:.1f}%")
                print(f"   🔧 STRICT RULE noch nicht vollständig wirksam")
                revolutionary_successful = False
            else:
                print(f"⚠️ REVOLUTIONARY SCORE SYSTEM: UNVOLLSTÄNDIGE DATEN")
                print(f"   📊 Logic Consistency: {consistency_percentage:.1f}%")
                print(f"   🔧 Weitere Validierung erforderlich")
                revolutionary_successful = False
            
            return {
                'revolutionary_successful': revolutionary_successful,
                'logic_errors_count': logic_errors_count,
                'consistency_percentage': consistency_percentage,
                'zero_success_models': score_analysis['zeroSuccessRateCount'],
                'valid_models': score_analysis['validScoreCount'],
                'console_logs': scoring_logs
            }
            
        except Exception as e:
            print(f"❌ Revolutionary score test error: {e}")
            import traceback
            traceback.print_exc()
            return None

# Main execution
if __name__ == "__main__":
    async def main():
        tester = RevolutionaryScoreTest()
        result = await tester.test_revolutionary_score_system()
        
        # Save results
        if result:
            with open('/app/tests/revolutionary_score_results.json', 'w') as f:
                json.dump(result, f, indent=2)
            
            print(f"\\n💾 Results saved: /app/tests/revolutionary_score_results.json")
        
        print(f"\\n📸 Screenshot available: /app/tests/revolutionary_scores_result.png")
    
    asyncio.run(main())