/**
 * Author: rahn
 * Datum: 07.08.2025
 * Version: 1.0
 * Beschreibung: Vollständiger End-to-End Browser-Test für MineSearch System
 */

const { chromium } = require('playwright');
const path = require('path');

class MineSearchE2ETest {
    constructor() {
        this.browser = null;
        this.page = null;
        this.testResults = {
            browserStart: false,
            csvUpload: false,
            batchSearch: false,
            searchCompletion: false,
            resultsValidation: false,
            tabsValidation: false,
            screenshots: []
        };
    }

    async setup() {
        console.log('🚀 Starting MineSearch E2E Test...');
        this.browser = await chromium.launch({ 
            headless: false,
            slowMo: 1000 // Langsamer für bessere Sichtbarkeit
        });
        this.page = await this.browser.newPage();
        
        // Viewport setzen
        await this.page.setViewportSize({ width: 1280, height: 720 });
        
        // Console Logs abfangen
        this.page.on('console', msg => {
            console.log(`📄 Console: ${msg.type()}: ${msg.text()}`);
        });
        
        // Fehler abfangen
        this.page.on('pageerror', error => {
            console.error(`❌ Page Error: ${error.message}`);
        });
    }

    async takeScreenshot(stepName, description = '') {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '_');
        const filename = `step_${stepName}_${timestamp}.png`;
        const fullPath = path.join(__dirname, 'screenshots', filename);
        
        await this.page.screenshot({ 
            path: fullPath, 
            fullPage: true 
        });
        
        this.testResults.screenshots.push({
            step: stepName,
            description: description,
            filename: filename,
            timestamp: timestamp
        });
        
