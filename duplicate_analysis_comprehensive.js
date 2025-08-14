/**
 * Comprehensive Duplicate Analysis - MineSearch 2.0
 * Author: rahn
 * Datum: 13.08.2025
 * Beschreibung: Detaillierte Analyse aller GUI-Doppelspurigkeiten nach Header-Revolution
 */

const { chromium } = require('playwright');

async function analyzeDuplicateElements() {
    console.log('🔍 [DUPLICATE-ANALYSIS] Starting comprehensive duplicate element analysis...');
    
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext();
    const page = await context.newPage();
    
    // Monitor JavaScript errors
    page.on('pageerror', error => {
        console.log('💥 [JS ERROR]', error.message);
    });
    
    let duplicateFindings = {
        navigation: [],
        settings: [],
        searchOptions: [],
        actions: [],
        general: []
    };
    
    try {
        console.log('🔄 [STEP 1] Loading main page and taking initial screenshot...');
        await page.goto('http://localhost:8000');
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(3000);
        
        // Take full page screenshot for reference
        await page.screenshot({ path: 'duplicate_analysis_fullpage.png', fullPage: true });
        
        console.log('🔄 [STEP 2] Analyzing NAVIGATION duplicates...');
        
        // Check for navigation duplicates
        const headerNavItems = await page.$$('.nav-item');
        const tabNavItems = await page.$$('.tab-navigation label');
        
        console.log(`📊 [NAV] Header navigation items: ${headerNavItems.length}`);
        console.log(`📊 [NAV] Tab navigation items: ${tabNavItems.length}`);
        
        if (headerNavItems.length > 0 && tabNavItems.length > 0) {
            duplicateFindings.navigation.push({
                type: 'Primary Navigation',
                locations: ['Header (.nav-item)', 'Below Header (.tab-navigation)'],
                count: `${headerNavItems.length} + ${tabNavItems.length}`,
                severity: 'HIGH',
                description: 'Double navigation system creates confusion'
            });
        }
        
        // Get navigation text content for comparison
        for (let i = 0; i < Math.min(headerNavItems.length, tabNavItems.length); i++) {
            const headerText = await headerNavItems[i].textContent();
            const tabText = await tabNavItems[i].textContent();
            console.log(`📋 [NAV-COMPARE] Header: "${headerText}" vs Tab: "${tabText}"`);
        }
        
        console.log('🔄 [STEP 3] Analyzing SETTINGS and SEARCH OPTIONS duplicates...');
        
        // Check for search option duplicates
        const headerSearchInput = await page.$('#quick-search-input');
        const mainSearchInputs = await page.$$('input[name="mine_name"], input[name="country"], input[name="commodity"]');
        
        if (headerSearchInput && mainSearchInputs.length > 0) {
            duplicateFindings.searchOptions.push({
                type: 'Search Input Fields',
                locations: ['Header (Quick Search)', 'Main Form (Detailed Search)'],
                count: `1 + ${mainSearchInputs.length}`,
                severity: 'MEDIUM',
                description: 'Quick search in header + detailed search form below'
            });
        }
        
        // Check for search mode options (2-Phase, Smart Search, etc.)
        const searchModeOptions = await page.$$('#two_phase_enabled, #smart_search_enabled, #comprehensive_search_enabled');
        const headerSettingsBtn = await page.$('button[onclick="toggleSettingsModal()"]');
        
        if (searchModeOptions.length > 0 && headerSettingsBtn) {
            duplicateFindings.settings.push({
                type: 'Search Mode Settings',
                locations: ['Header Settings Modal', 'Main Page Checkboxes'],
                count: `Settings Modal + ${searchModeOptions.length} checkboxes`,
                severity: 'HIGH',
                description: 'Search options accessible from both header settings and main form'
            });
        }
        
        console.log('🔄 [STEP 4] Opening Settings Modal for detailed analysis...');
        
        // Open settings modal to analyze its content
        if (headerSettingsBtn) {
            await headerSettingsBtn.click();
            await page.waitForTimeout(1500);
            
            const settingsModal = await page.$('#settings-modal');
            if (settingsModal) {
                const settingsVisible = await settingsModal.isVisible();
                if (settingsVisible) {
                    console.log('✅ [SETTINGS] Settings modal opened successfully');
                    
                    // Take screenshot of settings modal
                    await page.screenshot({ path: 'settings_modal_analysis.png' });
                    
                    // Check for duplicate settings options
                    const modalSettings = await settingsModal.$$('input[type="checkbox"]');
                    console.log(`📊 [SETTINGS] Modal has ${modalSettings.length} checkbox options`);
                    
                    // Compare with main page options
                    for (let setting of modalSettings) {
                        const settingId = await setting.getAttribute('id');
                        console.log(`📋 [SETTINGS] Modal setting: ${settingId}`);
                    }
                    
                    // Close modal
                    const closeBtn = await settingsModal.$('.modal-close');
                    if (closeBtn) {
                        await closeBtn.click();
                        await page.waitForTimeout(1000);
                    }
                }
            }
        }
        
        console.log('🔄 [STEP 5] Analyzing HELP and ACTION duplicates...');
        
        // Check for help/documentation duplicates
        const headerHelpBtn = await page.$('button[onclick="toggleHelpModal()"]');
        const mainHelpElements = await page.$$('.help-text, .documentation, small'); // Common help text elements
        
        if (headerHelpBtn && mainHelpElements.length > 0) {
            duplicateFindings.general.push({
                type: 'Help/Documentation',
                locations: ['Header Help Modal', 'Inline Help Text'],
                count: `1 modal + ${mainHelpElements.length} inline helps`,
                severity: 'LOW',
                description: 'Help available in header modal + scattered inline help texts'
            });
        }
        
        console.log('🔄 [STEP 6] Checking MODEL SELECTION duplicates...');
        
        // Check for model selection duplicates (if any)
        const modelSelectionSection = await page.$('#model-selection');
        const headerModelActions = await page.$$('.header-action-btn'); // Any model-related actions in header
        
        if (modelSelectionSection) {
            const modelCheckboxes = await page.$$('input[name="model"]');
            console.log(`📊 [MODELS] Main page has ${modelCheckboxes.length} model checkboxes`);
            
            // Check if header has any model-related functionality
            for (let action of headerModelActions) {
                const actionTitle = await action.getAttribute('title');
                if (actionTitle && actionTitle.toLowerCase().includes('model')) {
                    duplicateFindings.general.push({
                        type: 'Model Selection',
                        locations: ['Header Actions', 'Main Model Selection'],
                        count: 'Header action + Main selection',
                        severity: 'MEDIUM',
                        description: 'Model selection accessible from multiple locations'
                    });
                }
            }
        }
        
        console.log('🔄 [STEP 7] Testing different tabs for additional duplicates...');
        
        // Test different tabs to see if duplicates exist there
        const tabs = ['csv', 'statistics', 'sources', 'consolidated'];
        
        for (let tab of tabs) {
            console.log(`📋 [TAB-TEST] Switching to ${tab} tab...`);
            
            // Try both navigation methods
            const headerNavItem = await page.$(`[data-tab="${tab}"]`);
            const tabNavItem = await page.$(`#${tab}-tab`);
            
            if (headerNavItem) {
                await headerNavItem.click();
                await page.waitForTimeout(2000);
                
                // Check if this creates any new duplicates
                const currentUrl = page.url();
                console.log(`📍 [TAB-TEST] Current URL after ${tab}: ${currentUrl}`);
            }
        }
        
        console.log('🔄 [STEP 8] Final comprehensive screenshot...');
        
        // Back to main tab
        const singleTab = await page.$('[data-tab="single"]');
        if (singleTab) {
            await singleTab.click();
            await page.waitForTimeout(2000);
        }
        
        await page.screenshot({ path: 'duplicate_analysis_final.png', fullPage: true });
        
    } catch (error) {
        console.error('💥 [ERROR]', error);
        await page.screenshot({ path: 'duplicate_analysis_error.png' });
    } finally {
        await browser.close();
    }
    
    // Comprehensive Analysis Report
    console.log('');
    console.log('🏆 [DUPLICATE ANALYSIS RESULTS]');
    console.log('================================');
    
    const allFindings = [
        ...duplicateFindings.navigation,
        ...duplicateFindings.settings, 
        ...duplicateFindings.searchOptions,
        ...duplicateFindings.actions,
        ...duplicateFindings.general
    ];
    
    console.log(`📊 Total duplicate issues found: ${allFindings.length}`);
    console.log('');
    
    // Group by severity
    const highPriority = allFindings.filter(f => f.severity === 'HIGH');
    const mediumPriority = allFindings.filter(f => f.severity === 'MEDIUM');
    const lowPriority = allFindings.filter(f => f.severity === 'LOW');
    
    console.log('🚨 HIGH PRIORITY DUPLICATES:');
    highPriority.forEach((finding, index) => {
        console.log(`  ${index + 1}. ${finding.type}`);
        console.log(`     Locations: ${finding.locations.join(' + ')}`);
        console.log(`     Count: ${finding.count}`);
        console.log(`     Issue: ${finding.description}`);
        console.log('');
    });
    
    console.log('⚠️ MEDIUM PRIORITY DUPLICATES:');
    mediumPriority.forEach((finding, index) => {
        console.log(`  ${index + 1}. ${finding.type}`);
        console.log(`     Locations: ${finding.locations.join(' + ')}`);
        console.log(`     Count: ${finding.count}`);
        console.log(`     Issue: ${finding.description}`);
        console.log('');
    });
    
    console.log('ℹ️ LOW PRIORITY DUPLICATES:');
    lowPriority.forEach((finding, index) => {
        console.log(`  ${index + 1}. ${finding.type}`);
        console.log(`     Locations: ${finding.locations.join(' + ')}`);
        console.log(`     Count: ${finding.count}`);
        console.log(`     Issue: ${finding.description}`);
        console.log('');
    });
    
    console.log('🏁 [DUPLICATE ANALYSIS] Complete');
    return allFindings;
}

analyzeDuplicateElements().catch(console.error);