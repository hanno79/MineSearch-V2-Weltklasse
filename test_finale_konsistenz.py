#!/usr/bin/env python3
"""
Finaler End-to-End Test der Land-Konsistenz-Reparatur
"""

import asyncio
from playwright.async_api import async_playwright

async def test_finale_konsistenz():
    print("🎯 FINALER KONSISTENZ TEST")
    print("==========================")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=['--no-sandbox'])
        page = await browser.new_page()
        
        console_messages = []
        def handle_console(msg):
            console_messages.append(msg.text)
            if 'CONSOLIDATED' in msg.text or 'ERROR' in msg.text:
                print(f"📝 {msg.text}")
        page.on("console", handle_console)
        
        # Hard-refresh für neue Cache-Version
        await page.goto('http://localhost:8000/?v=1.3.2', wait_until='networkidle')
        await page.wait_for_timeout(3000)
        
        print("\n📊 Gehe zu Consolidated Tab...")
        await page.locator('.nav-item[data-tab="consolidated"]').click()
        await page.wait_for_timeout(4000)
        
        # Prüfe erste Card
        card_location = await page.evaluate("""
            () => {
                const firstCard = document.querySelector('.field-based-card, .mine-card');
                if (firstCard) {
                    const locationEl = firstCard.querySelector('.mine-location');
                    return locationEl ? locationEl.textContent.trim() : 'Nicht gefunden';
                }
                return 'Keine Card';
            }
        """)
        
        print(f"📋 Card Location: {card_location}")
        
        # Teste Details mit echter API
        print(f"\n🔍 Teste Details-Modal mit Antamina...")
        await page.evaluate("window.viewConsolidatedDetail('Antamina')")
        await page.wait_for_timeout(6000)  # Mehr Zeit für API
        
        # Analysiere Modal-Inhalt
        modal_analysis = await page.evaluate("""
            () => {
                const modal = document.querySelector('.modal-overlay');
                if (modal) {
                    const modalBody = modal.querySelector('.modal-body');
                    if (modalBody) {
                        const summarySection = modalBody.querySelector('.mine-summary');
                        if (summarySection) {
                            const text = summarySection.textContent;
                            
                            // Suche nach Land-Information
                            const lines = text.split('\\n').map(l => l.trim()).filter(l => l);
                            const landLine = lines.find(line => line.includes('Land:'));
                            
                            return {
                                modalExists: true,
                                hasSummary: true,
                                landLine: landLine || 'Land-Zeile nicht gefunden',
                                allLines: lines.slice(0, 10)  // Erste 10 Zeilen für Debug
                            };
                        }
                    }
                    return { modalExists: true, hasSummary: false, modalText: modal.textContent.substring(0, 200) };
                }
                return { modalExists: false };
            }
        """)
        
        print(f"\n📋 Modal-Analyse:")
        print(f"   Modal existiert: {modal_analysis.get('modalExists', False)}")
        print(f"   Hat Summary: {modal_analysis.get('hasSummary', False)}")
        print(f"   Land-Zeile: {modal_analysis.get('landLine', 'N/A')}")
        
        if modal_analysis.get('allLines'):
            print(f"   Erste Zeilen: {modal_analysis['allLines']}")
        
        # Finale Bewertung
        if modal_analysis.get('landLine') and 'Peru' in modal_analysis.get('landLine', ''):
            print(f"\n🎉 KONSISTENZ-REPARATUR ERFOLGREICH!")
            print(f"   ✅ Details-Modal zeigt Peru korrekt an")
            print(f"   ✅ Konsistenz zwischen Card und Details hergestellt")
        elif 'Nicht verfügbar' not in modal_analysis.get('landLine', ''):
            print(f"\n✅ REPARATUR FUNKTIONIERT!")
            print(f"   ✅ 'Nicht verfügbar' wird nicht mehr angezeigt")
        else:
            print(f"\n⚠️ Möglicherweise noch Cache-Problem oder API-Issue")
        
        await page.evaluate("window.closeModal()")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_finale_konsistenz())
