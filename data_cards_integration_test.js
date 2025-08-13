// Data-Cards Integration Test nach Reparatur
const { chromium } = require('playwright');

(async () => {
    console.log('🧪 [DATA-CARDS-TEST] Starte Data-Cards Integration Test...');
    
    const browser = await chromium.launch({ headless: false, slowMo: 500 });
    const page = await browser.newPage();
    
    try {
        // Öffne die Seite
        await page.goto('http://localhost:8000', { waitUntil: 'networkidle', timeout: 15000 });
        console.log('✅ [DATA-CARDS-TEST] Seite geladen');
        
        // Warte auf JavaScript-Initialisierung  
        await page.waitForTimeout(3000);
        
        // Test 1: Prüfe auf JavaScript-Fehler
        console.log('\n📋 [TEST 1] JavaScript-Konsole prüfen...');
        const logs = [];
        page.on('console', msg => {
            if (msg.type() === 'error') {
                logs.push(`ERROR: ${msg.text()}`);
            }
        });
        
        // Test 2: Aktiviere Quellen-Tab 
        console.log('\n📚 [TEST 2] Aktiviere Quellen-Tab...');
        await page.click('label[for="sources-tab"]');
        await page.waitForTimeout(3000); // Warte auf Quellen-Loading
        
        // Prüfe ob sources-table-container existiert
        const sourcesContainer = await page.locator('#sources-table-container').count();
        console.log(`   sources-table-container gefunden: ${sourcesContainer > 0 ? '✅' : '❌'}`);
        
        // Prüfe ob Data-Cards geladen werden
        await page.waitForTimeout(2000);
        const dataCards = await page.locator('.mine-data-card').count();
        console.log(`   Data-Cards gefunden: ${dataCards} Karten`);
        
        // Test 3: Aktiviere Statistiken-Tab
        console.log('\n📈 [TEST 3] Aktiviere Statistiken-Tab...');
        await page.click('label[for="statistics-tab"]');
        await page.waitForTimeout(3000);
        
        // Prüfe Statistiken-Container
        const statsContainer = await page.locator('#model-statistics-table-container').count();
        console.log(`   model-statistics-table-container gefunden: ${statsContainer > 0 ? '✅' : '❌'}`);
        
        // Warte etwas länger für Statistiken-Loading
        await page.waitForTimeout(3000);
        const statsCards = await page.locator('.mine-data-card').count();
        console.log(`   Statistik-Cards gefunden: ${statsCards} Karten`);
        
        // Test 4: Aktiviere Konsolidiert-Tab
        console.log('\n📋 [TEST 4] Aktiviere Konsolidiert-Tab...');
        await page.click('label[for="consolidated-tab"]');
        await page.waitForTimeout(3000);
        
        // Prüfe Konsolidiert-Container
        const consolidatedContainer = await page.locator('#consolidated-table-container').count();
        console.log(`   consolidated-table-container gefunden: ${consolidatedContainer > 0 ? '✅' : '❌'}`);
        
        await page.waitForTimeout(3000);
        const consolidatedCards = await page.locator('.mine-data-card').count();
        console.log(`   Konsolidierte-Cards gefunden: ${consolidatedCards} Karten`);
        
        // Test 5: Prüfe CSS-Variablen
        console.log('\n🎨 [TEST 5] CSS-Variablen prüfen...');
        const primaryColor = await page.evaluate(() => {
            return getComputedStyle(document.documentElement).getPropertyValue('--primary-600');
        });
        console.log(`   --primary-600: ${primaryColor ? '✅' : '❌'} (${primaryColor})`);
        
        const spaceXl = await page.evaluate(() => {
            return getComputedStyle(document.documentElement).getPropertyValue('--space-xl');
        });
        console.log(`   --space-xl: ${spaceXl ? '✅' : '❌'} (${spaceXl})`);
        
        // Test 6: JavaScript-Funktionen prüfen
        console.log('\n⚙️ [TEST 6] JavaScript-Funktionen prüfen...');
        const functions = await page.evaluate(() => {
            const results = {};
            results.renderDataCardGrid = typeof window.renderDataCardGrid;
            results.displayGroupedSources = typeof window.displayGroupedSources;
            results.displayConsolidatedResults = typeof window.displayConsolidatedResults;
            results.displayComprehensiveModelStatistics = typeof window.displayComprehensiveModelStatistics;
            return results;
        });
        
        Object.entries(functions).forEach(([name, type]) => {
            console.log(`   ${name}: ${type === 'function' ? '✅' : '❌'} (${type})`);
        });
        
        // Zusammenfassung
        const totalCards = dataCards + statsCards + consolidatedCards;
        const containersFound = sourcesContainer + statsContainer + consolidatedContainer;
        const cssVariablesOk = primaryColor && spaceXl;
        const functionsOk = Object.values(functions).every(type => type === 'function');
        
        console.log('\n' + '='.repeat(60));
        console.log('🎯 [DATA-CARDS-TEST] ZUSAMMENFASSUNG:');
        console.log('='.repeat(60));
        console.log(`✅ Container gefunden: ${containersFound}/3`);
        console.log(`🎨 Data-Cards geladen: ${totalCards} insgesamt`);
        console.log(`🎨 CSS-Variablen: ${cssVariablesOk ? 'OK' : 'FEHLER'}`);
        console.log(`⚙️ JavaScript-Funktionen: ${functionsOk ? 'OK' : 'FEHLER'}`);
        console.log(`❌ JavaScript-Fehler: ${logs.length}`);
        
        if (logs.length > 0) {
            console.log('\n📋 JAVASCRIPT-FEHLER:');
            logs.forEach(log => console.log(`   ${log}`));
        }
        
        const allTestsPassed = containersFound === 3 && totalCards > 0 && cssVariablesOk && functionsOk && logs.length === 0;
        
        if (allTestsPassed) {
            console.log('\n🎉 [DATA-CARDS-TEST] ✅ ALLE TESTS BESTANDEN!');
            console.log('   Data-Cards funktionieren korrekt');
            console.log('   Tab-System zeigt moderne Cards an');
            console.log('   Keine JavaScript-Fehler');
        } else {
            console.log('\n⚠️ [DATA-CARDS-TEST] ❌ EINIGE TESTS FEHLGESCHLAGEN');
            console.log('   Weitere Anpassungen erforderlich');
        }
        
        // Screenshot für Dokumentation
        await page.screenshot({ path: '/app/data_cards_final_test.png', fullPage: true });
        console.log('📸 Screenshot gespeichert: data_cards_final_test.png');
        
    } catch (error) {
        console.log(`❌ [DATA-CARDS-TEST] Fehler: ${error.message}`);
    } finally {
        await browser.close();
    }
})();