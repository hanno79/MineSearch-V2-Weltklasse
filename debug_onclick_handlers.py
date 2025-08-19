#!/usr/bin/env python3
"""
Author: rahn
Datum: 14.08.2025
Version: 1.0
Beschreibung: Debug onClick-Handler für Details-Buttons
"""

import asyncio
from playwright.async_api import async_playwright

async def debug_onclick_handlers():
    """Debug onClick-Handler für Details-Buttons"""
    print("🔍 ONCLICK HANDLER DEBUG")
    print("========================")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=['--no-sandbox'])
        page = await browser.new_page()
        
        console_logs = []
        def handle_console(msg):
            console_logs.append(f"[{msg.type}] {msg.text}")
            if msg.type in ['error', 'warning']:
                print(f"🖥️ {msg.type.upper()}: {msg.text}")
        page.on("console", handle_console)
        
        print("🌐 Loading page...")
        await page.goto('http://localhost:8000/', wait_until='networkidle')
        await page.wait_for_timeout(5000)
        
        print("\n📊 Gehe zu Consolidated Tab...")
        consolidated_tab = page.locator('.nav-item[data-tab="consolidated"]')
        await consolidated_tab.click()
        await page.wait_for_timeout(4000)
        
        # Debug: Prüfe verfügbare Funktionen
        print("\n🔍 Prüfe verfügbare Funktionen im window-Scope...")
        available_functions = await page.evaluate("""
            () => {
                const functions = [
                    'viewConsolidatedDetail',
                    'showDetailModal', 
                    'showModal',
                    'closeModal'
                ];
                
                const results = {};
                functions.forEach(func => {
                    results[func] = {
                        exists: typeof window[func] !== 'undefined',
                        type: typeof window[func]
                    };
                });
                
                return results;
            }
        """)
        
        for func_name, info in available_functions.items():
            status = "✅" if info['exists'] else "❌"
            print(f"{status} {func_name}: {info['type'] if info['exists'] else 'NOT FOUND'}")
        
        # Debug: Prüfe Details-Button-Struktur
        print("\n🔍 Prüfe Details-Button-Struktur...")
        button_info = await page.evaluate("""
            () => {
                const buttons = document.querySelectorAll('button:contains("Details"), .btn-details, button[onclick*="viewConsolidated"]');
                const info = [];
                
                for (let i = 0; i < Math.min(3, buttons.length); i++) {
                    const btn = buttons[i];
                    info.push({
                        index: i,
                        text: btn.textContent.trim(),
                        onclick: btn.getAttribute('onclick'),
                        classes: btn.className,
                        visible: btn.offsetParent !== null
                    });
                }
                
                return info;
            }
        """)
        
        print("📋 Details-Button Informationen:")
        for btn in button_info:
            print(f"   Button {btn['index']}: '{btn['text']}'")
            print(f"   - onClick: {btn['onclick']}")
            print(f"   - Classes: {btn['classes']}")
            print(f"   - Visible: {btn['visible']}")
        
        # Teste direkte Funktionsausführung
        if available_functions.get('viewConsolidatedDetail', {}).get('exists'):
            print("\n🖱️ Teste direkte Funktionsausführung...")
            try:
                # Finde ersten Mine-Namen
                mine_names = await page.evaluate("""
                    () => {
                        const cards = document.querySelectorAll('.field-based-card, .mine-card');
                        const names = [];
                        for (let card of cards) {
                            const nameEl = card.querySelector('.mine-name, h3, h4');
                            if (nameEl) {
                                names.push(nameEl.textContent.trim());
                            }
                        }
                        return names.slice(0, 3);
                    }
                """)
                
                if mine_names:
                    print(f"🏭 Teste mit Mine: {mine_names[0]}")
                    await page.evaluate(f"window.viewConsolidatedDetail('{mine_names[0]}')")
                    await page.wait_for_timeout(3000)
                    
                    # Prüfe ob Modal erschienen ist
                    modal_count = await page.locator('.modal-overlay').count()
                    print(f"📋 Modal nach direktem Aufruf: {modal_count > 0}")
                    
                    if modal_count > 0:
                        print("✅ DIREKTE FUNKTION: SUCCESS!")
                        # Teste Modal schließen
                        await page.evaluate("window.closeModal()")
                        await page.wait_for_timeout(1000)
                        modal_after = await page.locator('.modal-overlay').count()
                        print(f"📋 Modal nach closeModal(): {modal_after == 0}")
                    else:
                        print("❌ DIREKTE FUNKTION: FAILED")
                else:
                    print("❌ Keine Mine-Namen gefunden")
            except Exception as e:
                print(f"❌ Fehler bei direkter Ausführung: {e}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_onclick_handlers())