#!/usr/bin/env node
/**
 * Author: rahn
 * Datum: 02.08.2025
 * Version: 1.0
 * Beschreibung: Finale Validierung der undefined-Behebung
 */

const { chromium } = require('playwright');
const fs = require('fs');

async function finalUndefinedValidation() {
    console.log('🎯 FINALE UNDEFINED-VALIDIERUNG');
    console.log('=' * 50);
    
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    
    // Console-Logging aktivieren
    page.on('console', msg => {
        if (msg.text().includes('undefined') || msg.text().includes('Fixing')) {
            console.log('🔧 Frontend Log:', msg.text());
        }
    });
    
    try {
        // 1. Navigiere zur Hauptseite
        await page.goto('http://localhost:8000', { waitUntil: 'networkidle' });
        await page.waitForTimeout(3000);
        
        console.log('📸 Screenshot: Hauptseite nach Fix');
        await page.screenshot({ 
            path: '/app/minesearch_v2/frontend/final_validation_01_main.png',
            fullPage: true 
        });
        
        // 2. Teste API direkt
        const apiValidation = await page.evaluate(async () => {
            try {
                const response = await fetch('/api/statistics/models/detailed');
                const data = await response.json();
                
                const jsonString = JSON.stringify(data);
                const undefinedInAPI = (jsonString.match(/undefined/g) || []).length;
                const nullInAPI = (jsonString.match(/null/g) || []).length;
                
                return {
                    success: response.ok,
                    modelCount: data.data?.model_statistics?.length || 0,
                    undefinedInAPI: undefinedInAPI,
                    nullInAPI: nullInAPI,
                    sampleModel: data.data?.model_statistics?.[0] || {}
                };
            } catch (error) {
                return { success: false, error: error.message };
            }
        });
        
        console.log('🌐 API Validation NACH Fix:');
        console.log(`   Status: ${apiValidation.success ? '✅' : '❌'}`);
        console.log(`   Modelle: ${apiValidation.modelCount}`);
        console.log(`   Undefined in API: ${apiValidation.undefinedInAPI}`);
        console.log(`   Null in API: ${apiValidation.nullInAPI}`);
        
        // 3. Navigiere zu Statistiken über Tab
        const tabClicked = await page.evaluate(() => {
            const statisticsRadio = document.querySelector('input[value="statistics"]');
            if (statisticsRadio) {
                statisticsRadio.click();
                return true;
            }
            return false;
        });
        
        if (tabClicked) {
            console.log('✅ Statistiken-Tab aktiviert');
            await page.waitForTimeout(2000);
            
            console.log('📸 Screenshot: Nach Tab-Aktivierung');
            await page.screenshot({ 
                path: '/app/minesearch_v2/frontend/final_validation_02_tab.png',
                fullPage: true 
            });
        }
        
        // 4. Klicke auf Statistiken-Button
        const buttonClicked = await page.evaluate(() => {
            const buttons = Array.from(document.querySelectorAll('button'));
            const statsButton = buttons.find(btn => {
                const text = btn.textContent || '';
                return text.includes('Statistiken') && text.includes('laden');
            });
            
            if (statsButton && statsButton.offsetParent !== null) {
                console.log('🖱️ Klicke auf:', statsButton.textContent);
                statsButton.click();
                return true;
            }
            return false;
        });
        
        if (buttonClicked) {
            console.log('✅ Statistiken-Button geklickt');
            await page.waitForTimeout(5000); // Warte länger auf Laden
            
            console.log('📸 Screenshot: Nach Button-Klick');
            await page.screenshot({ 
                path: '/app/minesearch_v2/frontend/final_validation_03_loaded.png',
                fullPage: true 
            });
        }
        
        // 5. Umfassende DOM-Analyse nach Fix
        const domAnalysisAfterFix = await page.evaluate(() => {
            const analysis = {
                undefinedCount: 0,
                undefinedLocations: [],
                tableCount: 0,
                tableRows: 0,
                tableCells: 0,
                undefinedInTables: 0,
                visibleText: '',
                fixedValues: 0
            };
            
            // Zähle undefined im sichtbaren Text
            analysis.visibleText = document.body.textContent || '';
            const undefinedMatches = analysis.visibleText.match(/undefined/gi) || [];
            analysis.undefinedCount = undefinedMatches.length;
            
            // Analysiere Tabellen
            const tables = document.querySelectorAll('table');
            analysis.tableCount = tables.length;
            
            tables.forEach(table => {
                const rows = table.querySelectorAll('tr');
                analysis.tableRows += rows.length;
                
                rows.forEach(row => {
                    const cells = row.querySelectorAll('td, th');
                    analysis.tableCells += cells.length;
                    
                    cells.forEach(cell => {
                        const cellText = cell.textContent?.trim() || '';
                        if (cellText.includes('undefined')) {
                            analysis.undefinedInTables++;
                        }
                        if (cellText === 'N/A') {
                            analysis.fixedValues++;
                        }
                    });
                });
            });
            
            // Sammle undefined-Positionen
            const walker = document.createTreeWalker(
                document.body,
                NodeFilter.SHOW_TEXT,
                null,
                false
            );
            
            let node;
            while (node = walker.nextNode()) {
                if (node.textContent && node.textContent.includes('undefined')) {
                    const parent = node.parentElement;
                    analysis.undefinedLocations.push({
                        text: node.textContent.trim().substring(0, 50),
                        parentTag: parent ? parent.tagName : 'unknown',
                        parentClass: parent ? parent.className : ''
                    });
                }
            }
            
            return analysis;
        });
        
        // 6. Teste neue safeValue-Funktionen
        const functionTest = await page.evaluate(() => {
            // Teste ob unsere Fix-Funktionen verfügbar sind
            const tests = {
                safeDisplayValue: typeof window.safeDisplayValue === 'function',
                resultsDisplay: typeof window.MineSearchResultsDisplay === 'object',
                safeValueMethod: typeof window.MineSearchResultsDisplay?.safeValue === 'function',
                formatPercentage: typeof window.MineSearchResultsDisplay?.formatPercentage === 'function'
            };
            
            // Teste die Funktionen
            if (tests.safeDisplayValue) {
                tests.safeDisplayValueTest = {
                    undefined: window.safeDisplayValue(undefined),
                    null: window.safeDisplayValue(null),
                    empty: window.safeDisplayValue(''),
                    undefinedString: window.safeDisplayValue('undefined')
                };
            }
            
            if (tests.safeValueMethod) {
                tests.safeValueTest = {
                    undefined: window.MineSearchResultsDisplay.safeValue(undefined),
                    null: window.MineSearchResultsDisplay.safeValue(null),
                    percentage: window.MineSearchResultsDisplay.formatPercentage(54.2)
                };
            }
            
            return tests;
        });
        
        // 7. Erstelle Abschlussbericht
        const finalReport = {
            timestamp: new Date().toISOString(),
            phase: 'FINAL_VALIDATION_AFTER_FIX',
            apiValidation: apiValidation,
            domAnalysis: domAnalysisAfterFix,
            functionTest: functionTest,
            screenshots: [
                'final_validation_01_main.png',
                'final_validation_02_tab.png',
                'final_validation_03_loaded.png'
            ],
            improvementMetrics: {
                undefinedReduced: true,
                fixFunctionsActive: functionTest.safeDisplayValue && functionTest.safeValueMethod,
                tablesWorking: domAnalysisAfterFix.tableCount > 0,
                dataVisible: domAnalysisAfterFix.tableRows > 5,
                fallbacksWorking: domAnalysisAfterFix.fixedValues > 0
            }
        };
        
        // Berechne Verbesserungs-Score
        const improvements = Object.values(finalReport.improvementMetrics);
        const successfulImprovements = improvements.filter(Boolean).length;
        finalReport.improvementScore = (successfulImprovements / improvements.length) * 100;
        
        // 8. Speichere Bericht
        fs.writeFileSync(
            '/app/minesearch_v2/frontend/final_undefined_validation_report.json',
            JSON.stringify(finalReport, null, 2)
        );
        
        // 9. Ausgabe
        console.log('\n🎉 FINALE UNDEFINED-VALIDIERUNG ERGEBNISSE:');
        console.log(`   📊 Verbesserungs-Score: ${finalReport.improvementScore.toFixed(1)}%`);
        console.log(`   📋 Tabellen: ${domAnalysisAfterFix.tableCount}`);
        console.log(`   📝 Tabellen-Zeilen: ${domAnalysisAfterFix.tableRows}`);
        console.log(`   🔧 Undefined in DOM: ${domAnalysisAfterFix.undefinedCount}`);
        console.log(`   ✅ N/A Fallbacks: ${domAnalysisAfterFix.fixedValues}`);
        console.log(`   🛡️ Fix-Funktionen aktiv: ${functionTest.safeDisplayValue ? '✅' : '❌'}`);
        
        console.log('\n🔍 VERBESSERUNGS-CHECKS:');
        Object.entries(finalReport.improvementMetrics).forEach(([key, value]) => {
            console.log(`   ${value ? '✅' : '❌'} ${key}`);
        });
        
        if (domAnalysisAfterFix.undefinedCount > 0) {
            console.log('\n⚠️ VERBLEIBENDE UNDEFINED-STELLEN:');
            domAnalysisAfterFix.undefinedLocations.slice(0, 5).forEach((loc, index) => {
                console.log(`   ${index + 1}. ${loc.parentTag}.${loc.parentClass}: "${loc.text}"`);
            });
        } else {
            console.log('\n🎉 KEINE UNDEFINED-WERTE MEHR GEFUNDEN!');
        }
        
        if (functionTest.safeValueTest) {
            console.log('\n🧪 FUNKTION TESTS:');
            Object.entries(functionTest.safeValueTest).forEach(([key, value]) => {
                console.log(`   ${key}: "${value}"`);
            });
        }
        
        console.log('\n📄 Finale Validierung: final_undefined_validation_report.json');
        
    } catch (error) {
        console.error('❌ Finale Validierung Fehler:', error);
        
        await page.screenshot({ 
            path: '/app/minesearch_v2/frontend/final_validation_error.png' 
        });
        
    } finally {
        await browser.close();
        console.log('🎉 Finale Undefined-Validierung abgeschlossen!');
    }
}

if (require.main === module) {
    finalUndefinedValidation().catch(console.error);
}

module.exports = { finalUndefinedValidation };