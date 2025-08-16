"""
Author: rahn
Datum: 16.08.2025
Version: 1.0
Beschreibung: Test des Enhanced Model ID Normalization für perfekte Konsolidierung
"""

import asyncio
import json
import time
from playwright.async_api import async_playwright

class EnhancedDuplicateFixTest:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        
    async def test_enhanced_consolidation(self):
        """Test Enhanced Model ID Normalization System"""
        print("🔧 ENHANCED DUPLICATE ELIMINATION TEST")
        print("=" * 60)
        
        try:
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=False)
            page = await browser.new_page()
            
            # Capture detailed console logs for normalization analysis
            console_logs = []
            page.on("console", lambda msg: console_logs.append(f"{msg.type}: {msg.text}"))
            
            # Navigate to Statistics with cache bypass
            print("📍 [NAVIGATION] Loading Statistics with enhanced consolidation...")
            await page.goto(f"{self.base_url}/static/index.html?cache_bust={int(time.time())}")
            await page.wait_for_load_state("networkidle")
            
            # Hard refresh to ensure new cache version
            await page.reload(wait_until="networkidle")
            await asyncio.sleep(3)
            
            # Go to Statistics Tab
            stats_tab = await page.query_selector('nav.main-navigation a[data-tab="statistics"]')
            await stats_tab.click()
            await asyncio.sleep(15)  # Wait for enhanced consolidation processing
            
            # Scroll to see all cards
            await page.evaluate("window.scrollTo(0, 800)")
            await asyncio.sleep(3)
            
            # Take screenshot of enhanced consolidation
            await page.screenshot(path='/app/tests/enhanced_consolidation_result.png', full_page=True)
            
            # Analyze consolidation results with detailed duplicate detection
            consolidation_analysis = await page.evaluate("""
                () => {
                    console.log('🔍 [ENHANCED-ANALYSIS] Analyzing enhanced model consolidation...');
                    
                    const modelCards = document.querySelectorAll('.mine-data-card.model-stats-card, .model-stats-card');
                    console.log(`Found ${modelCards.length} model cards for enhanced analysis`);
                    
                    const modelData = [];
                    const modelCounts = {};
                    const duplicates = [];
                    
                    modelCards.forEach((card, index) => {
                        const cardText = card.textContent;
                        
                        // Extract model name with multiple patterns
                        const modelMatch = cardText.match(/(openrouter|perplexity|abacus|exa):[\\w\\-\\.]+/i);
                        if (!modelMatch) return;
                        
                        const modelName = modelMatch[0];
                        
                        // Enhanced duplicate detection
                        const normalizedName = modelName.toLowerCase().trim();
                        
                        if (!modelCounts[normalizedName]) {
                            modelCounts[normalizedName] = [];
                        }
                        modelCounts[normalizedName].push({
                            original: modelName,
                            cardIndex: index + 1
                        });
                        
                        // Extract performance metrics
                        const scoreMatch = cardText.match(/Performance.*?(\\d+(?:\\.\\d+)?)\\s*\\/\\s*10/i);
                        const successMatch = cardText.match(/Erfolgsrate.*?(\\d+(?:\\.\\d+)?)\\s*%/i);
                        const searchMatch = cardText.match(/Gesamte Suchen.*?(\\d+)/i);
                        
                        modelData.push({
                            cardIndex: index + 1,
                            modelName: modelName,
                            normalizedName: normalizedName,
                            score: scoreMatch ? parseFloat(scoreMatch[1]) : 0,
                            successRate: successMatch ? parseFloat(successMatch[1]) : 0,
                            totalSearches: searchMatch ? parseInt(searchMatch[1]) : 0
                        });
                    });
                    
                    // Find duplicates with detailed analysis
                    Object.entries(modelCounts).forEach(([normalized, instances]) => {
                        if (instances.length > 1) {
                            duplicates.push({
                                normalizedName: normalized,
                                count: instances.length,
                                instances: instances
                            });
                        }
                    });
                    
                    // Enhanced duplicate analysis
                    console.log(`📊 [ENHANCED-ANALYSIS] ${modelCards.length} cards, ${Object.keys(modelCounts).length} unique, ${duplicates.length} duplicates`);
                    
                    // Analyze specific problem models
                    const llamaVariants = modelData.filter(m => m.modelName.toLowerCase().includes('llama-3'));
                    const glmVariants = modelData.filter(m => m.modelName.toLowerCase().includes('glm-4'));
                    
                    return {
                        totalCards: modelCards.length,
                        uniqueModels: Object.keys(modelCounts).length,
                        duplicates: duplicates,
                        llamaVariants: llamaVariants,
                        glmVariants: glmVariants,
                        allModels: modelData,
                        enhancedSuccess: duplicates.length === 0
                    };
                }
            """)
            
            await browser.close()
            
            # ENHANCED CONSOLIDATION ANALYSIS
            print(f"\n🔧 ENHANCED CONSOLIDATION RESULTS:")
            print(f"=" * 60)
            print(f"📈 Total Cards: {consolidation_analysis['totalCards']}")
            print(f"🎯 Unique Models: {consolidation_analysis['uniqueModels']}")
            print(f"🔁 Duplicates Found: {len(consolidation_analysis['duplicates'])}")
            
            if consolidation_analysis['duplicates']:
                print(f"\n❌ REMAINING DUPLICATES:")
                for dup in consolidation_analysis['duplicates']:
                    print(f"   - {dup['normalizedName']}: {dup['count']} instances")
                    for instance in dup['instances']:
                        print(f"     └─ Card {instance['cardIndex']}: '{instance['original']}'")
            else:
                print(f"\n✅ PERFECT CONSOLIDATION ACHIEVED!")
            
            # Specific problem model analysis
            if consolidation_analysis['llamaVariants']:
                print(f"\n🦙 LLAMA-3 VARIANTS ({len(consolidation_analysis['llamaVariants'])}):")
                for variant in consolidation_analysis['llamaVariants']:
                    print(f"   - Card {variant['cardIndex']}: '{variant['modelName']}'")
            
            if consolidation_analysis['glmVariants']:
                print(f"\n🤖 GLM-4 VARIANTS ({len(consolidation_analysis['glmVariants'])}):")
                for variant in consolidation_analysis['glmVariants']:
                    print(f"   - Card {variant['cardIndex']}: '{variant['modelName']}'")
            
            # Analyze normalization logs
            normalization_logs = [log for log in console_logs 
                                 if 'NORMALIZATION' in log or 'MODEL-CONSOLIDATION' in log]
            
            print(f"\n📝 NORMALIZATION LOGS ({len(normalization_logs)} entries):")
            for log in normalization_logs[-15:]:  # Last 15 normalization logs
                print(f"   {log}")
            
            # FINAL VERDICT
            print(f"\n🎉 ENHANCED CONSOLIDATION TEST RESULT:")
            print(f"=" * 60)
            
            if consolidation_analysis['enhancedSuccess']:
                print(f"✅ ENHANCED CONSOLIDATION: VOLLSTÄNDIG ERFOLGREICH!")
                print(f"   ✅ Perfect Model Consolidation: 0 Duplikate")
                print(f"   ✅ Enhanced Normalization funktioniert!")
                print(f"   ✅ 100% Duplicate-Free Ziel erreicht!")
            else:
                duplicates_count = len(consolidation_analysis['duplicates'])
                print(f"⚠️ ENHANCED CONSOLIDATION: TEILWEISE ERFOLGREICH")
                print(f"   📊 Verbleibende Duplikate: {duplicates_count}")
                print(f"   🔧 Enhanced Normalization braucht weitere Optimierung")
                
                # Suggest improvements for remaining duplicates
                if duplicates_count > 0:
                    print(f"\n🔧 VERBESSERUNGSVORSCHLÄGE:")
                    for dup in consolidation_analysis['duplicates']:
                        print(f"   - {dup['normalizedName']}: Analysiere Unterschiede zwischen {dup['count']} Instanzen")
            
            return {
                'enhanced_success': consolidation_analysis['enhancedSuccess'],
                'total_cards': consolidation_analysis['totalCards'],
                'unique_models': consolidation_analysis['uniqueModels'],
                'duplicates': consolidation_analysis['duplicates'],
                'normalization_logs': normalization_logs
            }
            
        except Exception as e:
            print(f"❌ Enhanced consolidation test error: {e}")
            import traceback
            traceback.print_exc()
            return None

# Main execution
if __name__ == "__main__":
    async def main():
        tester = EnhancedDuplicateFixTest()
        result = await tester.test_enhanced_consolidation()
        
        # Save enhanced results
        if result:
            with open('/app/tests/enhanced_consolidation_results.json', 'w') as f:
                json.dump(result, f, indent=2)
            
            print(f"\n💾 Enhanced results saved: /app/tests/enhanced_consolidation_results.json")
        
        print(f"\n📸 Enhanced screenshot: /app/tests/enhanced_consolidation_result.png")
    
    asyncio.run(main())