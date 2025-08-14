/**
 * Quick Debug Test - PHASE 2.3
 * Author: rahn
 * Datum: 13.08.2025
 * Beschreibung: Quick test to see debug logs from results processor
 */

const { chromium } = require('playwright');

async function quickDebugTest() {
    console.log('🔍 [QUICK DEBUG] Testing results processing with debug logs...');
    
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext();
    const page = await context.newPage();
    
    // Monitor all console logs
    page.on('console', msg => {
        const text = msg.text();
        if (text.includes('[DEBUG]') || text.includes('[RESULTS]') || text.includes('Response received')) {
            console.log(`🖥️ [FRONTEND] ${text}`);
        }
    });
    
    page.on('response', async response => {
        if (response.url().includes('/api/search/multi')) {
            console.log(`📨 [API] ${response.status()} - Response captured`);
        }
    });
    
    try {
        console.log('🔄 Loading page and starting quick search...');
        await page.goto('http://localhost:8000');
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(2000);
        
        await page.fill('#mine_name', 'Quick Test');
        await page.fill('#country', 'Test Country');
        
        console.log('🔄 Clicking search...');
        await page.click('#start-search');
        
        // Wait just enough to see the debug logs
        await page.waitForTimeout(15000);
        
        console.log('📊 Checking results display...');
        const results = await page.$eval('#results', el => el.textContent.substring(0, 100)).catch(() => 'NOT_FOUND');
        console.log('Results content:', results);
        
        await page.screenshot({ path: 'quick_debug_result.png' });
        
    } catch (error) {
        console.error('💥 [ERROR]', error);
    }
    
    await browser.close();
    console.log('🏁 [QUICK DEBUG] Complete');
}

quickDebugTest().catch(console.error);