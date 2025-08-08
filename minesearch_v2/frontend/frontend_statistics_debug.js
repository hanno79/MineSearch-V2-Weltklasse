#!/usr/bin/env node
/**
 * Author: rahn
 * Datum: 02.08.2025
 * Version: 1.0
 * Beschreibung: Frontend Debug für Statistik-Anzeige - undefined Werte beheben
 */

const { chromium } = require('playwright');
const fs = require('fs');

async function debugFrontendStatistics() {
    console.log('🔧 FRONTEND STATISTIK DEBUG');
    console.log('=' * 50);
    
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    
    // Enable console logging
    page.on('console', msg => {
        if (msg.type() === 'error') {
            console.log('❌ Frontend Error:', msg.text());
        } else if (msg.type() === 'warning') {
            console.log('⚠️ Frontend Warning:', msg.text());
        }
    });
    
    try {
        // 1. Navigiere zur Hauptseite
        await page.goto('http://localhost:8000', { waitUntil: 'networkidle' });
        await page.waitForTimeout(2000);
        
        // 2. Teste API direkt im Browser
        const apiTest = await page.evaluate(async () => {
            try {
                console.log('🔍 Teste API direkt...');
                const response = await fetch('/api/statistics/models/detailed');
                const data = await response.json();
                
                const result = {
                    success: response.ok,
                    status: response.status,
                    modelCount: data.data?.model_statistics?.length || 0,
                    sampleModel: null,
                    hasUndefined: false
                };
                
                if (data.data?.model_statistics?.length > 0) {
                    const model = data.data.model_statistics[0];
                    result.sampleModel = {
                        model_id: model.model_id,
                        success_rate: model.success_rate,
                        overall_consistency: model.overall_consistency,
                        avg_fields_found: model.avg_fields_found
                    };
                    
                    // Prüfe auf undefined Werte
                    const jsonString = JSON.stringify(data);
                    if (jsonString.includes('null') || jsonString.includes('undefined')) {
                        result.hasUndefined = true;
                    }
                }
                
                return result;
            } catch (error) {
                return { success: false, error: error.message };
            }
        });
        
        console.log('🌐 API Test Ergebnis:');
        console.log(`   Status: ${apiTest.success ? '✅' : '❌'} (${apiTest.status || 'Error'})`);
        console.log(`   Modelle: ${apiTest.modelCount}`);
        if (apiTest.sampleModel) {
            console.log(`   Beispiel-Modell: ${apiTest.sampleModel.model_id}`);
            console.log(`     • Erfolgsrate: ${(apiTest.sampleModel.success_rate * 100).toFixed(1)}%`);
            console.log(`     • Konsistenz: ${(apiTest.sampleModel.overall_consistency * 100).toFixed(1)}%`);
            console.log(`     • Avg Felder: ${apiTest.sampleModel.avg_fields_found}`);
        }
        console.log(`   Undefined-Werte: ${apiTest.hasUndefined ? '❌' : '✅'}`);
        
        // 3. Finde und klicke Statistiken Button
        await page.evaluate(() => {
            console.log('🔍 Suche Statistiken-Button...');
            const buttons = Array.from(document.querySelectorAll('button'));
            window.statisticsButtons = [];
            
            buttons.forEach((btn, index) => {
                const text = btn.textContent || '';
                if (text.includes('Statistiken') || text.includes('laden')) {
                    window.statisticsButtons.push({
                        index: index,
                        text: text.trim(),
                        visible: btn.offsetParent !== null,
                        enabled: !btn.disabled
                    });
                }
            });
            
            console.log(`Gefundene Statistiken-Buttons: ${window.statisticsButtons.length}`);
            window.statisticsButtons.forEach(btn => {
                console.log(`  • ${btn.text} (sichtbar: ${btn.visible}, aktiv: ${btn.enabled})`);
            });
        });
        
        const buttonInfo = await page.evaluate(() => window.statisticsButtons);
        
        // 4. Klicke auf den ersten verfügbaren Button
        let buttonClicked = false;
        if (buttonInfo.length > 0) {
            const button = buttonInfo.find(btn => btn.visible && btn.enabled);
            if (button) {
                try {
                    await page.evaluate((buttonText) => {
                        const buttons = Array.from(document.querySelectorAll('button'));
                        const targetButton = buttons.find(btn => btn.textContent?.trim() === buttonText);
                        if (targetButton) {
                            console.log('🖱️ Klicke auf:', buttonText);
                            targetButton.click();
                        }
                    }, button.text);
                    
                    await page.waitForTimeout(3000);
                    buttonClicked = true;
                    console.log('✅ Button geklickt:', button.text);
                } catch (e) {
                    console.log('❌ Button-Klick fehlgeschlagen:', e.message);
                }
            }
        }
        
        // 5. Screenshot nach Button-Klick
        if (buttonClicked) {
            await page.screenshot({ 
                path: '/app/minesearch_v2/frontend/frontend_debug_after_click.png',
                fullPage: true 
            });
        }
        
        // 6. Analysiere DOM für Statistiken
        const domAnalysis = await page.evaluate(() => {
            const analysis = {
                tables: 0,
                undefinedTexts: 0,
                identicalValues: [],
                statisticsVisible: false,
                modelRows: 0
            };
            
            // Zähle Tabellen
            analysis.tables = document.querySelectorAll('table').length;
            
            // Suche nach "undefined" im sichtbaren Text
            const bodyText = document.body.textContent || '';
            const undefinedMatches = bodyText.match(/undefined/gi) || [];
            analysis.undefinedTexts = undefinedMatches.length;
            
            // Suche nach identischen Werten
            const hundredPercentMatches = bodyText.match(/100(\.0)?%/g) || [];
            analysis.identicalValues.push({
                type: 'hundred_percent',
                count: hundredPercentMatches.length
            });
            
            const zeroMatches = bodyText.match(/0\s*(ms|€|%|CAD)/g) || [];
            analysis.identicalValues.push({
                type: 'zero_values',
                count: zeroMatches.length
            });
            
            // Prüfe ob Statistiken sichtbar sind
            const statisticsElements = document.querySelectorAll('[id*="statist"], [class*="statist"], table');
            analysis.statisticsVisible = statisticsElements.length > 0;
            
            // Zähle Modell-Zeilen in Tabellen
            const tableRows = document.querySelectorAll('table tr');
            analysis.modelRows = Math.max(0, tableRows.length - 1); // Minus Header
            
            return analysis;
        });
        
        // 7. Cache-Test
        const cacheTest = await page.evaluate(() => {
            // Lösche alle localStorage/sessionStorage
            try {
                localStorage.clear();
                sessionStorage.clear();
                console.log('🧹 Browser Cache geleert');
                return { cacheCleared: true };
            } catch (e) {
                return { cacheCleared: false, error: e.message };
            }
        });
        
        // 8. Erstelle Debug-Bericht
        const debugReport = {
            timestamp: new Date().toISOString(),
            apiTest: apiTest,
            buttonInfo: buttonInfo,
            buttonClicked: buttonClicked,
            domAnalysis: domAnalysis,
            cacheTest: cacheTest,
            screenshots: ['frontend_debug_after_click.png'],
            problems: {
                apiUndefined: apiTest.hasUndefined,
                domUndefined: domAnalysis.undefinedTexts > 0,
                noStatistics: !domAnalysis.statisticsVisible,
                noButtons: buttonInfo.length === 0,
                tooManyIdentical: domAnalysis.identicalValues.some(v => v.count > 10)
            }
        };
        
        // 9. Speichere Bericht
        fs.writeFileSync(
            '/app/minesearch_v2/frontend/frontend_debug_report.json',
            JSON.stringify(debugReport, null, 2)
        );
        
        // 10. Ausgabe
        console.log('\n📊 FRONTEND DEBUG ERGEBNISSE:');
        console.log(`   🌐 API funktioniert: ${apiTest.success ? '✅' : '❌'}`);
        console.log(`   🖱️ Button gefunden: ${buttonInfo.length > 0 ? '✅' : '❌'}`);
        console.log(`   📊 Statistiken sichtbar: ${domAnalysis.statisticsVisible ? '✅' : '❌'}`);
        console.log(`   ❌ Undefined im DOM: ${domAnalysis.undefinedTexts}`);
        console.log(`   📋 Tabellen: ${domAnalysis.tables}`);
        console.log(`   📝 Modell-Zeilen: ${domAnalysis.modelRows}`);
        console.log(`   🧹 Cache geleert: ${cacheTest.cacheCleared ? '✅' : '❌'}`);
        
        const problemCount = Object.values(debugReport.problems).filter(p => p).length;
        console.log(`   🚨 Gefundene Probleme: ${problemCount}`);
        
        if (problemCount > 0) {
            console.log('\n🔍 PROBLEME DETAILS:');
            Object.entries(debugReport.problems).forEach(([key, value]) => {
                if (value) {
                    console.log(`      • ${key}: ${value}`);
                }
            });
        }
        
        console.log('\n📄 Debug-Bericht: frontend_debug_report.json');
        
    } catch (error) {
        console.error('❌ Frontend Debug Fehler:', error);
        
        await page.screenshot({ 
            path: '/app/minesearch_v2/frontend/frontend_debug_error.png' 
        });
        
    } finally {
        await browser.close();
        console.log('🎉 Frontend Debug abgeschlossen!');
    }
}

if (require.main === module) {
    debugFrontendStatistics().catch(console.error);
}

module.exports = { debugFrontendStatistics };