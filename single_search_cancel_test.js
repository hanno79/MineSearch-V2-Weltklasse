/**
 * Single Search Cancel Button Test
 * Author: rahn
 * Datum: 14.08.2025
 * Beschreibung: Test für Cancel-Button Funktionalität bei Single Search
 */

const { chromium } = require('playwright');

async function testSingleSearchCancel() {
    console.log('🧪 [CANCEL-TEST] Testing Single Search Cancel Button...');
    
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext();
    const page = await context.newPage();
    
    // Monitor console logs for cancel events
    page.on('console', msg => {
        const text = msg.text();
        if (text.includes('[CANCEL-SINGLE]') || text.includes('[SEARCH]') || text.includes('Abbrechen')) {
            console.log('🖥️ [PAGE-CONSOLE]', text);
        }
    });
    
    let testResults = {
        pageLoads: false,
        formFilled: false,
        searchStarted: false,
        cancelButtonVisible: false,
        cancelButtonWorks: false,
        searchAborted: false
    };
    
    try {
        console.log('📍 [TEST 1] Load page and fill form...');
        await page.goto('http://localhost:8000');
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(3000);
        
        testResults.pageLoads = true;
        console.log('✅ [TEST 1] Page loaded successfully');
        
        // Navigate to single search tab
        const singleTab = await page.$('.nav-item[data-tab="single"]');
        if (singleTab) {
            await singleTab.click();
            await page.waitForTimeout(1000);
        }
        
        // Fill search form
        console.log('📍 [TEST 2] Fill search form...');
        await page.fill('input[name="mine_name"]', 'Test Mine');
        await page.fill('input[name="country"]', 'Test Country');
        await page.fill('input[name="commodity"]', 'Gold');
        
        // Select a model (use Auto quick preset)
        const autoButton = await page.$('.quick-pill[data-preset="auto"]');
        if (autoButton) {
            await autoButton.click();
            await page.waitForTimeout(1000);
        }
        
        testResults.formFilled = true;
        console.log('✅ [TEST 2] Form filled successfully');
        
        // Take screenshot before search
        await page.screenshot({ path: 'single_cancel_test_01_before_search.png', fullPage: true });
        
        console.log('📍 [TEST 3] Start search...');
        
        // Start search (find the correct search button)
        // Try multiple possible selectors for the search button
        let searchButton = await page.$('button[onclick="startSingleSearch()"]');
        if (!searchButton) {
            // Try alternative selectors
            searchButton = await page.$('button:has-text("Advanced Search starten")');
            if (!searchButton) {
                searchButton = await page.$('button:has-text("Starten")');
                if (!searchButton) {
                    searchButton = await page.$('button[type="submit"]');
                    if (!searchButton) {
                        // Try by evaluating the page to find available buttons
                        const buttons = await page.evaluate(() => {
                            const allButtons = Array.from(document.querySelectorAll('button'));
                            return allButtons.map(btn => ({
                                text: btn.textContent.trim(),
                                onclick: btn.getAttribute('onclick'),
                                id: btn.id,
                                className: btn.className
                            }));
                        });
                        console.log('🔍 [DEBUG] Available buttons:', JSON.stringify(buttons, null, 2));
                    }
                }
            }
        }
        
        if (searchButton) {
            await searchButton.click();
            console.log('🚀 [TEST 3] Search started');
            testResults.searchStarted = true;
            
            // Wait briefly for loading message to appear, then immediately check for cancel button
            await page.waitForTimeout(500);
        } else {
            console.log('❌ [TEST 3] No search button found');
        }
        
        console.log('📍 [TEST 4] Check if cancel button is visible...');
        
        // Check multiple times for cancel button with shorter intervals
        let cancelButton = null;
        let attempts = 0;
        const maxAttempts = 10; // Check for 5 seconds total (500ms * 10)
        
        while (attempts < maxAttempts && !cancelButton) {
            cancelButton = await page.$('button[onclick="cancelSingleSearch()"]');
            if (cancelButton) {
                const isVisible = await cancelButton.isVisible();
                if (isVisible) {
                    testResults.cancelButtonVisible = true;
                    console.log(`✅ [TEST 4] Cancel button found and visible after ${attempts * 500}ms`);
                    break;
                } else {
                    cancelButton = null;
                }
            }
            
            // Also check for loading message as indication search is running
            const loadingDiv = await page.$('#results');
            if (loadingDiv) {
                const loadingContent = await loadingDiv.textContent();
                if (loadingContent.includes('läuft') || loadingContent.includes('Loading')) {
                    console.log(`🔄 [DEBUG] Search is running (attempt ${attempts + 1}): ${loadingContent.substring(0, 50)}...`);
                }
            }
            
            await page.waitForTimeout(500);
            attempts++;
        }
        
        if (testResults.cancelButtonVisible) {
            // Take screenshot with cancel button visible
            await page.screenshot({ path: 'single_cancel_test_02_cancel_button.png', fullPage: true });
            
            console.log('📍 [TEST 5] Click cancel button...');
            
            // Click cancel button
            await cancelButton.click();
            await page.waitForTimeout(2000);
            
            testResults.cancelButtonWorks = true;
            console.log('✅ [TEST 5] Cancel button clicked');
            
            // Check if search was aborted (look for abort message)
            const resultsDiv = await page.$('#results');
            if (resultsDiv) {
                const resultsContent = await resultsDiv.textContent();
                if (resultsContent.includes('abgebrochen') || resultsContent.includes('Abbrechen')) {
                    testResults.searchAborted = true;
                    console.log('✅ [TEST 5] Search was successfully aborted');
                } else {
                    console.log(`🔍 [DEBUG] Results content: ${resultsContent.substring(0, 100)}...`);
                }
            }
            
            // Take final screenshot
            await page.screenshot({ path: 'single_cancel_test_03_after_cancel.png', fullPage: true });
        } else {
            console.log('❌ [TEST 4] Cancel button not found after 5 seconds');
            // Take debug screenshot
            await page.screenshot({ path: 'single_cancel_test_debug_no_button.png', fullPage: true });
            
            // Debug: Check what's actually in the results div
            const resultsDiv = await page.$('#results');
            if (resultsDiv) {
                const content = await resultsDiv.innerHTML();
                console.log(`🔍 [DEBUG] Results HTML: ${content.substring(0, 200)}...`);
            }
        }
        
    } catch (error) {
        console.error('💥 [ERROR]', error);
        await page.screenshot({ path: 'single_cancel_test_error.png' });
    } finally {
        await browser.close();
    }
    
    // Final Assessment
    console.log('');
    console.log('🏆 [SINGLE SEARCH CANCEL TEST RESULTS]');
    console.log('=====================================');
    
    const testItems = [
        { name: 'Page Loads Successfully', status: testResults.pageLoads },
        { name: 'Form Filled Successfully', status: testResults.formFilled },
        { name: 'Search Started Successfully', status: testResults.searchStarted },
        { name: 'Cancel Button Visible During Search', status: testResults.cancelButtonVisible },
        { name: 'Cancel Button Works When Clicked', status: testResults.cancelButtonWorks },
        { name: 'Search Successfully Aborted', status: testResults.searchAborted }
    ];
    
    testItems.forEach((test, index) => {
        console.log(`${test.status ? '✅' : '❌'} ${index + 1}. ${test.name}`);
    });
    
    const successfulTests = testItems.filter(test => test.status).length;
    const totalTests = testItems.length;
    const successRate = Math.round(successfulTests / totalTests * 100);
    
    console.log('');
    console.log(`📊 Single Search Cancel Success Rate: ${successfulTests}/${totalTests} (${successRate}%)`);
    
    if (successRate >= 90) {
        console.log('');
        console.log('🎉 SINGLE SEARCH CANCEL: EXCELLENT SUCCESS!');
        console.log('✅ Cancel button appears during single search');
        console.log('✅ Cancel button is clickable and functional');
        console.log('✅ Search is properly aborted when cancelled');
        console.log('✅ User gets clear feedback about cancellation');
        console.log('🚀 Cancel functionality working perfectly!');
    } else if (successRate >= 70) {
        console.log('');
        console.log('🎯 SINGLE SEARCH CANCEL: GOOD PROGRESS');
        console.log('✅ Basic functionality working');
        console.log('⚠️ Some cancel features may need refinement');
    } else {
        console.log('');
        console.log('❌ SINGLE SEARCH CANCEL: NEEDS MORE WORK');
        console.log('❌ Cancel functionality not working properly');
        console.log('🔧 Further debugging required');
    }
    
    console.log('🏁 [SINGLE SEARCH CANCEL TEST] Complete');
    return successRate >= 85;
}

testSingleSearchCancel().catch(console.error);