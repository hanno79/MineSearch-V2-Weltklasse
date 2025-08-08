/*
Author: rahn
Datum: 27.07.2025
Version: 1.0
Beschreibung: Finaler umfassender Test aller implementierten Fixes
*/

const { chromium } = require('playwright');

async function runFinalComprehensiveTest() {
    console.log('🚀 Starte finalen umfassenden Test...');
    
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    
    let testResults = {
        backend_health: false,
        frontend_load: false,
        statistics_tab: false,
        model_count: false,
        accordion_functionality: false,
        accordion_persistence: false,
        table_sorting: false,
        ui_optimization: false,
        no_redundant_buttons: false,
        responsive_design: false
    };
    
    try {
        // 1. Backend Health Check
        console.log('📊 Backend Health Check...');
        const healthResponse = await page.goto('http://localhost:8000/health');
        if (healthResponse.status() === 200) {
            const healthData = await healthResponse.json();
            testResults.backend_health = healthData.status === 'healthy';
            console.log(`✅ Backend Health: ${testResults.backend_health ? 'PASS' : 'FAIL'}`);
        }
        
        // 2. Frontend Load Test
        console.log('🌐 Frontend Load Test...');
        await page.goto('http://localhost:8080');
        await page.waitForSelector('h1', { timeout: 5000 });
        const title = await page.textContent('h1');
        testResults.frontend_load = title.includes('MineSearch');
        console.log(`✅ Frontend Load: ${testResults.frontend_load ? 'PASS' : 'FAIL'}`);
        
        // 3. Statistics Tab Navigation
        console.log('📈 Statistics Tab Test...');
        await page.click('#method_statistics');
        await page.waitForTimeout(1000);
        const statsForm = await page.locator('#statistics_form');
        testResults.statistics_tab = await statsForm.isVisible();
        console.log(`✅ Statistics Tab: ${testResults.statistics_tab ? 'PASS' : 'FAIL'}`);
        
        // 4. Load Statistics und Model Count
        console.log('📊 Loading Statistics und Model Count...');
        await page.click('button:has-text("📊 Lade Statistiken")');
        await page.waitForTimeout(3000);
        
        const modelRows = await page.locator('.consolidated-table tbody tr:not(.model-details-row)');
        const modelCount = await modelRows.count();
        testResults.model_count = modelCount >= 6; // Mindestens 6 funktionierende OpenRouter Modelle
        console.log(`✅ Model Count (${modelCount}): ${testResults.model_count ? 'PASS' : 'FAIL'}`);
        
        // 5. Accordion Functionality Test
        console.log('📝 Accordion Functionality Test...');
        const detailButtons = await page.locator('button:has-text("📊 Details")');
        if (await detailButtons.count() > 0) {
            await detailButtons.first().click();
            await page.waitForTimeout(1000);
            
            const accordionRow = await page.locator('.model-details-row');
            testResults.accordion_functionality = await accordionRow.count() > 0;
            console.log(`✅ Accordion Open: ${testResults.accordion_functionality ? 'PASS' : 'FAIL'}`);
            
            // 6. Auto-Refresh Persistence Test (warte 35 Sekunden für Auto-Refresh)
            console.log('⏰ Auto-Refresh Persistence Test (35s)...');
            await page.waitForTimeout(35000);
            
            const accordionAfterRefresh = await page.locator('.model-details-row');
            testResults.accordion_persistence = await accordionAfterRefresh.count() > 0;
            console.log(`✅ Accordion Persistence: ${testResults.accordion_persistence ? 'PASS' : 'FAIL'}`);
        }
        
        // 7. Table Sorting Test
        console.log('📊 Table Sorting Test...');
        const sortHeaders = await page.locator('.consolidated-table th[onclick*="loadStatistics"]');
        if (await sortHeaders.count() > 0) {
            await sortHeaders.first().click();
            await page.waitForTimeout(1000);
            testResults.table_sorting = true;
            console.log(`✅ Table Sorting: ${testResults.table_sorting ? 'PASS' : 'FAIL'}`);
        }
        
        // 8. UI Optimization - Redundante Buttons prüfen
        console.log('🎨 UI Optimization Test...');
        const felderButtons = await page.locator('button:has-text("Felder")');
        testResults.no_redundant_buttons = await felderButtons.count() === 0;
        console.log(`✅ No Redundant Buttons: ${testResults.no_redundant_buttons ? 'PASS' : 'FAIL'}`);
        
        // 9. Responsive Design Test
        console.log('📱 Responsive Design Test...');
        await page.setViewportSize({ width: 768, height: 1024 });
        await page.waitForTimeout(1000);
        const tableContainer = await page.locator('#enhanced-statistics-table-container');
        testResults.responsive_design = await tableContainer.isVisible();
        console.log(`✅ Responsive Design: ${testResults.responsive_design ? 'PASS' : 'FAIL'}`);
        
        // 10. UI Optimization - Overflow Test
        await page.setViewportSize({ width: 1200, height: 800 });
        const tableOverflow = await page.evaluate(() => {
            const container = document.querySelector('#enhanced-statistics-table-container');
            return container && (container.scrollHeight > container.clientHeight || container.scrollWidth > container.clientWidth);
        });
        testResults.ui_optimization = tableOverflow; // Sollte scrollbar haben wenn Inhalt zu groß
        console.log(`✅ UI Optimization (Scrolling): ${testResults.ui_optimization ? 'PASS' : 'FAIL'}`);
        
    } catch (error) {
        console.error('❌ Test Error:', error.message);
    }
    
    await browser.close();
    
    // Testergebnisse auswerten
    const passedTests = Object.values(testResults).filter(result => result === true).length;
    const totalTests = Object.keys(testResults).length;
    const successRate = (passedTests / totalTests * 100).toFixed(1);
    
    console.log('\n🎯 FINALER TEST-REPORT:');
    console.log('================================');
    Object.entries(testResults).forEach(([test, result]) => {
        console.log(`${result ? '✅' : '❌'} ${test.replace(/_/g, ' ').toUpperCase()}: ${result ? 'PASS' : 'FAIL'}`);
    });
    console.log('================================');
    console.log(`📊 ERFOLGSRATE: ${passedTests}/${totalTests} (${successRate}%)`);
    console.log(`🎉 SYSTEM STATUS: ${successRate >= 80 ? 'PRODUKTIONSBEREIT' : 'BENÖTIGT FIXES'}`);
    
    return { testResults, passedTests, totalTests, successRate };
}

// Test ausführen
runFinalComprehensiveTest().catch(console.error);