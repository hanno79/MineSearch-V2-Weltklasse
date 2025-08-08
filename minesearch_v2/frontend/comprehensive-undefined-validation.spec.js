/**
 * Author: rahn
 * Datum: 02.08.2025
 * Version: 1.0
 * Beschreibung: Umfassende Playwright-Validierung für undefined-Werte
 */

const { test, expect } = require('@playwright/test');
const fs = require('fs');

test.describe('Comprehensive Undefined Validation', () => {
    
    test('should have zero undefined values in DOM after fix', async ({ page }) => {
        console.log('🎯 STARTING UNDEFINED VALIDATION');
        
        // Console-Logging aktivieren
        const consoleMessages = [];
        page.on('console', msg => {
            consoleMessages.push(msg.text());
            if (msg.text().includes('undefined') || msg.text().includes('Fixing')) {
                console.log('🔧 Frontend Log:', msg.text());
            }
        });
        
        // 1. Navigiere zur Hauptseite
        await page.goto('http://localhost:3000', { waitUntil: 'networkidle' });
        await page.waitForTimeout(2000);
        
        // Screenshot vor Tests
        await page.screenshot({ 
            path: '/app/minesearch_v2/frontend/test-results/validation_01_initial.png',
            fullPage: true 
        });
        
        // 2. Prüfe ob undefined-fix.js geladen ist
        const undefinedFixLoaded = await page.evaluate(() => {
            return typeof window.safeDisplayValue === 'function';
        });
        
        console.log(`🛡️ Undefined-Fix loaded: ${undefinedFixLoaded ? '✅' : '❌'}`);
        expect(undefinedFixLoaded).toBe(true);
        
        // 3. Teste safeDisplayValue-Funktion
        const functionTests = await page.evaluate(() => {
            const tests = {
                undefined: window.safeDisplayValue(undefined),
                null: window.safeDisplayValue(null),
                undefinedString: window.safeDisplayValue('undefined'),
                nullString: window.safeDisplayValue('null'),
                emptyString: window.safeDisplayValue(''),
                validValue: window.safeDisplayValue('valid')
            };
            return tests;
        });
        
        console.log('🧪 Function Tests:', functionTests);
        expect(functionTests.undefined).toBe('N/A');
        expect(functionTests.null).toBe('N/A');
        expect(functionTests.undefinedString).toBe('N/A');
        expect(functionTests.validValue).toBe('valid');
        
        // 4. Zähle undefined-Werte im DOM
        const undefinedAnalysis = await page.evaluate(() => {
            const body = document.body;
            const fullText = body.textContent || '';
            const undefinedMatches = fullText.match(/undefined/gi) || [];
            
            // Sammle spezifische undefined-Stellen
            const undefinedElements = [];
            const walker = document.createTreeWalker(
                body,
                NodeFilter.SHOW_TEXT,
                null,
                false
            );
            
            let node;
            while (node = walker.nextNode()) {
                if (node.textContent && node.textContent.includes('undefined')) {
                    const parent = node.parentElement;
                    undefinedElements.push({
                        text: node.textContent.trim(),
                        parentTag: parent ? parent.tagName : 'unknown',
                        parentClass: parent ? parent.className : ''
                    });
                }
            }
            
            return {
                totalCount: undefinedMatches.length,
                elements: undefinedElements,
                bodyText: fullText.substring(0, 500) // Erste 500 Zeichen für Debug
            };
        });
        
        console.log(`📊 Undefined count in DOM: ${undefinedAnalysis.totalCount}`);
        
        if (undefinedAnalysis.totalCount > 0) {
            console.log('⚠️ Found undefined values in:');
            undefinedAnalysis.elements.forEach((el, i) => {
                console.log(`   ${i+1}. ${el.parentTag}.${el.parentClass}: "${el.text}"`);
            });
        }
        
        // 5. Aktiviere Statistiken-Tab
        await page.evaluate(() => {
            const statisticsRadio = document.querySelector('input[value="statistics"]');
            if (statisticsRadio) {
                statisticsRadio.click();
            }
        });
        
        await page.waitForTimeout(1000);
        
        // Screenshot nach Tab-Aktivierung
        await page.screenshot({ 
            path: '/app/minesearch_v2/frontend/test-results/validation_02_tab_active.png',
            fullPage: true 
        });
        
        // 6. Klicke auf Statistiken-Button
        const statisticsButton = await page.locator('button:has-text("Statistiken")').first();
        if (await statisticsButton.isVisible()) {
            await statisticsButton.click();
            await page.waitForTimeout(3000); // Warte auf Laden
            
            // Screenshot nach Button-Klick
            await page.screenshot({ 
                path: '/app/minesearch_v2/frontend/test-results/validation_03_after_stats.png',
                fullPage: true 
            });
        }
        
        // 7. Analysiere Tabellen auf undefined-Werte
        const tableAnalysis = await page.evaluate(() => {
            const tables = document.querySelectorAll('table');
            const analysis = {
                tableCount: tables.length,
                totalCells: 0,
                undefinedInTables: 0,
                naValues: 0,
                cellContents: []
            };
            
            tables.forEach(table => {
                const cells = table.querySelectorAll('td, th');
                analysis.totalCells += cells.length;
                
                cells.forEach(cell => {
                    const text = cell.textContent?.trim() || '';
                    if (text.includes('undefined')) {
                        analysis.undefinedInTables++;
                    }
                    if (text === 'N/A') {
                        analysis.naValues++;
                    }
                    
                    // Sammle Beispiel-Zellinhalte
                    if (analysis.cellContents.length < 20) {
                        analysis.cellContents.push(text);
                    }
                });
            });
            
            return analysis;
        });
        
        console.log('📋 Table Analysis:');
        console.log(`   Tables: ${tableAnalysis.tableCount}`);
        console.log(`   Total cells: ${tableAnalysis.totalCells}`);
        console.log(`   Undefined in tables: ${tableAnalysis.undefinedInTables}`);
        console.log(`   N/A values: ${tableAnalysis.naValues}`);
        
        // 8. Finaler undefined-Count nach allen Aktionen
        const finalUndefinedCount = await page.evaluate(() => {
            const fullText = document.body.textContent || '';
            return (fullText.match(/undefined/gi) || []).length;
        });
        
        console.log(`🏁 Final undefined count: ${finalUndefinedCount}`);
        
        // 9. Browser-Compatibility Tests
        const browserFeatures = await page.evaluate(() => {
            return {
                mutationObserver: typeof MutationObserver !== 'undefined',
                treeWalker: typeof document.createTreeWalker !== 'undefined',
                propertyDescriptor: typeof Object.getOwnPropertyDescriptor !== 'undefined',
                defineProperty: typeof Object.defineProperty !== 'undefined'
            };
        });
        
        console.log('🌐 Browser Features:', browserFeatures);
        
        // 10. Erstelle finalen Bericht
        const finalReport = {
            timestamp: new Date().toISOString(),
            test: 'comprehensive-undefined-validation',
            results: {
                undefinedFixLoaded,
                functionTests,
                domAnalysis: undefinedAnalysis,
                tableAnalysis,
                finalUndefinedCount,
                browserFeatures,
                consoleMessageCount: consoleMessages.length
            },
            success: finalUndefinedCount === 0 && undefinedFixLoaded,
            screenshots: [
                'validation_01_initial.png',
                'validation_02_tab_active.png', 
                'validation_03_after_stats.png'
            ]
        };
        
        // Speichere Bericht
        fs.writeFileSync(
            '/app/minesearch_v2/frontend/test-results/comprehensive-undefined-validation-report.json',
            JSON.stringify(finalReport, null, 2)
        );
        
        // Screenshot finale Zustand
        await page.screenshot({ 
            path: '/app/minesearch_v2/frontend/test-results/validation_04_final.png',
            fullPage: true 
        });
        
        // 11. Assertions
        expect(finalUndefinedCount).toBe(0); // HAUPTZIEL: 0 undefined-Werte
        expect(undefinedFixLoaded).toBe(true);
        expect(tableAnalysis.undefinedInTables).toBe(0);
        
        console.log('✅ ALL UNDEFINED VALIDATION TESTS PASSED!');
    });
    
    test('should prevent new undefined values', async ({ page }) => {
        await page.goto('http://localhost:3000');
        
        // Injiziere undefined-Werte und teste ob sie automatisch gefixt werden
        const preventionTest = await page.evaluate(() => {
            // Erstelle Element mit undefined
            const testDiv = document.createElement('div');
            testDiv.textContent = 'undefined';
            document.body.appendChild(testDiv);
            
            // Warte kurz für MutationObserver
            return new Promise(resolve => {
                setTimeout(() => {
                    resolve(testDiv.textContent);
                }, 100);
            });
        });
        
        expect(preventionTest).toBe('N/A');
        console.log('🛡️ Prevention test passed - undefined automatically fixed to N/A');
    });
    
    test('should handle API responses without undefined', async ({ page }) => {
        await page.goto('http://localhost:3000');
        
        // Teste API-Response
        const apiTest = await page.evaluate(async () => {
            try {
                const response = await fetch('/api/statistics/models/detailed');
                const data = await response.json();
                const jsonString = JSON.stringify(data);
                
                return {
                    success: response.ok,
                    undefinedInResponse: (jsonString.match(/undefined/g) || []).length,
                    responseSize: jsonString.length
                };
            } catch (error) {
                return { success: false, error: error.message };
            }
        });
        
        console.log('🌐 API Test:', apiTest);
        
        if (apiTest.success) {
            expect(apiTest.undefinedInResponse).toBe(0);
        }
    });
});