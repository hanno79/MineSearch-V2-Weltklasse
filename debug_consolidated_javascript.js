/**
 * Author: rahn
 * Datum: 10.08.2025
 * Version: 1.0
 * Beschreibung: Debug Test für JavaScript Tab-System
 */

const { chromium } = require('playwright');

async function debugConsolidatedJS() {
    const browser = await chromium.launch();
    const page = await browser.newPage();
    
    console.log('🔍 JAVASCRIPT DEBUG TEST');
    console.log('========================\n');
    
    // Collect all console messages
    const messages = [];
    page.on('console', msg => {
        const text = msg.text();
        if (text.includes('TAB-AUTOLOADER') || text.includes('CONSOLIDATED')) {
            messages.push(`${msg.type()}: ${text}`);
        }
    });
    
    try {
        await page.goto('http://localhost:8000', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(2000);
        
        console.log('✅ Seite geladen, wechsle zu Konsolidiert-Tab...');
        
        // Click consolidated tab and wait for processing
        await page.click('label[for="consolidated-tab"]');
        await page.waitForTimeout(5000); // More time for debug output
        
        console.log('\n📝 JavaScript Console Messages:');
        messages.forEach(msg => console.log(`  ${msg}`));
        
        // Check if container has correct class
        const containerClass = await page.getAttribute('.container', 'class');
        console.log(`\n🎨 Container CSS-Klassen: ${containerClass}`);
        
        // Check if loadConsolidatedResults function exists
        const functionExists = await page.evaluate(() => {
            return typeof loadConsolidatedResults === 'function';
        });
        console.log(`📋 loadConsolidatedResults function exists: ${functionExists ? '✅' : '❌'}`);
        
        // Check form visibility with computed style
        const formComputedStyle = await page.evaluate(() => {
            const element = document.getElementById('consolidated_form');
            if (element) {
                const style = window.getComputedStyle(element);
                return {
                    display: style.display,
                    visibility: style.visibility,
                    opacity: style.opacity
                };
            }
            return null;
        });
        
        console.log(`\n🎨 consolidated_form computed style:`, formComputedStyle);
        
        // Check container computed style  
        const containerComputedStyle = await page.evaluate(() => {
            const element = document.getElementById('consolidated-table-container');
            if (element) {
                const style = window.getComputedStyle(element);
                return {
                    display: style.display,
                    visibility: style.visibility,
                    opacity: style.opacity
                };
            }
            return null;
        });
        
        console.log(`🎨 consolidated-table-container computed style:`, containerComputedStyle);
        
    } catch (error) {
        console.error('❌ Debug-Fehler:', error);
    } finally {
        await browser.close();
    }
}

debugConsolidatedJS();