/*
Author: rahn
Datum: 02.08.2025
Version: 1.0
Beschreibung: DOM Undefined Analyst - Detaillierte Live-Analyse der undefined-Werte
*/

const { chromium } = require('playwright');
const fs = require('fs');

async function analyzeDOMUndefined() {
    console.log('🔍 DOM Undefined Analyst gestartet...');
    
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    
    const analysis = {
        timestamp: new Date().toISOString(),
        totalUndefined: 0,
        categorizedUndefined: {
            smallTags: [],
            tableCells: [],
            textNodes: [],
            attributes: [],
            other: []
        },
        javascriptErrors: [],
        failedRequests: [],
        undefinedSources: {
            frontend: 0,
            api: 0,
            templates: 0
        },
        patterns: {
            rawUndefined: 0,
            stringUndefined: 0,
            nullAsUndefined: 0,
            emptyAsUndefined: 0
        },
        locations: []
    };
    
    // JavaScript-Fehler abfangen
    page.on('console', msg => {
        if (msg.type() === 'error') {
            analysis.javascriptErrors.push({
                text: msg.text(),
                location: msg.location()
            });
            console.log('❌ JS Error:', msg.text());
        }
    });
    
    // Netzwerk-Fehler abfangen
    page.on('response', response => {
        if (!response.ok()) {
            analysis.failedRequests.push({
                url: response.url(),
                status: response.status(),
                statusText: response.statusText()
            });
            console.log(`❌ Failed Request: ${response.url()} - ${response.status()}`);
        }
    });
    
    try {
        console.log('📄 Lade MineSearch Hauptseite...');
        await page.goto('http://localhost:8000', { waitUntil: 'networkidle' });
        
        // Warte auf vollständiges Laden
        await page.waitForTimeout(3000);
        
        console.log('🔍 Analysiere DOM nach undefined-Werten...');
        
        // SCHRITT 1: Suche alle undefined im DOM
        const undefinedAnalysis = await page.evaluate(() => {
            const analysis = {
                totalCount: 0,
                elements: [],
                patterns: {
                    rawUndefined: 0,
                    stringUndefined: 0,
                    nullAsUndefined: 0,
                    emptyAsUndefined: 0
                }
            };
            
            // Durchlaufe alle Textnodes
            const walker = document.createTreeWalker(
                document.body,
                NodeFilter.SHOW_TEXT,
                null,
                false
            );
            
            let node;
            while (node = walker.nextNode()) {
                const text = node.textContent;
                if (text && text.includes('undefined')) {
                    const undefinedCount = (text.match(/undefined/g) || []).length;
                    analysis.totalCount += undefinedCount;
                    
                    analysis.elements.push({
                        text: text.substring(0, 100),
                        parent: node.parentElement ? {
                            tagName: node.parentElement.tagName,
                            className: node.parentElement.className,
                            id: node.parentElement.id
                        } : null,
                        undefinedCount: undefinedCount
                    });
                    
                    // Pattern-Analyse
                    if (text.trim() === 'undefined') {
                        analysis.patterns.rawUndefined++;
                    } else if (text.includes('"undefined"') || text.includes("'undefined'")) {
                        analysis.patterns.stringUndefined++;
                    }
                }
            }
            
            // Durchlaufe alle Elemente
            document.querySelectorAll('*').forEach(el => {
                // Prüfe Attribute
                Array.from(el.attributes).forEach(attr => {
                    if (attr.value && attr.value.includes('undefined')) {
                        analysis.elements.push({
                            type: 'attribute',
                            element: el.tagName,
                            attribute: attr.name,
                            value: attr.value
                        });
                    }
                });
                
                // Prüfe innerHTML
                if (el.innerHTML && el.innerHTML.includes('undefined') && !el.querySelector('*')) {
                    const undefinedCount = (el.innerHTML.match(/undefined/g) || []).length;
                    analysis.totalCount += undefinedCount;
                    
                    analysis.elements.push({
                        type: 'innerHTML',
                        tagName: el.tagName,
                        className: el.className,
                        id: el.id,
                        content: el.innerHTML.substring(0, 100),
                        undefinedCount: undefinedCount
                    });
                }
            });
            
            return analysis;
        });
        
        analysis.totalUndefined = undefinedAnalysis.totalCount;
        analysis.patterns = undefinedAnalysis.patterns;
        
        console.log(`📊 Gefunden: ${analysis.totalUndefined} undefined-Werte`);
        
        // SCHRITT 2: Kategorisiere undefined-Vorkommen
        for (const element of undefinedAnalysis.elements) {
            if (element.parent && element.parent.tagName === 'SMALL') {
                analysis.categorizedUndefined.smallTags.push(element);
            } else if (element.parent && (element.parent.tagName === 'TD' || element.parent.tagName === 'TH')) {
                analysis.categorizedUndefined.tableCells.push(element);
            } else if (element.type === 'attribute') {
                analysis.categorizedUndefined.attributes.push(element);
            } else if (element.type === 'innerHTML') {
                analysis.categorizedUndefined.other.push(element);
            } else {
                analysis.categorizedUndefined.textNodes.push(element);
            }
        }
        
        console.log('📊 Kategorisierung:');
        console.log(`   SMALL Tags: ${analysis.categorizedUndefined.smallTags.length}`);
        console.log(`   Tabellenzellen: ${analysis.categorizedUndefined.tableCells.length}`);
        console.log(`   Text Nodes: ${analysis.categorizedUndefined.textNodes.length}`);
        console.log(`   Attribute: ${analysis.categorizedUndefined.attributes.length}`);
        console.log(`   Andere: ${analysis.categorizedUndefined.other.length}`);
        
        // SCHRITT 3: Lade Statistik-Seite
        console.log('📈 Navigiere zur Statistik-Seite...');
        await page.click('input[value="statistics"]');
        await page.waitForTimeout(2000);
        
        // Prüfe Statistik-Seite
        const statisticsUndefined = await page.evaluate(() => {
            const body = document.body.textContent || '';
            const undefinedMatches = body.match(/undefined/g) || [];
            return {
                count: undefinedMatches.length,
                hasStatistics: !!document.querySelector('.statistics-container, .consolidated-table-container')
            };
        });
        
        analysis.statisticsPage = statisticsUndefined;
        console.log(`📈 Statistik-Seite: ${statisticsUndefined.count} undefined-Werte`);
        
        // SCHRITT 4: API-Requests analysieren
        console.log('🌐 Analysiere API-Requests...');
        
        const apiRequests = [];
        page.on('response', async (response) => {
            if (response.url().includes('/api/')) {
                try {
                    const body = await response.text();
                    const undefinedCount = (body.match(/undefined/g) || []).length;
                    if (undefinedCount > 0) {
                        apiRequests.push({
                            url: response.url(),
                            undefinedCount: undefinedCount,
                            bodySnippet: body.substring(0, 200)
                        });
                        analysis.undefinedSources.api += undefinedCount;
                    }
                } catch (e) {
                    console.log(`⚠️ Konnte API Response nicht lesen: ${response.url()}`);
                }
            }
        });
        
        // Triggere eine Suche um API-Calls zu generieren
        await page.click('input[value="search"]');
        await page.waitForTimeout(1000);
        await page.fill('input[name="query"]', 'test');
        await page.click('button[type="submit"]');
        await page.waitForTimeout(3000);
        
        analysis.apiRequests = apiRequests;
        
        // SCHRITT 5: Console-Logs auswerten
        const consoleLogs = await page.evaluate(() => {
            return window.console._logs || [];
        });
        
        // Screenshot für visuelle Analyse
        await page.screenshot({ 
            path: '/app/minesearch_v2/frontend/dom_analysis_screenshot.png',
            fullPage: true 
        });
        
        console.log('📊 Analyse abgeschlossen');
        
    } catch (error) {
        console.error('❌ Fehler bei der Analyse:', error);
        analysis.error = error.message;
    } finally {
        await browser.close();
    }
    
    // Report speichern
    const reportPath = '/app/minesearch_v2/frontend/dom_undefined_analysis_report.json';
    fs.writeFileSync(reportPath, JSON.stringify(analysis, null, 2));
    
    console.log('\n📄 ANALYSE-ZUSAMMENFASSUNG:');
    console.log('=====================================');
    console.log(`📊 Total undefined-Werte: ${analysis.totalUndefined}`);
    console.log(`🏷️ SMALL Tags: ${analysis.categorizedUndefined.smallTags.length}`);
    console.log(`📋 Tabellenzellen: ${analysis.categorizedUndefined.tableCells.length}`);
    console.log(`📝 Text Nodes: ${analysis.categorizedUndefined.textNodes.length}`);
    console.log(`🔗 Attribute: ${analysis.categorizedUndefined.attributes.length}`);
    console.log(`❌ JavaScript-Fehler: ${analysis.javascriptErrors.length}`);
    console.log(`🌐 API undefined: ${analysis.undefinedSources.api}`);
    console.log(`📈 Statistik-Seite: ${analysis.statisticsPage?.count || 0} undefined`);
    console.log('\n📊 Pattern-Analyse:');
    console.log(`   Raw 'undefined': ${analysis.patterns.rawUndefined}`);
    console.log(`   String "undefined": ${analysis.patterns.stringUndefined}`);
    console.log(`   Null as undefined: ${analysis.patterns.nullAsUndefined}`);
    console.log(`   Empty as undefined: ${analysis.patterns.emptyAsUndefined}`);
    console.log(`\n📄 Report: ${reportPath}`);
    console.log('📷 Screenshot: dom_analysis_screenshot.png');
    
    return analysis;
}

// Script ausführen wenn direkt aufgerufen
if (require.main === module) {
    analyzeDOMUndefined()
        .then(() => {
            console.log('✅ DOM Undefined Analyse beendet');
            process.exit(0);
        })
        .catch(error => {
            console.error('❌ Fehler:', error);
            process.exit(1);
        });
}

module.exports = { analyzeDOMUndefined };