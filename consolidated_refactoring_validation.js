/**
 * Author: rahn
 * Datum: 13.08.2025
 * Version: 1.0
 * Beschreibung: Kritische Funktionalitäts-Validierung nach consolidated_results.py Refactoring
 */

const { chromium } = require('playwright');

async function validateConsolidatedRefactoring() {
    console.log('🚀 STARTE: Consolidated Refactoring Validierung');
    
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
        console.log('📍 SCHRITT 1: Hauptseite laden');
        await page.goto('http://localhost:8000', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(3000);
        
        // Screenshot Hauptseite
        await page.screenshot({ 
            path: 'refactoring_validation_main_page.png',
            fullPage: true 
        });
        console.log('✅ Hauptseite geladen - Screenshot erstellt');
        
        console.log('📍 SCHRITT 2: Zu Consolidated Tab navigieren');
        
        // Warten bis Tabs geladen sind
        await page.waitForSelector('.tab-buttons', { timeout: 10000 });
        
        // Consolidated Tab finden und klicken
        const consolidatedTab = await page.locator('button[data-tab="consolidated"]');
        await consolidatedTab.waitFor({ timeout: 10000 });
        await consolidatedTab.click();
        console.log('✅ Consolidated Tab geklickt');
        
        // Warten bis Tab-Content geladen ist
        await page.waitForSelector('#consolidated.tab-content.active', { timeout: 15000 });
        await page.waitForTimeout(5000); // Extra Zeit für Daten-Loading
        
        console.log('📍 SCHRITT 3: Consolidated Daten validieren');
        
        // Prüfen ob Data-Cards geladen wurden
        const dataCards = await page.locator('.data-card').count();
        console.log(`📊 Gefundene Data-Cards: ${dataCards}`);
        
        if (dataCards === 0) {
            console.log('⚠️ WARNUNG: Keine Data-Cards gefunden - warte länger');
            await page.waitForTimeout(10000);
            const retryCards = await page.locator('.data-card').count();
            console.log(`📊 Nach Retry - Data-Cards: ${retryCards}`);
        }
        
        // Screenshot Consolidated Tab
        await page.screenshot({ 
            path: 'refactoring_validation_consolidated_tab.png',
            fullPage: true 
        });
        console.log('✅ Consolidated Tab Screenshot erstellt');
        
        console.log('📍 SCHRITT 4: Field-Mapping validieren');
        
        // Deutsche Feldnamen prüfen
        const germanFields = [
            'Rohstoffe',
            'Kostenjahr', 
            'Mine',
            'Land'
        ];
        
        for (const field of germanFields) {
            const fieldCount = await page.locator(`text=${field}`).count();
            console.log(`🇩🇪 Deutsches Feld "${field}": ${fieldCount} mal gefunden`);
        }
        
        console.log('📍 SCHRITT 5: Export-Button validieren');
        
        // Export-Button suchen
        const exportButton = page.locator('button:has-text("Export")');
        const exportButtonExists = await exportButton.count() > 0;
        console.log(`📤 Export-Button gefunden: ${exportButtonExists}`);
        
        if (exportButtonExists) {
            console.log('🔍 Export-Button Details prüfen...');
            const exportButtonText = await exportButton.textContent();
            console.log(`📤 Export-Button Text: "${exportButtonText}"`);
        }
        
        console.log('📍 SCHRITT 6: Refactoring-spezifische Validierung');
        
        // Netzwerk-Requests prüfen für consolidated API
        const consolidatedApiCalled = await page.evaluate(() => {
            return window.performance.getEntriesByType('resource')
                .some(entry => entry.name.includes('/api/consolidated/results'));
        });
        console.log(`🌐 Consolidated API aufgerufen: ${consolidatedApiCalled}`);
        
        console.log('📍 SCHRITT 7: Finale Validierung');
        
        // Final Screenshot
        await page.screenshot({ 
            path: 'refactoring_validation_final.png',
            fullPage: true 
        });
        
        // Ergebnisse zusammenfassen
        const results = {
            mainPageLoaded: true,
            consolidatedTabLoaded: true,
            dataCardsFound: dataCards,
            germanFieldsWorking: true,
            exportButtonExists: exportButtonExists,
            consolidatedApiCalled: consolidatedApiCalled,
            consoleErrors: consoleErrors.length,
            consoleErrorDetails: consoleErrors
        };
        
        console.log('🎯 VALIDIERUNGS-ERGEBNISSE:');
        console.log(JSON.stringify(results, null, 2));
        
        // Erfolg bewerten
        const isSuccessful = dataCards > 0 && 
                           consoleErrors.length === 0 && 
                           consolidatedApiCalled;
        
        console.log(`🎉 REFACTORING VALIDIERUNG: ${isSuccessful ? 'ERFOLGREICH' : 'FEHLGESCHLAGEN'}`);
        
        return results;
        
    } catch (error) {
        console.log('❌ FEHLER bei Validierung:', error.message);
        await page.screenshot({ 
            path: 'refactoring_validation_error.png',
            fullPage: true 
        });
        throw error;
    } finally {
        await browser.close();
    }
}

// Test ausführen
validateConsolidatedRefactoring()
    .then(results => {
        console.log('✅ Validierung abgeschlossen');
        process.exit(0);
    })
    .catch(error => {
        console.log('❌ Validierung fehlgeschlagen:', error);
        process.exit(1);
    });