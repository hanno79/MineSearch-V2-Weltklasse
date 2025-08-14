/**
 * Settings Duplication Analysis - PHASE 2 Preparation
 * Author: rahn
 * Datum: 13.08.2025
 * Beschreibung: Analysiert doppelte Settings zwischen Header Modal und Main Page
 */

const { chromium } = require('playwright');

async function analyzeSettingsDuplication() {
    console.log('⚙️ [SETTINGS-ANALYSIS] Analyzing duplicate settings...');
    
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext();
    const page = await context.newPage();
    
    try {
        await page.goto('http://localhost:8000');
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(3000);
        
        console.log('🔄 [SETTINGS-ANALYSIS] Page loaded, analyzing duplicates...');
        
        // 1. ANALYSE: Header Settings Modal
        console.log('\n📋 [HEADER-SETTINGS] Analyzing header settings modal...');
        const settingsButton = await page.$('.header-action-btn[onclick*="toggleSettingsModal"]');
        if (settingsButton) {
            await settingsButton.click();
            await page.waitForTimeout(1000);
            
            // Check for modal content
            const settingsModal = await page.$('#settings-modal');
            const headerSettings = await page.$$('#settings-modal input, #settings-modal select');
            console.log(`✅ [HEADER-SETTINGS] Found ${headerSettings.length} settings in header modal`);
            
            // List specific header settings
            for (let i = 0; i < headerSettings.length; i++) {
                const setting = headerSettings[i];
                const id = await setting.getAttribute('id');
                const type = await setting.getAttribute('type') || 'select';
                console.log(`  - ${id} (${type})`);
            }
            
            // Close modal
            const closeBtn = await page.$('#settings-modal .modal-close');
            if (closeBtn) await closeBtn.click();
            await page.waitForTimeout(500);
        }
        
        // 2. ANALYSE: Main Page Settings/Options
        console.log('\n📋 [MAIN-PAGE-SETTINGS] Analyzing main page settings...');
        
        // Check for main page checkboxes and options
        const mainPageCheckboxes = await page.$$('main input[type="checkbox"]');
        const mainPageSelects = await page.$$('main select');
        
        console.log(`📊 [MAIN-PAGE-SETTINGS] Found ${mainPageCheckboxes.length} checkboxes and ${mainPageSelects.length} selects`);
        
        // List main page settings
        for (let i = 0; i < mainPageCheckboxes.length; i++) {
            const checkbox = mainPageCheckboxes[i];
            const id = await checkbox.getAttribute('id');
            const label = await page.textContent(`label[for="${id}"]`).catch(() => 'No label');
            console.log(`  - Checkbox: ${id} (${label})`);
        }
        
        for (let i = 0; i < mainPageSelects.length; i++) {
            const select = mainPageSelects[i];
            const id = await select.getAttribute('id');
            const label = await page.textContent(`label[for="${id}"]`).catch(() => 'No label');
            console.log(`  - Select: ${id} (${label})`);
        }
        
        // 3. IDENTIFIZIERE DUPLIKATE
        console.log('\n🔍 [DUPLICATION-ANALYSIS] Identifying duplications...');
        
        // Specific duplications to check
        const duplicateAnalysis = [
            {
                name: '2-Phasen-Suche',
                headerElement: 'auto-2phase',
                mainElement: 'two_phase_enabled',
                severity: 'HIGH'
            },
            {
                name: 'Smart-Search/Auto-Modell-Auswahl',
                headerElement: 'auto-model-selection', 
                mainElement: 'smart_search_enabled',
                severity: 'HIGH'
            },
            {
                name: 'Export Format',
                headerElement: 'default-export-format',
                mainElement: null, // Only in header currently
                severity: 'LOW'
            }
        ];
        
        console.log('\n📊 [DUPLICATION-REPORT] Settings Duplication Analysis:');
        console.log('='.repeat(60));
        
        let highPriorityDuplicates = 0;
        for (const dup of duplicateAnalysis) {
            const headerExists = await page.$(`#${dup.headerElement}`) !== null;
            const mainExists = dup.mainElement ? await page.$(`#${dup.mainElement}`) !== null : false;
            
            const isDuplicate = headerExists && mainExists;
            if (isDuplicate && dup.severity === 'HIGH') highPriorityDuplicates++;
            
            console.log(`${isDuplicate ? '🔄' : '✅'} ${dup.name}`);
            console.log(`   Header: ${headerExists ? '✅' : '❌'} (${dup.headerElement})`);
            console.log(`   Main:   ${mainExists ? '✅' : '❌'} (${dup.mainElement || 'N/A'})`);
            console.log(`   Status: ${isDuplicate ? 'DUPLICATE' : 'OK'} - Priority: ${dup.severity}`);
            console.log('');
        }
        
        // 4. SCREENSHOT für Dokumentation
        await page.screenshot({ path: 'settings_duplication_analysis.png', fullPage: true });
        
        // 5. FINAL ASSESSMENT
        console.log('\n🏆 [FINAL-ASSESSMENT] Settings Duplication Summary:');
        console.log('='.repeat(60));
        console.log(`📊 High-Priority Duplicates: ${highPriorityDuplicates}`);
        console.log(`📊 Total Main Page Settings: ${mainPageCheckboxes.length + mainPageSelects.length}`);
        console.log(`📊 Header Settings: ${headerSettings ? headerSettings.length : 0}`);
        
        if (highPriorityDuplicates > 0) {
            console.log('\n⚠️ RECOMMENDATION: Remove main page settings and consolidate to header modal');
            console.log('🎯 NEXT STEPS:');
            console.log('  1. Remove main page checkboxes: two_phase_enabled, smart_search_enabled');
            console.log('  2. Expand header settings modal with all needed options');
            console.log('  3. Implement synchronization between header settings and search forms');
            console.log('  4. Test all functionality after consolidation');
        } else {
            console.log('\n✅ NO MAJOR DUPLICATIONS FOUND - Settings already consolidated');
        }
        
    } catch (error) {
        console.error('💥 [ERROR]', error);
        await page.screenshot({ path: 'settings_analysis_error.png' });
    } finally {
        await browser.close();
    }
}

analyzeSettingsDuplication().catch(console.error);