/*
Author: rahn
Datum: 02.08.2025
Version: 1.0
Beschreibung: FINAL Undefined Analysis - Fokus auf Frontend-Rendering der Statistik-Tabellen
*/

const { chromium } = require('playwright');
const fs = require('fs');

async function finalUndefinedAnalysis() {
    console.log('🎯 FINAL UNDEFINED ANALYSIS - Frontend Rendering Focus');
    console.log('=========================================================');
    
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    
    const analysis = {
        timestamp: new Date().toISOString(),
        phase1_main_page: {},
        phase2_statistics_load: {},
        phase3_table_rendering: {},
        phase4_undefined_sources: {},
        frontend_scripts_analysis: {},
        root_cause_analysis: {}
    };
    
    try {
        // PHASE 1: Hauptseite laden
        console.log('📄 PHASE 1: Lade MineSearch Hauptseite...');
        await page.goto('http://localhost:8000', { waitUntil: 'networkidle' });
        
        // Warte bis alles geladen ist
        await page.waitForTimeout(3000);
        
        analysis.phase1_main_page = await page.evaluate(() => {
            const body = document.body.textContent || '';
            return {
                undefinedCount: (body.match(/undefined/g) || []).length,
                hasStatisticsTab: !!document.querySelector('input[value="statistics"]'),
                scriptsLoaded: {
                    htmx: typeof htmx !== 'undefined',
                    app: typeof window.MineSearchApp !== 'undefined',
                    resultsDisplay: typeof window.MineSearchResultsDisplay !== 'undefined',
                    undefinedFix: typeof window.safeDisplayValue !== 'undefined'
                }
            };
        });
        
        console.log(`   📊 Undefined auf Hauptseite: ${analysis.phase1_main_page.undefinedCount}`);
        console.log(`   📋 Statistics Tab verfügbar: ${analysis.phase1_main_page.hasStatisticsTab}`);
        
        // PHASE 2: Statistik-Tab laden
        if (analysis.phase1_main_page.hasStatisticsTab) {
            console.log('📄 PHASE 2: Aktiviere Statistics Tab...');
            
            // Klick auf Statistics Tab
            await page.click('input[value="statistics"]');
            await page.waitForTimeout(5000); // Warte länger für API-Load
            
            analysis.phase2_statistics_load = await page.evaluate(async () => {
                // API direkt im Browser testen
                try {
                    const response = await fetch('/api/statistics/models/detailed');
                    const data = await response.json();
                    
                    return {
                        apiResponse: {
                            success: response.ok,
                            status: response.status,
                            undefinedInResponse: JSON.stringify(data).includes('undefined'),
                            modelCount: data.data?.model_statistics?.length || 0,
                            sampleData: data.data?.model_statistics?.slice(0, 2) || []
                        },
                        domAfterLoad: {
                            undefinedCount: (document.body.textContent.match(/undefined/g) || []).length,
                            hasStatisticsContainer: !!document.querySelector('.statistics-container'),
                            hasTable: !!document.querySelector('table'),
                            tableCount: document.querySelectorAll('table').length
                        }
                    };
                } catch (error) {
                    return {
                        apiError: error.message,
                        domAfterLoad: {
                            undefinedCount: (document.body.textContent.match(/undefined/g) || []).length
                        }
                    };
                }
            });
            
            console.log(`   🌐 API Status: ${analysis.phase2_statistics_load.apiResponse?.status || 'ERROR'}`);
            console.log(`   📊 Undefined nach Load: ${analysis.phase2_statistics_load.domAfterLoad.undefinedCount}`);
            console.log(`   📋 Tabellen im DOM: ${analysis.phase2_statistics_load.domAfterLoad.tableCount}`);
            
            // PHASE 3: Detaillierte Tabellen-Analyse
            console.log('📄 PHASE 3: Analysiere Tabellen-Rendering...');
            
            analysis.phase3_table_rendering = await page.evaluate(() => {
                const tables = document.querySelectorAll('table');
                const tableAnalysis = [];
                
                tables.forEach((table, index) => {
                    const cells = table.querySelectorAll('td, th');
                    const undefinedCells = [];
                    
                    cells.forEach((cell, cellIndex) => {
                        if (cell.textContent.includes('undefined')) {
                            undefinedCells.push({
                                cellIndex: cellIndex,
                                content: cell.textContent,
                                innerHTML: cell.innerHTML,
                                className: cell.className,
                                parentRow: cell.parentElement?.className || '',
                                isGenerated: cell.getAttribute('data-generated') === 'true'
                            });
                        }
                    });
                    
                    if (undefinedCells.length > 0) {
                        tableAnalysis.push({
                            tableIndex: index,
                            tableId: table.id,
                            tableClass: table.className,
                            undefinedCells: undefinedCells,
                            totalCells: cells.length
                        });
                    }
                });
                
                return {
                    totalTables: tables.length,
                    tablesWithUndefined: tableAnalysis,
                    totalUndefinedCells: tableAnalysis.reduce((sum, t) => sum + t.undefinedCells.length, 0)
                };
            });
            
            console.log(`   📋 Tabellen mit undefined: ${analysis.phase3_table_rendering.tablesWithUndefined.length}`);
            console.log(`   📊 Total undefined Zellen: ${analysis.phase3_table_rendering.totalUndefinedCells}`);
            
            // PHASE 4: Analyse der undefined-Quellen im JavaScript
            console.log('📄 PHASE 4: Analysiere JavaScript undefined-Quellen...');
            
            analysis.phase4_undefined_sources = await page.evaluate(() => {
                // Teste verschiedene JavaScript-Funktionen
                const testData = {
                    testValue1: undefined,
                    testValue2: null,
                    testValue3: 'undefined',
                    testValue4: '',
                    testObject: { prop: undefined }
                };
                
                const functionTests = {};
                
                // Teste safeDisplayValue Funktion falls verfügbar
                if (typeof window.safeDisplayValue === 'function') {
                    functionTests.safeDisplayValue = {
                        undefined: window.safeDisplayValue(undefined),
                        null: window.safeDisplayValue(null),
                        string_undefined: window.safeDisplayValue('undefined'),
                        empty: window.safeDisplayValue('')
                    };
                }
                
                // Teste MineSearchResultsDisplay.safeValue falls verfügbar
                if (typeof window.MineSearchResultsDisplay?.safeValue === 'function') {
                    functionTests.resultsDisplaySafeValue = {
                        undefined: window.MineSearchResultsDisplay.safeValue(undefined),
                        null: window.MineSearchResultsDisplay.safeValue(null),
                        string_undefined: window.MineSearchResultsDisplay.safeValue('undefined'),
                        empty: window.MineSearchResultsDisplay.safeValue('')
                    };
                }
                
                // Suche nach undefined in localStorage/sessionStorage
                const storageAnalysis = {
                    localStorage: {},
                    sessionStorage: {}
                };
                
                try {
                    for (let i = 0; i < localStorage.length; i++) {
                        const key = localStorage.key(i);
                        const value = localStorage.getItem(key);
                        if (value && value.includes('undefined')) {
                            storageAnalysis.localStorage[key] = value.substring(0, 100);
                        }
                    }
                } catch (e) {}
                
                try {
                    for (let i = 0; i < sessionStorage.length; i++) {
                        const key = sessionStorage.key(i);
                        const value = sessionStorage.getItem(key);
                        if (value && value.includes('undefined')) {
                            storageAnalysis.sessionStorage[key] = value.substring(0, 100);
                        }
                    }
                } catch (e) {}
                
                return {
                    functionTests: functionTests,
                    storageAnalysis: storageAnalysis,
                    globalVariables: {
                        hasUndefinedFix: typeof window.safeDisplayValue !== 'undefined',
                        hasResultsDisplay: typeof window.MineSearchResultsDisplay !== 'undefined',
                        undefinedFixWorking: typeof window.safeDisplayValue === 'function' && window.safeDisplayValue(undefined) !== 'undefined'
                    }
                };
            });
            
            console.log(`   🔧 Undefined-Fix verfügbar: ${analysis.phase4_undefined_sources.globalVariables.hasUndefinedFix}`);
            console.log(`   🔧 Undefined-Fix funktioniert: ${analysis.phase4_undefined_sources.globalVariables.undefinedFixWorking}`);
            
            // Screenshot für visuelle Analyse
            await page.screenshot({ 
                path: '/app/minesearch_v2/frontend/final_undefined_analysis_screenshot.png',
                fullPage: true 
            });
        }
        
        // ROOT CAUSE ANALYSIS
        console.log('📄 ROOT CAUSE ANALYSIS...');
        
        analysis.root_cause_analysis = {
            conclusion: 'IDENTIFIED',
            source: 'frontend_rendering',
            evidence: {
                api_clean: analysis.phase2_statistics_load?.apiResponse?.undefinedInResponse === false,
                frontend_has_undefined: (analysis.phase2_statistics_load?.domAfterLoad?.undefinedCount || 0) > 0,
                table_rendering_issue: analysis.phase3_table_rendering?.totalUndefinedCells > 0,
                undefined_fix_loaded: analysis.phase4_undefined_sources?.globalVariables?.hasUndefinedFix || false,
                undefined_fix_working: analysis.phase4_undefined_sources?.globalVariables?.undefinedFixWorking || false
            },
            total_undefined_found: analysis.phase2_statistics_load?.domAfterLoad?.undefinedCount || 0
        };
        
    } catch (error) {
        console.error('❌ Fehler:', error);
        analysis.error = error.message;
    } finally {
        await browser.close();
    }
    
    // Report speichern
    const reportPath = '/app/minesearch_v2/frontend/final_undefined_analysis_report.json';
    fs.writeFileSync(reportPath, JSON.stringify(analysis, null, 2));
    
    // ZUSAMMENFASSUNG
    console.log('\n🎯 FINAL UNDEFINED ANALYSIS - ERGEBNISSE:');
    console.log('=========================================================');
    
    const rootCause = analysis.root_cause_analysis;
    console.log(`📊 Total undefined gefunden: ${rootCause.total_undefined_found}`);
    console.log(`🌐 API sauber: ${rootCause.evidence.api_clean ? '✅' : '❌'}`);
    console.log(`💻 Frontend hat undefined: ${rootCause.evidence.frontend_has_undefined ? '❌' : '✅'}`);
    console.log(`📋 Tabellen-Rendering Problem: ${rootCause.evidence.table_rendering_issue ? '❌' : '✅'}`);
    console.log(`🔧 Undefined-Fix geladen: ${rootCause.evidence.undefined_fix_loaded ? '✅' : '❌'}`);
    console.log(`🔧 Undefined-Fix funktioniert: ${rootCause.evidence.undefined_fix_working ? '✅' : '❌'}`);
    
    if (analysis.phase3_table_rendering?.tablesWithUndefined) {
        console.log(`\n📋 PROBLEMATISCHE TABELLEN:`);
        analysis.phase3_table_rendering.tablesWithUndefined.forEach((table, index) => {
            console.log(`   Tabelle ${table.tableIndex}: ${table.undefinedCells.length} undefined-Zellen`);
            table.undefinedCells.slice(0, 3).forEach(cell => {
                console.log(`      Zelle ${cell.cellIndex}: "${cell.content.substring(0, 30)}..."`);
            });
        });
    }
    
    console.log(`\n📄 Report: ${reportPath}`);
    console.log(`📷 Screenshot: final_undefined_analysis_screenshot.png`);
    
    return analysis;
}

// Script ausführen
if (require.main === module) {
    finalUndefinedAnalysis()
        .then((result) => {
            console.log('\n✅ FINAL UNDEFINED ANALYSIS BEENDET');
            console.log('=========================================');
            
            const evidence = result.root_cause_analysis?.evidence;
            if (evidence) {
                if (evidence.api_clean && evidence.frontend_has_undefined) {
                    console.log('🎯 ROOT CAUSE: Frontend-Rendering-Problem bei Statistik-Tabellen');
                    console.log('💡 LÖSUNG: Überprüfe results-display.js buildConsolidatedTable() Funktion');
                } else if (!evidence.undefined_fix_working) {
                    console.log('🎯 ROOT CAUSE: undefined-fix.js lädt nicht korrekt');
                    console.log('💡 LÖSUNG: Repariere undefined-fix.js Einbindung');
                } else {
                    console.log('🎯 ROOT CAUSE: Unbekannt - weitere Analyse erforderlich');
                }
            }
            
            process.exit(0);
        })
        .catch(error => {
            console.error('❌ Fehler:', error);
            process.exit(1);
        });
}

module.exports = { finalUndefinedAnalysis };