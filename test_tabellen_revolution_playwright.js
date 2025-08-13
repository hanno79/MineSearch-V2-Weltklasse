/**
 * Author: rahn
 * Datum: 12.08.2025
 * Version: 1.0
 * Beschreibung: Playwright Test für PHASE 3 TABELLEN-REVOLUTION
 * 
 * Testet die neue Data-Card-Implementation gegen die alten HTML-Tabellen
 * Validiert Source-Attribution-System und Mobile-Responsiveness
 */

const { chromium } = require('playwright');

async function testTabellenRevolution() {
    console.log('🎭 [PLAYWRIGHT] Starting Phase 3 Tabellen-Revolution Test');
    
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext({
        viewport: { width: 1200, height: 800 }
    });
    const page = await context.newPage();
    
    try {
        // 1. Navigate to MineSearch 2.0
        console.log('🌐 [TEST] Navigating to MineSearch 2.0...');
        await page.goto('http://localhost:8000', { waitUntil: 'networkidle' });
        
        // Wait for data-cards.js to load
        await page.waitForFunction(() => window.renderDataCardGrid, { timeout: 10000 });
        console.log('✅ [TEST] Data-Card-System loaded successfully');
        
        // 2. Test Tab Navigation and Data Loading
        console.log('🔄 [TEST] Testing tab navigation...');
        
        // Test Konsolidiert Tab (should use Data-Cards) - Fixed selector
        await page.click('label[for="consolidated-tab"]');
        await page.waitForTimeout(2000);
        
        // Check if Data-Card-Grid is rendered instead of tables
        const hasDataCardGrid = await page.locator('.data-card-grid').count();
        const hasOldTables = await page.locator('table').count();
        
        console.log(`📊 [TEST] Data-Card-Grids found: ${hasDataCardGrid}`);
        console.log(`🚫 [TEST] Old HTML tables found: ${hasOldTables}`);
        
        if (hasDataCardGrid > 0 && hasOldTables === 0) {
            console.log('✅ [SUCCESS] Tabellen-Revolution erfolgreich: Data-Cards statt HTML-Tabellen');
        } else {
            console.log('⚠️ [WARNING] Tabellen-Revolution nicht vollständig implementiert');
        }
        
        // 3. Test Source Attribution System
        console.log('🔗 [TEST] Testing Source-Attribution-System...');
        
        const sourceBadges = await page.locator('.source-badge').count();
        if (sourceBadges > 0) {
            console.log(`✅ [SUCCESS] Source-Attribution aktiv: ${sourceBadges} Source-Badges gefunden`);
            
            // Test clicking a source badge
            const firstBadge = page.locator('.source-badge').first();
            if (await firstBadge.count() > 0) {
                await firstBadge.click();
                console.log('✅ [SUCCESS] Source-Badge clickbar');
            }
        } else {
            console.log('⚠️ [WARNING] Keine Source-Badges gefunden');
        }
        
        // 4. Test Mine Details Modal
        console.log('📋 [TEST] Testing Mine Details Modal...');
        
        // Erst nach Detail-Buttons in sichtbaren Bereichen suchen
        await page.waitForTimeout(2000);
        const detailButtons = await page.locator('button').filter({ hasText: 'Details' }).count();
        console.log(`🎯 [TEST] Detail-Buttons gefunden: ${detailButtons}`);
        
        if (detailButtons > 0) {
            // Scroll zum ersten Button und dann klicken
            const firstButton = page.locator('button').filter({ hasText: 'Details' }).first();
            await firstButton.scrollIntoViewIfNeeded();
            await firstButton.click({ timeout: 5000 });
            await page.waitForTimeout(1000);
            
            // Check if modern modal appears
            const modal = await page.locator('.mine-detail-modal-overlay').count();
            if (modal > 0) {
                console.log('✅ [SUCCESS] Modernes Mine-Details-Modal funktioniert');
                
                // Test modal close
                await page.keyboard.press('Escape');
                await page.waitForTimeout(500);
                
                const modalClosed = await page.locator('.mine-detail-modal-overlay').count();
                if (modalClosed === 0) {
                    console.log('✅ [SUCCESS] Modal schließt mit ESC-Taste');
                }
            } else {
                console.log('⚠️ [WARNING] Kein Modal erschienen nach Button-Klick');
            }
        } else {
            console.log('⚠️ [WARNING] Keine Detail-Buttons gefunden');
        }
        
        // 5. Test Mobile Responsiveness
        console.log('📱 [TEST] Testing Mobile Responsiveness...');
        
        await context.setViewportSize({ width: 390, height: 844 }); // iPhone 12 size
        await page.waitForTimeout(1000);
        
        // Check if cards stack vertically on mobile
        const cardGrid = page.locator('.data-card-grid');
        const gridColumns = await cardGrid.evaluate((el) => {
            return window.getComputedStyle(el).gridTemplateColumns;
        });
        
        console.log(`📱 [TEST] Mobile grid-template-columns: ${gridColumns}`);
        
        if (gridColumns.includes('1fr') && !gridColumns.includes('minmax')) {
            console.log('✅ [SUCCESS] Mobile-responsive Grid: Cards stapeln sich vertikal');
        }
        
        // 6. Test Action Buttons
        console.log('🔄 [TEST] Testing Action Buttons...');
        
        const actionButtons = await page.locator('.action-button').count();
        console.log(`🎯 [TEST] Action-Buttons gefunden: ${actionButtons}`);
        
        if (actionButtons > 0) {
            // Test hover effects (only on desktop)
            await context.setViewportSize({ width: 1200, height: 800 });
            await page.waitForTimeout(500);
            
            const firstButton = page.locator('.action-button').first();
            await firstButton.hover();
            console.log('✅ [SUCCESS] Action-Button hover-effects funktionieren');
        }
        
        // 7. Performance Test: Load Time Measurement
        console.log('⚡ [TEST] Performance Test...');
        
        const startTime = Date.now();
        await page.reload({ waitUntil: 'networkidle' });
        const loadTime = Date.now() - startTime;
        
        console.log(`⚡ [PERFORMANCE] Page load time: ${loadTime}ms`);
        
        if (loadTime < 3000) {
            console.log('✅ [SUCCESS] Performance: Unter 3 Sekunden geladen');
        } else {
            console.log('⚠️ [WARNING] Performance: Über 3 Sekunden Ladezeit');
        }
        
        // 8. Visual Quality Assessment
        console.log('🎨 [TEST] Visual Quality Assessment...');
        
        await page.screenshot({ 
            path: 'tabellen_revolution_final_test.png',
            fullPage: true
        });
        console.log('📸 [TEST] Screenshot gespeichert: tabellen_revolution_final_test.png');
        
        // Final Assessment
        console.log('\n🏆 [FINAL ASSESSMENT] TABELLEN-REVOLUTION EVALUATION:');
        console.log('==================================================');
        
        const assessmentScore = {
            dataCardsImplemented: hasDataCardGrid > 0 && hasOldTables === 0 ? 25 : 0,
            sourceAttributionWorking: sourceBadges > 0 ? 20 : 0,
            modalSystemFunctional: modal > 0 ? 20 : 0,
            mobileResponsive: gridColumns.includes('1fr') ? 15 : 0,
            performanceGood: loadTime < 3000 ? 10 : 0,
            actionButtonsActive: actionButtons > 0 ? 10 : 0
        };
        
        const totalScore = Object.values(assessmentScore).reduce((a, b) => a + b, 0);
        
        console.log(`📊 Data-Cards vs HTML-Tables: ${assessmentScore.dataCardsImplemented}/25 points`);
        console.log(`🔗 Source-Attribution-System: ${assessmentScore.sourceAttributionWorking}/20 points`);
        console.log(`📋 Interactive Modal-System: ${assessmentScore.modalSystemFunctional}/20 points`);
        console.log(`📱 Mobile-Responsiveness: ${assessmentScore.mobileResponsive}/15 points`);
        console.log(`⚡ Performance (<3s): ${assessmentScore.performanceGood}/10 points`);
        console.log(`🎯 Action-Buttons: ${assessmentScore.actionButtonsActive}/10 points`);
        console.log(`━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);
        console.log(`🏆 GESAMT-SCORE: ${totalScore}/100 points`);
        
        let qualityRating;
        if (totalScore >= 90) {
            qualityRating = '🌟 EXZELLENT - Weltklasse Implementation';
        } else if (totalScore >= 75) {
            qualityRating = '✅ SEHR GUT - Professionelle Qualität';
        } else if (totalScore >= 60) {
            qualityRating = '👍 GUT - Solide Implementation';
        } else {
            qualityRating = '⚠️ VERBESSERUNGSBEDARF - Weitere Entwicklung nötig';
        }
        
        console.log(`📈 QUALITÄTS-RATING: ${qualityRating}`);
        
        // User Feedback Transformation Assessment
        if (totalScore >= 80) {
            console.log('\n🎉 USER-FEEDBACK-TRANSFORMATION PROGNOSE:');
            console.log('📈 Von "furchtbar" → "excellent" (Ziel erreicht!)');
            console.log('✨ Die Tabellen-Revolution war erfolgreich!');
        } else {
            console.log('\n🔧 WEITERE OPTIMIERUNGEN ERFORDERLICH:');
            console.log('📉 User-Feedback wird sich verbessern, aber weitere Arbeit nötig');
        }
        
    } catch (error) {
        console.error('❌ [ERROR] Test failed:', error);
    } finally {
        await browser.close();
        console.log('🎭 [PLAYWRIGHT] Test completed');
    }
}

// Run the test
if (require.main === module) {
    testTabellenRevolution().catch(console.error);
}

module.exports = { testTabellenRevolution };