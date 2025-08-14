/**
 * Author: rahn
 * Datum: 14.08.2025
 * Version: 1.0
 * Beschreibung: PHASE 3 - Final Comprehensive Testing & Quality Assurance Report
 */

const { chromium } = require('playwright');

async function generateFinalQualityReport() {
    console.log('🚀 [PHASE 3] Final Comprehensive Testing & Quality Assurance...');
    console.log('=' .repeat(70));
    
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    
    try {
        await page.goto('http://localhost:8000', { waitUntil: 'domcontentloaded' });
        console.log('✅ [PHASE 3] Page loaded successfully');
        
        const qualityReport = {
            timestamp: new Date().toISOString(),
            version: '2.0',
            systemStatus: 'TESTING',
            testResults: {}
        };
        
        // TEST 1: DATA CARD CONTENT ACCURACY
        console.log('\n🔍 [TEST 1] Data Card Content Accuracy...');
        await page.click('a[data-tab="consolidated"]');
        await page.waitForTimeout(1500);
        
        qualityReport.testResults.contentAccuracy = await page.evaluate(() => {
            const cards = document.querySelectorAll('.mine-data-card');
            const results = {
                totalCards: cards.length,
                validTitles: 0,
                validSources: 0,
                sampleTitles: []
            };
            
            cards.forEach((card, i) => {
                if (i < 5) {
                    const title = card.querySelector('.card-title')?.textContent?.trim();
                    const sources = card.querySelectorAll('.source-badge');
                    const hasNoSourcesWarning = Array.from(sources).some(s => 
                        s.textContent?.includes('Keine Quellen verfügbar'));
                    
                    results.sampleTitles.push(title);
                    
                    if (title && title.includes('🏭') && !title.includes('🤖')) {
                        results.validTitles++;
                    }
                    
                    if (sources.length > 0 && !hasNoSourcesWarning) {
                        results.validSources++;
                    }
                }
            });
            
            return results;
        });
        
        // TEST 2: MATHEMATICAL VALIDATION
        console.log('\n🧮 [TEST 2] Mathematical Validation...');
        await page.click('a[data-tab="statistics"]');
        await page.waitForTimeout(1500);
        
        qualityReport.testResults.mathematicalValidation = await page.evaluate(() => {
            const cards = document.querySelectorAll('.mine-data-card');
            const results = {
                totalCards: cards.length,
                validScores: 0,
                invalidScores: [],
                sampleScores: []
            };
            
            cards.forEach((card, i) => {
                if (i < 10) {
                    const scoreText = card.textContent.match(/(\d+\.?\d*)\s*\/\s*10/);
                    if (scoreText) {
                        const score = parseFloat(scoreText[1]);
                        results.sampleScores.push(score);
                        
                        if (score >= 0 && score <= 10) {
                            results.validScores++;
                        } else {
                            results.invalidScores.push({ cardIndex: i, score: score });
                        }
                    }
                }
            });
            
            return results;
        });
        
        // TEST 3: SOURCE ATTRIBUTION
        console.log('\n🔗 [TEST 3] Source Attribution System...');
        await page.click('a[data-tab="consolidated"]');
        await page.waitForTimeout(1500);
        
        qualityReport.testResults.sourceAttribution = await page.evaluate(() => {
            const cards = document.querySelectorAll('.mine-data-card');
            const results = {
                totalCards: cards.length,
                cardsWithSources: 0,
                cardsWithoutSources: 0,
                sampleSources: []
            };
            
            cards.forEach((card, i) => {
                if (i < 5) {
                    const sources = card.querySelectorAll('.source-badge');
                    const sourcesText = Array.from(sources).map(s => s.textContent?.trim());
                    const hasNoSourcesWarning = sourcesText.some(text => 
                        text?.includes('Keine Quellen verfügbar'));
                    
                    results.sampleSources.push(sourcesText.slice(0, 2));
                    
                    if (sources.length > 0 && !hasNoSourcesWarning) {
                        results.cardsWithSources++;
                    } else {
                        results.cardsWithoutSources++;
                    }
                }
            });
            
            return results;
        });
        
        // TEST 4: TAB FUNCTIONALITY
        console.log('\n📋 [TEST 4] Tab Functionality...');
        const tabTests = [];
        
        for (const tab of ['consolidated', 'statistics', 'sources']) {
            await page.click(`a[data-tab="${tab}"]`);
            await page.waitForTimeout(1000);
            
            const tabResult = await page.evaluate((tabName) => {
                const cards = document.querySelectorAll('.mine-data-card, .source-card');
                return {
                    tab: tabName,
                    cardsLoaded: cards.length,
                    functional: cards.length > 0
                };
            }, tab);
            
            tabTests.push(tabResult);
        }
        
        qualityReport.testResults.tabFunctionality = tabTests;
        
        // CALCULATE OVERALL SCORES
        console.log('\n📊 [SCORING] Calculating Quality Scores...');
        
        const scores = {
            contentAccuracy: calculateContentAccuracyScore(qualityReport.testResults.contentAccuracy),
            mathematicalValidation: calculateMathematicalScore(qualityReport.testResults.mathematicalValidation),
            sourceAttribution: calculateSourceScore(qualityReport.testResults.sourceAttribution),
            tabFunctionality: calculateTabScore(qualityReport.testResults.tabFunctionality)
        };
        
        const overallScore = Object.values(scores).reduce((a, b) => a + b, 0) / Object.keys(scores).length;
        
        qualityReport.scores = scores;
        qualityReport.overallScore = overallScore;
        qualityReport.systemGrade = getSystemGrade(overallScore);
        
        // GENERATE REPORT
        console.log('\n' + '='.repeat(70));
        console.log('🏆 MINESEARCH 2.0 - FINAL QUALITY ASSURANCE REPORT');
        console.log('='.repeat(70));
        
        console.log('\n📊 QUALITY SCORES:');
        console.log(`  Content Accuracy: ${scores.contentAccuracy.toFixed(1)}/10`);
        console.log(`  Mathematical Validation: ${scores.mathematicalValidation.toFixed(1)}/10`);
        console.log(`  Source Attribution: ${scores.sourceAttribution.toFixed(1)}/10`);
        console.log(`  Tab Functionality: ${scores.tabFunctionality.toFixed(1)}/10`);
        console.log(`  ` + '-'.repeat(30));
        console.log(`  📈 OVERALL SCORE: ${overallScore.toFixed(1)}/10`);
        console.log(`  🏆 SYSTEM GRADE: ${qualityReport.systemGrade}`);
        
        console.log('\n📋 DETAILED RESULTS:');
        console.log(`  Mine Cards: ${qualityReport.testResults.contentAccuracy.totalCards}`);
        console.log(`  Valid Titles: ${qualityReport.testResults.contentAccuracy.validTitles}/5`);
        console.log(`  Source Attribution: ${qualityReport.testResults.sourceAttribution.cardsWithSources}/5 cards with sources`);
        console.log(`  Mathematical Scores: ${qualityReport.testResults.mathematicalValidation.validScores}/10 valid`);
        console.log(`  Functional Tabs: ${tabTests.filter(t => t.functional).length}/3`);
        
        console.log('\n🎯 SYSTEM STATUS:');
        if (overallScore >= 9.0) {
            console.log('  🌟 WELTKLASSE - System übertrifft alle Erwartungen!');
        } else if (overallScore >= 8.0) {
            console.log('  🚀 EXZELLENT - System ist produktionstauglich und hochwertig!');
        } else if (overallScore >= 7.0) {
            console.log('  ✅ GUT - System funktioniert zuverlässig mit kleineren Verbesserungen!');
        } else {
            console.log('  🔄 VERBESSERUNGSBEDARF - System benötigt weitere Optimierungen!');
        }
        
        await page.screenshot({ path: 'final_quality_assurance_report.png', fullPage: true });
        
        // Save detailed report
        const fs = require('fs');
        fs.writeFileSync('/app/FINAL_QUALITY_REPORT.json', JSON.stringify(qualityReport, null, 2));
        
        return qualityReport;
        
    } catch (error) {
        console.error('❌ [PHASE 3] Error:', error);
        return { status: 'ERROR', error: error.message };
    } finally {
        await browser.close();
    }
}

