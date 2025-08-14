/**
 * Final Search Validation - PHASE 4.1
 * Author: rahn
 * Datum: 13.08.2025
 * Beschreibung: Test complete single search flow after fixes
 */

const { chromium } = require('playwright');

async function finalSearchValidation() {
    console.log('🎯 [FINAL VALIDATION] Starting complete search flow test...');
    
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext();
    const page = await context.newPage();
    
    let searchCompleted = false;
    let displayedResults = false;
    
    // Monitor API responses
    page.on('response', async response => {
        if (response.url().includes('/api/search/multi')) {
            console.log(`📨 [API] ${response.status()} ${response.url()}`);
            
            try {
                const responseText = await response.text();
                const responseJson = JSON.parse(responseText);
                
                console.log(`📊 [API] Success: ${responseJson.success}, Results: ${responseJson.data?.results?.length}`);
                searchCompleted = true;
                
                if (responseJson.success && responseJson.data?.results) {
                    const successful = responseJson.data.results.filter(r => r.success).length;
                    console.log(`✅ [API] ${successful} successful models out of ${responseJson.data.results.length}`);
                }
            } catch (e) {
                console.log('⚠️ [API] Could not parse response:', e.message);
            }
        }
    });
    
    // Monitor frontend logs
    page.on('console', msg => {
        const text = msg.text();
        if (text.includes('[SIMPLE]') || text.includes('[PHASE 4]') || text.includes('[RESULTS]')) {
            console.log(`🖥️ [FRONTEND] ${text}`);
            if (text.includes('displayed successfully')) {
                displayedResults = true;
            }
        }
    });
    
    page.on('pageerror', error => {
        console.log(`❌ [PAGE ERROR] ${error.message}`);
    });
    
    try {
        console.log('🔄 [STEP 1] Loading page...');
        await page.goto('http://localhost:8000');
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(3000);
        
        console.log('🔄 [STEP 2] Setting up search parameters...');
        await page.fill('#mine_name', 'Grasberg');
        await page.fill('#country', 'Indonesien');
        await page.fill('#commodity', 'Kupfer');
        
        console.log('🔄 [STEP 3] Starting search and waiting for completion...');
        await page.click('#start-search');
        
        // Wait for search to complete (60 seconds max)
        let waitTime = 0;
        while (!searchCompleted && waitTime < 60000) {
            await page.waitForTimeout(1000);
            waitTime += 1000;
            if (waitTime % 15000 === 0) {
                console.log(`⏳ [WAITING] ${waitTime/1000}s - Search in progress...`);
            }
        }
        
        if (searchCompleted) {
            console.log('✅ [STEP 4] Search API completed, waiting for results display...');
            
            // Wait additional time for results to display
            await page.waitForTimeout(5000);
            
            // Check what's displayed in results div
            const resultsContent = await page.$eval('#results', el => ({
                innerHTML: el.innerHTML.substring(0, 500),
                textContent: el.textContent.substring(0, 200),
                hasSuccessDiv: el.innerHTML.includes('Multi-Model-Suchergebnisse'),
                hasErrorDiv: el.innerHTML.includes('Suchergebnis fehlgeschlagen')
            })).catch(() => ({
                innerHTML: 'NOT_FOUND',
                textContent: 'NOT_FOUND',
                hasSuccessDiv: false,
                hasErrorDiv: false
            }));
            
            console.log('🔍 [RESULTS CHECK]');
            console.log('  Has Success Div:', resultsContent.hasSuccessDiv);
            console.log('  Has Error Div:', resultsContent.hasErrorDiv);
            console.log('  Text Content:', resultsContent.textContent);
            
            if (resultsContent.hasSuccessDiv) {
                console.log('🎉 [SUCCESS] Results are properly displayed!');
                
                // Count model cards
                const modelCards = await page.$$('.model-result-card');
                console.log(`📊 [ANALYSIS] Found ${modelCards.length} model result cards`);
                
                for (let i = 0; i < modelCards.length; i++) {
                    const modelId = await modelCards[i].$eval('h4', el => el.textContent).catch(() => 'Unknown');
                    console.log(`  Model ${i+1}: ${modelId}`);
                }
                
            } else if (resultsContent.hasErrorDiv) {
                console.log('❌ [FAILURE] Still showing error despite successful API response');
            } else {
                console.log('⚠️ [UNKNOWN] Unexpected results display state');
            }
            
        } else {
            console.log('⚠️ [TIMEOUT] Search did not complete within 60 seconds');
        }
        
        await page.screenshot({ path: 'final_search_validation_result.png' });
        
    } catch (error) {
        console.error('💥 [ERROR]', error);
        await page.screenshot({ path: 'final_search_validation_error.png' });
    }
    
    await browser.close();
    
    // Final Analysis
    console.log('\n📊 [FINAL ANALYSIS]');
    console.log('===================');
    console.log(`Search Completed: ${searchCompleted ? '✅' : '❌'}`);
    console.log(`Results Displayed: ${displayedResults ? '✅' : '❌'}`);
    
    if (searchCompleted && displayedResults) {
        console.log('🎉 SEARCH SYSTEM REPAIR: SUCCESSFUL');
        console.log('🚀 Single search is working correctly!');
    } else {
        console.log('⚠️ SEARCH SYSTEM REPAIR: PARTIAL');
        if (searchCompleted && !displayedResults) {
            console.log('🔧 Issue: API works but results not displaying');
        } else if (!searchCompleted) {
            console.log('🔧 Issue: API not responding or timing out');
        }
    }
    
    console.log('🏁 [FINAL VALIDATION] Complete');
}

finalSearchValidation().catch(console.error);