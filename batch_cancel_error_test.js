/**
 * Batch Cancel Error Test
 * Author: rahn
 * Datum: 14.08.2025
 * Beschreibung: Test ob AbortError bei Batch Cancel gefixt ist
 */

const { chromium } = require('playwright');

async function testBatchCancelError() {
    console.log('🧪 [BATCH-CANCEL-ERROR-TEST] Testing Batch Search Cancel Error Fix...');
    
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext();
    const page = await context.newPage();
    
    // Monitor console logs to catch errors
    const consoleMessages = [];
    page.on('console', msg => {
        const message = msg.text();
        consoleMessages.push(message);
        console.log('🖥️ [PAGE-CONSOLE]', message);
    });
    
    try {
        console.log('📍 [STEP 1] Load page...');
        await page.goto('http://localhost:8000');
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(3000);
        
        console.log('📍 [STEP 2] Switch to CSV Upload tab...');
        await page.click('li[data-tab="csv"]');
        await page.waitForTimeout(1000);
        
        console.log('📍 [STEP 3] Upload test CSV...');
        // Create test CSV content
        const csvContent = `mine_name,country,commodity
Test Mine 1,Test Country,Gold
Test Mine 2,Test Country,Silver`;
        
        // Save CSV to temp file
        const fs = require('fs');
        const path = require('path');
        const tmpFilePath = path.join(__dirname, 'test_batch.csv');
        fs.writeFileSync(tmpFilePath, csvContent);
        
        // Upload file
        const fileInput = await page.$('input[type="file"]');
        if (fileInput) {
            await fileInput.setInputFiles(tmpFilePath);
            await page.waitForTimeout(2000);
            
            console.log('📍 [STEP 4] Start batch search...');
            const batchForm = await page.$('#batch-search-form');
            if (batchForm) {
                await batchForm.evaluate(form => form.submit());
                
                console.log('📍 [STEP 5] Wait briefly, then cancel...');
                await page.waitForTimeout(1500); // Wait for search to start
                
                // Look for cancel button
                const cancelButton = await page.$('button[onclick="cancelBatchSearch()"]');
                if (cancelButton && await cancelButton.isVisible()) {
                    console.log('✅ [STEP 5] Cancel button found, clicking...');
                    await cancelButton.click();
                    await page.waitForTimeout(2000);
                    
                    // Analyze console messages
                    console.log('\n📊 [ANALYSIS] Console Message Analysis:');
                    
                    const errorMessages = consoleMessages.filter(msg => 
                        msg.includes('❌ [BATCH-SEARCH] Error:') && 
                        msg.includes('AbortError')
                    );
                    
                    const abortLogMessages = consoleMessages.filter(msg => 
                        msg.includes('🛑 [BATCH-SEARCH] Batch search was aborted by user')
                    );
                    
                    const cancelMessages = consoleMessages.filter(msg => 
                        msg.includes('✅ [CANCEL-BATCH] Batch search aborted successfully')
                    );
                    
                    console.log(`  Error messages with AbortError: ${errorMessages.length}`);
                    console.log(`  Proper abort log messages: ${abortLogMessages.length}`);
                    console.log(`  Cancel success messages: ${cancelMessages.length}`);
                    
                    if (errorMessages.length === 0) {
                        console.log('✅ [SUCCESS] No AbortError console errors found!');
                    } else {
                        console.log('❌ [FAILURE] AbortError console errors still present:');
                        errorMessages.forEach(msg => console.log(`    ${msg}`));
                    }
                    
                    if (abortLogMessages.length > 0) {
                        console.log('✅ [SUCCESS] Proper abort logging found');
                    } else {
                        console.log('❌ [FAILURE] No proper abort logging');
                    }
                    
                    const testSuccess = errorMessages.length === 0 && abortLogMessages.length > 0;
                    console.log(`\n🏆 [TEST RESULT] ${testSuccess ? 'PASSED' : 'FAILED'}`);
                    
                } else {
                    console.log('❌ [STEP 5] Cancel button not found or not visible');
                }
            } else {
                console.log('❌ [STEP 4] Batch search form not found');
            }
        } else {
            console.log('❌ [STEP 3] File input not found');
        }
        
        // Cleanup
        if (fs.existsSync(tmpFilePath)) {
            fs.unlinkSync(tmpFilePath);
        }
        
    } catch (error) {
        console.error('💥 [ERROR]', error);
    } finally {
        await browser.close();
    }
}

testBatchCancelError().catch(console.error);