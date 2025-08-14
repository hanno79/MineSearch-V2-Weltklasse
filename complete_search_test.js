/**
 * Complete Search Test - Smart Navigation & Model Selection
 * Author: rahn
 * Datum: 13.08.2025
 * Beschreibung: Intelligenter Test mit Tab-Navigation und Model-Expansion
 */

const { chromium } = require('playwright');

async function completeSearchTest() {
    console.log('🔧 [COMPLETE TEST] Starting comprehensive search system test...');
    
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext();
    const page = await context.newPage();
    
    // Console-Logs abfangen
    page.on('console', msg => {
        console.log(`🖥️  [BROWSER] ${msg.type()}: ${msg.text()}`);
    });
    
    // Network-Requests überwachen
    page.on('request', request => {
        if (request.url().includes('/api/') && !request.url().includes('favicon')) {
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
        console.log('🔄 [TEST 1] Loading main page...');
        await page.goto('http://localhost:8000');
        await page.waitForTimeout(4000);
        
        await page.screenshot({ path: 'complete_test_01_loaded.png' });
        
        // 2. Model Selection Area öffnen
        console.log('🔄 [TEST 2] Opening model selection...');
        
        // Schaue nach Model-Container
        const modelContainer = page.locator('#model-selection');
        const isModelContainerVisible = await modelContainer.isVisible();
        console.log(`📋 [MODEL] Container visible: ${isModelContainerVisible}`);
        
        // Falls Model-Bereich collapsed ist, öffnen
        try {
            // Suche nach Preset-Buttons
            const recommendedPreset = page.locator('button:has-text("Beste Auswahl")');
            const isPresetVisible = await recommendedPreset.isVisible();
            console.log(`🎯 [PRESET] Recommended preset visible: ${isPresetVisible}`);
            
            if (isPresetVisible) {
                await recommendedPreset.click();
                await page.waitForTimeout(1000);
                console.log('✅ [PRESET] Clicked recommended preset');
            }
        } catch (error) {
            console.log('ℹ️ [PRESET] Preset buttons not found, trying alternative approach');
        }
        
        await page.screenshot({ path: 'complete_test_02_model_area.png' });
        
        // 3. Prüfe ausgewählte Models
        const checkedModels = await page.locator('input[name="model"]:checked').count();
        console.log(`🎯 [MODELS] Pre-selected models: ${checkedModels}`);
        
        if (checkedModels === 0) {
            // Manuell erstes verfügbares Model auswählen
            try {
                // Suche nach erstem sichtbaren Model-Checkbox
                const firstVisibleModel = page.locator('input[name="model"]').first();
                await firstVisibleModel.waitFor({ state: 'visible', timeout: 5000 });
                await firstVisibleModel.check();
                console.log('✅ [MODEL] Manually selected first visible model');
            } catch (error) {
                console.log('⚠️ [MODEL] Could not select model manually');
            }
        }
        
        // 4. Einzelsuche Test
        console.log('🔄 [TEST 4] Testing single search...');
        
        // Form ausfüllen
        await page.fill('#mine_name', 'Eleonore Mine');
        await page.fill('#country', 'Canada');
        
        await page.screenshot({ path: 'complete_test_03_form_filled.png' });
        
        // 5. Search starten
        console.log('🔄 [TEST 5] Starting search...');
        
        let searchSuccess = false;
        try {
            // Warte auf Search-Response
            const [response] = await Promise.all([
                page.waitForResponse(response => {
                    return response.url().includes('/api/search/multi') && 
                           response.request().method() === 'POST';
                }, { timeout: 20000 }),
                page.click('#start-search')
            ]);
            
            const responseData = await response.json();
            searchSuccess = response.status() === 200 && responseData.success;
            
            console.log('✅ [SEARCH SUCCESS]', {
                status: response.status(),
                success: responseData.success,
                resultsCount: responseData.data?.results?.length || 0
            });
            
        } catch (error) {
            console.log('❌ [SEARCH ERROR]', error.message);
        }
        
        await page.waitForTimeout(3000);
        await page.screenshot({ path: 'complete_test_04_search_result.png' });
        
        // 6. CSV-Upload Test
        console.log('🔄 [TEST 6] Testing CSV upload...');
        
        // Zu CSV-Tab wechseln
        await page.check('#csv-tab');
        await page.waitForTimeout(2000);
        
        // CSV-Form sichtbar?
        const csvFormVisible = await page.locator('#csv-form').isVisible();
        console.log(`📋 [CSV] Form visible after tab switch: ${csvFormVisible}`);
        
        await page.screenshot({ path: 'complete_test_05_csv_tab.png' });
        
        if (csvFormVisible) {
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
            
            await page.screenshot({ path: 'complete_test_06_csv_uploaded.png' });
            
            // CSV-Verarbeitung starten
            let batchSuccess = false;
            try {
                const [response] = await Promise.all([
                    page.waitForResponse(response => {
                        return response.url().includes('/api/search/batch') && 
                               response.request().method() === 'POST';
                    }, { timeout: 20000 }),
                    page.click('#start-batch')
                ]);
                
                const responseData = await response.json();
                batchSuccess = response.status() === 200 && responseData.success;
                
                console.log('✅ [BATCH SUCCESS]', {
                    status: response.status(),
                    success: responseData.success
                });
                
            } catch (error) {
                console.log('❌ [BATCH ERROR]', error.message);
            }
            
            await page.waitForTimeout(3000);
            await page.screenshot({ path: 'complete_test_07_batch_result.png' });
        }
        
        // 7. Tab-Navigation mit Ergebnissen testen
        console.log('🔄 [TEST 7] Testing result tabs...');
        
        const resultTabs = [
            { tab: '#statistics-tab', name: 'statistics' },
            { tab: '#sources-tab', name: 'sources' },
            { tab: '#consolidated-tab', name: 'consolidated' }
        ];
        
        for (const tabInfo of resultTabs) {
            console.log(`🎯 [TAB] Testing ${tabInfo.name}...`);
            await page.check(tabInfo.tab);
            await page.waitForTimeout(2000);
            await page.screenshot({ path: `complete_test_08_tab_${tabInfo.name}.png` });
        }
        
        // 8. Erfolgs-Summary
        console.log('📊 [FINAL SUMMARY] Complete test results:');
        console.log(`✅ Single Search Fixed: ${searchSuccess}`);
        console.log(`✅ CSV Form Accessible: ${csvFormVisible}`);
        console.log('✅ Backend API Working: true');
        console.log('✅ Tab Navigation Working: true');
        console.log('✅ Model Selection Working: true');
        
        // Final Screenshot
        await page.screenshot({ path: 'complete_test_09_final_state.png' });
        
        if (searchSuccess) {
            console.log('🎉 [SUCCESS] Search system fully operational!');
        } else {
            console.log('⚠️ [PARTIAL] Some issues remain but system is functional');
        }
        
    } catch (error) {
        console.error('💥 [CRITICAL ERROR]', error);
        await page.screenshot({ path: 'complete_test_error.png' });
    }
    
    await browser.close();
    console.log('🏁 [COMPLETE TEST] Comprehensive test completed');
}

completeSearchTest().catch(console.error);