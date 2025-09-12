"""
Author: rahn
Datum: 16.08.2025
Version: 1.0
Beschreibung: Test für verbesserte Feldqualitäts-Berechnung
"""

import asyncio
import json
from playwright.async_api import async_playwright

class FieldQualityTest:
    def __init__(self):
    """__init__ - TODO: Dokumentation hinzufügen"""
        self.base_url = "http://localhost:8000"

    async def test_enhanced_field_quality(self):
        """Test die neue enhanced Feldqualitäts-Berechnung"""
        print("🧪 ENHANCED FIELD QUALITY TEST")
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

            # Test neue Feldqualitätsfunktion direkt
            test_result = await page.evaluate("""
                () => {
                    console.log('🔍 Testing Enhanced Field Quality Function...');

                    // Mock model data für verschiedene Qualitätsstufen
                    const testModels = [
                        // Hohe Qualität - gute Erfolgsrate
                        {
                            model_id: 'high-quality-model',
                            total_searches: 10,
                            successful_searches: 9,
                            success_rate: 0.9
                        },
                        // Mittlere Qualität - mittlere Erfolgsrate
                        {
                            model_id: 'medium-quality-model',
                            total_searches: 8,
                            successful_searches: 5,
                            success_rate: 0.625
                        },
                        // Niedrige Qualität - schlechte Erfolgsrate
                        {
                            model_id: 'low-quality-model',
                            total_searches: 5,
                            successful_searches: 1,
                            success_rate: 0.2
                        }
                    ];

                    const results = [];

                    // Test jedes Modell
                    testModels.forEach(modelData => {
                        if (typeof calculateFieldQuality !== 'undefined') {
                            const qualityResult = calculateFieldQuality(modelData);
                            results.push({
                                model_id: modelData.model_id,
                                score: qualityResult.score,
                                qualityLevel: qualityResult.qualityLevel,
                                percentage: qualityResult.details?.percentage,
                                realValues: qualityResult.details?.realValues,
                                totalFields: qualityResult.details?.totalFields,
                                qualityBreakdown: qualityResult.details?.qualityBreakdown,
                                description: qualityResult.description
                            });
                        }
                    });

                    console.log('Field Quality Test Results:', results);
                    return results;
                }
            """)

            await browser.close()

            print("📊 Enhanced Field Quality Results:")
            for result in test_result:
                print(f"\\n🤖 {result['model_id']}:")
                print(f"   Score: {result['score']:.1f}/10")
                print(f"   Quality Level: {result['qualityLevel']}")
                print(f"   Real Values: {result['realValues']}/{result['totalFields']} ({result['percentage']}%)")
                if result['qualityBreakdown']:
                    breakdown = result['qualityBreakdown']
                    print(f"   Breakdown: 🟢{breakdown['high']} hoch, 🟡{breakdown['medium']} mittel,
🔴{breakdown['low']} niedrig, ⚫{breakdown['empty']} leer")

            # Validate that scores are reasonable
            scores = [r['score'] for r in test_result]
            if len(scores) >= 3:
                high_score, medium_score, low_score = scores[0], scores[1], scores[2]
                quality_progression = high_score > medium_score > low_score
                print(f"\\n✅ Quality progression: {quality_progression} ({high_score:.1f} >
{medium_score:.1f} > {low_score:.1f})")
                return quality_progression

            return len(test_result) > 0

        except Exception as e:
            print(f"❌ Field quality test error: {e}")
            return False

    async def test_score_breakdown_display(self):
        """Test die erweiterte Score-Breakdown Anzeige"""
        print("\\n🧪 SCORE BREAKDOWN DISPLAY TEST")
        print("=" * 50)

        try:
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=False)
            page = await browser.new_page()

            await page.goto(f"{self.base_url}/static/index.html")
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(2)

            # Test Score Breakdown Funktion
            breakdown_result = await page.evaluate("""
                () => {
                    console.log('📊 Testing Enhanced Score Breakdown Display...');

                    // Mock model data mit enhanced breakdown
                    const mockModelData = {
                        model_id: 'test-breakdown-model',
                        score_breakdown: {
                            fieldQuality: {
                                score: 7.5,
                                qualityLevel: 'Hoch',
                                details: {
                                    percentage: '75.0',
                                    qualityBreakdown: {
                                        high: 45,
                                        medium: 30,
                                        low: 15,
                                        empty: 10
                                    }
                                }
                            },
                            consistency: {
                                score: 6.2,
                                details: {
                                    interpretation: 'Basiert auf 8 Suchläufen'
                                }
                            },
                            speed: {
                                score: 8.0,
                                details: {
                                    avgResponseTimeFormatted: '1.2s'
                                }
                            },
                            cost: {
                                score: 9.0,
                                details: {
                                    interpretation: 'Kostenlos'
                                }
                            }
                        }
                    };

                    if (typeof generateScoreBreakdown !== 'undefined') {
                        const breakdownHtml = generateScoreBreakdown(mockModelData);

                        // Check if it contains our enhanced field quality info
                        const hasQualityLevel = breakdownHtml.includes('Hoch');
                        const hasPercentage = breakdownHtml.includes('75.0%');
                        const hasQualityBreakdown = breakdownHtml.includes('🟢') &&
breakdownHtml.includes('🟡') && breakdownHtml.includes('🔴');

                        return {
                            hasBreakdown: breakdownHtml.length > 100,
                            hasQualityLevel: hasQualityLevel,
                            hasPercentage: hasPercentage,
                            hasQualityBreakdown: hasQualityBreakdown,
                            htmlLength: breakdownHtml.length
                        };
                    }

                    return { error: 'generateScoreBreakdown not available' };
                }
            """)

            await browser.close()

            print("📊 Score Breakdown Display Results:")
            print(f"   Has Breakdown: {breakdown_result.get("hasBreakdown", False)}")
            print(f"   Has Quality Level: {breakdown_result.get("hasQualityLevel", False)}")
            print(f"   Has Percentage: {breakdown_result.get("hasPercentage", False)}")
            print(f"   Has Quality Breakdown: {breakdown_result.get("hasQualityBreakdown", False)}")
            print(f"   HTML Length: {breakdown_result.get("htmlLength", 0)} chars")

            success = breakdown_result.get('hasBreakdown') and breakdown_result.get('hasQualityLevel')
            print(f"\\n✅ Breakdown display: {'PASSED' if success else 'FAILED'}")
            return success

        except Exception as e:
            print(f"❌ Breakdown display test error: {e}")
            return False

    async def run_field_quality_tests(self):
        """Run all field quality tests"""
        print("🚀 COMPREHENSIVE FIELD QUALITY TESTS")
        print("=" * 60)

        results = {}

        # Test 1: Enhanced Field Quality Calculation
        results['enhanced_calculation'] = await self.test_enhanced_field_quality()

        # Test 2: Score Breakdown Display
        results['breakdown_display'] = await self.test_score_breakdown_display()

        # Final Summary
        passed = sum(1 for result in results.values() if result is True)
        total = len(results)

        print(f"\\n📊 FIELD QUALITY TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Enhanced Calculation: {'PASSED' if results.get('enhanced_calculation') else 'FAILED'}")
        print(f"✅ Breakdown Display: {'PASSED' if results.get('breakdown_display') else 'FAILED'}")
        print(f"\\n🎯 TOTAL: {passed}/{total} tests passed")

        if passed == total:
            print("🎉 FIELD QUALITY ENHANCEMENT SUCCESSFUL!")
            print("✅ PHASE 1.4 erfolgreich abgeschlossen!")
        else:
            print("⚠️ Some field quality issues detected")

        return results

# Main execution
if __name__ == "__main__":
    async def main():
        tester = FieldQualityTest()
        results = await tester.run_field_quality_tests()

        # Save results
        with open('/app/tests/field_quality_results.json', 'w') as f:
            json.dump(results, f, indent=2)

        print(f"\\n💾 Results saved: /app/tests/field_quality_results.json")

    asyncio.run(main())
