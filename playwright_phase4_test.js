const { chromium } = require('playwright');

(async () => {
    console.log('🚀 [PLAYWRIGHT] Starte Phase 4 UI-Test...');
    const browser = await chromium.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    
    const page = await browser.newPage();
    
    try {
        // Lade MineSearch 2.0 UI
        console.log('📋 [PLAYWRIGHT] Lade http://localhost:8000...');
        await page.goto('http://localhost:8000', { 
            waitUntil: 'networkidle', 
            timeout: 15000 
        });
        
        console.log('✅ [PLAYWRIGHT] Seite geladen');
        
        // Warte auf Module Loading
        await page.waitForTimeout(2000);
        
        // Prüfe Phase 4 Elemente
        const title = await page.textContent('h1');
        console.log(`📋 [PLAYWRIGHT] Titel: ${title}`);
        
        // Prüfe Modelle-Loading
        const modelSection = await page.locator('#model-selection').isVisible();
        console.log(`📋 [PLAYWRIGHT] Model Selection sichtbar: ${modelSection}`);
        
        // Warte auf Model-Loading (5 Sekunden)
        console.log('⏳ [PLAYWRIGHT] Warte auf Modelle...');
        await page.waitForTimeout(5000);
        
        // Prüfe ob Modelle geladen
        const modelCheckboxes = await page.locator('input[type="checkbox"]').count();
        console.log(`📊 [PLAYWRIGHT] Anzahl Modelle: ${modelCheckboxes}`);
        
        // Prüfe Style-Verbesserungen
        const styleFile = await page.locator('link[href*="style.css"]').isVisible();
        console.log(`🎨 [PLAYWRIGHT] Style.css geladen: ${styleFile}`);
        
        // Prüfe Phase 4 Module
        const comparisonEngine = await page.evaluate(() => {
            return typeof window.ComparisonEngine !== 'undefined';
        });
        console.log(`🔬 [PLAYWRIGHT] ComparisonEngine verfügbar: ${comparisonEngine}`);
        
        // Prüfe Visual Design
        const containerStyle = await page.evaluate(() => {
            const container = document.querySelector('.container');
            if (!container) return 'not found';
            const style = window.getComputedStyle(container);
            return {
                backgroundColor: style.backgroundColor,
                borderRadius: style.borderRadius,
                padding: style.padding
            };
        });
        console.log(`🎨 [PLAYWRIGHT] Container-Style:`, JSON.stringify(containerStyle));
        
        // Prüfe Header
        const subtitle = await page.locator('.subtitle').textContent();
        console.log(`📋 [PLAYWRIGHT] Untertitel: ${subtitle}`);
        
        // Screenshot
        await page.screenshot({ 
            path: '/app/phase4_ui_test.png', 
            fullPage: true 
        });
        console.log('📸 [PLAYWRIGHT] Screenshot gespeichert: /app/phase4_ui_test.png');
        
        console.log('✅ [PLAYWRIGHT] Test abgeschlossen');
        
    } catch (error) {
        console.error('❌ [PLAYWRIGHT] Fehler:', error.message);
        await page.screenshot({ 
            path: '/app/phase4_error.png', 
            fullPage: true 
        });
    } finally {
        await browser.close();
    }
})();