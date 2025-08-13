/**
 * Author: rahn
 * Datum: 13.08.2025
 * Version: 1.0
 * Beschreibung: Einfacher Test für Consolidated Tab nach Refactoring
 */

const { chromium } = require('playwright');

async function simpleConsolidatedTest() {
    console.log('🚀 STARTE: Einfacher Consolidated Test');
    
    const browser = await chromium.launch({ 
        headless: false,
        slowMo: 2000
    });
    
    const context = await browser.newContext();
    const page = await context.newPage();
    
    try {
        console.log('📍 Lade Hauptseite...');
        await page.goto('http://localhost:8000', { waitUntil: 'networkidle' });
        await page.waitForTimeout(5000);
        
        // Screenshot der Hauptseite
        await page.screenshot({ 
            path: 'main_page_loaded.png',
            fullPage: true 
        });
        console.log('✅ Hauptseite Screenshot erstellt');
        
        // Prüfe ob Tabs existieren
        const pageContent = await page.content();
        console.log('🔍 Seite geladen, prüfe Tab-Struktur...');
        
        // Suche nach Tab-Buttons
        const tabButtons = await page.$$('.tab-button, button[data-tab], .nav-button');
        console.log(`📊 Gefundene Tab-Buttons: ${tabButtons.length}`);
        
        // Liste alle Buttons auf
        const allButtons = await page.$$('button');
        console.log(`🔘 Alle Buttons auf der Seite: ${allButtons.length}`);
        
        for (let i = 0; i < Math.min(allButtons.length, 10); i++) {
            const buttonText = await allButtons[i].textContent();
            const buttonId = await allButtons[i].getAttribute('id');
            const buttonClass = await allButtons[i].getAttribute('class');
            console.log(`Button ${i}: "${buttonText}" (id: ${buttonId}, class: ${buttonClass})`);
        }
        
        // Suche speziell nach Consolidated
        const consolidatedElements = await page.$$('*:has-text("Consolidated")');
        console.log(`🎯 Elemente mit "Consolidated": ${consolidatedElements.length}`);
        
        // Prüfe ob API-Endpoints verfügbar sind
        console.log('🌐 Teste API-Endpunkt...');
        const apiResponse = await page.goto('http://localhost:8000/api/consolidated/results');
        console.log(`📡 API Response Status: ${apiResponse.status()}`);
        
        if (apiResponse.status() === 200) {
            const apiData = await apiResponse.json();
            console.log(`📊 API Daten erhalten: ${apiData.length} Einträge`);
        }
        
        await page.screenshot({ 
            path: 'api_test_result.png',
            fullPage: true 
        });
        
        return {
            success: true,
            tabButtonsFound: tabButtons.length,
            allButtonsFound: allButtons.length,
            consolidatedElementsFound: consolidatedElements.length,
            apiStatus: apiResponse.status()
        };
        
    } catch (error) {
        console.log('❌ FEHLER:', error.message);
        await page.screenshot({ 
            path: 'error_screenshot.png',
            fullPage: true 
        });
        return { success: false, error: error.message };
    } finally {
        await browser.close();
    }
}

// Test ausführen
simpleConsolidatedTest()
    .then(results => {
        console.log('📋 TESTERGEBNISSE:', JSON.stringify(results, null, 2));
        process.exit(0);
    })
    .catch(error => {
        console.log('❌ Test fehlgeschlagen:', error);
        process.exit(1);
    });