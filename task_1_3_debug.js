/**
 * TASK 1.3 Debug: Frontend Data Card Logic Analysis
 * Author: rahn
 * Datum: 14.08.2025
 */

const { chromium } = require('playwright');

async function debugDataCardGeneration() {
    console.log('🔧 [TASK-1.3] Debugging Data Card Generation...');
    
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    
    await page.goto('http://localhost:8000');
    await page.waitForTimeout(3000);
    
    // Navigate to consolidated tab and wait for load
    await page.click('a[data-tab="consolidated"]');
    await page.waitForTimeout(5000);
    
    // Debug the data card generation process
    const debugInfo = await page.evaluate(() => {
        console.log('🔍 [DEBUG] Starting frontend debugging...');
        
        // Check if generateMineDataCard is available
        const hasMineCardFunction = typeof window.generateMineDataCard === 'function';
        const hasRenderGrid = typeof window.renderDataCardGrid === 'function';
        
        console.log('Functions available:', { hasMineCardFunction, hasRenderGrid });
        
        // Get sample consolidated data
        const cards = document.querySelectorAll('.mine-data-card');
        console.log(`Found ${cards.length} cards in DOM`);
        
        let sampleData = null;
        let cardHtml = '';
        
        if (cards.length > 0) {
            const firstCard = cards[0];
            sampleData = {
                title: firstCard.querySelector('.card-title')?.textContent?.trim(),
                subtitle: firstCard.querySelector('.card-subtitle')?.textContent?.trim(),
                dataRows: Array.from(firstCard.querySelectorAll('.data-row')).map(row => ({
                    label: row.querySelector('.data-label')?.textContent?.trim(),
                    value: row.querySelector('.data-value')?.textContent?.trim()
                }))
            };
            
            cardHtml = firstCard.outerHTML.substring(0, 500) + '...';
        }
        
        // Test generateMineDataCard with fake but correct data structure
        let testCardHtml = '';
        if (hasMineCardFunction) {
            try {
                const testMineData = {
                    mine_name: 'TEST_MINE_NAME',
                    country: 'TEST_COUNTRY',
                    best_values: {
                        mine_type: 'TEST_TYPE'
                    }
                };
                
                testCardHtml = window.generateMineDataCard(testMineData, 'consolidated');
                console.log('✅ [DEBUG] generateMineDataCard test successful');
            } catch (error) {
                console.error('❌ [DEBUG] generateMineDataCard test failed:', error.message);
            }
        }
        
        return {
            functionsAvailable: { hasMineCardFunction, hasRenderGrid },
            cardsInDOM: cards.length,
            sampleData,
            cardHtmlSample: cardHtml,
            testCardHtml: testCardHtml.substring(0, 200) + '...'
        };
    });
    
    console.log('🔍 [DEBUG] Frontend Analysis Results:');
    console.log('  Functions Available:', debugInfo.functionsAvailable);
    console.log('  Cards in DOM:', debugInfo.cardsInDOM);
    console.log('  Sample Card Data:', debugInfo.sampleData);
    
    if (debugInfo.sampleData?.title?.includes('🤖')) {
        console.log('❌ [PROBLEM CONFIRMED] Cards show model IDs instead of mine names!');
        console.log(`   Showing: "${debugInfo.sampleData.title}"`);
        console.log('   Expected: Real mine name like "Antamina"');
    }
    
    // Check if test card generation produces correct result
    if (debugInfo.testCardHtml.includes('TEST_MINE_NAME')) {
        console.log('✅ [DEBUG] generateMineDataCard function works correctly with test data');
    } else {
        console.log('❌ [DEBUG] generateMineDataCard function has issues');
    }
    
    await page.screenshot({ path: 'task_1_3_debug_screenshot.png', fullPage: true });
    await browser.close();
    
    return debugInfo;
}

debugDataCardGeneration().catch(console.error);