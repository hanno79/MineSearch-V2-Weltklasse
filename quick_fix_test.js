/**
 * Author: rahn  
 * Datum: 14.08.2025
 * Beschreibung: PHASE 2.1 - Source Attribution Debug Test
 */

const { chromium } = require('playwright');

async function testSourceAttribution() {
    console.log('🔍 [PHASE 2.1] Source Attribution Debug Test...');
    
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    
    try {
        await page.goto('http://localhost:8000', { waitUntil: 'networkidle' });
        
        // Navigiere zu Ergebnisse-Tab
        await page.click('a[data-tab="consolidated"]');
        await page.waitForTimeout(3000);
        
        // Analysiere erste 3 Cards für Source-Daten
        const sourceAnalysis = await page.evaluate(() => {
            const cards = document.querySelectorAll('.mine-data-card');
            const analysis = [];
            
            for (let i = 0; i < Math.min(3, cards.length); i++) {
                const card = cards[i];
                const title = card.querySelector('.card-title')?.textContent?.trim();
                const sourceBadge = card.querySelector('.source-badge')?.textContent?.trim();
                
                analysis.push({
                    cardIndex: i,
                    mineName: title,
                    sourceBadgeText: sourceBadge,
                    hasNoSources: sourceBadge?.includes('Keine Quellen verfügbar')
                });
            }
            
            return analysis;
        });
        
        console.log('📊 [PHASE 2.1] Source Attribution Analysis:');
        sourceAnalysis.forEach(card => {
            console.log(`  Card ${card.cardIndex}: ${card.mineName}`);
            console.log(`    Source Badge: "${card.sourceBadgeText}"`);
            console.log(`    Problem: ${card.hasNoSources ? 'JA' : 'NEIN'}`);
            console.log('');
        });
        
        // Test API Response direkt
        const apiResponse = await page.evaluate(async () => {
            const response = await fetch(`${window.API_BASE_URL}/api/consolidated/results?sort_by=mine_name&order=asc&exclude_exa=true&days_back=30`);
            const data = await response.json();
            
            if (data.success && data.data?.consolidated_results?.[0]) {
                const firstResult = data.data.consolidated_results[0];
                return {
                    mineName: firstResult.mine_name,
                    hasSourceSummary: !!firstResult.source_summary,
                    sourceSummaryKeys: firstResult.source_summary ? Object.keys(firstResult.source_summary) : [],
                    hasDetailedBreakdown: !!firstResult.detailed_breakdown,
                    sampleDetailedKeys: firstResult.detailed_breakdown ? Object.keys(firstResult.detailed_breakdown).slice(0, 3) : []
                };
            }
            return null;
        });
        
        console.log('📡 [PHASE 2.1] API Data Structure Analysis:');
        if (apiResponse) {
            console.log(`  Mine: ${apiResponse.mineName}`);
            console.log(`  Has source_summary: ${apiResponse.hasSourceSummary}`);
            console.log(`  source_summary keys: ${apiResponse.sourceSummaryKeys.join(', ')}`);
            console.log(`  Has detailed_breakdown: ${apiResponse.hasDetailedBreakdown}`);
            console.log(`  detailed_breakdown sample keys: ${apiResponse.sampleDetailedKeys.join(', ')}`);
        } else {
            console.log('  ❌ No API data available');
        }
        
        await page.screenshot({ path: 'quick_fix_test_result.png', fullPage: true });
        
        return {
            status: sourceAnalysis.every(card => card.hasNoSources) ? 'ALL_CARDS_MISSING_SOURCES' : 'SOME_SOURCES_FOUND',
            cardsWithoutSources: sourceAnalysis.filter(card => card.hasNoSources).length,
            totalCards: sourceAnalysis.length,
            apiDataStructure: apiResponse
        };
        
    } catch (error) {
        console.error('❌ [PHASE 2.1] Error:', error);
        return { status: 'ERROR', error: error.message };
    } finally {
        await browser.close();
    }
}

testSourceAttribution().then(result => {
    console.log('🎯 [PHASE 2.1] FINAL RESULT:', JSON.stringify(result, null, 2));
    process.exit(0);
}).catch(error => {
    console.error('💥 [PHASE 2.1] FATAL ERROR:', error);
    process.exit(1);
});