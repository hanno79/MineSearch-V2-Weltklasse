/**
 * Debug API Response - PHASE 2.1
 * Author: rahn
 * Datum: 13.08.2025
 * Beschreibung: Debug actual API response content for single and batch search
 */

const { chromium } = require('playwright');

async function debugAPIResponse() {
    console.log('🔍 [API DEBUG] Starting API response debugging...');
    
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext();
    const page = await context.newPage();
    
    // Comprehensive API monitoring
    page.on('request', request => {
        if (request.url().includes('/api/search') || request.url().includes('/api/batch')) {
            console.log(`📡 [REQUEST] ${request.method()} ${request.url()}`);
            console.log(`📋 [REQUEST HEADERS]`, request.headers());
        }
    });
    
    page.on('response', async response => {
        if (response.url().includes('/api/search') || response.url().includes('/api/batch')) {
            console.log(`📨 [RESPONSE] ${response.status()} ${response.url()}`);
            console.log(`📋 [RESPONSE HEADERS]`, response.headers());
            
            // Try to get response text
            try {
                const responseText = await response.text();
                console.log(`📄 [RESPONSE BODY]`, responseText.substring(0, 500) + '...');
                
                // Try to parse as JSON
                try {
                    const responseJson = JSON.parse(responseText);
                    console.log(`📊 [PARSED JSON]`, responseJson);
                    
                    if (responseJson.success !== undefined) {
                        console.log(`✅ [API RESULT] Success: ${responseJson.success}`);
                        if (responseJson.data) {
                            console.log(`📊 [DATA] Results count: ${responseJson.data.results?.length || 'N/A'}`);
                        }
                        if (responseJson.error) {
                            console.log(`❌ [ERROR] ${responseJson.error}`);
                        }
                    }
                } catch (jsonError) {
                    console.log(`⚠️ [JSON PARSE ERROR] Not valid JSON: ${jsonError.message}`);
                }
            } catch (textError) {
                console.log(`⚠️ [TEXT ERROR] Could not get response text: ${textError.message}`);
            }
        }
    });
    
    page.on('console', msg => {
        if (msg.text().includes('[SEARCH]') || msg.text().includes('Response received')) {
            console.log(`🖥️ [FRONTEND LOG] ${msg.text()}`);
        }
    });
    
    page.on('pageerror', error => {
        console.log(`❌ [PAGE ERROR] ${error.message}`);
    });
    
    try {
        // Load page
        console.log('🔄 [STEP 1] Loading page...');
        await page.goto('http://localhost:8000');
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(3000);
        
        // Test Single Search
        console.log('🔄 [STEP 2] Testing single search API response...');
        await page.fill('#mine_name', 'Grasberg');
        await page.fill('#country', 'Indonesien'); 
        
        await page.waitForTimeout(1000);
        
        console.log('🔄 [STEP 3] Clicking search button and monitoring response...');
        await page.click('#start-search');
        
        // Wait longer to see full API response cycle
        await page.waitForTimeout(30000);  // Wait 30 seconds to see full search cycle
        
        await page.screenshot({ path: 'debug_api_single_search.png' });
        
        console.log('✅ [SINGLE SEARCH] Debug completed - check logs above for API response details');
        
        await page.waitForTimeout(5000);
        
    } catch (error) {
        console.error('💥 [ERROR]', error);
        await page.screenshot({ path: 'debug_api_error.png' });
    }
    
    await browser.close();
    console.log('🏁 [API DEBUG] Complete');
}

debugAPIResponse().catch(console.error);