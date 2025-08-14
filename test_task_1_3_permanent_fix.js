/**
 * Author: rahn
 * Datum: 14.08.2025
 * Beschreibung: PHASE 2.1.2/2.1.3 - Test des neuen Source Attribution Systems
 */

const { chromium } = require('playwright');

async function testSourceAttributionFix() {
    console.log('🔍 [PHASE 2.1.2] Teste das neue Source Attribution Fallback-System...');
    
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    
    try {
        // Reduziere Timeout für schnelleren Test
        await page.goto('http://localhost:8000', { waitUntil: 'domcontentloaded', timeout: 10000 });
        console.log('✅ [PHASE 2.1.2] Page loaded');
        
        // Navigiere zum Ergebnisse-Tab
        await page.click('a[data-tab="consolidated"]');
        await page.waitForTimeout(2000);
        
        // Prüfe die ersten 3 Cards für Source-Attribution
        const sourceTest = await page.evaluate(() => {
            const cards = document.querySelectorAll('.mine-data-card');
            const results = [];
            
            for (let i = 0; i < Math.min(3, cards.length); i++) {
                const card = cards[i];
                const title = card.querySelector('.card-title')?.textContent?.trim();
                const sourceBadges = card.querySelectorAll('.source-badge');
                
                const badgeTexts = Array.from(sourceBadges).map(badge => badge.textContent?.trim());
                
                results.push({
                    cardIndex: i,
                    mineName: title,
                    sourceBadgeCount: sourceBadges.length,
                    sourceBadgeTexts: badgeTexts,
                    hasNoSourcesWarning: badgeTexts.some(text => text?.includes('Keine Quellen verfügbar')),
                    hasRealSources: badgeTexts.some(text => text?.includes('.gov') || text?.includes('.com') || text?.includes('.ca') || text?.includes('.gob.') || text?.includes('.org'))
                });
            }
            
            return results;
        });
        
        console.log('📊 [PHASE 2.1.2] SOURCE ATTRIBUTION TEST RESULTS:');
        console.log('='.repeat(50));
        
        let successCount = 0;
        sourceTest.forEach(result => {
            console.log(`Card ${result.cardIndex}: ${result.mineName}`);
            console.log(`  Badge Count: ${result.sourceBadgeCount}`);
            console.log(`  Badges: ${result.sourceBadgeTexts.join(', ')}`);
            console.log(`  No Sources Warning: ${result.hasNoSourcesWarning ? 'YES' : 'NO'}`);
            console.log(`  Real Sources: ${result.hasRealSources ? 'YES' : 'NO'}`);
            
            if (!result.hasNoSourcesWarning && result.hasRealSources) {
                successCount++;
                console.log('  ✅ STATUS: FIXED');
            } else {
                console.log('  ❌ STATUS: STILL BROKEN');
            }
            console.log('');
        });
        
        await page.screenshot({ path: 'task_1_3_permanent_fix_test.png', fullPage: true });
        
        const overallSuccess = successCount === sourceTest.length;
        console.log(`🎯 [PHASE 2.1.2] OVERALL RESULT: ${successCount}/${sourceTest.length} cards fixed`);
        
        return {
            status: overallSuccess ? 'SUCCESS' : 'PARTIAL_SUCCESS',
            fixedCards: successCount,
            totalCards: sourceTest.length,
            testResults: sourceTest
        };
        
    } catch (error) {
        console.error('❌ [PHASE 2.1.2] Error:', error);
        return { status: 'ERROR', error: error.message };
    } finally {
        await browser.close();
    }
}

testSourceAttributionFix().then(result => {
    if (result.status === 'SUCCESS') {
        console.log('🎉 [PHASE 2.1.2] SOURCE ATTRIBUTION COMPLETELY FIXED!');
    } else if (result.status === 'PARTIAL_SUCCESS') {
        console.log(`🔄 [PHASE 2.1.2] PARTIAL FIX: ${result.fixedCards}/${result.totalCards} cards now show sources`);
    } else {
        console.log('❌ [PHASE 2.1.2] FIX FAILED');
    }
    process.exit(0);
}).catch(error => {
    console.error('💥 [PHASE 2.1.2] FATAL ERROR:', error);
    process.exit(1);
});