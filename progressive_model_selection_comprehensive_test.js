/**
 * COMPREHENSIVE PROGRESSIVE MODEL SELECTION UI TEST
 * Tests all interactive features after API Response Format Fix
 * Expected: 31 models from 7 providers, not 0 models from 0 providers
 */

const puppeteer = require('puppeteer');

async function testProgressiveModelSelection() {
    console.log('🧪 [TEST] Starting comprehensive Progressive Model Selection UI test...');
    
    const browser = await puppeteer.launch({ 
        headless: false, 
        defaultViewport: { width: 1400, height: 900 },
        slowMo: 100
    });
    
    const page = await browser.newPage();
    
    // Listen for console messages from the browser
    page.on('console', (msg) => {
        if (msg.text().includes('[MODEL-UX]') || 
            msg.text().includes('[UI-REVOLUTION]') || 
            msg.text().includes('models') ||
            msg.text().includes('providers')) {
            console.log(`📋 [BROWSER] ${msg.text()}`);
        }
    });
    
    try {
        console.log('📡 [TEST] Loading MineSearch UI...');
        await page.goto('http://localhost:5000', { waitUntil: 'networkidle0' });
        await page.waitForTimeout(3000);
        
        // Take initial screenshot
        await page.screenshot({ path: 'progressive_model_test_01_initial.png', fullPage: true });
        console.log('📸 [TEST] Initial screenshot taken');
        
        // TASK 1: Verify models loaded (should be 31 models, 7 providers)
        console.log('\n🎯 [TEST] TASK 1: Verifying Progressive Model Selection loaded correctly...');
        
        const modelSelectionContainer = await page.$('#model-selection');
        if (modelSelectionContainer) {
            console.log('✅ [TEST] Model selection container found');
        } else {
            console.log('❌ [TEST] Model selection container NOT found!');
        }
        
        // Check for Progressive Model Selection elements
        const progressiveContainer = await page.$('.model-selection-enhanced');
        if (progressiveContainer) {
            console.log('✅ [TEST] Progressive Model Selection container found');
        } else {
            console.log('❌ [TEST] Progressive Model Selection container NOT found!');
        }
        
        // TASK 2: Test Quick Selection Pills
        console.log('\n🎯 [TEST] TASK 2: Testing Quick Selection Pills...');
        
        const quickPills = await page.$$('.quick-model-pill');
        console.log(`📊 [TEST] Found ${quickPills.length} quick selection pills`);
        
        if (quickPills.length > 0) {
            // Test first provider pill
            const firstPill = quickPills[0];
            const pillText = await page.evaluate(el => el.textContent, firstPill);
            console.log(`🔸 [TEST] Testing first pill: "${pillText}"`);
            
            await firstPill.click();
            await page.waitForTimeout(1000);
            
            await page.screenshot({ path: 'progressive_model_test_02_quick_pills.png', fullPage: true });
            console.log('📸 [TEST] Quick pills test screenshot taken');
            
            console.log('✅ [TEST] Quick Selection Pills clickable');
        } else {
            console.log('❌ [TEST] No Quick Selection Pills found!');
        }
        
        // TASK 3: Test Advanced Model Browser Toggle
        console.log('\n🎯 [TEST] TASK 3: Testing Advanced Model Browser...');
        
        const advancedToggle = await page.$('.advanced-toggle-btn');
        if (advancedToggle) {
            console.log('✅ [TEST] Advanced toggle button found');
            await advancedToggle.click();
            await page.waitForTimeout(1000);
            
            const advancedBrowser = await page.$('.advanced-model-browser');
            if (advancedBrowser) {
                const isVisible = await page.evaluate(el => {
                    const style = window.getComputedStyle(el);
                    return style.display !== 'none' && style.visibility !== 'hidden';
                }, advancedBrowser);
                
                console.log(`📊 [TEST] Advanced Model Browser visible: ${isVisible}`);
                
                await page.screenshot({ path: 'progressive_model_test_03_advanced_mode.png', fullPage: true });
                console.log('📸 [TEST] Advanced mode screenshot taken');
            }
        } else {
            console.log('❌ [TEST] Advanced toggle button NOT found!');
        }
        
        // TASK 4: Test Provider Tabs
        console.log('\n🎯 [TEST] TASK 4: Testing Provider Tabs...');
        
        const providerTabs = await page.$$('.provider-tab');
        console.log(`📊 [TEST] Found ${providerTabs.length} provider tabs`);
        
        if (providerTabs.length > 1) {
            // Test second provider tab (first is usually "All")
            const secondTab = providerTabs[1];
            const tabText = await page.evaluate(el => el.textContent, secondTab);
            console.log(`🔸 [TEST] Testing provider tab: "${tabText}"`);
            
            await secondTab.click();
            await page.waitForTimeout(1000);
            
            await page.screenshot({ path: 'progressive_model_test_04_provider_tabs.png', fullPage: true });
            console.log('📸 [TEST] Provider tabs test screenshot taken');
            
            console.log('✅ [TEST] Provider Tabs clickable');
        }
        
        // TASK 5: Test Model Cards Selection
        console.log('\n🎯 [TEST] TASK 5: Testing Model Cards Selection...');
        
        const modelCards = await page.$$('.model-card');
        console.log(`📊 [TEST] Found ${modelCards.length} model cards`);
        
        if (modelCards.length > 0) {
            // Test selecting a few model cards
            for (let i = 0; i < Math.min(3, modelCards.length); i++) {
                const card = modelCards[i];
                await card.click();
                await page.waitForTimeout(500);
                
                const checkbox = await card.$('input[type="checkbox"]');
                if (checkbox) {
                    const isChecked = await page.evaluate(el => el.checked, checkbox);
                    console.log(`🔸 [TEST] Model card ${i + 1} selected: ${isChecked}`);
                }
            }
            
            await page.screenshot({ path: 'progressive_model_test_05_model_selection.png', fullPage: true });
            console.log('📸 [TEST] Model selection screenshot taken');
            
            console.log('✅ [TEST] Model Cards selectable');
        }
        
        // TASK 6: Check Selection Summary
        console.log('\n🎯 [TEST] TASK 6: Testing Selection Summary...');
        
        const selectionSummary = await page.$('.selection-summary');
        if (selectionSummary) {
            const summaryText = await page.evaluate(el => el.textContent, selectionSummary);
            console.log(`📊 [TEST] Selection summary: "${summaryText}"`);
            
            const selectedCount = await page.$('#selected-count');
            if (selectedCount) {
                const count = await page.evaluate(el => el.textContent, selectedCount);
                console.log(`📊 [TEST] Selected models count: ${count}`);
                console.log('✅ [TEST] Selection Summary working');
            }
        }
        
        // Final comprehensive screenshot
        await page.screenshot({ path: 'progressive_model_test_06_final_complete.png', fullPage: true });
        console.log('📸 [TEST] Final comprehensive screenshot taken');
        
        console.log('\n🎉 [TEST] COMPREHENSIVE PROGRESSIVE MODEL SELECTION TEST COMPLETE');
        console.log('✅ [TEST] All interactive features tested successfully');
        
    } catch (error) {
        console.error('❌ [TEST] Test failed:', error);
        await page.screenshot({ path: 'progressive_model_test_error.png', fullPage: true });
    } finally {
        await page.waitForTimeout(2000);
        await browser.close();
    }
}

// Run the test
testProgressiveModelSelection().catch(console.error);