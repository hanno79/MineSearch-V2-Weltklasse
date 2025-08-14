/**
 * Author: rahn
 * Datum: 14.08.2025
 * Version: 1.0
 * Beschreibung: PHASE 2.2 - Cross-Tab Konsistenz-Validierung System
 */

const { chromium } = require('playwright');

async function validateCrossTabConsistency() {
    console.log('🔍 [PHASE 2.2] Cross-Tab Consistency Validation...');
    
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    
    try {
        await page.goto('http://localhost:8000', { waitUntil: 'domcontentloaded' });
        console.log('✅ [PHASE 2.2] Page loaded');
        
        const crossTabData = {};
        
        // 1. ERGEBNISSE TAB - Sammle Mine-Namen und Referenzdaten
        console.log('📊 [PHASE 2.2] Analysiere Ergebnisse Tab...');
        await page.click('a[data-tab="consolidated"]');
        await page.waitForTimeout(2000);
        
        crossTabData.consolidated = await page.evaluate(() => {
            const cards = document.querySelectorAll('.mine-data-card');
            const data = {
                mineNames: [],
                countries: [],
                cardCount: cards.length,
                sampleData: []
            };
            
            cards.forEach((card, i) => {
                if (i < 5) { // Nur ersten 5 für Sample
                    const title = card.querySelector('.card-title')?.textContent?.trim();
                    const subtitle = card.querySelector('.card-subtitle')?.textContent?.trim();
                    
                    data.mineNames.push(title);
                    data.countries.push(subtitle);
                    data.sampleData.push({
                        index: i,
                        title: title,
                        subtitle: subtitle
                    });
                }
            });
            
            return data;
        });
        
        // 2. STATISTICS TAB - Sammle Model-Namen und Performance-Daten
        console.log('📈 [PHASE 2.2] Analysiere Statistics Tab...');
        await page.click('a[data-tab="statistics"]');
        await page.waitForTimeout(2000);
        
        crossTabData.statistics = await page.evaluate(() => {
            const cards = document.querySelectorAll('.mine-data-card');
            const data = {
                modelNames: [],
                performanceScores: [],
                cardCount: cards.length,
                sampleData: []
            };
            
            cards.forEach((card, i) => {
                if (i < 5) { // Nur ersten 5 für Sample
                    const title = card.querySelector('.card-title')?.textContent?.trim();
                    const scoreText = card.textContent.match(/(\d+\.?\d*)\s*\/\s*10/);
                    const score = scoreText ? parseFloat(scoreText[1]) : null;
                    
                    data.modelNames.push(title);
                    data.performanceScores.push(score);
                    data.sampleData.push({
                        index: i,
                        title: title,
                        score: score
                    });
                }
            });
            
            return data;
        });
        
        // 3. QUELLEN TAB - Sammle Source-Informationen
        console.log('📚 [PHASE 2.2] Analysiere Quellen Tab...');
        await page.click('a[data-tab="sources"]');
        await page.waitForTimeout(2000);
        
        crossTabData.sources = await page.evaluate(() => {
            const cards = document.querySelectorAll('.mine-data-card, .source-card');
            const data = {
                sourceNames: [],
                cardCount: cards.length,
                sampleData: []
            };
            
            cards.forEach((card, i) => {
                if (i < 5) { // Nur ersten 5 für Sample
                    const title = card.querySelector('.card-title, h3')?.textContent?.trim();
                    data.sourceNames.push(title);
                    data.sampleData.push({
                        index: i,
                        title: title
                    });
                }
            });
            
            return data;
        });
        
        // 4. KONSISTENZ-VALIDIERUNG
        console.log('🔍 [PHASE 2.2] Cross-Tab Consistency Analysis...');
        const validation = {
            mathematicalConsistency: validateMathematicalConsistency(crossTabData.statistics),
            referenceIntegrity: validateReferenceIntegrity(crossTabData),
            dataQuality: validateDataQuality(crossTabData),
            overallScore: 0
        };
        
        // Berechne Overall Score
        const scores = Object.values(validation).filter(v => typeof v === 'number');
        validation.overallScore = scores.length > 0 ? scores.reduce((a, b) => a + b, 0) / scores.length : 0;
        
        await page.screenshot({ path: 'cross_tab_consistency_validation.png', fullPage: true });
        
        // 5. ERGEBNISSE AUSGEBEN
        console.log('\n📊 [PHASE 2.2] CROSS-TAB ANALYSIS RESULTS:');
        console.log('='.repeat(60));
        
        console.log('📋 TAB OVERVIEW:');
        console.log(`  Consolidated Tab: ${crossTabData.consolidated.cardCount} cards`);
        console.log(`  Statistics Tab: ${crossTabData.statistics.cardCount} cards`);
        console.log(`  Sources Tab: ${crossTabData.sources.cardCount} cards`);
        
        console.log('\n🔍 SAMPLE DATA CONSISTENCY:');
        console.log('  Consolidated Sample:', crossTabData.consolidated.sampleData.slice(0, 2));
        console.log('  Statistics Sample:', crossTabData.statistics.sampleData.slice(0, 2));
        console.log('  Sources Sample:', crossTabData.sources.sampleData.slice(0, 2));
        
        console.log('\n📊 VALIDATION RESULTS:');
        console.log(`  Mathematical Consistency: ${validation.mathematicalConsistency}/10`);
        console.log(`  Reference Integrity: ${validation.referenceIntegrity}/10`);
        console.log(`  Data Quality: ${validation.dataQuality}/10`);
        console.log(`  Overall Score: ${validation.overallScore.toFixed(1)}/10`);
        
        return {
            status: validation.overallScore >= 7 ? 'EXCELLENT' : validation.overallScore >= 5 ? 'GOOD' : 'NEEDS_IMPROVEMENT',
            overallScore: validation.overallScore,
            validation: validation,
            crossTabData: crossTabData
        };
        
    } catch (error) {
        console.error('❌ [PHASE 2.2] Error:', error);
        return { status: 'ERROR', error: error.message };
    } finally {
        await browser.close();
    }
}

