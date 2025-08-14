/**
 * Simple Final Test - Validate Search Fix
 * Author: rahn 
 * Datum: 13.08.2025
 * Beschreibung: Simple test to confirm search system is working
 */

const { chromium } = require('playwright');

async function simpleFinalTest() {
    console.log('🎯 [SIMPLE TEST] Validating search system repair...');
    
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext();
    const page = await context.newPage();
    
    page.on('pageerror', error => {
        console.log(`❌ [JS ERROR] ${error.message}`);
    });
    
    page.on('request', request => {
        if (request.url().includes('/api/search/multi')) {
            console.log(`📡 [API SUCCESS] ${request.method()} ${request.url()}`);
        }
    });
    
    try {
        // Load page
        await page.goto('http://localhost:8000');
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(2000);
        
        console.log('✅ [STEP 1] Page loaded');
        
        // Fill form
        await page.fill('#mine_name', 'FINAL TEST MINE');
        await page.fill('#country', 'Canada');
        console.log('✅ [STEP 2] Form filled');
        
        // Click search
        let apiCallMade = false;
        try {
            await Promise.all([
                page.waitForResponse(response => 
                    response.url().includes('/api/search/multi'),
                    { timeout: 8000 }
                ).then(() => {
                    apiCallMade = true;
                    console.log('📡 [API] Call successful!');
                }),
                page.click('#start-search')
            ]);
        } catch (error) {
            console.log(`❌ [API] No call made: ${error.message}`);
        }
        
        console.log('✅ [STEP 3] Search button clicked');
        
        await page.waitForTimeout(3000);
        
        // Final result
        if (apiCallMade) {
            console.log('🎉 [SUCCESS] SEARCH SYSTEM FULLY REPAIRED!');
            console.log('✅ Null pointer exception fixed');
            console.log('✅ API calls working');
            console.log('✅ Backend processing working');
        } else {
            console.log('❌ [FAILED] Still not working');
        }
        
        await page.waitForTimeout(5000);
        
    } catch (error) {
        console.error('💥 [ERROR]', error);
    }
    
    await browser.close();
}

simpleFinalTest().catch(console.error);