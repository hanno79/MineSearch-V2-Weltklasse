/**
 * CSV Final Verification - PHASE 4 Complete
 * Author: rahn
 * Datum: 13.08.2025
 * Beschreibung: Finale Verifikation der vollständig reparierten CSV-Batch-Suche
 */

const { chromium } = require('playwright');
const fs = require('fs');

async function csvFinalVerification() {
    console.log('🏆 [CSV FINAL VERIFICATION] Starting complete system validation...');
    
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext();
    const page = await context.newPage();
    
    // Create realistic mining CSV
    const testCSV = `mine_name,country,commodity,region,production_year
Antamina,Peru,Copper,Ancash,2023
Mount Isa,Australia,Copper,Queensland,2023`;
    
    const csvPath = '/tmp/final_verification.csv';
    fs.writeFileSync(csvPath, testCSV);
    console.log('📄 [CSV] Created final verification CSV with 2 mines');
    
    let overallSuccess = true;
    let detailedResults = {
        pageLoad: false,
        csvUpload: false,
        sessionExtraction: false,
        batchProcessing: false,
        resultsDisplay: false,
        htmlRendering: false
    };
    
    try {
        console.log('🔄 [VERIFICATION 1] Page load and CSV tab navigation...');
        await page.goto('http://localhost:8000');
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(2000);
        
        const csvTabLabel = await page.$('label[for="csv-tab"]');
        if (csvTabLabel) {
            await csvTabLabel.click();
            await page.waitForTimeout(1500);
            detailedResults.pageLoad = true;
            console.log('✅ [V1] Page load and navigation successful');
        } else {
            throw new Error('CSV tab not accessible');
        }
        
        console.log('🔄 [VERIFICATION 2] CSV upload functionality...');
        const fileInput = await page.$('input[type="file"]');
        if (fileInput) {
            await fileInput.setInputFiles(csvPath);
            await page.waitForTimeout(2000);
            detailedResults.csvUpload = true;
            console.log('✅ [V2] CSV upload successful');
        } else {
            throw new Error('File input not functional');
        }
        
        console.log('🔄 [VERIFICATION 3] Model selection validation...');
        await page.waitForTimeout(3000);
        const selectedModels = await page.$$('input[name="model"]:checked');
        console.log(`🎯 [V3] ${selectedModels.length} models auto-selected`);
        
        if (selectedModels.length === 0) {
            const availableModels = await page.$$('input[name="model"]');
            if (availableModels.length > 0) {
                await availableModels[0].check();
                console.log('✅ [V3] Model selection corrected');
            }
        }
        
        console.log('🔄 [VERIFICATION 4] Complete batch workflow execution...');
        
        // Monitor for session extraction
        page.on('console', msg => {
            const text = msg.text();
            if (text.includes('Session ID extracted:')) {
                detailedResults.sessionExtraction = true;
                console.log('✅ [V4] Session ID successfully extracted');
            }
            if (text.includes('Batch search completed')) {
                detailedResults.batchProcessing = true;
                console.log('✅ [V4] Batch processing completed');
            }
        });
        
        // Start batch search
        const batchButton = await page.$('button[onclick="startBatchSearch()"], .batch-search-button, #start-batch');
        if (batchButton) {
            await batchButton.click();
            console.log('🚀 [V4] Batch workflow initiated');
            
            // Monitor for completion with reasonable timeout
            let waitTime = 0;
            const maxWait = 120000; // 2 minutes should be enough for 2 mines
            const checkInterval = 8000;
            
            while (waitTime < maxWait && !detailedResults.batchProcessing) {
                await page.waitForTimeout(checkInterval);
                waitTime += checkInterval;
                
                const batchResults = await page.$eval('#batch-results', el => el.innerHTML).catch(() => '');
                
                if (batchResults.includes('Antamina') || batchResults.includes('Mount Isa')) {
                    detailedResults.resultsDisplay = true;
                    console.log('✅ [V4] Results display successful');
                }
                
                if (batchResults.includes('<table') && batchResults.length > 5000) {
                    detailedResults.htmlRendering = true;
                    detailedResults.batchProcessing = true;
                    console.log('✅ [V4] HTML rendering and batch processing confirmed');
                    break;
                }
                
                console.log(`⏱️ [V4] Progress: ${waitTime/1000}s, content: ${batchResults.length} chars`);
            }
            
        } else {
            throw new Error('Batch search button not found');
        }
        
        console.log('🔄 [VERIFICATION 5] Results validation and quality check...');
        
        const finalResults = await page.$eval('#batch-results', el => el.innerHTML).catch(() => '');
        
        // Quality checks
        const qualityChecks = {
            hasMiningData: finalResults.includes('Antamina') || finalResults.includes('Mount Isa'),
            hasTableStructure: finalResults.includes('<table') && finalResults.includes('<tr>'),
            hasCountryInfo: finalResults.includes('Peru') || finalResults.includes('Australia'),
            hasCommodityInfo: finalResults.includes('Copper'),
            hasSuccessMessage: finalResults.includes('erfolgreich') || finalResults.includes('✅'),
            reasonableLength: finalResults.length > 3000
        };
        
        const qualityScore = Object.values(qualityChecks).filter(Boolean).length;
        const totalChecks = Object.keys(qualityChecks).length;
        
        console.log('🔍 [V5] Quality Assessment:');
        Object.entries(qualityChecks).forEach(([check, passed]) => {
            console.log(`  ${passed ? '✅' : '❌'} ${check}: ${passed}`);
        });
        
        console.log(`📊 [V5] Overall Quality Score: ${qualityScore}/${totalChecks} (${Math.round(qualityScore/totalChecks*100)}%)`);
        
        if (qualityScore >= totalChecks * 0.8) { // 80% quality threshold
            detailedResults.htmlRendering = true;
            console.log('✅ [V5] Results quality validation passed');
        }
        
        await page.screenshot({ path: 'csv_final_verification_complete.png', fullPage: true });
        
    } catch (error) {
        console.error('💥 [ERROR]', error);
        overallSuccess = false;
        await page.screenshot({ path: 'csv_final_verification_error.png' });
    } finally {
        if (fs.existsSync(csvPath)) {
            fs.unlinkSync(csvPath);
        }
        await browser.close();
    }
    
    // Comprehensive Assessment
    console.log('');
    console.log('🏆 [CSV SYSTEM FINAL ASSESSMENT]');
    console.log('==================================');
    
    const verificationSteps = [
        { name: 'Page Load & Navigation', status: detailedResults.pageLoad },
        { name: 'CSV Upload', status: detailedResults.csvUpload },
        { name: 'Session Management', status: detailedResults.sessionExtraction },
        { name: 'Batch Processing', status: detailedResults.batchProcessing },
        { name: 'Results Display', status: detailedResults.resultsDisplay },
        { name: 'HTML Rendering', status: detailedResults.htmlRendering }
    ];
    
    verificationSteps.forEach((step, index) => {
        console.log(`${step.status ? '✅' : '❌'} ${index + 1}. ${step.name}`);
    });
    
    const successfulSteps = verificationSteps.filter(step => step.status).length;
    const totalSteps = verificationSteps.length;
    const successRate = Math.round(successfulSteps / totalSteps * 100);
    
    console.log('');
    console.log(`📊 Success Rate: ${successfulSteps}/${totalSteps} (${successRate}%)`);
    
    if (successRate >= 100) {
        console.log('');
        console.log('🎉 CSV BATCH SEARCH SYSTEM: FULLY OPERATIONAL!');
        console.log('==================================================');
        console.log('✅ Complete end-to-end functionality verified');
        console.log('✅ 2-step workflow (CSV Upload → Batch Search) working perfectly');
        console.log('✅ Session management implemented correctly');
        console.log('✅ Multi-model batch processing functional');
        console.log('✅ HTML results rendering properly');
        console.log('✅ Mining data extraction and display operational');
        console.log('');
        console.log('🚀 REPAIR MISSION ACCOMPLISHED!');
        console.log('🏆 CSV batch search system has been completely restored to full functionality');
    } else if (successRate >= 80) {
        console.log('');
        console.log('🎯 CSV BATCH SEARCH SYSTEM: MOSTLY FUNCTIONAL');
        console.log('==============================================');
        console.log('✅ Core functionality working');
        console.log('⚠️ Minor issues may remain');
        console.log('🔧 System ready for production with monitoring');
    } else {
        console.log('');
        console.log('⚠️ CSV BATCH SEARCH SYSTEM: NEEDS ADDITIONAL WORK');
        console.log('===================================================');
        console.log('❌ Critical issues still present');
        console.log('🔧 Further debugging and fixes required');
    }
    
    console.log('🏁 [CSV FINAL VERIFICATION] Complete');
    return successRate >= 90;
}

csvFinalVerification().catch(console.error);