/**
 * Search Fix Validation Test
 * Author: rahn
 * Datum: 13.08.2025
 * Beschreibung: Validierung der Search-Button Fixes für Einzelsuche und CSV-Upload
 */

const { chromium } = require('playwright');

async function validateSearchFixes() {
    console.log('🔧 [SEARCH FIX] Starting search system fix validation...');
    
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext();
    const page = await context.newPage();
    
    // Console-Logs abfangen
    page.on('console', msg => {
        console.log(`🖥️  [BROWSER] ${msg.type()}: ${msg.text()}`);
    });
    
    // Network-Requests überwachen
    page.on('request', request => {
        if (request.url().includes('/api/')) {
            console.log(`📡 [REQUEST] ${request.method()} ${request.url()}`);
        }
    });
    
    page.on('response', response => {
        if (response.url().includes('/api/')) {
            console.log(`📨 [RESPONSE] ${response.status()} ${response.url()}`);
        }
    });
    
    try {
        // 1. Hauptseite laden
        console.log('🔄 [TEST 1] Loading fixed main page...');
        await page.goto('http://localhost:8000');
        await page.waitForTimeout(3000);
        
        await page.screenshot({ path: 'search_fix_01_loaded.png' });
        
        // 2. Form-Element validieren
        console.log('🔄 [TEST 2] Validating form elements...');
        
        const singleForm = await page.locator('#single-search-form').isVisible();
        const csvForm = await page.locator('#csv-form').isVisible();
        const startButton = await page.locator('#start-search').isVisible();
        const batchButton = await page.locator('#start-batch').isVisible();
        
        console.log('📋 [FORM VALIDATION]', {
            singleForm,
            csvForm,
            startButton,
            batchButton
        });
        
        // 3. Einzelsuche Test
        console.log('🔄 [TEST 3] Testing single search...');
        
        // Form ausfüllen
        await page.fill('#mine_name', 'Eleonore Mine');
        await page.fill('#country', 'Canada');
        
        // Erstes verfügbares Modell auswählen (spezifischer Selector)
        const firstModel = page.locator('input[name="model"]:checked').first();
        const isModelSelected = await firstModel.isVisible();
        console.log(`🎯 [MODEL] At least one model pre-selected: ${isModelSelected}`);
        
        if (!isModelSelected) {
            // Fallback: Manuell erstes Modell auswählen
            await page.check('input[name="model"]');
            console.log('✅ [MODEL] Manually selected first model');
        }
        
        await page.screenshot({ path: 'search_fix_02_form_filled.png' });
        
        // 4. Search-Button Click mit Response-Monitoring
        console.log('🔄 [TEST 4] Testing search button click...');
        
        let searchResponse = null;
        try {
            // Warte auf Search-Response
            const [response] = await Promise.all([
                page.waitForResponse(response => 
                    response.url().includes('/api/search/multi') && 
                    response.request().method() === 'POST',
                    { timeout: 15000 }
                ),
                page.click('#start-search')
            ]);
            
            searchResponse = response;
            const responseData = await response.json();
            
            console.log('✅ [SEARCH SUCCESS]', {
                status: response.status(),
                success: responseData.success,
                resultsCount: responseData.data?.results?.length || 0
            });
            
        } catch (error) {
            console.log('❌ [SEARCH ERROR]', error.message);
        }
        
        await page.waitForTimeout(3000);
        await page.screenshot({ path: 'search_fix_03_search_results.png' });
        
        // 5. CSV-Upload Test
        console.log('🔄 [TEST 5] Testing CSV upload...');
        
        // Zu CSV-Tab wechseln
        await page.check('#csv-tab');
        await page.waitForTimeout(1000);
        
        // Test CSV-Datei erstellen
        const testCSV = `mine_name,country,commodity,region
Eleonore Mine,Canada,Gold,Quebec
Canadian Malartic,Canada,Gold,Quebec`;
        
        // Temporäre CSV-Datei schreiben
        const fs = require('fs');
        const tmpCSVPath = '/tmp/test_mines.csv';
        fs.writeFileSync(tmpCSVPath, testCSV);
        
        // CSV-File hochladen
        await page.setInputFiles('#csv_file', tmpCSVPath);
        
        await page.screenshot({ path: 'search_fix_04_csv_uploaded.png' });
        
        // CSV-Verarbeitung starten
        let batchResponse = null;
        try {
            const [response] = await Promise.all([
                page.waitForResponse(response => 
                    response.url().includes('/api/search/batch') && 
                    response.request().method() === 'POST',
                    { timeout: 15000 }
                ),
                page.click('#start-batch')
            ]);
            
            batchResponse = response;
            const responseData = await response.json();
            
            console.log('✅ [BATCH SUCCESS]', {
                status: response.status(),
                success: responseData.success
            });
            
        } catch (error) {
            console.log('❌ [BATCH ERROR]', error.message);
        }
        
        await page.waitForTimeout(5000);
        await page.screenshot({ path: 'search_fix_05_batch_results.png' });
        
        // 6. Tab-Navigation zu Ergebnissen testen
        console.log('🔄 [TEST 6] Testing tab navigation with results...');
        
        const tabs = ['#statistics-tab', '#sources-tab', '#consolidated-tab'];
        for (const tab of tabs) {
            console.log(`🎯 [TAB] Testing ${tab}...`);
            await page.check(tab);
            await page.waitForTimeout(2000);
            await page.screenshot({ path: `search_fix_06_tab_${tab.replace('#', '').replace('-tab', '')}.png` });
        }
        
        // 7. Erfolgs-Summary
        console.log('📊 [SUMMARY] Search fix validation completed');
        console.log('✅ [RESULTS]', {
            singleSearchFixed: searchResponse?.status() === 200,
            batchSearchFixed: batchResponse?.status() === 200,
            formsWorking: singleForm && csvForm,
            buttonsWorking: startButton && batchButton
        });
        
    } catch (error) {
        console.error('💥 [CRITICAL ERROR]', error);
        await page.screenshot({ path: 'search_fix_error.png' });
    }
    
    await browser.close();
    console.log('🏁 [SEARCH FIX] Validation completed');
}

validateSearchFixes().catch(console.error);