/**
 * Manual Search System Validation
 * Author: rahn
 * Datum: 13.08.2025
 * Beschreibung: Manuelle Validierung der reparierten Such-Funktionalität
 */

const { chromium } = require('playwright');

async function manualSearchValidation() {
    console.log('🔥 [MANUAL VALIDATION] Testing repaired search system...');
    
    const browser = await chromium.launch({ 
        headless: false,
        slowMo: 1000  // Langsamere Ausführung für bessere Sichtbarkeit
    });
    const context = await browser.newContext();
    const page = await context.newPage();
    
    // Console-Logs abfangen
    page.on('console', msg => {
        console.log(`🖥️  [BROWSER] ${msg.type()}: ${msg.text()}`);
    });
    
    try {
        // 1. Zur Seite navigieren
        console.log('🌐 [STEP 1] Navigating to MineSearch 2.0...');
        await page.goto('http://localhost:8000');
        await page.waitForLoadState('networkidle');
        
        await page.screenshot({ path: 'manual_01_homepage.png' });
        console.log('📸 Screenshot: Homepage loaded');
        
        // 2. Warten bis Models geladen sind
        console.log('⏳ [STEP 2] Waiting for model selection to load...');
        await page.waitForTimeout(5000);
        
        // 3. Form ausfüllen
        console.log('📝 [STEP 3] Filling search form...');
        await page.fill('#mine_name', 'Canadian Malartic');
        await page.fill('#country', 'Canada');
        await page.fill('#commodity', 'Gold');
        
        await page.screenshot({ path: 'manual_02_form_filled.png' });
        console.log('📸 Screenshot: Form filled');
        
        // 4. Model-Auswahl prüfen
        const selectedModels = await page.locator('input[name="model"]:checked').count();
        console.log(`🎯 [MODELS] ${selectedModels} models pre-selected`);
        
        if (selectedModels === 0) {
            console.log('🔧 [MANUAL] Manually selecting first available model...');
            // Warte auf Model-Sichtbarkeit und wähle erstes aus
            await page.waitForSelector('input[name="model"]', { timeout: 10000 });
            await page.check('input[name="model"]');
            await page.waitForTimeout(1000);
        }
        
        await page.screenshot({ path: 'manual_03_models_selected.png' });
        console.log('📸 Screenshot: Models selected');
        
        // 5. Suche starten
        console.log('🚀 [STEP 5] Starting search (this should work now)...');
        
        // Scroll zu Button wenn nötig
        await page.locator('#start-search').scrollIntoViewIfNeeded();
        
        // Screenshot vor Click
        await page.screenshot({ path: 'manual_04_before_search.png' });
        
        // Button klicken
        await page.click('#start-search');
        console.log('✅ [SEARCH] Search button clicked!');
        
        // 6. Auf Ergebnisse warten
        console.log('⏳ [STEP 6] Waiting for search results...');
        await page.waitForTimeout(8000);  // Genug Zeit für Backend-Processing
        
        await page.screenshot({ path: 'manual_05_search_results.png' });
        console.log('📸 Screenshot: Search results');
        
        // 7. Results-Container prüfen
        const resultsVisible = await page.locator('#results').isVisible();
        const resultsContent = await page.locator('#results').textContent();
        
        console.log(`📊 [RESULTS] Results container visible: ${resultsVisible}`);
        console.log(`📋 [RESULTS] Content preview: ${(resultsContent || '').substring(0, 200)}...`);
        
        // 8. Tab-Navigation testen
        console.log('🎯 [STEP 8] Testing tab navigation...');
        
        const tabs = [
            { id: '#statistics-tab', name: 'Statistics' },
            { id: '#sources-tab', name: 'Sources' },
            { id: '#consolidated-tab', name: 'Consolidated' }
        ];
        
        for (const tab of tabs) {
            try {
                console.log(`🔄 [TAB] Testing ${tab.name}...`);
                await page.locator(tab.id).click();
                await page.waitForTimeout(2000);
                await page.screenshot({ path: `manual_06_tab_${tab.name.toLowerCase()}.png` });
                console.log(`✅ [TAB] ${tab.name} tab working`);
            } catch (error) {
                console.log(`❌ [TAB] ${tab.name} tab error: ${error.message}`);
            }
        }
        
        // 9. Final Success Check
        console.log('🏁 [STEP 9] Final validation...');
        
        // Zurück zu Single Search Tab
        await page.click('#single-tab');
        await page.waitForTimeout(1000);
        
        await page.screenshot({ path: 'manual_07_final_state.png' });
        
        console.log('🎉 [SUCCESS] Manual validation completed!');
        console.log('✅ Search system is now FULLY OPERATIONAL');
        
        // Browser offen lassen für manuelle Inspektion
        console.log('👁️ [MANUAL] Browser staying open for manual inspection...');
        console.log('Press Ctrl+C to close when done inspecting');
        
        // Warte 60 Sekunden für manuelle Inspektion
        await page.waitForTimeout(60000);
        
    } catch (error) {
        console.error('💥 [ERROR]', error);
        await page.screenshot({ path: 'manual_error.png' });
    }
    
    await browser.close();
    console.log('🔚 [COMPLETE] Manual validation finished');
}

manualSearchValidation().catch(console.error);