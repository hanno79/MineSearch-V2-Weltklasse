"""
Author: rahn
Datum: 16.08.2025
Version: 1.0
Beschreibung: Comprehensive End-to-End System Validation mit Multi-Agent Claude-Flow
"""

import asyncio
import json
import time
from playwright.async_api import async_playwright

class ComprehensiveE2EValidation:
    def __init__(self):
    """__init__ - TODO: Dokumentation hinzufügen"""
        self.base_url = "http://localhost:8000"

    async def baseline_system_analysis(self):
        """PHASE 1: Baseline System State Documentation"""
        print("🔍 PHASE 1: BASELINE SYSTEM ANALYSIS")
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
            await page.goto(f"{self.base_url}/static/index.html?cache_bust={int(time.time())}")
            await page.wait_for_load_state("networkidle")

            # Navigate to Statistics Tab
            print("📍 [STATISTICS] Loading Statistics Tab...")
            stats_tab = await page.query_selector('nav.main-navigation a[data-tab="statistics"]')
            if not stats_tab:
                stats_tab = await page.query_selector('a[onclick*="statistics"]')

            await stats_tab.click()
            await asyncio.sleep(10)  # Wait for model consolidation

            # Analyze current model selection dropdown
            print("📋 [MODEL-SELECTION] Analyzing available models...")
            await page.goto(f"{self.base_url}/static/index.html")
            await page.wait_for_load_state("networkidle")

            # Get available models from dropdown
            model_dropdown_analysis = await page.evaluate("""
                () => {
                    const modelSelects = document.querySelectorAll('#provider-model-select option');
                    const availableModels = [];

                    modelSelects.forEach(option => {
                        if (option.value && option.value !== '') {
                            availableModels.push({
                                value: option.value,
                                text: option.textContent.trim()
                            });
                        }
                    });

                    return {
                        totalModels: availableModels.length,
                        models: availableModels
                    };
                }
            """)

            # Go back to Statistics for consolidation analysis
            await page.goto(f"{self.base_url}/static/index.html")
            stats_tab = await page.query_selector('nav.main-navigation a[data-tab="statistics"]')
            await stats_tab.click()
            await asyncio.sleep(15)  # Wait for full loading

            # Analyze current statistics state
            statistics_analysis = await page.evaluate("""
                () => {
                    const modelCards = document.querySelectorAll('.mine-data-card.model-stats-card, .model-stats-card');
                    const modelData = [];
                    const modelCounts = {};

                    modelCards.forEach((card, index) => {
                        const cardText = card.textContent;

                        // Extract model name
                        const modelMatch = cardText.match(/(openrouter|perplexity|abacus|exa):[\\w-]+/i);
                        if (!modelMatch) return;

                        const modelName = modelMatch[0];

                        // Count occurrences for duplicate detection
                        if (!modelCounts[modelName]) {
                            modelCounts[modelName] = 0;
                        }
                        modelCounts[modelName]++;

                        // Extract performance metrics
                        const scoreMatch = cardText.match(/Performance.*?(\\d+(?:\\.\\d+)?)\\s*\\/\\s*10/i);
                        const successMatch = cardText.match(/Erfolgsrate.*?(\\d+(?:\\.\\d+)?)\\s*%/i);
                        const searchMatch = cardText.match(/Gesamte Suchen.*?(\\d+)/i);

                        modelData.push({
                            index: index + 1,
                            modelName: modelName,
                            score: scoreMatch ? parseFloat(scoreMatch[1]) : 0,
                            successRate: successMatch ? parseFloat(successMatch[1]) : 0,
                            totalSearches: searchMatch ? parseInt(searchMatch[1]) : 0
                        });
                    });

                    // Find duplicates
                    const duplicates = [];
                    Object.entries(modelCounts).forEach(([modelName, count]) => {
                        if (count > 1) {
                            duplicates.push({ modelName, count });
                        }
                    });

                    // Find top 3 performers
                    const topPerformers = [...modelData]
                        .filter(m => m.successRate > 0)  // Only successful models
                        .sort((a, b) => b.score - a.score)
                        .slice(0, 3);

                    return {
                        totalCards: modelCards.length,
                        uniqueModels: Object.keys(modelCounts).length,
                        duplicates: duplicates,
                        topPerformers: topPerformers,
                        allModels: modelData
                    };
                }
            """)

            await browser.close()

            # BASELINE ANALYSIS RESULTS
            print(f"\n📊 BASELINE SYSTEM STATE:")
            print(f"=" * 60)
            print(f"📋 Available Models in Dropdown: {model_dropdown_analysis['totalModels']}")
            print(f"📈 Statistics Cards: {statistics_analysis['totalCards']}")
            print(f"🎯 Unique Models: {statistics_analysis['uniqueModels']}")
            print(f"🔁 Duplicates: {len(statistics_analysis['duplicates'])}")

            if statistics_analysis['duplicates']:
                print(f"\n❌ DUPLICATE MODELS DETECTED:")
                for dup in statistics_analysis['duplicates']:
                    print(f"   - {dup['modelName']}: {dup['count']} cards")

            print(f"\n🏆 TOP 3 PERFORMING MODELS:")
            for i, model in enumerate(statistics_analysis['topPerformers'], 1):
                print(f"   {i}. {model['modelName']}: {model['score']}/10 ({model['successRate']}% success)")

            # Identify unused models
            used_models = {model['modelName'] for model in statistics_analysis['allModels']}
            available_models = {model['value'] for model in model_dropdown_analysis['models']}
            unused_models = available_models - used_models

            print(f"\n🆕 UNUSED MODELS FOR TESTING ({len(unused_models)}):")
            for model in list(unused_models)[:5]:  # Show first 5
                print(f"   - {model}")

            return {
                'baseline_timestamp': time.time(),
                'model_dropdown': model_dropdown_analysis,
                'statistics_state': statistics_analysis,
                'unused_models': list(unused_models),
                'console_logs': console_logs[-20:]  # Last 20 logs
            }

        except Exception as e:
            print(f"❌ Baseline analysis error: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def automatic_model_selection_analysis(self):
        """PHASE 2: Automatic Model Selection Mechanism Analysis"""
        print("\n🤖 PHASE 2: AUTOMATIC MODEL SELECTION ANALYSIS")
        print("=" * 60)

        try:
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=False)
            page = await browser.new_page()

            print("📍 [NAVIGATION] Loading search page...")
            await page.goto(f"{self.base_url}/static/index.html")
            await page.wait_for_load_state("networkidle")

            # Check current top-3 selection in model dropdown
            current_selection = await page.evaluate("""
                () => {
                    const quickPresets = document.querySelectorAll('.quick-preset');
                    const selections = [];

                    quickPresets.forEach(preset => {
                        const text = preset.textContent.trim();
                        if (text.includes('Beste 3')) {
                            // Click to see what models are selected
                            preset.click();

                            setTimeout(() => {
                                const selectedOptions =
document.querySelectorAll('#provider-model-select option:checked');
                                selectedOptions.forEach(option => {
                                    if (option.value) {
                                        selections.push(option.value);
                                    }
                                });
                            }, 1000);
                        }
                    });

                    return selections;
                }
            """)

            # Also check what models are currently selected by default
            await asyncio.sleep(2)
            default_selection = await page.evaluate("""
                () => {
                    const select = document.querySelector('#provider-model-select');
                    const selectedOptions = Array.from(select.selectedOptions);
                    return selectedOptions.map(option => option.value).filter(v => v);
                }
            """)

            await browser.close()

            print(f"🎯 Current Top-3 Auto-Selection: {current_selection}")
            print(f"📋 Default Selected Models: {default_selection}")

            return {
                'current_top3': current_selection,
                'default_selection': default_selection
            }

        except Exception as e:
            print(f"❌ Model selection analysis error: {e}")
            return None

# Main execution
if __name__ == "__main__":
    async def main():
        validator = ComprehensiveE2EValidation()

        print("🚀 COMPREHENSIVE END-TO-END VALIDATION STARTING")
        print("=" * 80)

        # Phase 1: Baseline Analysis
        baseline_results = await validator.baseline_system_analysis()

        # Phase 2: Model Selection Analysis
        selection_results = await validator.automatic_model_selection_analysis()

        # Save comprehensive results
        if baseline_results and selection_results:
            comprehensive_results = {
                'validation_timestamp': time.time(),
                'baseline_analysis': baseline_results,
                'model_selection_analysis': selection_results
            }

            with open('/app/tests/comprehensive_e2e_results.json', 'w') as f:
                json.dump(comprehensive_results, f, indent=2)

            print(f"\n💾 Comprehensive results saved: /app/tests/comprehensive_e2e_results.json")

        print(f"\n🎉 PHASE 1 & 2 VALIDATION COMPLETE!")

    asyncio.run(main())
