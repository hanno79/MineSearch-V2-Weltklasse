/**
 * CSV Batch Validation - PHASE 4.2
 * Author: rahn
 * Datum: 13.08.2025
 * Beschreibung: Test CSV upload → processing → results workflow
 */

const { chromium } = require('playwright');
const fs = require('fs');

async function csvBatchTest() {
    console.log('📊 [CSV BATCH TEST] Starting CSV batch search validation...');
    
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext();
    const page = await context.newPage();
    
    // Create a test CSV file
    const testCSV = `mine_name,country,commodity,region
Canadian Malartic,Canada,Gold,Quebec
Grasberg,Indonesia,Copper,Papua
Escondida,Chile,Copper,Antofagasta`;
    
    fs.writeFileSync('/tmp/test_mines.csv', testCSV);
    console.log('📄 [CSV] Created test CSV with 3 mines');
    
    let uploadCompleted = false;
    let batchStarted = false;
    
    // Monitor responses
    page.on('response', async response => {
        if (response.url().includes('/api/upload-csv')) {
            console.log(`📨 [UPLOAD] ${response.status()} - CSV upload response`);
            uploadCompleted = true;
        }
        if (response.url().includes('/api/batch-search')) {
            console.log(`📨 [BATCH] ${response.status()} - Batch search response`);
            batchStarted = true;
        }
    });
    
    // Monitor console logs
    page.on('console', msg => {
        const text = msg.text();
        if (text.includes('[BATCH]') || text.includes('CSV') || text.includes('upload')) {
            console.log(`🖥️ [FRONTEND] ${text}`);
        }
    });
    
    try {
        console.log('🔄 [STEP 1] Loading page and going to batch search tab...');
        await page.goto('http://localhost:8000');
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(3000);
        
        // Click on CSV/Batch Search tab label (radio buttons are hidden)
        await page.click('label[for="csv-tab"]');
        await page.waitForTimeout(1000);
        
        console.log('🔄 [STEP 2] Uploading test CSV file...');
        
        // Upload CSV file
        const fileInput = await page.$('input[type="file"]');
        if (fileInput) {
            await fileInput.setInputFiles('/tmp/test_mines.csv');
            console.log('✅ [CSV] File selected');
            
            // Submit the form by clicking the submit button
            const submitButton = await page.$('#start-batch');
            if (submitButton) {
                console.log('🔄 [CSV] Submitting form...');
                await submitButton.click();
                console.log('✅ [CSV] Form submitted');
            } else {
                console.log('❌ [CSV] Submit button not found');
                return;
            }
        } else {
            console.log('❌ [CSV] File input not found');
            return;
        }
        
        // Wait for upload processing and response
        await page.waitForTimeout(10000);
        
        if (uploadCompleted) {
            console.log('✅ [STEP 3] CSV upload completed');
            
            // Look for batch search interface
            const batchInterface = await page.$('.batch-search-interface');
            if (batchInterface) {
                console.log('✅ [UI] Batch search interface found');
                
                // Start batch search
                const batchButton = await page.$('.batch-search-button');
                if (batchButton) {
                    console.log('🔄 [STEP 4] Starting batch search...');
                    await batchButton.click();
                    
                    // Wait for batch processing
                    await page.waitForTimeout(30000);  // Wait longer for batch processing
                    
                    if (batchStarted) {
                        console.log('✅ [BATCH] Batch search started successfully');
                        
                        // Check results
                        const batchResults = await page.$('#batch-results');
                        if (batchResults) {
                            const resultsContent = await batchResults.textContent();
                            console.log('📊 [RESULTS] Batch results found:', resultsContent.substring(0, 100));
                            
                            // Count result rows
                            const resultRows = await page.$$('.mine-result-row, .model-result-card');
                            console.log(`📈 [ANALYSIS] Found ${resultRows.length} result rows/cards`);
                        } else {
                            console.log('⚠️ [RESULTS] No batch results element found');
                        }
                    } else {
                        console.log('❌ [BATCH] Batch search did not start');
                    }
                } else {
                    console.log('❌ [UI] Batch search button not found');
                }
            } else {
                console.log('❌ [UI] Batch search interface not found after upload');
            }
        } else {
            console.log('❌ [UPLOAD] CSV upload did not complete');
        }
        
        await page.screenshot({ path: 'csv_batch_test_result.png' });
        
    } catch (error) {
        console.error('💥 [ERROR]', error);
        await page.screenshot({ path: 'csv_batch_test_error.png' });
    }
    
    await browser.close();
    
    // Clean up
    fs.unlinkSync('/tmp/test_mines.csv');
    
    // Final Analysis
    console.log('\n📊 [CSV BATCH ANALYSIS]');
    console.log('=======================');
    console.log(`CSV Upload: ${uploadCompleted ? '✅' : '❌'}`);
    console.log(`Batch Search: ${batchStarted ? '✅' : '❌'}`);
    
    if (uploadCompleted && batchStarted) {
        console.log('🎉 CSV BATCH SYSTEM: WORKING');
        console.log('🚀 CSV batch search is functional!');
    } else {
        console.log('⚠️ CSV BATCH SYSTEM: NEEDS REPAIR');
        if (!uploadCompleted) {
            console.log('🔧 Issue: CSV upload not working');
        }
        if (!batchStarted) {
            console.log('🔧 Issue: Batch search not starting');
        }
    }
    
    console.log('🏁 [CSV BATCH TEST] Complete');
}

csvBatchTest().catch(console.error);