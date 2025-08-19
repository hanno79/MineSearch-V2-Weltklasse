#!/usr/bin/env python3
"""
Test Details-Modal spezifisch
"""

import asyncio
from playwright.async_api import async_playwright

async def test_details_modal():
    """Teste Details-Modal spezifisch"""
    print("🏭 DETAILS-MODAL TEST")
    print("====================")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=['--no-sandbox'])
        page = await browser.new_page()
        
        console_messages = []
        def handle_console(msg):
            console_messages.append(f"[{msg.type}] {msg.text}")
            if any(keyword in msg.text for keyword in ['MODAL', 'CONSOLIDATED', 'API']):
                print(f"📝 {msg.text}")
        page.on("console", handle_console)
        
        print("🌐 Loading page...")
        await page.goto('http://localhost:8000/', wait_until='networkidle')
        await page.wait_for_timeout(5000)
        
        print("\n📊 Gehe zu Consolidated Tab...")
        consolidated_tab = page.locator('.nav-item[data-tab="consolidated"]')
        await consolidated_tab.click()
        await page.wait_for_timeout(4000)
        
        # Direkte Details-Button-Suche 
        print("\n🔍 Suche nach Details-Buttons...")
        buttons = await page.evaluate("""
            () => {
                // Suche verschiedene Button-Patterns
                const patterns = [
                    'button[onclick*="viewConsolidated"]',
                    '.btn-details',
                    'button:has-text("Details")',
                    'button:has-text("📊")'
                ];
                
                let allButtons = [];
                patterns.forEach(pattern => {
                    try {
                        const buttons = document.querySelectorAll(pattern);
                        allButtons.push(...buttons);
                    } catch (e) {
                        // Pattern invalid
                    }
                });
                
                // Entferne Duplikate
                const uniqueButtons = [...new Set(allButtons)];
                
                return uniqueButtons.map((btn, index) => ({
                    index,
                    text: btn.textContent.trim(),
                    onclick: btn.getAttribute('onclick'),
                    visible: btn.offsetParent !== null
                }));
            }
        """)
        
        print(f"📋 Gefundene Details-Buttons: {len(buttons)}")
        for btn in buttons[:3]:  # Zeige erste 3
            print(f"   Button {btn['index']}: '{btn['text']}' onClick: {btn['onclick']}")
        
        # Teste direkt mit Mine-Namen aus den Cards
        print("\n🏭 Teste mit echtem Mine-Namen...")
        mine_names = await page.evaluate("""
            () => {
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
                return names.slice(0, 2);
            }
        """)
        
        if mine_names:
            test_mine = mine_names[0]
            print(f"🏭 Teste Details für: {test_mine}")
            
            # Teste API-Endpoint direkt
            print("📡 Teste API-Endpoint...")
            api_result = await page.evaluate(f"""
                async () => {{
                    try {{
                        const response = await fetch('/api/consolidated/mine/' + encodeURIComponent('{test_mine}'));
                        const data = await response.json();
                        return {{
                            success: response.ok,
                            status: response.status,
                            hasData: data.success && data.data
                        }};
                    }} catch (error) {{
                        return {{ error: error.message }};
                    }}
                }}
            """)
            print(f"📡 API-Test: {api_result}")
            
            # Teste viewConsolidatedDetail() direkt
            print("🔧 Teste viewConsolidatedDetail() direkt...")
            await page.evaluate(f"""
                console.log('🔧 [TEST] Starte viewConsolidatedDetail("{test_mine}")...');
                window.viewConsolidatedDetail('{test_mine}');
            """)
            await page.wait_for_timeout(6000)  # Mehr Zeit für API-Call
            
            # Prüfe Modal
            modals = await page.locator('.modal-overlay').count()
            print(f"📋 Modal-Overlays nach viewConsolidatedDetail(): {modals}")
            
            if modals > 0:
                print("✅ DETAILS-MODAL GEÖFFNET!")
                
                # Teste closeModal()
                print("🔧 Teste closeModal()...")
                await page.evaluate("window.closeModal()")
                await page.wait_for_timeout(2000)
                
                modals_after = await page.locator('.modal-overlay').count()
                print(f"📋 Modal-Overlays nach closeModal(): {modals_after}")
                print(f"✅ DETAILS-MODAL SCHLIESSEN: {'ERFOLGREICH' if modals_after == 0 else 'FEHLGESCHLAGEN'}")
            else:
                print("❌ DETAILS-MODAL NICHT GEÖFFNET")
                
                # Debug: Console-Fehler?
                error_logs = [msg for msg in console_messages if 'error' in msg.lower()]
                if error_logs:
                    print("🚨 Console-Fehler:")
                    for log in error_logs[-3:]:
                        print(f"   {log}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_details_modal())
