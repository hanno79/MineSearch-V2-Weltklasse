/**
 * Enhanced API Debug - PHASE 2.2
 * Author: rahn
 * Datum: 13.08.2025
 * Beschreibung: Capture exact API response to identify response processing issue
 */

const { chromium } = require('playwright');

async function enhancedAPIDebug() {
    console.log('🔍 [ENHANCED API DEBUG] Starting comprehensive API debugging...');
    
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext();
    const page = await context.newPage();
    
    let apiResponseReceived = false;
    let apiResponseData = null;
    
    // Comprehensive API monitoring
    page.on('response', async response => {
        if (response.url().includes('/api/search/multi')) {
            console.log(`📨 [API RESPONSE] ${response.status()} ${response.url()}`);
            console.log(`📋 [RESPONSE HEADERS]`, response.headers());
            
            try {
                const responseText = await response.text();
                console.log(`📄 [RESPONSE BODY LENGTH]`, responseText.length);
                console.log(`📄 [RESPONSE BODY START]`, responseText.substring(0, 300));
                
                try {
                    const responseJson = JSON.parse(responseText);
                    apiResponseData = responseJson;
                    apiResponseReceived = true;
                    
                    console.log(`📊 [PARSED API RESPONSE]`);
                    console.log(`   Success: ${responseJson.success}`);
                    console.log(`   Has Data: ${!!responseJson.data}`);
                    console.log(`   Has Error: ${!!responseJson.error}`);
                    
                    if (responseJson.data && responseJson.data.results) {
                        console.log(`   Results Count: ${responseJson.data.results.length}`);
                        console.log(`   Successful Models: ${responseJson.data.successful_models}`);
                        console.log(`   Total Models: ${responseJson.data.total_models}`);
                        
                        responseJson.data.results.forEach((result, idx) => {
                            console.log(`   Model ${idx+1}: ${result.model_id} - Success: ${result.success}`);
                            if (!result.success) {
                                console.log(`     Error: ${result.error}`);
                            }
                        });
                    }
                    
                    if (responseJson.error) {
                        console.log(`❌ [API ERROR] ${responseJson.error}`);
                    }
                    
                } catch (jsonError) {
                    console.log(`⚠️ [JSON PARSE ERROR] ${jsonError.message}`);
                    console.log(`📄 [RAW RESPONSE]`, responseText);
                }
            } catch (textError) {
                console.log(`⚠️ [TEXT ERROR] ${textError.message}`);
            }
        }
    });
    
    // Monitor frontend console for errors
    page.on('console', msg => {
        if (msg.text().includes('Response received') || msg.text().includes('[SEARCH]') || msg.text().includes('Error')) {
            console.log(`🖥️ [FRONTEND] ${msg.text()}`);
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
        
        console.log('🔄 [STEP 2] Starting single search...');
        await page.fill('#mine_name', 'Test Mine');
        await page.fill('#country', 'Canada');
        
        console.log('🔄 [STEP 3] Clicking search and waiting for complete API cycle...');
        await page.click('#start-search');
        
        // Wait up to 60 seconds for API response
        let waitTime = 0;
        while (!apiResponseReceived && waitTime < 60000) {
            await page.waitForTimeout(1000);
            waitTime += 1000;
            if (waitTime % 10000 === 0) {
                console.log(`⏳ [WAITING] ${waitTime/1000}s - Still waiting for API response...`);
            }
        }
        
        if (apiResponseReceived) {
            console.log('✅ [SUCCESS] API response captured successfully');
            console.log('📊 [ANALYSIS] Response analysis:');
            
            if (apiResponseData.success) {
                console.log('   ✅ API reports SUCCESS');
                console.log('   📈 Frontend should display results');
            } else {
                console.log('   ❌ API reports FAILURE');
                console.log('   🔍 Error message:', apiResponseData.error);
            }
            
            // Check what frontend actually shows
            await page.waitForTimeout(2000);
            const resultsContent = await page.$eval('#results', el => el.innerText).catch(() => 'Not found');
            console.log('🖥️ [FRONTEND DISPLAY]', resultsContent.substring(0, 200));
            
        } else {
            console.log('⚠️ [TIMEOUT] No API response received within 60 seconds');
        }
        
        await page.screenshot({ path: 'enhanced_api_debug_result.png' });
        
    } catch (error) {
        console.error('💥 [ERROR]', error);
        await page.screenshot({ path: 'enhanced_api_debug_error.png' });
    }
    
    await browser.close();
    console.log('🏁 [ENHANCED API DEBUG] Complete');
}

enhancedAPIDebug().catch(console.error);