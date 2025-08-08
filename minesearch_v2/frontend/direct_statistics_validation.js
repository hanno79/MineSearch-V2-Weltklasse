/**
 * Author: rahn
 * Datum: 02.08.2025
 * Version: 1.0
 * Beschreibung: Direkte Validierung der Statistiken-API und Frontend-Verbindung
 */

const { chromium } = require('playwright');
const fs = require('fs');

async function directStatisticsValidation() {
    console.log('🔍 Starte direkte Statistiken-Validierung...');
    
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    
    const results = {
        timestamp: new Date().toISOString(),
        url: 'http://localhost:8000',
        apiCalls: [],
        domAnalysis: [],
        criticalFindings: [],
        networkRequests: []
    };
    
    try {
        // Intercepte alle Netzwerk-Requests
        page.on('request', request => {
            if (request.url().includes('models') || request.url().includes('statistics') || request.url().includes('api')) {
                results.networkRequests.push({
                    url: request.url(),
                    method: request.method(),
                    timestamp: new Date().toISOString(),
                    type: 'request'
                });
                console.log(`📡 REQUEST: ${request.method()} ${request.url()}`);
            }
        });
        
        page.on('response', response => {
            if (response.url().includes('models') || response.url().includes('statistics') || response.url().includes('api')) {
                results.networkRequests.push({
                    url: response.url(),
                    status: response.status(),
                    timestamp: new Date().toISOString(),
                    type: 'response'
                });
                console.log(`📡 RESPONSE: ${response.status()} ${response.url()}`);
            }
        });
        
        // Navigiere zur Seite
        console.log('📍 Navigiere zu http://localhost:8000...');
        await page.goto('http://localhost:8000', { waitUntil: 'networkidle' });
        await page.waitForTimeout(2000);
        
        // Screenshot initial
        await page.screenshot({ path: '/app/minesearch_v2/frontend/direct_01_initial.png' });
        
        // Analysiere DOM-Struktur nach Statistiken-Elementen
        console.log('🔍 Analysiere DOM für Statistiken-Elemente...');
        
        const domElements = await page.evaluate(() => {
            const elements = [];
            
            // Suche nach relevanten Elementen
            const buttons = document.querySelectorAll('button');
            buttons.forEach((btn, index) => {
                const text = btn.textContent?.trim();
                if (text && (text.includes('Statistiken') || text.includes('Modelle') || text.includes('laden'))) {
                    elements.push({
                        type: 'button',
                        text: text,
                        id: btn.id,
                        classes: btn.className,
                        onclick: btn.onclick?.toString() || 'none',
                        index: index
                    });
                }
            });
            
            // Suche nach Tabellen-Containern
            const tables = document.querySelectorAll('table, .table, .statistics-table, .models-table');
            tables.forEach((table, index) => {
                elements.push({
                    type: 'table',
                    id: table.id,
                    classes: table.className,
                    rowCount: table.querySelectorAll('tr').length,
                    index: index
                });
            });
            
            // Suche nach Container für Statistiken
            const containers = document.querySelectorAll('#statistics-container, .statistics-container, #models-container, .models-container');
            containers.forEach((container, index) => {
                elements.push({
                    type: 'container',
                    id: container.id,
                    classes: container.className,
                    innerHTML: container.innerHTML.substring(0, 200),
                    index: index
                });
            });
            
            return elements;
        });
        
        console.log('📋 DOM-Elemente gefunden:', domElements);
        results.domAnalysis = domElements;
        
        // Teste direkten API-Aufruf
        console.log('🔗 Teste direkte API-Aufrufe...');
        
        // Test 1: Models API
        try {
            const modelsResponse = await page.evaluate(async () => {
                const response = await fetch('/api/models_info');
                return {
                    status: response.status,
                    ok: response.ok,
                    data: await response.text()
                };
            });
            console.log('📊 Models API Response:', modelsResponse.status, modelsResponse.ok ? '✅' : '❌');
            results.apiCalls.push({
                endpoint: '/api/models_info',
                status: modelsResponse.status,
                success: modelsResponse.ok,
                dataPreview: modelsResponse.data.substring(0, 200)
            });
        } catch (error) {
            console.log('❌ Models API Error:', error.message);
            results.apiCalls.push({
                endpoint: '/api/models_info',
                error: error.message
            });
        }
        
        // Test 2: Consolidated Results API
        try {
            const consolidatedResponse = await page.evaluate(async () => {
                const response = await fetch('/api/consolidated_results');
                return {
                    status: response.status,
                    ok: response.ok,
                    data: await response.text()
                };
            });
            console.log('📊 Consolidated API Response:', consolidatedResponse.status, consolidatedResponse.ok ? '✅' : '❌');
            results.apiCalls.push({
                endpoint: '/api/consolidated_results',
                status: consolidatedResponse.status,
                success: consolidatedResponse.ok,
                dataPreview: consolidatedResponse.data.substring(0, 200)
            });
        } catch (error) {
            console.log('❌ Consolidated API Error:', error.message);
            results.apiCalls.push({
                endpoint: '/api/consolidated_results',
                error: error.message
            });
        }
        
        // Versuche JavaScript-Funktionen im Browser zu finden
        console.log('🔍 Suche nach JavaScript-Funktionen...');
        
        const jsFunctions = await page.evaluate(() => {
            const functions = [];
            
            // Suche nach globalen Funktionen
            if (typeof loadStatistics === 'function') {
                functions.push('loadStatistics found');
            }
            if (typeof loadModels === 'function') {
                functions.push('loadModels found');
            }
            if (typeof showStatistics === 'function') {
                functions.push('showStatistics found');
            }
            
            // Suche in Window-Objekten
            for (let key in window) {
                if (typeof window[key] === 'function' && (key.includes('statistic') || key.includes('model'))) {
                    functions.push(`${key} found in window`);
                }
            }
            
            return functions;
        });
        
        console.log('🔧 JavaScript-Funktionen:', jsFunctions);
        results.domAnalysis.push({ type: 'javascript', functions: jsFunctions });
        
        // Versuche Statistiken-Button zu finden und zu klicken
        const statisticsButtons = domElements.filter(el => 
            el.type === 'button' && 
            (el.text.includes('Statistiken') || el.text.includes('Modelle'))
        );
        
        if (statisticsButtons.length > 0) {
            console.log(`🖱️ Versuche Klick auf Statistiken-Button: ${statisticsButtons[0].text}`);
            
            try {
                // Klicke auf den ersten Statistiken-Button
                await page.click('button:has-text("Statistiken")');
                await page.waitForTimeout(3000);
                
                // Screenshot nach Klick
                await page.screenshot({ path: '/app/minesearch_v2/frontend/direct_02_after_click.png' });
                
                // Prüfe ob neue Tabellen-Elemente erschienen sind
                const tablesAfterClick = await page.$$eval('table tr', rows => {
                    return rows.slice(0, 10).map((row, index) => {
                        const cells = row.querySelectorAll('td, th');
                        return {
                            index: index,
                            cellCount: cells.length,
                            cellTexts: Array.from(cells).map(cell => cell.textContent?.trim())
                        };
                    });
                });
                
                console.log('📊 Tabellen nach Klick:', tablesAfterClick);
                results.domAnalysis.push({ type: 'tables_after_click', data: tablesAfterClick });
                
                // Prüfe auf spezifische Konsistenz-Werte
                const consistencyValues = tablesAfterClick.flatMap(row => 
                    row.cellTexts.filter(text => text && text.includes('%'))
                );
                
                if (consistencyValues.length > 0) {
                    console.log('🎯 Konsistenz-Werte gefunden:', consistencyValues);
                    results.criticalFindings.push(`Konsistenz-Werte: ${JSON.stringify(consistencyValues)}`);
                    
                    // Prüfe auf 100% Problem
                    const has100Percent = consistencyValues.some(val => val.includes('100%'));
                    if (has100Percent) {
                        results.criticalFindings.push('⚠️ PROBLEM: 100% Konsistenz-Werte gefunden!');
                    } else {
                        results.criticalFindings.push('✅ Keine 100% Konsistenz-Werte - gut!');
                    }
                } else {
                    results.criticalFindings.push('❌ Keine Konsistenz-Werte in Tabellen gefunden');
                }
                
            } catch (error) {
                console.log('❌ Fehler beim Klicken:', error.message);
                results.criticalFindings.push(`Button-Klick Fehler: ${error.message}`);
            }
        } else {
            console.log('⚠️ Keine Statistiken-Buttons gefunden');
            results.criticalFindings.push('Keine Statistiken-Buttons im DOM gefunden');
        }
        
        // Final Screenshot
        await page.screenshot({ path: '/app/minesearch_v2/frontend/direct_03_final.png' });
        
        console.log('\n✅ Direkte Validierung abgeschlossen!');
        
    } catch (error) {
        console.error('❌ Fehler bei direkter Validierung:', error);
        results.criticalFindings.push(`Kritischer Fehler: ${error.message}`);
    } finally {
        await browser.close();
        
        // Speichere Ergebnisse
        const reportPath = '/app/minesearch_v2/frontend/direct_statistics_validation_report.json';
        fs.writeFileSync(reportPath, JSON.stringify(results, null, 2));
        console.log(`📄 Validierungs-Report gespeichert: ${reportPath}`);
        
        return results;
    }
}

