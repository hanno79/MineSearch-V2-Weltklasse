/**
 * Author: rahn
 * Datum: 12.08.2025
 * Version: 1.0
 * Beschreibung: Direkter Data-Card-Test ohne komplexe Navigation
 * 
 * Testet ob renderDataCardGrid() funktioniert und Source-Attribution vorhanden ist
 */

const { chromium } = require('playwright');

async function directDataCardTest() {
    console.log('🎭 [DIRECT-TEST] Starting Direct Data-Card Test');
    
    const browser = await chromium.launch({ headless: false, slowMo: 1000 });
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
        console.log('✅ [TEST] Data-Card-System loaded successfully');
        
        // Test if renderDataCardGrid function exists
        const hasRenderFunction = await page.evaluate(() => {
            return typeof window.renderDataCardGrid === 'function';
        });
        console.log(`📊 [TEST] renderDataCardGrid function: ${hasRenderFunction ? '✅ Available' : '❌ Missing'}`);
        
        // Test if Source-Attribution functions exist
        const hasSourceFunctions = await page.evaluate(() => {
            return {
                generateSourceBadges: typeof window.generateSourceBadges === 'function',
                showMineDetails: typeof window.showMineDetails === 'function',
                exportMineData: typeof window.exportMineData === 'function',
                addToFavorites: typeof window.addToFavorites === 'function'
            };
        });
        
        console.log('🔗 [TEST] Source-Attribution Functions:');
        Object.entries(hasSourceFunctions).forEach(([func, exists]) => {
            console.log(`  ${exists ? '✅' : '❌'} ${func}`);
        });
        
        // Test direct Data-Card rendering
        console.log('🎨 [TEST] Testing direct Data-Card rendering...');
        
        const testResult = await page.evaluate(() => {
            // Create test container
            const container = document.createElement('div');
            container.id = 'test-container';
            document.body.appendChild(container);
            
            // Test mine data
            const testMineData = [
                {
                    mine_name: 'Test Gold Mine',
                    best_values: {
                        country: 'Australia',
                        mine_type: 'Open Pit Gold',
                        status: 'Active',
                        production_per_year: '1.2M oz',
                        ownership: 'Test Mining Corp'
                    },
                    source_summary: {
                        total_unique_sources: 5,
                        sources_by_domain: {
                            'mining.com': { count: 2, sample_url: 'https://mining.com/test' },
                            'reuters.com': { count: 3, sample_url: 'https://reuters.com/test' }
                        }
                    }
                }
            ];
            
            try {
                // Call renderDataCardGrid
                window.renderDataCardGrid(testMineData, container, 'consolidated');
                
                // Check if cards were rendered
                const dataCards = container.querySelectorAll('.mine-data-card');
                const sourceBadges = container.querySelectorAll('.source-badge');
                const actionButtons = container.querySelectorAll('.action-button');
                
                return {
                    success: true,
                    cardsRendered: dataCards.length,
                    sourceBadgesRendered: sourceBadges.length,
                    actionButtonsRendered: actionButtons.length,
                    hasCardGrid: container.querySelector('.data-card-grid') !== null,
                    hasSourceBadges: sourceBadges.length > 0
                };
            } catch (error) {
                return {
                    success: false,
                    error: error.message
                };
            }
        });
        
        if (testResult.success) {
            console.log('✅ [SUCCESS] Direct Data-Card rendering works!');
            console.log(`📊 [RESULT] Cards rendered: ${testResult.cardsRendered}`);
            console.log(`🔗 [RESULT] Source badges: ${testResult.sourceBadgesRendered}`);
            console.log(`🎯 [RESULT] Action buttons: ${testResult.actionButtonsRendered}`);
            console.log(`🎨 [RESULT] Has card grid: ${testResult.hasCardGrid ? '✅' : '❌'}`);
            console.log(`📚 [RESULT] Has source badges: ${testResult.hasSourceBadges ? '✅' : '❌'}`);
        } else {
            console.log('❌ [ERROR] Direct Data-Card rendering failed:', testResult.error);
        }
        
        // Test Modal System
        console.log('📋 [TEST] Testing Modal System...');
        
        const modalTest = await page.evaluate(() => {
            try {
                // Test modal functions exist
                const modalFunctions = {
                    showMineDetails: typeof window.showMineDetails === 'function',
                    closeMineModal: typeof window.closeMineModal === 'function',
                    generateDetailedModalContent: typeof window.generateDetailedModalContent === 'function'
                };
                
                return {
                    success: true,
                    functions: modalFunctions,
                    allPresent: Object.values(modalFunctions).every(f => f)
                };
            } catch (error) {
                return {
                    success: false,
                    error: error.message
                };
            }
        });
        
        if (modalTest.success) {
            console.log('📋 [MODAL] Modal functions check:');
            Object.entries(modalTest.functions).forEach(([func, exists]) => {
                console.log(`  ${exists ? '✅' : '❌'} ${func}`);
            });
            console.log(`🏆 [MODAL] All modal functions present: ${modalTest.allPresent ? '✅' : '❌'}`);
        }
        
        // Screenshot for verification
        await page.screenshot({ 
            path: 'direct_datacard_test_result.png',
            fullPage: true
        });
        console.log('📸 [TEST] Screenshot saved: direct_datacard_test_result.png');
        
        // Final assessment
        console.log('\n🏆 [FINAL ASSESSMENT] DIRECT DATA-CARD TEST:');
        console.log('============================================');
        
        const score = {
            renderFunctionExists: hasRenderFunction ? 25 : 0,
            sourceFunctionsExist: Object.values(hasSourceFunctions).every(f => f) ? 20 : 0,
            cardsRenderCorrectly: testResult.success && testResult.cardsRendered > 0 ? 25 : 0,
            sourceBadgesWork: testResult.success && testResult.hasSourceBadges ? 15 : 0,
            modalSystemReady: modalTest.success && modalTest.allPresent ? 15 : 0
        };
        
        const totalScore = Object.values(score).reduce((a, b) => a + b, 0);
        
        console.log(`📊 renderDataCardGrid Function: ${score.renderFunctionExists}/25 points`);
        console.log(`🔗 Source-Attribution Functions: ${score.sourceFunctionsExist}/20 points`);
        console.log(`🎨 Cards Render Correctly: ${score.cardsRenderCorrectly}/25 points`);
        console.log(`📚 Source Badges Working: ${score.sourceBadgesWork}/15 points`);
        console.log(`📋 Modal System Ready: ${score.modalSystemReady}/15 points`);
        console.log(`━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);
        console.log(`🏆 TOTAL SCORE: ${totalScore}/100 points`);
        
        let implementationStatus;
        if (totalScore >= 90) {
            implementationStatus = '🌟 EXZELLENT - Vollständig implementiert';
        } else if (totalScore >= 75) {
            implementationStatus = '✅ SEHR GUT - Erfolgreich implementiert';
        } else if (totalScore >= 60) {
            implementationStatus = '👍 GUT - Größtenteils implementiert';
        } else {
            implementationStatus = '⚠️ UNVOLLSTÄNDIG - Weitere Arbeit nötig';
        }
        
        console.log(`📈 IMPLEMENTATION STATUS: ${implementationStatus}`);
        
        // Tabellen-Revolution Assessment
        if (totalScore >= 80) {
            console.log('\n🎉 TABELLEN-REVOLUTION STATUS:');
            console.log('✅ Data-Card-System ist implementiert und funktionsfähig');
            console.log('✅ Source-Attribution-System ist bereit');
            console.log('✅ Modal-System ist vorbereitet');
            console.log('🚀 Bereit für User-Feedback-Transformation: "hässlich" → "excellent"');
        } else {
            console.log('\n🔧 WEITERE ARBEIT ERFORDERLICH:');
            console.log('⚠️ Einige Komponenten sind noch nicht vollständig implementiert');
        }
        
    } catch (error) {
        console.error('❌ [ERROR] Direct test failed:', error);
    } finally {
        await browser.close();
        console.log('🎭 [PLAYWRIGHT] Direct test completed');
    }
}

// Run the test
if (require.main === module) {
    directDataCardTest().catch(console.error);
}

module.exports = { directDataCardTest };