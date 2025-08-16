#!/usr/bin/env python3
"""
Author: rahn
Datum: 14.08.2025
Version: 1.0
Beschreibung: Test der verbesserten Modal-Schließ-Funktion
"""

import asyncio
from playwright.async_api import async_playwright

async def test_improved_modal():
    """Test der verbesserten Modal-Schließ-Funktion"""
    print("🔲 VERBESSERTER MODAL TEST")
    print("=========================")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=['--no-sandbox'])
        page = await browser.new_page()
        
        console_logs = []
        def handle_console(msg):
            console_logs.append(f"[{msg.type}] {msg.text}")
            print(f"🖥️ [{msg.type.upper()}] {msg.text}")
        page.on("console", handle_console)
        
        print("🌐 Loading page...")
        await page.goto('http://localhost:8000/', wait_until='networkidle')
        await page.wait_for_timeout(5000)
        
        print("\n📊 Gehe zu Consolidated Tab...")
        consolidated_tab = page.locator('.nav-item[data-tab="consolidated"]')
        await consolidated_tab.click()
        await page.wait_for_timeout(3000)
        
        # Test 1: Einfaches Test-Modal
        print("\n1️⃣ Teste Test-Modal mit verbesserter closeModal()...")
        await page.evaluate("""
            window.showModal('Verbesserter Modal Test', 
                '<p><strong>Test der verbesserten Modal-Funktion!</strong></p>' +
                '<p>Dieses Modal sollte sich mit dem roten ✕ Button schließen lassen.</p>' +
                '<p>Schaue in die Konsole für Debug-Informationen.</p>', 
                'medium')
        """)
        await page.wait_for_timeout(2000)
        
        modal = page.locator('.modal-overlay')
        modal_count = await modal.count()
        print(f"📋 Modal sichtbar: {modal_count > 0}")
        
        if modal_count > 0:
            print("🖱️ Teste closeModal() mit Debug-Ausgaben...")
            await page.evaluate("window.closeModal()")
            await page.wait_for_timeout(2000)
            
            modal_after = await modal.count()
            success = modal_after == 0
            print(f"✅ Modal geschlossen: {success}")
            
            # Zeige relevante Console-Logs
            modal_logs = [log for log in console_logs if 'MODAL' in log]
            if modal_logs:
                print("\n📝 Modal Debug-Logs:")
                for log in modal_logs[-10:]:  # Zeige letzte 10
                    print(f"   {log}")
        
        # Test 2: Teste Details-Modal wenn verfügbar
        print("\n2️⃣ Teste Details-Modal (falls verfügbar)...")
        try:
            # Suche nach einer Mine für Details-Test
            mine_names = await page.evaluate("""
                () => {
                    const cards = document.querySelectorAll('.field-based-card, .mine-card');
                    const names = [];
                    for (let card of cards) {
                        const nameEl = card.querySelector('.mine-name, h3, h4');
                        if (nameEl) {
                            const name = nameEl.textContent.trim();
                            if (name && name.length > 2 && !name.includes('MineSearch')) {
                                names.push(name);
                            }
                        }
                    }
                    return names.slice(0, 1);
                }
            """)
            
            if mine_names:
                print(f"🏭 Teste Details für: {mine_names[0]}")
                await page.evaluate(f"window.viewConsolidatedDetail('{mine_names[0]}')")
                await page.wait_for_timeout(3000)
                
                modal_count = await modal.count()
                if modal_count > 0:
                    print("📋 Details-Modal geöffnet")
                    await page.evaluate("window.closeModal()")
                    await page.wait_for_timeout(2000)
                    
                    modal_after = await modal.count()
                    print(f"✅ Details-Modal geschlossen: {modal_after == 0}")
                else:
                    print("⚠️ Details-Modal nicht geöffnet")
            else:
                print("⚠️ Keine Mine-Namen für Test gefunden")
        except Exception as e:
            print(f"⚠️ Details-Test-Fehler: {e}")
        
        print("\n🎯 VERBESSERTER MODAL TEST ABGESCHLOSSEN")
        print("=======================================")
        
        # Zusammenfassung der Console-Logs
        error_logs = [log for log in console_logs if 'ERROR' in log.upper()]
        if error_logs:
            print(f"🚨 {len(error_logs)} Fehler gefunden:")
            for log in error_logs[:3]:
                print(f"   {log}")
        else:
            print("✅ Keine kritischen Fehler")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_improved_modal())