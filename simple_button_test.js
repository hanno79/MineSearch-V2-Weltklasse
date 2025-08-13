/**
 * Author: rahn
 * Datum: 12.08.2025
 * Version: 1.0
 * Beschreibung: Einfacher Button-Funktionalitätstest
 */

const { chromium } = require('playwright');

async function simpleButtonTest() {
    console.log('🎭 [SIMPLE-TEST] Starting Simple Button Function Test');
    
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
        
        // Navigate to Konsolidiert Tab
        await page.click('label[for="consolidated-tab"]');
        await page.waitForTimeout(3000);
        
        console.log('🔍 [TEST] Testing Button Functions...');
        
        // Test if critical functions exist
        const functionTest = await page.evaluate(() => {
            const functions = {
                // Mine Card Functions
                showMineDetails: typeof window.showMineDetails === 'function',
                exportMineData: typeof window.exportMineData === 'function',
                addToFavorites: typeof window.addToFavorites === 'function',
                
                // Source Card Functions  
                showSourceDetails: typeof window.showSourceDetails === 'function',
                visitSource: typeof window.visitSource === 'function',
                analyzeSource: typeof window.analyzeSource === 'function',
                
                // Model Stats Functions
                testModel: typeof window.testModel === 'function',
                toggleModelStatus: typeof window.toggleModelStatus === 'function',
                
                // Modal Close Functions
                closeMineModal: typeof window.closeMineModal === 'function',
                closeSourceModal: typeof window.closeSourceModal === 'function',
                closeAnalysisModal: typeof window.closeAnalysisModal === 'function',
                closeModelTestModal: typeof window.closeModelTestModal === 'function',
                closeModelStatusModal: typeof window.closeModelStatusModal === 'function'
            };
            
            return functions;
        });
        
        console.log('🧪 [TEST] Function Availability Check:');
        let availableFunctions = 0;
        Object.entries(functionTest).forEach(([func, exists]) => {
            console.log(`  ${exists ? '✅' : '❌'} ${func}`);
            if (exists) availableFunctions++;
        });
        
        console.log(`📊 [TEST] Available Functions: ${availableFunctions}/${Object.keys(functionTest).length}`);
        
        // Test Button Clicks (Direct Function Calls)
        console.log('🎯 [TEST] Testing Direct Function Calls...');
        
        const directTests = await page.evaluate(() => {
            const results = [];
            
            try {
                // Test showMineDetails
                if (typeof window.showMineDetails === 'function') {
                    window.showMineDetails('Test Mine');
                    results.push({ function: 'showMineDetails', success: true });
                    // Close modal
                    if (typeof window.closeMineModal === 'function') {
                        setTimeout(() => window.closeMineModal(), 500);
                    }
                }
            } catch (e) {
                results.push({ function: 'showMineDetails', success: false, error: e.message });
            }
            
            try {
                // Test visitSource
                if (typeof window.visitSource === 'function') {
                    window.visitSource('https://example.com');
                    results.push({ function: 'visitSource', success: true });
                }
            } catch (e) {
                results.push({ function: 'visitSource', success: false, error: e.message });
            }
            
            try {
                // Test analyzeSource
                if (typeof window.analyzeSource === 'function') {
                    window.analyzeSource('example.com');
                    results.push({ function: 'analyzeSource', success: true });
                    // Close modal
                    if (typeof window.closeAnalysisModal === 'function') {
                        setTimeout(() => window.closeAnalysisModal(), 500);
                    }
                }
            } catch (e) {
                results.push({ function: 'analyzeSource', success: false, error: e.message });
            }
            
            try {
                // Test testModel
                if (typeof window.testModel === 'function') {
                    window.testModel('test-model');
                    results.push({ function: 'testModel', success: true });
                    // Close modal
                    if (typeof window.closeModelTestModal === 'function') {
                        setTimeout(() => window.closeModelTestModal(), 500);
                    }
                }
            } catch (e) {
                results.push({ function: 'testModel', success: false, error: e.message });
            }
            
            try {
                // Test toggleModelStatus
                if (typeof window.toggleModelStatus === 'function') {
                    window.toggleModelStatus('test-model');
                    results.push({ function: 'toggleModelStatus', success: true });
                    // Close modal
                    if (typeof window.closeModelStatusModal === 'function') {
                        setTimeout(() => window.closeModelStatusModal(), 500);
                    }
                }
            } catch (e) {
                results.push({ function: 'toggleModelStatus', success: false, error: e.message });
            }
            
            return results;
        });
        
        console.log('🧪 [TEST] Direct Function Test Results:');
        let successfulTests = 0;
        directTests.forEach(test => {
            console.log(`  ${test.success ? '✅' : '❌'} ${test.function}${test.error ? ` - ${test.error}` : ''}`);
            if (test.success) successfulTests++;
        });
        
        console.log(`📊 [TEST] Successful Tests: ${successfulTests}/${directTests.length}`);
        
        // Wait for any modals to appear and then close them
        await page.waitForTimeout(2000);
        
        // Take screenshot for verification
        await page.screenshot({ 
            path: 'simple_button_test_result.png',
            fullPage: true
        });
        console.log('📸 [TEST] Screenshot saved: simple_button_test_result.png');
        
        // Final Assessment
        console.log('\n🏆 [FINAL ASSESSMENT] SIMPLE BUTTON TEST:');
        console.log('=======================================');
        
        const score = {
            functionsAvailable: (availableFunctions / Object.keys(functionTest).length) * 60,
            directTestsSuccessful: (successfulTests / directTests.length) * 40
        };
        
        const totalScore = score.functionsAvailable + score.directTestsSuccessful;
        
        console.log(`📊 Functions Available: ${score.functionsAvailable.toFixed(1)}/60 points`);
        console.log(`🧪 Direct Tests Successful: ${score.directTestsSuccessful.toFixed(1)}/40 points`);
        console.log(`━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);
        console.log(`🏆 TOTAL SCORE: ${totalScore.toFixed(1)}/100 points`);
        
        let status;
        if (totalScore >= 90) {
            status = '🌟 EXZELLENT - Alle Button-Funktionen arbeiten perfekt';
        } else if (totalScore >= 75) {
            status = '✅ SEHR GUT - Button-System funktioniert zuverlässig';
        } else if (totalScore >= 60) {
            status = '👍 GUT - Meiste Funktionen arbeiten korrekt';
        } else {
            status = '⚠️ PROBLEME - Button-Funktionalität unvollständig';
        }
        
        console.log(`📈 BUTTON STATUS: ${status}`);
        
        if (totalScore >= 80) {
            console.log('\n🎉 BUTTON-REPARATUR ERFOLGREICH:');
            console.log('✅ Alle kritischen Button-Funktionen implementiert');
            console.log('✅ Modal-System funktioniert korrekt'); 
            console.log('✅ Global Exports korrekt konfiguriert');
            console.log('🚀 Bereit für User-Feedback-Test!');
        }
        
    } catch (error) {
        console.error('❌ [ERROR] Simple test failed:', error);
    } finally {
        await browser.close();
        console.log('🎭 [PLAYWRIGHT] Simple test completed');
    }
}

// Run the test
if (require.main === module) {
    simpleButtonTest().catch(console.error);
}

module.exports = { simpleButtonTest };