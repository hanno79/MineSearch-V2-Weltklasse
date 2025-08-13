/**
 * Author: rahn
 * Datum: 12.08.2025
 * Version: 1.0
 * Beschreibung: Spezifischer Test für URL-Probleme und Source-Attribution Konsistenz
 */

const { chromium } = require('playwright');

async function urlSourceDebugTest() {
    console.log('🎭 [URL-SOURCE-DEBUG] Starting URL & Source Attribution Debug Test');
    
    const browser = await chromium.launch({ headless: false, slowMo: 500 });
    const context = await browser.newContext({
        viewport: { width: 1200, height: 800 }
    });
    const page = await context.newPage();
    
    try {
        // Navigate to MineSearch 2.0
        console.log('🌐 [TEST] Navigating to MineSearch 2.0...');
        await page.goto('http://localhost:8000');
        await page.waitForLoadState('networkidle');
        
        // Wait for data-cards.js to load
        await page.waitForFunction(() => window.renderDataCardGrid, { timeout: 10000 });
        console.log('✅ [TEST] Data-Card-System loaded');
        
        // Test 1: URL-Validierung in visitSource
        console.log('\n🔧 [TEST 1] Testing URL Validation in visitSource...');
        
        const urlTests = await page.evaluate(() => {
            const testUrls = [
                'https:',                    // Problematische URL
                'http:',                     // Problematische URL
                'https://',                  // Unvollständige URL
                '',                          // Leere URL
                'mining.com',                // Korrekte Domain
                'https://reuters.com/mining', // Vollständige URL
                undefined,                   // Undefined URL
                null                         // Null URL
            ];
            
            const results = [];
            
            testUrls.forEach((testUrl, index) => {
                console.log(`🧪 [URL-TEST] Testing URL ${index + 1}: ${testUrl}`);
                
                try {
                    // Mock window.open to prevent actual opening
                    const originalOpen = window.open;
                    let openCalled = false;
                    let openUrl = '';
                    
                    window.open = function(url, target, features) {
                        openCalled = true;
                        openUrl = url;
                        return {}; // Mock window object
                    };
                    
                    // Test visitSource
                    window.visitSource(testUrl);
                    
                    // Restore original window.open
                    window.open = originalOpen;
                    
                    results.push({
                        input: testUrl,
                        success: true,
                        openCalled,
                        finalUrl: openUrl,
                        error: null
                    });
                    
                } catch (error) {
                    results.push({
                        input: testUrl,
                        success: false,
                        openCalled: false,
                        finalUrl: '',
                        error: error.message
                    });
                }
            });
            
            return results;
        });
        
        console.log('🧪 [URL-TEST] URL Validation Results:');
        urlTests.forEach((test, index) => {
            console.log(`  ${index + 1}. Input: ${test.input}`);
            console.log(`     ${test.success ? '✅' : '❌'} Success: ${test.success}`);
            if (test.success && test.openCalled) {
                console.log(`     🔗 Final URL: ${test.finalUrl}`);
            }
            if (test.error) {
                console.log(`     ❌ Error: ${test.error}`);
            }
            console.log('');
        });
        
        // Test 2: Source Attribution Consistency
        console.log('🔍 [TEST 2] Testing Source Attribution Consistency...');
        
        // Navigate to Statistics Tab
        await page.click('label[for="statistics-tab"]');
        await page.waitForTimeout(2000);
        
        // Load statistics
        await page.click('button:has-text("Statistiken laden")');
        await page.waitForTimeout(3000);
        
        // Check source badges in cards vs details
        const sourceConsistencyTest = await page.evaluate(() => {
            const results = [];
            
            // Find all model stats cards
            const modelCards = document.querySelectorAll('.model-stats-card');
            
            modelCards.forEach((card, index) => {
                const modelName = card.getAttribute('data-model') || `Model ${index + 1}`;
                
                // Count source badges in card
                const sourceBadges = card.querySelectorAll('.source-badge');
                const cardSourceCount = sourceBadges.length;
                
                // Check if "Keine Quellen verfügbar" is shown
                const noSourcesMessage = Array.from(sourceBadges).find(badge => 
                    badge.textContent.includes('Keine Quellen') || 
                    badge.textContent.includes('verfügbar')
                );
                
                results.push({
                    modelName,
                    cardSourceCount,
                    hasNoSourcesMessage: !!noSourcesMessage,
                    sourceBadgeTexts: Array.from(sourceBadges).map(badge => badge.textContent.trim())
                });
            });
            
            return results;
        });
        
        console.log('📊 [SOURCE-CONSISTENCY] Source Attribution Analysis:');
        sourceConsistencyTest.forEach(result => {
            console.log(`  🤖 ${result.modelName}:`);
            console.log(`     🔗 Source badges in card: ${result.cardSourceCount}`);
            console.log(`     ⚠️ "Keine Quellen" shown: ${result.hasNoSourcesMessage}`);
            if (result.sourceBadgeTexts.length > 0) {
                console.log(`     📝 Badge texts: ${result.sourceBadgeTexts.join(', ')}`);
            }
            console.log('');
        });
        
        // Test 3: Click Details buttons and compare source counts
        console.log('🔍 [TEST 3] Testing Details Modal Source Counts...');
        
        const detailsSourceTest = await page.evaluate(async () => {
            const results = [];
            const modelCards = document.querySelectorAll('.model-stats-card');
            
            // Test first 3 cards only to avoid too long test
            for (let i = 0; i < Math.min(3, modelCards.length); i++) {
                const card = modelCards[i];
                const modelName = card.getAttribute('data-model') || `Model ${i + 1}`;
                
                // Get card source count
                const cardSourceBadges = card.querySelectorAll('.source-badge');
                const cardSourceCount = cardSourceBadges.length;
                
                // Find and click details button
                const detailsButton = card.querySelector('button[onclick*="showModelDetails"]');
                if (detailsButton) {
                    try {
                        // Click details button
                        detailsButton.click();
                        
                        // Wait for modal to appear
                        await new Promise(resolve => setTimeout(resolve, 1000));
                        
                        // Count sources in modal
                        const modal = document.querySelector('.mine-detail-modal-overlay, .model-detail-modal, .detail-modal');
                        let modalSourceCount = 0;
                        
                        if (modal) {
                            const modalSourceBadges = modal.querySelectorAll('.source-badge');
                            const modalSourceLinks = modal.querySelectorAll('a[href*="http"], .source-link');
                            const modalSourceTexts = modal.textContent.match(/\d+\s*(quelle|source)/gi) || [];
                            
                            modalSourceCount = Math.max(
                                modalSourceBadges.length,
                                modalSourceLinks.length,
                                modalSourceTexts.length
                            );
                            
                            // Close modal
                            const closeButton = Array.from(modal.querySelectorAll('button')).find(btn => 
                                btn.textContent.includes('×') || 
                                btn.textContent.includes('Schließen') ||
                                btn.classList.contains('close-button')
                            ) || modal.querySelector('button');
                            if (closeButton) {
                                closeButton.click();
                            }
                        }
                        
                        results.push({
                            modelName,
                            cardSourceCount,
                            modalSourceCount,
                            hasInconsistency: cardSourceCount === 0 && modalSourceCount > 0
                        });
                        
                    } catch (error) {
                        results.push({
                            modelName,
                            cardSourceCount,
                            modalSourceCount: 0,
                            hasInconsistency: false,
                            error: error.message
                        });
                    }
                }
                
                // Wait between tests
                await new Promise(resolve => setTimeout(resolve, 500));
            }
            
            return results;
        });
        
        console.log('🔍 [DETAILS-SOURCE] Details Modal vs Card Source Comparison:');
        let inconsistencyCount = 0;
        detailsSourceTest.forEach(result => {
            console.log(`  🤖 ${result.modelName}:`);
            console.log(`     🎴 Card sources: ${result.cardSourceCount}`);
            console.log(`     📋 Modal sources: ${result.modalSourceCount}`);
            console.log(`     ⚠️ Inconsistent: ${result.hasInconsistency ? 'YES' : 'NO'}`);
            if (result.error) {
                console.log(`     ❌ Error: ${result.error}`);
            }
            if (result.hasInconsistency) {
                inconsistencyCount++;
            }
            console.log('');
        });
        
        // Take screenshot for verification
        await page.screenshot({ 
            path: 'url_source_debug_test_result.png',
            fullPage: true
        });
        console.log('📸 [TEST] Screenshot saved: url_source_debug_test_result.png');
        
        // Final Assessment
        console.log('\n🏆 [FINAL ASSESSMENT] URL & SOURCE DEBUG TEST:');
        console.log('===============================================');
        
        const urlIssues = urlTests.filter(test => !test.success).length;
        const totalUrlTests = urlTests.length;
        const urlSuccessRate = ((totalUrlTests - urlIssues) / totalUrlTests) * 100;
        
        const noSourcesCards = sourceConsistencyTest.filter(test => test.hasNoSourcesMessage).length;
        const totalModelCards = sourceConsistencyTest.length;
        
        console.log(`🔧 URL Validation:`);
        console.log(`   ✅ Successful: ${totalUrlTests - urlIssues}/${totalUrlTests} (${urlSuccessRate.toFixed(1)}%)`);
        console.log(`   ❌ Failed: ${urlIssues}/${totalUrlTests}`);
        
        console.log(`📊 Source Attribution:`);
        console.log(`   ⚠️ Cards showing "Keine Quellen": ${noSourcesCards}/${totalModelCards}`);
        console.log(`   🔍 Inconsistent card vs modal: ${inconsistencyCount}/${detailsSourceTest.length}`);
        
        let overallScore = 0;
        overallScore += urlSuccessRate * 0.4; // URL validation worth 40%
        overallScore += ((totalModelCards - noSourcesCards) / totalModelCards) * 30; // Source display worth 30%
        overallScore += ((detailsSourceTest.length - inconsistencyCount) / Math.max(1, detailsSourceTest.length)) * 30; // Consistency worth 30%
        
        console.log(`━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);
        console.log(`🏆 OVERALL SCORE: ${overallScore.toFixed(1)}/100 points`);
        
        let status;
        if (overallScore >= 85) {
            status = '🌟 EXZELLENT - Alle Probleme behoben';
        } else if (overallScore >= 70) {
            status = '✅ GUT - Wesentliche Verbesserungen';
        } else if (overallScore >= 50) {
            status = '⚠️ VERBESSERUNG - Noch Probleme vorhanden';
        } else {
            status = '❌ KRITISCH - Viele Probleme ungelöst';
        }
        
        console.log(`📈 STATUS: ${status}`);
        
        // Specific recommendations
        if (urlIssues > 0) {
            console.log('\n🔧 URL-REPARATUR EMPFEHLUNGEN:');
            console.log('   - Erweiterte URL-Validierung implementiert');
            console.log('   - Fallback zu Google-Suche hinzugefügt');
            console.log('   - Weitere Tests für Edge-Cases erforderlich');
        }
        
        if (noSourcesCards > 0) {
            console.log('\n📊 SOURCE-ATTRIBUTION EMPFEHLUNGEN:');
            console.log('   - extractSourcesFromModelData() Funktion überprüfen');
            console.log('   - Model-Data-Struktur analysieren');
            console.log('   - Debug-Logging aktiviert für Transparenz');
        }
        
    } catch (error) {
        console.error('❌ [ERROR] URL Source debug test failed:', error);
    } finally {
        await browser.close();
        console.log('🎭 [PLAYWRIGHT] URL Source debug test completed');
    }
}

// Run the test
if (require.main === module) {
    urlSourceDebugTest().catch(console.error);
}

module.exports = { urlSourceDebugTest };