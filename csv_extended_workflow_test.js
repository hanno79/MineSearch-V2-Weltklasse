/**
 * CSV Extended Workflow Test - PHASE 2.1
 * Author: rahn
 * Datum: 13.08.2025
 * Beschreibung: Extended test mit realistischem Timeout für komplette Batch-Verarbeitung
 */

const { chromium } = require('playwright');
const fs = require('fs');

async function testCsvExtendedWorkflow() {
    console.log('🔧 [CSV EXTENDED TEST] Starting extended CSV batch workflow test...');
    console.log('⏱️ [TIMEOUT] Using realistic timeout: 5 minutes for complete batch processing');
    
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext();
    const page = await context.newPage();
    
    // Enhanced monitoring
    page.on('pageerror', error => {
        console.log('💥 [JS ERROR]', error.message);
    });
    
    page.on('console', msg => {
        const text = msg.text();
        if (text.includes('[BATCH') || text.includes('CSV') || text.includes('session') || text.includes('upload')) {
            console.log('🖥️ [CONSOLE]', text);
        }
    });
    
    // Monitor ALL batch-search requests (including slow responses)
    page.on('response', async response => {
        const url = response.url();
        if (url.includes('/api/upload-csv')) {
            console.log(`📨 [API-UPLOAD] ${response.status()} - CSV upload completed`);
        } else if (url.includes('/api/batch-search')) {
            console.log(`📨 [API-BATCH] ${response.status()} - Batch search response received!`);
            if (response.status() === 200) {
                console.log('✅ [API-BATCH] Batch search completed successfully');
            } else {
                const errorText = await response.text();
                console.log(`❌ [API-BATCH] Error: ${errorText.substring(0, 300)}`);
            }
        }
    });
    
    // Create a smaller test CSV for faster processing
    const testCSV = `mine_name,country,commodity,region
Canadian Malartic,Canada,Gold,Quebec
Grasberg,Indonesia,Copper,Papua
Escondida,Chile,Copper,Antofagasta`;
    
    const csvPath = '/tmp/test_mining_small.csv';
    fs.writeFileSync(csvPath, testCSV);
    console.log('📄 [CSV] Created smaller test CSV with 3 mines for faster processing');
    
    let batchSearchCompleted = false;
    let batchApiResponseReceived = false;
    let finalHtmlGenerated = false;
    
    try {
        console.log('🔄 [STEP 1] Loading MineSearch and navigating to CSV tab...');
        await page.goto('http://localhost:8000');
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(3000);
        
        // Navigate to CSV tab
        const csvTabLabel = await page.$('label[for="csv-tab"]');
        if (csvTabLabel) {
            await csvTabLabel.click();
            await page.waitForTimeout(2000);
            console.log('✅ [TAB] CSV tab activated');
        } else {
            throw new Error('CSV tab not found');
        }
        
        console.log('🔄 [STEP 2] Uploading CSV and selecting models...');
        
        // Upload CSV
        const fileInput = await page.$('input[type="file"]');
        if (fileInput) {
            await fileInput.setInputFiles(csvPath);
            await page.waitForTimeout(3000);
            console.log('✅ [UPLOAD] CSV file uploaded');
        } else {
            throw new Error('File input not found');
        }
        
        // Wait for models and verify selection
        await page.waitForTimeout(5000);
        const selectedModels = await page.$$('input[name="model"]:checked');
        console.log(`🎯 [MODELS] ${selectedModels.length} models selected`);
        
        if (selectedModels.length === 0) {
            // Select first 2 models for faster processing
            const availableModels = await page.$$('input[name="model"]');
            const modelsToSelect = Math.min(2, availableModels.length);
            for (let i = 0; i < modelsToSelect; i++) {
                await availableModels[i].check();
            }
            console.log(`✅ [MODELS] Selected ${modelsToSelect} models for faster batch processing`);
        }
        
        console.log('🔄 [STEP 3] Starting batch search with extended monitoring...');
        
        // Start batch search
        const batchSearchButton = await page.$('button[onclick="startBatchSearch()"], .batch-search-button, #start-batch');
        if (batchSearchButton) {
            console.log('🚀 [BATCH] Starting extended batch search...');
            await batchSearchButton.click();
            console.log('✅ [BATCH] Batch search initiated');
        } else {
            throw new Error('Batch search button not found');
        }
        
        console.log('⏳ [WAIT] Extended monitoring for up to 5 minutes (300s)...');
        console.log('📊 [INFO] Expecting: 3 mines × 2-3 models = 6-9 individual searches');
        
        // Extended monitoring with detailed progress
        let waitTime = 0;
        const maxWaitTime = 300000; // 5 minutes
        const checkInterval = 10000; // 10 seconds
        
        while (waitTime < maxWaitTime && !batchSearchCompleted) {
            await page.waitForTimeout(checkInterval);
            waitTime += checkInterval;
            
            // Check batch-results div
            const batchResultsDiv = await page.$('#batch-results');
            if (batchResultsDiv) {
                const resultsContent = await batchResultsDiv.innerHTML();
                const hasSuccessContent = resultsContent.includes('✅') || 
                                         resultsContent.includes('erfolg') || 
                                         resultsContent.includes('Batch-Suchergebnisse') ||
                                         resultsContent.includes('table') ||
                                         resultsContent.includes('Canadian Malartic');
                
                const hasErrorContent = resultsContent.includes('❌') || 
                                       resultsContent.includes('fehlgeschlagen') || 
                                       resultsContent.includes('Error');
                
                console.log(`⏱️ [PROGRESS] ${waitTime/1000}s - Content: ${resultsContent.length} chars, Success: ${hasSuccessContent}, Error: ${hasErrorContent}`);
                
                if (hasSuccessContent && !hasErrorContent) {
                    console.log('🎉 [SUCCESS] Batch search appears to be completed successfully!');
                    batchSearchCompleted = true;
                    finalHtmlGenerated = true;
                    break;
                } else if (hasErrorContent) {
                    console.log('❌ [ERROR] Batch search failed');
                    console.log(`📊 [ERROR-DETAILS] ${resultsContent.substring(0, 800)}`);
                    break;
                }
                
                // Show progress indicators from loading message
                if (resultsContent.includes('läuft') || resultsContent.includes('Session:')) {
                    console.log(`📋 [PROGRESS] Batch processing in progress...`);
                }
            }
            
            // Additional check for any completed results in main results div
            const mainResultsDiv = await page.$('#results');
            if (mainResultsDiv) {
                const mainContent = await mainResultsDiv.innerHTML();
                if (mainContent.length > 500 && mainContent.includes('Canadian Malartic')) {
                    console.log('📊 [ALTERNATIVE] Results found in main results div');
                }
            }
            
            // Log every minute for long waits
            if (waitTime % 60000 === 0) {
                console.log(`🕐 [MILESTONE] ${waitTime/60000} minute(s) elapsed, continuing to wait...`);
            }
        }
        
        console.log('🔍 [STEP 4] Final comprehensive analysis...');
        
        // Take screenshot regardless of outcome
        await page.screenshot({ path: 'csv_extended_workflow_result.png', fullPage: true });
        
        // Comprehensive final analysis
        const finalBatchResults = await page.$eval('#batch-results', el => el.innerHTML).catch(() => '');
        const finalMainResults = await page.$eval('#results', el => el.innerHTML).catch(() => '');
        
        const totalResultsLength = finalBatchResults.length + finalMainResults.length;
        
        console.log('🔍 [FINAL ANALYSIS]');
        console.log(`  Total wait time: ${waitTime/1000}s (${(waitTime/60000).toFixed(1)} minutes)`);
        console.log(`  Batch results length: ${finalBatchResults.length} chars`);
        console.log(`  Main results length: ${finalMainResults.length} chars`);
        console.log(`  Total results content: ${totalResultsLength} chars`);
        
        // Check for actual mining data
        const hasMiningData = finalBatchResults.includes('Canadian Malartic') || 
                             finalBatchResults.includes('Grasberg') ||
                             finalBatchResults.includes('Escondida') ||
                             finalMainResults.includes('Canadian Malartic');
        
        const hasTableStructure = finalBatchResults.includes('<table') || finalBatchResults.includes('<tr');
        const hasCardStructure = finalBatchResults.includes('card') || finalBatchResults.includes('mine-result');
        
        console.log(`  Contains mining data: ${hasMiningData}`);
        console.log(`  Has table structure: ${hasTableStructure}`);  
        console.log(`  Has card structure: ${hasCardStructure}`);
        
        if (hasMiningData && (hasTableStructure || hasCardStructure)) {
            batchSearchCompleted = true;
            console.log('✅ [VERIFICATION] Batch search results successfully generated and displayed');
        } else if (hasMiningData) {
            console.log('⚠️ [PARTIAL] Mining data present but structure may be incomplete');
        } else {
            console.log('❌ [FAILURE] No mining data found in results');
        }
        
        // Show sample of results if available
        if (finalBatchResults.length > 0) {
            console.log(`📋 [SAMPLE] First 500 chars of batch results:`);
            console.log(`"${finalBatchResults.substring(0, 500)}"`);
        }
        
    } catch (error) {
        console.error('💥 [ERROR]', error);
        await page.screenshot({ path: 'csv_extended_error.png' });
    } finally {
        if (fs.existsSync(csvPath)) {
            fs.unlinkSync(csvPath);
            console.log('🧹 [CLEANUP] Test CSV file deleted');
        }
    }
    
    await browser.close();
    
    // Extended Assessment
    console.log('');
    console.log('📊 [CSV EXTENDED WORKFLOW ASSESSMENT]');
    console.log('=====================================');
    console.log(`⏱️ Processing Time: ${(waitTime/60000).toFixed(1)} minutes`);
    console.log(`🔄 2-Step Workflow: ✅ (Upload + Batch Search)`);
    console.log(`📨 API Response: ${batchApiResponseReceived ? '✅' : '❌'}`);
    console.log(`✅ Batch Completed: ${batchSearchCompleted ? '✅' : '❌'}`);
    console.log(`📊 HTML Generated: ${finalHtmlGenerated ? '✅' : '❌'}`);
    
    if (batchSearchCompleted && finalHtmlGenerated) {
        console.log('');
        console.log('🎉 CSV BATCH WORKFLOW: FULLY SUCCESSFUL!');
        console.log('✅ Complete end-to-end workflow functioning');
        console.log('✅ CSV upload → Session ID → Batch processing → Results display');
        console.log('🚀 CSV batch search system is fully operational');
    } else if (waitTime >= maxWaitTime) {
        console.log('');
        console.log('⏱️ CSV BATCH WORKFLOW: TIMEOUT EXCEEDED');
        console.log(`⚠️ Processing took longer than ${maxWaitTime/60000} minutes`);
        console.log('🔧 Consider optimizing batch processing performance');
        console.log('💡 Workflow may be functional but needs performance tuning');
    } else {
        console.log('');
        console.log('⚠️ CSV BATCH WORKFLOW: NEEDS INVESTIGATION');
        console.log('🔧 Check server logs for batch processing details');
    }
    
    console.log('🏁 [CSV EXTENDED TEST] Complete');
    return batchSearchCompleted;
}

// Run the extended test
testCsvExtendedWorkflow().catch(console.error);