// Führe Validierung aus
directStatisticsValidation()
    .then(results => {
        console.log('\n📊 DIREKTE VALIDIERUNGS-ZUSAMMENFASSUNG:');
        console.log('======================================');
        
        console.log('\n🔗 API-AUFRUFE:');
        results.apiCalls.forEach(call => {
            const status = call.success ? '✅' : '❌';
            console.log(`  ${status} ${call.endpoint}: ${call.status || 'Error'}`);
        });
        
        console.log('\n📡 NETZWERK-REQUESTS:');
        results.networkRequests.forEach(req => {
            console.log(`  ${req.type}: ${req.method || req.status} ${req.url}`);
        });
        
        console.log('\n🎯 KRITISCHE BEFUNDE:');
        results.criticalFindings.forEach(finding => {
            console.log(`  • ${finding}`);
        });
        
        console.log('\n📋 DOM-ANALYSE:');
        const buttons = results.domAnalysis.filter(el => el.type === 'button');
        const tables = results.domAnalysis.filter(el => el.type === 'table');
        console.log(`  • Statistiken-Buttons gefunden: ${buttons.length}`);
        console.log(`  • Tabellen gefunden: ${tables.length}`);
        
        // FINALE BEWERTUNG
        console.log('\n🏆 FINALE BEWERTUNG:');
        const hasApiConnection = results.apiCalls.some(call => call.success);
        const hasButtons = buttons.length > 0;
        const hasTables = tables.length > 0;
        const hasConsistencyData = results.criticalFindings.some(f => f.includes('Konsistenz-Werte:'));
        
        console.log(`  📡 API-Verbindung: ${hasApiConnection ? '✅' : '❌'}`);
        console.log(`  🖱️ Statistiken-Buttons: ${hasButtons ? '✅' : '❌'}`);
        console.log(`  📊 Tabellen vorhanden: ${hasTables ? '✅' : '❌'}`);
        console.log(`  🎯 Konsistenz-Daten: ${hasConsistencyData ? '✅' : '❌'}`);
        
        if (!hasApiConnection) {
            console.log('\n🚨 HAUPTPROBLEM: Backend-API nicht erreichbar!');
        } else if (!hasConsistencyData) {
            console.log('\n🚨 HAUPTPROBLEM: Keine Konsistenz-Daten werden angezeigt!');
        } else {
            console.log('\n✅ System scheint zu funktionieren!');
        }
    })
    .catch(error => {
        console.error('❌ Kritischer Fehler:', error);
    });