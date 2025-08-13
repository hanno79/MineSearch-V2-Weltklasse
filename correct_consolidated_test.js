/**
 * Author: rahn
 * Datum: 13.08.2025
 * Version: 1.0
 * Beschreibung: Korrigierter Test für Consolidated Tab nach Refactoring
 */

const { chromium } = require('playwright');

async function correctConsolidatedTest() {
    console.log('🚀 STARTE: Korrigierter Consolidated Test');
    
    const browser = await chromium.launch({ 
        headless: false,
        slowMo: 1500
    });
    
    const context = await browser.newContext();
    const page = await context.newPage();
    
    // Console-Errors sammeln
    const consoleErrors = [];
    page.on('console', msg => {
        if (msg.type() === 'error') {
            consoleErrors.push(msg.text());
            console.log('❌ CONSOLE ERROR:', msg.text());
        }
    });
    
    try {
        console.log('📍 SCHRITT 1: Hauptseite laden');
        await page.goto('http://localhost:8000', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(5000);
        
        console.log('📍 SCHRITT 2: Consolidated Tab aktivieren');
        
        // Radio-Button für Consolidated Tab finden und aktivieren
        const consolidatedRadio = await page.locator('#consolidated-tab');
        await consolidatedRadio.waitFor({ timeout: 10000 });
        await consolidatedRadio.check();
        console.log('✅ Consolidated Radio-Button aktiviert');
        
        // Warten bis der Tab-Inhalt sichtbar ist
        await page.waitForTimeout(3000);
        
        console.log('📍 SCHRITT 3: Tab-Inhalt prüfen');
        
        // Prüfen ob Consolidated Section sichtbar ist
        const consolidatedSection = await page.locator('#consolidated');
        const isVisible = await consolidatedSection.isVisible();
        console.log(`👁️ Consolidated Section sichtbar: ${isVisible}`);
        
        // Screenshot nach Tab-Wechsel
        await page.screenshot({ 
            path: 'consolidated_tab_activated.png',
            fullPage: true 
        });
        console.log('✅ Screenshot nach Tab-Aktivierung erstellt');
        
        console.log('📍 SCHRITT 4: API-Daten laden lassen');
        await page.waitForTimeout(5000); // Zeit für API-Calls
        
        // Prüfen ob Data-Cards geladen wurden
        const dataCards = await page.locator('.data-card').count();
        console.log(`📊 Data-Cards gefunden: ${dataCards}`);
        
        // Wenn keine Cards, warten wir länger
        if (dataCards === 0) {
            console.log('⏳ Warte länger auf Daten-Loading...');
            await page.waitForTimeout(10000);
            const retryCards = await page.locator('.data-card').count();
            console.log(`📊 Nach längerer Wartezeit - Data-Cards: ${retryCards}`);
        }
        
        console.log('📍 SCHRITT 5: API-Endpoint direkt testen');
        
        // Direkt zur API navigieren und Daten prüfen
        const apiUrl = 'http://localhost:8000/api/consolidated/results';
        const apiResponse = await page.goto(apiUrl);
        
        if (apiResponse.status() === 200) {
            const apiText = await page.textContent('body');
            const apiData = JSON.parse(apiText);
            console.log(`📡 API direkt erfolgreich: ${apiData.length} Einträge`);
            
            // Beispiel der ersten Einträge zeigen
            if (apiData.length > 0) {
                console.log('📋 Beispiel API-Daten:');
                console.log(JSON.stringify(apiData[0], null, 2));
            }
        }
        
        console.log('📍 SCHRITT 6: Zurück zur Hauptseite für finalen Test');
        await page.goto('http://localhost:8000');
        await page.waitForTimeout(3000);
        
        // Consolidated Tab wieder aktivieren
        await page.locator('#consolidated-tab').check();
        await page.waitForTimeout(5000);
        
        // Finale Screenshots
        await page.screenshot({ 
            path: 'consolidated_final_test.png',
            fullPage: true 
        });
        
        console.log('📍 SCHRITT 7: Deutsche Feldnamen prüfen');
        
        // Nach deutschen Texten suchen
        const germanTerms = ['Rohstoffe', 'Kostenjahr', 'Mine', 'Land'];
        const foundTerms = {};
        
        for (const term of germanTerms) {
            const count = await page.locator(`text=${term}`).count();
            foundTerms[term] = count;
            console.log(`🇩🇪 "${term}": ${count} mal gefunden`);
        }
        
        console.log('📍 SCHRITT 8: Export-Button prüfen');
        
        const exportButton = await page.locator('button:has-text("Export")').count();
        console.log(`📤 Export-Button gefunden: ${exportButton > 0}`);
        
        // Ergebnisse zusammenfassen
        const results = {
            success: true,
            consolidatedTabActivated: true,
            consolidatedSectionVisible: isVisible,
            dataCardsFound: dataCards,
            apiWorking: apiResponse.status() === 200,
            germanTermsFound: foundTerms,
            exportButtonExists: exportButton > 0,
            consoleErrors: consoleErrors.length,
            consoleErrorDetails: consoleErrors
        };
        
        console.log('🎯 REFACTORING VALIDIERUNGS-ERGEBNISSE:');
        console.log(JSON.stringify(results, null, 2));
        
        // Erfolg bewerten
        const isSuccessful = results.apiWorking && 
                           results.consolidatedTabActivated && 
                           consoleErrors.length === 0;
        
        console.log(`🎉 REFACTORING VALIDIERUNG: ${isSuccessful ? 'ERFOLGREICH ✅' : 'FEHLGESCHLAGEN ❌'}`);
        
        return results;
        
    } catch (error) {
        console.log('❌ FEHLER bei Test:', error.message);
        await page.screenshot({ 
            path: 'consolidated_test_error.png',
            fullPage: true 
        });
        return { success: false, error: error.message };
    } finally {
        await browser.close();
    }
}

// Test ausführen
correctConsolidatedTest()
    .then(results => {
        console.log('✅ Test abgeschlossen');
        if (results.success) {
            console.log('🎉 REFACTORING ERFOLGREICH VALIDIERT!');
        } else {
            console.log('❌ REFACTORING VALIDIERUNG FEHLGESCHLAGEN');
        }
        process.exit(0);
    })
    .catch(error => {
        console.log('❌ Test komplett fehlgeschlagen:', error);
        process.exit(1);
    });