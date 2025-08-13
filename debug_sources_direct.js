/**
 * Author: rahn
 * Datum: 13.08.2025
 * Version: 1.0
 * Beschreibung: Direkte Analyse der Source-Extract Problematik
 */

const { chromium } = require('playwright');

async function debugSourcesDirectly() {
    console.log('🔍 Direkte Source-Extract Debug-Analyse...');
    
    const browser = await chromium.launch({ 
        headless: false,
        slowMo: 500 
    });
    
    const context = await browser.newContext();
    const page = await context.newPage();
    
    // Console-Logs abfangen
    page.on('console', msg => {
        console.log(`🐛 KONSOLE: ${msg.type()}: ${msg.text()}`);
    });
    
    try {
        console.log('📡 Navigiere zu http://localhost:8000...');
        await page.goto('http://localhost:8000');
        await page.waitForLoadState('networkidle');
        
        // Warte auf UI-Initialisierung
        await page.waitForTimeout(3000);
        
        console.log('📸 Screenshot der aktuellen Seite...');
        await page.screenshot({ 
            path: '/app/current_page_state.png',
            fullPage: true 
        });
        
        // Verfügbare Tabs finden
        console.log('🔍 Suche verfügbare Tabs...');
        const tabs = await page.evaluate(() => {
            const tabButtons = document.querySelectorAll('button');
            return Array.from(tabButtons).map(btn => ({
                text: btn.textContent,
                onclick: btn.getAttribute('onclick'),
                id: btn.id,
                className: btn.className
            }));
        });
        
        console.log('📋 Verfügbare Tabs:', tabs);
        
        // Statistiken Tab direkt aufrufen
        console.log('📊 Aktiviere Statistiken Tab direkt...');
        await page.evaluate(() => {
            // Versuche verschiedene Methoden
            if (typeof showTab === 'function') {
                showTab('statistics');
            } else if (typeof window.showTab === 'function') {
                window.showTab('statistics');
            }
            
            // Falls die Funktion nicht verfügbar ist, manuell aktivieren
            const statsTab = document.getElementById('statistics');
            if (statsTab) {
                // Alle Tabs deaktivieren
                document.querySelectorAll('.tab-content').forEach(tab => {
                    tab.style.display = 'none';
                });
                // Statistiken Tab aktivieren
                statsTab.style.display = 'block';
            }
        });
        
        await page.waitForTimeout(2000);
        
        console.log('📸 Screenshot nach Tab-Aktivierung...');
        await page.screenshot({ 
            path: '/app/statistics_tab_activated.png',
            fullPage: true 
        });
        
        // Detaillierte Datenstruktur-Analyse
        console.log('\n🔬 DETAILLIERTE DATENSTRUKTUR-ANALYSE:');
        const debugInfo = await page.evaluate(() => {
            const debug = {
                globalModelDataExists: typeof window.globalModelData !== 'undefined',
                globalModelDataKeys: window.globalModelData ? Object.keys(window.globalModelData) : [],
                sampleModelEntry: null,
                extractSourcesFunctionExists: typeof extractSourcesFromModelData === 'function',
                sourceExtractionTest: null
            };
            
            // Sample Model Entry analysieren
            if (window.globalModelData && Object.keys(window.globalModelData).length > 0) {
                const firstKey = Object.keys(window.globalModelData)[0];
                debug.sampleModelEntry = {
                    key: firstKey,
                    data: window.globalModelData[firstKey]
                };
                
                // Test der extractSourcesFromModelData Funktion
                if (typeof extractSourcesFromModelData === 'function') {
                    console.log('🧪 Teste extractSourcesFromModelData mit echten Daten...');
                    const testResult = extractSourcesFromModelData(window.globalModelData[firstKey]);
                    debug.sourceExtractionTest = {
                        input: window.globalModelData[firstKey],
                        output: testResult
                    };
                    console.log('🔍 Extract Test Result:', testResult);
                }
            }
            
            return debug;
        });
        
        console.log('🗂️  Global Model Data existiert:', debugInfo.globalModelDataExists);
        console.log('🔑 Global Model Data Keys:', debugInfo.globalModelDataKeys);
        console.log('🧪 Extract Sources Function existiert:', debugInfo.extractSourcesFunctionExists);
        
        if (debugInfo.sampleModelEntry) {
            console.log('\n📝 SAMPLE MODEL ENTRY:');
            console.log('🔑 Key:', debugInfo.sampleModelEntry.key);
            console.log('📊 Data Structure:', JSON.stringify(debugInfo.sampleModelEntry.data, null, 2));
        }
        
        if (debugInfo.sourceExtractionTest) {
            console.log('\n🧪 SOURCE EXTRACTION TEST:');
            console.log('📝 Output:', debugInfo.sourceExtractionTest.output);
        }
        
        // Model Cards analysieren
        console.log('\n🃏 MODEL CARDS ANALYSE:');
        const cardAnalysis = await page.evaluate(() => {
            const cards = document.querySelectorAll('.model-card');
            const analysis = [];
            
            cards.forEach((card, index) => {
                const modelName = card.querySelector('.model-name')?.textContent || `Model ${index + 1}`;
                const sourceBadge = card.querySelector('.source-badge');
                const sourceText = sourceBadge ? sourceBadge.textContent : 'Kein Source Badge';
                
                analysis.push({
                    index,
                    modelName,
                    sourceText,
                    hasSourceBadge: !!sourceBadge,
                    badgeHTML: sourceBadge ? sourceBadge.outerHTML : null
                });
            });
            
            return analysis;
        });
        
        console.log('🃏 Gefundene Model Cards:', cardAnalysis.length);
        cardAnalysis.forEach(card => {
            console.log(`📋 ${card.modelName}:`);
            console.log(`   Source Text: "${card.sourceText}"`);
            console.log(`   Has Badge: ${card.hasSourceBadge}`);
            if (card.sourceText.includes('undefined')) {
                console.log(`   ❌ PROBLEM: undefined detected!`);
            }
        });
        
        await page.waitForTimeout(2000);
        
    } catch (error) {
        console.error('❌ Fehler bei der Debug-Analyse:', error);
    } finally {
        await browser.close();
    }
}

debugSourcesDirectly().catch(console.error);