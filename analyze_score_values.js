/**
 * Author: rahn
 * Datum: 14.08.2025
 * Beschreibung: Analysiere Score-Werte und Mathematical Validation (PHASE 1.2)
 */

const { chromium } = require('playwright');

async function analyzeScoreValues() {
    console.log('🔍 [PHASE 1.2] Analysiere Score-Werte und Mathematical Validation...');
    
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    
    try {
        await page.goto('http://localhost:8000', { waitUntil: 'networkidle' });
        console.log('✅ [PHASE 1.2] Page loaded');
        
        // TEST Statistics Tab für Score-Probleme
        console.log('📈 [PHASE 1.2] Analysiere Statistics Tab für mathematische Probleme...');
        await page.click('a[data-tab="statistics"]');
        await page.waitForTimeout(3000);
        
        const statisticsScores = await page.evaluate(() => {
            const cards = document.querySelectorAll('.mine-data-card');
            const scores = [];
            const problematicScores = [];
            
            cards.forEach((card, i) => {
                const title = card.querySelector('.card-title')?.textContent?.trim();
                
                // Suche nach Score-Elementen
                const allText = card.textContent || '';
                const scoreMatches = allText.match(/(\d+\.?\d*)\s*\/\s*(\d+)/g) || [];
                
                scoreMatches.forEach(match => {
                    const [value, max] = match.split('/').map(s => parseFloat(s.trim()));
                    scores.push({
                        cardIndex: i,
                        cardTitle: title,
                        scoreText: match,
                        value: value,
                        maximum: max,
                        isProblematic: value > max
                    });
                    
                    if (value > max) {
                        problematicScores.push({
                            cardTitle: title,
                            scoreText: match,
                            value: value,
                            maximum: max
                        });
                    }
                });
                
                // Suche auch nach Prozentsätzen über 100%
                const percentMatches = allText.match(/(\d+\.?\d*)\s*%/g) || [];
                percentMatches.forEach(match => {
                    const value = parseFloat(match.replace('%', ''));
                    if (value > 100) {
                        problematicScores.push({
                            cardTitle: title,
                            scoreText: match,
                            value: value,
                            maximum: 100,
                            type: 'percentage'
                        });
                    }
                });
            });
            
            return { scores, problematicScores };
        });
        
        console.log('📊 [PHASE 1.2] STATISTICS-TAB ANALYSE:');
        console.log(`  Cards analysiert: ${await page.$$eval('.mine-data-card', cards => cards.length)}`);
        console.log(`  Scores gefunden: ${statisticsScores.scores.length}`);
        console.log(`  Problematische Scores: ${statisticsScores.problematicScores.length}`);
        
        if (statisticsScores.problematicScores.length > 0) {
            console.log('🚨 [PHASE 1.2] MATHEMATISCH UNMÖGLICHE WERTE GEFUNDEN:');
            statisticsScores.problematicScores.forEach((score, i) => {
                console.log(`  [${i+1}] "${score.cardTitle}": ${score.scoreText} (${score.value} > ${score.maximum})`);
            });
            
            return {
                status: 'MATHEMATICAL_PROBLEMS_FOUND',
                problematicScores: statisticsScores.problematicScores,
                totalScores: statisticsScores.scores.length
            };
        } else {
            console.log('✅ [PHASE 1.2] Alle Scores sind mathematisch korrekt');
            return {
                status: 'OK',
                totalScores: statisticsScores.scores.length
            };
        }
        
    } catch (error) {
        console.error('❌ [PHASE 1.2] Error:', error);
        return { status: 'ERROR', error: error.message };
    } finally {
        await browser.close();
    }
}

analyzeScoreValues().then(result => {
    console.log('🎯 [PHASE 1.2] FINAL RESULT:', JSON.stringify(result, null, 2));
    process.exit(0);
}).catch(error => {
    console.error('💥 [PHASE 1.2] FATAL ERROR:', error);
    process.exit(1);
});