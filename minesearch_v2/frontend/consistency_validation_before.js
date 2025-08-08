#!/usr/bin/env node
/**
 * Author: rahn
 * Datum: 02.08.2025
 * Version: 1.0
 * Beschreibung: Playwright Test VORHER - Dokumentiert aktuelle Konsistenz-Probleme
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

async function validateConsistencyBefore() {
    console.log('🔍 KONSISTENZ-VALIDIERUNG VORHER');
    console.log('=' * 50);
    
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    
    try {
        // 1. Navigiere zur Hauptseite
        await page.goto('http://localhost:8000', { waitUntil: 'networkidle' });
        await page.waitForTimeout(2000);
        
        // 2. Screenshot der Ausgangssituation
        await page.screenshot({ 
            path: '/app/minesearch_v2/frontend/consistency_before_main.png',
            fullPage: true 
        });
        
        // 3. Klicke auf Statistiken Tab
        try {
            await page.click('input[value="statistics"]');
            await page.waitForTimeout(2000);
        } catch (e) {
            console.log('⚠️ Statistiken Tab nicht gefunden, versuche Alternative...');
        }
        
        // 4. Lade Statistiken
        const statisticsButtons = await page.$$('button');
        for (const button of statisticsButtons) {
            const text = await button.textContent();
            if (text && text.includes('Statistiken')) {
                console.log('🖱️ Klicke auf Statistiken Button:', text.trim());
                await button.click();
                await page.waitForTimeout(3000);
                break;
            }
        }
        
        // 5. Screenshot der Statistiken-Seite
        await page.screenshot({ 
            path: '/app/minesearch_v2/frontend/consistency_before_statistics.png',
            fullPage: true 
        });
        
        // 6. Extrahiere aktuelle Konsistenz-Werte
        const consistencyData = await page.evaluate(() => {
            const results = {
                tables: [],
                problematicValues: [],
                undefinedValues: [],
                identicalValues: []
            };
            
            // Suche alle Tabellen
            const tables = document.querySelectorAll('table');
            tables.forEach((table, index) => {
                const rows = Array.from(table.querySelectorAll('tr'));
                const tableData = rows.map(row => {
                    const cells = Array.from(row.querySelectorAll('td, th'));
                    return cells.map(cell => cell.textContent?.trim() || '');
                });
                
                if (tableData.length > 0) {
                    results.tables.push({
                        index: index,
                        data: tableData,
                        cellCount: tableData.reduce((sum, row) => sum + row.length, 0)
                    });
                }
            });
            
            // Suche problematische Werte
            const allText = document.body.textContent || '';
            
            // Zähle "undefined" Vorkommen
            const undefinedMatches = allText.match(/undefined/gi) || [];
            results.undefinedValues = undefinedMatches.length;
            
            // Suche nach 100% Werten
            const hundredPercentMatches = allText.match(/100(\.0)?%/g) || [];
            results.identicalValues = hundredPercentMatches.length;
            
            // Suche nach 0ms Werten
            const zeroTimeMatches = allText.match(/0\s*ms/g) || [];
            results.problematicValues.push({
                type: 'zero_time',
                count: zeroTimeMatches.length
            });
            
            // Suche nach 0 Kosten
            const zeroCostMatches = allText.match(/0(\.0)?\s*(€|\$|CAD|USD)/g) || [];
            results.problematicValues.push({
                type: 'zero_cost',
                count: zeroCostMatches.length
            });
            
            return results;
        });
        
        // 7. Teste Detail-Modal (falls verfügbar)
        const modelRows = await page.$$('tr');
        let modalOpened = false;
        
        for (const row of modelRows.slice(0, 3)) { // Teste erste 3 Zeilen
            try {
                await row.click();
                await page.waitForTimeout(1000);
                
                // Prüfe ob Modal geöffnet wurde
                const modal = await page.$('.modal, .dialog, [data-modal]');
                if (modal) {
                    console.log('📋 Detail-Modal gefunden');
                    await page.screenshot({ 
                        path: '/app/minesearch_v2/frontend/consistency_before_modal.png' 
                    });
                    modalOpened = true;
                    
                    // Schließe Modal
                    const closeButton = await page.$('button:has-text("✕"), button:has-text("Schließen"), .modal-close');
                    if (closeButton) {
                        await closeButton.click();
                        await page.waitForTimeout(500);
                    }
                    break;
                }
            } catch (e) {
                // Zeile nicht klickbar, weiter
            }
        }
        
        // 8. API direkter Test
        const apiResponse = await page.evaluate(async () => {
            try {
                const response = await fetch('/api/statistics/models/detailed');
                const data = await response.json();
                return {
                    success: response.ok,
                    data: data,
                    modelsCount: data.data?.model_statistics?.length || 0
                };
            } catch (error) {
                return { success: false, error: error.message };
            }
        });
        
        // 9. Erstelle Bericht
        const report = {
            timestamp: new Date().toISOString(),
            screenshots: [
                'consistency_before_main.png',
                'consistency_before_statistics.png'
            ],
            consistencyData: consistencyData,
            modalTested: modalOpened,
            apiResponse: apiResponse,
            problems: {
                undefinedValues: consistencyData.undefinedValues,
                identicalValues: consistencyData.identicalValues,
                zeroValues: consistencyData.problematicValues,
                tablesFound: consistencyData.tables.length
            }
        };
        
        if (modalOpened) {
            report.screenshots.push('consistency_before_modal.png');
        }
        
        // 10. Speichere Bericht
        fs.writeFileSync(
            '/app/minesearch_v2/frontend/consistency_validation_before_report.json',
            JSON.stringify(report, null, 2)
        );
        
        // 11. Ausgabe
        console.log('\n📊 VORHER-ANALYSE ERGEBNISSE:');
        console.log(`   🖼️ Screenshots: ${report.screenshots.length}`);
        console.log(`   📋 Tabellen gefunden: ${consistencyData.tables.length}`);
        console.log(`   ❌ "undefined" Werte: ${consistencyData.undefinedValues}`);
        console.log(`   🔄 Identische Werte (100%): ${consistencyData.identicalValues}`);
        console.log(`   🌐 API Response: ${apiResponse.success ? '✅' : '❌'}`);
        console.log(`   📝 Modal getestet: ${modalOpened ? '✅' : '❌'}`);
        
        if (apiResponse.success) {
            console.log(`   📈 API Modelle: ${apiResponse.modelsCount}`);
        }
        
        console.log('\n📄 Bericht gespeichert: consistency_validation_before_report.json');
        
    } catch (error) {
        console.error('❌ Fehler bei VORHER-Validierung:', error);
        
        // Notfall-Screenshot
        await page.screenshot({ 
            path: '/app/minesearch_v2/frontend/consistency_before_error.png' 
        });
        
    } finally {
        await browser.close();
        console.log('🎉 VORHER-Validierung abgeschlossen!');
    }
}

if (require.main === module) {
    validateConsistencyBefore().catch(console.error);
}

module.exports = { validateConsistencyBefore };