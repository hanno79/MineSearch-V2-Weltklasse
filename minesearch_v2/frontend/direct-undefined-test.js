/**
 * Author: rahn
 * Datum: 02.08.2025
 * Version: 1.0
 * Beschreibung: Direkter undefined-Test mit Playwright
 */

const { chromium } = require('playwright');

async function directUndefinedTest() {
    console.log('🎯 DIREKTER UNDEFINED TEST');
    
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    
    // Console-Logging aktivieren
    page.on('console', msg => {
        if (msg.text().includes('🔧') || msg.text().includes('undefined')) {
            console.log('Browser:', msg.text());
        }
    });
    
    try {
        // 1. Navigiere zur Seite
        await page.goto('http://localhost:3000', { waitUntil: 'networkidle' });
        await page.waitForTimeout(5000); // Lange warten auf alle Scripts
        
        console.log('📸 Taking screenshot...');
        await page.screenshot({ 
            path: '/app/minesearch_v2/frontend/direct-test-initial.png',
            fullPage: true 
        });
        
        // 2. Prüfe ob Scripts geladen sind
        const scriptStatus = await page.evaluate(() => {
            return {
                safeDisplayValue: typeof window.safeDisplayValue === 'function',
                getUndefinedCount: typeof window.getUndefinedCount === 'function',
                aggressiveFix: typeof window.String === 'function'
            };
        });
        
        console.log('📋 Script Status:', scriptStatus);
        
        // 3. Manueller undefined-Count
        const manualCount = await page.evaluate(() => {
            const bodyText = document.body.textContent || '';
            const matches = bodyText.match(/undefined/gi) || [];
            return {
                count: matches.length,
                sample: bodyText.substring(0, 500)
            };
        });
        
        console.log(`📊 Manual undefined count: ${manualCount.count}`);
        console.log(`📄 Body sample: ${manualCount.sample.substring(0, 100)}...`);
        
        // 4. Aktiviere Statistiken
        console.log('🔄 Activating statistics...');
        await page.evaluate(() => {
            const radio = document.querySelector('input[value="statistics"]');
            if (radio) radio.click();
        });
        
        await page.waitForTimeout(2000);
        
        // 5. Klicke Statistiken-Button
        const buttonVisible = await page.locator('button:has-text("Statistiken")').isVisible();
        if (buttonVisible) {
            console.log('🖱️ Clicking statistics button...');
            await page.locator('button:has-text("Statistiken")').click();
            await page.waitForTimeout(8000); // Sehr lange warten
        }
        
        console.log('📸 Taking final screenshot...');
        await page.screenshot({ 
            path: '/app/minesearch_v2/frontend/direct-test-final.png',
            fullPage: true 
        });
        
        // 6. Finaler Count
        const finalCount = await page.evaluate(() => {
            const bodyText = document.body.textContent || '';
            const matches = bodyText.match(/undefined/gi) || [];
            
            // Sammle alle undefined-Stellen
            const details = [];
            document.querySelectorAll('*').forEach(el => {
                if (el.textContent && el.textContent.includes('undefined') && el.children.length === 0) {
                    details.push({
                        tag: el.tagName,
                        text: el.textContent.substring(0, 50)
                    });
                }
            });
            
            return {
                count: matches.length,
                details: details.slice(0, 5)
            };
        });
        
        console.log(`🏁 Final undefined count: ${finalCount.count}`);
        if (finalCount.details.length > 0) {
            console.log('⚠️ Remaining undefined elements:');
            finalCount.details.forEach((el, i) => {
                console.log(`   ${i+1}. ${el.tag}: "${el.text}"`);
            });
        }
        
        // 7. Erfolgs-Check
        const success = finalCount.count === 0;
        console.log(`🎉 Test ${success ? 'ERFOLGREICH' : 'FEHLGESCHLAGEN'}`);
        
        return {
            scriptStatus,
            finalCount: finalCount.count,
            success
        };
        
    } catch (error) {
        console.error('❌ Test Fehler:', error);
        await page.screenshot({ 
            path: '/app/minesearch_v2/frontend/direct-test-error.png'
        });
    } finally {
        await browser.close();
    }
}

if (require.main === module) {
    directUndefinedTest().catch(console.error);
}

module.exports = { directUndefinedTest };