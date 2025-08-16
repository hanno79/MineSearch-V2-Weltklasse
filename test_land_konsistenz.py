#!/usr/bin/env python3
"""
Test der Land-Feld Konsistenz zwischen Card und Details-Modal
"""

import asyncio
from playwright.async_api import async_playwright

async def test_land_konsistenz():
    print("🌍 LAND-KONSISTENZ TEST")
    print("======================")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=['--no-sandbox'])
        page = await browser.new_page()
        
        console_messages = []
        def handle_console(msg):
            if any(keyword in msg.text for keyword in ['MODAL', 'CONSOLIDATED', 'ERROR']):
                print(f"📝 {msg.text}")
        page.on("console", handle_console)
        
        await page.goto('http://localhost:8000/', wait_until='networkidle')
        await page.wait_for_timeout(3000)
        
        print("\n📊 Gehe zu Consolidated Tab...")
        await page.locator('.nav-item[data-tab="consolidated"]').click()
        await page.wait_for_timeout(4000)
        
        # Schritt 1: Hole Land-Info aus der ersten Card
        card_info = await page.evaluate("""
            () => {
                const firstCard = document.querySelector('.field-based-card, .mine-card');
                if (firstCard) {
                    const mineTitle = firstCard.querySelector('.mine-title, h3');
                    const mineLocation = firstCard.querySelector('.mine-location');
                    
                    return {
                        mineName: mineTitle ? mineTitle.textContent.trim() : 'Unbekannt',
                        location: mineLocation ? mineLocation.textContent.trim() : 'Unbekannt'
                    };
                }
                return null;
            }
        """)
        
        if not card_info:
            print("❌ Keine Card gefunden!")
            await browser.close()
            return
            
        print(f"\n📋 Card-Information:")
        print(f"   Mine: {card_info['mineName']}")
        print(f"   Location: {card_info['location']}")
        
        # Extrahiere Mine-Name (ohne ⛏️ Symbol)
        mine_name = card_info['mineName'].replace('⛏️ ', '').strip()
        
        # Schritt 2: Öffne Details-Modal für diese Mine
        print(f"\n🔍 Öffne Details für: {mine_name}")
        try:
            await page.evaluate(f"window.viewConsolidatedDetail('{mine_name}')")
            await page.wait_for_timeout(5000)  # Mehr Zeit für API-Call
            
            # Prüfe Details-Modal Land-Info
            modal_info = await page.evaluate("""
                () => {
                    const modal = document.querySelector('.modal-overlay');
                    if (modal) {
                        // Suche nach Land-Information im Modal
                        const summaryItems = modal.querySelectorAll('.summary-item');
                        for (let item of summaryItems) {
                            const text = item.textContent;
                            if (text.includes('Land:')) {
                                const landInfo = text.replace('Land:', '').trim();
                                return {
                                    modalExists: true,
                                    landInfo: landInfo
                                };
                            }
                        }
                        return { modalExists: true, landInfo: 'Nicht gefunden' };
                    }
                    return { modalExists: false };
                }
            """)
            
            print(f"\n📋 Details-Modal Information:")
            print(f"   Modal geöffnet: {modal_info.get('modalExists', False)}")
            print(f"   Land im Modal: {modal_info.get('landInfo', 'Nicht verfügbar')}")
            
            # Schritt 3: Konsistenz-Vergleich
            if modal_info.get('modalExists'):
                card_location = card_info['location'].replace('📍 ', '').strip()
                modal_land = modal_info.get('landInfo', '').strip()
                
                print(f"\n🔍 KONSISTENZ-VERGLEICH:")
                print(f"   Card Location:  '{card_location}'")
                print(f"   Modal Land:     '{modal_land}'")
                
                # Vergleiche (berücksichtige dass Modal mehr Details haben könnte)
                if modal_land == 'Nicht verfügbar':
                    print(f"   ❌ KONSISTENZ-FEHLER: Modal zeigt 'Nicht verfügbar' obwohl Card Location hat")
                elif card_location.lower() in modal_land.lower() or modal_land.lower() in card_location.lower():
                    print(f"   ✅ KONSISTENZ OK: Land-Information stimmt überein")
                else:
                    print(f"   ⚠️ KONSISTENZ-WARNUNG: Unterschiedliche Darstellung")
                
                # Teste spezifische Erwartung für Antamina
                if 'Antamina' in mine_name and 'Peru' in modal_land:
                    print(f"   ✅ SPEZIFISCH: Antamina zeigt Peru korrekt")
            
            # Schließe Modal
            await page.evaluate("window.closeModal()")
            await page.wait_for_timeout(1000)
            
        except Exception as e:
            print(f"❌ Fehler beim Details-Test: {e}")
        
        print(f"\n🎯 LAND-KONSISTENZ TEST ABGESCHLOSSEN")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_land_konsistenz())
