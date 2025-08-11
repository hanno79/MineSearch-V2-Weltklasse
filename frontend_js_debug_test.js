/**
 * Playwright Script für JavaScript Console Error Detection
 * Explizit für User-Request: Browser-basierte Fehlerdiagnose
 */

const { chromium } = require('playwright');

(async () => {
    console.log('🚀 MineSearch JavaScript Console Error Detection');
    console.log('=================================================\n');

    const browser = await chromium.launch({ 
        headless: false,
        slowMo: 1000
    });
    
    const context = await browser.newContext();
    const page = await context.newPage();
    
    // Console messages sammeln
    const consoleMessages = [];
    const errors = [];
    
    page.on('console', msg => {
        const type = msg.type();
        const text = msg.text();
        consoleMessages.push({ type, text });
        
        if (type === 'error') {
            errors.push(text);
            console.log(`❌ [CONSOLE ERROR]: ${text}`);
        } else if (type === 'warning') {
            console.log(`⚠️ [CONSOLE WARNING]: ${text}`);
        } else if (type === 'log' && (text.includes('ERROR') || text.includes('❌'))) {
            console.log(`🔴 [LOG ERROR]: ${text}`);
        }
    });
    
    page.on('pageerror', error => {
        console.log(`💥 [PAGE ERROR]: ${error.message}`);
        errors.push(`PAGE ERROR: ${error.message}`);
    });
    
    try {
        console.log('📱 Navigiere zu http://localhost:8000...');
        await page.goto('http://localhost:8000', { 
            waitUntil: 'networkidle',
            timeout: 30000 
        });
        
        console.log('✅ Seite geladen, sammle JavaScript Errors...\n');
        
        // Warte auf DOM-Initialisierung
        await page.waitForTimeout(3000);
        
        // Prüfe ob kritische Elemente existieren
        console.log('🔍 DOM Element Check:');
        
        const modelSelection = await page.$('#model-selection');
        console.log(`   model-selection: ${modelSelection ? '✅ Gefunden' : '❌ Fehlt'}`);
        
        const statisticsContainer = await page.$('#model-statistics-table-container');
        console.log(`   model-statistics-table-container: ${statisticsContainer ? '✅ Gefunden' : '❌ Fehlt'}`);
        
        const searchTab = await page.$('#single-tab');
        console.log(`   single-tab: ${searchTab ? '✅ Gefunden' : '❌ Fehlt'}`);
        
        const csvTab = await page.$('#csv-tab');
        console.log(`   csv-tab: ${csvTab ? '✅ Gefunden' : '❌ Fehlt'}`);
        
        const sourcesTab = await page.$('#sources-tab');
        console.log(`   sources-tab: ${sourcesTab ? '✅ Gefunden' : '❌ Fehlt'}`);
        
        const statisticsTab = await page.$('#statistics-tab');
        console.log(`   statistics-tab: ${statisticsTab ? '✅ Gefunden' : '❌ Fehlt'}`);
        
        // Try to trigger model loading
        console.log('\n📊 Versuche Model-Loading zu triggern...');
        try {
            await page.evaluate(() => {
                if (typeof loadModelsForFilter === 'function') {
                    console.log('🔄 loadModelsForFilter() aufgerufen...');
                    loadModelsForFilter();
                } else {
                    console.error('❌ loadModelsForFilter ist nicht definiert');
                }
            });
        } catch (e) {
            console.log(`❌ Model loading error: ${e.message}`);
        }
        
        // Warte weitere 3 Sekunden für asynchrone Aufrufe
        await page.waitForTimeout(3000);
        
        console.log('\n📋 ZUSAMMENFASSUNG:');
        console.log(`   Gesamt Console Messages: ${consoleMessages.length}`);
        console.log(`   JavaScript Errors: ${errors.length}`);
        
        if (errors.length > 0) {
            console.log('\n🚨 GEFUNDENE FEHLER:');
            errors.forEach((error, i) => {
                console.log(`   ${i + 1}. ${error}`);
            });
        }
        
        console.log('\n📸 Screenshot für visuelle Inspektion...');
        await page.screenshot({ 
            path: '/app/js_debug_screenshot.png',
            fullPage: true 
        });
        
        console.log('\n⏰ Browser bleibt 10 Sekunden offen für manuelle Inspektion...');
        await page.waitForTimeout(10000);
        
    } catch (error) {
        console.error(`💥 Test Fehler: ${error.message}`);
    }
    
    await browser.close();
    console.log('\n✅ JavaScript Console Error Detection abgeschlossen');
})();