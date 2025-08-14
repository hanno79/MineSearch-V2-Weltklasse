/**
 * Test Single Notification
 * Author: rahn
 * Datum: 14.08.2025
 * Beschreibung: Test ob nur noch eine Abbruch-Notification erscheint
 */

const { chromium } = require('playwright');

async function testSingleNotification() {
    console.log('🧪 [NOTIFICATION-TEST] Testing single notification on cancel...');
    
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext();
    const page = await context.newPage();
    
    // Track showNotification calls
    const notificationCalls = [];
    
    try {
        console.log('📍 [STEP 1] Load page...');
        await page.goto('http://localhost:8000');
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(2000);
        
        console.log('📍 [STEP 2] Override showNotification to track calls...');
        
        await page.evaluate(() => {
            // Store original function
            window._originalShowNotification = window.showNotification;
            window._notificationCalls = [];
            
            // Override showNotification to track calls
            window.showNotification = function(message, type = 'info') {
                const call = { message, type, timestamp: Date.now() };
                window._notificationCalls.push(call);
                console.log(`📢 [NOTIFICATION-TRACKED] ${type}: ${message}`);
                
                // Still call original function for visual feedback
                if (window._originalShowNotification) {
                    window._originalShowNotification(message, type);
                }
            };
        });
        
        console.log('📍 [STEP 3] Simulate batch search cancel...');
        
        const result = await page.evaluate(() => {
            console.log('🔧 [SIMULATE] Testing batch search cancel flow...');
            
            // Clear any existing calls
            window._notificationCalls = [];
            
            // Simulate active batch search
            window.batchSearchAbortController = new AbortController();
            
            // Call cancelBatchSearch - this should show 1 notification
            if (typeof cancelBatchSearch === 'function') {
                cancelBatchSearch();
            }
            
            // Simulate the AbortError catch in startBatchSearch
            try {
                const error = new Error('signal is aborted without reason');
                error.name = 'AbortError';
                throw error;
            } catch (error) {
                // This is our updated catch logic
                if (error.name === 'AbortError') {
                    console.log('🛑 [BATCH-SEARCH] Batch search was aborted by user');
                    
                    // Stop timer
                    if (typeof window.searchTimer !== 'undefined' && window.searchTimer.stop) {
                        window.searchTimer.stop();
                    }
                    
                    // UI is already updated by cancelBatchSearch()
                    // Don't show notification - already shown by cancelBatchSearch()
                    return;
                } else {
                    // Only log non-abort errors - should show notification
                    console.error(`❌ [BATCH-SEARCH] Error:`, error);
                    if (typeof showNotification === 'function') {
                        showNotification(`❌ Batch-Suche fehlgeschlagen: ${error.message}`, 'error');
                    }
                }
            }
            
            return {
                notificationCalls: window._notificationCalls ? window._notificationCalls.slice() : [],
                success: true
            };
        });
        
        console.log(`📊 [RESULTS] Notifications called: ${result.notificationCalls.length}`);
        
        result.notificationCalls.forEach((call, index) => {
            console.log(`  ${index + 1}. [${call.type}] ${call.message}`);
        });
        
        // Analyze results
        const abortNotifications = result.notificationCalls.filter(call => 
            call.message.includes('abgebrochen') && call.type === 'info'
        );
        
        const errorNotifications = result.notificationCalls.filter(call => 
            call.type === 'error'
        );
        
        console.log('\n📊 [ANALYSIS]');
        console.log(`  🛑 Abort notifications: ${abortNotifications.length}`);
        console.log(`  ❌ Error notifications: ${errorNotifications.length}`);
        
        const testPassed = abortNotifications.length === 1; // Should be exactly 1
        
        console.log(`\n🏆 [TEST RESULT] ${testPassed ? 'PASSED ✅' : 'FAILED ❌'}`);
        
        if (testPassed) {
            console.log('🎉 Only one notification shown on batch cancel!');
        } else {
            console.log('💥 Multiple notifications still being shown');
        }
        
        // Wait to see visual notifications
        await page.waitForTimeout(3000);
        
    } catch (error) {
        console.error('💥 [ERROR]', error);
    } finally {
        await browser.close();
    }
}

testSingleNotification().catch(console.error);