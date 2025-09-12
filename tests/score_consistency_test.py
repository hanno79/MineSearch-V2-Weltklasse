"""
Author: rahn
Datum: 16.08.2025
Version: 1.0
Beschreibung: Test für Score-Konsistenz - Behebt Problem mit 10/10 Score bei 0% Erfolgsrate
"""

import asyncio
import json
from playwright.async_api import async_playwright

class ScoreConsistencyTest:
    def __init__(self):
    """__init__ - TODO: Dokumentation hinzufügen"""
        self.base_url = "http://localhost:8000"

    async def test_score_consistency_validation(self):
        """Test die mathematische Konsistenz der Scores"""
        print("🧪 SCORE CONSISTENCY VALIDATION TEST")
        print("=" * 50)

        try:
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=False)
            page = await browser.new_page()

            await page.goto(f"{self.base_url}/static/index.html")
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(2)

            # Test verschiedene Score-Szenarien direkt
            consistency_result = await page.evaluate("""
                () => {
                    console.log('🧮 Testing score consistency scenarios...');

                    if (typeof calculateAdvancedPerformanceScore === 'undefined') {
                        return { error: 'calculateAdvancedPerformanceScore function not available' };
                    }

                    const testScenarios = [
                        // Scenario 1: 0% Erfolgsrate - sollte niedrigen Score haben
                        {
                            name: 'Zero Success Rate',
                            model_id: 'test:zero-success',
                            total_searches: 5,
                            successful_searches: 0,
                            success_rate: 0.0
                        },
                        // Scenario 2: 100% Erfolgsrate - sollte hohen Score haben
                        {
                            name: 'Perfect Success Rate',
                            model_id: 'test:perfect',
                            total_searches: 10,
                            successful_searches: 10,
                            success_rate: 1.0
                        },
                        // Scenario 3: 50% Erfolgsrate - sollte mittleren Score haben
                        {
                            name: 'Medium Success Rate',
                            model_id: 'test:medium',
                            total_searches: 8,
                            successful_searches: 4,
                            success_rate: 0.5
                        }
                    ];

                    const results = [];

                    testScenarios.forEach(scenario => {
                        const scoreResult = calculateAdvancedPerformanceScore(scenario);

                        // Prüfe mathematische Konsistenz
                        const isConsistent = (
                            (scenario.success_rate === 0.0 && scoreResult.totalScore <= 3.0) ||
                            (scenario.success_rate === 1.0 && scoreResult.totalScore >= 7.0) ||
                            (scenario.success_rate > 0.0 && scenario.success_rate < 1.0 &&
scoreResult.totalScore > 0.0 && scoreResult.totalScore < 10.0)
                        );

                        results.push({
                            scenario: scenario.name,
                            successRate: scenario.success_rate,
                            totalScore: scoreResult.totalScore,
                            isConsistent: isConsistent,
                            fieldQualityScore: scoreResult.breakdown?.fieldQuality?.score || 0,
                            consistencyScore: scoreResult.breakdown?.consistency?.score || 0,
                            speedScore: scoreResult.breakdown?.speed?.score || 0,
                            costScore: scoreResult.breakdown?.cost?.score || 0
                        });

                        console.log(`📊 ${scenario.name}: Success=${scenario.success_rate*100}%,
Score=${scoreResult.totalScore.toFixed(1)}, Consistent=${isConsistent}`);
                    });

                    const allConsistent = results.every(r => r.isConsistent);

                    return {
                        success: true,
                        results: results,
                        allConsistent: allConsistent,
                        inconsistentCount: results.filter(r => !r.isConsistent).length
                    };
                }
            """)

            await browser.close()

            print("📊 Score consistency results:")
            if consistency_result.get('error'):
                print(f"   ❌ Error: {consistency_result['error']}")
                return False
            else:
                print(f"   ✅ Success: {consistency_result['success']}")
                print(f"   📈 All consistent: {consistency_result['allConsistent']}")
                print(f"   ⚠️ Inconsistent count: {consistency_result['inconsistentCount']}")

                print("\\n📋 Detailed results:")
                for result in consistency_result['results']:
                    status = "✅" if result['isConsistent'] else "❌"
                    print(f"   {status} {result['scenario']}: {result['successRate']*100}% →
{result['totalScore']:.1f}/10")
                    print(f"      Components: Field={result['fieldQualityScore']:.1f},
Consistency={result['consistencyScore']:.1f}, Speed={result['speedScore']:.1f},
Cost={result['costScore']:.1f}")

                return consistency_result['allConsistent']

        except Exception as e:
            print(f"❌ Score consistency test error: {e}")
            return False

    async def test_statistics_tab_consistency(self):
        """Test Konsistenz in Statistics Tab mit echten Daten"""
        print("\\n🧪 STATISTICS TAB CONSISTENCY TEST")
        print("=" * 50)

        try:
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=False)
            page = await browser.new_page()

            await page.goto(f"{self.base_url}/static/index.html")
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(2)

            # Go to Statistics tab
            await page.click('header nav a[href="#statistics"]')
            await asyncio.sleep(8)  # Wait for statistics to load with new scoring

            # Check for consistency issues in model cards
            consistency_check = await page.evaluate("""
                () => {
                    console.log('🔍 Checking statistics tab for score inconsistencies...');

                    const modelCards = document.querySelectorAll('.model-stats-card');
                    const inconsistencies = [];
                    const validCards = [];

                    modelCards.forEach((card, index) => {
                        try {
                            // Extract model name
                            const nameElement = card.querySelector('.card-title, .data-row .data-value');
                            const modelName = nameElement ? nameElement.textContent.trim() : `Model ${index + 1}`;

                            // Extract score
                            const scoreElement = card.querySelector('.performance-score');
                            const scoreText = scoreElement ? scoreElement.textContent.trim() : '';
                            const scoreMatch = scoreText.match(/([0-9.]+)\/10/);
                            const score = scoreMatch ? parseFloat(scoreMatch[1]) : null;

                            // Extract success rate
                            const successElements = card.querySelectorAll('.data-row');
                            let successRate = null;

                            successElements.forEach(row => {
                                const label = row.querySelector('.data-label');
                                const value = row.querySelector('.data-value');
                                if (label && value && label.textContent.includes('Erfolgsrate')) {
                                    const rateText = value.textContent.trim();
                                    const rateMatch = rateText.match(/([0-9.]+)%/);
                                    successRate = rateMatch ? parseFloat(rateMatch[1]) : null;
                                }
                            });

                            if (score !== null && successRate !== null) {
                                validCards.push({ modelName, score, successRate });

                                // Check for impossible combinations
                                if (score >= 9.0 && successRate === 0.0) {
                                    inconsistencies.push({
                                        modelName: modelName,
                                        score: score,
                                        successRate: successRate,
                                        issue: 'High score with 0% success rate'
                                    });
                                    console.log(`⚠️ INCONSISTENCY: ${modelName} has score
${score}/10 but 0% success rate`);
                                } else if (score === 0.0 && successRate > 80.0) {
                                    inconsistencies.push({
                                        modelName: modelName,
                                        score: score,
                                        successRate: successRate,
                                        issue: 'Zero score with high success rate'
                                    });
                                    console.log(`⚠️ INCONSISTENCY: ${modelName} has 0/10 score but
${successRate}% success rate`);
                                } else {
                                    console.log(`✅ CONSISTENT: ${modelName} - Score: ${score}/10,
Success: ${successRate}%`);
                                }
                            }
                        } catch (error) {
                            console.log(`❌ Error analyzing card ${index}: ${error.message}`);
                        }
                    });

                    return {
                        totalCards: modelCards.length,
                        validCards: validCards.length,
                        inconsistencies: inconsistencies,
                        inconsistencyCount: inconsistencies.length
                    };
                }
            """)

            await browser.close()

            print("📊 Statistics tab consistency results:")
            print(f"   📋 Total cards: {consistency_check['totalCards']}")
            print(f"   ✅ Valid cards analyzed: {consistency_check['validCards']}")
            print(f"   ⚠️ Inconsistencies found: {consistency_check['inconsistencyCount']}")

            if consistency_check['inconsistencies']:
                print("\\n🔍 Found inconsistencies:")
                for issue in consistency_check['inconsistencies']:
                    print(f"   ❌ {issue['modelName']}: Score {issue['score']}/10, Success
{issue['successRate']}% - {issue['issue']}")
            else:
                print("\\n✅ No inconsistencies found in statistics tab!")

            return consistency_check['inconsistencyCount'] == 0

        except Exception as e:
            print(f"❌ Statistics consistency test error: {e}")
            return False

    async def test_enhanced_field_quality_scoring(self):
        """Test die Enhanced Field Quality Scoring für bessere Konsistenz"""
        print("\\n🧪 ENHANCED FIELD QUALITY SCORING TEST")
        print("=" * 50)

        try:
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=False)
            page = await browser.new_page()

            await page.goto(f"{self.base_url}/static/index.html")
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(2)

            # Test enhanced field quality function
            quality_test = await page.evaluate("""
                () => {
                    console.log('🔍 Testing enhanced field quality scoring...');

                    if (typeof calculateFieldQuality === 'undefined') {
                        return { error: 'calculateFieldQuality function not available' };
                    }

                    const testCases = [
                        // Case 1: Model mit 0% Erfolgsrate
                        {
                            name: 'Zero Success Model',
                            model_id: 'test:zero',
                            total_searches: 5,
                            successful_searches: 0,
                            success_rate: 0.0
                        },
                        // Case 2: Model mit hoher Erfolgsrate
                        {
                            name: 'High Success Model',
                            model_id: 'test:high',
                            total_searches: 10,
                            successful_searches: 9,
                            success_rate: 0.9
                        }
                    ];

                    const results = [];

                    testCases.forEach(testCase => {
                        const qualityResult = calculateFieldQuality(testCase);

                        results.push({
                            name: testCase.name,
                            successRate: testCase.success_rate,
                            qualityScore: qualityResult.score,
                            qualityLevel: qualityResult.qualityLevel,
                            realValues: qualityResult.details?.realValues || 0,
                            totalFields: qualityResult.details?.totalFields || 0,
                            isLogical: (
                                (testCase.success_rate === 0.0 && qualityResult.score <= 2.0) ||
                                (testCase.success_rate >= 0.8 && qualityResult.score >= 6.0)
                            )
                        });

                        console.log(`📊 ${testCase.name}: Success=${testCase.success_rate*100}%,
Quality=${qualityResult.score.toFixed(1)}, Level=${qualityResult.qualityLevel}`);
                    });

                    const allLogical = results.every(r => r.isLogical);

                    return {
                        success: true,
                        results: results,
                        allLogical: allLogical
                    };
                }
            """)

            await browser.close()

            print("📊 Enhanced field quality results:")
            if quality_test.get('error'):
                print(f"   ❌ Error: {quality_test['error']}")
                return False
            else:
                print(f"   ✅ Success: {quality_test['success']}")
                print(f"   🧠 All logical: {quality_test['allLogical']}")

                print("\\n📋 Quality scoring results:")
                for result in quality_test['results']:
                    status = "✅" if result['isLogical'] else "❌"
                    print(f"   {status} {result['name']}: {result['successRate']*100}% →
Quality={result['qualityScore']:.1f} ({result['qualityLevel']})")

                return quality_test['allLogical']

        except Exception as e:
            print(f"❌ Enhanced quality test error: {e}")
            return False

    async def run_score_consistency_tests(self):
        """Run all score consistency tests"""
        print("🚀 COMPREHENSIVE SCORE CONSISTENCY TESTS")
        print("=" * 60)

        results = {}

        # Test 1: Score Consistency Validation
        results['score_validation'] = await self.test_score_consistency_validation()

        # Test 2: Statistics Tab Consistency
        results['statistics_consistency'] = await self.test_statistics_tab_consistency()

        # Test 3: Enhanced Field Quality Scoring
        results['quality_scoring'] = await self.test_enhanced_field_quality_scoring()

        # Final Summary
        passed = sum(1 for result in results.values() if result is True)
        total = len(results)

        print(f"\\n📊 SCORE CONSISTENCY TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Score Validation: {'PASSED' if results.get('score_validation') else 'FAILED'}")
        print(f"✅ Statistics Consistency: {'PASSED' if results.get('statistics_consistency') else 'FAILED'}")
        print(f"✅ Quality Scoring: {'PASSED' if results.get('quality_scoring') else 'FAILED'}")
        print(f"\\n🎯 TOTAL: {passed}/{total} tests passed")

        if passed == total:
            print("🎉 SCORE CONSISTENCY FULLY RESOLVED!")
            print("✅ PHASE 3.1 erfolgreich abgeschlossen!")
            print("🏆 10/10 + 0% Erfolgsrate Problem wurde behoben!")
        elif passed >= 2:
            print("🟡 SCORE CONSISTENCY MOSTLY FIXED!")
            print("✅ PHASE 3.1 weitgehend erfolgreich!")
        else:
            print("⚠️ Score consistency needs further improvements")

        return results

# Main execution
if __name__ == "__main__":
    async def main():
        tester = ScoreConsistencyTest()
        results = await tester.run_score_consistency_tests()

        # Save results
        with open('/app/tests/score_consistency_results.json', 'w') as f:
            json.dump(results, f, indent=2)

        print(f"\\n💾 Results saved: /app/tests/score_consistency_results.json")

    asyncio.run(main())
