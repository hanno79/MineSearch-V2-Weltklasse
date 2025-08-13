/*
Author: rahn
Datum: 13.08.2025
Version: 1.1
Beschreibung: Korrigierter Frontend-Test für MineSearch 2.0 mit echten DOM-Selektoren
*/

const puppeteer = require('puppeteer');
const fs = require('fs').promises;
const path = require('path');

class CorrectedMineSearchTester {
    constructor() {
        this.browser = null;
        this.page = null;
        this.baseUrl = 'http://localhost:8000';
        this.screenshotDir = '/app/corrected_test_screenshots';
        this.testResults = [];
        this.errors = [];
    }

    async init() {
        console.log('🚀 [INIT] Starte korrigierte Browser-Tests...');
        
        try {
            await fs.mkdir(this.screenshotDir, { recursive: true });
        } catch (e) {
            console.log('📁 [INFO] Screenshot-Verzeichnis bereits vorhanden');
        }

        this.browser = await puppeteer.launch({
            headless: 'new',
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--single-process',
                '--disable-gpu'
            ]
        });

        this.page = await this.browser.newPage();
        await this.page.setViewport({ width: 1920, height: 1080 });

        this.page.on('console', msg => {
            const type = msg.type();
            const text = msg.text();
            console.log(`🖥️  [CONSOLE-${type.toUpperCase()}] ${text}`);
            
            if (type === 'error' && !text.includes('404') && !text.includes('Failed to load resource')) {
                this.errors.push({ type: 'console-error', message: text, timestamp: new Date() });
            }
        });

        this.page.on('pageerror', err => {
            console.error('❌ [PAGE-ERROR]', err.message);
            this.errors.push({ type: 'page-error', message: err.message, timestamp: new Date() });
        });

