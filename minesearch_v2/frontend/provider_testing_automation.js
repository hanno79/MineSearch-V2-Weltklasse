/**
 * Author: rahn
 * Datum: 27.07.2025
 * Version: 1.0
 * Beschreibung: Automatisierte Provider-Testing für Details-Button-Probleme
 */

const { chromium } = require('playwright');

class ModelProviderTester {
    constructor() {
        this.browser = null;
        this.page = null;
        this.problematicProviders = [];
        this.successfulProviders = [];
        this.errorPatterns = new Map();
    }

    async init() {
        console.log('🔧 Initialisiere Browser für Provider-Tests...');
        this.browser = await chromium.launch({ 
            headless: false,
            devtools: true
        });
        this.page = await this.browser.newPage();
        
        // Console-Logs überwachen
        this.page.on('console', msg => {
            const text = msg.text();
            if (text.includes('SyntaxError') || text.includes('missing )')) {
                console.log(`🚨 JavaScript Error detected: ${text}`);
                this.recordError(text);
            }
        });

        // JavaScript-Fehler abfangen
        this.page.on('pageerror', error => {
            console.log(`🚨 Page Error: ${error.message}`);
            this.recordError(error.message);
        });

        await this.page.goto('http://localhost:8082');
        console.log('✅ Browser initialisiert');
    }

    recordError(errorText) {
        // Extrahiere Model-ID aus Fehlermeldung falls möglich
        const modelMatch = errorText.match(/showModelDetails\('([^']+)'\)/);
        if (modelMatch) {
            const modelId = modelMatch[1];
            if (!this.errorPatterns.has(modelId)) {
                this.errorPatterns.set(modelId, []);
            }
            this.errorPatterns.get(modelId).push(errorText);
            this.problematicProviders.push(modelId);
        }
    }

    async waitForStatisticsTab() {
        console.log('⏳ Warte auf Statistics-Tab...');
        try {
            await this.page.waitForSelector('#statisticsTab', { timeout: 10000 });
            await this.page.click('#statisticsTab');
            await this.page.waitForTimeout(2000);
            console.log('✅ Statistics-Tab aktiv');
            return true;
        } catch (error) {
            console.log(`❌ Statistics-Tab nicht gefunden: ${error.message}`);
            return false;
        }
    }

    async getAllModelButtons() {
        console.log('🔍 Suche alle Model-Details-Buttons...');
        
        // Warte auf Statistik-Inhalte
        await this.page.waitForSelector('.statistics-content', { timeout: 5000 });
        
        // Finde alle Details-Buttons
        const buttons = await this.page.$$('button[onclick*="showModelDetails"]');
        console.log(`✅ ${buttons.length} Details-Buttons gefunden`);
        
        const modelData = [];
        for (const button of buttons) {
            try {
                const onclick = await button.getAttribute('onclick');
                const modelMatch = onclick.match(/showModelDetails\('([^']+)'\)/);
                if (modelMatch) {
                    const modelId = modelMatch[1];
                    modelData.push({
                        element: button,
                        modelId: modelId,
                        onclick: onclick
                    });
                }
            } catch (error) {
                console.log(`⚠️ Fehler beim Analysieren Button: ${error.message}`);
            }
        }
        
        return modelData;
    }

