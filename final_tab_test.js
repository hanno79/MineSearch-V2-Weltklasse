// Finaler Tab-Test mit Label-Klicks (Radio Buttons sind hidden)
const { chromium } = require('playwright');

(async () => {
    console.log('🧪 [FINAL-TAB-TEST] Starte finalen Tab-Test...');
    
    const browser = await chromium.launch({ headless: false, slowMo: 1000 });
    const page = await browser.newPage();
    
    try {
        // Öffne die Seite
        await page.goto('http://localhost:8000', { waitUntil: 'networkidle', timeout: 15000 });
        console.log('✅ [FINAL-TAB-TEST] Seite geladen');
        
        // Warte auf JavaScript-Initialisierung  
        await page.waitForTimeout(3000);
        
        // Test 1: Initial State - Einzelsuche sichtbar
        console.log('\n🔍 [TEST 1] Initial State - Einzelsuche-Tab');
        const singleVisible = await page.isVisible('#single-search');
        console.log(`   Einzelsuche sichtbar: ${singleVisible ? '✅' : '❌'}`);
        
        // Test 2: CSV Tab aktivieren über Label
        console.log('\n📊 [TEST 2] Aktiviere CSV-Tab');
        await page.click('label[for="csv-tab"]');
        await page.waitForTimeout(1000);
        
        const csvVisible = await page.isVisible('#csv-upload');
        const singleHidden = !(await page.isVisible('#single-search'));
        console.log(`   CSV sichtbar: ${csvVisible ? '✅' : '❌'}`);
        console.log(`   Einzelsuche versteckt: ${singleHidden ? '✅' : '❌'}`);
        
        // Test 3: Quellen Tab aktivieren
        console.log('\n📚 [TEST 3] Aktiviere Quellen-Tab');
        await page.click('label[for="sources-tab"]');
        await page.waitForTimeout(2000); // Mehr Zeit für Quellen-Loading
        
        const sourcesVisible = await page.isVisible('#sources');
        const csvHidden = !(await page.isVisible('#csv-upload'));
        console.log(`   Quellen sichtbar: ${sourcesVisible ? '✅' : '❌'}`);
        console.log(`   CSV versteckt: ${csvHidden ? '✅' : '❌'}`);
        
        // Test 4: Statistiken Tab  
        console.log('\n📈 [TEST 4] Aktiviere Statistiken-Tab');
        await page.click('label[for="statistics-tab"]');
        await page.waitForTimeout(2000);
        
        const statsVisible = await page.isVisible('#statistics');
        const sourcesHidden = !(await page.isVisible('#sources'));
        console.log(`   Statistiken sichtbar: ${statsVisible ? '✅' : '❌'}`);
        console.log(`   Quellen versteckt: ${sourcesHidden ? '✅' : '❌'}`);
        
        // Test 5: Konsolidiert Tab
        console.log('\n📋 [TEST 5] Aktiviere Konsolidiert-Tab');
        await page.click('label[for="consolidated-tab"]');
        await page.waitForTimeout(2000);
        
        const consolidatedVisible = await page.isVisible('#consolidated');
        const statsHidden = !(await page.isVisible('#statistics'));
        console.log(`   Konsolidiert sichtbar: ${consolidatedVisible ? '✅' : '❌'}`);
        console.log(`   Statistiken versteckt: ${statsHidden ? '✅' : '❌'}`);
        
        // Test 6: Zurück zu Einzelsuche
        console.log('\n🔍 [TEST 6] Zurück zu Einzelsuche');
        await page.click('label[for="single-tab"]');
        await page.waitForTimeout(1000);
        
        const singleVisibleFinal = await page.isVisible('#single-search');
        const consolidatedHidden = !(await page.isVisible('#consolidated'));
        console.log(`   Einzelsuche sichtbar: ${singleVisibleFinal ? '✅' : '❌'}`);
        console.log(`   Konsolidiert versteckt: ${consolidatedHidden ? '✅' : '❌'}`);
        
        // FINAL RESULTS
        const allTests = [
            singleVisible, csvVisible, singleHidden, sourcesVisible, csvHidden,
            statsVisible, sourcesHidden, consolidatedVisible, statsHidden,
            singleVisibleFinal, consolidatedHidden
        ];
        
        const successCount = allTests.filter(test => test).length;
        const success = successCount === allTests.length;
        
        console.log('\n' + '='.repeat(60));
        console.log('🎯 [FINAL-TAB-TEST] ZUSAMMENFASSUNG:');
        console.log('='.repeat(60));
        console.log(`✅ Erfolgreiche Tests: ${successCount}/${allTests.length}`);
        console.log(`🔄 Tab-Navigation: ${success ? 'FUNKTIONIERT' : 'FEHLERHAFT'}`);
        console.log(`🎨 CSS Tab-Sichtbarkeit: ${success ? 'OK' : 'PROBLEM'}`);
        
        if (success) {
            console.log('🎉 [FINAL-TAB-TEST] ✅ PHASE 3 TAB-REVOLUTION ERFOLGREICH!');
            console.log('   Alle Tabs funktionieren - nur aktiver Tab sichtbar');
        } else {
            console.log('⚠️ [FINAL-TAB-TEST] ❌ Tab-System benötigt Korrekturen');
        }
        
        // Screenshot für Dokumentation
        await page.screenshot({ path: '/app/tab_system_final_test.png', fullPage: true });
        console.log('📸 Screenshot gespeichert: tab_system_final_test.png');
        
    } catch (error) {
        console.log(`❌ [FINAL-TAB-TEST] Fehler: ${error.message}`);
    } finally {
        await browser.close();
    }
})();