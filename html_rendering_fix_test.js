/**
 * HTML Rendering Fix Test - PHASE 5.1
 * Author: rahn
 * Datum: 13.08.2025
 * Beschreibung: Test ob HTML-Rendering nach sanitizeHTML()-Fix funktioniert
 */

const { chromium } = require('playwright');

async function testHtmlRenderingFix() {
    console.log('🔧 [HTML FIX TEST] Starting HTML rendering fix validation...');
    
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
        if (text.includes('[SEARCH]') || text.includes('displayResults') || text.includes('HTML') || text.includes('RESULTS')) {
            console.log('🖥️ [CONSOLE]', text);
        }
    });
    
    // Monitor API responses
    page.on('response', async response => {
        if (response.url().includes('/api/search/multi')) {
            console.log(`📨 [API] ${response.status()} - Search response received`);
        }
    });
    
    try {
        console.log('🔄 [STEP 1] Loading MineSearch page...');
        await page.goto('http://localhost:8000');
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(3000);
        
        console.log('🔄 [STEP 2] Filling search form with simple criteria...');
        
        // Fill in search criteria  
        await page.fill('input[name="mine_name"]', 'Canadian Malartic');
        await page.fill('input[name="country"]', 'Canada');
        
        // Wait for models to load
        console.log('⏳ [MODELS] Waiting for models to load...');
        await page.waitForTimeout(5000);
        
        // Select the recommended models (which should be auto-selected)
        const selectedModels = await page.$$('input[name="model"]:checked');
        console.log(`🎯 [MODELS] Found ${selectedModels.length} selected models`);
        
        // If no models selected, select first available
        if (selectedModels.length === 0) {
            const availableModels = await page.$$('input[name="model"]');
            if (availableModels.length > 0) {
                await availableModels[0].check();
                console.log('✅ [MODELS] Selected first available model');
            }
        }
        
        console.log('🔄 [STEP 3] Starting search to test HTML rendering...');
        
        // Get initial results div content
        const initialContent = await page.$eval('#results', el => el.innerHTML.trim());
        console.log(`📊 [BEFORE] Initial results div: "${initialContent.substring(0, 50)}"`);
        
        // Start search
        const searchButton = await page.$('button[onclick="startSingleSearch()"], #single-search button, .search-button');
        if (searchButton) {
            await searchButton.click();
            console.log('✅ [SEARCH] Search started');
        } else {
            console.log('❌ [SEARCH] Search button not found');
            await page.screenshot({ path: 'no_search_button_fix_test.png' });
            return;
        }
        
        // Wait for search completion (much longer wait as requested)
        console.log('⏳ [WAIT] Waiting 60 seconds for search to complete and render...');
        await page.waitForTimeout(60000);
        
        console.log('🔍 [STEP 4] Analyzing HTML rendering after fix...');
        
        // Get results after search
        const resultsAfter = await page.$eval('#results', el => el.innerHTML);
        console.log(`📊 [AFTER] Results length: ${resultsAfter.length} chars`);
        console.log(`📊 [AFTER] First 300 chars: "${resultsAfter.substring(0, 300)}"`);
        
        // Detailed analysis of HTML vs Text
        const resultsElement = await page.$('#results');
        if (resultsElement) {
            const elementHTML = await resultsElement.innerHTML();
            const elementText = await resultsElement.textContent();
            const visibleText = await resultsElement.innerText();
            
            console.log('🔍 [HTML ANALYSIS AFTER FIX]');
            console.log(`  innerHTML length: ${elementHTML.length}`);
            console.log(`  textContent length: ${elementText.length}`);
            console.log(`  innerText length: ${visibleText.length}`);
            
            const textToHtmlRatio = elementText.length / elementHTML.length;
            console.log(`  Text/HTML Ratio: ${(textToHtmlRatio * 100).toFixed(1)}%`);
            
            // Check for HTML entities (bad)
            const hasHTMLEntities = elementHTML.includes('&lt;') || elementHTML.includes('&gt;') || elementHTML.includes('&amp;');
            console.log(`  Contains HTML entities: ${hasHTMLEntities}`);
            
            // Check for raw HTML tags visible in text (bad)
            const hasRawHTMLInText = elementText.includes('<div') || elementText.includes('<span') || elementText.includes('<h');
            console.log(`  Raw HTML visible in text: ${hasRawHTMLInText}`);
            
            // Check for proper HTML structure (good)
            const hasProperHTML = elementHTML.includes('<div') && elementHTML.includes('class=');
            console.log(`  Has proper HTML structure: ${hasProperHTML}`);
            
            // FINAL DIAGNOSIS
            if (!hasHTMLEntities && !hasRawHTMLInText && hasProperHTML && textToHtmlRatio < 0.7) {
                console.log('');
                console.log('🎉 [SUCCESS] HTML RENDERING FIX SUCCESSFUL!');
                console.log('✅ HTML is being rendered properly (not displayed as text)');
                console.log('✅ No HTML entities found (no escaping)');
                console.log('✅ No raw HTML visible in text content');
                console.log('✅ Proper HTML structure present');
            } else if (hasHTMLEntities) {
                console.log('');
                console.log('❌ [STILL BROKEN] HTML is still being escaped to entities');
                console.log('🔧 [ACTION NEEDED] sanitizeHTML() is still being called somehow');
            } else if (hasRawHTMLInText) {
                console.log('');
                console.log('❌ [STILL BROKEN] Raw HTML is visible in text content');
                console.log('🔧 [ACTION NEEDED] innerHTML is not working properly');
            } else {
                console.log('');
                console.log('⚠️ [PARTIAL FIX] Some improvement but still needs work');
                console.log(`Text/HTML ratio: ${(textToHtmlRatio * 100).toFixed(1)}% (should be < 70%)`)
            }
        }
        
        // Take a screenshot of the results
        await page.screenshot({ path: 'html_rendering_fix_test.png', fullPage: true });
        
        // Check if specific HTML elements are rendered
        console.log('🔍 [ELEMENT CHECK] Looking for rendered HTML elements...');
        
        const cardElements = await page.$$('.result-card, .mine-data-card, .modern-card');
        console.log(`📊 [ELEMENTS] Found ${cardElements.length} card elements`);
        
        const headerElements = await page.$$('#results h2, #results h3, #results h4');
        console.log(`📊 [ELEMENTS] Found ${headerElements.length} header elements in results`);
        
        const buttonElements = await page.$$('#results button');
        console.log(`📊 [ELEMENTS] Found ${buttonElements.length} button elements in results`);
        
        if (cardElements.length > 0 || headerElements.length > 0) {
            console.log('✅ [ELEMENTS] HTML elements are being rendered properly!');
        } else {
            console.log('❌ [ELEMENTS] No HTML elements found - still displaying as text');
        }
        
    } catch (error) {
        console.error('💥 [ERROR]', error);
        await page.screenshot({ path: 'html_fix_test_error.png' });
    }
    
    await browser.close();
    console.log('🏁 [HTML FIX TEST] Complete');
}

testHtmlRenderingFix().catch(console.error);