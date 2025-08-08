/**
 * Author: rahn
 * Datum: 02.08.2025
 * Version: 1.0
 * Beschreibung: Zeitabhängiger undefined-Check um dynamische Insertion zu erfassen
 */

const { chromium } = require('playwright');

async function timingUndefinedCheck() {
    console.log('⏰ TIMING UNDEFINED-CHECK');
    
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    
    try {
        // 1. Navigiere zur Seite
        await page.goto('http://localhost:3000', { waitUntil: 'networkidle' });
        
        // 2. Check in mehreren Zeitpunkten
        const timeChecks = [];
        
        // Sofort nach Laden
        timeChecks.push({
            time: 'immediate',
            count: await page.evaluate(() => (document.body.textContent.match(/undefined/gi) || []).length)
        });
        
        console.log(`📊 Sofort nach Laden: ${timeChecks[0].count} undefined`);
        
        // Nach 1 Sekunde
        await page.waitForTimeout(1000);
        timeChecks.push({
            time: '1s',
            count: await page.evaluate(() => (document.body.textContent.match(/undefined/gi) || []).length)
        });
        
        console.log(`📊 Nach 1s: ${timeChecks[1].count} undefined`);
        
        // Aktiviere Statistiken
        console.log('🔄 Activating statistics...');
        await page.evaluate(() => {
            const radio = document.querySelector('input[value="statistics"]');
            if (radio) radio.click();
        });
        
        // Nach Tab-Aktivierung
        await page.waitForTimeout(500);
        timeChecks.push({
            time: 'after_tab',
            count: await page.evaluate(() => (document.body.textContent.match(/undefined/gi) || []).length)
        });
        
        console.log(`📊 Nach Tab-Aktivierung: ${timeChecks[2].count} undefined`);
        
        // Klicke Statistiken-Button
        const button = await page.locator('button:has-text("Statistiken")');
        if (await button.isVisible()) {
            console.log('🖱️ Clicking statistics button...');
            await button.click();
            
            // Check während des Ladens
            await page.waitForTimeout(1000);
            timeChecks.push({
                time: 'during_load',
                count: await page.evaluate(() => (document.body.textContent.match(/undefined/gi) || []).length)
            });
            
            console.log(`📊 Während Laden: ${timeChecks[3].count} undefined`);
            
            // Check nach vollständigem Laden
            await page.waitForTimeout(4000);
            timeChecks.push({
                time: 'after_load',
                count: await page.evaluate(() => (document.body.textContent.match(/undefined/gi) || []).length)
            });
            
            console.log(`📊 Nach vollständigem Laden: ${timeChecks[4].count} undefined`);
        }
        
        // 3. Suche nach dem spezifischen Timing wo undefined auftaucht
        if (timeChecks.some(check => check.count > 0)) {
            console.log('\n🔍 TIMING-ANALYSE:');
            timeChecks.forEach(check => {
                console.log(`   ${check.time}: ${check.count} undefined-Werte`);
            });
            
            // Finde den moment wo undefined erscheint
            const appearanceMoment = timeChecks.find(check => check.count > 0);
            if (appearanceMoment) {
                console.log(`\n⚠️ Undefined erscheint bei: ${appearanceMoment.time}`);
                
                // Detail-Check zu diesem Zeitpunkt
                const detailCheck = await page.evaluate(() => {
                    const allElements = [];
                    document.querySelectorAll('*').forEach(el => {
                        if (el.textContent && el.textContent.includes('undefined')) {
                            allElements.push({
                                tag: el.tagName,
                                class: el.className,
                                id: el.id,
                                text: el.textContent.substring(0, 100),
                                visible: el.offsetParent !== null
                            });
                        }
                    });
                    return allElements;
                });
                
                console.log(`\n🎯 GEFUNDENE ELEMENTE (${detailCheck.length}):`);
                detailCheck.forEach((el, i) => {
                    console.log(`   ${i+1}. ${el.tag}.${el.class}`);
                    console.log(`      Text: "${el.text}"`);
                    console.log(`      Sichtbar: ${el.visible}`);
                });
            }
        }
        
        // 4. Final screenshot
        await page.screenshot({ 
            path: '/app/minesearch_v2/frontend/timing-check-final.png',
            fullPage: true 
        });
        
        const finalCount = timeChecks[timeChecks.length - 1].count;
        console.log(`\n🏁 FINAL COUNT: ${finalCount}`);
        
        return {
            success: finalCount === 0,
            timeChecks
        };
        
    } catch (error) {
        console.error('❌ Timing check failed:', error);
    } finally {
        await browser.close();
    }
}

if (require.main === module) {
    timingUndefinedCheck().catch(console.error);
}

module.exports = { timingUndefinedCheck };