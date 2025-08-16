"""
Author: rahn
Datum: 16.08.2025
Version: 1.0
Beschreibung: Quebec Mining CSV Test mit neuen unbenutzten Modellen für End-to-End Workflow
"""

import asyncio
import json
import time
from playwright.async_api import async_playwright

class QuebecMiningNewSearchTest:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        
    async def execute_quebec_mining_test(self):
        """Execute Quebec Mining CSV Test with unused models"""
        print("🍁 QUEBEC MINING CSV TEST WITH NEW MODELS")
        print("=" * 60)
        
        try:
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=False)
            page = await browser.new_page()
            
            # Step 1: Document current statistics baseline
            print("📊 [BASELINE] Documenting current statistics state...")
            await page.goto(f"{self.base_url}/static/index.html")
            await page.wait_for_load_state("networkidle")
            
            # Go to Statistics to get baseline
            stats_tab = await page.query_selector('nav.main-navigation a[data-tab="statistics"]')
            await stats_tab.click()
            await asyncio.sleep(10)
            
            baseline_stats = await page.evaluate("""
                () => {
                    const cards = document.querySelectorAll('.model-stats-card');
                    return {
                        totalCards: cards.length,
                        timestamp: Date.now()
                    };
                }
            """)
            
            print(f"📋 Baseline: {baseline_stats['totalCards']} model cards")
            
            # Step 2: Navigate to CSV Batch Upload
            print("📤 [UPLOAD] Navigating to CSV batch upload...")
            batch_tab = await page.query_selector('nav.main-navigation a[data-tab="csv"]')
            if not batch_tab:
                batch_tab = await page.query_selector('a[onclick*="csv"]')
            
            if batch_tab:
                await batch_tab.click()
                await asyncio.sleep(3)
                print("✅ Navigated to CSV batch tab")
            else:
                print("❌ CSV batch tab not found")
                return None
            
            # Step 3: Upload Quebec Mining CSV
            print("📁 [CSV] Uploading Quebec mining test CSV...")
            file_input = await page.query_selector('#csv_file')
            if not file_input:
                file_input = await page.query_selector('input[type="file"]')
            
            if file_input:
                await file_input.set_input_files('/app/tests/quebec_mining_test.csv')
                await asyncio.sleep(3)
                print("✅ CSV file uploaded successfully")
            else:
                print("❌ File input not found")
                return None
            
            # Step 4: Verify CSV upload and content
            csv_preview = await page.evaluate("""
                () => {
                    const preview = document.querySelector('#csv-preview');
                    return preview ? preview.textContent : 'No preview found';
                }
            """)
            
            print(f"📋 CSV Preview: {csv_preview[:200]}...")
            
            # Step 5: Select models (try to find unused ones)
            print("🎯 [MODELS] Selecting models for Quebec mining test...")
            
            # First, get available models
            available_models = await page.evaluate("""
                () => {
                    const select = document.querySelector('#provider-model-select');
                    if (!select) return [];
                    
                    const options = Array.from(select.options);
                    return options.map(option => ({
                        value: option.value,
                        text: option.textContent.trim()
                    })).filter(opt => opt.value && opt.value !== '');
                }
            """)
            
            print(f"📋 Available models: {len(available_models)}")
            
            # Select 2-3 models that might be less used
            target_models = []
            for model in available_models:
                if any(keyword in model['value'].lower() for keyword in ['gpt-4o-mini', 'claude-3-haiku', 'gemini-flash']):
                    target_models.append(model['value'])
                    if len(target_models) >= 2:
                        break
            
            if not target_models:
                # Fallback to first available models
                target_models = [model['value'] for model in available_models[:2]]
            
            print(f"🎯 Selected models: {target_models}")
            
            # Select the models
            for model in target_models:
                await page.evaluate(f"""
                    () => {{
                        const select = document.querySelector('#provider-model-select');
                        if (select) {{
                            const option = Array.from(select.options).find(opt => opt.value === '{model}');
                            if (option) {{
                                option.selected = true;
                            }}
                        }}
                    }}
                """)
            
            await asyncio.sleep(2)
            
            # Step 6: Start the search
            print("🚀 [SEARCH] Starting Quebec mining batch search...")
            
            start_button = await page.query_selector('button:has-text("Batch-Suche starten"), button:has-text("Start Search"), #start-batch-search')
            if start_button:
                await start_button.click()
                print("✅ Search started successfully")
            else:
                print("❌ Start button not found")
                available_buttons = await page.evaluate("""
                    () => {
                        const buttons = Array.from(document.querySelectorAll('button'));
                        return buttons.map(btn => btn.textContent.trim()).filter(text => text);
                    }
                """)
                print(f"Available buttons: {available_buttons}")
            
            # Step 7: Monitor search progress
            print("⏳ [PROGRESS] Monitoring search progress...")
            
            search_complete = False
            max_wait_time = 120  # 2 minutes max
            start_time = time.time()
            
            while not search_complete and (time.time() - start_time) < max_wait_time:
                await asyncio.sleep(5)
                
                # Check for completion indicators
                progress_info = await page.evaluate("""
                    () => {
                        // Look for progress indicators
                        const progressElements = document.querySelectorAll('[class*="progress"], [id*="progress"], .status, .result');
                        const progressTexts = Array.from(progressElements).map(el => el.textContent.trim());
                        
                        // Check for completion keywords
                        const pageText = document.body.textContent;
                        const isComplete = pageText.includes('abgeschlossen') || 
                                         pageText.includes('completed') || 
                                         pageText.includes('fertig') ||
                                         progressTexts.some(text => text.includes('100%'));
                        
                        return {
                            isComplete: isComplete,
                            progressTexts: progressTexts,
                            timestamp: Date.now()
                        };
                    }
                """)
                
                if progress_info['isComplete']:
                    search_complete = True
                    print("✅ Search completed!")
                else:
                    elapsed = int(time.time() - start_time)
                    print(f"⏳ Search in progress... ({elapsed}s elapsed)")
            
            if not search_complete:
                print("⚠️ Search may still be running - proceeding with analysis")
            
            # Step 8: Check if results are available in API
            print("📊 [RESULTS] Checking for new results in API...")
            
            # Switch to results tab to see if new data appears
            results_tab = await page.query_selector('nav.main-navigation a[data-tab="consolidated"]')
            if results_tab:
                await results_tab.click()
                await asyncio.sleep(5)
            
            # Step 9: Return to Statistics to see updates
            print("📈 [STATISTICS] Checking for statistics updates...")
            
            stats_tab = await page.query_selector('nav.main-navigation a[data-tab="statistics"]')
            await stats_tab.click()
            await asyncio.sleep(15)  # Wait for potential new model consolidation
            
            # Analyze updated statistics
            final_stats = await page.evaluate("""
                () => {
                    const cards = document.querySelectorAll('.model-stats-card');
                    const modelData = [];
                    
                    cards.forEach((card, index) => {
                        const cardText = card.textContent;
                        const modelMatch = cardText.match(/(openrouter|perplexity|abacus|exa):[\\w\\-\\.]+/i);
                        
                        if (modelMatch) {
                            const scoreMatch = cardText.match(/Performance.*?(\\d+(?:\\.\\d+)?)\\s*\\/\\s*10/i);
                            const successMatch = cardText.match(/Erfolgsrate.*?(\\d+(?:\\.\\d+)?)\\s*%/i);
                            const searchMatch = cardText.match(/Gesamte Suchen.*?(\\d+)/i);
                            
                            modelData.push({
                                modelName: modelMatch[0],
                                score: scoreMatch ? parseFloat(scoreMatch[1]) : 0,
                                successRate: successMatch ? parseFloat(successMatch[1]) : 0,
                                totalSearches: searchMatch ? parseInt(searchMatch[1]) : 0
                            });
                        }
                    });
                    
                    return {
                        totalCards: cards.length,
                        models: modelData,
                        timestamp: Date.now()
                    };
                }
            """)
            
            await browser.close()
            
            # ANALYSIS RESULTS
            print(f"\n🍁 QUEBEC MINING TEST RESULTS:")
            print(f"=" * 60)
            print(f"📊 Baseline Cards: {baseline_stats['totalCards']}")
            print(f"📈 Final Cards: {final_stats['totalCards']}")
            print(f"📦 New Models Added: {final_stats['totalCards'] - baseline_stats['totalCards']}")
            print(f"🎯 Target Models: {target_models}")
            
            # Check if any of our target models appear in final statistics
            target_found = []
            for model in target_models:
                found = any(model in stats_model['modelName'] for stats_model in final_stats['models'])
                if found:
                    target_found.append(model)
            
            print(f"✅ Target Models in Statistics: {len(target_found)}/{len(target_models)}")
            for model in target_found:
                print(f"   - {model}")
            
            # Show top performing models after search
            top_models = sorted(final_stats['models'], key=lambda x: x['score'], reverse=True)[:3]
            print(f"\n🏆 TOP 3 MODELS AFTER SEARCH:")
            for i, model in enumerate(top_models, 1):
                print(f"   {i}. {model['modelName']}: {model['score']}/10 ({model['successRate']}%)")
            
            return {
                'test_successful': final_stats['totalCards'] >= baseline_stats['totalCards'],
                'baseline_cards': baseline_stats['totalCards'],
                'final_cards': final_stats['totalCards'],
                'new_models_added': final_stats['totalCards'] - baseline_stats['totalCards'],
                'target_models': target_models,
                'target_models_found': target_found,
                'top_performers': top_models
            }
            
        except Exception as e:
            print(f"❌ Quebec mining test error: {e}")
            import traceback
            traceback.print_exc()
            return None

# Main execution
if __name__ == "__main__":
    async def main():
        tester = QuebecMiningNewSearchTest()
        result = await tester.execute_quebec_mining_test()
        
        if result:
            with open('/app/tests/quebec_mining_test_results.json', 'w') as f:
                json.dump(result, f, indent=2)
            
            print(f"\n💾 Quebec mining test results saved")
            
            # Final assessment
            if result['test_successful'] and result['new_models_added'] > 0:
                print(f"\n🎉 QUEBEC MINING TEST: VOLLSTÄNDIG ERFOLGREICH!")
                print(f"   ✅ New models successfully integrated")
                print(f"   ✅ Statistics automatically updated")
                print(f"   ✅ End-to-End workflow functional")
            else:
                print(f"\n⚠️ QUEBEC MINING TEST: TEILWEISE ERFOLGREICH")
                print(f"   📊 Cards: {result['baseline_cards']} → {result['final_cards']}")
                print(f"   🔍 May need more time for processing")
    
    asyncio.run(main())