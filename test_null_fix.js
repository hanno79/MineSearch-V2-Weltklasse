/**
 * Test Null Fix - Phase 2.1 Validation
 * Author: rahn
 * Datum: 13.08.2025
 * Beschreibung: Test that the null pointer fix actually works
 */

const { chromium } = require('playwright');

async function testNullFix() {
    console.log('🔧 [NULL FIX TEST] Testing null pointer exception fix...');
    
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext();
    const page = await context.newPage();
    
    // Console logging
    page.on('console', msg => {
        console.log(`🖥️ [BROWSER] ${msg.type()}: ${msg.text()}`);
    });
    
    page.on('pageerror', error => {
        console.log(`❌ [PAGE ERROR] ${error.message}`);
    });
    
    page.on('request', request => {
        if (request.url().includes('/api/search/multi')) {
            console.log(`📡 [SUCCESS] API CALL MADE: ${request.method()} ${request.url()}`);
        }
    });
    
    try {
        // Load page
        console.log('📋 [TEST] Loading page...');
        await page.goto('http://localhost:8000');
        await page.waitForLoadState('networkidle');
        
        // Fill form
        console.log('📋 [TEST] Filling form...');
        await page.fill('#mine_name', 'Test Mine');
        await page.fill('#country', 'Canada');
        
        // Wait for models to load
        await page.waitForTimeout(3000);
        
        // Click search button
        console.log('📋 [TEST] Clicking search button...');
        
        let searchSuccess = false;
        try {
            // Wait for API response
            const [response] = await Promise.all([
                page.waitForResponse(response => 
                    response.url().includes('/api/search/multi') && 
                    response.request().method() === 'POST',
                    { timeout: 8000 }
                ),
                page.click('#start-search')
            ]);
            
            console.log(`✅ [SUCCESS] API call made! Status: ${response.status()}`);
            searchSuccess = true;
            
        } catch (error) {
            console.log(`❌ [FAILED] No API call: ${error.message}`);
        }
        
        await page.screenshot({ path: 'null_fix_test_result.png' });
        
        if (searchSuccess) {
            console.log('🎉 [FIXED] Null pointer exception successfully fixed!');
        } else {
            console.log('❌ [STILL BROKEN] Fix did not work');
        }
        
        await page.waitForTimeout(5000);
        
    } catch (error) {
        console.error('💥 [ERROR]', error);
        await page.screenshot({ path: 'null_fix_test_error.png' });
    }
    
    await browser.close();
}

testNullFix().catch(console.error);