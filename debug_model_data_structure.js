/**
 * Author: rahn
 * Datum: 13.08.2025
 * Version: 1.0
 * Beschreibung: Debug der Model-Datenstruktur für Source-Attribution
 */

const { chromium } = require('playwright');

async function debugModelDataStructure() {
    console.log('🔬 Debug der Model-Datenstruktur für Source-Attribution...');
    
    const browser = await chromium.launch({ 
        headless: false,
        slowMo: 500 
    });
    
    const context = await browser.newContext();
    const page = await context.newPage();
    
    page.on('console', msg => {
        if (msg.type() === 'log' && (msg.text().includes('MODEL-SOURCE-EXTRACT') || msg.text().includes('STATISTICS'))) {
            console.log(`🐛 KONSOLE: ${msg.text()}`);
        }
    });
    
    try {
        await page.goto('http://localhost:8000');
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(5000); // Warten auf vollständige Initialisierung
        
        // Statistiken Tab aktivieren
        await page.evaluate(() => {
            if (typeof showTab === 'function') {
                showTab('statistics');
            }
        });
        
        await page.waitForTimeout(2000);
        
        // Detaillierte Analyse der Datenstruktur
        const modelDataAnalysis = await page.evaluate(() => {
            const analysis = {
                statisticsDataExists: typeof statisticsData !== 'undefined',
                statisticsDataContent: typeof statisticsData !== 'undefined' ? statisticsData : null,
                currentStatsExists: typeof currentStats !== 'undefined',
                currentStatsContent: typeof currentStats !== 'undefined' ? currentStats : null,
                sampleModelAnalysis: null
            };
            
            // Falls statisticsData existiert, analysiere die Struktur
            if (typeof statisticsData !== 'undefined' && statisticsData && statisticsData.models) {
                const modelKeys = Object.keys(statisticsData.models);
                if (modelKeys.length > 0) {
                    const firstModelKey = modelKeys[0];
                    const firstModel = statisticsData.models[firstModelKey];
                    
                    analysis.sampleModelAnalysis = {
                        modelKey: firstModelKey,
                        modelId: firstModel.model_id,
                        hasFieldPerformance: !!firstModel.field_performance,
                        hasRecentSearches: !!firstModel.recent_searches,
                        hasSourcesUsed: !!firstModel.sources_used,
                        hasAggregatedSources: !!firstModel.aggregated_sources,
                        actualStructure: firstModel,
                        fieldPerformanceKeys: firstModel.field_performance ? Object.keys(firstModel.field_performance) : [],
                        recentSearchesLength: firstModel.recent_searches ? firstModel.recent_searches.length : 0
                    };
                    
                    // Test der Extract-Funktion mit echten Daten
                    if (typeof extractSourcesFromModelData === 'function') {
                        console.log('🧪 [DEBUG] Teste extractSourcesFromModelData mit echten Model-Daten...');
                        const extractResult = extractSourcesFromModelData(firstModel);
                        analysis.extractTestResult = extractResult;
                        console.log('🔍 [DEBUG] Extract Result:', extractResult);
                    }
                }
            }
            
            return analysis;
        });
        
        console.log('\n📊 STATISTIKEN-DATEN ANALYSE:');
        console.log('✅ statisticsData existiert:', modelDataAnalysis.statisticsDataExists);
        console.log('✅ currentStats existiert:', modelDataAnalysis.currentStatsExists);
        
        if (modelDataAnalysis.sampleModelAnalysis) {
            const sample = modelDataAnalysis.sampleModelAnalysis;
            console.log('\n🔍 SAMPLE MODEL ANALYSE:');
            console.log('🔑 Model Key:', sample.modelKey);
            console.log('🆔 Model ID:', sample.modelId);
            console.log('📊 Has field_performance:', sample.hasFieldPerformance);
            console.log('🔎 Has recent_searches:', sample.hasRecentSearches);
            console.log('📈 Has sources_used:', sample.hasSourcesUsed);
            console.log('📋 Has aggregated_sources:', sample.hasAggregatedSources);
            console.log('🔑 Field Performance Keys:', sample.fieldPerformanceKeys);
            console.log('📏 Recent Searches Length:', sample.recentSearchesLength);
            
            if (sample.extractTestResult) {
                console.log('\n🧪 EXTRACT TEST RESULT:');
                console.log('📊 Extracted Sources Count:', sample.extractTestResult.length);
                console.log('📋 Extracted Sources:', sample.extractTestResult);
            }
            
            console.log('\n📋 VOLLSTÄNDIGE MODEL-STRUKTUR:');
            console.log(JSON.stringify(sample.actualStructure, null, 2));
        }
        
        // Screenshot für visuelle Überprüfung
        await page.screenshot({ 
            path: '/app/model_data_debug_screenshot.png',
            fullPage: true 
        });
        
        await page.waitForTimeout(2000);
        
    } catch (error) {
        console.error('❌ Fehler bei der Model-Daten-Analyse:', error);
    } finally {
        await browser.close();
    }
}

debugModelDataStructure().catch(console.error);