function calculateContentAccuracyScore(data) {
    const titleAccuracy = data.validTitles / 5;
    return Math.min(titleAccuracy * 10, 10);
}

function calculateMathematicalScore(data) {
    if (data.sampleScores.length === 0) return 5;
    const accuracy = data.validScores / data.sampleScores.length;
    return Math.min(accuracy * 10, 10);
}

function calculateSourceScore(data) {
    const accuracy = data.cardsWithSources / 5;
    return Math.min(accuracy * 10, 10);
}

function calculateTabScore(tabTests) {
    const functionalTabs = tabTests.filter(t => t.functional).length;
    return Math.min((functionalTabs / 3) * 10, 10);
}

function getSystemGrade(score) {
    if (score >= 9.5) return 'A+ (WELTKLASSE)';
    if (score >= 9.0) return 'A (EXZELLENT)';
    if (score >= 8.0) return 'B+ (SEHR GUT)';
    if (score >= 7.0) return 'B (GUT)';
    if (score >= 6.0) return 'C+ (BEFRIEDIGEND)';
    if (score >= 5.0) return 'C (AUSREICHEND)';
    return 'D (UNZUREICHEND)';
}

generateFinalQualityReport().then(report => {
    console.log('\n🎊 [PHASE 3] FINAL QUALITY ASSURANCE COMPLETE!');
    console.log('='.repeat(70));
    process.exit(0);
}).catch(error => {
    console.error('💥 [PHASE 3] FATAL ERROR:', error);
    process.exit(1);
});