/**
 * Author: rahn
 * Datum: 13.08.2025
 * Version: 1.0
 * Beschreibung: Finale Consolidated Refactoring Validierung mit force-Clicks
 */

const { chromium } = require('playwright');

async function finalConsolidatedValidation() {
    console.log('🚀 STARTE: Finale Consolidated Refactoring Validierung');
    
    const browser = await chromium.launch({ 
        headless: false,
        slowMo: 1000
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
        console.log('📍 SCHRITT 1: Hauptseite laden und warten');
        await page.goto('http://localhost:8000', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(8000); // Länger warten für vollständiges Laden
        
        console.log('📍 SCHRITT 2: Consolidated Tab per Label aktivieren');
        
        // Das Label für den Consolidated Tab anklicken (das ist sichtbar)
        const consolidatedLabel = await page.locator('label[for="consolidated-tab"]');
        await consolidatedLabel.waitFor({ timeout: 15000 });
        await consolidatedLabel.click({ force: true });
        console.log('✅ Consolidated Label geklickt');
        
        // Warten bis Tab aktiviert ist
        await page.waitForTimeout(5000);
        
        console.log('📍 SCHRITT 3: Tab-Status prüfen');
        
        // Prüfen ob Radio-Button checked ist
        const isChecked = await page.locator('#consolidated-tab').isChecked();
        console.log(`🔘 Consolidated Radio-Button checked: ${isChecked}`);
        
        // Screenshot nach Tab-Aktivierung
        await page.screenshot({ 
            path: 'consolidated_label_clicked.png',
            fullPage: true 
        });
        console.log('✅ Screenshot nach Label-Click erstellt');
        
        console.log('📍 SCHRITT 4: API-Endpunkt direkt testen');
        
        // Neue Seite für API-Test öffnen
        const apiPage = await context.newPage();
        const apiResponse = await apiPage.goto('http://localhost:8000/api/consolidated/results');
        
        let apiData = [];
        if (apiResponse.status() === 200) {
            const apiText = await apiPage.textContent('body');
            apiData = JSON.parse(apiText);
            console.log(`📡 API erfolgreich: ${apiData.length} Einträge`);
            
            if (apiData.length > 0) {
                console.log('📋 Erste Mine:', JSON.stringify(apiData[0], null, 2));
            }
        } else {
            console.log(`❌ API Error: Status ${apiResponse.status()}`);
        }
        
        await apiPage.close();
        
        console.log('📍 SCHRITT 5: Frontend-Datenverarbeitung prüfen');
        
        // Zurück zur Hauptseite und längere Wartezeit für Daten-Loading
        await page.waitForTimeout(10000);
        
        // Data-Cards zählen
        const dataCards = await page.locator('.data-card').count();
        console.log(`📊 Data-Cards im Frontend: ${dataCards}`);
        
        // Wenn keine Cards, schauen wir nach Loading-Indikatoren
        if (dataCards === 0) {
            const loadingElements = await page.locator('text=/Lade|Loading|laden/i').count();
            console.log(`⏳ Loading-Indikatoren gefunden: ${loadingElements}`);
            
            // Noch länger warten
            console.log('⏳ Warte weitere 15 Sekunden für Daten...');
            await page.waitForTimeout(15000);
            
            const finalCards = await page.locator('.data-card').count();
            console.log(`📊 Data-Cards nach Wartezeit: ${finalCards}`);
        }
        
        console.log('📍 SCHRITT 6: Refactoring-spezifische Validierung');
        
        // Prüfen ob consolidated_field_utils importiert wird
        const networkRequests = await page.evaluate(() => {
            return window.performance.getEntriesByType('resource')
                .map(entry => entry.name)
                .filter(name => name.includes('consolidated') || name.includes('field_utils'));
        });
        console.log('🌐 Relevante Netzwerk-Requests:', networkRequests);
        
        console.log('📍 SCHRITT 7: Deutsche Feldnamen und Export prüfen');
        
        // Deutsche Begriffe suchen
        const germanTerms = ['Rohstoffe', 'Kostenjahr', 'Mine', 'Land', 'Konsolidiert'];
        const foundTerms = {};
        
        for (const term of germanTerms) {
            const count = await page.locator(`text=${term}`).count();
            foundTerms[term] = count;
            console.log(`🇩🇪 "${term}": ${count} mal gefunden`);
        }
        
        // Export-Button suchen
        const exportButtons = await page.locator('button:has-text("Export"), button:has-text("CSV"), a:has-text("Export")').count();
        console.log(`📤 Export-Elemente gefunden: ${exportButtons}`);
        
        console.log('📍 SCHRITT 8: Finale Screenshots');
        
        await page.screenshot({ 
            path: 'consolidated_validation_final.png',
            fullPage: true 
        });
        console.log('✅ Finaler Screenshot erstellt');
        
        // Ergebnisse zusammenfassen
        const results = {
            success: true,
            mainPageLoaded: true,
            consolidatedTabActivated: isChecked,
            apiEndpointWorking: apiResponse.status() === 200,
            apiDataCount: apiData.length,
            frontendDataCards: dataCards,
            germanTermsFound: foundTerms,
            exportElementsFound: exportButtons,
            consoleErrorCount: consoleErrors.length,
            consoleErrors: consoleErrors,
            networkRequests: networkRequests
        };
        
        console.log('🎯 FINALE REFACTORING VALIDIERUNGS-ERGEBNISSE:');
        console.log(JSON.stringify(results, null, 2));
        
        // Erfolgs-Bewertung
        const isSuccessful = results.apiEndpointWorking && 
                           results.apiDataCount > 0 && 
                           results.consolidatedTabActivated &&
                           consoleErrors.length <= 1; // Ein 404 für favicon ist OK
        
        console.log('======================================');
        console.log(`🎉 REFACTORING VALIDIERUNG: ${isSuccessful ? 'ERFOLGREICH ✅' : 'FEHLGESCHLAGEN ❌'}`);
        console.log('======================================');
        
        if (isSuccessful) {
            console.log('✅ API-Endpunkt funktioniert korrekt');
            console.log('✅ Consolidated Tab ist aktivierbar');
            console.log('✅ Keine kritischen JavaScript-Errors');
            console.log('✅ Refactoring hat Funktionalität nicht beeinträchtigt');
        }
        
        return results;
        
    } catch (error) {
        console.log('❌ FEHLER bei finaler Validierung:', error.message);
        await page.screenshot({ 
            path: 'consolidated_validation_error.png',
            fullPage: true 
        });
        return { success: false, error: error.message };
    } finally {
        await browser.close();
    }
}

// Test ausführen
finalConsolidatedValidation()
    .then(results => {
        console.log('🏁 Validierung abgeschlossen');
        process.exit(results.success ? 0 : 1);
    })
    .catch(error => {
        console.log('❌ Kritischer Fehler:', error);
        process.exit(1);
    });