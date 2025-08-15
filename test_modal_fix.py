#!/usr/bin/env python3
"""
Author: rahn
Datum: 15.08.2025
Version: 1.0
Beschreibung: Direkter Modal-Fix Test ohne Timeouts
"""

import asyncio
from playwright.async_api import async_playwright

async def test_modal_fix():
    """Direkter Test der Modal-Fix"""
    print("🔧 MODAL-FIX TEST")
    print("=================")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=['--no-sandbox'])
        page = await browser.new_page()
        
        console_messages = []
        def handle_console(msg):
            console_messages.append(f"[{msg.type}] {msg.text}")
            if 'MODAL' in msg.text:
                print(f"📝 {msg.text}")
        page.on("console", handle_console)
        
        print("🌐 Loading page...")
        await page.goto('http://localhost:8000/', wait_until='networkidle')
        await page.wait_for_timeout(5000)
        
        print("\n📊 Gehe zu Consolidated Tab...")
        consolidated_tab = page.locator('.nav-item[data-tab="consolidated"]')
        await consolidated_tab.click()
        await page.wait_for_timeout(4000)
        
        # Test 1: Einfaches Modal
        print("\n1️⃣ Teste showModal() mit Debug...")
        await page.evaluate("""
            console.log('🔧 [TEST] Starte Modal-Test...');
            window.showModal('Modal Fix Test', 
                '<p><strong>Modal-System Test!</strong></p>' +
                '<p>Schaue in die Konsole für Debug-Details.</p>', 
                'medium');
        """)
        await page.wait_for_timeout(2000)
        
        # Prüfe Modal
        modals = await page.locator('.modal-overlay').count()
        print(f"📋 Modal-Overlays gefunden: {modals}")
        
        if modals > 0:
            print("🔧 Teste closeModal() mit erweiterten Debug-Ausgaben...")
            await page.evaluate("""
                console.log('🔧 [TEST] Rufe closeModal() auf...');
                try {
                    window.closeModal();
                    console.log('🔧 [TEST] closeModal() Aufruf beendet');
                } catch (error) {
                    console.error('🔧 [TEST] closeModal() Fehler:', error);
                }
            """)
            await page.wait_for_timeout(3000)
            
            modals_after = await page.locator('.modal-overlay').count()
            print(f"📋 Modal-Overlays nach closeModal(): {modals_after}")
            
            if modals_after == 0:
                print("✅ MODAL-SCHLIESSEN: ERFOLGREICH!")
            else:
                print("❌ MODAL-SCHLIESSEN: FEHLGESCHLAGEN")
        
        # Test 2: Teste Mine-Details wenn möglich
        print("\n2️⃣ Teste Mine-Details...")
        mine_names = await page.evaluate("""
            () => {
                // Suche nach Mine-Namen in Cards
                const cards = document.querySelectorAll('.field-based-card, .mine-card');
                const names = [];
                for (let card of cards) {
                    const nameEl = card.querySelector('.mine-name, h3, h4');
                    if (nameEl) {
                        const text = nameEl.textContent.trim();
                        if (text && text.length > 2 && !text.includes('MineSearch')) {
                            names.push(text);
                        }
                    }
                }
                return names.slice(0, 1);  // Nur eine für Test
            }
        """)
        
        if mine_names:
            mine_name = mine_names[0]
            print(f"🏭 Teste Details für: {mine_name}")
            
            await page.evaluate(f"""
                console.log('🔧 [TEST] Rufe viewConsolidatedDetail("{mine_name}") auf...');
                try {{
                    window.viewConsolidatedDetail('{mine_name}');
                    console.log('🔧 [TEST] viewConsolidatedDetail() Aufruf beendet');
                }} catch (error) {{
                    console.error('🔧 [TEST] viewConsolidatedDetail() Fehler:', error);
                }}
            """)
            await page.wait_for_timeout(5000)  # Mehr Zeit für API-Call
            
            # Prüfe Details-Modal
            details_modals = await page.locator('.modal-overlay').count()
            print(f"📋 Details-Modal-Overlays: {details_modals}")
            
            if details_modals > 0:
                print("✅ DETAILS-MODAL: GEÖFFNET!")
                
                # Teste Details-Modal schließen
                await page.evaluate("""
                    console.log('🔧 [TEST] Schließe Details-Modal...');
                    window.closeModal();
                """)
                await page.wait_for_timeout(2000)
                
                details_after = await page.locator('.modal-overlay').count()
                print(f"📋 Details-Modal nach closeModal(): {details_after}")
                print(f"✅ DETAILS-MODAL SCHLIESSEN: {'ERFOLGREICH' if details_after == 0 else 'FEHLGESCHLAGEN'}")
        
        print("\n🎯 MODAL-FIX TEST ABGESCHLOSSEN")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_modal_fix())
