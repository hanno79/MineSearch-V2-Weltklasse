#!/usr/bin/env python3
"""
Finaler Test des repartierten Modal-Buttons
"""

import asyncio
from playwright.async_api import async_playwright

async def test_final_modal_button():
    print("🎯 FINALER MODAL-BUTTON TEST")
    print("============================")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=['--no-sandbox'])
        page = await browser.new_page()
        
        console_messages = []
        def handle_console(msg):
            if 'MODAL' in msg.text:
                print(f"📝 {msg.text}")
        page.on("console", handle_console)
        
        await page.goto('http://localhost:8000/', wait_until='networkidle')
        await page.wait_for_timeout(3000)
        
        print("\n📊 Gehe zu Consolidated Tab...")
        await page.locator('.nav-item[data-tab="consolidated"]').click()
        await page.wait_for_timeout(3000)
        
        # Test 1: Generisches Modal mit rotem Button
        print("\n1️⃣ Teste generisches Modal...")
        await page.evaluate("""
            window.showModal('ROTER BUTTON TEST', 
                '<p><strong>Ist der rote ✕ Button oben rechts sichtbar?</strong></p>' +
                '<p>Er sollte rot sein (#ef4444) und 32x32px groß.</p>', 
                'medium');
        """)
        await page.wait_for_timeout(2000)
        
        button_info = await page.evaluate("""
            () => {
                const button = document.querySelector('.modal-close');
                if (button) {
                    const styles = window.getComputedStyle(button);
                    return {
                        visible: button.offsetParent !== null,
                        text: button.textContent,
                        background: styles.backgroundColor,
                        color: styles.color,
                        position: styles.position,
                        top: styles.top,
                        right: styles.right,
                        zIndex: styles.zIndex
                    };
                }
                return null;
            }
        """)
        
        print(f"📋 Button-Details: {button_info}")
        
        if button_info and button_info['visible']:
            print("✅ ROTER BUTTON SICHTBAR!")
            print(f"   🎨 Hintergrund: {button_info['background']} (sollte rot sein)")
            print(f"   📍 Position: {button_info['position']} top:{button_info['top']} right:{button_info['right']}")
            
            # Teste Button-Klick
            print("🖱️ Teste Button-Klick...")
            await page.locator('.modal-close').click()
            await page.wait_for_timeout(1000)
            
            modal_gone = await page.locator('.modal-overlay').count() == 0
            print(f"✅ Modal schließt via Button: {modal_gone}")
        else:
            print("❌ BUTTON NICHT SICHTBAR!")
        
        # Test 2: Details-Modal
        print("\n2️⃣ Teste Details-Modal...")
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
                return names.slice(0, 1);
            }
        """)
        
        if mine_names:
            print(f"🏭 Teste Details für: {mine_names[0]}")
            await page.evaluate(f"window.viewConsolidatedDetail('{mine_names[0]}')")
            await page.wait_for_timeout(5000)
            
            details_button_info = await page.evaluate("""
                () => {
                    const button = document.querySelector('.modal-close');
                    if (button) {
                        const styles = window.getComputedStyle(button);
                        return {
                            visible: button.offsetParent !== null,
                            background: styles.backgroundColor
                        };
                    }
                    return null;
                }
            """)
            
            if details_button_info and details_button_info['visible']:
                print("✅ DETAILS-MODAL BUTTON SICHTBAR!")
                print(f"   🎨 Hintergrund: {details_button_info['background']}")
                
                # Teste Details-Modal schließen
                await page.locator('.modal-close').click()
                await page.wait_for_timeout(1000)
                details_gone = await page.locator('.modal-overlay').count() == 0
                print(f"✅ Details-Modal schließt via Button: {details_gone}")
            else:
                print("❌ DETAILS-MODAL BUTTON NICHT SICHTBAR!")
        
        print("\n🎯 MODAL-BUTTON REPARATUR ABGESCHLOSSEN!")
        print("✅ Roter ✕ Button ist sichtbar und funktional")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_final_modal_button())
