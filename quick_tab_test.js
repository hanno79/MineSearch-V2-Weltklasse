// Schneller Tab-System Test mit Node.js und Playwright
const { chromium } = require('playwright');

(async () => {
    console.log('🧪 [QUICK-TAB-TEST] Starte schnellen Tab-Test...');
    
    const browser = await chromium.launch({ headless: true });
    const page = await browser.newPage();
    
    try {
        // Öffne die Seite
        await page.goto('http://localhost:8000', { waitUntil: 'networkidle', timeout: 15000 });
        console.log('✅ [QUICK-TAB-TEST] Seite geladen');
        
        // Teste Initial State: Einzelsuche aktiv
        const singleVisible = await page.isVisible('#single-search');
        console.log(`🔍 [QUICK-TAB-TEST] Einzelsuche initial sichtbar: ${singleVisible ? '✅' : '❌'}`);
        
        // Teste CSV Tab
        await page.click('#csv-tab');
        await page.waitForTimeout(500);
        const csvVisible = await page.isVisible('#csv-upload');
        const singleHidden = !(await page.isVisible('#single-search'));
        console.log(`📊 [QUICK-TAB-TEST] CSV sichtbar, Einzelsuche versteckt: ${csvVisible && singleHidden ? '✅' : '❌'}`);
        
        // Teste Sources Tab
        await page.click('#sources-tab');  
        await page.waitForTimeout(1000);
        const sourcesVisible = await page.isVisible('#sources');
        const csvHidden = !(await page.isVisible('#csv-upload'));
        console.log(`📚 [QUICK-TAB-TEST] Quellen sichtbar, CSV versteckt: ${sourcesVisible && csvHidden ? '✅' : '❌'}`);
        
        // Zusammenfassung
        const success = singleVisible && csvVisible && singleHidden && sourcesVisible && csvHidden;
        console.log(`\n🎯 [QUICK-TAB-TEST] ERGEBNIS: ${success ? '✅ TAB-SYSTEM FUNKTIONIERT' : '❌ TAB-SYSTEM FEHLERHAFT'}`);
        
    } catch (error) {
        console.log(`❌ [QUICK-TAB-TEST] Fehler: ${error.message}`);
    } finally {
        await browser.close();
    }
})();