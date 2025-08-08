/**
 * Author: rahn
 * Datum: 02.08.2025
 * Version: 1.0
 * Beschreibung: Browser-basierte Validierung der Konsistenzwerte im MineSearch v2 Frontend
 */

const { chromium } = require('playwright');
const fs = require('fs');

async function validateFrontendConsistencyValues() {
    console.log('🔍 Starte Browser-Validierung der Konsistenzwerte...');
    
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    
    const results = {
        timestamp: new Date().toISOString(),
        url: 'http://localhost:8000',
        findings: [],
        errors: [],
        expectedValues: {
            averageConsistency: '~49.7%',
            shouldNotBe: '100%'
        }
    };
    
    try {
        // Navigiere zur Frontend-URL
        console.log('📍 Navigiere zu http://localhost:8000...');
        await page.goto('http://localhost:8000', { waitUntil: 'networkidle' });
        await page.waitForTimeout(2000);
        
        // Screenshot für Dokumentation
        await page.screenshot({ path: '/app/minesearch_v2/frontend/validation_01_initial.png' });
        
        // Suche nach der Statistiken-Tabelle
        console.log('🔍 Suche nach Statistiken-Bereich...');
        
        // Prüfe verschiedene mögliche Selektoren für Statistiken
        const possibleSelectors = [
            '#modelsTab',
            '[data-tab="models"]',
            '.tab-button:has-text("Modelle")',
            'button:has-text("Statistiken")',
            'button:has-text("Modelle")',
            '.statistics-table',
            '#statistics-container'
        ];
        
        let statisticsFound = false;
        for (const selector of possibleSelectors) {
            try {
                const element = await page.$(selector);
                if (element) {
                    console.log(`✅ Gefunden: ${selector}`);
                    results.findings.push(`Statistiken-Element gefunden: ${selector}`);
                    statisticsFound = true;
                    break;
                }
            } catch (e) {
                // Selector nicht gefunden, weiter versuchen
            }
        }
        
        if (!statisticsFound) {
            console.log('⚠️ Kein direkter Statistiken-Bereich gefunden, prüfe verfügbare Tabs...');
            
            // Hole alle verfügbaren Tabs
            const tabs = await page.$$eval('button[data-tab], .tab-button', elements => 
                elements.map(el => ({
                    text: el.textContent?.trim(),
                    dataTab: el.getAttribute('data-tab'),
                    class: el.className
                }))
            );
            
            console.log('Verfügbare Tabs:', tabs);
            results.findings.push(`Verfügbare Tabs: ${JSON.stringify(tabs)}`);
        }
        
        // Klicke auf Modelle/Statistiken Tab wenn vorhanden
        try {
            const modelsTab = await page.$('[data-tab="models"], button:has-text("Modelle"), button:has-text("Statistiken")');
            if (modelsTab) {
                console.log('🖱️ Klicke auf Modelle/Statistiken Tab...');
                await modelsTab.click();
                await page.waitForTimeout(2000);
                await page.screenshot({ path: '/app/minesearch_v2/frontend/validation_02_after_tab_click.png' });
            }
        } catch (e) {
            console.log('ℹ️ Kein Modelle-Tab gefunden oder bereits aktiv');
        }
        
        // Suche nach "Statistiken laden" Button
        const loadStatsSelectors = [
            'button:has-text("Statistiken laden")',
            'button:has-text("Modelle laden")',
            '#loadStatistics',
            '.load-statistics-btn',
            'button[onclick*="statistics"]',
            'button[onclick*="models"]'
        ];
        
        let loadButtonFound = false;
        for (const selector of loadStatsSelectors) {
            try {
                const button = await page.$(selector);
                if (button) {
                    console.log(`🖱️ Klicke auf "Statistiken laden" Button: ${selector}...`);
                    await button.click();
                    await page.waitForTimeout(3000); // Warte auf Datenladung
                    await page.screenshot({ path: '/app/minesearch_v2/frontend/validation_03_after_load.png' });
                    loadButtonFound = true;
                    results.findings.push(`Statistiken geladen via: ${selector}`);
                    break;
                }
            } catch (e) {
                // Button nicht gefunden, weiter versuchen
            }
        }
        
        if (!loadButtonFound) {
            console.log('⚠️ Kein "Statistiken laden" Button gefunden, prüfe ob Daten bereits geladen sind...');
            results.findings.push('Kein "Statistiken laden" Button gefunden');
        }
        
        // Analysiere die ersten 5-10 Modelle in der Tabelle
        console.log('📊 Analysiere Modell-Daten in der Tabelle...');
        
        // Suche nach Tabellen-Rows mit Modell-Daten
        const tableRows = await page.$$eval('table tr, .model-row, .statistics-row', rows => {
            return rows.slice(1, 11).map((row, index) => { // Erste 10 Rows (ohne Header)
                const cells = row.querySelectorAll('td, .cell, .data-cell');
                const cellTexts = Array.from(cells).map(cell => cell.textContent?.trim());
                
                return {
                    index: index,
                    cellCount: cells.length,
                    cellTexts: cellTexts,
                    innerHTML: row.innerHTML.substring(0, 200) // Ersten 200 Zeichen für Debug
                };
            });
        });
        
        console.log(`📋 Gefundene Tabellen-Rows: ${tableRows.length}`);
        
        if (tableRows.length > 0) {
            results.findings.push(`Tabellen-Rows gefunden: ${tableRows.length}`);
            
            // Analysiere jeden Row auf Konsistenz-Werte
            tableRows.forEach((row, index) => {
                console.log(`\n📊 Modell ${index + 1}:`);
                console.log(`   Zellen: ${row.cellCount}`);
                console.log(`   Texte: ${JSON.stringify(row.cellTexts)}`);
                
                // Suche nach Konsistenz-Werten
                const consistencyValues = row.cellTexts.filter(text => 
                    text && (text.includes('%') || text.includes('consistency') || text.includes('konsistenz'))
                );
                
                if (consistencyValues.length > 0) {
                    console.log(`   🎯 Konsistenz-Werte: ${JSON.stringify(consistencyValues)}`);
                    results.findings.push(`Modell ${index + 1} - Konsistenz: ${JSON.stringify(consistencyValues)}`);
                    
                    // Prüfe ob noch 100% angezeigt wird
                    const has100Percent = consistencyValues.some(val => val.includes('100%'));
                    if (has100Percent) {
                        results.findings.push(`⚠️ Modell ${index + 1} zeigt noch 100% Konsistenz!`);
                    }
                }
            });
        } else {
            console.log('⚠️ Keine Tabellen-Rows mit Modell-Daten gefunden');
            results.findings.push('Keine Tabellen-Rows mit Modell-Daten gefunden');
            
            // Fallback: Suche nach beliebigen Konsistenz-Werten auf der Seite
            const allConsistencyTexts = await page.$$eval('*', elements => {
                const texts = [];
                elements.forEach(el => {
                    const text = el.textContent?.trim();
                    if (text && (text.includes('%') || text.includes('consistency') || text.includes('konsistenz'))) {
                        texts.push(text);
                    }
                });
                return [...new Set(texts)].slice(0, 20); // Unique values, maximal 20
            });
            
            console.log('🔍 Alle gefundenen Konsistenz-Texte:', allConsistencyTexts);
            results.findings.push(`Alle Konsistenz-Texte auf Seite: ${JSON.stringify(allConsistencyTexts)}`);
        }
        
        // Teste Detail-Modal
        console.log('\n🔍 Teste Detail-Modal Funktionalität...');
        
        // Suche nach Detail-Buttons oder klickbaren Modell-Rows
        const detailSelectors = [
            'button:has-text("Details")',
            '.detail-btn',
            'tr:first-of-type td:first-child', // Erste Modell-Row
            '.model-row:first-child',
            'button[onclick*="detail"]'
        ];
        
        let detailModalOpened = false;
        for (const selector of detailSelectors) {
            try {
                const element = await page.$(selector);
                if (element) {
                    console.log(`🖱️ Klicke auf Detail-Element: ${selector}...`);
                    await element.click();
                    await page.waitForTimeout(2000);
                    
                    // Prüfe ob Modal geöffnet wurde
                    const modal = await page.$('.modal, .detail-modal, [role="dialog"]');
                    if (modal) {
                        console.log('✅ Detail-Modal erfolgreich geöffnet!');
                        await page.screenshot({ path: '/app/minesearch_v2/frontend/validation_04_modal_open.png' });
                        detailModalOpened = true;
                        results.findings.push('Detail-Modal erfolgreich geöffnet');
                        
                        // Suche nach Feld-Konsistenz Sektion
                        const fieldConsistencySection = await page.$(':has-text("Feld-Konsistenz"), :has-text("📊"), :has-text("Field Consistency")');
                        if (fieldConsistencySection) {
                            console.log('✅ Feld-Konsistenz Sektion gefunden!');
                            results.findings.push('Feld-Konsistenz Sektion im Modal vorhanden');
                            
                            // Suche nach Feld-Konsistenz laden Button
                            const loadFieldConsistencyBtn = await page.$('button:has-text("Feld-Konsistenz laden"), button:has-text("🔍")');
                            if (loadFieldConsistencyBtn) {
                                console.log('🖱️ Klicke auf "Feld-Konsistenz laden" Button...');
                                await loadFieldConsistencyBtn.click();
                                await page.waitForTimeout(3000);
                                await page.screenshot({ path: '/app/minesearch_v2/frontend/validation_05_field_consistency.png' });
                                results.findings.push('Feld-Konsistenz Button geklickt');
                                
                                // Analysiere angezeigte Feld-Konsistenz Werte
                                const fieldValues = await page.$$eval('.field-consistency-item, .consistency-field', elements => {
                                    return elements.map(el => ({
                                        text: el.textContent?.trim(),
                                        innerHTML: el.innerHTML.substring(0, 100)
                                    }));
                                });
                                
                                console.log('📊 Feld-Konsistenz Werte:', fieldValues);
                                results.findings.push(`Feld-Konsistenz Werte: ${JSON.stringify(fieldValues)}`);
                            } else {
                                results.findings.push('❌ Feld-Konsistenz Button nicht gefunden');
                            }
                        } else {
                            results.findings.push('❌ Feld-Konsistenz Sektion nicht gefunden');
                        }
                        
                        break;
                    }
                }
            } catch (e) {
                // Element nicht gefunden oder klickbar
            }
        }
        
        if (!detailModalOpened) {
            console.log('⚠️ Kein Detail-Modal konnte geöffnet werden');
            results.findings.push('❌ Detail-Modal konnte nicht geöffnet werden');
        }
        
        // Final Screenshot
        await page.screenshot({ path: '/app/minesearch_v2/frontend/validation_06_final.png' });
        
        console.log('\n✅ Browser-Validierung abgeschlossen!');
        
    } catch (error) {
        console.error('❌ Fehler bei Browser-Validierung:', error);
        results.errors.push(`Fehler: ${error.message}`);
    } finally {
        await browser.close();
        
        // Speichere Ergebnisse
        const reportPath = '/app/minesearch_v2/frontend/browser_validation_report.json';
        fs.writeFileSync(reportPath, JSON.stringify(results, null, 2));
        console.log(`📄 Validierungs-Report gespeichert: ${reportPath}`);
        
        return results;
    }
}

