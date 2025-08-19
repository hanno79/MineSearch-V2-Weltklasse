#!/usr/bin/env python3
"""
Author: rahn
Datum: 14.08.2025
Version: 1.0
Beschreibung: Test des verbesserten Modal-Systems mit rotem Schließen-Button
"""

import asyncio
from playwright.async_api import async_playwright

async def test_modal_system():
    """Teste Modal-System und roten Schließen-Button"""
    print("🔲 MODAL SYSTEM TEST")
    print("===================")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=['--no-sandbox'])
        page = await browser.new_page()
        
        # Console-Logs verfolgen
        def handle_console(msg):
            if msg.type in ['error', 'warning']:
                print(f"🖥️ CONSOLE {msg.type.upper()}: {msg.text}")
        page.on("console", handle_console)
        
        print("🌐 Loading page...")
        await page.goto('http://localhost:8000/', wait_until='networkidle')
        await page.wait_for_timeout(5000)
        
        # 1. Test Consolidated Tab und Details-Modal
        print("\n📊 TEST 1: Consolidated Details Modal")
        consolidated_tab = page.locator('.nav-item[data-tab="consolidated"]')
        await consolidated_tab.click()
        await page.wait_for_timeout(3000)
        
        # Klicke auf ersten Details-Button
        first_details_button = page.locator('button:has-text("Details anzeigen")').first
        if await first_details_button.count() > 0:
            await first_details_button.click()
            print("✅ Details-Button geklickt")
            await page.wait_for_timeout(2000)
            
            # Prüfe Modal-Struktur
            modal = page.locator('.modal-overlay')
            modal_header = page.locator('.modal-header h3')
            close_button = page.locator('.modal-close')
            
            modal_exists = await modal.count() > 0
            header_exists = await modal_header.count() > 0
            close_button_exists = await close_button.count() > 0
            
            print(f"📋 Modal sichtbar: {modal_exists}")
            print(f"📋 Header vorhanden: {header_exists}")
            print(f"🔴 Schließen-Button vorhanden: {close_button_exists}")
            
            if close_button_exists:
                close_button_text = await close_button.text_content()
                print(f"🔴 Button-Text: '{close_button_text}'")
                
                # Teste Schließen-Button
                await close_button.click()
                print("✅ Schließen-Button geklickt")
                await page.wait_for_timeout(1000)
                
                # Prüfe ob Modal geschlossen
                modal_after_close = await modal.count()
                print(f"📋 Modal nach Schließen: {modal_after_close == 0}")
                
                if modal_after_close == 0:
                    print("✅ MODAL SCHLIESSEN: SUCCESS!")
                else:
                    print("❌ MODAL SCHLIESSEN: FAILED")
            else:
                print("❌ SCHLIESSEN-BUTTON: NICHT GEFUNDEN")
        else:
            print("❌ Keine Details-Buttons gefunden")
        
        # 2. Test Sources Tab Modal (falls vorhanden)
        print("\n📚 TEST 2: Sources Tab Modal")
        sources_tab = page.locator('.nav-item[data-tab="sources"]')
        await sources_tab.click()
        await page.wait_for_timeout(3000)
        
        # Suche nach Quellen-Details-Buttons
        source_details = page.locator('button:has-text("Details"), .source-item button')
        source_count = await source_details.count()
        print(f"📚 Gefundene Quellen-Details: {source_count}")
        
        if source_count > 0:
            await source_details.first.click()
            await page.wait_for_timeout(2000)
            
            modal = page.locator('.modal-overlay')
            close_button = page.locator('.modal-close')
            
            if await modal.count() > 0 and await close_button.count() > 0:
                await close_button.click()
                await page.wait_for_timeout(1000)
                modal_closed = await modal.count() == 0
                print(f"✅ Sources Modal schließbar: {modal_closed}")
            else:
                print("📚 Sources Modal-Test übersprungen")
        
        print("\n🎯 MODAL SYSTEM TEST ABGESCHLOSSEN")
        print("=================================")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_modal_system())