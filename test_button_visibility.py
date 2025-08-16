#!/usr/bin/env python3
import asyncio
from playwright.async_api import async_playwright

async def test_button_visibility():
    print("🔍 BUTTON VISIBILITY TEST")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=['--no-sandbox'])
        page = await browser.new_page()
        
        await page.goto('http://localhost:8000/', wait_until='networkidle')
        await page.wait_for_timeout(3000)
        
        print("\n📊 Gehe zu Consolidated Tab...")
        await page.locator('.nav-item[data-tab="consolidated"]').click()
        await page.wait_for_timeout(3000)
        
        print("\n🧪 Teste Test-Modal...")
        await page.evaluate("""
            window.showModal('Button Test', 
                '<p>Test des Modal-Buttons</p>', 
                'medium');
        """)
        await page.wait_for_timeout(2000)
        
        # Prüfe Button-Eigenschaften
        button_info = await page.evaluate("""
            () => {
                const button = document.querySelector('.modal-close');
                if (button) {
                    const styles = window.getComputedStyle(button);
                    return {
                        exists: true,
                        visible: button.offsetParent !== null,
                        text: button.textContent,
                        background: styles.backgroundColor,
                        color: styles.color,
                        width: styles.width,
                        height: styles.height,
                        display: styles.display
                    };
                }
                return { exists: false };
            }
        """)
        
        print(f"📋 Button-Info: {button_info}")
        
        # Teste auch Help-Modal aus Header
        print("\n🆘 Teste Help-Modal aus Header...")
        await page.locator('button:has-text("?")').click()  # Help-Button
        await page.wait_for_timeout(2000)
        
        help_button_info = await page.evaluate("""
            () => {
                const buttons = document.querySelectorAll('.modal-close');
                return Array.from(buttons).map((button, index) => {
                    const styles = window.getComputedStyle(button);
                    return {
                        index,
                        visible: button.offsetParent !== null,
                        text: button.textContent,
                        background: styles.backgroundColor,
                        color: styles.color,
                        onclick: button.getAttribute('onclick')
                    };
                });
            }
        """)
        
        print(f"📋 Help-Modal Buttons: {help_button_info}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_button_visibility())
