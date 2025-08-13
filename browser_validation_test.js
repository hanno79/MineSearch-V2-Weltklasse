/**
 * Author: rahn
 * Datum: 13.08.2025
 * Version: 1.0
 * Beschreibung: Systematische Browser-Validierung für MineSearch 2.0
 */

const { chromium } = require('playwright');

async function validateMineSearchBrowser() {
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext({ 
        viewport: { width: 1920, height: 1080 } 
    });
    const page = await context.newPage();

    console.log('🚀 Starte MineSearch 2.0 Browser-Validierung...');

    try {
        // 1. GRUNDFUNKTIONALITÄT: Hauptseite laden
        console.log('\n=== PHASE 1: GRUNDFUNKTIONALITÄT ===');
        await page.goto('http://localhost:8000');
        await page.waitForLoadState('networkidle');
        
        // Screenshot der geladenen Seite
        await page.screenshot({ path: 'hauptseite_geladen.png', fullPage: true });
        console.log('✓ Hauptseite geladen und Screenshot erstellt');

        // Header und Navigation validieren
        const header = await page.locator('header').count();
        const navTabs = await page.locator('.nav-tabs .nav-item').count();
        console.log(`✓ Header gefunden: ${header > 0 ? 'JA' : 'NEIN'}`);
        console.log(`✓ Navigation Tabs gefunden: ${navTabs} Tabs`);

        // Tab-Namen validieren
        const tabNames = await page.locator('.nav-tabs .nav-link').allTextContents();
        console.log('✓ Tab-Namen:', tabNames);

        // 2. MODEL-SELECTION DROPDOWN
        console.log('\n=== PHASE 2: MODEL-SELECTION DROPDOWN ===');
        const modelSelect = await page.locator('#model-select');
        const modelOptions = await page.locator('#model-select option').count();
        console.log(`✓ Model-Selection Dropdown: ${modelOptions} Optionen verfügbar`);

        if (modelOptions > 0) {
            const modelTexts = await page.locator('#model-select option').allTextContents();
            console.log(`✓ Erste 5 Modelle: ${modelTexts.slice(0, 5).join(', ')}`);
        }

        // 3. TAB-SYSTEM ITERATIV TESTEN
        console.log('\n=== PHASE 3: TAB-SYSTEM VALIDIERUNG ===');
        const tabs = ['search-tab', 'statistics-tab', 'results-tab', 'sources-tab', 'help-tab'];
        
        for (const tabId of tabs) {
            try {
                await page.click(`[data-bs-target="#${tabId}"]`);
                await page.waitForTimeout(500);
                
                const tabContent = await page.locator(`#${tabId}`).isVisible();
                await page.screenshot({ path: `tab_${tabId}.png` });
                console.log(`✓ Tab ${tabId}: ${tabContent ? 'SICHTBAR' : 'VERSTECKT'}`);
            } catch (error) {
                console.log(`❌ Tab ${tabId}: FEHLER - ${error.message}`);
            }
        }

        // 4. DATA-CARDS SYSTEM TESTEN
        console.log('\n=== PHASE 4: DATA-CARDS SYSTEM ===');
        // Zurück zum Search Tab
        await page.click('[data-bs-target="#search-tab"]');
        await page.waitForTimeout(500);

        // Test-Suche durchführen
        await page.fill('#mine-name', 'Grasberg Mine');
        await page.selectOption('#model-select', { index: 1 }); // Erstes verfügbares Modell
        
        await page.screenshot({ path: 'vor_test_suche.png' });
        
        // Suche starten
        await page.click('#search-btn');
        console.log('✓ Test-Suche gestartet mit "Grasberg Mine"');

        // Warten auf Ergebnisse
        await page.waitForTimeout(3000);
        await page.screenshot({ path: 'nach_test_suche.png' });

        // Prüfen ob Data-Cards erschienen sind
        const dataCards = await page.locator('.data-card').count();
        console.log(`✓ Data-Cards gefunden: ${dataCards} Cards`);

        // 5. DETAILS-BUTTONS UND MODAL TESTEN
        console.log('\n=== PHASE 5: DETAILS-BUTTONS & MODAL ===');
        if (dataCards > 0) {
            // Ersten Details-Button klicken
            await page.click('.details-btn', { timeout: 5000 });
            await page.waitForTimeout(1000);
            
            const modal = await page.locator('.modal').isVisible();
            await page.screenshot({ path: 'modal_geoeffnet.png' });
            console.log(`✓ Modal geöffnet: ${modal ? 'JA' : 'NEIN'}`);
            
            if (modal) {
                // Modal schließen
                await page.click('.modal .btn-close');
                await page.waitForTimeout(500);
            }
        }

        // 6. EXCEPTION-HANDLER VALIDATION
        console.log('\n=== PHASE 6: EXCEPTION-HANDLER VALIDATION ===');
        
        // Leere Suche testen
        await page.fill('#mine-name', '');
        await page.click('#search-btn');
        await page.waitForTimeout(1000);
        await page.screenshot({ path: 'leere_suche_test.png' });
        
        // Ungültiges Format testen
        await page.fill('#mine-name', '12345!@#$%');
        await page.click('#search-btn');
        await page.waitForTimeout(1000);
        await page.screenshot({ path: 'ungueltige_eingabe_test.png' });

        // 7. JAVASCRIPT CONSOLE ERRORS
        console.log('\n=== PHASE 7: JAVASCRIPT-CONSOLE PRÜFUNG ===');
        const consoleErrors = [];
        page.on('console', msg => {
            if (msg.type() === 'error') {
                consoleErrors.push(msg.text());
            }
        });
        
        // Seite neu laden um Console-Errors zu sammeln
        await page.reload();
        await page.waitForTimeout(2000);
        
        console.log(`✓ Console-Errors gefunden: ${consoleErrors.length}`);
        if (consoleErrors.length > 0) {
            console.log('❌ Console-Errors:', consoleErrors);
        }

        // 8. RESPONSIVE DESIGN TESTEN
        console.log('\n=== PHASE 8: RESPONSIVE DESIGN ===');
        const viewports = [
            { width: 1920, height: 1080, name: 'desktop' },
            { width: 1024, height: 768, name: 'tablet' },
            { width: 375, height: 667, name: 'mobile' }
        ];

        for (const viewport of viewports) {
            await page.setViewportSize({ width: viewport.width, height: viewport.height });
            await page.waitForTimeout(500);
            await page.screenshot({ path: `responsive_${viewport.name}.png` });
            console.log(`✓ Responsive Test ${viewport.name}: Screenshot erstellt`);
        }

        console.log('\n🎉 Browser-Validierung erfolgreich abgeschlossen!');

    } catch (error) {
        console.error('❌ KRITISCHER FEHLER bei Browser-Validierung:', error);
        await page.screenshot({ path: 'fehler_screenshot.png' });
    } finally {
        await browser.close();
    }
}

// Test starten
validateMineSearchBrowser().catch(console.error);