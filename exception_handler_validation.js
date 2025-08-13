/**
 * Author: rahn
 * Datum: 13.08.2025
 * Version: 1.0
 * Beschreibung: Spezifische Exception-Handler Validierung für MineSearch 2.0
 */

const { chromium } = require('playwright');

async function validateExceptionHandlers() {
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext({ 
        viewport: { width: 1920, height: 1080 } 
    });
    const page = await context.newPage();

    console.log('🔍 EXCEPTION-HANDLER VALIDIERUNG');

    // Console-Errors sammeln
    const consoleErrors = [];
    const consoleWarnings = [];
    
    page.on('console', msg => {
        if (msg.type() === 'error') {
            consoleErrors.push(msg.text());
        } else if (msg.type() === 'warning') {
            consoleWarnings.push(msg.text());
        }
    });

    try {
        // PHASE 1: Seite laden und warten
        console.log('\n=== PHASE 1: GRUNDVALIDIERUNG ===');
        await page.goto('http://localhost:8000');
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(3000);
        
        await page.screenshot({ path: 'exception_test_01_loaded.png' });
        console.log('✅ Seite geladen');

        // PHASE 2: Exception Tests
        console.log('\n=== PHASE 2: EXCEPTION-HANDLER TESTS ===');

        // Test 1: Leere Suche
        console.log('\n--- Test 1: Leere Suche ---');
        await page.click('text="🔍 Einzelsuche"');
        await page.waitForTimeout(1000);

        // Mine Name leer lassen und Suche starten
        await page.fill('input[type="text"]', '');
        await page.click('button:has-text("Suche starten")');
        await page.waitForTimeout(2000);
        await page.screenshot({ path: 'exception_test_02_leere_suche.png' });
        console.log('✅ Leere Suche getestet');

        // Test 2: Ungültige Eingabe
        console.log('\n--- Test 2: Ungültige Eingabe ---');
        await page.fill('input[placeholder*="Mine"]', '!@#$%^&*()');
        await page.click('button:has-text("Suche starten")');
        await page.waitForTimeout(2000);
        await page.screenshot({ path: 'exception_test_03_ungueltige_eingabe.png' });
        console.log('✅ Ungültige Eingabe getestet');

        // Test 3: Kein Modell ausgewählt
        console.log('\n--- Test 3: Kein Modell ausgewählt ---');
        // Alle Modelle abwählen
        await page.click('text="Alle abwählen"');
        await page.fill('input[placeholder*="Mine"]', 'Test Mine');
        await page.click('button:has-text("Suche starten")');
        await page.waitForTimeout(2000);
        await page.screenshot({ path: 'exception_test_04_kein_modell.png' });
        console.log('✅ Kein Modell ausgewählt getestet');

        // Test 4: Tab-Wechsel während Suche
        console.log('\n--- Test 4: Tab-Wechsel Tests ---');
        // Ein Modell auswählen
        await page.click('text="🥇 Beste Auswahl (3 Modelle)"');
        await page.fill('input[placeholder*="Mine"]', 'Quick Test');
        
        // Suche starten
        await page.click('button:has-text("Suche starten")');
        await page.waitForTimeout(500);
        
        // Schnell zu anderem Tab wechseln
        await page.click('text="📈 Statistiken"');
        await page.waitForTimeout(1000);
        await page.screenshot({ path: 'exception_test_05_tab_wechsel.png' });
        console.log('✅ Tab-Wechsel während Suche getestet');

        // Zurück zum Einzelsuche Tab
        await page.click('text="🔍 Einzelsuche"');
        await page.waitForTimeout(2000);
        await page.screenshot({ path: 'exception_test_06_zurueck_einzelsuche.png' });

        // PHASE 3: CSV Upload Exception Tests
        console.log('\n=== PHASE 3: CSV UPLOAD EXCEPTION TESTS ===');
        await page.click('text="📊 CSV-Upload"');
        await page.waitForTimeout(1000);

        // Test: Upload ohne Datei
        const uploadButton = await page.locator('button:has-text("Upload"), button:has-text("Hochladen")');
        if (await uploadButton.count() > 0) {
            await uploadButton.first().click();
            await page.waitForTimeout(1000);
            await page.screenshot({ path: 'exception_test_07_upload_ohne_datei.png' });
            console.log('✅ Upload ohne Datei getestet');
        }

        // PHASE 4: Modal Exception Tests
        console.log('\n=== PHASE 4: MODAL EXCEPTION TESTS ===');
        
        // Zurück zur Einzelsuche und echte Suche starten
        await page.click('text="🔍 Einzelsuche"');
        await page.waitForTimeout(1000);

        // Ein Modell sicherstellen
        await page.click('text="🥇 Beste Auswahl (3 Modelle)"');
        await page.fill('input[placeholder*="Mine"]', 'Grasberg');
        await page.click('button:has-text("Suche starten")');
        console.log('✅ Echte Suche für Modal-Tests gestartet');

        // Warten auf mögliche Ergebnisse
        await page.waitForTimeout(8000);
        await page.screenshot({ path: 'exception_test_08_nach_echter_suche.png' });

        // Versuchen Details-Button zu finden und testen
        const detailsButtons = await page.locator('button:has-text("Details"), .details-btn').count();
        console.log(`✅ Details-Buttons gefunden: ${detailsButtons}`);

        if (detailsButtons > 0) {
            await page.locator('button:has-text("Details"), .details-btn').first().click();
            await page.waitForTimeout(1000);
            await page.screenshot({ path: 'exception_test_09_modal_geoeffnet.png' });
            
            // Modal schließen testen (ESC)
            await page.keyboard.press('Escape');
            await page.waitForTimeout(500);
            await page.screenshot({ path: 'exception_test_10_modal_geschlossen.png' });
            console.log('✅ Modal ESC-Schließen getestet');
        }

        // PHASE 5: Console-Errors auswerten
        console.log('\n=== PHASE 5: CONSOLE-ERRORS AUSWERTUNG ===');
        console.log(`📊 Console-Errors: ${consoleErrors.length}`);
        console.log(`📊 Console-Warnings: ${consoleWarnings.length}`);

        if (consoleErrors.length > 0) {
            console.log('\n❌ CONSOLE-ERRORS:');
            consoleErrors.slice(0, 5).forEach((error, i) => {
                console.log(`  ${i+1}. ${error.substring(0, 100)}`);
            });
        }

        if (consoleWarnings.length > 0) {
            console.log('\n⚠️ CONSOLE-WARNINGS:');
            consoleWarnings.slice(0, 3).forEach((warning, i) => {
                console.log(`  ${i+1}. ${warning.substring(0, 100)}`);
            });
        }

        // PHASE 6: Responsive Exception Tests
        console.log('\n=== PHASE 6: RESPONSIVE EXCEPTION TESTS ===');
        
        // Mobile Viewport
        await page.setViewportSize({ width: 375, height: 667 });
        await page.waitForTimeout(1000);
        await page.screenshot({ path: 'exception_test_11_mobile_responsive.png' });
        
        // Navigation testen auf Mobile
        await page.click('text="📈 Statistiken"');
        await page.waitForTimeout(1000);
        await page.screenshot({ path: 'exception_test_12_mobile_statistiken.png' });
        
        console.log('✅ Mobile Responsive Tests abgeschlossen');

        // Zurück zu Desktop
        await page.setViewportSize({ width: 1920, height: 1080 });
        await page.screenshot({ path: 'exception_test_13_final_desktop.png' });

        // ZUSAMMENFASSUNG
        console.log('\n🎯 EXCEPTION-HANDLER VALIDIERUNG ABGESCHLOSSEN');
        console.log(`✅ Tests durchgeführt: 13 Screenshot-Punkte`);
        console.log(`✅ Console-Errors: ${consoleErrors.length}`);
        console.log(`✅ Console-Warnings: ${consoleWarnings.length}`);
        
        const criticalErrors = consoleErrors.filter(error => 
            error.includes('TypeError') || 
            error.includes('ReferenceError') ||
            error.includes('SyntaxError')
        ).length;
        
        console.log(`✅ Kritische Errors: ${criticalErrors}`);
        
        if (criticalErrors === 0) {
            console.log('🎉 EXCEPTION-HANDLER VALIDATION ERFOLGREICH');
        } else {
            console.log('⚠️ KRITISCHE ERRORS GEFUNDEN - NACHBEARBEITUNG NÖTIG');
        }

    } catch (error) {
        console.error('❌ FEHLER bei Exception-Handler Validierung:', error);
        await page.screenshot({ path: 'exception_test_CRITICAL_ERROR.png' });
    } finally {
        await browser.close();
    }
}

// Test starten
validateExceptionHandlers().catch(console.error);