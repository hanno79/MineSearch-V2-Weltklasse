/**
 * Author: rahn
 * Datum: 16.07.2025
 * Version: 1.0
 * Beschreibung: Umfassender Playwright-Test zur Untersuchung der API-Endpoints und Datenbankanzeigeprobleme in MineSearch v2.1
 */

const { test, expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');

// Konfiguration
const BASE_URL = 'http://localhost:8000';
const REPORT_DIR = './test-reports';
const SCREENSHOTS_DIR = './test-screenshots';

// Erstelle Ausgabeverzeichnisse
if (!fs.existsSync(REPORT_DIR)) {
    fs.mkdirSync(REPORT_DIR, { recursive: true });
}
if (!fs.existsSync(SCREENSHOTS_DIR)) {
    fs.mkdirSync(SCREENSHOTS_DIR, { recursive: true });
}

// Test-Daten für verschiedene Szenarien
const testData = {
    searchQueries: [
        { query: 'gold mine canada', location: 'Canada' },
        { query: 'iron ore mine australia', location: 'Australia' },
        { query: 'copper mine chile', location: 'Chile' }
    ],
    apiEndpoints: [
        '/api/sources/grouped',
        '/api/results',
        '/api/benchmark/summary',
        '/api/benchmark/field-statistics',
        '/api/benchmark/field-comparison',
        '/api/models'
    ]
};

let testReport = {
    timestamp: new Date().toISOString(),
    apiEndpoints: {},
    networkRequests: [],
    consoleErrors: [],
    uiInteractions: {},
    screenshots: [],
    summary: {
        workingFeatures: [],
        brokenFeatures: [],
        recommendations: []
    }
};

test.describe('MineSearch v2.1 - Comprehensive API & Database Investigation', () => {
    let page;
    let context;

    test.beforeAll(async ({ browser }) => {
        context = await browser.newContext();
        page = await context.newPage();
        
        // Netzwerk-Requests abfangen und loggen
        page.on('request', request => {
            testReport.networkRequests.push({
                url: request.url(),
                method: request.method(),
                headers: request.headers(),
                timestamp: new Date().toISOString()
            });
        });

        page.on('response', response => {
            const request = testReport.networkRequests.find(req => req.url === response.url());
            if (request) {
                request.status = response.status();
                request.statusText = response.statusText();
                request.responseHeaders = response.headers();
            }
        });

        // Console-Fehler abfangen
        page.on('console', msg => {
            if (msg.type() === 'error' || msg.type() === 'warn') {
                testReport.consoleErrors.push({
                    type: msg.type(),
                    text: msg.text(),
                    timestamp: new Date().toISOString()
                });
            }
        });

        // Unbehandelte Fehler abfangen
        page.on('pageerror', error => {
            testReport.consoleErrors.push({
                type: 'pageerror',
                text: error.message,
                stack: error.stack,
                timestamp: new Date().toISOString()
            });
        });
    });

    test.afterAll(async () => {
        // Finalen Report generieren
        await generateFinalReport();
        await context.close();
    });

    test('1. Direkte API-Endpoint Tests', async () => {
        console.log('🔍 Teste alle API-Endpoints direkt...');
        
        for (const endpoint of testData.apiEndpoints) {
            const endpointData = {
                endpoint: endpoint,
                timestamp: new Date().toISOString(),
                status: null,
                responseTime: null,
                data: null,
                error: null
            };

            try {
                const startTime = Date.now();
                const response = await page.goto(`${BASE_URL}${endpoint}`, { 
                    waitUntil: 'networkidle' 
                });
                const endTime = Date.now();
                
                endpointData.status = response.status();
                endpointData.responseTime = endTime - startTime;
                
                if (response.status() === 200) {
                    const contentType = response.headers()['content-type'];
                    if (contentType && contentType.includes('application/json')) {
                        endpointData.data = await response.json();
                    } else {
                        endpointData.data = await response.text();
                    }
                    testReport.summary.workingFeatures.push(`API Endpoint ${endpoint} - Status: ${response.status()}`);
                } else {
                    endpointData.error = `HTTP ${response.status()} - ${response.statusText()}`;
                    testReport.summary.brokenFeatures.push(`API Endpoint ${endpoint} - Fehler: ${endpointData.error}`);
                }
            } catch (error) {
                endpointData.error = error.message;
                testReport.summary.brokenFeatures.push(`API Endpoint ${endpoint} - Exception: ${error.message}`);
            }

            testReport.apiEndpoints[endpoint] = endpointData;
            
            // Screenshot des API-Responses
            await page.screenshot({
                path: `${SCREENSHOTS_DIR}/api_${endpoint.replace(/\//g, '_')}_response.png`,
                fullPage: true
            });
        }
    });

    test('2. Frontend laden und Netzwerk-Requests überwachen', async () => {
        console.log('🌐 Lade Frontend und überwache Netzwerk-Requests...');
        
        // Lösche bisherige Netzwerk-Requests
        testReport.networkRequests = [];
        
        try {
            await page.goto(BASE_URL, { waitUntil: 'networkidle' });
            
            // Warte auf vollständiges Laden
            await page.waitForTimeout(3000);
            
            // Screenshot der Hauptseite
            await page.screenshot({
                path: `${SCREENSHOTS_DIR}/frontend_main_page.png`,
                fullPage: true
            });
            
            testReport.summary.workingFeatures.push('Frontend lädt erfolgreich');
            
        } catch (error) {
            testReport.summary.brokenFeatures.push(`Frontend Laden - Fehler: ${error.message}`);
        }
        
        // Analysiere abgefangene Netzwerk-Requests
        const apiRequests = testReport.networkRequests.filter(req => req.url.includes('/api/'));
        console.log(`📊 ${apiRequests.length} API-Requests beim Frontend-Load erkannt`);
        
        for (const req of apiRequests) {
            console.log(`  - ${req.method} ${req.url} (Status: ${req.status || 'pending'})`);
        }
    });

    test('3. UI-Interaktionen und Button-Tests', async () => {
        console.log('🖱️ Teste UI-Interaktionen und Button-Funktionalität...');
        
        await page.goto(BASE_URL, { waitUntil: 'networkidle' });
        
        // Test verschiedene Tabs und Bereiche
        const uiElements = [
            { name: 'Main Search Tab', selector: '#main-search-tab' },
            { name: 'Batch Search Tab', selector: '#batch-search-tab' },
            { name: 'Database Tab', selector: '#database-tab' },
            { name: 'Field Statistics Button', selector: 'button[onclick*="showFieldStatistics"]' },
            { name: 'Field Comparison Button', selector: 'button[onclick*="showFieldComparison"]' },
            { name: 'Model Statistics Button', selector: 'button[onclick*="showModelStatistics"]' }
        ];
        
        for (const element of uiElements) {
            try {
                const elementHandle = await page.$(element.selector);
                if (elementHandle) {
                    // Element gefunden
                    testReport.uiInteractions[element.name] = {
                        found: true,
                        visible: await elementHandle.isVisible(),
                        enabled: await elementHandle.isEnabled()
                    };
                    
                    // Versuche zu klicken
                    if (await elementHandle.isVisible() && await elementHandle.isEnabled()) {
                        // Lösche Netzwerk-Request-Log für diese Interaktion
                        const requestsBefore = testReport.networkRequests.length;
                        
                        await elementHandle.click();
                        await page.waitForTimeout(2000); // Warte auf Antwort
                        
                        const requestsAfter = testReport.networkRequests.length;
                        const newRequests = testReport.networkRequests.slice(requestsBefore);
                        
                        testReport.uiInteractions[element.name].clicked = true;
                        testReport.uiInteractions[element.name].networkRequests = newRequests;
                        
                        // Screenshot nach Klick
                        await page.screenshot({
                            path: `${SCREENSHOTS_DIR}/ui_${element.name.replace(/\s+/g, '_')}_clicked.png`,
                            fullPage: true
                        });
                        
                        testReport.summary.workingFeatures.push(`UI Element ${element.name} - Klick erfolgreich`);
                    } else {
                        testReport.summary.brokenFeatures.push(`UI Element ${element.name} - Nicht klickbar`);
                    }
                } else {
                    testReport.uiInteractions[element.name] = { found: false };
                    testReport.summary.brokenFeatures.push(`UI Element ${element.name} - Nicht gefunden`);
                }
            } catch (error) {
                testReport.uiInteractions[element.name] = { 
                    found: false, 
                    error: error.message 
                };
                testReport.summary.brokenFeatures.push(`UI Element ${element.name} - Fehler: ${error.message}`);
            }
        }
    });

    test('4. Datenbankansicht-Tests - Zeros-Problem dokumentieren', async () => {
        console.log('🗄️ Teste Datenbankansichten und dokumentiere Zeros-Problem...');
        
        await page.goto(BASE_URL, { waitUntil: 'networkidle' });
        
        // Gehe zur Datenbank-Registerkarte
        try {
            await page.click('#database-tab');
            await page.waitForTimeout(2000);
            
            // Screenshot der Datenbank-Übersicht
            await page.screenshot({
                path: `${SCREENSHOTS_DIR}/database_overview.png`,
                fullPage: true
            });
            
            // Teste Field Statistics
            try {
                await page.click('button[onclick*="showFieldStatistics"]');
                await page.waitForTimeout(3000);
                
                // Screenshot der Field Statistics
                await page.screenshot({
                    path: `${SCREENSHOTS_DIR}/field_statistics_display.png`,
                    fullPage: true
                });
                
                // Prüfe auf Zeros-Problem
                const fieldStatsContent = await page.$eval('#field-statistics-content', el => el.textContent);
                const hasZerosIssue = fieldStatsContent.includes('0') || fieldStatsContent.includes('No data');
                
                if (hasZerosIssue) {
                    testReport.summary.brokenFeatures.push('Field Statistics zeigt Zeros/No data an');
                } else {
                    testReport.summary.workingFeatures.push('Field Statistics zeigt korrekte Daten an');
                }
                
            } catch (error) {
                testReport.summary.brokenFeatures.push(`Field Statistics - Fehler: ${error.message}`);
            }
            
            // Teste Field Comparison
            try {
                await page.click('button[onclick*="showFieldComparison"]');
                await page.waitForTimeout(3000);
                
                // Screenshot der Field Comparison
                await page.screenshot({
                    path: `${SCREENSHOTS_DIR}/field_comparison_display.png`,
                    fullPage: true
                });
                
                // Prüfe auf Zeros-Problem
                const fieldCompContent = await page.$eval('#field-comparison-content', el => el.textContent);
                const hasZerosIssue = fieldCompContent.includes('0') || fieldCompContent.includes('No data');
                
                if (hasZerosIssue) {
                    testReport.summary.brokenFeatures.push('Field Comparison zeigt Zeros/No data an');
                } else {
                    testReport.summary.workingFeatures.push('Field Comparison zeigt korrekte Daten an');
                }
                
            } catch (error) {
                testReport.summary.brokenFeatures.push(`Field Comparison - Fehler: ${error.message}`);
            }
            
        } catch (error) {
            testReport.summary.brokenFeatures.push(`Datenbank-Tab - Fehler: ${error.message}`);
        }
    });

    test('5. Detaillierte Datenanalyse der API-Responses', async () => {
        console.log('📊 Analysiere API-Response-Daten im Detail...');
        
        // Analysiere Field Statistics API
        const fieldStatsEndpoint = testReport.apiEndpoints['/api/benchmark/field-statistics'];
        if (fieldStatsEndpoint && fieldStatsEndpoint.data) {
            const stats = fieldStatsEndpoint.data;
            
            // Prüfe auf leere oder Zero-Werte
            const hasEmptyData = checkForEmptyData(stats);
            if (hasEmptyData) {
                testReport.summary.brokenFeatures.push('Field Statistics API liefert leere/Zero-Daten');
                testReport.summary.recommendations.push('Überprüfe Datenbankabfragen für Field Statistics');
            } else {
                testReport.summary.workingFeatures.push('Field Statistics API liefert valide Daten');
            }
        }
        
        // Analysiere Field Comparison API
        const fieldCompEndpoint = testReport.apiEndpoints['/api/benchmark/field-comparison'];
        if (fieldCompEndpoint && fieldCompEndpoint.data) {
            const comparison = fieldCompEndpoint.data;
            
            // Prüfe auf leere oder Zero-Werte
            const hasEmptyData = checkForEmptyData(comparison);
            if (hasEmptyData) {
                testReport.summary.brokenFeatures.push('Field Comparison API liefert leere/Zero-Daten');
                testReport.summary.recommendations.push('Überprüfe Datenbankabfragen für Field Comparison');
            } else {
                testReport.summary.workingFeatures.push('Field Comparison API liefert valide Daten');
            }
        }
        
        // Analysiere Sources API
        const sourcesEndpoint = testReport.apiEndpoints['/api/sources/grouped'];
        if (sourcesEndpoint && sourcesEndpoint.data) {
            const sources = sourcesEndpoint.data;
            
            if (Array.isArray(sources) && sources.length > 0) {
                testReport.summary.workingFeatures.push(`Sources API liefert ${sources.length} Quellen`);
            } else {
                testReport.summary.brokenFeatures.push('Sources API liefert keine Quellen');
                testReport.summary.recommendations.push('Überprüfe Quellen-Datenbank und -abfragen');
            }
        }
    });

    test('6. Performance und Ladezeiten', async () => {
        console.log('⚡ Teste Performance und Ladezeiten...');
        
        const performanceMetrics = {
            pageLoadTime: null,
            apiResponseTimes: {},
            largeResponseSizes: []
        };
        
        // Messe Seitenladezeit
        const startTime = Date.now();
        await page.goto(BASE_URL, { waitUntil: 'networkidle' });
        performanceMetrics.pageLoadTime = Date.now() - startTime;
        
        // Analysiere API-Response-Zeiten
        for (const [endpoint, data] of Object.entries(testReport.apiEndpoints)) {
            if (data.responseTime) {
                performanceMetrics.apiResponseTimes[endpoint] = data.responseTime;
                
                if (data.responseTime > 5000) {
                    testReport.summary.brokenFeatures.push(`${endpoint} - Langsame Response-Zeit: ${data.responseTime}ms`);
                    testReport.summary.recommendations.push(`Optimiere ${endpoint} für bessere Performance`);
                }
            }
        }
        
        // Prüfe auf große Response-Größen
        for (const request of testReport.networkRequests) {
            if (request.responseHeaders && request.responseHeaders['content-length']) {
                const size = parseInt(request.responseHeaders['content-length']);
                if (size > 1000000) { // > 1MB
                    performanceMetrics.largeResponseSizes.push({
                        url: request.url,
                        size: size
                    });
                }
            }
        }
        
        testReport.performance = performanceMetrics;
    });
});

// Hilfsfunktionen
function checkForEmptyData(data) {
    if (!data || typeof data !== 'object') return true;
    
    function hasOnlyZerosOrEmpty(obj) {
        for (const key in obj) {
            const value = obj[key];
            if (typeof value === 'object' && value !== null) {
                if (!hasOnlyZerosOrEmpty(value)) return false;
            } else if (typeof value === 'number' && value !== 0) {
                return false;
            } else if (typeof value === 'string' && value.trim() !== '' && value !== '0') {
                return false;
            } else if (Array.isArray(value) && value.length > 0) {
                return false;
            }
        }
        return true;
    }
    
    return hasOnlyZerosOrEmpty(data);
}

async function generateFinalReport() {
    console.log('📋 Generiere finalen Untersuchungsbericht...');
    
    const reportContent = `
# MineSearch v2.1 - Comprehensive API & Database Investigation Report
Generiert am: ${testReport.timestamp}

## 🟢 Funktionierende Features
${testReport.summary.workingFeatures.map(feature => `- ${feature}`).join('\n')}

## 🔴 Defekte Features
${testReport.summary.brokenFeatures.map(feature => `- ${feature}`).join('\n')}

## 💡 Empfehlungen
${testReport.summary.recommendations.map(rec => `- ${rec}`).join('\n')}

## 🔗 API-Endpoint Analyse
${Object.entries(testReport.apiEndpoints).map(([endpoint, data]) => `
### ${endpoint}
- Status: ${data.status || 'N/A'}
- Response-Zeit: ${data.responseTime || 'N/A'}ms
- Fehler: ${data.error || 'Keine'}
- Daten verfügbar: ${data.data ? 'Ja' : 'Nein'}
`).join('\n')}

## 🌐 Netzwerk-Requests (Insgesamt: ${testReport.networkRequests.length})
${testReport.networkRequests.filter(req => req.url.includes('/api/')).map(req => `
- ${req.method} ${req.url} (Status: ${req.status || 'pending'})
`).join('\n')}

## ❌ Console-Fehler (Insgesamt: ${testReport.consoleErrors.length})
${testReport.consoleErrors.map(error => `
- [${error.type}] ${error.text}
`).join('\n')}

## 🖱️ UI-Interaktionen
${Object.entries(testReport.uiInteractions).map(([name, data]) => `
### ${name}
- Gefunden: ${data.found ? 'Ja' : 'Nein'}
- Sichtbar: ${data.visible ? 'Ja' : 'Nein'}
- Aktiviert: ${data.enabled ? 'Ja' : 'Nein'}
- Geklickt: ${data.clicked ? 'Ja' : 'Nein'}
- Netzwerk-Requests: ${data.networkRequests ? data.networkRequests.length : 0}
`).join('\n')}

## 📊 Performance-Metriken
${testReport.performance ? `
- Seitenladezeit: ${testReport.performance.pageLoadTime}ms
- API-Response-Zeiten: ${Object.entries(testReport.performance.apiResponseTimes).map(([endpoint, time]) => `\n  - ${endpoint}: ${time}ms`).join('')}
- Große Responses: ${testReport.performance.largeResponseSizes.length}
` : 'Nicht verfügbar'}

## 🖼️ Screenshots
Alle Screenshots wurden in ./test-screenshots/ gespeichert:
- Frontend-Hauptseite
- API-Response-Ansichten
- UI-Interaktionen
- Datenbankansichten mit Zeros-Problem

## 📋 Zusammenfassung
Das Hauptproblem scheint in der Datenbankabfrage-Logik oder der Datenverarbeitung zu liegen. 
Die API-Endpoints sind erreichbar, aber die zurückgegebenen Daten enthalten möglicherweise 
Null-Werte oder leere Datensätze, die als Zeros in der Frontend-Darstellung erscheinen.

**Nächste Schritte:**
1. Überprüfe die SQL-Abfragen in den Backend-Services
2. Validiere die Datenbank-Inhalte direkt
3. Prüfe die Datenverarbeitungs-Pipeline
4. Teste die Frontend-Datenverarbeitung
`;
    
    fs.writeFileSync(
        path.join(REPORT_DIR, `minesearch_investigation_report_${Date.now()}.md`),
        reportContent
    );
    
    // Zusätzlich JSON-Report für weitere Verarbeitung
    fs.writeFileSync(
        path.join(REPORT_DIR, `minesearch_investigation_data_${Date.now()}.json`),
        JSON.stringify(testReport, null, 2)
    );
    
    console.log('✅ Untersuchungsbericht wurde erstellt');
}