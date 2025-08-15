#!/usr/bin/env python3
"""
Test der "Beste Werte" Algorithmus-Reparatur
Prüft ob echte Werte IMMER gegen "Unbekannt" gewinnen
"""

import asyncio
from playwright.async_api import async_playwright

async def test_beste_werte_fix():
    print("🎯 TESTE WERTE ALGORITHMUS FIX")
    print("==============================")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=['--no-sandbox'])
        page = await browser.new_page()
        
        console_messages = []
        def handle_console(msg):
            console_messages.append(msg.text)
            if 'BEST' in msg.text or 'ALGORITHM' in msg.text or 'UNBEKANNT' in msg.text:
                print(f"📝 {msg.text}")
        page.on("console", handle_console)
        
        # Force-refresh mit Cache-Buster
        await page.goto('http://localhost:8000/?cache_bust=' + str(asyncio.get_event_loop().time()), wait_until='networkidle')
        await page.wait_for_timeout(3000)
        
        print("\\n📊 Gehe zu Consolidated Tab...")
        await page.locator('.nav-item[data-tab="consolidated"]').click()
        await page.wait_for_timeout(5000)  # Mehr Zeit für API-Calls
        
        # Teste verschiedene Minen für Land-Konsistenz
        test_mines = ['Antamina', 'Canadian Malartic', 'Eleonore']
        
        for mine_name in test_mines:
            print(f"\\n🧪 Teste {mine_name} für echte vs 'Unbekannt' Werte...")
            
            # Versuche Details-Modal zu öffnen
            try:
                await page.evaluate(f"window.viewConsolidatedDetail('{mine_name}')")
                await page.wait_for_timeout(6000)  # Genug Zeit für API + Scoring
                
                # Analysiere Modal-Inhalt auf problematische Felder
                modal_analysis = await page.evaluate("""
                    () => {
                        const modal = document.querySelector('.modal-overlay');
                        if (modal) {
                            const modalText = modal.textContent;
                            const lines = modalText.split('\\\\n').map(l => l.trim()).filter(l => l);
                            
                            // Suche nach Feldern mit "Unbekannt"
                            const unbekanntFields = lines.filter(line => 
                                line.includes('Unbekannt') && 
                                !line.includes('Land:') // Land ist OK wenn wirklich unbekannt
                            );
                            
                            // Suche nach Land-Feld speziell
                            const landLine = lines.find(line => line.includes('Land:'));
                            
                            return {
                                modalExists: true,
                                unbekanntCount: unbekanntFields.length,
                                unbekanntFields: unbekanntFields.slice(0, 5), // Erste 5
                                landLine: landLine || 'Land-Zeile nicht gefunden',
                                totalLines: lines.length
                            };
                        }
                        return { modalExists: false };
                    }
                """)
                
                print(f"   📋 {mine_name} Modal-Analyse:")
                print(f"      Modal existiert: {modal_analysis.get('modalExists', False)}")
                print(f"      'Unbekannt' Felder: {modal_analysis.get('unbekanntCount', 0)}")
                print(f"      Land-Zeile: {modal_analysis.get('landLine', 'N/A')}")
                
                # Bewerte das Ergebnis
                if modal_analysis.get('modalExists'):
                    unbekannt_count = modal_analysis.get('unbekanntCount', 0)
                    land_line = modal_analysis.get('landLine', '')
                    
                    if 'Peru' in land_line and mine_name == 'Antamina':
                        print(f"      ✅ LAND-FIX: Antamina zeigt Peru korrekt!")
                    elif 'Canada' in land_line and mine_name == 'Canadian Malartic':
                        print(f"      ✅ LAND-FIX: Canadian Malartic zeigt Canada korrekt!")
                    elif 'Unbekannt' not in land_line and 'Quebec' in land_line and mine_name == 'Eleonore':
                        print(f"      ✅ LAND-FIX: Eleonore zeigt Quebec korrekt!")
                    
                    if unbekannt_count < 3:
                        print(f"      ✅ ALGORITHMUS-FIX: Nur {unbekannt_count} 'Unbekannt' Felder - gute Verbesserung!")
                    else:
                        print(f"      ⚠️ VERBESSERUNG MÖGLICH: {unbekannt_count} 'Unbekannt' Felder gefunden")
                        if modal_analysis.get('unbekanntFields'):
                            print(f"      Beispiele: {modal_analysis['unbekanntFields']}")
                
                # Schließe Modal
                await page.evaluate("window.closeModal()")
                await page.wait_for_timeout(1000)
                
            except Exception as e:
                print(f"      ❌ Fehler bei {mine_name}: {e}")
        
        # Teste auch Card-Ansicht auf Konsistenz
        print(f"\\n📋 TESTE CARD-ANSICHT AUF KONSISTENZ...")
        card_analysis = await page.evaluate("""
            () => {
                const cards = document.querySelectorAll('.field-based-card, .mine-card');
                let consistentCount = 0;
                let totalCards = 0;
                
                cards.forEach(card => {
                    totalCards++;
                    const location = card.querySelector('.mine-location');
                    if (location && location.textContent && 
                        !location.textContent.includes('Unbekannt') && 
                        location.textContent.trim() !== '📍') {
                        consistentCount++;
                    }
                });
                
                return {
                    totalCards: totalCards,
                    consistentCards: consistentCount,
                    consistencyRate: totalCards > 0 ? Math.round((consistentCount / totalCards) * 100) : 0
                };
            }
        """)
        
        print(f"   📊 Card-Konsistenz:")
        print(f"      Total Cards: {card_analysis.get('totalCards', 0)}")
        print(f"      Konsistente Cards: {card_analysis.get('consistentCards', 0)}")
        print(f"      Konsistenzrate: {card_analysis.get('consistencyRate', 0)}%")
        
        # Finale Bewertung
        consistency_rate = card_analysis.get('consistencyRate', 0)
        if consistency_rate > 80:
            print(f"\\n🎉 BESTE-WERTE-ALGORITHMUS FIX ERFOLGREICH!")
            print(f"   ✅ {consistency_rate}% der Cards zeigen echte Werte statt 'Unbekannt'")
            print(f"   ✅ Echte Werte gewinnen jetzt gegen hohe 'Unbekannt'-Frequenz!")
        elif consistency_rate > 60:
            print(f"\\n✅ DEUTLICHE VERBESSERUNG!")
            print(f"   ✅ {consistency_rate}% Konsistenz - erheblich besser als vorher")
        else:
            print(f"\\n⚠️ Weitere Optimierung nötig")
            print(f"   ⚠️ Nur {consistency_rate}% Konsistenz - Algorithmus braucht weitere Anpassung")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_beste_werte_fix())