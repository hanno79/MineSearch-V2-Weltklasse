/**
 * Author: rahn
 * Datum: 13.08.2025
 * Version: 1.0
 * Beschreibung: Playwright-Analyse der Quellenangaben in Statistik-Cards
 */

const { chromium } = require('playwright');

async function analyzeSourceAttribution() {
    console.log('🔍 Starte Quellenangaben-Analyse mit Playwright...');
    
    const browser = await chromium.launch({ 
        headless: false,
        slowMo: 1000 
    });
    
    const context = await browser.newContext();
    const page = await context.newPage();
    
    // Console-Logs abfangen
    page.on('console', msg => {
        if (msg.text().includes('SOURCE-EXTRACT') || msg.text().includes('undefined') || msg.text().includes('source')) {
            console.log(`🐛 KONSOLE: ${msg.type()}: ${msg.text()}`);
        }
    });
    
    try {
        console.log('📡 Navigiere zu http://localhost:8000...');
        await page.goto('http://localhost:8000');
        await page.waitForLoadState('networkidle');
        
        console.log('📊 Wechsle zum Statistiken Tab...');
        await page.click('button[onclick="showTab(\'statistics\')"]');
        await page.waitForTimeout(2000);
        
        console.log('📸 Erstelle Screenshot der Statistiken-Seite...');
        await page.screenshot({ 
            path: '/app/statistics_source_analysis.png',
            fullPage: true 
        });
        
        console.log('🔍 Analysiere Source-Badges...');
        
        // Alle Model-Cards finden
        const modelCards = await page.$$('.model-card');
        console.log(`📋 Gefundene Model-Cards: ${modelCards.length}`);
        
        let undefinedSources = 0;
        let validSources = 0;
        let noSourcesAvailable = 0;
        
        for (let i = 0; i < modelCards.length; i++) {
            const card = modelCards[i];
            
            // Model Name extrahieren
            const modelNameEl = await card.$('.model-name');
            const modelName = modelNameEl ? await modelNameEl.textContent() : `Model ${i+1}`;
            
            // Source Badge finden
            const sourceBadge = await card.$('.source-badge');
            if (sourceBadge) {
                const sourceText = await sourceBadge.textContent();
                console.log(`📝 ${modelName}: Source = "${sourceText}"`);
                
                if (sourceText.includes('undefined')) {
                    undefinedSources++;
                    console.log(`❌ PROBLEM: ${modelName} zeigt "undefined"`);
                } else if (sourceText.includes('keine Quellen verfügbar')) {
                    noSourcesAvailable++;
                    console.log(`⚠️  ${modelName}: Keine Quellen verfügbar`);
                } else {
                    validSources++;
                    console.log(`✅ ${modelName}: Gültige Quelle gefunden`);
                }
            } else {
                console.log(`❓ ${modelName}: Kein Source-Badge gefunden`);
            }
        }
        
        console.log('\n📊 ZUSAMMENFASSUNG:');
        console.log(`✅ Gültige Quellen: ${validSources}`);
        console.log(`❌ Undefined Quellen: ${undefinedSources}`);
        console.log(`⚠️  Keine Quellen verfügbar: ${noSourcesAvailable}`);
        console.log(`❓ Fehlende Source-Badges: ${modelCards.length - validSources - undefinedSources - noSourcesAvailable}`);
        
        // Detaillierte Datenstruktur-Analyse
        console.log('\n🔬 DATENSTRUKTUR-ANALYSE:');
        const modelData = await page.evaluate(() => {
            // Globale Variablen prüfen
            const data = {
                globalModelData: typeof window.globalModelData !== 'undefined' ? Object.keys(window.globalModelData || {}) : 'undefined',
                currentSearchResults: typeof window.currentSearchResults !== 'undefined' ? window.currentSearchResults : 'undefined',
                statisticsData: typeof window.statisticsData !== 'undefined' ? window.statisticsData : 'undefined'
            };
            
            // Erste Model-Card analysieren für Datenstruktur
            const firstCard = document.querySelector('.model-card');
            if (firstCard) {
                const modelName = firstCard.querySelector('.model-name')?.textContent;
                console.log('SOURCE-EXTRACT: Analysiere Model:', modelName);
                
                // Versuche Daten zu extrahieren
                if (window.globalModelData && window.globalModelData[modelName]) {
                    const modelInfo = window.globalModelData[modelName];
                    console.log('SOURCE-EXTRACT: Model Data:', modelInfo);
                    data.sampleModelData = modelInfo;
                }
            }
            
            return data;
        });
        
        console.log('🗂️  Global Model Data Keys:', modelData.globalModelData);
        console.log('🔍 Current Search Results:', typeof modelData.currentSearchResults);
        console.log('📊 Statistics Data:', typeof modelData.statisticsData);
        
        if (modelData.sampleModelData) {
            console.log('📝 Sample Model Data Structure:', JSON.stringify(modelData.sampleModelData, null, 2));
        }
        
        // Source-Extract Funktion testen
        console.log('\n🧪 TESTE extractSourcesFromModelData FUNKTION:');
        const sourceExtractionTest = await page.evaluate(() => {
            if (typeof extractSourcesFromModelData === 'function') {
                console.log('SOURCE-EXTRACT: Funktion gefunden, teste...');
                
                // Test mit Sample-Daten
                const testData = {
                    source: 'Testquelle',
                    url: 'https://example.com',
                    metadata: { source: 'Metadata Source' },
                    sources: ['Quelle1', 'Quelle2']
                };
                
                const result = extractSourcesFromModelData(testData);
                console.log('SOURCE-EXTRACT: Test Result:', result);
                return { found: true, testResult: result };
            } else {
                console.log('SOURCE-EXTRACT: Funktion nicht gefunden!');
                return { found: false, error: 'extractSourcesFromModelData nicht verfügbar' };
            }
        });
        
        console.log('🔧 Source Extract Function Test:', sourceExtractionTest);
        
        await page.waitForTimeout(3000);
        
    } catch (error) {
        console.error('❌ Fehler bei der Analyse:', error);
    } finally {
        await browser.close();
    }
}

analyzeSourceAttribution().catch(console.error);