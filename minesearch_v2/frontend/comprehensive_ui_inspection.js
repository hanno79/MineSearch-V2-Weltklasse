#!/usr/bin/env node
/**
 * Author: rahn
 * Datum: 02.08.2025
 * Version: 1.0
 * Beschreibung: Vollständige UI-Inspektion zur Identifikation aller undefined-Werte
 */

const { chromium } = require('playwright');
const fs = require('fs');

async function comprehensiveUIInspection() {
    console.log('🔍 VOLLSTÄNDIGE UI-INSPEKTION GESTARTET');
    console.log('=' * 60);
    
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    
    // Aktiviere detailliertes Logging
    page.on('console', msg => {
        if (msg.type() === 'error') {
            console.log('❌ JS Error:', msg.text());
        }
    });
    
    try {
        // 1. Navigiere zur Hauptseite
        await page.goto('http://localhost:8000', { waitUntil: 'networkidle' });
        await page.waitForTimeout(3000);
        
        console.log('📸 Screenshot 1: Hauptseite geladen');
        await page.screenshot({ 
            path: '/app/minesearch_v2/frontend/inspection_01_main.png',
            fullPage: true 
        });
        
        // 2. Analysiere Hauptseite auf undefined
        const mainPageAnalysis = await page.evaluate(() => {
            const analysis = {
                undefinedCount: 0,
                undefinedLocations: [],
                visibleText: document.body.textContent || '',
                availableTabs: [],
                statisticsElements: []
            };
            
            // Zähle undefined im sichtbaren Text
            const undefinedMatches = analysis.visibleText.match(/undefined/gi) || [];
            analysis.undefinedCount = undefinedMatches.length;
            
            // Finde undefined-Positionen im DOM
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
                        text: node.textContent.trim(),
                        parentTag: parent ? parent.tagName : 'unknown',
                        parentClass: parent ? parent.className : '',
                        parentId: parent ? parent.id : ''
                    });
                }
            }
            
            // Finde verfügbare Tabs
            const inputs = document.querySelectorAll('input[type="radio"]');
            inputs.forEach(input => {
                const label = document.querySelector(`label[for="${input.id}"]`);
                analysis.availableTabs.push({
                    id: input.id,
                    value: input.value,
                    label: label ? label.textContent.trim() : 'No label',
                    checked: input.checked
                });
            });
            
            // Finde Statistik-Elemente
            const statsElements = document.querySelectorAll('[id*="statist"], [class*="statist"], button');
            statsElements.forEach((el, index) => {
                const text = el.textContent?.trim() || '';
                if (text.includes('Statistik') || text.includes('laden') || text.includes('Modell')) {
                    analysis.statisticsElements.push({
                        index: index,
                        tag: el.tagName,
                        text: text,
                        visible: el.offsetParent !== null,
                        id: el.id,
                        className: el.className
                    });
                }
            });
            
            return analysis;
        });
        
        console.log('🔍 Hauptseite Analyse:');
        console.log(`   Undefined-Werte: ${mainPageAnalysis.undefinedCount}`);
        console.log(`   Verfügbare Tabs: ${mainPageAnalysis.availableTabs.length}`);
        console.log(`   Statistik-Elemente: ${mainPageAnalysis.statisticsElements.length}`);
        
        // 3. Navigiere zu Statistiken
        let statisticsNavigated = false;
        
        // Versuche Radio Button
        const statsRadio = await page.$('input[value="statistics"]');
        if (statsRadio) {
            console.log('🖱️ Klicke auf Statistiken Radio Button');
            await statsRadio.click();
            await page.waitForTimeout(2000);
            statisticsNavigated = true;
        }
        
        // Screenshot nach Navigation
        if (statisticsNavigated) {
            console.log('📸 Screenshot 2: Nach Statistiken-Navigation');
            await page.screenshot({ 
                path: '/app/minesearch_v2/frontend/inspection_02_statistics_nav.png',
                fullPage: true 
            });
        }
        
        // 4. Suche nach Statistiken-Button und klicke
        const buttonClicked = await page.evaluate(() => {
            const buttons = Array.from(document.querySelectorAll('button'));
            const statsButton = buttons.find(btn => {
                const text = btn.textContent || '';
                return text.includes('Statistiken') && text.includes('laden');
            });
            
            if (statsButton && statsButton.offsetParent !== null) {
                console.log('🖱️ Klicke auf Statistiken-Button:', statsButton.textContent);
                statsButton.click();
                return true;
            }
            return false;
        });
        
        if (buttonClicked) {
            console.log('✅ Statistiken-Button geklickt');
            await page.waitForTimeout(4000); // Warte auf Laden
            
            console.log('📸 Screenshot 3: Nach Button-Klick');
            await page.screenshot({ 
                path: '/app/minesearch_v2/frontend/inspection_03_after_button.png',
                fullPage: true 
            });
        }
        
        // 5. Detaillierte Statistiken-Analyse
        const statisticsPageAnalysis = await page.evaluate(() => {
            const analysis = {
                undefinedCount: 0,
                undefinedDetails: [],
                tablesFound: 0,
                tableContents: [],
                visibleStatistics: false
            };
            
            // Zähle undefined erneut
            const bodyText = document.body.textContent || '';
            const undefinedMatches = bodyText.match(/undefined/gi) || [];
            analysis.undefinedCount = undefinedMatches.length;
            
            // Finde alle undefined in Tabellen
            const tables = document.querySelectorAll('table');
            analysis.tablesFound = tables.length;
            
            tables.forEach((table, tableIndex) => {
                const rows = Array.from(table.querySelectorAll('tr'));
                const tableData = {
                    tableIndex: tableIndex,
                    rowCount: rows.length,
                    undefinedCells: []
                };
                
                rows.forEach((row, rowIndex) => {
                    const cells = Array.from(row.querySelectorAll('td, th'));
                    cells.forEach((cell, cellIndex) => {
                        const cellText = cell.textContent?.trim() || '';
                        if (cellText.includes('undefined') || cellText === 'undefined') {
                            tableData.undefinedCells.push({
                                row: rowIndex,
                                cell: cellIndex,
                                text: cellText,
                                innerHTML: cell.innerHTML
                            });
                        }
                    });
                });
                
                if (tableData.undefinedCells.length > 0) {
                    analysis.tableContents.push(tableData);
                }
            });
            
            // Prüfe ob Statistiken sichtbar sind
            analysis.visibleStatistics = tables.length > 0 || 
                document.querySelector('.statistics-container, #statistics') !== null;
            
            return analysis;
        });
        
        console.log('📊 Statistiken-Seite Analyse:');
        console.log(`   Undefined-Werte: ${statisticsPageAnalysis.undefinedCount}`);
        console.log(`   Tabellen gefunden: ${statisticsPageAnalysis.tablesFound}`);
        console.log(`   Statistiken sichtbar: ${statisticsPageAnalysis.visibleStatistics}`);
        console.log(`   Tabellen mit undefined: ${statisticsPageAnalysis.tableContents.length}`);
        
        // 6. API direkt testen
        const apiTest = await page.evaluate(async () => {
            try {
                const response = await fetch('/api/statistics/models/detailed');
                const data = await response.json();
                
                return {
                    success: response.ok,
                    status: response.status,
                    modelCount: data.data?.model_statistics?.length || 0,
                    hasNullValues: JSON.stringify(data).includes('null'),
                    sampleData: data.data?.model_statistics?.slice(0, 3) || []
                };
            } catch (error) {
                return { success: false, error: error.message };
            }
        });
        
        console.log('🌐 API Test:');
        console.log(`   Status: ${apiTest.success ? '✅' : '❌'} (${apiTest.status})`);
        console.log(`   Modelle: ${apiTest.modelCount}`);
        console.log(`   Null-Werte in API: ${apiTest.hasNullValues ? '❌' : '✅'}`);
        
        // 7. Erstelle detaillierten Bericht
        const fullReport = {
            timestamp: new Date().toISOString(),
            mainPage: mainPageAnalysis,
            statisticsPage: statisticsPageAnalysis,
            apiTest: apiTest,
            screenshots: [
                'inspection_01_main.png',
                'inspection_02_statistics_nav.png',
                'inspection_03_after_button.png'
            ],
            criticalFindings: {
                totalUndefined: statisticsPageAnalysis.undefinedCount,
                undefinedInTables: statisticsPageAnalysis.tableContents.length > 0,
                statisticsVisible: statisticsPageAnalysis.visibleStatistics,
                apiWorking: apiTest.success,
                problemSeverity: 'CRITICAL'
            }
        };
        
        // 8. Speichere Bericht
        fs.writeFileSync(
            '/app/minesearch_v2/frontend/comprehensive_ui_inspection_report.json',
            JSON.stringify(fullReport, null, 2)
        );
        
        // 9. Detaillierte Ausgabe
        console.log('\n🚨 KRITISCHE BEFUNDE:');
        console.log(`   📊 Total undefined: ${fullReport.criticalFindings.totalUndefined}`);
        console.log(`   📋 Tabellen mit undefined: ${statisticsPageAnalysis.tableContents.length}`);
        
        if (statisticsPageAnalysis.tableContents.length > 0) {
            console.log('\n📋 UNDEFINED IN TABELLEN:');
            statisticsPageAnalysis.tableContents.forEach(table => {
                console.log(`   Tabelle ${table.tableIndex}: ${table.undefinedCells.length} undefined-Zellen`);
                table.undefinedCells.slice(0, 5).forEach(cell => {
                    console.log(`     • Zeile ${cell.row}, Spalte ${cell.cell}: "${cell.text}"`);
                });
            });
        }
        
        console.log('\n📄 Vollständiger Bericht: comprehensive_ui_inspection_report.json');
        
    } catch (error) {
        console.error('❌ UI-Inspektion Fehler:', error);
        
        await page.screenshot({ 
            path: '/app/minesearch_v2/frontend/inspection_error.png' 
        });
        
    } finally {
        await browser.close();
        console.log('🎉 UI-Inspektion abgeschlossen!');
    }
}

if (require.main === module) {
    comprehensiveUIInspection().catch(console.error);
}

module.exports = { comprehensiveUIInspection };