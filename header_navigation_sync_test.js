/**
 * Header Navigation Synchronisation Test
 * Author: rahn
 * Datum: 14.08.2025
 * Beschreibung: Test für korrekte Header-Navigation nach Hard Reload
 */

const { chromium } = require('playwright');

async function testHeaderNavigationSync() {
    console.log('🧪 [HEADER-SYNC-TEST] Testing header navigation synchronization after hard reload...');
    
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext();
    const page = await context.newPage();
    
    // Monitor console logs for navigation events
    page.on('console', msg => {
        const text = msg.text();
        if (text.includes('[NAVIGATION]') || text.includes('[TAB-AUTOLOADER]') || text.includes('[SYNC]')) {
            console.log('🖥️ [PAGE-CONSOLE]', text);
        }
    });
    
    let testResults = {
        pageLoads: false,
        headerShowsSingle: false,
        contentShowsSingle: false,
        synchronizedAfterReload: false,
        noDoubleClickNeeded: false
    };
    
    try {
        console.log('📍 [TEST 1] Initial page load...');
        await page.goto('http://localhost:8000');
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(3000); // Wait for all initialization
        
        testResults.pageLoads = true;
        console.log('✅ [TEST 1] Page loaded successfully');
        
        console.log('📍 [TEST 2] Check initial state...');
        
        // Check header navigation - should show "Suche" as active
        const activeNavItem = await page.$('.nav-item.active');
        const activeNavText = activeNavItem ? await activeNavItem.textContent() : 'NOT_FOUND';
        const activeNavDataTab = activeNavItem ? await activeNavItem.getAttribute('data-tab') : 'NOT_FOUND';
        
        console.log(`📊 [HEADER] Active nav item text: "${activeNavText}"`);
        console.log(`📊 [HEADER] Active nav item data-tab: "${activeNavDataTab}"`);
        
        if (activeNavDataTab === 'single' && activeNavText.includes('Suche')) {
            testResults.headerShowsSingle = true;
            console.log('✅ [TEST 2] Header correctly shows "Suche" as active');
        } else {
            console.log('❌ [TEST 2] Header does not show "Suche" as active');
        }
        
        // Check content visibility - should show single search form
        const singleContent = await page.$('#single-search.active');
        const csvContent = await page.$('#csv-upload.active');
        
        console.log(`📊 [CONTENT] Single search content active: ${singleContent ? 'YES' : 'NO'}`);
        console.log(`📊 [CONTENT] CSV content active: ${csvContent ? 'YES' : 'NO'}`);
        
        if (singleContent && !csvContent) {
            testResults.contentShowsSingle = true;
            console.log('✅ [TEST 2] Content correctly shows single search');
        } else {
            console.log('❌ [TEST 2] Content does not show single search correctly');
        }
        
        // Screenshot initial state
        await page.screenshot({ path: 'header_sync_initial.png', fullPage: true });
        
        console.log('📍 [TEST 3] Performing hard reload...');
        
        // Perform hard reload to test synchronization
        await page.reload({ waitUntil: 'networkidle' });
        await page.waitForTimeout(3000); // Wait for initialization after reload
        
        console.log('📍 [TEST 4] Check state after hard reload...');
        
        // Re-check header state after reload
        const afterReloadNavItem = await page.$('.nav-item.active');
        const afterReloadNavText = afterReloadNavItem ? await afterReloadNavItem.textContent() : 'NOT_FOUND';
        const afterReloadNavDataTab = afterReloadNavItem ? await afterReloadNavItem.getAttribute('data-tab') : 'NOT_FOUND';
        
        console.log(`📊 [AFTER-RELOAD] Active nav item text: "${afterReloadNavText}"`);
        console.log(`📊 [AFTER-RELOAD] Active nav item data-tab: "${afterReloadNavDataTab}"`);
        
        // Re-check content state after reload
        const afterReloadSingleContent = await page.$('#single-search.active');
        const afterReloadCsvContent = await page.$('#csv-upload.active');
        
        console.log(`📊 [AFTER-RELOAD] Single search content active: ${afterReloadSingleContent ? 'YES' : 'NO'}`);
        console.log(`📊 [AFTER-RELOAD] CSV content active: ${afterReloadCsvContent ? 'YES' : 'NO'}`);
        
        // Check if both header and content are synchronized correctly
        if (afterReloadNavDataTab === 'single' && afterReloadSingleContent && !afterReloadCsvContent) {
            testResults.synchronizedAfterReload = true;
            console.log('✅ [TEST 4] Header and content are synchronized after reload');
        } else {
            console.log('❌ [TEST 4] Header and content are NOT synchronized after reload');
        }
        
        console.log('📍 [TEST 5] Test direct tab switching...');
        
        // Test if switching to CSV and back works correctly
        const csvNavItem = await page.$('.nav-item[data-tab="csv"]');
        if (csvNavItem) {
            await csvNavItem.click();
            await page.waitForTimeout(2000);
            
            // Check if CSV tab is now active
            const csvActive = await page.$('.nav-item[data-tab="csv"].active');
            const csvContentActive = await page.$('#csv-upload.active');
            
            console.log(`📊 [CSV-SWITCH] CSV nav active: ${csvActive ? 'YES' : 'NO'}`);
            console.log(`📊 [CSV-SWITCH] CSV content active: ${csvContentActive ? 'YES' : 'NO'}`);
            
            // Switch back to single
            const singleNavItem = await page.$('.nav-item[data-tab="single"]');
            if (singleNavItem) {
                await singleNavItem.click();
                await page.waitForTimeout(2000);
                
                // Check if single tab is active again
                const backToSingleNav = await page.$('.nav-item[data-tab="single"].active');
                const backToSingleContent = await page.$('#single-search.active');
                
                if (backToSingleNav && backToSingleContent) {
                    testResults.noDoubleClickNeeded = true;
                    console.log('✅ [TEST 5] Tab switching works with single click');
                } else {
                    console.log('❌ [TEST 5] Tab switching requires multiple clicks');
                }
            }
        }
        
        // Final screenshot
        await page.screenshot({ path: 'header_sync_final.png', fullPage: true });
        
    } catch (error) {
        console.error('💥 [ERROR]', error);
        await page.screenshot({ path: 'header_sync_error.png' });
    } finally {
        await browser.close();
    }
    
    // Final Assessment
    console.log('');
    console.log('🏆 [HEADER NAVIGATION SYNC TEST RESULTS]');
    console.log('==========================================');
    
    const testItems = [
        { name: 'Page Loads Successfully', status: testResults.pageLoads },
        { name: 'Header Shows Single Tab Initially', status: testResults.headerShowsSingle },
        { name: 'Content Shows Single Search Initially', status: testResults.contentShowsSingle },
        { name: 'Synchronized After Hard Reload', status: testResults.synchronizedAfterReload },
        { name: 'No Double Click Needed', status: testResults.noDoubleClickNeeded }
    ];
    
    testItems.forEach((test, index) => {
        console.log(`${test.status ? '✅' : '❌'} ${index + 1}. ${test.name}`);
    });
    
    const successfulTests = testItems.filter(test => test.status).length;
    const totalTests = testItems.length;
    const successRate = Math.round(successfulTests / totalTests * 100);
    
    console.log('');
    console.log(`📊 Header Navigation Sync Success Rate: ${successfulTests}/${totalTests} (${successRate}%)`);
    
    if (successRate >= 90) {
        console.log('');
        console.log('🎉 HEADER NAVIGATION SYNC: EXCELLENT SUCCESS!');
        console.log('✅ Header correctly shows "Suche" after hard reload');
        console.log('✅ Single search content is displayed correctly');
        console.log('✅ No more synchronization issues');
        console.log('✅ Tab switching works with single click');
        console.log('🚀 Problem fixed - header and content are synchronized!');
    } else if (successRate >= 70) {
        console.log('');
        console.log('🎯 HEADER NAVIGATION SYNC: GOOD PROGRESS');
        console.log('✅ Basic functionality working');
        console.log('⚠️ Some synchronization issues may remain');
    } else {
        console.log('');
        console.log('❌ HEADER NAVIGATION SYNC: NEEDS MORE WORK');
        console.log('❌ Synchronization issues still present');
        console.log('🔧 Further debugging required');
    }
    
    console.log('🏁 [HEADER NAVIGATION SYNC TEST] Complete');
    return successRate >= 85;
}

testHeaderNavigationSync().catch(console.error);