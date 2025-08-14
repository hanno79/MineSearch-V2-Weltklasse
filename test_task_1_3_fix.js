/**
 * TASK 1.3 Fix Test: Permanent Fix für Data Card Logic
 * Author: rahn
 * Datum: 14.08.2025
 */

const { chromium } = require('playwright');

async function testTask13Fix() {
    console.log('🔧 [TASK-1.3] Testing permanent fix for data card logic...');
    
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    
    // Monitor console for debug messages
    page.on('console', msg => {
        const text = msg.text();
        if (text.includes('[INIT]') || text.includes('[CONSOLIDATED]') || text.includes('[STATISTICS]')) {
            console.log(`🌐 [BROWSER] ${text}`);
        }
    });
    
    await page.goto('http://localhost:8000');
    await page.waitForTimeout(2000);
    
    console.log('🧪 [TEST] Phase 1: Page loads with default tab - should NOT auto-load statistics');
    await page.waitForTimeout(2000);
    
    // Check default tab
    const defaultTab = await page.evaluate(() => {
        const activeTab = document.querySelector('input[name="tab"]:checked');
        return activeTab ? activeTab.value : 'none';
    });
    console.log(`📊 [TEST] Default active tab: ${defaultTab}`);
    
    // Navigate to consolidated tab
    console.log('🧪 [TEST] Phase 2: Navigate to consolidated tab...');
    await page.click('a[data-tab="consolidated"]');
    await page.waitForTimeout(6000); // Wait longer for data loading
    
    // Check results after fix
    const results = await page.evaluate(() => {
        const cards = document.querySelectorAll('#consolidated-table-container .mine-data-card');
        const firstTitle = cards.length > 0 ? cards[0].querySelector('.card-title')?.textContent?.trim() : null;
        
        // Check for model container contamination
        const modelStatsCards = document.querySelectorAll('#model-statistics-table-container .mine-data-card');
        
        return {
            consolidatedCards: cards.length,
            firstTitle: firstTitle,
            modelStatsCards: modelStatsCards.length,
            containerState: {
                consolidated: document.getElementById('consolidated-table-container')?.innerHTML.length || 0,
                modelStats: document.getElementById('model-statistics-table-container')?.innerHTML.length || 0
            }
        };
    });
    
    console.log('🔧 [FIX-TEST] Results after permanent fix:');
    console.log(`  Consolidated cards: ${results.consolidatedCards}`);
    console.log(`  First title: "${results.firstTitle}"`);
    console.log(`  Model stats cards: ${results.modelStatsCards}`);
    console.log(`  Container sizes: consolidated=${results.containerState.consolidated}, modelStats=${results.containerState.modelStats}`);
    
    let isFixed = false;
    
    if (results.firstTitle && !results.firstTitle.includes('🤖')) {
        console.log('✅ [SUCCESS] PERMANENT FIX WORKS! Shows mine name instead of model ID');
        console.log(`✅ [SUCCESS] Showing: "${results.firstTitle}"`);
        isFixed = true;
    } else if (results.consolidatedCards === 0) {
        console.log('⚠️ [INFO] No consolidated cards found - checking if data loading failed');
    } else {
        console.log('❌ [STILL BROKEN] Still showing model IDs instead of mine names');
        console.log(`❌ [FAILURE] Showing: "${results.firstTitle}"`);
    }
    
    // Test statistics tab separately
    console.log('🧪 [TEST] Phase 3: Test statistics tab - should load statistics correctly');
    await page.click('a[data-tab="statistics"]');
    await page.waitForTimeout(4000);
    
    const statsResults = await page.evaluate(() => {
        const statsCards = document.querySelectorAll('#model-statistics-table-container .mine-data-card');
        return {
            statsCardsCount: statsCards.length,
            statsLoaded: statsCards.length > 0
        };
    });
    
    console.log(`📊 [STATS-TEST] Statistics cards loaded: ${statsResults.statsCardsCount}`);
    
    // Final screenshot
    await page.screenshot({ path: 'task_1_3_permanent_fix_test.png', fullPage: true });
    await browser.close();
    
    return {
        isFixed,
        consolidatedCards: results.consolidatedCards,
        firstTitle: results.firstTitle,
        statsWorking: statsResults.statsLoaded
    };
}

testTask13Fix().catch(console.error);