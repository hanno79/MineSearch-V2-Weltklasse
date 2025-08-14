/**
 * Advanced Search UX Test - Improved Timing Version
 * Author: rahn
 * Datum: 13.08.2025
 * Beschreibung: Test mit verbesserter Timing-Behandlung für Modal Model Loading
 */

const { chromium } = require('playwright');

async function testAdvancedSearchUXImproved() {
    console.log('🎯 [UX-TEST-IMPROVED] Testing Advanced Search UX improvements with better timing...');
    
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext();
    const page = await context.newPage();
    
    // Monitor console logs
    page.on('console', msg => {
        const text = msg.text();
        if (text.includes('[STATUS]') || text.includes('[SETTINGS-MODAL]') || text.includes('[SYNC]')) {
            console.log('🖥️ [CONSOLE]', text);
        }
    });
    
    let testResults = {
        settingsStatusVisible: false,
        settingsStatusUpdated: false,
        quickLinkWorks: false,
        modalModelsFixed: false,
        modelSyncWorks: false,
        uxImproved: false
    };
    
    try {
        console.log('🔄 [TEST 1] Page Load & Settings Status Check...');
        await page.goto('http://localhost:8000');
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(5000);
        
        // Check if settings status display exists
        const settingsStatus = await page.$('.search-settings-status');
        const settingsHeader = await page.$('.settings-status-header h4');
        const settingsGrid = await page.$('.settings-status-grid');
        const quickLink = await page.$('.settings-quick-link');
        
        console.log(`📊 [SETTINGS-STATUS] Container: ${settingsStatus ? 'EXISTS' : 'MISSING'}`);
        console.log(`📊 [SETTINGS-STATUS] Header: ${settingsHeader ? 'EXISTS' : 'MISSING'}`);
        console.log(`📊 [SETTINGS-STATUS] Grid: ${settingsGrid ? 'EXISTS' : 'MISSING'}`);
        console.log(`📊 [SETTINGS-STATUS] Quick link: ${quickLink ? 'EXISTS' : 'MISSING'}`);
        
        if (settingsStatus && settingsHeader && settingsGrid && quickLink) {
            testResults.settingsStatusVisible = true;
            console.log('✅ [TEST 1] Settings status display is visible');
        }
        
        console.log('🔄 [TEST 2] Settings Status Values Check...');
        
        // Check if status values are loaded (not "Lädt...")
        const status2Phase = await page.textContent('#status-2phase').catch(() => 'NOT_FOUND');
        const statusSmart = await page.textContent('#status-smart').catch(() => 'NOT_FOUND');
        const statusModels = await page.textContent('#status-models').catch(() => 'NOT_FOUND');
        
        console.log(`📊 [STATUS-VALUES] 2-Phase: "${status2Phase}"`);
        console.log(`📊 [STATUS-VALUES] Smart Search: "${statusSmart}"`);
        console.log(`📊 [STATUS-VALUES] Models: "${statusModels}"`);
        
        if (status2Phase !== 'Lädt...' && statusSmart !== 'Lädt...' && statusModels !== 'Lädt...') {
            testResults.settingsStatusUpdated = true;
            console.log('✅ [TEST 2] Settings status values are updated');
        }
        
        console.log('🔄 [TEST 3] Quick Link to Settings Modal...');
        
        if (quickLink) {
            await quickLink.click();
            await page.waitForTimeout(2000);
            
            const modalVisible = await page.$('#settings-modal[style*="block"]');
            console.log(`📊 [QUICK-LINK] Modal opened: ${modalVisible ? 'YES' : 'NO'}`);
            
            if (modalVisible) {
                testResults.quickLinkWorks = true;
                console.log('✅ [TEST 3] Quick link to settings modal works');
                
                console.log('🔄 [TEST 4] Settings Modal Model Loading (with extended wait)...');
                
                // Wait longer for models to load in modal
                console.log('⏳ [MODAL-LOADING] Waiting 8 seconds for models to load...');
                await page.waitForTimeout(8000);
                
                // Check if models are loaded in modal (not error message)
                const modalModelContent = await page.textContent('#modal-model-selection').catch(() => '');
                const hasErrorMessage = modalModelContent.includes('❌ Modelle konnten nicht geladen werden') || 
                                       modalModelContent.includes('⚠️ Hauptmodell-Container nicht gefunden');
                const hasModels = await page.$$('#modal-model-selection input[type="checkbox"]');
                
                console.log(`📊 [MODAL-MODELS] Error message: ${hasErrorMessage ? 'YES (BAD)' : 'NO (GOOD)'}`);
                console.log(`📊 [MODAL-MODELS] Model checkboxes: ${hasModels.length}`);
                console.log(`📊 [MODAL-MODELS] Modal content preview: "${modalModelContent.substring(0, 100)}..."`);
                
                if (!hasErrorMessage && hasModels.length > 50) { // Should have many models
                    testResults.modalModelsFixed = true;
                    console.log('✅ [TEST 4] Settings modal model loading is fixed');
                    
                    console.log('🔄 [TEST 5] Model Synchronization...');
                    
                    // Test model sync between main page and modal
                    if (hasModels.length > 0) {
                        try {
                            // Click a model in modal using JavaScript to avoid visibility issues
                            await page.evaluate(() => {
                                const checkbox = document.querySelector('#modal-model-selection input[type="checkbox"]');
                                if (checkbox) {
                                    checkbox.click();
                                    return true;
                                }
                                return false;
                            });
                            
                            await page.waitForTimeout(1000);
                            
                            // Check if main page model is also selected
                            const mainModels = await page.$$('#model-selection input[type="checkbox"]:checked');
                            console.log(`📊 [SYNC] Main page selected models after modal click: ${mainModels.length}`);
                            
                            if (mainModels.length > 0) {
                                testResults.modelSyncWorks = true;
                                console.log('✅ [TEST 5] Model synchronization works');
                            } else {
                                console.log('⚠️ [TEST 5] Model synchronization may need more time or different approach');
                            }
                        } catch (error) {
                            console.log('⚠️ [TEST 5] Model sync test encountered error:', error.message);
                        }
                    }
                } else if (hasModels.length > 0 && hasModels.length < 50) {
                    console.log(`⚠️ [MODAL-MODELS] Models found but less than expected: ${hasModels.length} (expected 50+)`);
                } else {
                    console.log('❌ [MODAL-MODELS] No models found or error messages present');
                }
                
                // Close modal
                const closeBtn = await page.$('#settings-modal .modal-close');
                if (closeBtn) await closeBtn.click();
                await page.waitForTimeout(1000);
            }
        }
        
        console.log('🔄 [TEST 6] Overall UX Improvement...');
        
        // Check improved comparison text
        const comparisonText = await page.textContent('.search-comparison-info').catch(() => '');
        const hasImprovedText = comparisonText.includes('erweiterte Einstellungen');
        const hasHelpTip = await page.$('.settings-help');
        
        console.log(`📊 [UX] Improved comparison text: ${hasImprovedText ? 'YES' : 'NO'}`);
        console.log(`📊 [UX] Help tip visible: ${hasHelpTip ? 'YES' : 'NO'}`);
        
        if (hasImprovedText && hasHelpTip) {
            testResults.uxImproved = true;
            console.log('✅ [TEST 6] Overall UX improvements are visible');
        }
        
        // Final screenshots
        await page.screenshot({ path: 'advanced_search_ux_improved_final.png', fullPage: true });
        
        // Test mobile view
        await page.setViewportSize({ width: 375, height: 667 });
        await page.waitForTimeout(1000);
        await page.screenshot({ path: 'advanced_search_mobile_ux_final.png', fullPage: true });
        
    } catch (error) {
        console.error('💥 [ERROR]', error);
        await page.screenshot({ path: 'advanced_search_ux_error_improved.png' });
    } finally {
        await browser.close();
    }
    
    // Final Assessment
    console.log('');
    console.log('🏆 [ADVANCED SEARCH UX TEST RESULTS - IMPROVED]');
    console.log('===============================================');
    
    const testItems = [
        { name: 'Settings Status Display Visible', status: testResults.settingsStatusVisible },
        { name: 'Settings Status Values Updated', status: testResults.settingsStatusUpdated },
        { name: 'Quick Link to Settings Works', status: testResults.quickLinkWorks },
        { name: 'Modal Model Loading Fixed', status: testResults.modalModelsFixed },
        { name: 'Model Synchronization Works', status: testResults.modelSyncWorks },
        { name: 'Overall UX Improved', status: testResults.uxImproved }
    ];
    
    testItems.forEach((test, index) => {
        console.log(`${test.status ? '✅' : '❌'} ${index + 1}. ${test.name}`);
    });
    
    const successfulTests = testItems.filter(test => test.status).length;
    const totalTests = testItems.length;
    const successRate = Math.round(successfulTests / totalTests * 100);
    
    console.log('');
    console.log(`📊 UX Improvement Success Rate: ${successfulTests}/${totalTests} (${successRate}%)`);
    
    if (successRate >= 90) {
        console.log('');
        console.log('🎉 ADVANCED SEARCH UX: EXCELLENT SUCCESS!');
        console.log('✅ Settings status display shows current configuration');
        console.log('✅ Quick link to settings modal works perfectly');
        console.log('✅ Header settings modal model loading is fixed');
        console.log('✅ Model synchronization between main page and modal works');
        console.log('✅ UX is now clear and informative for users');
        console.log('🚀 Advanced Search is truly "advanced" with visible settings!');
    } else if (successRate >= 70) {
        console.log('');
        console.log('🎯 ADVANCED SEARCH UX: GOOD PROGRESS');
        console.log('✅ Major improvements implemented');
        console.log('⚠️ Some functionality may need fine-tuning');
    } else {
        console.log('');
        console.log('❌ ADVANCED SEARCH UX: NEEDS MORE WORK');
        console.log('❌ Critical issues remain');
        console.log('🔧 Further investigation required');
    }
    
    console.log('🏁 [ADVANCED SEARCH UX TEST - IMPROVED] Complete');
    return successRate >= 85;
}

testAdvancedSearchUXImproved().catch(console.error);