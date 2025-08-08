/*
Author: rahn
Datum: 02.08.2025
Version: 1.0
Beschreibung: Trace der 160 undefined-Werte - Spezifische Quellenanalyse
*/

const { chromium } = require('playwright');
const fs = require('fs');

async function traceUndefinedSource() {
    console.log('🔍 Tracing undefined sources...');
    
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    
    // Fange alle console.log ab
    page.on('console', msg => {
        console.log('🖥️ Console:', msg.text());
    });
    
    const analysis = {
        timestamp: new Date().toISOString(),
        phases: {},
        detailedFindings: []
    };
    
    try {
        // PHASE 1: Hauptseite laden und analysieren
        console.log('📄 PHASE 1: Lade Hauptseite...');
        await page.goto('http://localhost:8000/index.html', { waitUntil: 'networkidle' });
        
        const phase1 = await page.evaluate(() => {
            const body = document.body.textContent || '';
            const undefinedCount = (body.match(/undefined/g) || []).length;
            
            return {
                undefinedInDOM: undefinedCount,
                pageLoaded: !!document.querySelector('#search-container'),
                hasStatisticsTab: !!document.querySelector('input[value="statistics"]')
            };
        });
        
        analysis.phases.phase1 = phase1;
        console.log(`   📊 Undefined in DOM: ${phase1.undefinedInDOM}`);
        
        // PHASE 2: Backend starten und API testen
        console.log('📄 PHASE 2: Teste Backend-Connection...');
        
        // Teste verschiedene API-Endpoints
        const apiTests = [
            'http://localhost:5001/api/models',
            'http://localhost:5001/api/consolidated_results',
            'http://localhost:5001/api/sources'
        ];
        
        const apiResults = [];
        for (const url of apiTests) {
            try {
                const response = await page.goto(url);
                const text = await response.text();
                const undefinedCount = (text.match(/undefined/g) || []).length;
                
                apiResults.push({
                    url: url,
                    status: response.status(),
                    undefinedCount: undefinedCount,
                    responseLength: text.length,
                    snippet: text.substring(0, 200)
                });
                
                console.log(`   🌐 ${url}: ${undefinedCount} undefined-Werte`);
            } catch (error) {
                apiResults.push({
                    url: url,
                    error: error.message
                });
                console.log(`   ❌ ${url}: ${error.message}`);
            }
        }
        
        analysis.phases.phase2 = { apiResults };
        
        // PHASE 3: Zurück zur Frontend-Seite und Statistiken laden
        console.log('📄 PHASE 3: Lade Frontend und navigiere zu Statistiken...');
        await page.goto('http://localhost:8000/index.html', { waitUntil: 'networkidle' });
        
        // Versuche Statistik-Seite zu laden
        await page.waitForTimeout(2000);
        
        // Prüfe ob Statistics-Tab sichtbar ist
        const statsTabVisible = await page.isVisible('input[value="statistics"]');
        console.log(`   📊 Statistics Tab sichtbar: ${statsTabVisible}`);
        
        if (statsTabVisible) {
            console.log('   📊 Klicke Statistics Tab...');
            await page.click('input[value="statistics"]');
            await page.waitForTimeout(3000);
            
            // Analysiere Statistik-Seite
            const statsAnalysis = await page.evaluate(() => {
                const body = document.body.textContent || '';
                const undefinedCount = (body.match(/undefined/g) || []).length;
                
                // Suche nach spezifischen Elementen
                const statisticsContainer = document.querySelector('.statistics-container');
                const consolidatedTable = document.querySelector('.consolidated-table-container');
                const tables = document.querySelectorAll('table');
                
                const tableAnalysis = [];
                tables.forEach((table, index) => {
                    const tableText = table.textContent || '';
                    const tableUndefined = (tableText.match(/undefined/g) || []).length;
                    
                    if (tableUndefined > 0) {
                        // Analysiere Tabellenzellen
                        const cells = [];
                        table.querySelectorAll('td, th').forEach((cell, cellIndex) => {
                            if (cell.textContent.includes('undefined')) {
                                cells.push({
                                    cellIndex: cellIndex,
                                    content: cell.textContent.substring(0, 50),
                                    tagName: cell.tagName,
                                    className: cell.className
                                });
                            }
                        });
                        
                        tableAnalysis.push({
                            tableIndex: index,
                            undefinedCount: tableUndefined,
                            cells: cells,
                            id: table.id,
                            className: table.className
                        });
                    }
                });
                
                return {
                    totalUndefined: undefinedCount,
                    hasStatisticsContainer: !!statisticsContainer,
                    hasConsolidatedTable: !!consolidatedTable,
                    tablesWithUndefined: tableAnalysis,
                    totalTables: tables.length
                };
            });
            
            analysis.phases.phase3 = statsAnalysis;
            console.log(`   📊 Statistik-Seite Undefined: ${statsAnalysis.totalUndefined}`);
            console.log(`   📋 Tabellen mit undefined: ${statsAnalysis.tablesWithUndefined.length}`);
            
            // Screenshot der Statistik-Seite
            await page.screenshot({ 
                path: '/app/minesearch_v2/frontend/undefined_trace_statistics.png',
                fullPage: true 
            });
        }
        
        // PHASE 4: Detaillierte DOM-Analyse
        console.log('📄 PHASE 4: Detaillierte DOM-Analyse...');
        
        const detailedDOMAnalysis = await page.evaluate(() => {
            const results = {
                undefinedElements: [],
                patterns: {
                    inTableCells: 0,
                    inSmallTags: 0,
                    inTextNodes: 0,
                    inAttributes: 0
                }
            };
            
            // Durchlaufe alle Elemente
            document.querySelectorAll('*').forEach((el, index) => {
                // Prüfe Textinhalt
                if (el.textContent && el.textContent.includes('undefined') && el.children.length === 0) {
                    const undefinedCount = (el.textContent.match(/undefined/g) || []).length;
                    
                    results.undefinedElements.push({
                        index: index,
                        tagName: el.tagName,
                        className: el.className,
                        id: el.id,
                        textContent: el.textContent.substring(0, 100),
                        undefinedCount: undefinedCount,
                        parent: el.parentElement ? {
                            tagName: el.parentElement.tagName,
                            className: el.parentElement.className,
                            id: el.parentElement.id
                        } : null
                    });
                    
                    // Kategorisiere
                    if (el.tagName === 'TD' || el.tagName === 'TH') {
                        results.patterns.inTableCells += undefinedCount;
                    } else if (el.tagName === 'SMALL') {
                        results.patterns.inSmallTags += undefinedCount;
                    }
                }
                
                // Prüfe Attribute
                Array.from(el.attributes).forEach(attr => {
                    if (attr.value && attr.value.includes('undefined')) {
                        results.undefinedElements.push({
                            type: 'attribute',
                            tagName: el.tagName,
                            attribute: attr.name,
                            value: attr.value,
                            className: el.className,
                            id: el.id
                        });
                        results.patterns.inAttributes++;
                    }
                });
            });
            
            // Prüfe Text-Nodes separat
            const walker = document.createTreeWalker(
                document.body,
                NodeFilter.SHOW_TEXT,
                null,
                false
            );
            
            let node;
            while (node = walker.nextNode()) {
                if (node.textContent && node.textContent.includes('undefined')) {
                    const undefinedCount = (node.textContent.match(/undefined/g) || []).length;
                    results.patterns.inTextNodes += undefinedCount;
                }
            }
            
            return results;
        });
        
        analysis.phases.phase4 = detailedDOMAnalysis;
        console.log(`   📊 DOM Elemente mit undefined: ${detailedDOMAnalysis.undefinedElements.length}`);
        console.log(`   📋 In Tabellenzellen: ${detailedDOMAnalysis.patterns.inTableCells}`);
        console.log(`   🏷️ In SMALL Tags: ${detailedDOMAnalysis.patterns.inSmallTags}`);
        console.log(`   📝 In Text Nodes: ${detailedDOMAnalysis.patterns.inTextNodes}`);
        console.log(`   🔗 In Attributen: ${detailedDOMAnalysis.patterns.inAttributes}`);
        
    } catch (error) {
        console.error('❌ Fehler:', error);
        analysis.error = error.message;
    } finally {
        await browser.close();
    }
    
    // Report speichern
    const reportPath = '/app/minesearch_v2/frontend/undefined_trace_report.json';
    fs.writeFileSync(reportPath, JSON.stringify(analysis, null, 2));
    
    console.log('\n📄 TRACE-ANALYSE ZUSAMMENFASSUNG:');
    console.log('=====================================');
    
    if (analysis.phases.phase1) {
        console.log(`📄 Phase 1 - Hauptseite: ${analysis.phases.phase1.undefinedInDOM} undefined`);
    }
    
    if (analysis.phases.phase2) {
        const totalApiUndefined = analysis.phases.phase2.apiResults
            .filter(r => r.undefinedCount)
            .reduce((sum, r) => sum + r.undefinedCount, 0);
        console.log(`🌐 Phase 2 - API: ${totalApiUndefined} undefined`);
    }
    
    if (analysis.phases.phase3) {
        console.log(`📊 Phase 3 - Statistiken: ${analysis.phases.phase3.totalUndefined} undefined`);
        console.log(`📋 Tabellen mit Problem: ${analysis.phases.phase3.tablesWithUndefined.length}`);
    }
    
    if (analysis.phases.phase4) {
        const p4 = analysis.phases.phase4.patterns;
        console.log(`📊 Phase 4 - DOM Detail:`);
        console.log(`   Tabellenzellen: ${p4.inTableCells}`);
        console.log(`   SMALL Tags: ${p4.inSmallTags}`);
        console.log(`   Text Nodes: ${p4.inTextNodes}`);
        console.log(`   Attribute: ${p4.inAttributes}`);
    }
    
    console.log(`\n📄 Report: ${reportPath}`);
    
    return analysis;
}

// Script ausführen
if (require.main === module) {
    traceUndefinedSource()
        .then(() => {
            console.log('✅ Undefined Source Trace beendet');
            process.exit(0);
        })
        .catch(error => {
            console.error('❌ Fehler:', error);
            process.exit(1);
        });
}

module.exports = { traceUndefinedSource };