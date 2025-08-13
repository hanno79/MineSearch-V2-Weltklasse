/**
 * Author: rahn
 * Datum: 12.08.2025
 * Version: 1.0
 * Beschreibung: Einfacher Test für Statistics-Cards nach Fix
 */

const { chromium } = require('playwright');

async function simpleStatisticsTest() {
    console.log('🎭 [STATS-TEST] Starting Simple Statistics Test');
    
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext({ viewport: { width: 1200, height: 800 } });
    const page = await context.newPage();
    
    try {
        await page.goto('http://localhost:8000');
        await page.waitForLoadState('networkidle');
        
        // Reload to get new statistics-loader.js
        await page.reload({ waitUntil: 'networkidle' });
        
        // Navigate to Statistics Tab
        await page.click('label[for="statistics-tab"]');
        await page.waitForTimeout(2000);
        
        // Click load statistics
        console.log('🔄 Clicking loadStatistics button...');
        await page.click('button:has-text("Statistiken laden")');
        await page.waitForTimeout(8000);
        
        // Check results
        const result = await page.evaluate(() => {
            const container = document.getElementById('model-statistics-table-container');
            const modelCards = document.querySelectorAll('.model-stats-card');
            const sourceBadges = document.querySelectorAll('.source-badge');
            const noSourceMessages = Array.from(sourceBadges).filter(badge => 
                badge.textContent.includes('Keine Quellen')
            );
            
            return {
                containerHTML: container ? container.innerHTML.substring(0, 800) : 'Not found',
                modelCardsCount: modelCards.length,
                sourceBadgesCount: sourceBadges.length,
                noSourceMessagesCount: noSourceMessages.length,
                hasDataCardGrid: document.querySelector('.data-card-grid') ? true : false
            };
        });
        
        console.log('📊 STATISTICS TEST RESULTS:');
        console.log('Model cards found:', result.modelCardsCount);
        console.log('Source badges found:', result.sourceBadgesCount);
        console.log('No sources messages:', result.noSourceMessagesCount);
        console.log('Has data card grid:', result.hasDataCardGrid);
        console.log('Container preview:', result.containerHTML);
        
        await page.screenshot({ path: 'statistics_fixed_test.png' });
        console.log('📸 Screenshot saved');
        
        // Assessment
        const score = {
            cardsLoaded: result.modelCardsCount > 0 ? 40 : 0,
            sourcesFixed: result.noSourceMessagesCount === 0 && result.sourceBadgesCount > 0 ? 60 : 0
        };
        
        const total = score.cardsLoaded + score.sourcesFixed;
        console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
        console.log(`🏆 TOTAL SCORE: ${total}/100`);
        
        if (total >= 80) {
            console.log('✅ Statistics Cards erfolgreich repariert!');
        } else {
            console.log('⚠️ Weitere Reparaturen erforderlich');
        }
        
    } catch (error) {
        console.error('❌ Test failed:', error);
    } finally {
        await browser.close();
    }
}

// Run
simpleStatisticsTest().catch(console.error);