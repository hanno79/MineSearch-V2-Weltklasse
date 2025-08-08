const { chromium } = require('playwright');

async function analyzeConsistencyValues() {
    console.log('🔍 KONSISTENZ-ANALYSE - Browser UI Validation');
    console.log('=' * 60);
    
    const browser = await chromium.launch({ headless: false, slowMo: 1000 });
    const page = await browser.newPage();
    
    try {
        // Navigiere zur MineSearch Anwendung
        console.log('📱 Navigiere zu MineSearch...');
        await page.goto('http://localhost:8000');
        await page.waitForLoadState('networkidle');
        
        // Wechsle zu Statistics Tab
        console.log('📊 Wechsle zu Statistics Tab...');
        const statsRadio = await page.locator('input[value="method_statistics"]');
        await statsRadio.click();
        await page.waitForTimeout(3000);
        
        // Lade Statistics
        console.log('🔄 Lade Statistics...');
        const loadStatsBtn = await page.locator('button:has-text("📊 Statistiken laden")');
        if (await loadStatsBtn.isVisible()) {
            await loadStatsBtn.click();
            await page.waitForTimeout(5000);
        }
        
        // Screenshot der Haupttabelle
        console.log('📸 Screenshot der Haupt-Statistik-Tabelle...');
        await page.screenshot({ 
            path: '/app/minesearch_v2/frontend/consistency_main_table.png',
            fullPage: true 
        });
        
        // Extrahiere Konsistenz-Werte aus Haupttabelle
        console.log('🔍 Extrahiere Konsistenz-Werte aus Haupttabelle...');
        const consistencyValues = await page.evaluate(() => {
            const table = document.querySelector('#enhanced-statistics-table-container table, .model-statistics-table');
            if (!table) return { error: 'Tabelle nicht gefunden' };
            
            const rows = Array.from(table.querySelectorAll('tr'));
            const results = [];
            
            rows.forEach((row, index) => {
                const cells = Array.from(row.querySelectorAll('td, th'));
                if (cells.length >= 5) {
                    const modelName = cells[0]?.textContent?.trim();
                    // Suche Konsistenz-Spalte (normalerweise Spalte 4 oder 5)
                    const consistencyCell = cells.find(cell => 
                        cell.textContent?.includes('%') && 
                        (cell.textContent?.includes('100') || cell.textContent?.includes('Konsistenz'))
                    );
                    
                    if (modelName && consistencyCell && !modelName.includes('Modell')) {
                        results.push({
                            row: index,
                            model: modelName,
                            consistency: consistencyCell.textContent?.trim(),
                            rawHTML: consistencyCell.innerHTML
                        });
                    }
                }
            });
            
            return { success: true, data: results };
        });
        
        console.log('📋 Konsistenz-Werte Haupttabelle:', JSON.stringify(consistencyValues, null, 2));
        
        // Analysiere Detail-Modals
        console.log('🎭 Analysiere Detail-Modals...');
        const detailButtons = await page.locator('button:has-text("Details")').all();
        
        for (let i = 0; i < Math.min(3, detailButtons.length); i++) {
            console.log(`🔍 Öffne Detail-Modal ${i + 1}...`);
            
            await detailButtons[i].click();
            await page.waitForTimeout(3000);
            
            // Screenshot des Detail-Modals
            await page.screenshot({ 
                path: `/app/minesearch_v2/frontend/consistency_detail_modal_${i + 1}.png`,
                fullPage: true 
            });
            
            // Extrahiere Detail-Modal Konsistenz-Werte
            const modalConsistency = await page.evaluate(() => {
                // Suche nach Performance-Übersicht
                const performanceSection = document.querySelector('div:has-text("Performance-Übersicht")');
                if (!performanceSection) return { error: 'Performance-Übersicht nicht gefunden' };
                
                const parent = performanceSection.closest('div');
                const consistencyItems = Array.from(parent.querySelectorAll('div')).filter(div =>
                    div.textContent?.includes('Konsistenz') || 
                    div.textContent?.includes('Erfolgsrate') ||
                    div.textContent?.includes('Felder')
                );
                
                return {
                    success: true,
                    data: consistencyItems.map(item => ({
                        text: item.textContent?.trim(),
                        html: item.innerHTML
                    }))
                };
            });
            
            console.log(`📊 Detail-Modal ${i + 1} Konsistenz:`, JSON.stringify(modalConsistency, null, 2));
            
            // Schließe Modal (ESC oder Close-Button)
            await page.keyboard.press('Escape');
            await page.waitForTimeout(1000);
        }
        
        console.log('✅ Browser-Analyse abgeschlossen');
        
    } catch (error) {
        console.error('❌ Browser-Analyse Fehler:', error);
    } finally {
        await browser.close();
    }
}

// Führe Analyse durch
analyzeConsistencyValues().catch(console.error);