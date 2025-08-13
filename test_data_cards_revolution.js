/**
 * Playwright Test für Data-Cards Revolution
 * Testet die neuen modernen Cards vs. hässliche Tabellen
 */

const { chromium } = require('playwright');

async function testDataCardsRevolution() {
    console.log('🎨 [DATA-CARDS-TEST] Starte Data-Cards Revolution Test...');
    
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    
    try {
        // Navigiere zur MineSearch 2.0 Oberfläche
        console.log('🌐 [NAVIGATION] Lade MineSearch 2.0...');
        await page.goto('http://localhost:8000/static/index.html', { 
            waitUntil: 'domcontentloaded',
            timeout: 10000 
        });
        
        // Screenshot: Initiale Ansicht
        await page.screenshot({ 
            path: '/app/data_cards_01_initial.png',
            fullPage: true 
        });
        console.log('📸 [SCREENSHOT] data_cards_01_initial.png erstellt');
        
        // Warte auf Modell-Loading
        console.log('🔄 [MODELS] Warte auf Modell-Loading...');
        await page.waitForTimeout(3000);
        
        // Navigiere zu Statistics-Tab (hier sind Data-Cards implementiert)
        console.log('📊 [STATISTICS] Wechsle zu Statistics-Tab...');
        await page.click('label[for="statistics-tab"]');
        await page.waitForTimeout(1000);
        
        // Screenshot: Statistics-Tab geöffnet
        await page.screenshot({ 
            path: '/app/data_cards_02_statistics_tab.png',
            fullPage: true 
        });
        console.log('📸 [SCREENSHOT] data_cards_02_statistics_tab.png erstellt');
        
        // Lade Statistiken (löst Data-Cards aus)
        console.log('📈 [LOAD-STATS] Lade Statistiken...');
        await page.click('button:has-text("Statistiken laden")');
        await page.waitForTimeout(5000);
        
        // Screenshot: Data-Cards geladen
        await page.screenshot({ 
            path: '/app/data_cards_03_loaded.png',
            fullPage: true 
        });
        console.log('📸 [SCREENSHOT] data_cards_03_loaded.png erstellt');
        
        // Prüfe ob Data-Cards vorhanden sind
        const dataCards = await page.$$('.mine-data-card');
        console.log(`🃏 [DATA-CARDS] ${dataCards.length} Data-Cards gefunden`);
        
        if (dataCards.length > 0) {
            console.log('✅ [SUCCESS] Data-Cards erfolgreich gerendert!');
            
            // Prüfe Source-Badges
            const sourceBadges = await page.$$('.source-badge');
            console.log(`🔗 [SOURCE-BADGES] ${sourceBadges.length} Source-Badges gefunden`);
            
            // Teste Card-Hover-Effekte
            if (dataCards.length > 0) {
                console.log('🎯 [HOVER-TEST] Teste Card-Hover...');
                await dataCards[0].hover();
                await page.waitForTimeout(1000);
                
                await page.screenshot({ 
                    path: '/app/data_cards_04_hover.png',
                    fullPage: true 
                });
                console.log('📸 [SCREENSHOT] data_cards_04_hover.png erstellt');
            }
            
        } else {
            console.log('❌ [ERROR] Keine Data-Cards gefunden - möglicherweise noch Tabellen');
            
            // Prüfe ob alte Tabellen vorhanden sind
            const tables = await page.$$('table');
            console.log(`📋 [TABLES] ${tables.length} alte Tabellen gefunden`);
        }
        
        // Teste Consolidated-Tab
        console.log('📋 [CONSOLIDATED] Wechsle zu Consolidated-Tab...');
        await page.click('label[for="consolidated-tab"]');
        await page.waitForTimeout(1000);
        
        await page.click('button:has-text("Filter anwenden")');
        await page.waitForTimeout(5000);
        
        await page.screenshot({ 
            path: '/app/data_cards_05_consolidated.png',
            fullPage: true 
        });
        console.log('📸 [SCREENSHOT] data_cards_05_consolidated.png erstellt');
        
        // Finaler Screenshot der ganzen Seite
        await page.screenshot({ 
            path: '/app/data_cards_final_result.png',
            fullPage: true 
        });
        console.log('📸 [SCREENSHOT] data_cards_final_result.png erstellt');
        
        console.log('🎉 [COMPLETE] Data-Cards Revolution Test abgeschlossen!');
        
    } catch (error) {
        console.error('❌ [ERROR] Test fehlgeschlagen:', error);
        
        await page.screenshot({ 
            path: '/app/data_cards_error.png',
            fullPage: true 
        });
        console.log('📸 [ERROR] data_cards_error.png erstellt');
    }
    
    await browser.close();
}

testDataCardsRevolution().catch(console.error);