    async testModelButton(modelData) {
        const { modelId, element, onclick } = modelData;
        console.log(`\n🧪 Teste Model: ${modelId}`);
        console.log(`📋 OnClick: ${onclick}`);

        try {
            // Scrolle Button in Sicht
            await element.scrollIntoViewIfNeeded();
            await this.page.waitForTimeout(500);

            // Markiere aktuellen Fehlerstand
            const errorsBefore = this.errorPatterns.size;

            // Klicke Button
            await element.click();
            
            // Warte kurz für JavaScript-Ausführung
            await this.page.waitForTimeout(2000);

            // Prüfe auf neue Fehler
            const errorsAfter = this.errorPatterns.size;
            
            if (errorsAfter > errorsBefore) {
                console.log(`❌ ${modelId}: JavaScript-Fehler detectiert`);
                return false;
            }

            // Prüfe ob Accordion geöffnet wurde
            const accordionExists = await this.page.$(`#model-details-${modelId.replace(/[^a-zA-Z0-9]/g, '-')}`);
            if (accordionExists) {
                console.log(`✅ ${modelId}: Accordion erfolgreich geöffnet`);
                this.successfulProviders.push(modelId);
                return true;
            } else {
                console.log(`⚠️ ${modelId}: Kein Accordion gefunden, aber auch kein JS-Fehler`);
                return false;
            }

        } catch (error) {
            console.log(`❌ ${modelId}: Test-Fehler - ${error.message}`);
            this.problematicProviders.push(modelId);
            return false;
        }
    }

    async testSpecificProviders() {
        console.log('\n🎯 Teste spezifische problematische Provider...');
        
        const testCases = [
            'grok:grok-3-mini',
            'grok:grok-2',
            'openai:gpt-3.5-turbo',
            'openai:gpt-4',
            'anthropic:claude-sonnet-4',
            'gemini:gemini-2.5-pro'
        ];

        for (const modelId of testCases) {
            console.log(`\n🔬 Direct-Test: ${modelId}`);
            
            try {
                // Direkte JavaScript-Ausführung
                const result = await this.page.evaluate((id) => {
                    try {
                        if (typeof window.showModelDetails === 'function') {
                            window.showModelDetails(id);
                            return { success: true, error: null };
                        } else {
                            return { success: false, error: 'Function not defined' };
                        }
                    } catch (e) {
                        return { success: false, error: e.message };
                    }
                }, modelId);

                if (result.success) {
                    console.log(`✅ ${modelId}: Direct call successful`);
                } else {
                    console.log(`❌ ${modelId}: Direct call failed - ${result.error}`);
                    this.problematicProviders.push(modelId);
                }
                
                await this.page.waitForTimeout(1000);

            } catch (error) {
                console.log(`❌ ${modelId}: Direct test error - ${error.message}`);
                this.problematicProviders.push(modelId);
            }
        }
    }

    async analyzeOnClickPatterns() {
        console.log('\n🔍 Analysiere OnClick-Pattern...');
        
        const modelButtons = await this.getAllModelButtons();
        const patterns = new Map();
        
        for (const { modelId, onclick } of modelButtons) {
            // Extrahiere Pattern
            const quotingStyle = onclick.includes('"') ? 'double' : 'single';
            const hasSpecialChars = /[:\-\.]/.test(modelId);
            const hasNumbers = /\d/.test(modelId);
            
            const pattern = `${quotingStyle}_quotes_special:${hasSpecialChars}_numbers:${hasNumbers}`;
            
            if (!patterns.has(pattern)) {
                patterns.set(pattern, []);
            }
            patterns.get(pattern).push({ modelId, onclick });
        }

        console.log('\n📊 OnClick-Pattern-Analyse:');
        for (const [pattern, models] of patterns) {
            console.log(`\n${pattern}: ${models.length} Modelle`);
            models.slice(0, 3).forEach(({ modelId, onclick }) => {
                console.log(`  - ${modelId}: ${onclick}`);
            });
            if (models.length > 3) {
                console.log(`  ... und ${models.length - 3} weitere`);
            }
        }

        return patterns;
    }

