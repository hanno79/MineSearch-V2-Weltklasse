/**
 * Author: rahn
 * Datum: 02.08.2025
 * Version: 1.0
 * Beschreibung: Playwright Test zur Validierung der undefined-Behebung
 */

const { test, expect } = require('@playwright/test');
const fs = require('fs');

test.describe('Ultimate Undefined Validation', () => {
    
    test('should achieve ZERO undefined values with aggressive fixes', async ({ page }) => {
        console.log('🎯 ULTIMATE UNDEFINED VALIDATION STARTING');
        
        // Console-Logging aktivieren
        const consoleMessages = [];
        page.on('console', msg => {
            consoleMessages.push(msg.text());
            if (msg.text().includes('🔧') || msg.text().includes('undefined')) {
                console.log('Frontend:', msg.text());
            }
        });
        
        // 1. Navigiere zur Hauptseite
        await page.goto('http://localhost:3000', { waitUntil: 'networkidle' });
        await page.waitForTimeout(3000); // Warte auf alle Fixes
        
        // 2. Prüfe ob aggressive fix geladen ist
        const aggressiveFixLoaded = await page.evaluate(() => {
            return typeof window.getUndefinedCount === 'function';
        });
        
        console.log(`🚀 Aggressive fix loaded: ${aggressiveFixLoaded ? '✅' : '❌'}`);
        
        // 3. Führe manuellen undefined-Check aus
        const manualCheck = await page.evaluate(() => {
            return window.getUndefinedCount ? window.getUndefinedCount() : -1;
        });
        
        console.log(`📊 Manual undefined check: ${manualCheck}`);
        
        // 4. Aktiviere Statistiken-Tab
        await page.evaluate(() => {
            const statisticsRadio = document.querySelector('input[value="statistics"]');
            if (statisticsRadio) {
                statisticsRadio.click();
            }
        });
        
        await page.waitForTimeout(2000);
        
        // 5. Klicke auf Statistiken-Button
        const statisticsButton = await page.locator('button:has-text("Statistiken")').first();
        if (await statisticsButton.isVisible()) {
            await statisticsButton.click();
            await page.waitForTimeout(5000); // Längere Wartezeit für API-Calls
        }
        
        // 6. Warte auf alle dynamischen Inhalte
        await page.waitForTimeout(3000);
        
        // 7. Finaler DOM-Scan
        const finalScan = await page.evaluate(() => {
            const bodyText = document.body.textContent || '';
            const undefinedMatches = bodyText.match(/undefined/gi) || [];
            
            // Sammle alle undefined-Stellen
            const undefinedElements = [];
            document.querySelectorAll('*').forEach(element => {
                if (element.textContent && element.textContent.includes('undefined') && element.children.length === 0) {
                    undefinedElements.push({
                        tag: element.tagName,
                        class: element.className,
                        text: element.textContent.substring(0, 50)
                    });
                }
            });
            
            // Spezielle Tabellen-Analyse
            const tableAnalysis = {
                tableCount: 0,
                cellsWithUndefined: 0,
                totalCells: 0
            };
            
            document.querySelectorAll('table').forEach(table => {
                tableAnalysis.tableCount++;
                const cells = table.querySelectorAll('td, th');
                tableAnalysis.totalCells += cells.length;
                
                cells.forEach(cell => {
                    if (cell.textContent && cell.textContent.includes('undefined')) {
                        tableAnalysis.cellsWithUndefined++;
                    }
                });
            });
            
            return {
                totalUndefinedCount: undefinedMatches.length,
                undefinedElements,
                tableAnalysis,
                bodyTextSample: bodyText.substring(0, 200)
            };
        });
        
        // 8. Screenshot finale Zustand
        await page.screenshot({ 
            path: '/app/minesearch_v2/frontend/test-results/ultimate-validation-final.png',
            fullPage: true 
        });
        
        // 9. Erstelle detaillierten Bericht
        const ultimateReport = {
            timestamp: new Date().toISOString(),
            test: 'ultimate-undefined-validation',
            aggressiveFixLoaded,
            manualCheckResult: manualCheck,
            finalScanResults: finalScan,
            consoleMessageCount: consoleMessages.length,
            success: finalScan.totalUndefinedCount === 0,
            improvements: {
                aggressiveFixActive: aggressiveFixLoaded,
                tablesProcessed: finalScan.tableAnalysis.tableCount > 0,
                zeroUndefined: finalScan.totalUndefinedCount === 0
            }
        };
        
        // Speichere Bericht
        fs.writeFileSync(
            '/app/minesearch_v2/frontend/test-results/ultimate-undefined-validation-report.json',
            JSON.stringify(ultimateReport, null, 2)
        );
        
        // 10. Ausgabe und Assertions
        console.log('\n🏆 ULTIMATE UNDEFINED VALIDATION RESULTS:');
        console.log(`   📊 Total undefined count: ${finalScan.totalUndefinedCount}`);
        console.log(`   📋 Tables processed: ${finalScan.tableAnalysis.tableCount}`);
        console.log(`   🔧 Table cells with undefined: ${finalScan.tableAnalysis.cellsWithUndefined}`);
        console.log(`   🚀 Aggressive fix loaded: ${aggressiveFixLoaded ? '✅' : '❌'}`);
        console.log(`   ✅ Success: ${ultimateReport.success ? '✅' : '❌'}`);
        
        if (finalScan.undefinedElements.length > 0) {
            console.log('\n⚠️ REMAINING UNDEFINED ELEMENTS:');
            finalScan.undefinedElements.slice(0, 10).forEach((el, i) => {
                console.log(`   ${i+1}. ${el.tag}.${el.class}: "${el.text}"`);
            });
        }
        
        // HAUPTASSERTION: 0 undefined-Werte
        expect(finalScan.totalUndefinedCount).toBe(0);
        expect(finalScan.tableAnalysis.cellsWithUndefined).toBe(0);
        expect(aggressiveFixLoaded).toBe(true);
        
        console.log('🎉 ULTIMATE UNDEFINED VALIDATION COMPLETED SUCCESSFULLY!');
    });
});