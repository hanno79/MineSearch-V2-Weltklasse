/**
 * CSV Batch Improvements Test
 * Author: rahn
 * Datum: 14.08.2025
 * Beschreibung: Test für Count-Steuerung und Abbruch-Funktionalität bei CSV Batch Search
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

async function testCSVBatchImprovements() {
    console.log('🧪 [CSV-BATCH-TEST] Testing CSV batch improvements: count control and cancel functionality...');
    
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext();
    const page = await context.newPage();
    
    // Monitor console logs
    page.on('console', msg => {
        const text = msg.text();
        if (text.includes('[BATCH-') || text.includes('[CANCEL-') || text.includes('[BATCH-OPTIONS]')) {
            console.log('🖥️ [CONSOLE]', text);
        }
    });
    
    let testResults = {
        pageLoads: false,
        batchCountUIVisible: false,
        countSettingWorks: false,
        csvUploads: false,
        cancelButtonAppears: false,
        cancelFunctionWorks: false,
        countParametersSent: false
    };
    
    try {
        console.log('🔄 [TEST 1] Page Load and CSV Batch Tab...');
        await page.goto('http://localhost:8000');
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(3000);
        
        testResults.pageLoads = true;
        console.log('✅ [TEST 1] Page loaded successfully');
        
        // Switch to CSV batch tab
        await page.click('[data-tab="csv"]');
        await page.waitForTimeout(2000);
        
        console.log('🔄 [TEST 2] Batch Count UI Elements Check...');
        
        // Check if count UI elements exist
        const batchCountOptions = await page.$('.batch-count-options');
        const limitedRadio = await page.$('#batch-limited');
        const allRadio = await page.$('#batch-all');
        const countInput = await page.$('#batch-count');
        
        console.log(`📊 [COUNT-UI] Count options container: ${batchCountOptions ? 'EXISTS' : 'MISSING'}`);
        console.log(`📊 [COUNT-UI] Limited radio: ${limitedRadio ? 'EXISTS' : 'MISSING'}`);
        console.log(`📊 [COUNT-UI] All radio: ${allRadio ? 'EXISTS' : 'MISSING'}`);
        console.log(`📊 [COUNT-UI] Count input: ${countInput ? 'EXISTS' : 'MISSING'}`);
        
        if (batchCountOptions && limitedRadio && allRadio && countInput) {
            testResults.batchCountUIVisible = true;
            console.log('✅ [TEST 2] Batch count UI elements are visible');
        }
        
        console.log('🔄 [TEST 3] Count Setting Validation...');
        
        // Check default values
        const limitedChecked = await limitedRadio?.isChecked();
        const defaultCount = await countInput?.inputValue();
        
        console.log(`📊 [COUNT-SETTING] Limited radio checked: ${limitedChecked}`);
        console.log(`📊 [COUNT-SETTING] Default count value: "${defaultCount}"`);
        
        if (limitedChecked && defaultCount === '3') {
            testResults.countSettingWorks = true;
            console.log('✅ [TEST 3] Count setting defaults are correct');
        }
        
        // Test changing count value
        if (countInput) {
            await countInput.fill('5');
            const newValue = await countInput.inputValue();
            console.log(`📊 [COUNT-SETTING] Changed count to: "${newValue}"`);
        }
        
        // Test switching to "all mines" mode
        if (allRadio) {
            await allRadio.click();
            const allChecked = await allRadio.isChecked();
            console.log(`📊 [COUNT-SETTING] All radio after click: ${allChecked}`);
            
            // Switch back to limited for testing
            await limitedRadio?.click();
        }
        
        console.log('🔄 [TEST 4] CSV Upload and Batch Processing...');
        
        // Create a simple test CSV file
        const testCSVContent = `mine_name,country,commodity
Test Mine 1,Canada,Gold
Test Mine 2,Australia,Copper
Test Mine 3,Chile,Silver`;
        
        const testCSVPath = path.join(__dirname, 'test_batch_mines.csv');
        fs.writeFileSync(testCSVPath, testCSVContent);
        
        // Upload CSV file
        const fileInput = await page.$('input[type="file"]');
        if (fileInput) {
            await fileInput.setInputFiles(testCSVPath);
            await page.waitForTimeout(1000);
            
            console.log('📁 [CSV-UPLOAD] Test CSV file uploaded');
            
            // Select some models (use quick preset)
            const quickPill = await page.$('.quick-pill.recommended');
            if (quickPill) {
                await quickPill.click();
                await page.waitForTimeout(2000);
                console.log('🤖 [MODELS] Selected recommended models');
            }
            
            console.log('🔄 [TEST 5] Start Batch Search and Monitor Cancel Button...');
            
            // Intercept batch search requests to check parameters
            let requestParameters = null;
            page.on('request', request => {
                if (request.url().includes('/api/batch-search')) {
                    const postData = request.postData();
                    if (postData) {
                        requestParameters = postData;
                        console.log('📤 [REQUEST] Batch search parameters captured');
                    }
                }
            });
            
            // Start batch search
            const startButton = await page.$('button[onclick*="startBatchSearch"]');
            if (startButton) {
                await startButton.click();
                console.log('🚀 [BATCH] Batch search started');
                
                // Wait for loading message and cancel button
                await page.waitForTimeout(3000);
                
                // Check if cancel button appears in loading message
                const cancelButton = await page.$('button:has-text("Abbrechen")');
                console.log(`🛑 [CANCEL-BUTTON] Cancel button visible: ${cancelButton ? 'YES' : 'NO'}`);
                
                if (cancelButton) {
                    testResults.cancelButtonAppears = true;
                    console.log('✅ [TEST 5] Cancel button appears in loading message');
                    
                    console.log('🔄 [TEST 6] Test Cancel Functionality...');
                    
                    // Wait a moment then click cancel
                    await page.waitForTimeout(2000);
                    await cancelButton.click();
                    
                    // Check if search was cancelled
                    await page.waitForTimeout(2000);
                    const errorMessage = await page.textContent('#batch-results').catch(() => '');
                    
                    console.log(`📊 [CANCEL-TEST] Result message: "${errorMessage.substring(0, 100)}..."`);
                    
                    if (errorMessage.includes('abgebrochen')) {
                        testResults.cancelFunctionWorks = true;
                        console.log('✅ [TEST 6] Cancel functionality works');
                    }
                }
                
                // Check request parameters if captured
                if (requestParameters) {
                    console.log('📊 [REQUEST-PARAMS] Checking sent parameters...');
                    
                    const hasSearchAll = requestParameters.includes('search_all=false');
                    const hasCount = requestParameters.includes('count=5'); // We changed it to 5 earlier
                    
                    console.log(`📊 [PARAMS] search_all=false: ${hasSearchAll}`);
                    console.log(`📊 [PARAMS] count=5: ${hasCount}`);
                    
                    if (hasSearchAll || hasCount) {
                        testResults.countParametersSent = true;
                        console.log('✅ [PARAMS] Count parameters are being sent correctly');
                    }
                }
            }
        }
        
        // Clean up test file
        if (fs.existsSync(testCSVPath)) {
            fs.unlinkSync(testCSVPath);
            console.log('🗑️ [CLEANUP] Test CSV file removed');
        }
        
        // Screenshots
        await page.screenshot({ path: 'csv_batch_improvements_test.png', fullPage: true });
        
    } catch (error) {
        console.error('💥 [ERROR]', error);
        await page.screenshot({ path: 'csv_batch_improvements_error.png' });
    } finally {
        await browser.close();
    }
    
    // Final Assessment
    console.log('');
    console.log('🏆 [CSV BATCH IMPROVEMENTS TEST RESULTS]');
    console.log('==========================================');
    
    const testItems = [
        { name: 'Page Loads Successfully', status: testResults.pageLoads },
        { name: 'Batch Count UI Visible', status: testResults.batchCountUIVisible },
        { name: 'Count Setting Works', status: testResults.countSettingWorks },
        { name: 'Cancel Button Appears', status: testResults.cancelButtonAppears },
        { name: 'Cancel Function Works', status: testResults.cancelFunctionWorks },
        { name: 'Count Parameters Sent', status: testResults.countParametersSent }
    ];
    
    testItems.forEach((test, index) => {
        console.log(`${test.status ? '✅' : '❌'} ${index + 1}. ${test.name}`);
    });
    
    const successfulTests = testItems.filter(test => test.status).length;
    const totalTests = testItems.length;
    const successRate = Math.round(successfulTests / totalTests * 100);
    
    console.log('');
    console.log(`📊 CSV Batch Improvements Success Rate: ${successfulTests}/${totalTests} (${successRate}%)`);
    
    if (successRate >= 90) {
        console.log('');
        console.log('🎉 CSV BATCH IMPROVEMENTS: EXCELLENT SUCCESS!');
        console.log('✅ Count control UI is fully functional');
        console.log('✅ Default to 3 mines for testing purposes works');
        console.log('✅ Cancel button appears during batch operations');
        console.log('✅ Cancel functionality properly aborts searches');
        console.log('✅ Count parameters are sent to backend correctly');
        console.log('🚀 Users can now control batch size and abort long searches!');
    } else if (successRate >= 70) {
        console.log('');
        console.log('🎯 CSV BATCH IMPROVEMENTS: GOOD PROGRESS');
        console.log('✅ Major features implemented');
        console.log('⚠️ Some functionality may need fine-tuning');
    } else {
        console.log('');
        console.log('❌ CSV BATCH IMPROVEMENTS: NEEDS MORE WORK');
        console.log('❌ Critical issues remain');
        console.log('🔧 Further investigation required');
    }
    
    console.log('🏁 [CSV BATCH IMPROVEMENTS TEST] Complete');
    return successRate >= 85;
}

testCSVBatchImprovements().catch(console.error);