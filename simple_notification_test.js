/**
 * Simple Notification Test
 * Author: rahn
 * Datum: 14.08.2025
 * Beschreibung: Einfacher Test für single notification
 */

const { chromium } = require('playwright');

async function simpleNotificationTest() {
    console.log('🧪 [SIMPLE-TEST] Testing notification behavior...');
    
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext();
    const page = await context.newPage();
    
    // Monitor notifications via DOM
    try {
        console.log('📍 [STEP 1] Load page...');
        await page.goto('http://localhost:8000');
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(2000);
        
        console.log('📍 [STEP 2] Call cancelBatchSearch directly...');
        
        await page.evaluate(() => {
            // Setup batch search controller
            window.batchSearchAbortController = new AbortController();
            
            // Call cancel function
            if (typeof cancelBatchSearch === 'function') {
                cancelBatchSearch();
            }
        });
        
        // Wait a moment for notifications to appear
        await page.waitForTimeout(2000);
        
        console.log('📍 [STEP 3] Count visible notifications...');
        
        // Count notification elements in DOM (they have specific styles)
        const notificationCount = await page.evaluate(() => {
            const notifications = document.querySelectorAll('[style*="position: fixed"][style*="top: 20px"][style*="right: 20px"]');
            console.log(`📊 Found ${notifications.length} notification elements`);
            
            // Also check if any contain abort text
            const abortNotifications = Array.from(notifications).filter(el => 
                el.textContent.includes('abgebrochen') || el.textContent.includes('abbrech')
            );
            
            console.log(`📊 Found ${abortNotifications.length} abort-related notifications`);
            
            return {
                total: notifications.length,
                abort: abortNotifications.length
            };
        });
        
        console.log(`📊 [RESULTS]`);
        console.log(`  Total notifications: ${notificationCount.total}`);
        console.log(`  Abort notifications: ${notificationCount.abort}`);
        
        const testPassed = notificationCount.abort <= 1; // Should be 0 or 1, not more
        
        console.log(`\n🏆 [TEST RESULT] ${testPassed ? 'PASSED ✅' : 'FAILED ❌'}`);
        
        if (testPassed) {
            console.log('🎉 No duplicate notifications detected!');
        } else {
            console.log('💥 Multiple notifications still visible');
        }
        
        // Take screenshot for visual confirmation
        await page.screenshot({ path: 'notification_test_result.png', fullPage: true });
        console.log('📷 Screenshot saved: notification_test_result.png');
        
        // Wait to see notifications
        await page.waitForTimeout(5000);
        
    } catch (error) {
        console.error('💥 [ERROR]', error);
    } finally {
        await browser.close();
    }
}

simpleNotificationTest().catch(console.error);