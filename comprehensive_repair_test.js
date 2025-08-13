const { chromium } = require('playwright');

(async () => {
    console.log('🔧 [REPAIR-TEST] Starte umfassende Reparatur-Validierung...');
    const browser = await chromium.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    
    const page = await browser.newPage();
    
    // Network-Events abhören
    let loadedResources = [];
    page.on('response', (response) => {
        const url = response.url();
        const status = response.status();
        if (url.includes('static/') || url.includes('unpkg.com') || url.includes('jsdelivr.net')) {
            loadedResources.push({ url: url.split('/').pop(), status });
            if (status >= 400) {
                console.log(`❌ [NETWORK] ${status} - ${url}`);
            }
        }
    });
    
    page.on('console', (msg) => {
        const text = msg.text();
        if (text.includes('[TAB-AUTOLOADER]') || text.includes('[MAIN]') || text.includes('loadModelsForFilter')) {
            console.log(`🖥️ [CONSOLE] ${text}`);
        }
    });
    
    try {
        console.log('📋 [REPAIR-TEST] Lade http://localhost:8000...');
        await page.goto('http://localhost:8000', { 
            waitUntil: 'networkidle', 
            timeout: 15000 
        });
        
        // Warte auf vollständige Initialisierung
        console.log('⏳ [REPAIR-TEST] Warte auf System-Initialisierung...');
        await page.waitForTimeout(8000);
        
        // 1. TEST: TAB-NAVIGATION
        console.log('🔬 [TEST 1] Tab-Navigation testen...');
        
        // Teste alle Tab-Buttons
        const tabButtons = await page.$$('.tab-navigation label');
        console.log(`📊 [TEST 1] Gefunden: ${tabButtons.length} Tab-Buttons`);
        
        let tabTestResults = {};
        const tabIds = ['single-tab', 'csv-tab', 'sources-tab', 'statistics-tab', 'consolidated-tab'];
        
        for (const tabId of tabIds) {
            try {
                // Klicke auf Tab
                await page.click(`label[for="${tabId}"]`);
                await page.waitForTimeout(2000);
                
                // Prüfe CSS-Klasse
                const containerClass = await page.getAttribute('.container', 'class');
                const expectedClass = `tab-${tabId.replace('-tab', '')}`;
                const hasCorrectClass = containerClass && containerClass.includes(expectedClass);
                
                tabTestResults[tabId] = {
                    clickable: true,
                    cssClass: hasCorrectClass,
                    containerClass: containerClass
                };
                
                console.log(`✅ [TEST 1] ${tabId}: CSS-Klasse ${hasCorrectClass ? 'OK' : 'FEHLT'} (${expectedClass})`);
            } catch (error) {
                tabTestResults[tabId] = { clickable: false, error: error.message };
                console.log(`❌ [TEST 1] ${tabId}: ${error.message}`);
            }
        }
        
        // 2. TEST: MODELL-LOADING  
        console.log('🔬 [TEST 2] Modell-Loading testen...');
        
        const modelCheckboxes = await page.locator('input[type="checkbox"][name="selected_models"]').count();
        console.log(`📊 [TEST 2] Modelle geladen: ${modelCheckboxes}`);
        
        // Prüfe Modell-Container
        const modelContainer = await page.locator('#model-selection').textContent();
        const modelsLoading = modelContainer && modelContainer.includes('Lade verfügbare Modelle');
        
        // 3. TEST: UI-DESIGN ELEMENTE
        console.log('🔬 [TEST 3] UI-Design Elemente testen...');
        
        const designElements = {
            'Header Gradient': await page.locator('header').isVisible(),
            'Tab Navigation': await page.locator('.tab-navigation').isVisible(),
            '2-Phasen-Suche': await page.locator('#two_phase_enabled').isVisible(),
            'Smart-Search': await page.locator('#smart_search_enabled').isVisible(),
            'Container Styling': await page.locator('.container').isVisible()
        };
        
        for (const [element, visible] of Object.entries(designElements)) {
            console.log(`📊 [TEST 3] ${element}: ${visible ? '✅ OK' : '❌ FEHLT'}`);
        }
        
        // 4. TEST: JAVASCRIPT MODULE
        console.log('🔬 [TEST 4] JavaScript-Module testen...');
        
        const jsModules = await page.evaluate(() => {
            return {
                'API_BASE_URL': typeof window.API_BASE_URL,
                'TabAutoLoader': typeof window.TabAutoLoader,
                'sanitizeHTML': typeof window.sanitizeHTML,
                'loadModelsForFilter': typeof window.loadModelsForFilter,
                'ComparisonEngine': typeof window.ComparisonEngine
            };
        });
        
        for (const [module, type] of Object.entries(jsModules)) {
            const available = type !== 'undefined';
            console.log(`📊 [TEST 4] ${module}: ${available ? '✅ OK' : '❌ FEHLT'} (${type})`);
        }
        
        // 5. TEST: EXTERNE BIBLIOTHEKEN
        console.log('🔬 [TEST 5] Externe Bibliotheken testen...');
        
        const externalLibs = await page.evaluate(() => {
            return {
                'HTMX': typeof window.htmx,
                'Chart.js': typeof window.Chart
            };
        });
        
        for (const [lib, type] of Object.entries(externalLibs)) {
            const available = type !== 'undefined';
            console.log(`📊 [TEST 5] ${lib}: ${available ? '✅ OK' : '❌ FEHLT'} (${type})`);
        }
        
        // FINAL SCREENSHOT
        await page.screenshot({ 
            path: '/app/repair_validation_final.png', 
            fullPage: true 
        });
        console.log('📸 [REPAIR-TEST] Screenshot gespeichert: /app/repair_validation_final.png');
        
        // ZUSAMMENFASSUNG
        console.log('\\n🎯 [ZUSAMMENFASSUNG] Reparatur-Test Ergebnisse:');
        console.log(`📊 Tab-Navigation: ${Object.values(tabTestResults).filter(r => r.clickable && r.cssClass).length}/5 funktional`);
        console.log(`📊 Modelle: ${modelCheckboxes} geladen`);
        console.log(`📊 UI-Elemente: ${Object.values(designElements).filter(v => v).length}/${Object.keys(designElements).length} vorhanden`);
        console.log(`📊 JS-Module: ${Object.values(jsModules).filter(t => t !== 'undefined').length}/${Object.keys(jsModules).length} verfügbar`);
        console.log(`📊 Externe Libs: ${Object.values(externalLibs).filter(t => t !== 'undefined').length}/${Object.keys(externalLibs).length} geladen`);
        console.log(`📊 Netzwerk: ${loadedResources.filter(r => r.status === 200).length}/${loadedResources.length} Ressourcen OK`);
        
    } catch (error) {
        console.error('❌ [REPAIR-TEST] Fehler:', error.message);
        await page.screenshot({ 
            path: '/app/repair_test_error.png', 
            fullPage: true 
        });
    } finally {
        await browser.close();
    }
})();