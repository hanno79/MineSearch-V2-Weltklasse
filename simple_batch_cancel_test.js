/**
 * Simple Batch Cancel Test
 * Author: rahn
 * Datum: 14.08.2025
 * Beschreibung: Einfacher Test ob AbortError-Fix funktioniert
 */

const { chromium } = require('playwright');

async function simpleBatchCancelTest() {
    console.log('🧪 [SIMPLE-BATCH-TEST] Testing if AbortError fix works...');
    
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext();
    const page = await context.newPage();
    
    // Monitor console for AbortError messages
    const consoleMessages = [];
    page.on('console', msg => {
        const message = msg.text();
        consoleMessages.push(message);
        
        // Log only relevant messages
        if (message.includes('BATCH') || message.includes('CANCEL') || message.includes('AbortError')) {
            console.log('🖥️ [RELEVANT]', message);
        }
    });
    
    try {
        console.log('📍 [STEP 1] Load page and navigate to CSV tab...');
        await page.goto('http://localhost:8000/#csv');
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(2000);
        
        console.log('📍 [STEP 2] Test batch cancel function directly...');
        
        // Test the batch cancel function directly in browser console
        const result = await page.evaluate(async () => {
            console.log('🧪 [DIRECT-TEST] Testing cancelBatchSearch() function directly...');
            
            // Simulate having an active batch search
            window.batchSearchAbortController = new AbortController();
            
            // Call the cancel function
            if (typeof cancelBatchSearch === 'function') {
                cancelBatchSearch();
                return {
                    success: true,
                    functionExists: true
                };
            } else {
                return {
                    success: false,
                    functionExists: false
                };
            }
        });
        
        console.log(`📊 [RESULT] Function test: ${JSON.stringify(result)}`);
        
        // Wait for console messages to settle
        await page.waitForTimeout(2000);
        
        // Analyze console messages for AbortError
        console.log('\n📊 [ANALYSIS] Console Message Analysis:');
        
        const abortErrorMessages = consoleMessages.filter(msg => 
            msg.includes('❌ [BATCH-SEARCH] Error:') && msg.includes('AbortError')
        );
        
        const properAbortMessages = consoleMessages.filter(msg => 
            msg.includes('🛑 [BATCH-SEARCH] Batch search was aborted by user') ||
            msg.includes('✅ [CANCEL-BATCH] Batch search aborted successfully')
        );
        
        console.log(`  ❌ AbortError messages: ${abortErrorMessages.length}`);
        console.log(`  ✅ Proper abort messages: ${properAbortMessages.length}`);
        
        if (abortErrorMessages.length > 0) {
            console.log('\n❌ [FOUND ERROR MESSAGES]:');
            abortErrorMessages.forEach(msg => console.log(`    ${msg}`));
        }
        
        if (properAbortMessages.length > 0) {
            console.log('\n✅ [FOUND PROPER MESSAGES]:');
            properAbortMessages.forEach(msg => console.log(`    ${msg}`));
        }
        
        const testPassed = abortErrorMessages.length === 0 && properAbortMessages.length > 0;
        
        console.log(`\n🏆 [TEST RESULT] ${testPassed ? 'PASSED ✅' : 'FAILED ❌'}`);
        
        if (testPassed) {
            console.log('🎉 AbortError fix is working correctly!');
        } else {
            console.log('💥 AbortError fix needs more work');
        }
        
    } catch (error) {
        console.error('💥 [ERROR]', error);
    } finally {
        await browser.close();
    }
}

simpleBatchCancelTest().catch(console.error);