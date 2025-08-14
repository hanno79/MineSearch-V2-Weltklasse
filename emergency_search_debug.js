/**
 * Emergency Search System Debug Test
 * Author: rahn
 * Datum: 13.08.2025
 * Beschreibung: Direkte API-Calls und Frontend-Debugging für Such-System
 */

const { chromium } = require('playwright');

async function emergencySearchDebug() {
    console.log('🚨 [EMERGENCY DEBUG] Starting critical search system analysis...');
    
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext();
    const page = await context.newPage();
    
    // Console-Logs abfangen
    page.on('console', msg => {
        console.log(`🖥️  [BROWSER CONSOLE] ${msg.type()}: ${msg.text()}`);
    });
    
    // Network-Requests überwachen
    page.on('request', request => {
        if (request.url().includes('/api/')) {
            console.log(`📡 [REQUEST] ${request.method()} ${request.url()}`);
        }
    });
    
    page.on('response', response => {
        if (response.url().includes('/api/')) {
            console.log(`📨 [RESPONSE] ${response.status()} ${response.url()}`);
        }
    });
    
    try {
        // 1. Hauptseite laden
        console.log('🔄 [TEST 1] Loading main page...');
        await page.goto('http://localhost:8000');
        await page.waitForTimeout(3000);
        
        await page.screenshot({ path: 'debug_01_main_page.png' });
        
        // 2. Direkte API-Tests
        console.log('🔄 [TEST 2] Direct API endpoint tests...');
        
        // Models API-Test
        const modelsResponse = await page.evaluate(async () => {
            try {
                const response = await fetch('/api/models');
                const data = await response.json();
                return { status: response.status, data: data };
            } catch (error) {
                return { error: error.message };
            }
        });
        console.log('📊 [MODELS API]', modelsResponse);
        
        // 3. Search Multi API Test
        const searchMultiTest = await page.evaluate(async () => {
            try {
                const response = await fetch('/api/search/multi', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        mine_name: 'Eleonore Mine',
                        country: 'Canada',
                        model_ids: ['openrouter:deepseek-free'],
                        comprehensive_search: false
                    })
                });
                const data = await response.json();
                return { 
                    status: response.status, 
                    statusText: response.statusText,
                    data: data,
                    headers: Object.fromEntries(response.headers.entries())
                };
            } catch (error) {
                return { error: error.message, stack: error.stack };
            }
        });
        console.log('🔍 [SEARCH MULTI API]', JSON.stringify(searchMultiTest, null, 2));
        
        // 4. Frontend Form Test
        console.log('🔄 [TEST 4] Frontend form interaction...');
        
        // Mine-Name eingeben
        await page.fill('input[name="mine_name"]', 'Eleonore Mine');
        await page.fill('input[name="country"]', 'Canada');
        
        // Model auswählen (erstes verfügbares)
        const firstModelExists = await page.locator('input[name="model"]:first-child').isVisible();
        if (firstModelExists) {
            await page.check('input[name="model"]:first-child');
            console.log('✅ [FORM] First model selected');
        } else {
            console.log('❌ [FORM] No models available');
        }
        
        await page.screenshot({ path: 'debug_02_form_filled.png' });
        
        // 5. Search-Button Click Test
        console.log('🔄 [TEST 5] Search button click test...');
        
        const searchButtonExists = await page.locator('#start-search').isVisible();
        console.log(`🎯 [SEARCH BUTTON] Exists: ${searchButtonExists}`);
        
        if (searchButtonExists) {
            // Click und Response verfolgen
            const [response] = await Promise.all([
                page.waitForResponse(response => 
                    response.url().includes('/api/search') && 
                    response.request().method() === 'POST',
                    { timeout: 10000 }
                ).catch(() => null),
                page.click('#start-search')
            ]);
            
            if (response) {
                const responseBody = await response.json().catch(() => 'Unable to parse JSON');
                console.log('🎯 [SEARCH RESPONSE]', {
                    status: response.status(),
                    statusText: response.statusText(),
                    url: response.url(),
                    body: responseBody
                });
            } else {
                console.log('❌ [SEARCH RESPONSE] No response received within timeout');
            }
            
            await page.waitForTimeout(5000);
            await page.screenshot({ path: 'debug_03_after_search_click.png' });
        }
        
        // 6. JavaScript-Error-Check
        const jsErrors = await page.evaluate(() => {
            return window.jsErrors || [];
        });
        console.log('🚨 [JS ERRORS]', jsErrors);
        
        // 7. Network-Logs analysieren
        console.log('📊 [NETWORK ANALYSIS] Check completed');
        
    } catch (error) {
        console.error('💥 [CRITICAL ERROR]', error);
        await page.screenshot({ path: 'debug_error.png' });
    }
    
    await browser.close();
    console.log('🏁 [EMERGENCY DEBUG] Analysis completed');
}

emergencySearchDebug().catch(console.error);