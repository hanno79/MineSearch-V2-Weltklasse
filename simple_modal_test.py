#!/usr/bin/env python3
"""
Author: rahn
Datum: 11.08.2025
Version: 1.0
Beschreibung: Einfacher Modal-Test für MineSearch 2.0
"""

import asyncio
from playwright.async_api import async_playwright

async def simple_modal_test():
    """Einfacher Modal-Test"""
    print("🧪 SIMPLE MODAL TEST")
    print("=" * 50)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=700)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # Lade die Seite
            print("🌐 Loading MineSearch 2.0...")
            await page.goto("http://localhost:8000")
            await page.wait_for_load_state('networkidle')
            
            # Warte auf JavaScript Loading
            await page.wait_for_timeout(3000)
            
            # Screenshot der geladenen Seite
            await page.screenshot(path="/app/loaded_page.png", full_page=True)
            print("📸 Screenshot: loaded_page.png")
            
            # Teste ob showModelDetails Funktion verfügbar ist
            function_exists = await page.evaluate('typeof window.showModelDetails === "function"')
            print(f"showModelDetails function exists: {function_exists}")
            
            # Teste ob ModalManager verfügbar ist
            modal_manager_exists = await page.evaluate('typeof window.ModalManager !== "undefined"')
            print(f"ModalManager exists: {modal_manager_exists}")
            
            if function_exists and modal_manager_exists:
                print("✅ Modal functions are loaded!")
                
                # Teste Modal direkt mit JavaScript
                print("🔄 Testing modal with JavaScript call...")
                modal_result = await page.evaluate('''
                    try {
                        window.showModelDetails("openrouter:test-model");
                        return "success";
                    } catch (error) {
                        return "error: " + error.message;
                    }
                ''')
                
                print(f"Modal test result: {modal_result}")
                
                if modal_result == "success":
                    await page.wait_for_timeout(2000)
                    
                    # Screenshot mit geöffnetem Modal
                    await page.screenshot(path="/app/modal_opened.png", full_page=True)
                    print("📸 Screenshot: modal_opened.png")
                    
                    # Prüfe ob Modal sichtbar ist
                    modal_visible = await page.evaluate('document.querySelectorAll(".model-details-modal").length > 0')
                    
                    if modal_visible:
                        print("🎉 SUCCESS: Modal opened successfully!")
                        
                        # Teste Modal schließen
                        close_result = await page.evaluate('''
                            try {
                                const modal = document.querySelector(".model-details-modal");
                                const closeBtn = modal.querySelector("button");
                                if (closeBtn) closeBtn.click();
                                return "closed";
                            } catch (error) {
                                return "error: " + error.message;
                            }
                        ''')
                        
                        print(f"Modal close result: {close_result}")
                        await page.wait_for_timeout(1000)
                        
                        # Final screenshot
                        await page.screenshot(path="/app/modal_closed.png", full_page=True)
                        print("📸 Screenshot: modal_closed.png")
                        
                        return True
                    else:
                        print("❌ Modal not visible in DOM")
                        return False
                else:
                    print(f"❌ Modal test failed: {modal_result}")
                    return False
            else:
                print("❌ Modal functions not loaded")
                return False
                
        except Exception as e:
            print(f"❌ Test failed: {e}")
            return False
            
        finally:
            await browser.close()

async def main():
    """Hauptfunktion"""
    success = await simple_modal_test()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 SIMPLE MODAL TEST: SUCCESS!")
    else:
        print("❌ SIMPLE MODAL TEST: FAILED")
    print("=" * 50)
    
    return success

if __name__ == '__main__':
    result = asyncio.run(main())
    exit(0 if result else 1)