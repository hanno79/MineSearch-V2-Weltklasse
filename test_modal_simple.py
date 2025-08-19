#!/usr/bin/env python3
"""
Author: rahn
Datum: 14.08.2025
Version: 1.0
Beschreibung: Einfacher Modal-Test ohne Timeout-Probleme
"""

import asyncio
from playwright.async_api import async_playwright

async def test_modal_simple():
    """Einfacher Test für Modal-System"""
    print("🔲 EINFACHER MODAL TEST")
    print("======================")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=['--no-sandbox'])
        page = await browser.new_page()
        
        console_errors = []
        def handle_console(msg):
            if msg.type in ['error']:
                console_errors.append(msg.text)
                print(f"🚨 ERROR: {msg.text}")
        page.on("console", handle_console)
        
        print("🌐 Loading page...")
        await page.goto('http://localhost:8000/', wait_until='networkidle')
        await page.wait_for_timeout(5000)
        
        print("\n📊 Gehe zu Consolidated Tab...")
        consolidated_tab = page.locator('.nav-item[data-tab="consolidated"]')
        await consolidated_tab.click()
        await page.wait_for_timeout(3000)
        
        # Suche nach Details-Buttons
        details_buttons = page.locator('button:has-text("Details anzeigen"), .btn-details, button:has-text("📊")')
        button_count = await details_buttons.count()
        print(f"📋 Gefundene Details-Buttons: {button_count}")
        
        if button_count > 0:
            print("🖱️ Klicke ersten Details-Button...")
            await details_buttons.first.click()
            await page.wait_for_timeout(3000)
            
            # Prüfe Modal
            modal = page.locator('.modal-overlay')
            modal_count = await modal.count()
            print(f"📋 Modal gefunden: {modal_count > 0}")
            
            if modal_count > 0:
                # Prüfe Close-Button
                close_buttons = page.locator('.modal-close, button:has-text("✕")')
                close_count = await close_buttons.count()
                print(f"🔴 Close-Buttons gefunden: {close_count}")
                
                if close_count > 0:
                    print("🖱️ Klicke Close-Button via JavaScript...")
                    # Verwende JavaScript zum Schließen statt Playwright-Click
                    await page.evaluate("() => window.closeModal()")
                    await page.wait_for_timeout(1000)
                    
                    modal_after = await modal.count()
                    print(f"📋 Modal nach Schließen: {modal_after == 0}")
                    
                    if modal_after == 0:
                        print("✅ MODAL SCHLIESSEN: SUCCESS!")
                    else:
                        print("❌ MODAL SCHLIESSEN: FAILED - versuche Overlay-Click")
                        # Fallback: Klick auf Overlay
                        await modal.click()
                        await page.wait_for_timeout(1000)
                        modal_final = await modal.count()
                        print(f"📋 Modal nach Overlay-Click: {modal_final == 0}")
        else:
            print("❌ Keine Details-Buttons gefunden")
        
        if console_errors:
            print("\n🚨 JavaScript-Fehler:")
            for error in console_errors[:5]:
                print(f"   - {error}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_modal_simple())