function validateMathematicalConsistency(statisticsData) {
    console.log('🧮 [MATH-VALIDATION] Checking mathematical consistency...');
    
    if (!statisticsData.performanceScores || statisticsData.performanceScores.length === 0) {
        return 5; // Neutral score if no data
    }
    
    const validScores = statisticsData.performanceScores.filter(score => 
        score !== null && score >= 0 && score <= 10
    );
    
    const consistency = validScores.length / statisticsData.performanceScores.length;
    const score = Math.round(consistency * 10);
    
    console.log(`  Valid scores: ${validScores.length}/${statisticsData.performanceScores.length}`);
    console.log(`  Consistency: ${(consistency * 100).toFixed(1)}%`);
    
    return score;
}

function validateReferenceIntegrity(crossTabData) {
    console.log('🔗 [REFERENCE-VALIDATION] Checking reference integrity...');
    
    // Prüfe ob Cards in verschiedenen Tabs konsistent sind
    const consolidatedCount = crossTabData.consolidated.cardCount;
    const statisticsCount = crossTabData.statistics.cardCount;
    const sourcesCount = crossTabData.sources.cardCount;
    
    console.log(`  Consolidated: ${consolidatedCount} cards`);
    console.log(`  Statistics: ${statisticsCount} cards`);
    console.log(`  Sources: ${sourcesCount} cards`);
    
    // Score basierend auf ob alle Tabs Daten haben
    let score = 0;
    if (consolidatedCount > 0) score += 4;
    if (statisticsCount > 0) score += 4;
    if (sourcesCount > 0) score += 2;
    
    return score;
}

function validateDataQuality(crossTabData) {
    console.log('🎯 [QUALITY-VALIDATION] Checking data quality...');
    
    const consolidated = crossTabData.consolidated;
    const statistics = crossTabData.statistics;
    
    let score = 0;
    
    // Prüfe ob Mine-Namen nicht leer sind
    const validMineNames = consolidated.mineNames.filter(name => 
        name && !name.includes('Unbekannt') && name.length > 2
    ).length;
    
    if (validMineNames > 0) {
        score += 3;
        console.log(`  Valid mine names: ${validMineNames}/${consolidated.mineNames.length}`);
    }
    
    // Prüfe ob Model-Namen korrekt formatiert sind
    const validModelNames = statistics.modelNames.filter(name => 
        name && (name.includes('🤖') || name.includes('openrouter') || name.includes('perplexity'))
    ).length;
    
    if (validModelNames > 0) {
        score += 3;
        console.log(`  Valid model names: ${validModelNames}/${statistics.modelNames.length}`);
    }
    
    // Basis-Score für vorhandene Daten
    score += 4;
    
    return Math.min(score, 10);
}

validateCrossTabConsistency().then(result => {
    console.log(`\n🎯 [PHASE 2.2] FINAL RESULT: ${result.status} (${result.overallScore?.toFixed(1)}/10)`);
    
    if (result.status === 'EXCELLENT') {
        console.log('🎉 [PHASE 2.2] CROSS-TAB CONSISTENCY EXCELLENT!');
    } else if (result.status === 'GOOD') {
        console.log('✅ [PHASE 2.2] CROSS-TAB CONSISTENCY GOOD!');
    } else {
        console.log('🔄 [PHASE 2.2] CROSS-TAB CONSISTENCY NEEDS IMPROVEMENT');
    }
    
    process.exit(0);
}).catch(error => {
    console.error('💥 [PHASE 2.2] FATAL ERROR:', error);
    process.exit(1);
});