/**
 * Author: rahn
 * Datum: 10.08.2025
 * Version: 1.0
 * Beschreibung: Umfassender Test aller Detail-Buttons (Konsolidiert, Quellen, Statistiken)
 * 
 * WICHTIG: Test direkt im Browser mit Playwright MCP Server wie vom User angefordert
 */

const { chromium } = require('playwright');

async function testAllDetailButtonsComprehensive() {
    const browser = await chromium.launch({ headless: false }); // Sichtbarer Browser für bessere Inspektion
    const page = await browser.newPage();
    
    console.log('🔍 UMFASSENDER TEST: ALLE DETAIL-BUTTONS');
    console.log('=========================================\n');
    
    // JavaScript-Errors sammeln
    const jsErrors = [];
    page.on('console', msg => {
        if (msg.type() === 'error') {
            jsErrors.push(msg.text());
            console.log(`🚨 Browser Console Error: ${msg.text()}`);
        }
    });
    
    // Network-Fehler überwachen
    const networkErrors = [];
    page.on('response', response => {
        if (!response.ok() && response.status() !== 404) {
            networkErrors.push(`${response.status()} ${response.url()}`);
        }
    });
    
    const testResults = {
        consolidated: { success: false, buttonCount: 0, errors: [] },
        sources: { success: false, buttonCount: 0, errors: [] },
        statistics: { success: false, buttonCount: 0, errors: [] }
    };
    
    try {
        await page.goto('http://localhost:8000', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(3000);
        
        console.log('✅ MineSearch 2.0 Seite geladen\n');
        
        // =============================================
        // TEST 1: KONSOLIDIERTE DETAIL-BUTTONS
        // =============================================
        
        console.log('📋 TEST 1: KONSOLIDIERTE DETAIL-BUTTONS');
        console.log('========================================');
        
        try {
            // Navigiere zu Konsolidiert-Tab
            await page.click('label[for="consolidated-tab"]');
            await page.waitForTimeout(5000);
            
            // Warte auf Tabelle
            await page.waitForSelector('#consolidated-table-container table', { timeout: 10000 });
            console.log('  ✅ Konsolidiert-Tabelle geladen');
            
            // Finde Detail-Buttons
            const consolidatedButtons = await page.$$('button:has-text("Details")');
            console.log(`  📊 Konsolidierte Detail-Buttons gefunden: ${consolidatedButtons.length}`);
            testResults.consolidated.buttonCount = consolidatedButtons.length;
            
            if (consolidatedButtons.length > 0) {
                // Prüfe viewConsolidatedDetail Funktion
                const functionExists = await page.evaluate(() => {
                    return typeof window.viewConsolidatedDetail === 'function';
                });
                console.log(`  📋 viewConsolidatedDetail verfügbar: ${functionExists ? '✅' : '❌'}`);
                
                if (functionExists) {
                    // Teste ersten Button
                    console.log('  🔘 Teste ersten konsolidierten Detail-Button...');
                    await consolidatedButtons[0].click();
                    await page.waitForTimeout(3000);
                    
                    // Prüfe auf Modal oder Notification
                    const modalExists = await page.$('.modal-overlay, .detail-modal, .comprehensive-details-modal') !== null;
                    const notificationExists = await page.$('.notification') !== null;
                    
                    if (modalExists || notificationExists) {
                        console.log('  ✅ ERFOLG: Konsolidierte Detail-Buttons funktionieren');
                        testResults.consolidated.success = true;
                        
                        // Modal schließen falls offen
                        if (modalExists) {
                            await page.keyboard.press('Escape');
                            await page.waitForTimeout(1000);
                        }
                    } else {
                        console.log('  ❌ FEHLER: Kein Modal/Notification nach Button-Klick');
                        testResults.consolidated.errors.push('Keine sichtbare Reaktion');
                    }
                } else {
                    console.log('  ❌ FEHLER: viewConsolidatedDetail Funktion nicht verfügbar');
                    testResults.consolidated.errors.push('Function nicht verfügbar');
                }
            } else {
                console.log('  ❌ FEHLER: Keine konsolidierten Detail-Buttons gefunden');
                testResults.consolidated.errors.push('Keine Buttons gefunden');
            }
            
        } catch (error) {
            console.log(`  ❌ FEHLER bei konsolidierten Buttons: ${error.message}`);
            testResults.consolidated.errors.push(error.message);
        }
        
        console.log(''); // Leerzeile
        
        // =============================================
        // TEST 2: QUELLEN DETAIL-BUTTONS
        // =============================================
        
        console.log('📋 TEST 2: QUELLEN DETAIL-BUTTONS');
        console.log('==================================');
        
        try {
            // Navigiere zu Quellen-Tab
            await page.click('label[for="sources-tab"]');
            await page.waitForTimeout(5000);
            
            // Warte auf Quellen-Tabelle
            await page.waitForSelector('#sources-table-container table', { timeout: 10000 });
            console.log('  ✅ Quellen-Tabelle geladen');
            
            // Finde Quellen Detail-Buttons
            const sourceButtons = await page.$$('#sources-table-container button:has-text("Details")');
            console.log(`  📊 Quellen Detail-Buttons gefunden: ${sourceButtons.length}`);
            testResults.sources.buttonCount = sourceButtons.length;
            
            if (sourceButtons.length > 0) {
                // Prüfe toggleSourceDetails und loadEnhancedSourceDetails Funktionen
                const functionsCheck = await page.evaluate(() => {
                    return {
                        toggleSourceDetails: typeof window.toggleSourceDetails === 'function',
                        loadEnhancedSourceDetails: typeof window.loadEnhancedSourceDetails === 'function'
                    };
                });
                console.log(`  📋 toggleSourceDetails verfügbar: ${functionsCheck.toggleSourceDetails ? '✅' : '❌'}`);
                console.log(`  📋 loadEnhancedSourceDetails verfügbar: ${functionsCheck.loadEnhancedSourceDetails ? '✅' : '❌'}`);
                
                if (functionsCheck.toggleSourceDetails) {
                    // Teste ersten Quellen-Button
                    console.log('  🔘 Teste ersten Quellen Detail-Button...');
                    
                    // Hole Domain vom ersten Button
                    const firstButtonOnclick = await sourceButtons[0].getAttribute('onclick');
                    console.log(`  🔍 Erster Button onclick: ${firstButtonOnclick}`);
                    
                    await sourceButtons[0].click();
                    await page.waitForTimeout(3000);
                    
                    // Prüfe auf Detail-Zeile (Accordion-Style)
                    const detailsRowVisible = await page.evaluate(() => {
                        const detailRows = document.querySelectorAll('.accordion-details-row');
                        for (const row of detailRows) {
                            if (row.style.display === 'table-row' || row.style.display === '') {
                                return true;
                            }
                        }
                        return false;
                    });
                    
                    if (detailsRowVisible) {
                        console.log('  ✅ ERFOLG: Quellen Detail-Zeile geöffnet');
                        testResults.sources.success = true;
                        
                        // Prüfe auf Loading/Content
                        const hasContent = await page.evaluate(() => {
                            const detailRows = document.querySelectorAll('.accordion-details-row');
                            for (const row of detailRows) {
                                if (row.style.display === 'table-row' && row.textContent.trim().length > 10) {
                                    return true;
                                }
                            }
                            return false;
                        });
                        
                        if (hasContent) {
                            console.log('  ✅ ERFOLG: Detail-Inhalte werden geladen/angezeigt');
                        } else {
                            console.log('  ⚠️ Detail-Zeile ist sichtbar, aber ohne Inhalte');
                        }
                        
                    } else {
                        console.log('  ❌ FEHLER: Quellen Detail-Zeile nicht sichtbar');
                        testResults.sources.errors.push('Detail-Zeile nicht sichtbar');
                        
                        // Debug: Prüfe auf Console-Errors
                        const currentErrors = jsErrors.filter(err => 
                            err.includes('Details elements not found') || 
                            err.includes('not defined')
                        );
                        if (currentErrors.length > 0) {
                            console.log('  🚨 Gefundene Console-Errors:');
                            currentErrors.forEach(err => console.log(`    - ${err}`));
                        }
                    }
                } else {
                    console.log('  ❌ FEHLER: toggleSourceDetails Funktion nicht verfügbar');
                    testResults.sources.errors.push('toggleSourceDetails Function fehlt');
                }
            } else {
                console.log('  ❌ FEHLER: Keine Quellen Detail-Buttons gefunden');
                testResults.sources.errors.push('Keine Buttons gefunden');
            }
            
        } catch (error) {
            console.log(`  ❌ FEHLER bei Quellen-Buttons: ${error.message}`);
            testResults.sources.errors.push(error.message);
        }
        
        console.log(''); // Leerzeile
        
        // =============================================
        // TEST 3: STATISTIKEN DETAIL-BUTTONS
        // =============================================
        
        console.log('📋 TEST 3: STATISTIKEN DETAIL-BUTTONS');
        console.log('=====================================');
        
        try {
            // Navigiere zu Statistiken-Tab
            await page.click('label[for="statistics-tab"]');
            await page.waitForTimeout(5000);
            
            // Warte auf Statistiken zu laden
            await page.waitForSelector('#model-statistics-container', { timeout: 10000 });
            console.log('  ✅ Statistiken-Tab geladen');
            
            // Finde Statistiken Detail-Buttons
            const statsButtons = await page.$$('#model-statistics-container button:has-text("Details")');
            console.log(`  📊 Statistiken Detail-Buttons gefunden: ${statsButtons.length}`);
            testResults.statistics.buttonCount = statsButtons.length;
            
            if (statsButtons.length > 0) {
                // Teste ersten Statistik-Button
                console.log('  🔘 Teste ersten Statistiken Detail-Button...');
                
                await statsButtons[0].click();
                await page.waitForTimeout(3000);
                
                // Prüfe auf Modal oder erweiterte Inhalte
                const modalExists = await page.$('.modal-overlay, .detail-modal') !== null;
                const expandedContentExists = await page.evaluate(() => {
                    return document.querySelectorAll('.expanded-stats, .detailed-statistics').length > 0;
                });
                
                if (modalExists || expandedContentExists) {
                    console.log('  ✅ ERFOLG: Statistiken Detail-Button funktioniert');
                    testResults.statistics.success = true;
                    
                    if (modalExists) {
                        await page.keyboard.press('Escape');
                        await page.waitForTimeout(1000);
                    }
                } else {
                    console.log('  ❌ FEHLER: Keine erweiterten Statistiken nach Button-Klick');
                    testResults.statistics.errors.push('Keine sichtbare Reaktion');
                }
            } else {
                console.log('  ⚠️ Keine Statistiken Detail-Buttons gefunden (kann normal sein)');
                testResults.statistics.errors.push('Keine Buttons (normal)');
            }
            
        } catch (error) {
            console.log(`  ❌ FEHLER bei Statistiken-Buttons: ${error.message}`);
            testResults.statistics.errors.push(error.message);
        }
        
        console.log(''); // Leerzeile
        
        // =============================================
        // FINALE BEWERTUNG
        // =============================================
        
        console.log('🎯 UMFASSENDE DETAIL-BUTTONS BEWERTUNG');
        console.log('======================================');
        
        const consolidatedOK = testResults.consolidated.success || testResults.consolidated.buttonCount === 0;
        const sourcesOK = testResults.sources.success || testResults.sources.buttonCount === 0;
        const statisticsOK = testResults.statistics.success || testResults.statistics.buttonCount === 0;
        
        console.log('📊 ERGEBNISSE ÜBERSICHT:');
        console.log(`   🔹 Konsolidierte Buttons: ${testResults.consolidated.success ? '✅ FUNKTIONIERT' : '❌ FEHLER'} (${testResults.consolidated.buttonCount} Buttons)`);
        console.log(`   🔹 Quellen Buttons: ${testResults.sources.success ? '✅ FUNKTIONIERT' : '❌ FEHLER'} (${testResults.sources.buttonCount} Buttons)`);
        console.log(`   🔹 Statistiken Buttons: ${testResults.statistics.success ? '✅ FUNKTIONIERT' : '❌ FEHLER'} (${testResults.statistics.buttonCount} Buttons)`);
        
        console.log('\n🚨 FEHLER-ANALYSE:');
        const relevantJSErrors = jsErrors.filter(error => 
            !error.includes('favicon') && 
            (error.includes('not found') || error.includes('not defined') || error.includes('404'))
        );
        console.log(`   📋 JavaScript-Errors: ${relevantJSErrors.length}`);
        
        if (relevantJSErrors.length > 0) {
            console.log('   ❌ GEFUNDENE JS-ERRORS:');
            relevantJSErrors.forEach(error => console.log(`     - ${error}`));
        }
        
        console.log(`   📋 Network-Errors: ${networkErrors.length}`);
        if (networkErrors.length > 0) {
            networkErrors.forEach(error => console.log(`     - ${error}`));
        }
        
        // FINAL SUCCESS CRITERIA
        const isFullSuccess = testResults.consolidated.success && testResults.sources.success;
        const isPartialSuccess = testResults.consolidated.success || testResults.sources.success;
        const hasNoBlockingErrors = relevantJSErrors.length === 0;
        
        console.log('\n🏆 FINALE BEWERTUNG:');
        if (isFullSuccess && hasNoBlockingErrors) {
            console.log('🎉 VOLLSTÄNDIGER ERFOLG!');
            console.log('✅ Alle Detail-Button-Systeme funktionieren ohne Fehler!');
            console.log('💪 Fix für Quellen Detail-Buttons war erfolgreich!');
        } else if (isPartialSuccess) {
            console.log('✅ TEILERFOLG!');
            console.log('🏆 Mindestens ein Detail-Button-System funktioniert korrekt!');
            if (!testResults.sources.success) {
                console.log('⚠️ Quellen Detail-Buttons benötigen noch Aufmerksamkeit');
            }
        } else {
            console.log('⚠️ VERBESSERUNG ERFORDERLICH');
            console.log('❌ Detail-Button-Systeme haben noch Probleme');
        }
        
        return {
            success: isFullSuccess,
            partialSuccess: isPartialSuccess,
            noBlockingErrors: hasNoBlockingErrors,
            results: testResults,
            jsErrors: relevantJSErrors,
            networkErrors,
            summary: {
                consolidatedWorking: testResults.consolidated.success,
                sourcesWorking: testResults.sources.success,
                statisticsWorking: testResults.statistics.success,
                totalButtons: testResults.consolidated.buttonCount + testResults.sources.buttonCount + testResults.statistics.buttonCount
            }
        };
        
    } catch (error) {
        console.error('❌ Gesamttest-Fehler:', error);
        return { success: false, error: error.message };
    } finally {
        await browser.close();
    }
}

// Test ausführen
testAllDetailButtonsComprehensive().then(result => {
    console.log('\n📋 Test abgeschlossen!');
    console.log('Ergebnis:', result.success ? 'ERFOLG' : 'FEHLER');
});