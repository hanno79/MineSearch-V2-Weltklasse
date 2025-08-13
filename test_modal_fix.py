#!/usr/bin/env python3
"""
Author: rahn
Datum: 11.08.2025
Version: 1.0
Beschreibung: Test Modal Fix für MineSearch 2.0
"""

import asyncio
from playwright.async_api import async_playwright

async def test_modal_fix():
    """Teste Modal-Fix"""
    print("🧪 TESTING MODAL FIX")
    print("=" * 50)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=500)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # Lade die Seite
            print("🌐 Loading MineSearch 2.0...")
            await page.goto("http://localhost:8000")
            await page.wait_for_load_state('networkidle')
            
            # Navigiere zu Statistics Tab (wo Details-Buttons sind)
            print("📊 Switching to Statistics tab...")
            stats_tab = await page.query_selector('input[value="statistics"]')
            if stats_tab:
                await stats_tab.click()
                await page.wait_for_timeout(2000)
                print("✅ Statistics tab activated")
            else:
                print("❌ Statistics tab not found")
                return False
            
            # Screenshot vor Modal-Test
            await page.screenshot(path="/app/before_modal_test.png", full_page=True)
            print("📸 Screenshot: before_modal_test.png")
            
            # Suche Details-Buttons
            await page.wait_for_timeout(3000)  # Warte auf Statistiken-Laden
            detail_buttons = await page.query_selector_all('button:has-text("Details")')
            
            print(f"🔍 Found {len(detail_buttons)} Details buttons")
            
            if detail_buttons:
                print("🖱️ Clicking first Details button...")
                
                # Setze Error-Handler
                page.on("pageerror", lambda error: print(f"Page Error: {error}"))
                
                # Klicke auf ersten Button
                await detail_buttons[0].click()
                await page.wait_for_timeout(2000)
                
                # Screenshot nach Modal-Test
                await page.screenshot(path="/app/after_modal_test.png", full_page=True)
                print("📸 Screenshot: after_modal_test.png")
                
                # Prüfe ob Modal geöffnet wurde
                modals = await page.query_selector_all('.model-details-modal, .modal')
                if modals:
                    print(f"✅ SUCCESS: {len(modals)} modal(s) opened!")
                    
                    # Teste Modal schließen mit Close-Button
                    close_button = await page.query_selector('.model-details-modal button:has-text("Schließen")')
                    if close_button:
                        print("🔄 Testing modal close...")
                        await close_button.click()
                        await page.wait_for_timeout(1000)
                        
                        # Prüfe ob Modal geschlossen
                        remaining_modals = await page.query_selector_all('.model-details-modal')
                        if len(remaining_modals) == 0:
                            print("✅ Modal closed successfully!")
                            return True
                        else:
                            print("⚠️ Modal not closed")
                    else:
                        print("❌ Close button not found")
                else:
                    print("❌ FAILED: No modals opened")
                    return False
            else:
                print("❌ No Details buttons found")
                return False
                
        except Exception as e:
            print(f"❌ Test failed: {e}")
            return False
            
        finally:
            await browser.close()

async def main():
    """Hauptfunktion"""
    success = await test_modal_fix()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 MODAL FIX TEST: SUCCESS!")
    else:
        print("❌ MODAL FIX TEST: FAILED")
    print("=" * 50)
    
    return success

if __name__ == '__main__':
    result = asyncio.run(main())
    exit(0 if result else 1)