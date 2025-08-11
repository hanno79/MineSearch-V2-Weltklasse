/**
 * Author: rahn
 * Datum: 10.08.2025
 * Version: 1.0
 * Beschreibung: Finale Validierung aller 5 Tabs nach Fix-Completion
 */

const { chromium } = require('playwright');

async function validateAllTabs() {
    const browser = await chromium.launch();
    const page = await browser.newPage();
    
    console.log('🎯 FINALE VALIDIERUNG ALLER TABS');
    console.log('==================================\n');
    
    const tabs = [
        { id: 'single-tab', name: 'Einzelsuche', container: '#single_form' },
        { id: 'csv-tab', name: 'CSV-Upload', container: '#csv_form' },
        { id: 'sources-tab', name: 'Quellen', container: '#sources_form', dataContainer: '#sources-table-container' },
        { id: 'statistics-tab', name: 'Statistiken', container: '#statistics_form', dataContainer: '#model-statistics-table-container' },
        { id: 'consolidated-tab', name: 'Konsolidiert', container: '#consolidated_form', dataContainer: '#consolidated-table-container' }
    ];
    
    try {
        await page.goto('http://localhost:8000', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(2000);
        
        console.log('✅ Seite geladen\n');
        
        let allTabsWorking = true;
        
        for (const tab of tabs) {
            console.log(`🔍 TEST: ${tab.name} Tab...`);
            
            // Click tab
            await page.click(`label[for="${tab.id}"]`);
            await page.waitForTimeout(3000); // Wait for auto-loading
            
            // Check form visibility
            const formVisible = await page.isVisible(tab.container);
            console.log(`  ${tab.container} sichtbar: ${formVisible ? '✅' : '❌'}`);
            
            // Check data container if exists
            if (tab.dataContainer) {
                const dataVisible = await page.isVisible(tab.dataContainer);
                const dataContent = await page.textContent(tab.dataContainer);
                const hasContent = dataContent && dataContent.trim().length > 100;
                
                console.log(`  ${tab.dataContainer} sichtbar: ${dataVisible ? '✅' : '❌'}`);
                console.log(`  ${tab.dataContainer} hat Inhalt: ${hasContent ? '✅' : '❌'}`);
                
                if (!formVisible || !dataVisible || !hasContent) {
                    allTabsWorking = false;
                }
            } else {
                if (!formVisible) {
                    allTabsWorking = false;
                }
            }
            
            console.log(''); // Empty line for readability
        }
        
        // Final assessment
        console.log('🎯 FINALE BEWERTUNG:');
        console.log('====================');
        if (allTabsWorking) {
            console.log('🎉 ALLE 5 TABS FUNKTIONIEREN KORREKT!');
            console.log('✅ Tab-Navigation: Funktional');
            console.log('✅ Auto-Loading: Funktional'); 
            console.log('✅ Daten-Anzeige: Funktional');
            console.log('✅ CSS-Display: Funktional');
            console.log('\n🏆 TAB-SYSTEM VOLLSTÄNDIG REPARIERT!');
        } else {
            console.log('❌ Einige Tabs haben noch Probleme');
        }
        
    } catch (error) {
        console.error('❌ Validierungs-Fehler:', error);
    } finally {
        await browser.close();
    }
}

validateAllTabs();