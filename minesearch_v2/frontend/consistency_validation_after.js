#!/usr/bin/env node
/**
 * Author: rahn
 * Datum: 02.08.2025
 * Version: 1.0
 * Beschreibung: Playwright Test NACHHER - Validiert korrigierte Konsistenz-Werte
 */

const { chromium } = require('playwright');
const fs = require('fs');

async function validateConsistencyAfter() {
    console.log('✅ KONSISTENZ-VALIDIERUNG NACHHER');
    console.log('=' * 50);
    
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    
    try {
        // 1. Navigiere zur Hauptseite
        await page.goto('http://localhost:8000', { waitUntil: 'networkidle' });
        await page.waitForTimeout(2000);
        
        // 2. Direkte API-Validierung
        const apiValidation = await page.evaluate(async () => {
            try {
                const response = await fetch('/api/statistics/models/detailed');
                const data = await response.json();
                
                const models = data.data?.model_statistics || [];
                const validation = {
                    success: response.ok,
                    modelCount: models.length,
                    validationResults: {
                        realisticValues: true,
                        noExtremeValues: true,
                        variousConsistency: true,
                        noUndefined: true
                    },
                    sampleModels: [],
                    consistencyRange: { min: 100, max: 0 },
                    successRateRange: { min: 100, max: 0 }
                };
                
                // Validiere erste 5 Modelle
                for (let i = 0; i < Math.min(5, models.length); i++) {
                    const model = models[i];
                    const sample = {
                        model_id: model.model_id,
                        success_rate: model.success_rate,
                        overall_consistency: model.overall_consistency,
                        avg_fields_found: model.avg_fields_found
                    };
                    validation.sampleModels.push(sample);
                    
                    // Prüfe realistische Werte
                    if (model.success_rate > 100 || model.overall_consistency > 100) {
                        validation.validationResults.realisticValues = false;
                    }
                    
                    // Prüfe extreme Werte (>1000%)
                    if (model.success_rate > 1000 || model.overall_consistency > 1000) {
                        validation.validationResults.noExtremeValues = false;
                    }
                    
                    // Sammle Range-Daten
                    if (model.overall_consistency) {
                        validation.consistencyRange.min = Math.min(validation.consistencyRange.min, model.overall_consistency);
                        validation.consistencyRange.max = Math.max(validation.consistencyRange.max, model.overall_consistency);
                    }
                    
                    if (model.success_rate) {
                        validation.successRateRange.min = Math.min(validation.successRateRange.min, model.success_rate);
                        validation.successRateRange.max = Math.max(validation.successRateRange.max, model.success_rate);
                    }
                }
                
                // Prüfe Varianz in Konsistenz-Werten
                const consistencies = validation.sampleModels.map(m => m.overall_consistency);
                const uniqueConsistencies = new Set(consistencies);
                validation.validationResults.variousConsistency = uniqueConsistencies.size > 2;
                
                // Prüfe auf undefined
                const jsonString = JSON.stringify(data);
                validation.validationResults.noUndefined = !jsonString.includes('null') && !jsonString.includes('undefined');
                
                return validation;
            } catch (error) {
                return { success: false, error: error.message };
            }
        });
        
        console.log('🌐 API Validierung NACHHER:');
        console.log(`   Status: ${apiValidation.success ? '✅' : '❌'}`);
        console.log(`   Modelle: ${apiValidation.modelCount}`);
        
        if (apiValidation.validationResults) {
            const results = apiValidation.validationResults;
            console.log(`   📊 Realistische Werte: ${results.realisticValues ? '✅' : '❌'}`);
            console.log(`   🚫 Keine Extremwerte: ${results.noExtremeValues ? '✅' : '❌'}`);
            console.log(`   🎲 Verschiedene Konsistenz: ${results.variousConsistency ? '✅' : '❌'}`);
            console.log(`   ✨ Keine undefined: ${results.noUndefined ? '✅' : '❌'}`);
            
            console.log('   📈 Konsistenz-Range:', 
                `${apiValidation.consistencyRange.min.toFixed(1)}% - ${apiValidation.consistencyRange.max.toFixed(1)}%`);
            console.log('   🎯 Erfolgsraten-Range:', 
                `${apiValidation.successRateRange.min.toFixed(1)}% - ${apiValidation.successRateRange.max.toFixed(1)}%`);
        }
        
        // 3. Zeige Beispiel-Modelle
        if (apiValidation.sampleModels.length > 0) {
            console.log('\n📋 Beispiel-Modelle:');
            apiValidation.sampleModels.forEach((model, index) => {
                console.log(`   ${index + 1}. ${model.model_id}`);
                console.log(`      • Erfolg: ${model.success_rate.toFixed(1)}%`);
                console.log(`      • Konsistenz: ${model.overall_consistency.toFixed(1)}%`);
                console.log(`      • Felder: ${model.avg_fields_found.toFixed(1)}`);
            });
        }
        
        // 4. Navigiere zu Statistiken-Seite
        try {
            // Versuche verschiedene Navigation-Methoden
            const navigationSuccess = await page.evaluate(() => {
                // Methode 1: Radio Button
                const statisticsRadio = document.querySelector('input[value="statistics"]');
                if (statisticsRadio) {
                    statisticsRadio.click();
                    return 'radio_clicked';
                }
                
                // Methode 2: Button mit "Statistiken"
                const buttons = Array.from(document.querySelectorAll('button'));
                const statsButton = buttons.find(btn => 
                    btn.textContent && btn.textContent.includes('Statistiken') && btn.textContent.includes('laden')
                );
                if (statsButton) {
                    statsButton.click();
                    return 'button_clicked';
                }
                
                return 'no_navigation';
            });
            
            console.log(`\n🖱️ Navigation: ${navigationSuccess}`);
            await page.waitForTimeout(3000);
            
        } catch (e) {
            console.log('⚠️ Navigation fehlgeschlagen:', e.message);
        }
        
        // 5. Screenshot NACHHER
        await page.screenshot({ 
            path: '/app/minesearch_v2/frontend/consistency_after_main.png',
            fullPage: true 
        });
        
        // 6. Analysiere DOM für Statistiken
        const domAnalysis = await page.evaluate(() => {
            const analysis = {
                tablesFound: 0,
                statisticsVisible: false,
                modelRowsFound: 0,
                consistencyValuesFound: [],
                successRateValuesFound: [],
                problemsDetected: {
                    undefinedValues: 0,
                    extremeValues: 0,
                    identicalValues: 0
                }
            };
            
            // Zähle Tabellen
            const tables = document.querySelectorAll('table');
            analysis.tablesFound = tables.length;
            
            // Prüfe Statistiken-Sichtbarkeit
            analysis.statisticsVisible = document.querySelector('#statistics-container, .statistics-table, [id*="statist"]') !== null;
            
            // Analysiere Tabellen-Inhalte
            tables.forEach(table => {
                const rows = Array.from(table.querySelectorAll('tr'));
                analysis.modelRowsFound += Math.max(0, rows.length - 1); // Minus Header
                
                rows.forEach(row => {
                    const cells = Array.from(row.querySelectorAll('td, th'));
                    cells.forEach(cell => {
                        const text = cell.textContent || '';
                        
                        // Sammle Konsistenz-Werte
                        const consistencyMatch = text.match(/(\d+\.?\d*)%/);
                        if (consistencyMatch) {
                            const value = parseFloat(consistencyMatch[1]);
                            if (value > 0 && value <= 100) {
                                analysis.consistencyValuesFound.push(value);
                            } else if (value > 100) {
                                analysis.problemsDetected.extremeValues++;
                            }
                        }
                        
                        // Prüfe auf undefined
                        if (text.includes('undefined')) {
                            analysis.problemsDetected.undefinedValues++;
                        }
                    });
                });
            });
            
            // Prüfe auf identische Werte
            const allText = document.body.textContent || '';
            const hundredPercentMatches = allText.match(/100\.0%/g) || [];
            analysis.problemsDetected.identicalValues = hundredPercentMatches.length;
            
            return analysis;
        });
        
        // 7. Erstelle NACHHER-Bericht
        const afterReport = {
            timestamp: new Date().toISOString(),
            phase: 'AFTER_FIX',
            apiValidation: apiValidation,
            domAnalysis: domAnalysis,
            screenshots: ['consistency_after_main.png'],
            overallValidation: {
                apiWorking: apiValidation.success,
                realisticValues: apiValidation.validationResults?.realisticValues || false,
                noExtremeValues: apiValidation.validationResults?.noExtremeValues || false,
                variousConsistency: apiValidation.validationResults?.variousConsistency || false,
                noUndefined: apiValidation.validationResults?.noUndefined || false,
                statisticsVisible: domAnalysis.statisticsVisible,
                noProblems: domAnalysis.problemsDetected.undefinedValues === 0 && 
                           domAnalysis.problemsDetected.extremeValues === 0
            }
        };
        
        // 8. Berechne Erfolgs-Score
        const validationChecks = Object.values(afterReport.overallValidation);
        const passedChecks = validationChecks.filter(check => check === true).length;
        const totalChecks = validationChecks.length;
        const successScore = (passedChecks / totalChecks) * 100;
        
        afterReport.successScore = successScore;
        
        // 9. Speichere Bericht
        fs.writeFileSync(
            '/app/minesearch_v2/frontend/consistency_validation_after_report.json',
            JSON.stringify(afterReport, null, 2)
        );
        
        // 10. Ausgabe
        console.log('\n🎉 NACHHER-VALIDIERUNG ERGEBNISSE:');
        console.log(`   📊 Erfolgs-Score: ${successScore.toFixed(1)}% (${passedChecks}/${totalChecks})`);
        console.log(`   🖼️ Screenshots: ${afterReport.screenshots.length}`);
        console.log(`   📋 Tabellen: ${domAnalysis.tablesFound}`);
        console.log(`   📝 Modell-Zeilen: ${domAnalysis.modelRowsFound}`);
        console.log(`   🎯 Konsistenz-Werte: ${domAnalysis.consistencyValuesFound.length}`);
        
        console.log('\n✅ VALIDIERUNGS-CHECKS:');
        Object.entries(afterReport.overallValidation).forEach(([key, value]) => {
            console.log(`   ${value ? '✅' : '❌'} ${key}`);
        });
        
        if (domAnalysis.problemsDetected.undefinedValues > 0 || 
            domAnalysis.problemsDetected.extremeValues > 0) {
            console.log('\n🚨 GEFUNDENE PROBLEME:');
            console.log(`   • Undefined-Werte: ${domAnalysis.problemsDetected.undefinedValues}`);
            console.log(`   • Extreme Werte: ${domAnalysis.problemsDetected.extremeValues}`);
        } else {
            console.log('\n🎉 KEINE PROBLEME GEFUNDEN!');
        }
        
        console.log('\n📄 NACHHER-Bericht: consistency_validation_after_report.json');
        
    } catch (error) {
        console.error('❌ NACHHER-Validierung Fehler:', error);
        
        await page.screenshot({ 
            path: '/app/minesearch_v2/frontend/consistency_after_error.png' 
        });
        
    } finally {
        await browser.close();
        console.log('🎉 NACHHER-Validierung abgeschlossen!');
    }
}

if (require.main === module) {
    validateConsistencyAfter().catch(console.error);
}

module.exports = { validateConsistencyAfter };