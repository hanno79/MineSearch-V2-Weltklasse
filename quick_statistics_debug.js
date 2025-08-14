/**
 * Quick Statistics Debug Test
 * Author: rahn  
 * Datum: 14.08.2025
 */

const { chromium } = require('playwright');

async function debugStatisticsTab() {
    console.log('🔍 [DEBUG] Testing Statistics Tab Load...');
    
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    
    // Monitor console messages
    page.on('console', msg => {
        console.log(`🌐 [BROWSER] ${msg.type()}: ${msg.text()}`);
    });
    
    await page.goto('http://localhost:8000');
    await page.waitForTimeout(3000);
    
    // Click Statistics tab
    console.log('📊 [DEBUG] Clicking Statistics tab...');
    await page.click('a[data-tab="statistics"]');
    await page.waitForTimeout(2000);
    
    // Check if loadStatistics function exists
    const hasLoadStats = await page.evaluate(() => {
        return typeof window.loadStatistics === 'function';
    });
    console.log(`✅ [DEBUG] loadStatistics exists: ${hasLoadStats}`);
    
    // Check if renderDataCardGrid exists  
    const hasRenderCards = await page.evaluate(() => {
        return typeof window.renderDataCardGrid === 'function';
    });
    console.log(`✅ [DEBUG] renderDataCardGrid exists: ${hasRenderCards}`);
    
    // Manually trigger loadStatistics
    console.log('📊 [DEBUG] Manually triggering loadStatistics...');
    await page.evaluate(() => {
        if (window.loadStatistics) {
            window.loadStatistics().catch(console.error);
        }
    });
    
    await page.waitForTimeout(5000);
    
    // Check if container has content
    const containerContent = await page.textContent('#model-statistics-table-container');
    console.log(`📊 [DEBUG] Container content: "${containerContent}"`);
    
    // Check if cards exist
    const cardCount = await page.$$eval('.model-card, .statistics-card, .data-card', cards => cards.length);
    console.log(`📊 [DEBUG] Found ${cardCount} statistics cards`);
    
    // Take screenshot
    await page.screenshot({ 
        path: 'statistics_debug_final.png', 
        fullPage: true 
    });
    
    await browser.close();
}

debugStatisticsTab().catch(console.error);