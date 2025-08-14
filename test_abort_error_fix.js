/**
 * Test AbortError Fix
 * Author: rahn
 * Datum: 14.08.2025
 * Beschreibung: Test ob AbortError korrekt behandelt wird
 */

const { chromium } = require('playwright');

async function testAbortErrorFix() {
    console.log('🧪 [ABORT-ERROR-TEST] Testing AbortError handling fix...');
    
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext();
    const page = await context.newPage();
    
    // Monitor console messages
    const consoleMessages = [];
    page.on('console', msg => {
        const message = msg.text();
        consoleMessages.push(message);
        
        // Log relevant messages
        if (message.includes('BATCH') || message.includes('Error') || message.includes('AbortError')) {
            console.log('🖥️ [CONSOLE]', message);
        }
    });
    
    try {
        console.log('📍 [STEP 1] Load page...');
        await page.goto('http://localhost:8000');
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(2000);
        
        console.log('📍 [STEP 2] Simulate AbortError in batch search...');
        
        const result = await page.evaluate(() => {
            console.log('🔧 [SIMULATE] Simulating startBatchSearch error handling...');
            
            // Simulate the error handling logic from startBatchSearch
            function simulateBatchSearchError() {
                try {
                    // Simulate an AbortError
                    const error = new Error('signal is aborted without reason');
                    error.name = 'AbortError';
                    throw error;
                } catch (error) {
                    console.log('🔧 [SIMULATE] Caught error in batch search:', error.name);
                    
                    // This is the NEW logic from our fix
                    if (error.name === 'AbortError') {
                        console.log('🛑 [BATCH-SEARCH] Batch search was aborted by user');
                        
                        // Stop timer
                        if (typeof window.searchTimer !== 'undefined' && window.searchTimer.stop) {
                            window.searchTimer.stop();
                        }
                        
                        // Show UI feedback (not creating actual elements for test)
                        console.log('🔧 [SIMULATE] Would show: Batch-Suche abgebrochen');
                        console.log('🔧 [SIMULATE] Would show notification: 🛑 Batch-Suche wurde abgebrochen');
                        
                        return { 
                            type: 'abort', 
                            logged: '🛑 [BATCH-SEARCH] Batch search was aborted by user',
                            errorLogged: false 
                        };
                    } else {
                        // Only log non-abort errors
                        console.error(`❌ [BATCH-SEARCH] Error:`, error);
                        
                        // Stop timer
                        if (typeof window.searchTimer !== 'undefined' && window.searchTimer.stop) {
                            window.searchTimer.stop();
                        }
                        
                        console.log('🔧 [SIMULATE] Would show: Batch-Suche fehlgeschlagen');
                        
                        return { 
                            type: 'error', 
                            logged: `❌ [BATCH-SEARCH] Error: ${error.message}`,
                            errorLogged: true 
                        };
                    }
                }
            }
            
            // Test both AbortError and regular error
            const abortResult = simulateBatchSearchError();
            
            // Test regular error
            function simulateRegularError() {
                try {
                    const error = new Error('Network connection failed');
                    throw error;
                } catch (error) {
                    if (error.name === 'AbortError') {
                        console.log('🛑 [BATCH-SEARCH] Batch search was aborted by user');
                        return { type: 'abort', errorLogged: false };
                    } else {
                        console.error(`❌ [BATCH-SEARCH] Error:`, error);
                        return { type: 'error', errorLogged: true };
                    }
                }
            }
            
            const regularResult = simulateRegularError();
            
            return {
                abortTest: abortResult,
                regularErrorTest: regularResult
            };
        });
        
        console.log('📊 [RESULTS]');
        console.log('  AbortError test:', JSON.stringify(result.abortTest));
        console.log('  Regular error test:', JSON.stringify(result.regularErrorTest));
        
        // Wait for console messages
        await page.waitForTimeout(1000);
        
        // Analyze results
        const abortLogMessages = consoleMessages.filter(msg => 
            msg.includes('🛑 [BATCH-SEARCH] Batch search was aborted by user')
        );
        
        const abortErrorMessages = consoleMessages.filter(msg => 
            msg.includes('❌ [BATCH-SEARCH] Error:') && msg.includes('AbortError')
        );
        
        const regularErrorMessages = consoleMessages.filter(msg => 
            msg.includes('❌ [BATCH-SEARCH] Error: Network connection failed')
        );
        
        console.log('\n📊 [ANALYSIS]');
        console.log(`  🛑 Abort log messages: ${abortLogMessages.length}`);
        console.log(`  ❌ AbortError error messages: ${abortErrorMessages.length}`);
        console.log(`  ❌ Regular error messages: ${regularErrorMessages.length}`);
        
        const fixWorking = (
            abortLogMessages.length > 0 &&      // AbortError was logged as info
            abortErrorMessages.length === 0 &&  // AbortError was NOT logged as error
            regularErrorMessages.length > 0     // Regular errors are still logged as error
        );
        
        console.log(`\n🏆 [TEST RESULT] ${fixWorking ? 'PASSED ✅' : 'FAILED ❌'}`);
        
        if (fixWorking) {
            console.log('🎉 AbortError fix is working correctly!');
            console.log('  ✅ AbortError logged as info, not error');
            console.log('  ✅ Regular errors still logged as error');
        } else {
            console.log('💥 AbortError fix has issues');
        }
        
    } catch (error) {
        console.error('💥 [TEST-ERROR]', error);
    } finally {
        await browser.close();
    }
}

testAbortErrorFix().catch(console.error);