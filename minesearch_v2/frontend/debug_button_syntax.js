/*
Author: rahn
Datum: 27.07.2025
Version: 1.0
Beschreibung: Debug-Script für Button-Syntax-Probleme
*/

const { chromium } = require('playwright');

async function debugButtonSyntax() {
    console.log('🔍 Debugging Button Syntax Errors...');
    
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    
    // Sammle alle JavaScript-Fehler
    const jsErrors = [];
    page.on('pageerror', error => {
        jsErrors.push({
            message: error.message,
            stack: error.stack,
            timestamp: new Date().toISOString()
        });
        console.log(`❌ JS Error: ${error.message}`);
    });
    
    try {
        // Lade Frontend
        await page.goto('http://localhost:8080');
        await page.waitForSelector('h1', { timeout: 10000 });
        
        // Gehe zu Statistics Tab
        await page.click('#method_statistics');
        await page.waitForTimeout(2000);
        
        // Lade Statistics
        await page.click('button:has-text("📊 Lade Statistiken")');
        await page.waitForTimeout(5000);
        
        // Sammle alle onclick-Handler
        const allButtons = await page.evaluate(() => {
            const buttons = Array.from(document.querySelectorAll('button[onclick]'));
            return buttons.map(btn => ({
                onclick: btn.getAttribute('onclick'),
                text: btn.textContent.trim(),
                id: btn.id || 'no-id',
                className: btn.className || 'no-class'
            }));
        });
        
        console.log('\n📋 Alle onclick-Handler:');
        allButtons.forEach((btn, index) => {
            console.log(`${index + 1}. ${btn.text}: ${btn.onclick}`);
            
            // Prüfe auf Syntax-Probleme
            if (btn.onclick.includes('showModelDetails')) {
                console.log(`   🎯 Model Details Button gefunden!`);
                
                // Teste Syntax
                try {
                    new Function(btn.onclick);
                    console.log(`   ✅ Syntax OK`);
                } catch (error) {
                    console.log(`   ❌ Syntax Error: ${error.message}`);
                }
            }
        });
        
        // Teste spezifische Problem-Buttons
        const detailButtons = await page.locator('button:has-text("Details")');
        const buttonCount = await detailButtons.count();
        
        console.log(`\n🔍 Details-Buttons gefunden: ${buttonCount}`);
        
        for (let i = 0; i < Math.min(buttonCount, 10); i++) {
            try {
                const button = detailButtons.nth(i);
                const buttonText = await button.textContent();
                const onclick = await button.getAttribute('onclick');
                
                console.log(`\nButton ${i + 1}: ${buttonText}`);
                console.log(`  onclick: ${onclick}`);
                
                // Teste ob Button klickbar ist
                const isClickable = await button.isEnabled();
                console.log(`  Klickbar: ${isClickable}`);
                
                if (onclick && onclick.includes('showModelDetails')) {
                    // Teste Button-Klick
                    console.log(`  🖱️ Teste Klick...`);
                    await button.click();
                    await page.waitForTimeout(1000);
                    
                    if (jsErrors.length > 0) {
                        console.log(`  ❌ Klick verursachte JS-Fehler!`);
                    } else {
                        console.log(`  ✅ Klick erfolgreich`);
                    }
                }
                
            } catch (error) {
                console.log(`  ❌ Button ${i + 1} Error: ${error.message}`);
            }
        }
        
    } catch (error) {
        console.error('❌ Debug Error:', error.message);
    }
    
    // Zeige alle gefundenen JS-Fehler
    if (jsErrors.length > 0) {
        console.log('\n🚨 JavaScript-Fehler gefunden:');
        jsErrors.forEach((error, index) => {
            console.log(`${index + 1}. ${error.timestamp}: ${error.message}`);
        });
    } else {
        console.log('\n✅ Keine JavaScript-Fehler gefunden');
    }
    
    await browser.close();
}

debugButtonSyntax().catch(console.error);