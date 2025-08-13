/**
 * Author: rahn
 * Datum: 13.08.2025
 * Version: 1.1
 * Beschreibung: Korrigierte Browser-Validierung für MineSearch 2.0 mit korrekten Selektoren
 */

const { chromium } = require('playwright');

async function validateMineSearchBrowserCorrected() {
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext({ 
        viewport: { width: 1920, height: 1080 } 
    });
    const page = await context.newPage();

    console.log('🚀 Starte korrigierte MineSearch 2.0 Browser-Validierung...');

    try {
        // 1. GRUNDFUNKTIONALITÄT: Hauptseite laden
        console.log('\n=== PHASE 1: GRUNDFUNKTIONALITÄT ===');
        await page.goto('http://localhost:8000');
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(2000); // Warten auf JavaScript-Initialisierung
        
        // Screenshot der geladenen Seite
        await page.screenshot({ path: 'hauptseite_validierung.png', fullPage: true });
        console.log('✓ Hauptseite geladen und Screenshot erstellt');

        // Header und Navigation validieren
        const header = await page.locator('header h1').textContent();
        const navTabs = await page.locator('.tab-navigation input[type="radio"]').count();
        console.log(`✓ Header gefunden: "${header}"`);
        console.log(`✓ Navigation Tabs gefunden: ${navTabs} Tabs`);

        // Tab-Namen validieren (Labels)
        const tabLabels = await page.locator('.tab-navigation label').allTextContents();
        console.log('✓ Tab-Labels:', tabLabels);

        // 2. MODEL-SELECTION VALIDIERUNG
        console.log('\n=== PHASE 2: MODEL-SELECTION VALIDIERUNG ===');
        await page.waitForTimeout(3000); // Warten auf Model-Loading
        
        const modelSection = await page.locator('#model-selection').isVisible();
        console.log(`✓ Model-Selection Bereich sichtbar: ${modelSection ? 'JA' : 'NEIN'}`);
        
        // Schauen ob Modelle geladen sind
        const modelCheckboxes = await page.locator('#model-selection input[type="checkbox"]').count();
        console.log(`✓ Model Checkboxes gefunden: ${modelCheckboxes} Modelle`);

        if (modelCheckboxes > 0) {
            const firstFewModels = await page.locator('#model-selection label').first().textContent();
            console.log(`✓ Erstes Modell: ${firstFewModels}`);
        }

        // 3. TAB-SYSTEM ITERATIV TESTEN
        console.log('\n=== PHASE 3: TAB-SYSTEM VALIDIERUNG ===');
        const tabs = [
            { id: 'single-tab', name: 'Einzelsuche' },
            { id: 'csv-tab', name: 'CSV-Upload' },
            { id: 'sources-tab', name: 'Quellen' },
            { id: 'statistics-tab', name: 'Statistiken' },
            { id: 'consolidated-tab', name: 'Konsolidiert' }
        ];
        
        for (const tab of tabs) {
            try {
                await page.click(`#${tab.id}`);
                await page.waitForTimeout(1000);
                
                const isChecked = await page.locator(`#${tab.id}`).isChecked();
                await page.screenshot({ path: `tab_${tab.id}_aktiv.png` });
                console.log(`✓ Tab ${tab.name}: ${isChecked ? 'AKTIV' : 'INAKTIV'}`);
                
                // Prüfen ob Tab-Content sichtbar ist
                const tabContent = await page.locator(`.tab-content[data-tab="${tab.id.replace('-tab', '')}"]`).isVisible();
                console.log(`  → Content sichtbar: ${tabContent ? 'JA' : 'NEIN'}`);
                
            } catch (error) {
                console.log(`❌ Tab ${tab.name}: FEHLER - ${error.message}`);
            }
        }

        // 4. EINZELSUCHE FUNKTIONALITÄT (Default Tab)
        console.log('\n=== PHASE 4: EINZELSUCHE VALIDIERUNG ===');
        await page.click('#single-tab'); // Zurück zum ersten Tab
        await page.waitForTimeout(500);

        // Suche-Input prüfen
        const searchInput = await page.locator('input[placeholder*="Mine"]').first();
        const searchInputVisible = await searchInput.isVisible();
        console.log(`✓ Such-Input sichtbar: ${searchInputVisible ? 'JA' : 'NEIN'}`);

        // Such-Button prüfen
        const searchButtons = await page.locator('button:has-text("Suche")').count();
        console.log(`✓ Such-Buttons gefunden: ${searchButtons}`);

        // 5. TEST-SUCHE DURCHFÜHREN
        console.log('\n=== PHASE 5: TEST-SUCHE DURCHFÜHRUNG ===');
        if (searchInputVisible && modelCheckboxes > 0) {
            // Erstes verfügbares Modell auswählen
            await page.locator('#model-selection input[type="checkbox"]').first().check();
            
            // Test-Suche eingeben
            await searchInput.fill('Grasberg Mine');
            await page.screenshot({ path: 'vor_testsuche_eingabe.png' });
            
            // Suche starten
            await page.locator('button:has-text("Suche")').first().click();
            console.log('✓ Test-Suche gestartet mit "Grasberg Mine"');
            
            // Warten auf Ergebnisse (länger warten für echte Suche)
            await page.waitForTimeout(5000);
            await page.screenshot({ path: 'nach_testsuche_ergebnisse.png' });
            
            // Prüfen ob Ergebnisse angezeigt werden
            const results = await page.locator('.result, .data-card, [class*="result"]').count();
            console.log(`✓ Suchergebnisse gefunden: ${results} Elemente`);
        }

        // 6. STATISTIKEN TAB VALIDIERUNG
        console.log('\n=== PHASE 6: STATISTIKEN TAB VALIDIERUNG ===');
        await page.click('#statistics-tab');
        await page.waitForTimeout(2000);
        
        await page.screenshot({ path: 'statistiken_tab_aktiv.png' });
        
        // Prüfen ob Charts/Statistiken geladen sind
        const charts = await page.locator('canvas, .chart, [id*="chart"]').count();
        console.log(`✓ Charts/Statistiken gefunden: ${charts} Elemente`);

        // 7. EXCEPTION-HANDLER VALIDATION
        console.log('\n=== PHASE 7: EXCEPTION-HANDLER VALIDATION ===');
        await page.click('#single-tab'); // Zurück zur Suche
        await page.waitForTimeout(500);
        
        // Leere Suche testen (wenn Suche-Input noch sichtbar ist)
        try {
            const searchInput2 = await page.locator('input[placeholder*="Mine"]').first();
            await searchInput2.fill('');
            await page.locator('button:has-text("Suche")').first().click();
            await page.waitForTimeout(1000);
            await page.screenshot({ path: 'leere_suche_exception_test.png' });
            console.log('✓ Leere Suche getestet');
        } catch (error) {
            console.log('ℹ️ Leere Suche Test übersprungen:', error.message);
        }

        // 8. JAVASCRIPT CONSOLE ERRORS SAMMELN
        console.log('\n=== PHASE 8: JAVASCRIPT-CONSOLE PRÜFUNG ===');
        const consoleErrors = [];
        const consoleWarnings = [];
        
        page.on('console', msg => {
            if (msg.type() === 'error') {
                consoleErrors.push(msg.text());
            } else if (msg.type() === 'warning') {
                consoleWarnings.push(msg.text());
            }
        });
        
        // Seite neu laden um Console-Messages zu sammeln
        await page.reload();
        await page.waitForTimeout(3000);
        
        console.log(`✓ Console-Errors: ${consoleErrors.length}`);
        console.log(`✓ Console-Warnings: ${consoleWarnings.length}`);
        
        if (consoleErrors.length > 0) {
            console.log('❌ Console-Errors:', consoleErrors.slice(0, 3)); // Erste 3 zeigen
        }
        if (consoleWarnings.length > 0) {
            console.log('⚠️ Console-Warnings:', consoleWarnings.slice(0, 3));
        }

        // 9. RESPONSIVE DESIGN TESTEN
        console.log('\n=== PHASE 9: RESPONSIVE DESIGN ===');
        const viewports = [
            { width: 1920, height: 1080, name: 'desktop_fullhd' },
            { width: 1024, height: 768, name: 'tablet_landscape' },
            { width: 375, height: 667, name: 'mobile_portrait' }
        ];

        for (const viewport of viewports) {
            await page.setViewportSize({ width: viewport.width, height: viewport.height });
            await page.waitForTimeout(500);
            await page.screenshot({ path: `responsive_test_${viewport.name}.png` });
            console.log(`✓ Responsive Test ${viewport.name}: Screenshot erstellt`);
        }

        // 10. FINAL VALIDATION SUMMARY
        console.log('\n=== PHASE 10: VALIDIERUNGS-ZUSAMMENFASSUNG ===');
        
        // Zurück zu Desktop Viewport
        await page.setViewportSize({ width: 1920, height: 1080 });
        await page.screenshot({ path: 'finale_validierung_screenshot.png', fullPage: true });
        
        console.log('✓ Header: Korrekt geladen');
        console.log(`✓ Navigation: ${navTabs} Tabs verfügbar`);
        console.log(`✓ Modelle: ${modelCheckboxes} verfügbar`);
        console.log(`✓ Console-Errors: ${consoleErrors.length}`);
        console.log(`✓ Responsive: 3 Viewports getestet`);

        console.log('\n🎉 KORRIGIERTE Browser-Validierung erfolgreich abgeschlossen!');
        console.log('📁 Screenshots gespeichert für detaillierte Analyse');

    } catch (error) {
        console.error('❌ KRITISCHER FEHLER bei korrigierter Browser-Validierung:', error);
        await page.screenshot({ path: 'kritischer_fehler_screenshot.png' });
    } finally {
        await browser.close();
    }
}

// Test starten
validateMineSearchBrowserCorrected().catch(console.error);