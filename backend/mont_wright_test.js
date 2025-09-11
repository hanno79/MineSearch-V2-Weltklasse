const { chromium } = require('playwright');

async function testMontWrightMine() {
    console.log('🚀 Starte Browser-Test für Mont Wright Mine...');
    
    // Browser starten
    const browser = await chromium.launch({ 
        headless: false,  // Sichtbarer Browser für bessere Überwachung
        args: ['--disable-web-security', '--disable-features=VizDisplayCompositor']
    });
    
    const page = await browser.newPage();
    
    try {
        console.log('📡 Verbinde zu MineSearch Frontend...');
        await page.goto('http://localhost:8000', { waitUntil: 'networkidle' });
        
        // Screenshot der Startseite
        await page.screenshot({ path: 'mont_wright_test_1_homepage.png', fullPage: true });
        console.log('📸 Screenshot: Homepage gespeichert');
        
        // Zur Einzelsuche navigieren
        console.log('🔍 Navigiere zur Einzelsuche...');
        await page.click('text=Einzelsuche');
        await page.waitForTimeout(2000);
        
        // Mont Wright Daten eingeben
        console.log('✍️ Gebe Mont Wright Suchparameter ein...');
        await page.fill('input[placeholder*="Mine"]', 'Mont Wright');
        await page.fill('input[placeholder*="Land"]', 'Kanada');
        
        // Modelle auswählen (3 verschiedene für gute Abdeckung)
        console.log('🤖 Wähle AI-Modelle aus...');
        await page.check('input[value="openrouter:deepseek-free"]');
        await page.check('input[value="openrouter:claude-3.5-sonnet"]'); 
        await page.check('input[value="tavily:search"]');
        
        // Screenshot vor dem Suche-Start
        await page.screenshot({ path: 'mont_wright_test_2_before_search.png', fullPage: true });
        console.log('📸 Screenshot: Vor der Suche gespeichert');
        
        // Suche starten
        console.log('🚀 Starte Suche...');
        await page.click('button[type="submit"]');
        
        // Auf Ergebnisse warten (längerer Timeout für echte Suche)
        console.log('⏳ Warte auf Suchergebnisse...');
        await page.waitForSelector('.results-table', { timeout: 120000 }); // 2 Minuten
        
        // Screenshot der Ergebnisse
        await page.screenshot({ path: 'mont_wright_test_3_results.png', fullPage: true });
        console.log('📸 Screenshot: Ergebnisse gespeichert');
        
        // KRITISCHE VALIDIERUNG: Prüfe neue Felder
        console.log('🔍 Validiere neue Fördermenge-Felder...');
        
        // Prüfe Header der Ergebnistabelle
        const tableHeaders = await page.$$eval('table thead th', headers => 
            headers.map(h => h.textContent.trim())
        );
        
        console.log('📋 Gefundene Tabellen-Header:', tableHeaders);
        
        // Validierung der neuen Felder
        const hasRohstoffField = tableHeaders.some(h => h.includes('Fördermenge/Jahr Rohstoff'));
        const hasAbraumField = tableHeaders.some(h => h.includes('Fördermenge/Jahr Abraum'));
        const hasOldField = tableHeaders.some(h => h === 'Fördermenge/Jahr');
        
        console.log('✅ Validierungsergebnisse:');
        console.log(`   - Fördermenge/Jahr Rohstoff: ${hasRohstoffField ? '✅ VORHANDEN' : '❌ FEHLT'}`);
        console.log(`   - Fördermenge/Jahr Abraum: ${hasAbraumField ? '✅ VORHANDEN' : '❌ FEHLT'}`);
        console.log(`   - Alte Fördermenge/Jahr: ${hasOldField ? '❌ NOCH VORHANDEN (FEHLER)' : '✅ ENTFERNT'}`);
        
        // Prüfe Dateninhalt
        console.log('📊 Prüfe Dateninhalt der neuen Felder...');
        
        const tableData = await page.$$eval('table tbody tr', rows => 
            rows.map(row => {
                const cells = Array.from(row.querySelectorAll('td'));
                return cells.map(cell => cell.textContent.trim());
            })
        );
        
        if (tableData.length > 0) {
            console.log('📋 Erste Datenzeile:', tableData[0]);
            
            // Finde Index der neuen Felder
            const rohstoffIndex = tableHeaders.findIndex(h => h.includes('Fördermenge/Jahr Rohstoff'));
            const abraumIndex = tableHeaders.findIndex(h => h.includes('Fördermenge/Jahr Abraum'));
            
            if (rohstoffIndex >= 0 && tableData[0][rohstoffIndex]) {
                console.log(`📈 Rohstoff-Produktion: ${tableData[0][rohstoffIndex]}`);
            }
            
            if (abraumIndex >= 0 && tableData[0][abraumIndex]) {
                console.log(`🏔️ Abraum-Extraktion: ${tableData[0][abraumIndex]}`);
            }
        }
        
        // Finale Screenshots mit Details
        await page.screenshot({ path: 'mont_wright_test_4_final_validation.png', fullPage: true });
        console.log('📸 Screenshot: Finale Validierung gespeichert');
        
        // Test-Zusammenfassung
        const testSuccess = hasRohstoffField && hasAbraumField && !hasOldField;
        console.log('\n🎯 TEST-ZUSAMMENFASSUNG:');
        console.log(`   Status: ${testSuccess ? '✅ ERFOLGREICH' : '❌ FEHLGESCHLAGEN'}`);
        console.log(`   Mine: Mont Wright, Quebec, Kanada`);
        console.log(`   Feldaufteilung: ${testSuccess ? 'Korrekt implementiert' : 'Probleme erkannt'}`);
        
        return {
            success: testSuccess,
            headers: tableHeaders,
            data: tableData[0] || [],
            screenshots: [
                'mont_wright_test_1_homepage.png',
                'mont_wright_test_2_before_search.png', 
                'mont_wright_test_3_results.png',
                'mont_wright_test_4_final_validation.png'
            ]
        };
        
    } catch (error) {
        console.error('❌ Test-Fehler:', error);
        await page.screenshot({ path: 'mont_wright_test_error.png', fullPage: true });
        throw error;
        
    } finally {
        // Browser schließen
        await browser.close();
        console.log('🔚 Browser geschlossen');
    }
}

// Test ausführen
testMontWrightMine()
    .then(result => {
        console.log('\n🏁 Test abgeschlossen:', result.success ? 'ERFOLGREICH ✅' : 'FEHLGESCHLAGEN ❌');
        process.exit(result.success ? 0 : 1);
    })
    .catch(error => {
        console.error('\n💥 Test-Ausführung fehlgeschlagen:', error);
        process.exit(1);
    });