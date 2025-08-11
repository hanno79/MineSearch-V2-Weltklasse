/**
 * Author: rahn
 * Datum: 10.08.2025
 * Version: 1.0
 * Beschreibung: Umfassender End-to-End Test des MineSearch 2.0 Tab-Systems
 */

const { chromium } = require('playwright');

async function comprehensiveEndToEndTest() {
    const browser = await chromium.launch();
    const page = await browser.newPage();
    
    console.log('🎯 UMFASSENDER END-TO-END TEST');
    console.log('==============================\n');
    
    // Collect all console messages
    const messages = [];
    page.on('console', msg => {
        messages.push(`${msg.type()}: ${msg.text()}`);
    });
    
    // Collect network errors
    const networkErrors = [];
    page.on('response', response => {
        if (!response.ok()) {
            networkErrors.push(`${response.status()}: ${response.url()}`);
        }
    });
    
    try {
        await page.goto('http://localhost:8000', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(5000); // Extended wait for full initialization
        
        console.log('✅ Seite vollständig geladen');
        
        // COMPREHENSIVE TAB TESTING
        const tabs = [
            {
                id: 'single-tab',
                name: 'Einzelsuche',
                formId: '#single_form',
                hasAutoLoading: false,
                expectedContent: 'Mine'
            },
            {
                id: 'csv-tab', 
                name: 'CSV-Upload',
                formId: '#csv_form',
                hasAutoLoading: false,
                expectedContent: 'CSV'
            },
            {
                id: 'sources-tab',
                name: 'Quellen',
                formId: '#sources_form',
                tableId: '#sources-table-container',
                hasAutoLoading: true,
                expectedContent: 'Domain',
                minContentLength: 3000
            },
            {
                id: 'statistics-tab',
                name: 'Statistiken', 
                formId: '#statistics_form',
                tableId: '#model-statistics-table-container',
                hasAutoLoading: true,
                expectedContent: 'Modell',
                minContentLength: 8000
            },
            {
                id: 'consolidated-tab',
                name: 'Konsolidiert',
                formId: '#consolidated_form', 
                tableId: '#consolidated-table-container',
                hasAutoLoading: true,
                expectedContent: 'Mine',
                minContentLength: 8000
            }
        ];
        
        let allTestsPassed = true;
        const testResults = [];
        
        for (const tab of tabs) {
            console.log(`\n🔍 TESTING: ${tab.name.toUpperCase()} TAB`);
            console.log('=' + '='.repeat(tab.name.length + 11));
            
            // Click tab
            await page.click(`label[for="${tab.id}"]`);
            await page.waitForTimeout(tab.hasAutoLoading ? 6000 : 2000);
            
            const result = {
                name: tab.name,
                formVisible: false,
                tableVisible: true, // Default true for non-table tabs
                hasContent: false,
                contentLength: 0,
                autoLoadingWorks: true, // Default true for non-auto-loading tabs
                passed: false
            };
            
            // Check form visibility
            const formVisible = await page.isVisible(tab.formId);
            result.formVisible = formVisible;
            console.log(`  Form sichtbar (${tab.formId}): ${formVisible ? '✅' : '❌'}`);
            
            // Check table visibility (if applicable)
            if (tab.tableId) {
                const tableVisible = await page.isVisible(tab.tableId);
                result.tableVisible = tableVisible;
                console.log(`  Tabelle sichtbar (${tab.tableId}): ${tableVisible ? '✅' : '❌'}`);
                
                // Check table content
                const tableContent = await page.textContent(tab.tableId);
                result.contentLength = tableContent ? tableContent.length : 0;
                result.hasContent = tableContent && 
                                  tableContent.includes(tab.expectedContent) &&
                                  tableContent.length >= tab.minContentLength;
                
                console.log(`  Tabelle hat Inhalt: ${result.hasContent ? '✅' : '❌'}`);
                console.log(`  Inhaltslänge: ${result.contentLength} Zeichen`);
                
                if (tab.hasAutoLoading) {
                    result.autoLoadingWorks = result.hasContent;
                    console.log(`  Auto-Loading funktioniert: ${result.autoLoadingWorks ? '✅' : '❌'}`);
                }
            } else {
                // For non-table tabs, check form content
                const formContent = await page.textContent(tab.formId);
                result.contentLength = formContent ? formContent.length : 0;
                result.hasContent = formContent && formContent.includes(tab.expectedContent);
                console.log(`  Form hat Inhalt: ${result.hasContent ? '✅' : '❌'}`);
            }
            
            // Overall tab assessment
            result.passed = result.formVisible && result.tableVisible && result.hasContent && result.autoLoadingWorks;
            console.log(`  GESAMTBEWERTUNG: ${result.passed ? '✅ BESTANDEN' : '❌ FEHLGESCHLAGEN'}`);
            
            testResults.push(result);
            if (!result.passed) allTestsPassed = false;
        }
        
        // TAB SWITCHING TEST
        console.log('\n🔄 TAB-SWITCHING STRESS TEST');
        console.log('=============================');
        
        let switchingWorks = true;
        for (let i = 0; i < 3; i++) {
            console.log(`\nRunde ${i + 1}:`);
            for (const tab of tabs) {
                await page.click(`label[for="${tab.id}"]`);
                await page.waitForTimeout(500);
                const isActive = await page.isChecked(`#${tab.id}`);
                console.log(`  ${tab.name}: ${isActive ? '✅' : '❌'}`);
                if (!isActive) switchingWorks = false;
            }
        }
        
        // NETWORK & CONSOLE ANALYSIS
        console.log('\n🌐 NETZWERK & KONSOLE ANALYSE');
        console.log('==============================');
        
        const criticalErrors = messages.filter(msg => 
            msg.includes('ERROR') || msg.includes('404') || msg.includes('Failed')
        );
        
        console.log(`Network Errors: ${networkErrors.length}`);
        if (networkErrors.length > 0) {
            networkErrors.forEach(error => console.log(`  ❌ ${error}`));
        }
        
        console.log(`Console Errors: ${criticalErrors.length}`);
        if (criticalErrors.length > 0) {
            criticalErrors.forEach(error => console.log(`  ❌ ${error}`));
        }
        
        // FINAL ASSESSMENT
        console.log('\n🏆 FINALE GESAMTBEWERTUNG');
        console.log('=========================');
        
        const passedTabs = testResults.filter(r => r.passed).length;
        const hasNoErrors = networkErrors.length === 0 && criticalErrors.length === 0;
        
        console.log(`✅ Tabs bestanden: ${passedTabs}/5`);
        console.log(`✅ Tab-Switching: ${switchingWorks ? 'FUNKTIONIERT' : 'FEHLGESCHLAGEN'}`);
        console.log(`✅ Keine kritischen Fehler: ${hasNoErrors ? 'JA' : 'NEIN'}`);
        
        // Detailed results per tab
        console.log('\n📊 DETAILLIERTE TAB-ERGEBNISSE:');
        testResults.forEach(result => {
            console.log(`  ${result.name}: ${result.passed ? '✅' : '❌'} (${result.contentLength} Zeichen)`);
        });
        
        const overallSuccess = allTestsPassed && switchingWorks && hasNoErrors;
        
        console.log('\n' + '='.repeat(50));
        if (overallSuccess) {
            console.log('🎉 VOLLSTÄNDIGER ERFOLG! ALLE TESTS BESTANDEN!');
            console.log('🏆 MineSearch 2.0 Tab-System ist vollständig funktional!');
            console.log('✅ Alle 5 Tabs zeigen Daten korrekt an');
            console.log('✅ Auto-Loading funktioniert perfekt');
            console.log('✅ Tab-Navigation ohne Konflikte');
            console.log('✅ Keine kritischen Fehler');
        } else {
            console.log('❌ EINIGE TESTS FEHLGESCHLAGEN');
            console.log('⚠️ Weitere Optimierungen erforderlich');
        }
        console.log('='.repeat(50));
        
        return overallSuccess;
        
    } catch (error) {
        console.error('❌ Test-Fehler:', error);
        return false;
    } finally {
        await browser.close();
    }
}

comprehensiveEndToEndTest();