/**
 * Author: rahn
 * Datum: 14.08.2025
 * Version: 1.0
 * Beschreibung: PHASE 2.1.1 - Deep Backend API Datenstruktur Analyse für Source Attribution
 */

const { chromium } = require('playwright');

async function deepContentAnalysis() {
    console.log('🔍 [PHASE 2.1.1] Deep Backend API Analyse für Source Attribution...');
    
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    
    try {
        await page.goto('http://localhost:8000', { waitUntil: 'networkidle' });
        console.log('✅ [PHASE 2.1.1] Page loaded');
        
        // Detaillierte API Response Analyse
        const apiAnalysis = await page.evaluate(async () => {
            console.log('📡 [API-ANALYSIS] Starting deep API structure analysis...');
            
            const response = await fetch(`${window.API_BASE_URL}/api/consolidated/results?sort_by=mine_name&order=asc&exclude_exa=true&days_back=30`);
            const data = await response.json();
            
            if (!data.success || !data.data?.consolidated_results) {
                return { error: 'No consolidated results available' };
            }
            
            const firstResult = data.data.consolidated_results[0];
            console.log('🔍 [API-ANALYSIS] First result keys:', Object.keys(firstResult));
            
            return {
                totalResults: data.data.consolidated_results.length,
                firstResultAnalysis: {
                    mineName: firstResult.mine_name,
                    topLevelKeys: Object.keys(firstResult),
                    
                    // SOURCE SUMMARY ANALYSE
                    hasSourceSummary: !!firstResult.source_summary,
                    sourceSummaryStructure: firstResult.source_summary ? {
                        keys: Object.keys(firstResult.source_summary),
                        hasSources: !!firstResult.source_summary.sources,
                        hasSourcesByDomain: !!firstResult.source_summary.sources_by_domain,
                        sourcesType: Array.isArray(firstResult.source_summary.sources) ? 'array' : typeof firstResult.source_summary.sources
                    } : null,
                    
                    // DETAILED BREAKDOWN ANALYSE
                    hasDetailedBreakdown: !!firstResult.detailed_breakdown,
                    detailedBreakdownStructure: firstResult.detailed_breakdown ? {
                        fieldCount: Object.keys(firstResult.detailed_breakdown).length,
                        sampleFields: Object.keys(firstResult.detailed_breakdown).slice(0, 3),
                        firstFieldStructure: (() => {
                            const firstField = Object.values(firstResult.detailed_breakdown)[0];
                            return firstField ? {
                                keys: Object.keys(firstField),
                                hasBestValue: !!firstField.best_value,
                                bestValueStructure: firstField.best_value ? {
                                    keys: Object.keys(firstField.best_value),
                                    hasSources: !!firstField.best_value.sources
                                } : null
                            } : null;
                        })()
                    } : null,
                    
                    // ALTERNATIVE FIELDS SUCHE
                    alternativeSourceFields: (() => {
                        const result = {};
                        for (const [key, value] of Object.entries(firstResult)) {
                            if (key.toLowerCase().includes('source') || 
                                key.toLowerCase().includes('url') ||
                                key.toLowerCase().includes('domain')) {
                                result[key] = {
                                    type: typeof value,
                                    isArray: Array.isArray(value),
                                    sampleValue: typeof value === 'string' ? value.slice(0, 50) : null
                                };
                            }
                        }
                        return result;
                    })()
                }
            };
        });
        
        console.log('📊 [PHASE 2.1.1] API STRUCTURE ANALYSIS:');
        
        if (apiAnalysis.error) {
            console.log('❌ API Error:', apiAnalysis.error);
            return { status: 'API_ERROR', error: apiAnalysis.error };
        }
        
        console.log(`📋 Mine: ${apiAnalysis.firstResultAnalysis.mineName}`);
        console.log(`🔑 Keys: ${apiAnalysis.firstResultAnalysis.topLevelKeys.join(', ')}`);
        
        console.log('\n🔍 SOURCE FIELDS:');
        console.log(`  source_summary: ${apiAnalysis.firstResultAnalysis.hasSourceSummary ? 'YES' : 'NO'}`);
        console.log(`  detailed_breakdown: ${apiAnalysis.firstResultAnalysis.hasDetailedBreakdown ? 'YES' : 'NO'}`);
        
        if (Object.keys(apiAnalysis.firstResultAnalysis.alternativeSourceFields).length > 0) {
            console.log('  Alternative fields:', Object.keys(apiAnalysis.firstResultAnalysis.alternativeSourceFields));
        }
        
        return {
            status: 'ANALYSIS_COMPLETE',
            analysis: apiAnalysis
        };
        
    } catch (error) {
        console.error('❌ [PHASE 2.1.1] Error:', error);
        return { status: 'ERROR', error: error.message };
    } finally {
        await browser.close();
    }
}

deepContentAnalysis().then(result => {
    console.log('\n🎯 [PHASE 2.1.1] COMPLETE!');
    process.exit(0);
}).catch(error => {
    console.error('💥 [PHASE 2.1.1] ERROR:', error);
    process.exit(1);
});