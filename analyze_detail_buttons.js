/**
 * Author: rahn
 * Datum: 10.08.2025
 * Version: 1.0
 * Beschreibung: Analyse aller Detail-Button-Probleme in MineSearch 2.0
 */

const { chromium } = require('playwright');

async function analyzeDetailButtons() {
    const browser = await chromium.launch();
    const page = await browser.newPage();
    
    console.log('🔍 DETAIL-BUTTON ANALYSE');
    console.log('========================\n');
    
    // Collect all console errors
    const jsErrors = [];
    page.on('console', msg => {
        if (msg.type() === 'error' || msg.text().includes('not defined') || msg.text().includes('❌')) {
            jsErrors.push(msg.text());
        }
    });
    
    // Collect JavaScript errors
    page.on('pageerror', error => {
        jsErrors.push(`PAGE ERROR: ${error.message}`);
    });
    
    try {
        await page.goto('http://localhost:8000', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(3000);
        
        console.log('✅ Seite geladen');
        
        const detailAnalysis = {
            sources: { buttons: 0, working: 0, errors: [] },
            statistics: { buttons: 0, working: 0, errors: [] },
            consolidated: { buttons: 0, working: 0, errors: [] }
        };
        
        // ANALYSE: Quellen-Tab Detail-Buttons
        console.log('\n🔍 ANALYSE: Quellen-Tab Detail-Buttons');
        await page.click('label[for="sources-tab"]');
        await page.waitForTimeout(4000);
        
        const sourceButtons = await page.$$('button:has-text("Details")');
        detailAnalysis.sources.buttons = sourceButtons.length;
        console.log(`  Gefundene Detail-Buttons: ${sourceButtons.length}`);
        
        if (sourceButtons.length > 0) {
            console.log('  Teste ersten Detail-Button...');
            try {
                await sourceButtons[0].click();
                await page.waitForTimeout(1000);
                console.log('  ✅ Button klickbar');
                detailAnalysis.sources.working = 1;
            } catch (error) {
                console.log(`  ❌ Button-Error: ${error.message}`);
                detailAnalysis.sources.errors.push(error.message);
            }
        }
        
        // ANALYSE: Statistiken-Tab Detail-Buttons
        console.log('\n🔍 ANALYSE: Statistiken-Tab Detail-Buttons');
        await page.click('label[for="statistics-tab"]');
        await page.waitForTimeout(4000);
        
        const statsButtons = await page.$$('button:has-text("Details")');
        detailAnalysis.statistics.buttons = statsButtons.length;
        console.log(`  Gefundene Detail-Buttons: ${statsButtons.length}`);
        
        if (statsButtons.length > 0) {
            console.log('  Teste ersten Detail-Button...');
            try {
                await statsButtons[0].click();
                await page.waitForTimeout(1000);
                console.log('  ✅ Button klickbar');
                detailAnalysis.statistics.working = 1;
            } catch (error) {
                console.log(`  ❌ Button-Error: ${error.message}`);
                detailAnalysis.statistics.errors.push(error.message);
            }
        }
        
        // ANALYSE: Konsolidiert-Tab Detail-Buttons
        console.log('\n🔍 ANALYSE: Konsolidiert-Tab Detail-Buttons');
        await page.click('label[for="consolidated-tab"]');
        await page.waitForTimeout(4000);
        
        const consolidatedButtons = await page.$$('button:has-text("Details")');
        detailAnalysis.consolidated.buttons = consolidatedButtons.length;
        console.log(`  Gefundene Detail-Buttons: ${consolidatedButtons.length}`);
        
        if (consolidatedButtons.length > 0) {
            console.log('  Teste ersten Detail-Button...');
            try {
                await consolidatedButtons[0].click();
                await page.waitForTimeout(1000);
                console.log('  ✅ Button klickbar');
                detailAnalysis.consolidated.working = 1;
            } catch (error) {
                console.log(`  ❌ Button-Error: ${error.message}`);
                detailAnalysis.consolidated.errors.push(error.message);
            }
        }
        
        // GLOBAL FUNCTION CHECK
        console.log('\n🔍 GLOBAL FUNCTION AVAILABILITY CHECK');
        const functionCheck = await page.evaluate(() => {
            return {
                viewConsolidatedDetail: typeof window.viewConsolidatedDetail,
                toggleSourceDetails: typeof window.toggleSourceDetails,
                viewResultDetail: typeof window.viewResultDetail,
                loadSources: typeof window.loadSources,
                loadConsolidatedResults: typeof window.loadConsolidatedResults,
                showDetailModal: typeof window.showDetailModal
            };
        });
        
        console.log('Global Functions Status:');
        Object.entries(functionCheck).forEach(([name, type]) => {
            console.log(`  ${name}: ${type === 'function' ? '✅' : '❌'} (${type})`);
        });
        
        // ONCLICK HANDLER ANALYSIS
        console.log('\n🔍 ONCLICK HANDLER ANALYSIS');
        const onclickAnalysis = await page.evaluate(() => {
            const buttons = Array.from(document.querySelectorAll('button'));
            const detailButtons = buttons.filter(btn => btn.textContent.includes('Details'));
            
            return detailButtons.map(btn => ({
                text: btn.textContent.trim(),
                onclick: btn.onclick ? 'Has onclick' : 'No onclick',
                attributes: btn.getAttributeNames().map(name => `${name}="${btn.getAttribute(name)}"`).join(' ')
            }));
        });
        
        console.log(`Gefundene Detail-Buttons insgesamt: ${onclickAnalysis.length}`);
        onclickAnalysis.forEach((btn, index) => {
            console.log(`  Button ${index + 1}: ${btn.text}`);
            console.log(`    onclick: ${btn.onclick}`);
            console.log(`    attributes: ${btn.attributes}`);
        });
        
        // JAVASCRIPT ERRORS SUMMARY
        console.log('\n📋 JAVASCRIPT ERRORS SUMMARY');
        console.log(`Gesammelte JS-Errors: ${jsErrors.length}`);
        
        const uniqueErrors = [...new Set(jsErrors)];
        uniqueErrors.forEach(error => {
            console.log(`  ❌ ${error}`);
        });
        
        // FINAL ANALYSIS
        console.log('\n🎯 DETAIL-BUTTON ANALYSE ZUSAMMENFASSUNG');
        console.log('=======================================');
        
        const totalButtons = detailAnalysis.sources.buttons + detailAnalysis.statistics.buttons + detailAnalysis.consolidated.buttons;
        const workingButtons = detailAnalysis.sources.working + detailAnalysis.statistics.working + detailAnalysis.consolidated.working;
        
        console.log(`📊 Gefundene Detail-Buttons: ${totalButtons}`);
        console.log(`✅ Funktionierende Buttons: ${workingButtons}`);
        console.log(`❌ Defekte Buttons: ${totalButtons - workingButtons}`);
        
        console.log('\nPro Tab:');
        console.log(`  Quellen: ${detailAnalysis.sources.buttons} Buttons, ${detailAnalysis.sources.working} funktionieren`);
        console.log(`  Statistiken: ${detailAnalysis.statistics.buttons} Buttons, ${detailAnalysis.statistics.working} funktionieren`);
        console.log(`  Konsolidiert: ${detailAnalysis.consolidated.buttons} Buttons, ${detailAnalysis.consolidated.working} funktionieren`);
        
        console.log('\nFehlende Funktionen:');
        Object.entries(functionCheck).forEach(([name, type]) => {
            if (type !== 'function') {
                console.log(`  ❌ ${name} (${type})`);
            }
        });
        
        const hasProblems = totalButtons > workingButtons || uniqueErrors.length > 0;
        
        if (hasProblems) {
            console.log('\n⚠️ PROBLEME ERKANNT - REPARATUR ERFORDERLICH');
        } else {
            console.log('\n✅ ALLE DETAIL-BUTTONS FUNKTIONIEREN');
        }
        
        return {
            success: !hasProblems,
            totalButtons,
            workingButtons,
            errors: uniqueErrors,
            missingFunctions: Object.entries(functionCheck).filter(([name, type]) => type !== 'function').map(([name]) => name)
        };
        
    } catch (error) {
        console.error('❌ Analyse-Fehler:', error);
        return { success: false, error: error.message };
    } finally {
        await browser.close();
    }
}

analyzeDetailButtons();