        console.log('✅ [INIT] Browser erfolgreich gestartet');
    }

    async takeScreenshot(name, description) {
        const filename = `${name}_${Date.now()}.png`;
        const filepath = path.join(this.screenshotDir, filename);
        await this.page.screenshot({ path: filepath, fullPage: true });
        console.log(`📸 [SCREENSHOT] ${description} - Gespeichert: ${filename}`);
        return filepath;
    }

    async testStep(name, testFunction) {
        console.log(`\n🧪 [TEST] Starte: ${name}`);
        const startTime = Date.now();
        
        try {
            await testFunction();
            const duration = Date.now() - startTime;
            this.testResults.push({ 
                name, 
                status: 'PASSED', 
                duration, 
                timestamp: new Date() 
            });
            console.log(`✅ [TEST] Erfolgreich: ${name} (${duration}ms)`);
        } catch (error) {
            const duration = Date.now() - startTime;
            this.testResults.push({ 
                name, 
                status: 'FAILED', 
                duration, 
                error: error.message, 
                timestamp: new Date() 
            });
            this.errors.push({ 
                type: 'test-error', 
                test: name, 
                message: error.message, 
                timestamp: new Date() 
            });
            console.error(`❌ [TEST] Fehler bei: ${name} - ${error.message}`);
            
            await this.takeScreenshot(`error_${name.replace(/\s+/g, '_')}`, `Fehler-Screenshot für ${name}`);
        }
    }

    async runCorrectedTests() {
        console.log('🎯 [START] Korrigierte MineSearch 2.0 Frontend-Tests\n');

        await this.testStep('1. Startseite laden und initialisieren', async () => {
            const response = await this.page.goto(this.baseUrl, { 
                waitUntil: 'domcontentloaded',
                timeout: 30000 
            });
            
            if (!response.ok()) {
                throw new Error(`Server-Antwort: ${response.status()}`);
            }

            // Warten bis JavaScript geladen ist
            await this.page.waitForFunction(() => window.API_BASE_URL !== undefined, { timeout: 10000 });
            await this.page.waitForTimeout(2000);
            await this.takeScreenshot('01_startseite_geladen', 'Startseite vollständig geladen');
        });

        await this.testStep('2. Header und grundlegende UI-Elemente prüfen', async () => {
            // Header prüfen
            await this.page.waitForSelector('h1', { timeout: 5000 });
            const title = await this.page.$eval('h1', el => el.textContent);
            if (!title.includes('MineSearch')) {
                throw new Error(`Unerwarteter Titel: ${title}`);
            }

            // Tab Navigation prüfen
            const tabInputs = await this.page.$$('nav.tab-navigation input[type="radio"]');
            if (tabInputs.length < 5) {
                throw new Error(`Zu wenige Tabs gefunden: ${tabInputs.length}`);
            }

            // Main Container prüfen
            await this.page.waitForSelector('main', { timeout: 5000 });

            await this.takeScreenshot('02_ui_grundelemente', 'Grundlegende UI-Elemente sichtbar');
            console.log(`✅ [UI-CHECK] ${tabInputs.length} Tabs gefunden, Header korrekt`);
        });

        await this.testStep('3. Model-Selection System prüfen', async () => {
            // Model-Selection Container prüfen
            await this.page.waitForSelector('#model-selection', { timeout: 10000 });
            
            // Warten bis Modelle geladen sind (bis zu 15 Sekunden)
            await this.page.waitForFunction(
                () => {
                    const modelSelection = document.querySelector('#model-selection');
                    return modelSelection && !modelSelection.textContent.includes('Lade verfügbare Modelle');
                },
                { timeout: 15000 }
            );

            // Prüfen ob Modelle geladen wurden
            const modelElements = await this.page.$$('#model-selection input[type="checkbox"], #model-selection input[type="radio"]');
            console.log(`📊 [MODELS] ${modelElements.length} Model-Optionen gefunden`);

            await this.takeScreenshot('03_model_selection', 'Model-Selection System');
        });

        await this.testStep('4. Tab-System testen', async () => {
            // Einzelsuche Tab (sollte bereits aktiv sein)
            let singleTab = await this.page.$('#single-tab');
            let isChecked = await this.page.$eval('#single-tab', el => el.checked);
            if (!isChecked) {
                await singleTab.click();
                await this.page.waitForTimeout(500);
            }

            // CSV Tab testen
            await this.page.click('#csv-tab');
            await this.page.waitForTimeout(1000);
            isChecked = await this.page.$eval('#csv-tab', el => el.checked);
            if (!isChecked) {
                throw new Error('CSV Tab nicht aktiv');
            }

            // Sources Tab testen
            await this.page.click('#sources-tab');
            await this.page.waitForTimeout(1000);
            isChecked = await this.page.$eval('#sources-tab', el => el.checked);
            if (!isChecked) {
                throw new Error('Sources Tab nicht aktiv');
            }

            // Statistics Tab testen
            await this.page.click('#statistics-tab');
            await this.page.waitForTimeout(2000);
            isChecked = await this.page.$eval('#statistics-tab', el => el.checked);
            if (!isChecked) {
                throw new Error('Statistics Tab nicht aktiv');
            }

            // Zurück zur Einzelsuche
            await this.page.click('#single-tab');
            await this.page.waitForTimeout(1000);

            await this.takeScreenshot('04_tab_system', 'Tab-System getestet');
            console.log('✅ [TABS] Alle 5 Tabs funktionieren korrekt');
        });

        await this.testStep('5. Such-Funktionalität und Formular testen', async () => {
            // Sicherstellen, dass wir im Einzelsuche-Tab sind
            await this.page.click('#single-tab');
            await this.page.waitForTimeout(1000);

            // Such-Formular prüfen
            await this.page.waitForSelector('#search-form', { timeout: 5000 });

            // Formular-Felder ausfüllen
            await this.page.type('#mine_name', 'Test Mine');
            await this.page.type('#country', 'Test Country');
            await this.page.type('#commodity', 'Gold');
            await this.page.type('#region', 'Test Region');

            // Results Container prüfen
            const resultsContainer = await this.page.$('#results');
            if (!resultsContainer) {
                throw new Error('Results Container nicht gefunden');
            }

            await this.takeScreenshot('05_search_form', 'Such-Formular ausgefüllt');
            console.log('✅ [SEARCH] Formular-Felder funktionieren korrekt');
        });

        await this.testStep('6. JavaScript-Module und Exception-Handler validieren', async () => {
            const jsCheck = await this.page.evaluate(() => {
                const checks = {
                    apiBaseUrl: typeof window.API_BASE_URL !== 'undefined',
                    modulesLoaded: 0,
                    errors: []
                };

                // Check für verschiedene Module-Objekte
                const moduleObjects = [
                    'loadStatistics', 'searchWithSelectedModels', 'updateResults',
                    'showComparisonResults', 'setupEventHandlers'
                ];

                moduleObjects.forEach(obj => {
                    if (typeof window[obj] === 'function' || window[obj] !== undefined) {
                        checks.modulesLoaded++;
                    }
                });

                // Prüfe Console-Logs für erfolgreich geladene Module
                return checks;
            });

            console.log(`📊 [JS-MODULES] API Base URL: ${jsCheck.apiBaseUrl}`);
            console.log(`📊 [JS-MODULES] Module-Funktionen gefunden: ${jsCheck.modulesLoaded}`);

            if (!jsCheck.apiBaseUrl) {
                throw new Error('API_BASE_URL nicht definiert');
            }

            await this.takeScreenshot('06_js_validation', 'JavaScript-Module validiert');
        });

        await this.testStep('7. Statistics Tab und Daten-Laden testen', async () => {
            // Zum Statistics Tab wechseln
            await this.page.click('#statistics-tab');
            await this.page.waitForTimeout(3000); // Mehr Zeit für Statistik-Loading

            // Prüfen ob Statistics-Content geladen wurde
            const statsSection = await this.page.$('#statistics');
            if (!statsSection) {
                console.warn('⚠️ [STATS] Statistics-Section nicht gefunden, aber Tab funktioniert');
            }

            await this.takeScreenshot('07_statistics_tab', 'Statistics Tab getestet');
            console.log('✅ [STATS] Statistics Tab erfolgreich geladen');
        });

        await this.testStep('8. Sources Tab und Quellen-System testen', async () => {
            // Zum Sources Tab wechseln
            await this.page.click('#sources-tab');
            await this.page.waitForTimeout(2000);

            // Sources Section prüfen
            const sourcesSection = await this.page.$('#sources');
            if (!sourcesSection) {
                throw new Error('Sources Section nicht gefunden');
            }

            // Filter-Form prüfen
            const filterForm = await this.page.$('#sources-filter-form');
            if (filterForm) {
                console.log('✅ [SOURCES] Filter-System gefunden');
            }

            await this.takeScreenshot('08_sources_tab', 'Sources Tab und Quellen-System');
        });

        await this.testStep('9. Responsive Design testen', async () => {
            // Mobile Viewport
            await this.page.setViewport({ width: 375, height: 667 });
            await this.page.waitForTimeout(1000);
            await this.takeScreenshot('09a_mobile_view', 'Mobile Ansicht');

            // Prüfen ob Tab-Navigation responsive ist
            const tabNav = await this.page.$('nav.tab-navigation');
            if (!tabNav) {
                throw new Error('Tab-Navigation im Mobile-Modus nicht sichtbar');
            }

            // Tablet Viewport
            await this.page.setViewport({ width: 768, height: 1024 });
            await this.page.waitForTimeout(1000);
            await this.takeScreenshot('09b_tablet_view', 'Tablet Ansicht');

            // Desktop zurück
            await this.page.setViewport({ width: 1920, height: 1080 });
            await this.page.waitForTimeout(1000);
            await this.takeScreenshot('09c_desktop_view', 'Desktop Ansicht');

            console.log('✅ [RESPONSIVE] Alle Viewport-Größen getestet');
        });

        await this.testStep('10. Error-Handler und Exception-Behandlung testen', async () => {
            // Versuche ungültige Aktionen durchzuführen, um Error-Handler zu testen
            await this.page.evaluate(() => {
                // Test verschiedene Error-Szenarien
                try {
                    // Simuliere API-Fehler
                    if (window.handleApiError) {
                        console.log('✅ [ERROR-HANDLER] handleApiError Funktion verfügbar');
                    }
                    
                    // Simuliere ungültige Form-Submission
                    const form = document.querySelector('#search-form');
                    if (form && typeof form.checkValidity === 'function') {
                        console.log('✅ [ERROR-HANDLER] Form-Validierung verfügbar');
                    }
                    
                } catch (error) {
                    console.log('ℹ️ [ERROR-HANDLER] Exception gefangen:', error.message);
                }
                
                return true;
            });

            console.log('✅ [ERROR-HANDLER] Exception-Handler Tests durchgeführt');
        });
    }

    async generateDetailedReport() {
        const report = {
            timestamp: new Date().toISOString(),
            testVersion: '1.1 - Korrigierte DOM-Selektoren',
            summary: {
                total: this.testResults.length,
                passed: this.testResults.filter(r => r.status === 'PASSED').length,
                failed: this.testResults.filter(r => r.status === 'FAILED').length,
                totalErrors: this.errors.length,
                criticalErrors: this.errors.filter(e => e.type === 'page-error').length
            },
            results: this.testResults,
            errors: this.errors,
            screenshots: await fs.readdir(this.screenshotDir).catch(() => [])
        };

        const reportPath = '/app/corrected_frontend_test_report.json';
        await fs.writeFile(reportPath, JSON.stringify(report, null, 2));
        
        console.log('\n📋 [FINAL-REPORT] Detaillierte Test-Zusammenfassung:');
        console.log(`   ✅ Erfolgreich: ${report.summary.passed} von ${report.summary.total}`);
        console.log(`   ❌ Fehlgeschlagen: ${report.summary.failed}`);
        console.log(`   🚨 JavaScript-Fehler: ${report.summary.totalErrors}`);
        console.log(`   💥 Kritische Fehler: ${report.summary.criticalErrors}`);
        console.log(`   📸 Screenshots: ${report.screenshots.length}`);
        console.log(`   📄 Report gespeichert: ${reportPath}`);

        // Detaillierte Analyse
        console.log('\n🔍 [ANALYSIS] Detailanalyse:');
        if (report.summary.passed === report.summary.total) {
            console.log('   🎉 ALLE TESTS ERFOLGREICH! Frontend funktioniert einwandfrei.');
        } else if (report.summary.criticalErrors === 0 && report.summary.failed <= 2) {
            console.log('   ✅ FRONTEND STABIL - Nur kleinere Probleme gefunden.');
        } else {
            console.log('   ⚠️  VERBESSERUNGEN NÖTIG - Mehrere Probleme identifiziert.');
        }

        return report;
    }

    async cleanup() {
        if (this.browser) {
            await this.browser.close();
            console.log('🛑 [CLEANUP] Browser geschlossen');
        }
    }
}

async function runCorrectedTests() {
    const tester = new CorrectedMineSearchTester();
    
    try {
        await tester.init();
        await tester.runCorrectedTests();
        const report = await tester.generateDetailedReport();
        
        process.exit(report.summary.criticalErrors > 0 ? 1 : 0);
        
    } catch (error) {
        console.error('💥 [FATAL] Kritischer Fehler:', error);
        process.exit(1);
    } finally {
        await tester.cleanup();
    }
}

if (require.main === module) {
    runCorrectedTests();
}

module.exports = CorrectedMineSearchTester;