    async generateReport() {
        console.log('\n📋 Generiere umfassenden Test-Report...');
        
        const report = {
            summary: {
                totalTested: this.successfulProviders.length + this.problematicProviders.length,
                successful: this.successfulProviders.length,
                problematic: this.problematicProviders.length,
                errorPatterns: this.errorPatterns.size
            },
            successful: this.successfulProviders,
            problematic: [...new Set(this.problematicProviders)], // Remove duplicates
            errorDetails: Object.fromEntries(this.errorPatterns),
            recommendations: []
        };

        // Analyse der Fehler-Pattern
        if (this.errorPatterns.size > 0) {
            const commonErrors = {};
            for (const [modelId, errors] of this.errorPatterns) {
                errors.forEach(error => {
                    if (!commonErrors[error]) commonErrors[error] = [];
                    commonErrors[error].push(modelId);
                });
            }

            report.commonErrorPatterns = commonErrors;
            
            // Generiere Empfehlungen
            for (const [error, models] of Object.entries(commonErrors)) {
                if (error.includes('missing )')) {
                    report.recommendations.push({
                        issue: 'Missing parenthesis in function calls',
                        affectedModels: models,
                        solution: 'Check JavaScript function call syntax in onclick handlers'
                    });
                }
                if (error.includes('SyntaxError')) {
                    report.recommendations.push({
                        issue: 'JavaScript syntax error',
                        affectedModels: models,
                        solution: 'Validate JavaScript code generation for model IDs with special characters'
                    });
                }
            }
        }

        return report;
    }

    async runFullTest() {
        console.log('🚀 Starte umfassenden Provider-Test...');
        
        try {
            await this.init();
            
            // Wechsle zu Statistics-Tab
            const statsTabFound = await this.waitForStatisticsTab();
            if (!statsTabFound) {
                throw new Error('Statistics-Tab nicht verfügbar');
            }

            // Analysiere OnClick-Pattern
            await this.analyzeOnClickPatterns();
            
            // Hole alle Model-Buttons
            const modelButtons = await this.getAllModelButtons();
            console.log(`\n🎯 Teste ${modelButtons.length} Model-Provider...`);

            // Teste jeden Button
            let testCount = 0;
            for (const modelData of modelButtons) {
                testCount++;
                console.log(`\n[${testCount}/${modelButtons.length}] Testing...`);
                await this.testModelButton(modelData);
                
                // Koordinations-Notification
                if (testCount % 5 === 0) {
                    console.log(`📢 Koordination: ${testCount} Provider getestet`);
                }
            }

            // Teste spezifische problematische Provider
            await this.testSpecificProviders();

            // Generiere Report
            const report = await this.generateReport();
            
            console.log('\n📊 TEST-ZUSAMMENFASSUNG:');
            console.log(`Total getestet: ${report.summary.totalTested}`);
            console.log(`Erfolgreich: ${report.summary.successful}`);
            console.log(`Problematisch: ${report.summary.problematic}`);
            console.log(`Error-Pattern: ${report.summary.errorPatterns}`);

            return report;

        } catch (error) {
            console.log(`❌ Test-Fehler: ${error.message}`);
            throw error;
        } finally {
            if (this.browser) {
                await this.browser.close();
            }
        }
    }

    async cleanup() {
        if (this.browser) {
            await this.browser.close();
        }
    }
}

// Main Execution
async function runProviderTests() {
    const tester = new ModelProviderTester();
    
    try {
        const report = await tester.runFullTest();
        
        // Schreibe Report
        const fs = require('fs');
        fs.writeFileSync(
            'PROVIDER_TESTING_REPORT.json', 
            JSON.stringify(report, null, 2)
        );
        
        console.log('\n✅ Report gespeichert: PROVIDER_TESTING_REPORT.json');
        return report;
        
    } catch (error) {
        console.log(`❌ Test fehlgeschlagen: ${error.message}`);
        return null;
    } finally {
        await tester.cleanup();
    }
}

// Für Claude-Flow Koordination
if (require.main === module) {
    runProviderTests().then(() => {
        console.log('🏁 Provider-Testing abgeschlossen');
        process.exit(0);
    }).catch(error => {
        console.error('💥 Provider-Testing fehlgeschlagen:', error);
        process.exit(1);
    });
}

module.exports = { ModelProviderTester, runProviderTests };