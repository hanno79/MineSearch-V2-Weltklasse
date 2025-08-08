/**
 * Author: rahn
 * Datum: 02.08.2025
 * Version: 1.0
 * Beschreibung: Tracer für den letzten undefined-Wert
 */

const { chromium } = require('playwright');
const fs = require('fs');

async function traceLastUndefined() {
    console.log('🕵️ TRACE LETZTER UNDEFINED-WERT');
    
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    
    try {
        // 1. Navigiere zur Seite
        await page.goto('http://localhost:3000', { waitUntil: 'networkidle' });
        await page.waitForTimeout(3000);
        
        // 2. Aktiviere Statistiken
        await page.evaluate(() => {
            const radio = document.querySelector('input[value="statistics"]');
            if (radio) radio.click();
        });
        
        await page.waitForTimeout(1000);
        
        // 3. Klicke Statistiken-Button
        const button = await page.locator('button:has-text("Statistiken")');
        if (await button.isVisible()) {
            await button.click();
            await page.waitForTimeout(5000);
        }
        
        // 4. DETAILLIERTE ANALYSE - JEDEN EINZELNEN KNOTEN PRÜFEN
        const traceResult = await page.evaluate(() => {
            const report = {
                timestamp: new Date().toISOString(),
                undefinedFound: [],
                totalTextNodes: 0,
                totalElements: 0,
                searchDetails: {}
            };
            
            // Gehe durch ALLE Text-Knoten
            const walker = document.createTreeWalker(
                document.body,
                NodeFilter.SHOW_TEXT,
                null,
                false
            );
            
            let node;
            while (node = walker.nextNode()) {
                report.totalTextNodes++;
                const text = node.textContent || '';
                
                if (text.includes('undefined')) {
                    const parent = node.parentElement;
                    const parentInfo = {
                        tag: parent ? parent.tagName : 'NO_PARENT',
                        class: parent ? parent.className : '',
                        id: parent ? parent.id : '',
                        innerHTML: parent ? parent.innerHTML.substring(0, 200) : '',
                        textContent: text.substring(0, 100),
                        position: {
                            x: parent ? parent.offsetLeft : 0,
                            y: parent ? parent.offsetTop : 0
                        }
                    };
                    
                    report.undefinedFound.push(parentInfo);
                    
                    // Versuche zu identifizieren WARUM es nicht gefixt wurde
                    parentInfo.debugInfo = {
                        hasChildren: parent ? parent.children.length > 0 : false,
                        isVisible: parent ? parent.offsetParent !== null : false,
                        nodeType: node.nodeType,
                        parentNodeType: parent ? parent.nodeType : 'N/A'
                    };
                }
            }
            
            // Prüfe auch alle Elemente direkt
            document.querySelectorAll('*').forEach(el => {
                report.totalElements++;
                if (el.textContent && el.textContent.includes('undefined') && el.children.length === 0) {
                    report.undefinedFound.push({
                        tag: el.tagName,
                        class: el.className,
                        id: el.id,
                        textContent: el.textContent.substring(0, 100),
                        innerHTML: el.innerHTML.substring(0, 200),
                        source: 'direct_element_check'
                    });
                }
            });
            
            // Spezielle Suche in versteckten/unsichtbaren Elementen
            document.querySelectorAll('[style*="display: none"], [style*="visibility: hidden"], .hidden').forEach(el => {
                if (el.textContent && el.textContent.includes('undefined')) {
                    report.undefinedFound.push({
                        tag: el.tagName,
                        class: el.className,
                        id: el.id,
                        textContent: el.textContent.substring(0, 100),
                        source: 'hidden_element'
                    });
                }
            });
            
            // Suche in Scripts und Templates
            document.querySelectorAll('script, template').forEach(el => {
                if (el.textContent && el.textContent.includes('undefined')) {
                    report.undefinedFound.push({
                        tag: el.tagName,
                        type: el.type || 'no-type',
                        textContent: el.textContent.substring(0, 100),
                        source: 'script_or_template'
                    });
                }
            });
            
            return report;
        });
        
        // 5. Screenshot mit Markierungen
        await page.screenshot({ 
            path: '/app/minesearch_v2/frontend/trace-undefined-location.png',
            fullPage: true 
        });
        
        // 6. Speichere detaillierten Bericht
        fs.writeFileSync(
            '/app/minesearch_v2/frontend/undefined-trace-report.json',
            JSON.stringify(traceResult, null, 2)
        );
        
        // 7. Ausgabe
        console.log('\n🔍 TRACE ERGEBNISSE:');
        console.log(`   📊 Undefined Stellen gefunden: ${traceResult.undefinedFound.length}`);
        console.log(`   📄 Text-Knoten gescannt: ${traceResult.totalTextNodes}`);
        console.log(`   🏷️ Elemente gescannt: ${traceResult.totalElements}`);
        
        if (traceResult.undefinedFound.length > 0) {
            console.log('\n🎯 GEFUNDENE UNDEFINED-STELLEN:');
            traceResult.undefinedFound.forEach((item, i) => {
                console.log(`\n   ${i+1}. ${item.tag} (${item.source || 'text_walker'})`);
                console.log(`      Klasse: ${item.class || 'none'}`);
                console.log(`      ID: ${item.id || 'none'}`);
                console.log(`      Text: "${item.textContent}"`);
                if (item.debugInfo) {
                    console.log(`      Debug: children=${item.debugInfo.hasChildren}, visible=${item.debugInfo.isVisible}`);
                }
                if (item.position) {
                    console.log(`      Position: x=${item.position.x}, y=${item.position.y}`);
                }
            });
        }
        
        console.log('\n📄 Detaillierter Bericht: undefined-trace-report.json');
        
        return traceResult;
        
    } catch (error) {
        console.error('❌ Trace failed:', error);
    } finally {
        await browser.close();
    }
}

if (require.main === module) {
    traceLastUndefined().catch(console.error);
}

module.exports = { traceLastUndefined };