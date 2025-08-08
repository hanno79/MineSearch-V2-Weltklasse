/**
 * Author: rahn
 * Datum: 02.08.2025
 * Version: 1.0
 * Beschreibung: Einfacher undefined-Check ohne aggressive Korrekturen
 */

const { chromium } = require('playwright');

async function simpleUndefinedCheck() {
    console.log('🔍 EINFACHER UNDEFINED-CHECK');
    
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    
    // Nur wichtige Console-Messages
    page.on('console', msg => {
        if (msg.text().includes('🔧 Fixing') || msg.text().includes('undefined')) {
            console.log('Log:', msg.text());
        }
    });
    
    try {
        // 1. Navigiere zur Seite
        await page.goto('http://localhost:3000', { waitUntil: 'networkidle' });
        await page.waitForTimeout(3000); // Kurze Wartezeit
        
        // 2. Prüfe Script-Status
        const scriptStatus = await page.evaluate(() => {
            return {
                safeDisplayValue: typeof window.safeDisplayValue === 'function',
                undefinedFix: typeof window.checkUndefinedStatus === 'function'
            };
        });
        
        console.log('📋 Scripts loaded:', scriptStatus);
        
        // 3. Erster undefined-Count
        const initialCount = await page.evaluate(() => {
            const bodyText = document.body.textContent || '';
            const matches = bodyText.match(/undefined/gi) || [];
            return matches.length;
        });
        
        console.log(`📊 Initial undefined count: ${initialCount}`);
        
        // 4. Aktiviere Statistiken
        console.log('🔄 Activating statistics...');
        await page.evaluate(() => {
            const radio = document.querySelector('input[value="statistics"]');
            if (radio) radio.click();
        });
        
        await page.waitForTimeout(1000);
        
        // 5. Klicke Statistiken-Button
        const button = await page.locator('button:has-text("Statistiken")');
        if (await button.isVisible()) {
            console.log('🖱️ Clicking statistics button...');
            await button.click();
            await page.waitForTimeout(5000); // Warte auf API-Response
        }
        
        // 6. Finaler undefined-Count
        const finalResult = await page.evaluate(() => {
            const bodyText = document.body.textContent || '';
            const matches = bodyText.match(/undefined/gi) || [];
            
            // Suche spezifisch nach undefined-Werten in Tabellen
            const tableUndefined = [];
            document.querySelectorAll('table td, table th').forEach(cell => {
                const text = cell.textContent?.trim() || '';
                if (text.includes('undefined')) {
                    tableUndefined.push({
                        tag: cell.tagName,
                        text: text.substring(0, 50),
                        html: cell.innerHTML.substring(0, 100)
                    });
                }
            });
            
            return {
                totalCount: matches.length,
                tableUndefined: tableUndefined,
                tableCount: document.querySelectorAll('table').length,
                bodySnapshot: bodyText.substring(0, 300)
            };
        });
        
        // 7. Screenshot für Dokumentation
        await page.screenshot({ 
            path: '/app/minesearch_v2/frontend/simple-check-result.png',
            fullPage: true 
        });
        
        // 8. Ergebnisse
        console.log('\n🏁 FINAL RESULTS:');
        console.log(`   📊 Total undefined count: ${finalResult.totalCount}`);
        console.log(`   📋 Tables found: ${finalResult.tableCount}`);
        console.log(`   🔧 Table cells with undefined: ${finalResult.tableUndefined.length}`);
        
        if (finalResult.tableUndefined.length > 0) {
            console.log('\n⚠️ TABLE CELLS WITH UNDEFINED:');
            finalResult.tableUndefined.slice(0, 3).forEach((cell, i) => {
                console.log(`   ${i+1}. ${cell.tag}: "${cell.text}"`);
                console.log(`      HTML: ${cell.html}`);
            });
        }
        
        console.log('\n📄 Body snippet:');
        console.log(`   "${finalResult.bodySnapshot}"`);
        
        const success = finalResult.totalCount === 0;
        console.log(`\n🎯 SUCCESS: ${success ? '✅' : '❌'}`);
        
        return {
            success,
            finalCount: finalResult.totalCount,
            tableIssues: finalResult.tableUndefined.length
        };
        
    } catch (error) {
        console.error('❌ Check failed:', error);
    } finally {
        await browser.close();
    }
}

if (require.main === module) {
    simpleUndefinedCheck().catch(console.error);
}

module.exports = { simpleUndefinedCheck };