/**
 * Manual CSV Batch Test
 * Author: rahn  
 * Datum: 14.08.2025
 * Beschreibung: Interaktiver Test für CSV Batch Improvements
 */

const { chromium } = require('playwright');

async function manualCSVBatchTest() {
    console.log('🧪 [MANUAL-TEST] Interactive CSV Batch Test mit Count und Cancel...');
    
    const browser = await chromium.launch({ 
        headless: false,
        slowMo: 1000  // Slow down for visual inspection
    });
    const context = await browser.newContext();
    const page = await context.newPage();
    
    // Monitor console messages from the page
    page.on('console', msg => {
        const text = msg.text();
        if (text.includes('[BATCH-') || text.includes('[CANCEL-') || text.includes('AbortController')) {
            console.log('🖥️ [PAGE-CONSOLE]', text);
        }
    });
    
    try {
        console.log('📍 [STEP 1] Loading page and navigating to CSV Batch...');
        await page.goto('http://localhost:8000');
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(3000);
        
        // Click CSV batch tab
        console.log('📍 [STEP 2] Switching to CSV Batch tab...');
        await page.click('[data-tab="csv"]');
        await page.waitForTimeout(2000);
        
        // Screenshot the batch options
        await page.screenshot({ path: 'batch_options_ui.png' });
        console.log('📸 Screenshot saved: batch_options_ui.png');
        
        // Check batch count options
        console.log('📍 [STEP 3] Checking count control UI...');
        const limitedRadio = await page.$('#batch-limited');
        const allRadio = await page.$('#batch-all');
        const countInput = await page.$('#batch-count');
        
        console.log(`✅ Limited radio exists: ${limitedRadio ? 'YES' : 'NO'}`);
        console.log(`✅ All radio exists: ${allRadio ? 'YES' : 'NO'}`);
        console.log(`✅ Count input exists: ${countInput ? 'YES' : 'NO'}`);
        
        if (countInput) {
            const currentValue = await countInput.inputValue();
            console.log(`✅ Default count value: ${currentValue}`);
            
            // Change count to 2 for faster testing
            await countInput.fill('2');
            const newValue = await countInput.inputValue();
            console.log(`✅ Changed count to: ${newValue}`);
        }
        
        // Upload test CSV
        console.log('📍 [STEP 4] Creating and uploading test CSV...');
        const testCSV = `mine_name,country,commodity
Eleonore Mine,Canada,Gold
Canadian Malartic,Canada,Gold`;
        
        const fs = require('fs');
        const path = require('path');
        const testCSVPath = path.join(__dirname, 'test_manual.csv');
        fs.writeFileSync(testCSVPath, testCSV);
        
        const fileInput = await page.$('input[type="file"]');
        await fileInput.setInputFiles(testCSVPath);
        await page.waitForTimeout(1000);
        
        // Select models using quick preset
        console.log('📍 [STEP 5] Selecting models...');
        const quickPill = await page.$('.quick-pill.recommended');
        if (quickPill) {
            await quickPill.click();
            await page.waitForTimeout(2000);
        }
        
        console.log('📍 [STEP 6] Starting batch search...');
        const startButton = await page.$('button[onclick*="startBatchSearch"]');
        
        if (startButton) {
            console.log('🚀 Starting batch search - watch for Cancel button!');
            await startButton.click();
            
            // Wait and check for cancel button every second
            for (let i = 0; i < 10; i++) {
                await page.waitForTimeout(1000);
                
                const cancelButton = await page.$('button:has-text("Abbrechen")');
                const loadingDiv = await page.$('#batch-results');
                
                if (loadingDiv) {
                    const content = await loadingDiv.textContent();
                    console.log(`📊 [${i+1}s] Loading content: "${content.substring(0, 50)}..."`);
                }
                
                if (cancelButton) {
                    console.log('🛑 [FOUND] Cancel button is visible!');
                    
                    if (i > 2) { // Wait at least 3 seconds before canceling
                        console.log('🛑 [TEST] Clicking cancel button...');
                        await cancelButton.click();
                        await page.waitForTimeout(2000);
                        
                        const finalContent = await loadingDiv?.textContent();
                        console.log(`📊 [RESULT] Final content: "${finalContent?.substring(0, 100)}..."`);
                        
                        if (finalContent?.includes('abgebrochen')) {
                            console.log('✅ [SUCCESS] Cancel functionality works!');
                        } else {
                            console.log('❌ [FAIL] Cancel didn\'t work as expected');
                        }
                        break;
                    }
                } else {
                    console.log(`⏳ [${i+1}s] Cancel button not yet visible...`);
                }
            }
        }
        
        // Clean up
        fs.unlinkSync(testCSVPath);
        
        // Final screenshot
        await page.screenshot({ path: 'manual_test_final.png', fullPage: true });
        console.log('📸 Final screenshot saved: manual_test_final.png');
        
        console.log('');
        console.log('🏁 [MANUAL TEST] Complete - Check the screenshots!');
        console.log('✅ Count control UI should be visible');  
        console.log('✅ Cancel button should appear during batch processing');
        console.log('✅ Cancel function should abort the search');
        
    } catch (error) {
        console.error('💥 [ERROR]', error);
        await page.screenshot({ path: 'manual_test_error.png' });
    } finally {
        // Keep browser open for manual inspection
        console.log('🔍 [MANUAL] Browser kept open for inspection - press Ctrl+C to close');
        // await browser.close(); // Commented out to keep open
    }
}

manualCSVBatchTest().catch(console.error);