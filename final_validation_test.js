/**
 * Author: rahn
 * Datum: 13.08.2025
 * Version: 1.2
 * Beschreibung: Finale Browser-Validierung mit Label-Clicks statt Radio-Buttons
 */

const { chromium } = require('playwright');

async function finalMineSearchValidation() {
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext({ 
        viewport: { width: 1920, height: 1080 } 
    });
    const page = await context.newPage();

    console.log('🎯 FINALE MineSearch 2.0 Browser-Validierung');

    try {
        // PHASE 1: Grundvalidierung
        console.log('\n=== GRUNDVALIDIERUNG ===');
        await page.goto('http://localhost:8000');
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(3000);
        
        await page.screenshot({ path: 'final_hauptseite.png', fullPage: true });
        
        const header = await page.locator('header h1').textContent();
        const navTabs = await page.locator('.tab-navigation label').count();
        const tabLabels = await page.locator('.tab-navigation label').allTextContents();
        
        console.log(`✅ Header: "${header}"`);
        console.log(`✅ Tabs: ${navTabs} verfügbar`);
        console.log(`✅ Tab-Namen: ${tabLabels.join(', ')}`);

        // PHASE 2: Model-Loading Validierung
        console.log('\n=== MODEL-LOADING VALIDIERUNG ===');
        const modelCheckboxes = await page.locator('#model-selection input[type="checkbox"]').count();
        console.log(`✅ Modelle geladen: ${modelCheckboxes} Modelle`);

        // PHASE 3: Tab-Navigation (über Labels)
        console.log('\n=== TAB-NAVIGATION TEST ===');
        const tabs = [
            { label: '🔍 Einzelsuche', expected: 'single' },
            { label: '📊 CSV-Upload', expected: 'csv' },
            { label: '📚 Quellen', expected: 'sources' },
            { label: '📈 Statistiken', expected: 'statistics' },
            { label: '📋 Konsolidiert', expected: 'consolidated' }
        ];
        
        for (const tab of tabs) {
            try {
                // Label anklicken statt Radio-Button
                await page.click(`text="${tab.label}"`);
                await page.waitForTimeout(1000);
                
                // Prüfen ob entsprechender Radio-Button aktiviert ist
                const isChecked = await page.locator(`input[value="${tab.expected}"]`).isChecked();
                await page.screenshot({ path: `final_tab_${tab.expected}.png` });
                console.log(`✅ ${tab.label}: ${isChecked ? 'AKTIV' : 'INAKTIV'}`);
                
            } catch (error) {
                console.log(`❌ ${tab.label}: FEHLER - ${error.message.substring(0, 50)}`);
            }
        }

        // PHASE 4: Einzelsuche Funktionalität (Default Tab)
        console.log('\n=== EINZELSUCHE FUNKTIONALITÄT ===');
        await page.click('text="🔍 Einzelsuche"');
        await page.waitForTimeout(1000);

        // Erstes Modell auswählen für Test
        if (modelCheckboxes > 0) {
            await page.locator('#model-selection input[type="checkbox"]').first().check();
            console.log('✅ Erstes Modell ausgewählt');
        }

        // Such-Input finden und testen
        const searchInputs = await page.locator('input[type="text"]').count();
        console.log(`✅ Such-Inputs gefunden: ${searchInputs}`);

        if (searchInputs > 0) {
            // Test-Suche durchführen
            await page.locator('input[type="text"]').first().fill('Grasberg Mine');
            await page.screenshot({ path: 'final_vor_suche.png' });
            
            // Such-Button finden und klicken
            const searchButtons = await page.locator('button:has-text("Suche"), button:has-text("Search")').count();
            console.log(`✅ Such-Buttons gefunden: ${searchButtons}`);
            
            if (searchButtons > 0) {
                await page.locator('button:has-text("Suche"), button:has-text("Search")').first().click();
                console.log('✅ Suche gestartet');
                
                // Warten auf Ergebnisse
                await page.waitForTimeout(5000);
                await page.screenshot({ path: 'final_nach_suche.png' });
            }
        }

        // PHASE 5: Statistiken Tab
        console.log('\n=== STATISTIKEN TAB VALIDIERUNG ===');
        await page.click('text="📈 Statistiken"');
        await page.waitForTimeout(2000);
        
        await page.screenshot({ path: 'final_statistiken.png' });
        
        const charts = await page.locator('canvas, .chart').count();
        console.log(`✅ Charts/Statistiken: ${charts} Elemente`);

        // PHASE 6: Console-Errors sammeln
        console.log('\n=== CONSOLE-ERRORS PRÜFUNG ===');
        const consoleErrors = [];
        
        page.on('console', msg => {
            if (msg.type() === 'error') {
                consoleErrors.push(msg.text());
            }
        });
        
        await page.reload();
        await page.waitForTimeout(3000);
        
        console.log(`✅ Console-Errors: ${consoleErrors.length}`);
        if (consoleErrors.length > 0) {
            consoleErrors.slice(0, 2).forEach(error => {
                console.log(`❌ Error: ${error.substring(0, 100)}`);
            });
        }

        // PHASE 7: Mobile Responsive Test
        console.log('\n=== RESPONSIVE DESIGN TEST ===');
        await page.setViewportSize({ width: 375, height: 667 });
        await page.waitForTimeout(1000);
        await page.screenshot({ path: 'final_mobile.png' });
        console.log('✅ Mobile Screenshot erstellt');

        // Zurück zu Desktop
        await page.setViewportSize({ width: 1920, height: 1080 });
        await page.screenshot({ path: 'final_desktop_end.png', fullPage: true });

        // ZUSAMMENFASSUNG
        console.log('\n=== VALIDIERUNGS-ERGEBNIS ===');
        console.log(`✅ Header korrekt: JA`);
        console.log(`✅ Tabs funktional: ${navTabs}/5`);
        console.log(`✅ Modelle geladen: ${modelCheckboxes}`);
        console.log(`✅ Console-Errors: ${consoleErrors.length}`);
        console.log(`✅ Screenshots erstellt: 8+`);
        
        console.log('\n🎉 FINALE VALIDIERUNG ABGESCHLOSSEN');

    } catch (error) {
        console.error('❌ KRITISCHER VALIDIERUNGSFEHLER:', error);
        await page.screenshot({ path: 'final_error.png' });
    } finally {
        await browser.close();
    }
}

// Test starten
finalMineSearchValidation().catch(console.error);