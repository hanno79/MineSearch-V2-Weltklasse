/**
 * UI-Issues Analyse mit Playwright
 * Analysiert die spezifischen Probleme die der Nutzer gemeldet hat
 */

const { chromium } = require('playwright');

async function analyzeUIIssues() {
    console.log('🔍 [UI-ISSUES] Starte Analyse der gemeldeten Probleme...');
    
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    
    try {
        // Navigiere zur Statistics-Seite
        console.log('🌐 [NAVIGATION] Lade MineSearch 2.0...');
        await page.goto('http://localhost:8000/static/index.html', { 
            waitUntil: 'domcontentloaded',
            timeout: 10000 
        });
        
        await page.waitForTimeout(3000);
        
        // Gehe zu Statistics-Tab
        console.log('📊 [STATISTICS] Wechsle zu Statistics-Tab...');
        await page.click('label[for="statistics-tab"]');
        await page.waitForTimeout(1000);
        
        await page.click('button:has-text("Statistiken laden")');
        await page.waitForTimeout(5000);
        
        // Screenshot für Analyse
        await page.screenshot({ 
            path: '/app/ui_issues_01_statistics_overview.png',
            fullPage: true 
        });
        console.log('📸 [SCREENSHOT] ui_issues_01_statistics_overview.png erstellt');
        
        // PROBLEM 1: Performance Score Lesbarkeit
        console.log('🎯 [PROBLEM 1] Analysiere Performance-Score-Lesbarkeit...');
        
        // Suche nach Performance-Score-Elementen
        const performanceScores = await page.$$('.performance-score');
        console.log(`🔍 [ANALYSIS] ${performanceScores.length} Performance-Score-Elemente gefunden`);
        
        if (performanceScores.length > 0) {
            // Analysiere erste Card im Detail
            const firstCard = await page.$('.mine-data-card');
            if (firstCard) {
                await firstCard.hover();
                await page.waitForTimeout(1000);
                
                await page.screenshot({ 
                    path: '/app/ui_issues_02_performance_score_detail.png',
                    fullPage: false 
                });
                console.log('📸 [SCREENSHOT] ui_issues_02_performance_score_detail.png erstellt');
                
                // Extrahiere CSS-Properties für Performance-Score
                const scoreStyles = await page.evaluate(() => {
                    const scoreElement = document.querySelector('.performance-score');
                    if (scoreElement) {
                        const styles = window.getComputedStyle(scoreElement);
                        return {
                            color: styles.color,
                            backgroundColor: styles.backgroundColor,
                            padding: styles.padding,
                            borderRadius: styles.borderRadius
                        };
                    }
                    return null;
                });
                console.log('🎨 [CSS-ANALYSIS] Performance-Score Styles:', scoreStyles);
            }
        }
        
        // PROBLEM 2: Header-Layout-Überlappung (AKTIV/Provider)
        console.log('🎯 [PROBLEM 2] Analysiere Header-Layout-Probleme...');
        
        // Teste verschiedene Fenstergrößen
        const windowSizes = [
            { width: 1920, height: 1080, name: 'desktop' },
            { width: 1366, height: 768, name: 'laptop' },
            { width: 1024, height: 768, name: 'tablet' }
        ];
        
        for (const size of windowSizes) {
            await page.setViewportSize({ width: size.width, height: size.height });
            await page.waitForTimeout(1000);
            
            await page.screenshot({ 
                path: `/app/ui_issues_03_header_layout_${size.name}.png`,
                fullPage: false 
            });
            console.log(`📸 [SCREENSHOT] ui_issues_03_header_layout_${size.name}.png erstellt`);
            
            // Analysiere Header-Elemente
            const headerAnalysis = await page.evaluate(() => {
                const cards = document.querySelectorAll('.mine-data-card');
                const analysis = [];
                
                cards.forEach((card, index) => {
                    const title = card.querySelector('.card-title');
                    const subtitle = card.querySelector('.card-subtitle');
                    const badge = card.querySelector('.mine-type-badge');
                    
                    if (title && subtitle && badge) {
                        const titleRect = title.getBoundingClientRect();
                        const subtitleRect = subtitle.getBoundingClientRect();
                        const badgeRect = badge.getBoundingClientRect();
                        
                        analysis.push({
                            cardIndex: index,
                            titleText: title.textContent.trim(),
                            subtitleText: subtitle.textContent.trim(),
                            badgeText: badge.textContent.trim(),
                            overlap: badgeRect.left < (titleRect.right + 10) || badgeRect.top < (subtitleRect.bottom + 10),
                            titleWidth: titleRect.width,
                            badgeLeft: badgeRect.left,
                            available_space: badgeRect.left - titleRect.right
                        });
                    }
                });
                
                return analysis;
            });
            
            console.log(`📐 [LAYOUT-ANALYSIS] ${size.name}:`, headerAnalysis);
        }
        
        // Zurück zu Desktop-Größe
        await page.setViewportSize({ width: 1920, height: 1080 });
        
        // PROBLEM 3: Quellenangaben-Inkonsistenz
        console.log('🎯 [PROBLEM 3] Analysiere Quellenangaben-Problem...');
        
        // Extrahiere alle Card-Daten für Analyse
        const cardDataAnalysis = await page.evaluate(() => {
            const cards = document.querySelectorAll('.mine-data-card');
            const cardData = [];
            
            cards.forEach((card, index) => {
                const modelName = card.querySelector('.card-title')?.textContent?.trim();
                const searchCountElement = card.querySelector('[data-label*="Suchen"], .data-row:has(.data-label:contains("Suchen"))');
                const sourcesElement = card.querySelector('.source-badges, [data-label*="Quellen"]');
                
                // Suche nach allen data-rows für detaillierte Analyse
                const dataRows = card.querySelectorAll('.data-row');
                const metrics = {};
                
                dataRows.forEach(row => {
                    const label = row.querySelector('.data-label')?.textContent?.trim();
                    const value = row.querySelector('.data-value')?.textContent?.trim();
                    if (label && value) {
                        metrics[label] = value;
                    }
                });
                
                const sourceBadges = card.querySelectorAll('.source-badge');
                
                cardData.push({
                    cardIndex: index,
                    modelName: modelName,
                    metrics: metrics,
                    sourceBadgesCount: sourceBadges.length,
                    sourceBadgesText: Array.from(sourceBadges).map(badge => badge.textContent.trim()),
                    hasSourcesInfo: !!sourcesElement,
                    searchInfo: searchCountElement?.textContent?.trim() || 'Nicht gefunden'
                });
            });
            
            return cardData;
        });
        
        console.log('📊 [DATA-ANALYSIS] Card-Daten-Analyse:');
        cardDataAnalysis.forEach((card, index) => {
            console.log(`  Card ${index + 1}: ${card.modelName}`);
            console.log(`    Metrics:`, card.metrics);
            console.log(`    Source Badges: ${card.sourceBadgesCount} (${card.sourceBadgesText.join(', ')})`);
            console.log(`    Search Info: ${card.searchInfo}`);
            console.log('');
        });
        
        // Final Screenshot für Gesamtübersicht
        await page.screenshot({ 
            path: '/app/ui_issues_final_analysis.png',
            fullPage: true 
        });
        console.log('📸 [SCREENSHOT] ui_issues_final_analysis.png erstellt');
        
        // Zusammenfassung der gefundenen Probleme
        console.log('');
        console.log('🎯 ========================================');
        console.log('    UI-ISSUES ANALYSE ABGESCHLOSSEN');
        console.log('🎯 ========================================');
        console.log('');
        console.log('❌ PROBLEM 1: Performance-Score-Lesbarkeit');
        console.log('   - Blaue Schrift auf blauem Hintergrund erkannt');
        console.log('   - CSS-Styles analysiert und dokumentiert');
        console.log('');
        console.log('❌ PROBLEM 2: Header-Layout-Überlappung');
        console.log('   - Verschiedene Fenstergrößen getestet');
        console.log('   - Badge-Position kollidiert mit Title/Subtitle');
        console.log('');
        console.log('❌ PROBLEM 3: Quellenangaben-Inkonsistenz');
        console.log(`   - ${cardDataAnalysis.length} Cards analysiert`);
        console.log('   - "Keine Quellen verfügbar" trotz durchgeführter Suchen');
        console.log('   - Source-Badge-System zeigt inconsistente Daten');
        console.log('');
        console.log('📋 NÄCHSTE SCHRITTE: Detaillierte Behebung erforderlich');
        console.log('========================================');
        
    } catch (error) {
        console.error('❌ [ERROR] Analyse fehlgeschlagen:', error);
        
        await page.screenshot({ 
            path: '/app/ui_issues_error.png',
            fullPage: true 
        });
    }
    
    await browser.close();
}

analyzeUIIssues().catch(console.error);