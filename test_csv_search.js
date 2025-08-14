/**
 * Test CSV Search - Phase 3.2 Validation
 * Author: rahn
 * Datum: 13.08.2025
 * Beschreibung: Test CSV batch search functionality
 */

const { chromium } = require('playwright');
const fs = require('fs');

async function testCSVSearch() {
    console.log('📊 [CSV TEST] Testing CSV batch search...');
    
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
        if (request.url().includes('/api/search/batch')) {
            console.log(`📡 [SUCCESS] CSV API CALL MADE: ${request.method()} ${request.url()}`);
        }
    });
    
    try {
        // Load page
        console.log('📋 [TEST] Loading page...');
        await page.goto('http://localhost:8000');
        await page.waitForLoadState('networkidle');
        
        // Switch to CSV tab
        console.log('📋 [TEST] Switching to CSV tab...');
        await page.check('#csv-tab');
        await page.waitForTimeout(2000);
        
        // Check if CSV form is visible
        const csvFormVisible = await page.locator('#csv-form').isVisible();
        console.log(`📋 [CSV FORM] Visible: ${csvFormVisible}`);
        
        if (csvFormVisible) {
            // Create test CSV
            const testCSV = `mine_name,country,commodity,region
Test Mine 1,Canada,Gold,Quebec
Test Mine 2,USA,Copper,Nevada`;
            
            const tmpCSVPath = '/tmp/test_mines.csv';
            fs.writeFileSync(tmpCSVPath, testCSV);
            console.log('📄 [CSV] Test CSV file created');
            
            // Upload CSV file
            await page.setInputFiles('#csv_file', tmpCSVPath);
            console.log('📤 [CSV] File uploaded');
            
            await page.waitForTimeout(1000);
            
            // Click batch search button
            console.log('📋 [TEST] Clicking batch search button...');
            
            let csvSearchSuccess = false;
            try {
                // Wait for batch API response
                const [response] = await Promise.all([
                    page.waitForResponse(response => 
                        response.url().includes('/api/search/batch') && 
                        response.request().method() === 'POST',
                        { timeout: 8000 }
                    ),
                    page.click('#start-batch')
                ]);
                
                console.log(`✅ [SUCCESS] CSV API call made! Status: ${response.status()}`);
                csvSearchSuccess = true;
                
            } catch (error) {
                console.log(`❌ [FAILED] No CSV API call: ${error.message}`);
            }
            
            await page.screenshot({ path: 'csv_search_test_result.png' });
            
            if (csvSearchSuccess) {
                console.log('🎉 [CSV FIXED] CSV batch search working!');
            } else {
                console.log('❌ [CSV BROKEN] CSV search still has issues');
            }
        } else {
            console.log('❌ [CSV FORM] CSV form not visible after tab switch');
        }
        
        await page.waitForTimeout(5000);
        
    } catch (error) {
        console.error('💥 [ERROR]', error);
        await page.screenshot({ path: 'csv_search_test_error.png' });
    }
    
    await browser.close();
}

testCSVSearch().catch(console.error);