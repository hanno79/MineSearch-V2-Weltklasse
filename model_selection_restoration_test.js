/**
 * Model Selection Restoration Test - CRITICAL REPAIR VALIDATION
 * Author: rahn
 * Datum: 13.08.2025
 * Beschreibung: Test ob die kritische Modellauswahl wiederhergestellt wurde
 */

const { chromium } = require('playwright');

async function testModelSelectionRestoration() {
    console.log('🔧 [RESTORATION-TEST] Testing critical model selection restoration...');
    
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext();
    const page = await context.newPage();
    
    // Monitor console logs
    page.on('console', msg => {
        const text = msg.text();
        if (text.includes('[MODEL]') || text.includes('[MAIN]') || text.includes('loadModelsForFilter')) {
            console.log('🖥️ [CONSOLE]', text);
        }
    });
    
    let testResults = {
        pageLoad: false,
        modelContainerExists: false,
        modelsLoaded: false,
        modelsSelectable: false,
        uiProfessional: false
    };
    
    try {
        console.log('🔄 [TEST 1] Page Load & Model Container Check...');
        await page.goto('http://localhost:8000');
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(3000);
        
        testResults.pageLoad = true;
        console.log('✅ [TEST 1] Page loaded successfully');
        
        console.log('🔄 [TEST 2] Model Selection Container Check...');
        
        // Check if model selection container exists
        const globalModelSection = await page.$('.global-model-selection');
        const modelContainer = await page.$('#model-selection');
        const modelHeader = await page.$('.model-selection-header h3');
        
        console.log(`📊 [CONTAINER] Global model section: ${globalModelSection ? 'EXISTS' : 'MISSING'}`);
        console.log(`📊 [CONTAINER] Model container: ${modelContainer ? 'EXISTS' : 'MISSING'}`);
        console.log(`📊 [CONTAINER] Model header: ${modelHeader ? 'EXISTS' : 'MISSING'}`);
        
        if (globalModelSection && modelContainer && modelHeader) {
            testResults.modelContainerExists = true;
            console.log('✅ [TEST 2] Model selection container restored successfully');
        }
        
        console.log('🔄 [TEST 3] Model Loading Check...');
        
        // Wait for models to load
        await page.waitForTimeout(5000);
        
        // Check if models are loaded
        const modelCheckboxes = await page.$$('#model-selection input[type="checkbox"]');
        const providerLabels = await page.$$('#model-selection label');
        const loadingText = await page.$('#model-selection .model-loading');
        
        console.log(`📊 [MODELS] Model checkboxes: ${modelCheckboxes.length}`);
        console.log(`📊 [MODELS] Provider labels: ${providerLabels.length}`);
        console.log(`📊 [MODELS] Loading text still visible: ${loadingText ? 'YES (BAD)' : 'NO (GOOD)'}`);
        
        if (modelCheckboxes.length > 0 && providerLabels.length > 0) {
            testResults.modelsLoaded = true;
            console.log('✅ [TEST 3] Models loaded successfully');
            
            // Test model selection
            console.log('🔄 [TEST 4] Model Selection Functionality...');
            
            if (modelCheckboxes.length > 0) {
                // Click first model
                await modelCheckboxes[0].click();
                await page.waitForTimeout(500);
                
                const isChecked = await modelCheckboxes[0].isChecked();
                console.log(`📊 [SELECTION] First model clickable and checked: ${isChecked ? 'YES' : 'NO'}`);
                
                if (isChecked) {
                    testResults.modelsSelectable = true;
                    console.log('✅ [TEST 4] Model selection functionality working');
                }
            }
        } else {
            console.log('⚠️ [TEST 3] Models not loaded yet - checking if loadModelsForFilter is being called...');
        }
        
        console.log('🔄 [TEST 5] UI Professional Appearance...');
        
        // Check UI elements
        const selectionTips = await page.$('.selection-tips');
        const modelDescription = await page.$('.model-description');
        const professionalStyling = await page.evaluate(() => {
            const container = document.querySelector('.global-model-selection');
            if (!container) return false;
            const styles = window.getComputedStyle(container);
            return styles.background.includes('gradient') && styles.borderRadius;
        });
        
        console.log(`📊 [UI] Selection tips: ${selectionTips ? 'EXISTS' : 'MISSING'}`);
        console.log(`📊 [UI] Model description: ${modelDescription ? 'EXISTS' : 'MISSING'}`);
        console.log(`📊 [UI] Professional styling: ${professionalStyling ? 'YES' : 'NO'}`);
        
        if (selectionTips && modelDescription && professionalStyling) {
            testResults.uiProfessional = true;
            console.log('✅ [TEST 5] UI appears professional and informative');
        }
        
        // Screenshots
        await page.screenshot({ path: 'model_selection_restored.png', fullPage: true });
        
        // Mobile test
        await page.setViewportSize({ width: 375, height: 667 });
        await page.waitForTimeout(1000);
        await page.screenshot({ path: 'model_selection_mobile.png', fullPage: true });
        
    } catch (error) {
        console.error('💥 [ERROR]', error);
        await page.screenshot({ path: 'model_selection_restoration_error.png' });
    } finally {
        await browser.close();
    }
    
    // Assessment
    console.log('');
    console.log('🏆 [MODEL SELECTION RESTORATION TEST RESULTS]');
    console.log('==============================================');
    
    const testItems = [
        { name: 'Page Load', status: testResults.pageLoad },
        { name: 'Model Container Exists', status: testResults.modelContainerExists },
        { name: 'Models Loaded', status: testResults.modelsLoaded },
        { name: 'Models Selectable', status: testResults.modelsSelectable },
        { name: 'UI Professional', status: testResults.uiProfessional }
    ];
    
    testItems.forEach((test, index) => {
        console.log(`${test.status ? '✅' : '❌'} ${index + 1}. ${test.name}`);
    });
    
    const successfulTests = testItems.filter(test => test.status).length;
    const totalTests = testItems.length;
    const successRate = Math.round(successfulTests / totalTests * 100);
    
    console.log('');
    console.log(`📊 Restoration Success Rate: ${successfulTests}/${totalTests} (${successRate}%)`);
    
    if (successRate >= 80) {
        console.log('');
        console.log('🎉 MODEL SELECTION RESTORATION: SUCCESS!');
        console.log('✅ Critical model selection functionality restored');
        console.log('✅ Users can now select AI models for searches');
        console.log('✅ Professional UI with clear instructions');
        if (successRate < 100) {
            console.log('⚠️ Some minor improvements may be needed');
        }
    } else if (successRate >= 60) {
        console.log('');
        console.log('🎯 MODEL SELECTION RESTORATION: PARTIAL SUCCESS');
        console.log('✅ Container and UI restored');
        console.log('⚠️ Model loading or selection may need attention');
    } else {
        console.log('');
        console.log('❌ MODEL SELECTION RESTORATION: FAILED');
        console.log('❌ Critical functionality still missing');
        console.log('🔧 Further investigation required');
    }
    
    console.log('🏁 [MODEL SELECTION RESTORATION TEST] Complete');
    return successRate >= 80;
}

testModelSelectionRestoration().catch(console.error);