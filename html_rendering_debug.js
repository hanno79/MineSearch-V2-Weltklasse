/**
 * HTML Rendering Debug - PHASE 4.3
 * Author: rahn
 * Datum: 13.08.2025
 * Beschreibung: Diagnose warum HTML als Text angezeigt wird statt gerendert
 */

const { chromium } = require('playwright');

async function debugHtmlRendering() {
    console.log('🔧 [HTML DEBUG] Starting HTML rendering diagnosis...');
    
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext();
    const page = await context.newPage();
    
    // Monitor JavaScript errors
    page.on('pageerror', error => {
        console.log('💥 [JS ERROR]', error.message);
    });
    
    // Monitor console messages
    page.on('console', msg => {
        const text = msg.text();
        if (text.includes('[SEARCH]') || text.includes('displayResults') || text.includes('HTML')) {
            console.log('🖥️ [CONSOLE]', text);
        }
    });
    
    // Monitor network responses
    page.on('response', async response => {
        if (response.url().includes('/api/search/multi')) {
            console.log(`📨 [API] ${response.status()} - Search API response`);
            try {
                const responseText = await response.text();
                console.log(`📊 [API DATA] Response length: ${responseText.length} chars`);
                console.log(`📊 [API PREVIEW] First 200 chars: ${responseText.substring(0, 200)}`);
            } catch (e) {
                console.log('❌ [API] Could not read response text:', e.message);
            }
        }
    });
    
    try {
        console.log('🔄 [STEP 1] Loading MineSearch page...');
        await page.goto('http://localhost:8000');
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(3000);
        
        console.log('🔄 [STEP 2] Filling search form...');
        
        // Fill in search criteria
        await page.fill('input[name="mine_name"]', 'Canadian Malartic');
        await page.fill('input[name="country"]', 'Canada');
        await page.fill('input[name="commodity"]', 'Gold');
        
        // Check if models are loaded
        const modelCheckboxes = await page.$$('input[name="model"]');
        console.log(`🎯 [MODELS] Found ${modelCheckboxes.length} model checkboxes`);
        
        // Select at least one model (if available)
        if (modelCheckboxes.length > 0) {
            await modelCheckboxes[0].check();
            console.log('✅ [MODELS] First model selected');
        } else {
            console.log('⚠️ [MODELS] No model checkboxes found - continuing anyway');
        }
        
        console.log('🔄 [STEP 3] Starting single search...');
        
        // Get results div BEFORE search
        const resultsBefore = await page.$eval('#results', el => el.innerHTML);
        console.log(`📊 [BEFORE] Results div content: "${resultsBefore.substring(0, 100)}"`);
        
        // Click search button
        const searchButton = await page.$('button[onclick="startSingleSearch()"], #single-search button[type="submit"], .search-button');
        if (searchButton) {
            await searchButton.click();
            console.log('✅ [SEARCH] Search button clicked');
        } else {
            console.log('❌ [SEARCH] Search button not found');
            await page.screenshot({ path: 'no_search_button.png' });
            return;
        }
        
        // Wait for search to complete - LONG wait as requested
        console.log('⏳ [WAIT] Waiting 45 seconds for search to complete...');
        await page.waitForTimeout(45000);
        
        console.log('🔍 [STEP 4] Analyzing results after search...');
        
        // Get results div AFTER search
        const resultsAfter = await page.$eval('#results', el => el.innerHTML);
        console.log(`📊 [AFTER] Results div content length: ${resultsAfter.length} chars`);
        console.log(`📊 [AFTER] Results preview: "${resultsAfter.substring(0, 300)}"`);
        
        // Check if content looks like HTML being displayed as text
        const containsHTMLTags = resultsAfter.includes('<div') || resultsAfter.includes('<span') || resultsAfter.includes('<table');
        const containsHTMLEntities = resultsAfter.includes('&lt;') || resultsAfter.includes('&gt;') || resultsAfter.includes('&amp;');
        
        console.log('🔍 [ANALYSIS] HTML Rendering Analysis:');
        console.log(`  Contains HTML tags: ${containsHTMLTags}`);
        console.log(`  Contains HTML entities: ${containsHTMLEntities}`);
        
        if (containsHTMLEntities) {
            console.log('🚨 [ISSUE FOUND] HTML is being ESCAPED - displayed as entities instead of rendered');
            console.log('🔧 [ROOT CAUSE] Frontend is using textContent instead of innerHTML');
        } else if (resultsAfter.includes('<') && resultsAfter.includes('>')) {
            console.log('🚨 [ISSUE FOUND] Raw HTML tags visible - not being rendered');
            console.log('🔧 [ROOT CAUSE] Frontend is displaying HTML source instead of parsing it');
        }
        
        // Take debugging screenshots
        await page.screenshot({ path: 'html_rendering_issue.png' });
        
        // Check the exact DOM structure
        const resultsElement = await page.$('#results');
        if (resultsElement) {
            const elementHTML = await resultsElement.innerHTML();
            const elementText = await resultsElement.textContent();
            
            console.log('🔍 [DOM ANALYSIS]');
            console.log(`  Element innerHTML length: ${elementHTML.length}`);
            console.log(`  Element textContent length: ${elementText.length}`);
            console.log(`  Ratio (text/html): ${(elementText.length / elementHTML.length * 100).toFixed(1)}%`);
            
            // If text content is much smaller than HTML, it means HTML is being rendered
            // If they're similar, it means HTML is being displayed as text
            if (elementText.length / elementHTML.length > 0.8) {
                console.log('🚨 [DIAGNOSIS] HTML is being displayed as TEXT (not rendered)');
                console.log('🎯 [SOLUTION NEEDED] Fix displayResults() to use innerHTML instead of textContent');
            } else {
                console.log('✅ [DIAGNOSIS] HTML seems to be rendered properly');
            }
        }
        
        // Check if there are any JavaScript errors related to displayResults
        const errorLogs = await page.evaluate(() => {
            return window.console && window.console.errors ? window.console.errors : [];
        });
        console.log(`🔍 [JS ERRORS] Found ${errorLogs.length} JavaScript errors`);
        
    } catch (error) {
        console.error('💥 [ERROR]', error);
        await page.screenshot({ path: 'html_debug_error.png' });
    }
    
    await browser.close();
    
    console.log('🏁 [HTML DEBUG] Analysis complete');
    console.log('');
    console.log('📋 NEXT STEPS:');
    console.log('1. If HTML entities found (&lt; &gt;): Fix HTML escaping in displayResults()');
    console.log('2. If raw HTML visible: Change textContent to innerHTML in results display');
    console.log('3. Check results-processor.js for incorrect DOM manipulation');
}

debugHtmlRendering().catch(console.error);