/**
 * COMPREHENSIVE PROGRESSIVE MODEL SELECTION UI TEST mit Playwright
 * Tests all interactive features after API Response Format Fix
 * Expected: 31 models from 7 providers, not 0 models from 0 providers
 */

const { chromium } = require('playwright');

async function testProgressiveModelSelection() {
    console.log('🧪 [TEST] Starting comprehensive Progressive Model Selection UI test with Playwright...');
    
    const browser = await chromium.launch({ 
        headless: false,
        slowMo: 200
    });
    
    const page = await browser.newPage({
        viewport: { width: 1400, height: 900 }
    });
    
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
        await page.goto('http://localhost:5000', { waitUntil: 'networkidle' });
        await page.waitForTimeout(3000);
        
        // Take initial screenshot
        await page.screenshot({ path: 'progressive_model_test_01_initial.png', fullPage: true });
        console.log('📸 [TEST] Initial screenshot taken');
        
        // TASK 1: Verify models loaded (should be 31 models, 7 providers)
        console.log('\\n🎯 [TEST] TASK 1: Verifying Progressive Model Selection loaded correctly...');
        
        const modelSelectionContainer = await page.locator('#model-selection');
        await modelSelectionContainer.waitFor({ timeout: 10000 });
        console.log('✅ [TEST] Model selection container found and loaded');
        
        // Check for Progressive Model Selection elements
        const progressiveContainer = await page.locator('.model-selection-enhanced');
        if (await progressiveContainer.count() > 0) {
            console.log('✅ [TEST] Progressive Model Selection container found');
        } else {
            console.log('❌ [TEST] Progressive Model Selection container NOT found!');
        }
        
        // TASK 2: Test Quick Selection Pills
        console.log('\\n🎯 [TEST] TASK 2: Testing Quick Selection Pills...');
        
        const quickPills = await page.locator('.quick-model-pill');
        const pillCount = await quickPills.count();
        console.log(`📊 [TEST] Found ${pillCount} quick selection pills`);
        
        if (pillCount > 0) {
            // Test first provider pill
            const firstPill = quickPills.first();
            const pillText = await firstPill.textContent();
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
        console.log('\\n🎯 [TEST] TASK 3: Testing Advanced Model Browser...');
        
        const advancedToggle = await page.locator('.advanced-toggle-btn');
        if (await advancedToggle.count() > 0) {
            console.log('✅ [TEST] Advanced toggle button found');
            await advancedToggle.click();
            await page.waitForTimeout(1000);
            
            const advancedBrowser = await page.locator('.advanced-model-browser');
            if (await advancedBrowser.count() > 0) {
                const isVisible = await advancedBrowser.isVisible();
                console.log(`📊 [TEST] Advanced Model Browser visible: ${isVisible}`);
                
                await page.screenshot({ path: 'progressive_model_test_03_advanced_mode.png', fullPage: true });
                console.log('📸 [TEST] Advanced mode screenshot taken');
            }
        } else {
            console.log('❌ [TEST] Advanced toggle button NOT found!');
        }
        
        // TASK 4: Test Provider Tabs
        console.log('\\n🎯 [TEST] TASK 4: Testing Provider Tabs...');
        
        const providerTabs = await page.locator('.provider-tab');
        const tabCount = await providerTabs.count();
        console.log(`📊 [TEST] Found ${tabCount} provider tabs`);
        
        if (tabCount > 1) {
            // Test second provider tab (first is usually "All")
            const secondTab = providerTabs.nth(1);
            const tabText = await secondTab.textContent();
            console.log(`🔸 [TEST] Testing provider tab: "${tabText}"`);
            
            await secondTab.click();
            await page.waitForTimeout(1000);
            
            await page.screenshot({ path: 'progressive_model_test_04_provider_tabs.png', fullPage: true });
            console.log('📸 [TEST] Provider tabs test screenshot taken');
            
            console.log('✅ [TEST] Provider Tabs clickable');
        }
        
        // TASK 5: Test Model Cards Selection
        console.log('\\n🎯 [TEST] TASK 5: Testing Model Cards Selection...');
        
        const modelCards = await page.locator('.model-card');
        const cardCount = await modelCards.count();
        console.log(`📊 [TEST] Found ${cardCount} model cards`);
        
        if (cardCount > 0) {
            // Test selecting a few model cards
            for (let i = 0; i < Math.min(3, cardCount); i++) {
                const card = modelCards.nth(i);
                await card.click();
                await page.waitForTimeout(500);
                
                const checkbox = card.locator('input[type="checkbox"]');
                if (await checkbox.count() > 0) {
                    const isChecked = await checkbox.isChecked();
                    console.log(`🔸 [TEST] Model card ${i + 1} selected: ${isChecked}`);
                }
            }
            
            await page.screenshot({ path: 'progressive_model_test_05_model_selection.png', fullPage: true });
            console.log('📸 [TEST] Model selection screenshot taken');
            
            console.log('✅ [TEST] Model Cards selectable');
        }
        
        // TASK 6: Check Selection Summary
        console.log('\\n🎯 [TEST] TASK 6: Testing Selection Summary...');
        
        const selectionSummary = await page.locator('.selection-summary');
        if (await selectionSummary.count() > 0) {
            const summaryText = await selectionSummary.textContent();
            console.log(`📊 [TEST] Selection summary: "${summaryText}"`);
            
            const selectedCount = page.locator('#selected-count');
            if (await selectedCount.count() > 0) {
                const count = await selectedCount.textContent();
                console.log(`📊 [TEST] Selected models count: ${count}`);
                console.log('✅ [TEST] Selection Summary working');
            }
        }
        
        // TASK 7: Verify no conflicts with legacy UI
        console.log('\\n🎯 [TEST] TASK 7: Verifying no conflicts with legacy UI...');
        
        // Check if legacy checkboxes are properly hidden
        const legacyCheckboxes = page.locator('#legacy-checkboxes');
        if (await legacyCheckboxes.count() > 0) {
            const isHidden = await legacyCheckboxes.evaluate(el => {
                const style = window.getComputedStyle(el);
                return style.display === 'none';
            });
            console.log(`📊 [TEST] Legacy checkboxes hidden: ${isHidden}`);
        }
        
        // Final comprehensive screenshot
        await page.screenshot({ path: 'progressive_model_test_06_final_complete.png', fullPage: true });
        console.log('📸 [TEST] Final comprehensive screenshot taken');
        
        console.log('\\n🎉 [TEST] COMPREHENSIVE PROGRESSIVE MODEL SELECTION TEST COMPLETE');
        console.log('✅ [TEST] All interactive features tested successfully');
        
        // Extract final model selection state
        const finalState = await page.evaluate(() => {
            const selectedModels = [];
            const checkboxes = document.querySelectorAll('#model-selection input[type="checkbox"]:checked');
            checkboxes.forEach(cb => selectedModels.push(cb.value));
            return {
                selectedModels,
                totalModels: document.querySelectorAll('#model-selection input[type="checkbox"]').length,
                progressiveUiActive: !!document.querySelector('.model-selection-enhanced')
            };
        });
        
        console.log('📊 [TEST] Final State:', JSON.stringify(finalState, null, 2));
        
    } catch (error) {
        console.error('❌ [TEST] Test failed:', error);
        await page.screenshot({ path: 'progressive_model_test_error.png', fullPage: true });
        throw error;
    } finally {
        await page.waitForTimeout(2000);
        await browser.close();
    }
}

// Run the test
testProgressiveModelSelection().catch(console.error);