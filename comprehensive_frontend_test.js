/*
Author: rahn
Datum: 13.08.2025
Version: 1.0
Beschreibung: Umfassender Frontend-Test für MineSearch 2.0 mit Puppeteer
*/

const puppeteer = require('puppeteer');
const fs = require('fs').promises;
const path = require('path');

class MineSearchFrontendTester {
    constructor() {
        this.browser = null;
        this.page = null;
        this.baseUrl = 'http://localhost:8000';
        this.screenshotDir = '/app/test_screenshots';
        this.testResults = [];
        this.errors = [];
    }

    async init() {
        console.log('🚀 [INIT] Starte Browser für Frontend-Tests...');
        
        // Screenshot-Verzeichnis erstellen
        try {
            await fs.mkdir(this.screenshotDir, { recursive: true });
        } catch (e) {
            console.log('📁 [INFO] Screenshot-Verzeichnis bereits vorhanden');
        }

        // Browser starten
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

        // Console-Logs und Fehler abfangen
        this.page.on('console', msg => {
            const type = msg.type();
            const text = msg.text();
            console.log(`🖥️  [CONSOLE-${type.toUpperCase()}] ${text}`);
            
            if (type === 'error') {
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
            
            // Screenshot bei Fehler
            await this.takeScreenshot(`error_${name.replace(/\s+/g, '_')}`, `Fehler-Screenshot für ${name}`);
        }
    }

    async runAllTests() {
        console.log('🎯 [START] MineSearch 2.0 Frontend-Tests beginnen\n');

        await this.testStep('1. Startseite laden', async () => {
            const response = await this.page.goto(this.baseUrl, { 
                waitUntil: 'domcontentloaded',
                timeout: 30000 
            });
            
            if (!response.ok()) {
                throw new Error(`Server-Antwort: ${response.status()}`);
            }

            // Warten bis wichtige Elemente geladen sind
            await this.page.waitForSelector('body', { timeout: 10000 });
            await this.takeScreenshot('01_startseite_geladen', 'Startseite vollständig geladen');
        });

        await this.testStep('2. Grundlegende UI-Elemente prüfen', async () => {
            // Header prüfen
            await this.page.waitForSelector('h1', { timeout: 5000 });
            const title = await this.page.$eval('h1', el => el.textContent);
            if (!title.includes('MineSearch')) {
                throw new Error(`Unerwarteter Titel: ${title}`);
            }

            // Such-Container prüfen
            await this.page.waitForSelector('#searchContainer', { timeout: 5000 });
            
            // Tab-System prüfen
            const tabs = await this.page.$$('#tabContainer .tab-button');
            if (tabs.length < 3) {
                throw new Error(`Zu wenige Tabs gefunden: ${tabs.length}`);
            }

            await this.takeScreenshot('02_ui_elemente', 'Grundlegende UI-Elemente sichtbar');
        });

        await this.testStep('3. Model-Selection Dropdown testen', async () => {
            await this.page.waitForSelector('#modelSelect', { timeout: 5000 });
            
            // Dropdown öffnen
            await this.page.click('#modelSelect');
            await this.page.waitForTimeout(1000);

            // Optionen prüfen
            const options = await this.page.$$('#modelSelect option');
            if (options.length < 5) {
                throw new Error(`Zu wenige Modell-Optionen: ${options.length}`);
            }

            // Ein Modell auswählen
            await this.page.select('#modelSelect', 'perplexity:sonar');
            await this.page.waitForTimeout(500);

            await this.takeScreenshot('03_model_selection', 'Model-Selection getestet');
        });

        await this.testStep('4. Such-Funktionalität testen', async () => {
            // Suchfeld finden und befüllen
            await this.page.waitForSelector('#searchQuery', { timeout: 5000 });
            await this.page.type('#searchQuery', 'Test-Suche Frontend-Validierung');
            
            // Such-Button klicken
            await this.page.click('#searchBtn');
            
            // Warten auf Suchergebnisse oder Loading-Indikator
            await this.page.waitForTimeout(2000);
            
            // Prüfen ob Search gestartet wurde (Loading-Indikator oder Results)
            const loadingOrResults = await this.page.$('.loading, .search-results, #searchProgress');
            if (!loadingOrResults) {
                throw new Error('Keine Reaktion auf Suchanfrage erkennbar');
            }

            await this.takeScreenshot('04_search_functionality', 'Such-Funktionalität getestet');
        });

        await this.testStep('5. Tab-System testen', async () => {
            // Search Tab
            await this.page.click('#searchTab');
            await this.page.waitForTimeout(500);
            
            let activeTab = await this.page.$eval('#searchTab', el => el.classList.contains('active'));
            if (!activeTab) {
                throw new Error('Search Tab nicht aktiv');
            }

            // Statistics Tab
            await this.page.click('#statisticsTab');
            await this.page.waitForTimeout(1000);
            
            activeTab = await this.page.$eval('#statisticsTab', el => el.classList.contains('active'));
            if (!activeTab) {
                throw new Error('Statistics Tab nicht aktiv');
            }

            // Results Tab
            await this.page.click('#resultsTab');
            await this.page.waitForTimeout(1000);
            
            activeTab = await this.page.$eval('#resultsTab', el => el.classList.contains('active'));
            if (!activeTab) {
                throw new Error('Results Tab nicht aktiv');
            }

            await this.takeScreenshot('05_tab_system', 'Tab-System getestet');
        });

        await this.testStep('6. Data-Cards System prüfen', async () => {
            // Zurück zu Search Tab für Data-Cards
            await this.page.click('#searchTab');
            await this.page.waitForTimeout(1000);

            // Nach Data-Cards suchen
            const dataCards = await this.page.$$('.data-card, .result-card, .model-card');
            console.log(`📊 [DATA-CARDS] ${dataCards.length} Cards gefunden`);

            // Falls Cards vorhanden, Details-Buttons testen
            if (dataCards.length > 0) {
                const detailsButtons = await this.page.$$('.details-btn, .show-details, [onclick*="Details"]');
                console.log(`🔘 [BUTTONS] ${detailsButtons.length} Details-Buttons gefunden`);
                
                if (detailsButtons.length > 0) {
                    // Ersten Details-Button klicken
                    await detailsButtons[0].click();
                    await this.page.waitForTimeout(1000);
                    
                    // Modal oder Details prüfen
                    const modal = await this.page.$('.modal, .details-modal, [class*="modal"]');
                    if (modal) {
                        console.log('✅ [MODAL] Details-Modal erfolgreich geöffnet');
                    }
                }
            }

            await this.takeScreenshot('06_data_cards', 'Data-Cards System getestet');
        });

        await this.testStep('7. JavaScript-Fehler prüfen', async () => {
            // JavaScript-Evaluierung testen
            await this.page.evaluate(() => {
                // Test wichtiger globaler Funktionen/Objekte
                if (typeof window.API_BASE_URL === 'undefined') {
                    throw new Error('API_BASE_URL nicht definiert');
                }
                
                // Test auf wichtige Funktionen
                const requiredFunctions = ['searchModels', 'loadStatistics', 'showTab'];
                for (const func of requiredFunctions) {
                    if (typeof window[func] !== 'function' && typeof window[func] === 'undefined') {
                        console.warn(`Funktion ${func} möglicherweise nicht verfügbar`);
                    }
                }
                
                return true;
            });

            console.log('✅ [JS-CHECK] JavaScript-Environment geprüft');
        });

        await this.testStep('8. Responsive Design testen', async () => {
            // Mobile Viewport
            await this.page.setViewport({ width: 375, height: 667 });
            await this.page.waitForTimeout(1000);
            await this.takeScreenshot('08a_mobile_view', 'Mobile Ansicht');

            // Tablet Viewport
            await this.page.setViewport({ width: 768, height: 1024 });
            await this.page.waitForTimeout(1000);
            await this.takeScreenshot('08b_tablet_view', 'Tablet Ansicht');

            // Desktop zurück
            await this.page.setViewport({ width: 1920, height: 1080 });
            await this.page.waitForTimeout(1000);
            await this.takeScreenshot('08c_desktop_view', 'Desktop Ansicht');
        });
    }

    async generateReport() {
        const report = {
            timestamp: new Date().toISOString(),
            summary: {
                total: this.testResults.length,
                passed: this.testResults.filter(r => r.status === 'PASSED').length,
                failed: this.testResults.filter(r => r.status === 'FAILED').length,
                totalErrors: this.errors.length
            },
            results: this.testResults,
            errors: this.errors,
            screenshots: await fs.readdir(this.screenshotDir).catch(() => [])
        };

        const reportPath = '/app/frontend_test_report.json';
        await fs.writeFile(reportPath, JSON.stringify(report, null, 2));
        
        console.log('\n📋 [REPORT] Test-Zusammenfassung:');
        console.log(`   ✅ Erfolgreich: ${report.summary.passed}`);
        console.log(`   ❌ Fehlgeschlagen: ${report.summary.failed}`);
        console.log(`   🚨 Fehler insgesamt: ${report.summary.totalErrors}`);
        console.log(`   📸 Screenshots: ${report.screenshots.length}`);
        console.log(`   📄 Report gespeichert: ${reportPath}`);

        return report;
    }

    async cleanup() {
        if (this.browser) {
            await this.browser.close();
            console.log('🛑 [CLEANUP] Browser geschlossen');
        }
    }
}

// Test ausführen
async function runTests() {
    const tester = new MineSearchFrontendTester();
    
    try {
        await tester.init();
        await tester.runAllTests();
        const report = await tester.generateReport();
        
        // Exit-Code basierend auf Testergebnissen
        process.exit(report.summary.failed > 0 ? 1 : 0);
        
    } catch (error) {
        console.error('💥 [FATAL] Kritischer Fehler:', error);
        process.exit(1);
    } finally {
        await tester.cleanup();
    }
}

// Nur ausführen wenn direkt aufgerufen
if (require.main === module) {
    runTests();
}

module.exports = MineSearchFrontendTester;