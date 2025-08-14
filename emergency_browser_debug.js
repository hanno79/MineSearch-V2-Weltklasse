/**
 * Emergency Browser Debug - Phase 1.1
 * Author: rahn
 * Datum: 13.08.2025
 * Beschreibung: Emergency debugging of search system with real browser
 */

const { chromium } = require('playwright');

async function emergencyBrowserDebug() {
    console.log('🚨 [EMERGENCY DEBUG] Starting real browser debugging session...');
    
    const browser = await chromium.launch({ 
        headless: false,
        slowMo: 500
    });
    const context = await browser.newContext();
    const page = await context.newPage();
    
    // Comprehensive logging
    page.on('console', msg => {
        console.log(`🖥️ [BROWSER CONSOLE] ${msg.type()}: ${msg.text()}`);
    });
    
    page.on('pageerror', error => {
        console.log(`❌ [PAGE ERROR] ${error.message}`);
    });
    
    page.on('request', request => {
        if (request.url().includes('/api/') && !request.url().includes('favicon')) {
            console.log(`📡 [REQUEST] ${request.method()} ${request.url()}`);
        }
    });
    
    page.on('response', response => {
        if (response.url().includes('/api/')) {
            console.log(`📨 [RESPONSE] ${response.status()} ${response.url()}`);
        }
    });
    
    try {
        // Step 1: Load the page
        console.log('📋 [STEP 1] Loading MineSearch 2.0...');
        await page.goto('http://localhost:8000');
        await page.waitForLoadState('networkidle');
        await page.screenshot({ path: 'emergency_debug_01_loaded.png' });
        
        // Step 2: Test JavaScript function availability
        console.log('📋 [STEP 2] Testing JavaScript function availability...');
        const functionTests = await page.evaluate(() => {
            return {
                startSingleSearchExists: typeof window.startSingleSearch === 'function',
                startBatchSearchExists: typeof window.startBatchSearch === 'function',
                searchJsLoaded: !!document.querySelector('script[src*="search.js"]'),
                apiBaseUrl: window.API_BASE_URL
            };
        });
        
        console.log('🔍 [FUNCTION CHECK]', functionTests);
        
        // Step 3: Fill out form
        console.log('📋 [STEP 3] Filling out single search form...');
        await page.fill('#mine_name', 'Test Mine');
        await page.fill('#country', 'Canada');
        
        // Step 4: Check if models are pre-selected
        const selectedModels = await page.locator('input[name="model"]:checked').count();
        console.log(`🎯 [MODELS] Pre-selected models: ${selectedModels}`);
        
        if (selectedModels === 0) {
            console.log('🔧 [FIX] Manually selecting first model...');
            await page.waitForSelector('input[name="model"]', { timeout: 5000 });
            await page.check('input[name="model"]');
        }
        
        await page.screenshot({ path: 'emergency_debug_02_form_filled.png' });
        
        // Step 5: Test button click behavior
        console.log('📋 [STEP 5] Testing search button click...');
        
        // Test if onclick handler exists
        const buttonInfo = await page.evaluate(() => {
            const button = document.getElementById('start-search');
            return {
                exists: !!button,
                onclick: button ? button.onclick?.toString() : null,
                formOnsubmit: document.getElementById('single-search-form')?.onsubmit?.toString() || null
            };
        });
        
        console.log('🔘 [BUTTON INFO]', buttonInfo);
        
        // Step 6: Try to click search button and monitor what happens
        console.log('📋 [STEP 6] Clicking search button...');
        
        let apiCallMade = false;
        let searchError = null;
        
        try {
            // Set up promise to wait for API response
            const apiResponsePromise = page.waitForResponse(response => 
                response.url().includes('/api/search/multi') && 
                response.request().method() === 'POST',
                { timeout: 10000 }
            );
            
            // Click the button
            await page.click('#start-search');
            console.log('✅ [CLICK] Button clicked successfully');
            
            // Wait for API call
            const response = await apiResponsePromise;
            console.log(`📨 [API SUCCESS] ${response.status()}`);
            apiCallMade = true;
            
        } catch (error) {
            searchError = error.message;
            console.log(`❌ [API TIMEOUT] No API call made: ${searchError}`);
        }
        
        await page.screenshot({ path: 'emergency_debug_03_after_click.png' });
        
        // Step 7: Diagnose the issue
        console.log('📋 [STEP 7] Diagnosing the problem...');
        
        const diagnosis = await page.evaluate(() => {
            const form = document.getElementById('single-search-form');
            const button = document.getElementById('start-search');
            
            return {
                formExists: !!form,
                buttonExists: !!button,
                formOnsubmit: form?.getAttribute('onsubmit'),
                buttonType: button?.type,
                buttonDisabled: button?.disabled,
                consoleErrors: window.console._errors || []
            };
        });
        
        console.log('🔍 [DIAGNOSIS]', diagnosis);
        
        // Step 8: Test CSV upload as well
        console.log('📋 [STEP 8] Testing CSV upload tab...');
        
        await page.check('#csv-tab');
        await page.waitForTimeout(1000);
        
        const csvFormVisible = await page.locator('#csv-form').isVisible();
        console.log(`📋 [CSV FORM] Visible: ${csvFormVisible}`);
        
        await page.screenshot({ path: 'emergency_debug_04_csv_tab.png' });
        
        // Summary
        console.log('📊 [EMERGENCY SUMMARY]');
        console.log(`✅ Page loaded: true`);
        console.log(`✅ JavaScript functions exist: ${functionTests.startSingleSearchExists}`);
        console.log(`✅ API call made on click: ${apiCallMade}`);
        console.log(`❌ Search button issue: ${!apiCallMade ? 'YES' : 'NO'}`);
        
        if (!apiCallMade) {
            console.log('🔧 [NEXT ACTION] Need to fix form handler or JavaScript loading');
        } else {
            console.log('✅ [SUCCESS] Search system working correctly');
        }
        
        // Keep browser open for manual inspection
        console.log('👁️ [MANUAL] Browser open for 30 seconds for manual testing...');
        await page.waitForTimeout(30000);
        
    } catch (error) {
        console.error('💥 [CRITICAL ERROR]', error);
        await page.screenshot({ path: 'emergency_debug_error.png' });
    }
    
    await browser.close();
    console.log('🏁 [EMERGENCY DEBUG] Complete');
}

emergencyBrowserDebug().catch(console.error);