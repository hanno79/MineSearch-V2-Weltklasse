/**
 * Author: rahn
 * Datum: 14.08.2025
 * Version: 1.0
 * Beschreibung: PHASE 1.1 Validation - Data-Card Titel-Display Problem diagnostizieren
 */

const { chromium } = require('playwright');

async function validateTask1_1() {
    console.log('🔍 [TASK 1.1] Diagnostiziere Data-Card Titel-Display Problem...');
    
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    
    try {
        // Öffne die Anwendung
        await page.goto('http://localhost:8000', { waitUntil: 'networkidle' });
        console.log('✅ [TASK 1.1] Page loaded');
        
        // Navigiere zum Ergebnisse-Tab
        await page.click('a[data-tab="consolidated"]');
        await page.waitForTimeout(2000);
        
        // Prüfe, welche Art von Daten im Ergebnisse-Tab angezeigt werden
        const cards = await page.$$('.mine-data-card');
        console.log(`📊 [TASK 1.1] Found ${cards.length} cards in Ergebnisse tab`);
        
        if (cards.length > 0) {
            // Extrahiere die ersten 5 Card-Titel
            const cardTitles = [];
            for (let i = 0; i < Math.min(5, cards.length); i++) {
                const titleElement = await cards[i].$('.card-title');
                if (titleElement) {
                    const title = await titleElement.textContent();
                    cardTitles.push(title);
                }
            }
            
            console.log('🏷️ [TASK 1.1] Card Titles:', cardTitles);
            
            // Prüfe ob es Model-IDs sind (enthalten 🤖 und openrouter/perplexity)
            const modelIdCards = cardTitles.filter(title => 
                title.includes('🤖') || 
                title.includes('openrouter:') || 
                title.includes('perplexity:')
            );
            
            const mineNameCards = cardTitles.filter(title => 
                title.includes('Mine') && 
                !title.includes('openrouter:') && 
                !title.includes('perplexity:')
            );
            
            console.log(`🤖 [TASK 1.1] Model-ID-Cards: ${modelIdCards.length}/${cardTitles.length}`);
            console.log(`🏭 [TASK 1.1] Mine-Name-Cards: ${mineNameCards.length}/${cardTitles.length}`);
            
            // Screenshot für Dokumentation
            await page.screenshot({ 
                path: 'task_1_1_validation.png', 
                fullPage: true 
            });
            
            // DIAGNOSE ERGEBNIS
            if (modelIdCards.length > mineNameCards.length) {
                console.log('🚨 [TASK 1.1] PROBLEM BESTÄTIGT: Ergebnisse-Tab zeigt Model-IDs statt Mine-Namen!');
                
                // API-Aufruf analysieren
                const response = await page.evaluate(async () => {
                    const resp = await fetch(`${window.API_BASE_URL}/api/consolidated/results?sort_by=mine_name&order=asc&exclude_exa=true&days_back=30`);
                    const data = await resp.json();
                    return {
                        success: data.success,
                        dataType: typeof data.data,
                        firstResult: data.data?.consolidated_results?.[0] || null,
                        totalResults: data.data?.consolidated_results?.length || 0
                    };
                });
                
                console.log('📡 [TASK 1.1] API Response Analysis:', response);
                
                if (response.firstResult) {
                    console.log('🔍 [TASK 1.1] First Result Keys:', Object.keys(response.firstResult));
                    console.log('🔍 [TASK 1.1] Has mine_name?', 'mine_name' in response.firstResult);
                    console.log('🔍 [TASK 1.1] Has model_id?', 'model_id' in response.firstResult);
                }
                
                return {
                    status: 'PROBLEM_CONFIRMED',
                    issue: 'Model-IDs instead of Mine-Names',
                    modelIdCards: modelIdCards.length,
                    mineNameCards: mineNameCards.length,
                    totalCards: cardTitles.length,
                    apiResponse: response
                };
                
            } else {
                console.log('✅ [TASK 1.1] OK: Ergebnisse-Tab zeigt korrekt Mine-Namen');
                return {
                    status: 'OK',
                    mineNameCards: mineNameCards.length,
                    totalCards: cardTitles.length
                };
            }
            
        } else {
            console.log('❌ [TASK 1.1] ERROR: Keine Cards im Ergebnisse-Tab gefunden');
            return { status: 'NO_CARDS_FOUND' };
        }
        
    } catch (error) {
        console.error('❌ [TASK 1.1] Error:', error);
        return { status: 'ERROR', error: error.message };
    } finally {
        await browser.close();
    }
}

// Führe den Test aus
validateTask1_1().then(result => {
    console.log('🎯 [TASK 1.1] FINAL RESULT:', result);
    process.exit(0);
}).catch(error => {
    console.error('💥 [TASK 1.1] FATAL ERROR:', error);
    process.exit(1);
});