// Führe Validierung aus
validateFrontendConsistencyValues()
    .then(results => {
        console.log('\n📊 VALIDIERUNGS-ZUSAMMENFASSUNG:');
        console.log('=================================');
        results.findings.forEach(finding => console.log(`• ${finding}`));
        
        if (results.errors.length > 0) {
            console.log('\n❌ FEHLER:');
            results.errors.forEach(error => console.log(`• ${error}`));
        }
        
        // Analyse der Ergebnisse
        const still100Percent = results.findings.some(f => f.includes('100%'));
        const hasRealisticValues = results.findings.some(f => f.includes('%') && !f.includes('100%'));
        
        console.log('\n🎯 KRITISCHE ANALYSE:');
        console.log(`   • Zeigt noch 100% Konsistenz: ${still100Percent ? 'JA ⚠️' : 'NEIN ✅'}`);
        console.log(`   • Hat realistische Werte: ${hasRealisticValues ? 'JA ✅' : 'NEIN ⚠️'}`);
        
        if (still100Percent) {
            console.log('\n🚨 PROBLEM IDENTIFIZIERT: Frontend zeigt noch 100% Konsistenz!');
            console.log('   → Frontend-Backend-Verbindungsproblem vermutet');
        }
    })
    .catch(error => {
        console.error('❌ Kritischer Fehler:', error);
    });