/**
 * Main Model Selection Repair Test
 * Author: rahn
 * Datum: 13.08.2025
 * Beschreibung: Test ob die Hauptseiten-Modellauswahl wieder vollständig funktioniert
 */

const { chromium } = require('playwright');

async function testMainModelSelectionRepair() {
    console.log('🔧 [REPAIR-TEST] Testing main page model selection after settings modal cleanup...');
    
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext();
    const page = await context.newPage();
    
    // Monitor console logs
    page.on('console', msg => {
        const text = msg.text();
        if (text.includes('[MODEL-FILTER]') || text.includes('[UI-REVOLUTION]') || text.includes('[DEBUG]')) {
            console.log('🖥️ [CONSOLE]', text);
        }
    });
    
    let testResults = {
        pageLoads: false,
        modelSectionExists: false,
        modelsLoad: false,
        labelsVisible: false,
        quickPillsWork: false,
        headerSettingsClean: false
    };
    
    try {
        console.log('🔄 [TEST 1] Page Load and Model Section Check...');
        await page.goto('http://localhost:8000');
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(6000); // Extra time for model loading
        
        testResults.pageLoads = true;
        console.log('✅ [TEST 1] Page loaded successfully');
        
        console.log('🔄 [TEST 2] Model Selection Section Exists...');
        const modelSection = await page.$('.global-model-selection');
        const modelContainer = await page.$('#model-selection');
        
        console.log(`📊 [MODEL-SECTION] Global section: ${modelSection ? 'EXISTS' : 'MISSING'}`);
        console.log(`📊 [MODEL-SECTION] Container: ${modelContainer ? 'EXISTS' : 'MISSING'}`);
        
        if (modelSection && modelContainer) {
            testResults.modelSectionExists = true;
            console.log('✅ [TEST 2] Model selection section exists');
        }
        
        console.log('🔄 [TEST 3] Models Loading Check...');
        
        // Check for loading indicator vs actual content
        const loadingIndicator = await page.$('.model-loading');
        const quickPills = await page.$$('.quick-pill');
        const providerGroups = await page.$$('.provider-group');
        const allCheckboxes = await page.$$('#model-selection input[type="checkbox"]');
        
        console.log(`📊 [MODELS] Loading indicator: ${loadingIndicator ? 'STILL PRESENT' : 'GONE (GOOD)'}`);
        console.log(`📊 [MODELS] Quick pills: ${quickPills.length}`);
        console.log(`📊 [MODELS] Provider groups: ${providerGroups.length}`);
        console.log(`📊 [MODELS] Total checkboxes: ${allCheckboxes.length}`);
        
        if (allCheckboxes.length > 50 && !loadingIndicator) {
            testResults.modelsLoad = true;
            console.log('✅ [TEST 3] Models loaded successfully');
        } else {
            console.log('❌ [TEST 3] Models not loaded or still loading');
        }
        
        console.log('🔄 [TEST 4] Model Labels Visibility...');
        
        // Check if labels are visible
        const modelLabels = await page.$$('.model-option .model-name');
        const providerHeaders = await page.$$('.provider-header .provider-info strong');
        
        console.log(`📊 [LABELS] Model names: ${modelLabels.length}`);
        console.log(`📊 [LABELS] Provider headers: ${providerHeaders.length}`);
        
        // Get text content to verify they're not empty
        const sampleModelName = modelLabels.length > 0 ? await modelLabels[0].textContent() : '';
        const sampleProviderName = providerHeaders.length > 0 ? await providerHeaders[0].textContent() : '';
        
        console.log(`📊 [LABELS] Sample model name: "${sampleModelName}"`);
        console.log(`📊 [LABELS] Sample provider name: "${sampleProviderName}"`);
        
        if (modelLabels.length > 30 && sampleModelName.length > 0 && sampleProviderName.length > 0) {
            testResults.labelsVisible = true;
            console.log('✅ [TEST 4] Model labels are visible and populated');
        } else {
            console.log('❌ [TEST 4] Model labels missing or empty');
        }
        
        console.log('🔄 [TEST 5] Quick Selection Pills Test...');
        
        if (quickPills.length > 0) {
            // Try clicking "Beste Auswahl" button
            const recommendedPill = quickPills.find(async (pill) => {
                const text = await pill.textContent();
                return text.includes('Beste Auswahl');
            });
            
            if (recommendedPill) {
                await recommendedPill.click();
                await page.waitForTimeout(2000);
                
                const checkedAfterClick = await page.$$('#model-selection input[type="checkbox"]:checked');
                console.log(`📊 [QUICK-PILLS] Models selected after click: ${checkedAfterClick.length}`);
                
                if (checkedAfterClick.length >= 3) {
                    testResults.quickPillsWork = true;
                    console.log('✅ [TEST 5] Quick selection pills work');
                } else {
                    console.log('❌ [TEST 5] Quick selection pills not working');
                }
            }
        }
        
        console.log('🔄 [TEST 6] Header Settings Modal Clean Check...');
        
        // Open settings modal
        const settingsButton = await page.$('button[onclick*="toggleSettingsModal"]');
        if (settingsButton) {
            await settingsButton.click();
            await page.waitForTimeout(1000);
            
            // Check if modal opened and doesn't contain model selection
            const settingsModal = await page.$('#settings-modal[style*="block"]');
            const modalModelSelection = await page.$('#modal-model-selection');
            
            console.log(`📊 [SETTINGS-MODAL] Modal opened: ${settingsModal ? 'YES' : 'NO'}`);
            console.log(`📊 [SETTINGS-MODAL] Model selection present: ${modalModelSelection ? 'YES (BAD)' : 'NO (GOOD)'}`);
            
            if (settingsModal && !modalModelSelection) {
                testResults.headerSettingsClean = true;
                console.log('✅ [TEST 6] Header settings modal is clean (no model selection)');
            } else {
                console.log('❌ [TEST 6] Header settings modal still has model selection or not working');
            }
            
            // Close modal
            const closeBtn = await page.$('#settings-modal .modal-close');
            if (closeBtn) await closeBtn.click();
        }
        
        // Final screenshots
        await page.screenshot({ path: 'main_model_selection_repaired.png', fullPage: true });
        
    } catch (error) {
        console.error('💥 [ERROR]', error);
        await page.screenshot({ path: 'main_model_selection_repair_error.png' });
    } finally {
        await browser.close();
    }
    
    // Final Assessment
    console.log('');
    console.log('🏆 [MAIN MODEL SELECTION REPAIR RESULTS]');
    console.log('========================================');
    
    const testItems = [
        { name: 'Page Loads Successfully', status: testResults.pageLoads },
        { name: 'Model Selection Section Exists', status: testResults.modelSectionExists },
        { name: 'Models Load Correctly', status: testResults.modelsLoad },
        { name: 'Model Labels Visible', status: testResults.labelsVisible },
        { name: 'Quick Pills Work', status: testResults.quickPillsWork },
        { name: 'Header Settings Clean', status: testResults.headerSettingsClean }
    ];
    
    testItems.forEach((test, index) => {
        console.log(`${test.status ? '✅' : '❌'} ${index + 1}. ${test.name}`);
    });
    
    const successfulTests = testItems.filter(test => test.status).length;
    const totalTests = testItems.length;
    const successRate = Math.round(successfulTests / totalTests * 100);
    
    console.log('');
    console.log(`📊 Main Model Selection Repair Success Rate: ${successfulTests}/${totalTests} (${successRate}%)`);
    
    if (successRate >= 90) {
        console.log('');
        console.log('🎉 MODEL SELECTION REPAIR: EXCELLENT SUCCESS!');
        console.log('✅ Main page model selection is fully functional');
        console.log('✅ All model labels and provider groups are visible');
        console.log('✅ Quick selection buttons work perfectly');
        console.log('✅ Header settings modal is clean (no model selection)');
        console.log('🚀 Problem solved - models are back on main page only!');
    } else if (successRate >= 70) {
        console.log('');
        console.log('🎯 MODEL SELECTION REPAIR: GOOD PROGRESS');
        console.log('✅ Basic functionality restored');
        console.log('⚠️ Some features may need additional fixes');
    } else {
        console.log('');
        console.log('❌ MODEL SELECTION REPAIR: NEEDS MORE WORK');
        console.log('❌ Critical issues remain');
        console.log('🔧 Further investigation required');
    }
    
    console.log('🏁 [MAIN MODEL SELECTION REPAIR TEST] Complete');
    return successRate >= 85;
}

testMainModelSelectionRepair().catch(console.error);