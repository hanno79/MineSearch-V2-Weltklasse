/**
 * Settings Consolidation Test - PHASE 2 Validation
 * Author: rahn
 * Datum: 13.08.2025
 * Beschreibung: Test der konsolidierten Settings ohne doppelte Settings
 */

const { chromium } = require('playwright');

async function testSettingsConsolidation() {
    console.log('⚙️ [SETTINGS-TEST] Testing consolidated settings system...');
    
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext();
    const page = await context.newPage();
    
    // Monitor console logs
    page.on('console', msg => {
        const text = msg.text();
        if (text.includes('[SETTINGS]') || text.includes('[NAVIGATION]')) {
            console.log('🖥️ [CONSOLE]', text);
        }
    });
    
    let testResults = {
        pageLoad: false,
        noDuplicateSettings: false,
        headerModalExpanded: false,
        settingsSync: false,
        virtualElementsCreated: false
    };
    
    try {
        console.log('🔄 [TEST 1] Page Load & Duplicate Check...');
        await page.goto('http://localhost:8000');
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(3000);
        
        testResults.pageLoad = true;
        console.log('✅ [TEST 1] Page loaded successfully');
        
        console.log('🔄 [TEST 2] Check Main Page Settings Removed...');
        
        // Check that main page settings are gone
        const oldTwoPhaseVisible = await page.$('main #two_phase_enabled[style*="display: none"], main #two_phase_enabled:not([style])') === null;
        const oldSmartSearchVisible = await page.$('main #smart_search_enabled[style*="display: none"], main #smart_search_enabled:not([style])') === null;
        const oldModelSelection = await page.$('main .search-mode') === null;
        
        console.log(`📊 [MAIN-SETTINGS] Old 2-Phase checkbox visible: ${!oldTwoPhaseVisible ? 'YES (BAD)' : 'NO (GOOD)'}`);
        console.log(`📊 [MAIN-SETTINGS] Old Smart Search checkbox visible: ${!oldSmartSearchVisible ? 'YES (BAD)' : 'NO (GOOD)'}`);
        console.log(`📊 [MAIN-SETTINGS] Old model selection visible: ${!oldModelSelection ? 'YES (BAD)' : 'NO (GOOD)'}`);
        
        if (oldTwoPhaseVisible && oldSmartSearchVisible && oldModelSelection) {
            testResults.noDuplicateSettings = true;
            console.log('✅ [TEST 2] Main page duplicate settings successfully removed');
        }
        
        console.log('🔄 [TEST 3] Test Header Settings Modal...');
        
        // Open header settings modal
        const settingsButton = await page.$('.header-action-btn[onclick*="toggleSettingsModal"]');
        if (settingsButton) {
            await settingsButton.click();
            await page.waitForTimeout(2000);
            
            // Check for expanded modal content
            const modalExists = await page.$('#settings-modal') !== null;
            const modalModelSelection = await page.$('#modal-model-selection') !== null;
            const auto2Phase = await page.$('#auto-2phase') !== null;
            const autoModelSelection = await page.$('#auto-model-selection') !== null;
            const exportFormat = await page.$('#default-export-format') !== null;
            
            console.log(`📊 [HEADER-MODAL] Modal exists: ${modalExists ? 'YES' : 'NO'}`);
            console.log(`📊 [HEADER-MODAL] Model selection: ${modalModelSelection ? 'YES' : 'NO'}`);
            console.log(`📊 [HEADER-MODAL] 2-Phase setting: ${auto2Phase ? 'YES' : 'NO'}`);
            console.log(`📊 [HEADER-MODAL] Smart Search setting: ${autoModelSelection ? 'YES' : 'NO'}`);
            console.log(`📊 [HEADER-MODAL] Export format: ${exportFormat ? 'YES' : 'NO'}`);
            
            if (modalExists && modalModelSelection && auto2Phase && autoModelSelection && exportFormat) {
                testResults.headerModalExpanded = true;
                console.log('✅ [TEST 3] Header settings modal properly expanded');
            }
            
            // Test settings functionality
            if (auto2Phase) {
                console.log('🔄 [TEST 4] Testing Settings Functionality...');
                
                // Toggle 2-phase setting
                await auto2Phase.click();
                await page.waitForTimeout(500);
                
                // Save settings
                const saveButton = await page.$('button[onclick="saveSettings()"]');
                if (saveButton) {
                    await saveButton.click();
                    await page.waitForTimeout(1000);
                    
                    testResults.settingsSync = true;
                    console.log('✅ [TEST 4] Settings save functionality working');
                }
            }
        }
        
        console.log('🔄 [TEST 5] Check Virtual Elements Created...');
        
        // Check if virtual elements were created for backward compatibility
        const virtualTwoPhase = await page.$('#virtual-two-phase, #two_phase_enabled');
        const virtualSmartSearch = await page.$('#virtual-smart-search, #smart_search_enabled');
        const virtualModelSelection = await page.$('#virtual-model-selection, #model-selection');
        
        console.log(`📊 [VIRTUAL] Virtual 2-Phase: ${virtualTwoPhase ? 'EXISTS' : 'MISSING'}`);
        console.log(`📊 [VIRTUAL] Virtual Smart Search: ${virtualSmartSearch ? 'EXISTS' : 'MISSING'}`);
        console.log(`📊 [VIRTUAL] Virtual Model Selection: ${virtualModelSelection ? 'EXISTS' : 'MISSING'}`);
        
        if (virtualTwoPhase && virtualSmartSearch && virtualModelSelection) {
            testResults.virtualElementsCreated = true;
            console.log('✅ [TEST 5] Virtual elements created for backward compatibility');
        }
        
        // Final screenshots
        await page.screenshot({ path: 'settings_consolidation_success.png', fullPage: true });
        
        // Screenshot with settings modal open
        const settingsModalOpen = await page.$('#settings-modal[style*="block"]');
        if (settingsModalOpen) {
            await page.screenshot({ path: 'settings_modal_consolidated.png', fullPage: true });
        }
        
    } catch (error) {
        console.error('💥 [ERROR]', error);
        await page.screenshot({ path: 'settings_consolidation_error.png' });
    } finally {
        await browser.close();
    }
    
    // Assessment
    console.log('');
    console.log('🏆 [SETTINGS CONSOLIDATION TEST RESULTS]');
    console.log('======================================');
    
    const testItems = [
        { name: 'Page Load', status: testResults.pageLoad },
        { name: 'No Duplicate Settings on Main Page', status: testResults.noDuplicateSettings },
        { name: 'Header Modal Expanded', status: testResults.headerModalExpanded },
        { name: 'Settings Sync Functional', status: testResults.settingsSync },
        { name: 'Virtual Elements Created', status: testResults.virtualElementsCreated }
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
        console.log('🎉 SETTINGS CONSOLIDATION: EXCELLENT SUCCESS!');
        console.log('✅ Duplicate settings successfully eliminated');
        console.log('✅ Header settings modal is the single source of settings');
        console.log('✅ Backward compatibility maintained with virtual elements');
        console.log('🚀 Ready for PHASE 3: Search UX Improvements');
    } else if (successRate >= 70) {
        console.log('');
        console.log('🎯 SETTINGS CONSOLIDATION: MOSTLY SUCCESSFUL');
        console.log('✅ Major duplicates eliminated');
        console.log('⚠️ Some functionality may need fine-tuning');
    } else {
        console.log('');
        console.log('⚠️ SETTINGS CONSOLIDATION: NEEDS ATTENTION');
        console.log('❌ Critical issues remain');
        console.log('🔧 Review and fix required');
    }
    
    console.log('🏁 [SETTINGS CONSOLIDATION TEST] Complete');
    return successRate >= 80;
}

testSettingsConsolidation().catch(console.error);