        console.log(`📸 Screenshot: ${filename} - ${description}`);
    }

    async step1_browserStart() {
        console.log('\n📡 SCHRITT 1: Browser-Start und Seitenladevorgang');
        
        try {
            await this.page.goto('http://localhost:8000', { 
                waitUntil: 'networkidle', 
                timeout: 30000 
            });
            
            // Warten auf Seiteninhalt
            await this.page.waitForSelector('h1', { timeout: 15000 });
            await this.takeScreenshot('01_browser_start', 'Initial page load');
            
            // Validierung der Grundstruktur
            const title = await this.page.textContent('h1');
            console.log(`✅ Page title: ${title}`);
            
            // Überprüfung der wichtigsten Elemente
            const tabsExist = await this.page.locator('.tab-nav').count() > 0;
            const uploadFormExists = await this.page.locator('form').count() > 0;
            
            console.log(`✅ Tabs found: ${tabsExist}`);
            console.log(`✅ Upload form found: ${uploadFormExists}`);
            
            this.testResults.browserStart = true;
            return true;
            
        } catch (error) {
            console.error(`❌ Browser start failed: ${error.message}`);
            await this.takeScreenshot('01_browser_start_error', 'Browser start error');
            return false;
        }
    }

    async step2_csvUpload() {
        console.log('\n📄 SCHRITT 2: CSV-Upload');
        
        try {
            // Sicherstellen dass wir im CSV Tab sind
            const csvTab = this.page.locator('button[data-tab="csv"]');
            if (await csvTab.count() > 0) {
                await csvTab.click();
                await this.page.waitForTimeout(1000);
            }
            
            await this.takeScreenshot('02_before_upload', 'Before CSV upload');
            
            // File Input finden und Datei hochladen
            const fileInput = this.page.locator('input[type="file"]');
            await fileInput.setInputFiles('/app/test_mines.csv');
            
            // Warten auf Upload-Verarbeitung
            await this.page.waitForTimeout(2000);
            
            // Upload Button klicken falls vorhanden
            const uploadButton = this.page.locator('button:has-text("Upload")');
            if (await uploadButton.count() > 0) {
                await uploadButton.click();
                await this.page.waitForTimeout(3000);
            }
            
            await this.takeScreenshot('02_after_upload', 'After CSV upload');
            
            // Validierung des Uploads
            const uploadSuccess = await this.page.locator('.csv-preview, .upload-success, table').count() > 0;
            console.log(`✅ CSV Upload successful: ${uploadSuccess}`);
            
            this.testResults.csvUpload = uploadSuccess;
            return uploadSuccess;
            
        } catch (error) {
            console.error(`❌ CSV upload failed: ${error.message}`);
            await this.takeScreenshot('02_upload_error', 'CSV upload error');
            return false;
        }
    }

    async step3_batchSearch() {
        console.log('\n🔍 SCHRITT 3: Batch-Suche starten');
        
        try {
            // Zu Models Tab wechseln falls nötig
            const modelsTab = this.page.locator('button[data-tab="models"]');
            if (await modelsTab.count() > 0) {
                await modelsTab.click();
                await this.page.waitForTimeout(2000);
            }
            
            await this.takeScreenshot('03_models_tab', 'Models tab opened');
            
            // Warten auf Modelle zu laden
            await this.page.waitForTimeout(5000);
            
            // Kostenlose Modelle auswählen (DeepSeek, etc.)
            const modelCheckboxes = this.page.locator('input[type="checkbox"]');
            const modelCount = await modelCheckboxes.count();
            
            console.log(`📋 Found ${modelCount} model checkboxes`);
            
            // Erste 2-3 Modelle auswählen (kostenlose bevorzugen)
            let selectedCount = 0;
            for (let i = 0; i < Math.min(modelCount, 3); i++) {
                const checkbox = modelCheckboxes.nth(i);
                const isChecked = await checkbox.isChecked();
                
                if (!isChecked) {
                    await checkbox.check();
                    selectedCount++;
                    await this.page.waitForTimeout(500);
                }
            }
            
            console.log(`✅ Selected ${selectedCount} models`);
            await this.takeScreenshot('03_models_selected', `${selectedCount} models selected`);
            
            // Batch Search Button finden und klicken
            const batchSearchButton = this.page.locator('button:has-text("Batch Search"), button:has-text("Start Search"), button[id*="search"]');
            
            if (await batchSearchButton.count() > 0) {
                await batchSearchButton.first().click();
                console.log('🚀 Batch search started');
                await this.takeScreenshot('03_search_started', 'Batch search initiated');
                
                this.testResults.batchSearch = true;
                return true;
            } else {
                console.error('❌ Batch search button not found');
                await this.takeScreenshot('03_no_search_button', 'No search button found');
                return false;
            }
            
        } catch (error) {
            console.error(`❌ Batch search failed: ${error.message}`);
            await this.takeScreenshot('03_search_error', 'Batch search error');
            return false;
        }
    }

    async step4_waitForCompletion() {
        console.log('\n⏳ SCHRITT 4: Warten auf Suchabschluss (60-120 Sekunden)');
        
        const maxWaitTime = 120000; // 2 Minuten
        const checkInterval = 10000; // 10 Sekunden
        const startTime = Date.now();
        
        while (Date.now() - startTime < maxWaitTime) {
            try {
                // Screenshot für Fortschritt
                const elapsed = Math.floor((Date.now() - startTime) / 1000);
                await this.takeScreenshot('04_progress', `Search progress after ${elapsed}s`);
                
                // Überprüfung auf Fertigstellung
                const completionIndicators = [
                    '.search-complete',
                    '.results-ready', 
                    'text=Search completed',
                    'text=Results available',
                    '.progress[value="100"]',
                    'table tbody tr' // Ergebnisse in Tabelle
                ];
                
                let isComplete = false;
                for (const indicator of completionIndicators) {
                    if (await this.page.locator(indicator).count() > 0) {
                        console.log(`✅ Completion detected: ${indicator}`);
                        isComplete = true;
                        break;
                    }
                }
                
                // Auch auf Error-Zustände prüfen
                const errorIndicators = [
                    '.error',
                    'text=Error',
                    'text=Failed'
                ];
                
                for (const error of errorIndicators) {
                    if (await this.page.locator(error).count() > 0) {
                        console.log(`⚠️  Error detected: ${error}`);
                        break;
                    }
                }
                
                if (isComplete) {
                    console.log('🎉 Search completion detected!');
                    await this.takeScreenshot('04_completion', 'Search completed');
                    this.testResults.searchCompletion = true;
                    return true;
                }
                
                console.log(`⏳ Still waiting... (${elapsed}s/${maxWaitTime/1000}s)`);
                await this.page.waitForTimeout(checkInterval);
                
            } catch (error) {
                console.error(`❌ Error during wait: ${error.message}`);
            }
        }
        
        console.log('⏰ Timeout reached - proceeding with results check');
        await this.takeScreenshot('04_timeout', 'Timeout reached');
        return true; // Weiter machen auch bei Timeout
    }

    async step5_validateResults() {
        console.log('\n📊 SCHRITT 5: Ergebnisse validieren');
        
        try {
            // Zu Results/CSV Tab wechseln
            const resultsTab = this.page.locator('button[data-tab="csv"], button[data-tab="results"]');
            if (await resultsTab.count() > 0) {
                await resultsTab.first().click();
                await this.page.waitForTimeout(2000);
            }
            
            await this.takeScreenshot('05_results_tab', 'Results tab opened');
            
            // Ergebnisse prüfen
            const resultsValidation = {
                tableExists: await this.page.locator('table').count() > 0,
                hasRows: await this.page.locator('table tbody tr').count() > 0,
                hasData: await this.page.locator('table td').count() > 0
            };
            
            console.log('📋 Results validation:');
            console.log(`  - Table exists: ${resultsValidation.tableExists}`);
            console.log(`  - Has rows: ${resultsValidation.hasRows}`);
            console.log(`  - Has data: ${resultsValidation.hasData}`);
            
            // Beispiel-Daten extrahieren
            if (resultsValidation.hasData) {
                const sampleData = await this.page.locator('table tbody tr').first().textContent();
                console.log(`  - Sample row: ${sampleData?.substring(0, 100)}...`);
            }
            
            this.testResults.resultsValidation = resultsValidation.tableExists && resultsValidation.hasRows;
            return this.testResults.resultsValidation;
            
        } catch (error) {
            console.error(`❌ Results validation failed: ${error.message}`);
            await this.takeScreenshot('05_validation_error', 'Results validation error');
            return false;
        }
    }

    async step6_validateTabs() {
        console.log('\n📑 SCHRITT 6: Alle Tabs validieren');
        
        const tabsToTest = [
            { selector: 'button[data-tab="csv"]', name: 'CSV Results' },
            { selector: 'button[data-tab="statistics"]', name: 'Statistics' },
            { selector: 'button[data-tab="sources"]', name: 'Sources' }
        ];
        
        let tabsWorking = 0;
        
        for (const tab of tabsToTest) {
            try {
                console.log(`🔍 Testing tab: ${tab.name}`);
                
                const tabButton = this.page.locator(tab.selector);
                if (await tabButton.count() > 0) {
                    await tabButton.click();
                    await this.page.waitForTimeout(2000);
                    
                    await this.takeScreenshot(`06_tab_${tab.name.toLowerCase()}`, `${tab.name} tab content`);
                    
                    // Content validation
                    const hasContent = await this.page.locator('table, .content, .statistics, .sources').count() > 0;
                    
                    console.log(`  ✅ ${tab.name}: ${hasContent ? 'Has content' : 'No content'}`);
                    
                    if (hasContent) tabsWorking++;
                    
                } else {
                    console.log(`  ⚠️  ${tab.name}: Tab not found`);
                }
                
            } catch (error) {
                console.error(`❌ Tab ${tab.name} failed: ${error.message}`);
            }
        }
        
        this.testResults.tabsValidation = tabsWorking >= 2; // Mindestens 2 Tabs funktionsfähig
        console.log(`📊 Tabs validation: ${tabsWorking}/${tabsToTest.length} tabs working`);
        
        return this.testResults.tabsValidation;
    }

    async generateReport() {
        console.log('\n📋 GENERATING FINAL REPORT');
        console.log('═'.repeat(60));
        
        const report = {
            timestamp: new Date().toISOString(),
            testDuration: 'N/A',
            results: this.testResults,
            summary: {
                totalSteps: 6,
                passedSteps: 0,
                failedSteps: 0,
                overallSuccess: false
            }
        };
        
        // Schritt-Erfolg zählen
        const stepResults = [
            this.testResults.browserStart,
            this.testResults.csvUpload,
            this.testResults.batchSearch,
            this.testResults.searchCompletion,
            this.testResults.resultsValidation,
            this.testResults.tabsValidation
        ];
        
        report.summary.passedSteps = stepResults.filter(result => result === true).length;
        report.summary.failedSteps = report.summary.totalSteps - report.summary.passedSteps;
        report.summary.overallSuccess = report.summary.passedSteps >= 4; // Mindestens 4 von 6 Schritten
        
        console.log(`🎯 TEST SUMMARY:`);
        console.log(`   Total Steps: ${report.summary.totalSteps}`);
        console.log(`   Passed: ${report.summary.passedSteps}`);
        console.log(`   Failed: ${report.summary.failedSteps}`);
        console.log(`   Overall Success: ${report.summary.overallSuccess ? '✅ PASS' : '❌ FAIL'}`);
        console.log('');
        
        console.log(`📊 DETAILED RESULTS:`);
        console.log(`   1. Browser Start: ${this.testResults.browserStart ? '✅' : '❌'}`);
        console.log(`   2. CSV Upload: ${this.testResults.csvUpload ? '✅' : '❌'}`);
        console.log(`   3. Batch Search: ${this.testResults.batchSearch ? '✅' : '❌'}`);
        console.log(`   4. Search Completion: ${this.testResults.searchCompletion ? '✅' : '❌'}`);
        console.log(`   5. Results Validation: ${this.testResults.resultsValidation ? '✅' : '❌'}`);
        console.log(`   6. Tabs Validation: ${this.testResults.tabsValidation ? '✅' : '❌'}`);
        console.log('');
        
        console.log(`📸 SCREENSHOTS: ${this.testResults.screenshots.length} captured`);
        this.testResults.screenshots.forEach((screenshot, index) => {
            console.log(`   ${index + 1}. ${screenshot.step}: ${screenshot.description}`);
        });
        
        // Report als JSON speichern
        const reportPath = path.join(__dirname, 'e2e_test_report.json');
        require('fs').writeFileSync(reportPath, JSON.stringify(report, null, 2));
        console.log(`💾 Report saved to: ${reportPath}`);
        
        return report;
    }

    async cleanup() {
        if (this.browser) {
            await this.browser.close();
            console.log('🧹 Browser closed');
        }
    }

    async run() {
        const startTime = Date.now();
        
        try {
            await this.setup();
            
            // Alle Testschritte ausführen
            await this.step1_browserStart();
            await this.step2_csvUpload();
            await this.step3_batchSearch();
            await this.step4_waitForCompletion();
            await this.step5_validateResults();
            await this.step6_validateTabs();
            
        } catch (error) {
            console.error(`💥 Test execution failed: ${error.message}`);
            await this.takeScreenshot('error', 'Test execution error');
        } finally {
            const report = await this.generateReport();
            await this.cleanup();
            
            const duration = Math.floor((Date.now() - startTime) / 1000);
            console.log(`⏱️  Total test duration: ${duration} seconds`);
            
            return report;
        }
    }
}

// Test ausführen wenn direkt aufgerufen
if (require.main === module) {
    (async () => {
        const test = new MineSearchE2ETest();
        await test.run();
    })();
}

module.exports = MineSearchE2ETest;