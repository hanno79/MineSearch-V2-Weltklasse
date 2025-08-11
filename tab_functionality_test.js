/**
 * Playwright Test für MineSearch 2.0 Tab-Funktionalität
 * Testet Tab-Navigation, Content-Display und Auto-Loading
 */

const { chromium } = require('playwright');

(async () => {
    console.log('🔍 MineSearch 2.0 Tab-Funktionalität Test');
    console.log('========================================\n');

    const browser = await chromium.launch({ 
        headless: false,
        slowMo: 1500
    });
    
    const context = await browser.newContext();
    const page = await context.newPage();
    
    // Console messages sammeln
    const consoleMessages = [];
    
    page.on('console', msg => {
        const type = msg.type();
        const text = msg.text();
        consoleMessages.push({ type, text });
        
        if (text.includes('TAB-AUTOLOADER') || text.includes('STATISTICS') || text.includes('SOURCES')) {
            console.log(`📝 [${type.toUpperCase()}]: ${text}`);
        }
    });
    
    try {
        console.log('📱 Navigiere zu http://localhost:8000...');
        await page.goto('http://localhost:8000', { 
            waitUntil: 'networkidle',
            timeout: 30000 
        });
        
        console.log('✅ Seite geladen\n');
        
        // Test 1: Alle Tabs sind sichtbar
        console.log('🔍 TEST 1: Tab-Sichtbarkeit');
        const tabs = ['single-tab', 'csv-tab', 'sources-tab', 'statistics-tab', 'consolidated-tab'];
        
        for (const tabId of tabs) {
            const tab = await page.$(`#${tabId}`);
            const label = await page.$(`label[for="${tabId}"]`);
            console.log(`   ${tabId}: ${tab ? '✅' : '❌'} Radio Button | ${label ? '✅' : '❌'} Label`);
        }
        
        // Test 2: Default-Tab Content
        console.log('\n🔍 TEST 2: Default Single-Tab Content');
        await page.waitForTimeout(2000);
        
        const singleFormVisible = await page.isVisible('#single_form');
        console.log(`   single_form sichtbar: ${singleFormVisible ? '✅' : '❌'}`);
        
        const modelSelection = await page.isVisible('#model-selection');
        console.log(`   model-selection sichtbar: ${modelSelection ? '✅' : '❌'}`);
        
        // Screenshot vom Default-Zustand
        await page.screenshot({ 
            path: '/app/tab_test_01_default.png',
            fullPage: true 
        });
        console.log('   📸 Screenshot: tab_test_01_default.png');
        
        // Test 3: Tab-Wechsel zu Quellen
        console.log('\n🔍 TEST 3: Wechsel zu Quellen-Tab');
        await page.click('label[for="sources-tab"]');
        await page.waitForTimeout(3000); // Warte auf Auto-Loading
        
        const sourcesFormVisible = await page.isVisible('#sources_form');
        console.log(`   sources_form sichtbar: ${sourcesFormVisible ? '✅' : '❌'}`);
        
        const sourcesTableContainer = await page.isVisible('#sources-table-container');
        console.log(`   sources-table-container sichtbar: ${sourcesTableContainer ? '✅' : '❌'}`);
        
        // Prüfe ob Tabellen-Content geladen wurde
        const sourcesTableContent = await page.textContent('#sources-table-container');
        const hasTableData = sourcesTableContent && sourcesTableContent.includes('Domain');
        console.log(`   Tabellen-Daten geladen: ${hasTableData ? '✅' : '❌'}`);
        
        await page.screenshot({ 
            path: '/app/tab_test_02_sources.png',
            fullPage: true 
        });
        console.log('   📸 Screenshot: tab_test_02_sources.png');
        
        // Test 4: Tab-Wechsel zu Statistiken
        console.log('\n🔍 TEST 4: Wechsel zu Statistiken-Tab');
        await page.click('label[for="statistics-tab"]');
        await page.waitForTimeout(3000); // Warte auf Auto-Loading
        
        const statsFormVisible = await page.isVisible('#statistics_form');
        console.log(`   statistics_form sichtbar: ${statsFormVisible ? '✅' : '❌'}`);
        
        const statsContainer = await page.isVisible('#model-statistics-table-container');
        console.log(`   model-statistics-table-container sichtbar: ${statsContainer ? '✅' : '❌'}`);
        
        // Prüfe ob Statistiken geladen wurden
        const statsContent = await page.textContent('#model-statistics-table-container');
        const hasStatsData = statsContent && (statsContent.includes('Modell') || statsContent.includes('Provider'));
        console.log(`   Statistik-Daten geladen: ${hasStatsData ? '✅' : '❌'}`);
        
        await page.screenshot({ 
            path: '/app/tab_test_03_statistics.png',
            fullPage: true 
        });
        console.log('   📸 Screenshot: tab_test_03_statistics.png');
        
        // Test 5: Tab-Wechsel zu Konsolidiert
        console.log('\n🔍 TEST 5: Wechsel zu Konsolidiert-Tab');
        await page.click('label[for="consolidated-tab"]');
        await page.waitForTimeout(3000);
        
        const consolidatedFormVisible = await page.isVisible('#consolidated_form');
        console.log(`   consolidated_form sichtbar: ${consolidatedFormVisible ? '✅' : '❌'}`);
        
        const consolidatedContainer = await page.isVisible('#consolidated-table-container');
        console.log(`   consolidated-table-container sichtbar: ${consolidatedContainer ? '✅' : '❌'}`);
        
        await page.screenshot({ 
            path: '/app/tab_test_04_consolidated.png',
            fullPage: true 
        });
        console.log('   📸 Screenshot: tab_test_04_consolidated.png');
        
        // Test 6: CSV-Tab
        console.log('\n🔍 TEST 6: Wechsel zu CSV-Tab');
        await page.click('label[for="csv-tab"]');
        await page.waitForTimeout(1000);
        
        const csvFormVisible = await page.isVisible('#csv_form');
        console.log(`   csv_form sichtbar: ${csvFormVisible ? '✅' : '❌'}`);
        
        await page.screenshot({ 
            path: '/app/tab_test_05_csv.png',
            fullPage: true 
        });
        console.log('   📸 Screenshot: tab_test_05_csv.png');
        
        // Test 7: Zurück zu Single-Tab
        console.log('\n🔍 TEST 7: Zurück zu Single-Tab');
        await page.click('label[for="single-tab"]');
        await page.waitForTimeout(1000);
        
        const singleFormVisible2 = await page.isVisible('#single_form');
        console.log(`   single_form wieder sichtbar: ${singleFormVisible2 ? '✅' : '❌'}`);
        
        console.log('\n📋 ZUSAMMENFASSUNG:');
        console.log('================');
        
        const autoloaderMessages = consoleMessages.filter(msg => 
            msg.text.includes('TAB-AUTOLOADER') || 
            msg.text.includes('Loading sources') || 
            msg.text.includes('Loading statistics')
        );
        
        console.log(`   Console Auto-Loader Messages: ${autoloaderMessages.length}`);
        console.log(`   Screenshots erstellt: 5`);
        
        if (autoloaderMessages.length > 0) {
            console.log('\n🔄 Auto-Loader Activity:');
            autoloaderMessages.slice(0, 5).forEach(msg => {
                console.log(`   - ${msg.text}`);
            });
        }
        
        console.log('\n⏰ Browser bleibt 10 Sekunden offen für Inspektion...');
        await page.waitForTimeout(10000);
        
    } catch (error) {
        console.error(`💥 Test Fehler: ${error.message}`);
    }
    
    await browser.close();
    console.log('\n✅ Tab-Funktionalität Test abgeschlossen');
})();