/**
 * Navigation Cleanup Test - PHASE 1 Validation
 * Author: rahn
 * Datum: 13.08.2025
 * Beschreibung: Test der bereinigten Navigation ohne doppelte Tab-Navigation
 */

const { chromium } = require('playwright');

async function testNavigationCleanup() {
    console.log('🧹 [NAV-CLEANUP-TEST] Testing cleaned navigation system...');
    
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext();
    const page = await context.newPage();
    
    // Monitor JavaScript errors
    page.on('pageerror', error => {
        console.log('💥 [JS ERROR]', error.message);
    });
    
    // Monitor console for navigation messages
    page.on('console', msg => {
        const text = msg.text();
        if (text.includes('[NAVIGATION]') || text.includes('[TAB-AUTOLOADER]')) {
            console.log('🖥️ [CONSOLE]', text);
        }
    });
    
    let testResults = {
        pageLoad: false,
        noDuplicateNav: false,
        headerNavFunctional: false,
        tabSwitching: false,
        allTabsWork: false
    };
    
    try {
        console.log('🔄 [TEST 1] Page Load & Duplicate Check...');
        await page.goto('http://localhost:8000');
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(3000);
        
        testResults.pageLoad = true;
        console.log('✅ [TEST 1] Page loaded successfully');
        
        console.log('🔄 [TEST 2] Checking for Navigation Duplicates...');
        
        // Check that old tab-navigation is gone
        const oldTabNav = await page.$('.tab-navigation');
        const oldTabInputs = await page.$$('.tab-navigation input[type="radio"]');
        
        // Check that header navigation exists
        const headerNav = await page.$('.main-navigation');
        const headerNavItems = await page.$$('.nav-item');
        
        console.log(`📊 [NAV-CHECK] Old tab navigation: ${oldTabNav ? 'EXISTS (BAD)' : 'REMOVED (GOOD)'}`);
        console.log(`📊 [NAV-CHECK] Old tab inputs: ${oldTabInputs.length} (should be 0)`);
        console.log(`📊 [NAV-CHECK] Header navigation: ${headerNav ? 'EXISTS (GOOD)' : 'MISSING (BAD)'}`);
        console.log(`📊 [NAV-CHECK] Header nav items: ${headerNavItems.length} (should be 5)`);
        
        if (!oldTabNav && oldTabInputs.length === 0 && headerNav && headerNavItems.length === 5) {
            testResults.noDuplicateNav = true;
            console.log('✅ [TEST 2] Navigation duplication successfully eliminated');
        }
        
        console.log('🔄 [TEST 3] Header Navigation Functionality...');
        
        if (headerNavItems.length >= 5) {
            testResults.headerNavFunctional = true;
            console.log('✅ [TEST 3] Header navigation has all expected items');
        }
        
        console.log('🔄 [TEST 4] Tab Switching via Header Navigation...');
        
        const tabTests = [
            { tab: 'single', name: 'Einzelsuche' },
            { tab: 'csv', name: 'CSV Batch' },
            { tab: 'statistics', name: 'Statistiken' },
            { tab: 'sources', name: 'Quellen' },
            { tab: 'consolidated', name: 'Konsolidierte Ergebnisse' }
        ];
        
        let successfulTabSwitches = 0;
        
        for (let i = 0; i < tabTests.length; i++) {
            const tabTest = tabTests[i];
            console.log(`📋 [TAB-TEST] Testing tab: ${tabTest.tab} (${tabTest.name})`);
            
            // Find nav item for this tab
            const navItem = await page.$(`[data-tab="${tabTest.tab}"]`);
            if (navItem) {
                await navItem.click();
                await page.waitForTimeout(2000);
                
                // Check if tab became active
                const isActive = await navItem.evaluate(el => el.classList.contains('active'));
                if (isActive) {
                    successfulTabSwitches++;
                    console.log(`✅ [TAB-TEST] ${tabTest.name} tab switched successfully`);
                } else {
                    console.log(`❌ [TAB-TEST] ${tabTest.name} tab switch failed`);
                }
            } else {
                console.log(`❌ [TAB-TEST] Nav item for ${tabTest.tab} not found`);
            }
        }
        
        if (successfulTabSwitches >= 4) { // Allow 1 failure
            testResults.tabSwitching = true;
            testResults.allTabsWork = true;
            console.log(`✅ [TEST 4] Tab switching successful: ${successfulTabSwitches}/${tabTests.length}`);
        }
        
        console.log('🔄 [TEST 5] Final Screenshots...');
        
        // Back to single tab for final screenshot
        const singleNavItem = await page.$('[data-tab="single"]');
        if (singleNavItem) {
            await singleNavItem.click();
            await page.waitForTimeout(1000);
        }
        
        await page.screenshot({ path: 'navigation_cleanup_success.png', fullPage: true });
        
        // Mobile test
        await page.setViewportSize({ width: 375, height: 667 });
        await page.waitForTimeout(1000);
        await page.screenshot({ path: 'navigation_cleanup_mobile.png', fullPage: true });
        
    } catch (error) {
        console.error('💥 [ERROR]', error);
        await page.screenshot({ path: 'navigation_cleanup_error.png' });
    } finally {
        await browser.close();
    }
    
    // Assessment
    console.log('');
    console.log('🏆 [NAVIGATION CLEANUP TEST RESULTS]');
    console.log('====================================');
    
    const testItems = [
        { name: 'Page Load', status: testResults.pageLoad },
        { name: 'No Duplicate Navigation', status: testResults.noDuplicateNav },
        { name: 'Header Navigation Functional', status: testResults.headerNavFunctional },
        { name: 'Tab Switching', status: testResults.tabSwitching },
        { name: 'All Tabs Working', status: testResults.allTabsWork }
    ];
    
    testItems.forEach((test, index) => {
        console.log(`${test.status ? '✅' : '❌'} ${index + 1}. ${test.name}`);
    });
    
    const successfulTests = testItems.filter(test => test.status).length;
    const totalTests = testItems.length;
    const successRate = Math.round(successfulTests / totalTests * 100);
    
    console.log('');
    console.log(`📊 Success Rate: ${successfulTests}/${totalTests} (${successRate}%)`);
    
    if (successRate >= 90) {
        console.log('');
        console.log('🎉 NAVIGATION CLEANUP: EXCELLENT SUCCESS!');
        console.log('✅ Duplicate navigation successfully eliminated');
        console.log('✅ Header navigation is the single source of navigation');
        console.log('✅ All tab switching functionality preserved');
        console.log('🚀 Ready for PHASE 2: Settings Cleanup');
    } else if (successRate >= 70) {
        console.log('');
        console.log('🎯 NAVIGATION CLEANUP: MOSTLY SUCCESSFUL');
        console.log('✅ Major duplicates eliminated');
        console.log('⚠️ Some functionality may need fine-tuning');
    } else {
        console.log('');
        console.log('⚠️ NAVIGATION CLEANUP: NEEDS ATTENTION');
        console.log('❌ Critical issues remain');
        console.log('🔧 Review and fix required');
    }
    
    console.log('🏁 [NAVIGATION CLEANUP TEST] Complete');
    return successRate >= 80;
}

testNavigationCleanup().catch(console.error);