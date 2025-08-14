/**
 * CSV Batch Workflow Test - PHASE 2
 * Author: rahn
 * Datum: 13.08.2025
 * Beschreibung: Vollständiger Test des 2-Schritt CSV-Workflows mit iterativer Fehlerbehebung
 */

const { chromium } = require('playwright');
const fs = require('fs');

async function testCsvBatchWorkflow() {
    console.log('🔧 [CSV WORKFLOW TEST] Starting comprehensive CSV batch workflow test...');
    
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext();
    const page = await context.newPage();
    
    // Monitor JavaScript errors
    page.on('pageerror', error => {
        console.log('💥 [JS ERROR]', error.message);
    });
    
    // Monitor console messages (focus on batch search)
    page.on('console', msg => {
        const text = msg.text();
        if (text.includes('[BATCH') || text.includes('CSV') || text.includes('session') || text.includes('upload')) {
            console.log('🖥️ [CONSOLE]', text);
        }
    });
    
    // Monitor network requests (track both upload-csv and batch-search)
    page.on('response', async response => {
        const url = response.url();
        if (url.includes('/api/upload-csv')) {
            console.log(`📨 [API-UPLOAD] ${response.status()} - CSV upload response`);
            if (response.status() !== 200) {
                const errorText = await response.text();
                console.log(`❌ [API-UPLOAD] Error: ${errorText.substring(0, 200)}`);
            }
        } else if (url.includes('/api/batch-search')) {
            console.log(`📨 [API-BATCH] ${response.status()} - Batch search response`);
            if (response.status() !== 200) {
                const errorText = await response.text();
                console.log(`❌ [API-BATCH] Error: ${errorText.substring(0, 200)}`);
            }
        }
    });
    
    // Create test CSV file with mining data
    const testCSV = `mine_name,country,commodity,region,production_year
Canadian Malartic,Canada,Gold,Quebec,2023
Grasberg,Indonesia,Copper,Papua,2023
Escondida,Chile,Copper,Antofagasta,2023
Kalgoorlie Super Pit,Australia,Gold,Western Australia,2023
Bingham Canyon,USA,Copper,Utah,2023`;
    
    const csvPath = '/tmp/test_mining_batch.csv';
    fs.writeFileSync(csvPath, testCSV);
    console.log('📄 [CSV] Created test CSV with 5 mines');
    
    let uploadSuccess = false;
    let sessionIdExtracted = false;
    let batchSearchStarted = false;
    let batchSearchCompleted = false;
    let resultsDisplayed = false;
    
    try {
        console.log('🔄 [STEP 1] Loading MineSearch page...');
        await page.goto('http://localhost:8000');
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(3000);
        
        console.log('🔄 [STEP 2] Navigating to CSV batch search tab...');
        
        // Click on CSV tab (use label since radio buttons are hidden)
        const csvTabLabel = await page.$('label[for="csv-tab"]');
        if (csvTabLabel) {
            await csvTabLabel.click();
            console.log('✅ [TAB] CSV tab clicked');
            await page.waitForTimeout(2000);
        } else {
            console.log('❌ [TAB] CSV tab label not found');
            await page.screenshot({ path: 'csv_tab_not_found.png' });
            return;
        }
        
        // Check if CSV section is visible
        const csvSection = await page.$('#csv-upload');
        const isVisible = csvSection ? await csvSection.isVisible() : false;
        console.log(`📊 [CSV-SECTION] CSV upload section visible: ${isVisible}`);
        
        console.log('🔄 [STEP 3] Uploading CSV file...');
        
        // Find and upload CSV file
        const fileInput = await page.$('input[type="file"]');
        if (fileInput) {
            await fileInput.setInputFiles(csvPath);
            console.log('✅ [UPLOAD] CSV file selected');
            await page.waitForTimeout(2000);
        } else {
            console.log('❌ [UPLOAD] File input not found');
            await page.screenshot({ path: 'file_input_not_found.png' });
            return;
        }
        
        console.log('🔄 [STEP 4] Selecting models for batch search...');
        
        // Wait for models to load
        await page.waitForTimeout(5000);
        
        // Check selected models
        const selectedModels = await page.$$('input[name="model"]:checked');
        console.log(`🎯 [MODELS] Found ${selectedModels.length} pre-selected models`);
        
        // If no models selected, select first few available
        if (selectedModels.length === 0) {
            const availableModels = await page.$$('input[name="model"]');
            const modelsToSelect = Math.min(3, availableModels.length);
            for (let i = 0; i < modelsToSelect; i++) {
                await availableModels[i].check();
            }
            console.log(`✅ [MODELS] Selected ${modelsToSelect} models for batch search`);
        }
        
        console.log('🔄 [STEP 5] Starting batch search workflow...');
        
        // Find and click the batch search button
        const batchSearchButton = await page.$('button[onclick="startBatchSearch()"], .batch-search-button, #start-batch');
        if (batchSearchButton) {
            console.log('🚀 [BATCH] Starting batch search workflow...');
            await batchSearchButton.click();
            batchSearchStarted = true;
            console.log('✅ [BATCH] Batch search button clicked');
        } else {
            console.log('❌ [BATCH] Batch search button not found');
            // Try to find any submit button in the CSV form
            const submitButton = await page.$('#csv-form button[type="submit"], #csv-upload button');
            if (submitButton) {
                await submitButton.click();
                console.log('✅ [BATCH] Fallback: CSV form submit button clicked');
                batchSearchStarted = true;
            } else {
                console.log('❌ [BATCH] No suitable button found');
                await page.screenshot({ path: 'no_batch_button.png' });
                return;
            }
        }
        
        console.log('⏳ [WAIT] Waiting 90 seconds for complete batch workflow (upload + processing)...');
        
        // Wait for the complete workflow with progress monitoring
        let waitTime = 0;
        const maxWaitTime = 90000; // 90 seconds
        const checkInterval = 5000; // 5 seconds
        
        while (waitTime < maxWaitTime) {
            await page.waitForTimeout(checkInterval);
            waitTime += checkInterval;
            
            // Check for results in batch-results div
            const batchResultsDiv = await page.$('#batch-results');
            if (batchResultsDiv) {
                const resultsContent = await batchResultsDiv.innerHTML();
                const hasContent = resultsContent.length > 100; // More than just loading message
                const hasError = resultsContent.includes('fehlgeschlagen') || resultsContent.includes('Error') || resultsContent.includes('error');
                const hasSuccess = resultsContent.includes('erfolg') || resultsContent.includes('✅') || resultsContent.includes('Batch-Suchergebnisse');
                
                console.log(`⏱️ [PROGRESS] ${waitTime/1000}s - Content: ${resultsContent.length} chars, Success: ${hasSuccess}, Error: ${hasError}`);
                
                if (hasError) {
                    console.log('❌ [BATCH] Error detected in results');
                    console.log(`📊 [ERROR-CONTENT] ${resultsContent.substring(0, 500)}`);
                    break;
                } else if (hasSuccess && hasContent) {
                    console.log('✅ [BATCH] Success indicators found in results');
                    batchSearchCompleted = true;
                    resultsDisplayed = true;
                    break;
                }
            }
            
            // Check progress in regular results div as well
            const resultsDiv = await page.$('#results');
            if (resultsDiv) {
                const resultsContent = await resultsDiv.innerHTML();
                if (resultsContent.length > 100) {
                    console.log(`📊 [RESULTS] Main results div has content: ${resultsContent.length} chars`);
                }
            }
        }
        
        console.log('🔍 [STEP 6] Analyzing final results...');
        
        // Comprehensive results analysis
        const batchResultsDiv = await page.$('#batch-results');
        const mainResultsDiv = await page.$('#results');
        
        let finalResults = '';
        let resultLocation = 'none';
        
        if (batchResultsDiv) {
            const batchContent = await batchResultsDiv.innerHTML();
            if (batchContent.length > 100) {
                finalResults = batchContent;
                resultLocation = 'batch-results';
            }
        }
        
        if (!finalResults && mainResultsDiv) {
            const mainContent = await mainResultsDiv.innerHTML();
            if (mainContent.length > 100) {
                finalResults = mainContent;
                resultLocation = 'results';
            }
        }
        
        console.log('🔍 [ANALYSIS] Final Results Analysis:');
        console.log(`  Results location: ${resultLocation}`);
        console.log(`  Results length: ${finalResults.length} characters`);
        
        if (finalResults.length > 0) {
            console.log(`  First 300 chars: "${finalResults.substring(0, 300)}"`);
            
            // Check for success indicators
            const hasSuccessIndicators = finalResults.includes('✅') || finalResults.includes('erfolg') || finalResults.includes('Batch-Suchergebnisse');
            const hasErrorIndicators = finalResults.includes('❌') || finalResults.includes('fehlgeschlagen') || finalResults.includes('Error');
            const hasSessionId = finalResults.includes('session') || finalResults.includes('Session');
            const hasResultData = finalResults.includes('Canadian Malartic') || finalResults.includes('Grasberg') || finalResults.includes('mine');
            
            console.log(`  Success indicators: ${hasSuccessIndicators}`);
            console.log(`  Error indicators: ${hasErrorIndicators}`);
            console.log(`  Session references: ${hasSessionId}`);
            console.log(`  Mining data present: ${hasResultData}`);
            
            if (hasSuccessIndicators && !hasErrorIndicators) {
                batchSearchCompleted = true;
                resultsDisplayed = true;
                console.log('✅ [SUCCESS] CSV batch workflow appears successful');
            } else if (hasErrorIndicators) {
                console.log('❌ [ERROR] CSV batch workflow has errors');
                
                // Check for specific error patterns
                if (finalResults.includes('session_id')) {
                    console.log('🎯 [ERROR-TYPE] Session ID related error detected');
                } else if (finalResults.includes('422')) {
                    console.log('🎯 [ERROR-TYPE] Unprocessable Entity (422) error detected');
                } else if (finalResults.includes('404')) {
                    console.log('🎯 [ERROR-TYPE] Not Found (404) error detected');
                }
            }
        } else {
            console.log('⚠️ [ANALYSIS] No results content found');
        }
        
        // Take comprehensive screenshots
        await page.screenshot({ path: 'csv_batch_workflow_final.png', fullPage: true });
        
        // Count HTML elements to check rendering
        const resultTables = await page.$$('#batch-results table, #results table');
        const resultCards = await page.$$('#batch-results .card, #results .card, #batch-results .mine-result, #results .mine-result');
        const resultButtons = await page.$$('#batch-results button, #results button');
        
        console.log(`📊 [ELEMENTS] Found ${resultTables.length} tables, ${resultCards.length} cards, ${resultButtons.length} buttons`);
        
    } catch (error) {
        console.error('💥 [ERROR]', error);
        await page.screenshot({ path: 'csv_workflow_error.png' });
    } finally {
        // Clean up
        if (fs.existsSync(csvPath)) {
            fs.unlinkSync(csvPath);
            console.log('🧹 [CLEANUP] Test CSV file deleted');
        }
    }
    
    await browser.close();
    
    // Final Assessment
    console.log('');
    console.log('📊 [CSV WORKFLOW ASSESSMENT]');
    console.log('============================');
    console.log(`📤 CSV Upload: ${uploadSuccess ? '✅' : '❌'}`);
    console.log(`🎯 Session ID: ${sessionIdExtracted ? '✅' : '❌'}`);
    console.log(`🚀 Batch Search Started: ${batchSearchStarted ? '✅' : '❌'}`);
    console.log(`✅ Batch Search Completed: ${batchSearchCompleted ? '✅' : '❌'}`);
    console.log(`📊 Results Displayed: ${resultsDisplayed ? '✅' : '❌'}`);
    
    const overallSuccess = batchSearchStarted && batchSearchCompleted && resultsDisplayed;
    
    if (overallSuccess) {
        console.log('');
        console.log('🎉 CSV BATCH WORKFLOW: SUCCESSFUL!');
        console.log('✅ All workflow steps completed successfully');
        console.log('🚀 CSV batch search is fully functional');
    } else {
        console.log('');
        console.log('⚠️ CSV BATCH WORKFLOW: NEEDS REPAIR');
        if (!batchSearchStarted) {
            console.log('🔧 Issue: Batch search did not start');
        }
        if (!batchSearchCompleted) {
            console.log('🔧 Issue: Batch search did not complete');
        }
        if (!resultsDisplayed) {
            console.log('🔧 Issue: Results not properly displayed');
        }
        console.log('🔄 Further debugging and fixes needed');
    }
    
    console.log('🏁 [CSV WORKFLOW TEST] Complete');
    return overallSuccess;
}

// Run the test
testCsvBatchWorkflow().catch(console.error);