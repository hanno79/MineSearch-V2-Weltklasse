#!/usr/bin/env python3
"""
Author: rahn  
Datum: 14.08.2025
Version: 1.0
Beschreibung: Test ob Auto-Loading nach den Fixes funktioniert
"""

import asyncio
from playwright.async_api import async_playwright

async def test_auto_loading():
    """Teste ob Auto-Loading nach den Reparaturen funktioniert"""
    print("🔄 AUTO-LOADING TEST NACH REPARATUREN")
    print("=====================================")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=['--no-sandbox'])
        page = await browser.new_page()
        
        # Console monitoring
        console_logs = []
        def handle_console(msg):
            console_logs.append(f"[{msg.type}] {msg.text}")
            print(f"🖥️ [{msg.type.upper()}]: {msg.text}")
        page.on("console", handle_console)
        
        print("🌐 Loading page with repairs...")
        await page.goto('http://localhost:8000/', wait_until='networkidle')
        await page.wait_for_timeout(4000)  # Extra wait for all scripts
        
        # Test 1: Auto-Loading beim Consolidated Tab
        print("\n📊 TEST: Auto-Loading Consolidated Tab")
        consolidated_tab = page.locator('.nav-item[data-tab="consolidated"]')
        await consolidated_tab.click()
        print("✅ Clicked consolidated tab")
        
        # Wait for auto-loading to complete
        await page.wait_for_timeout(8000)
        
        # Check results
        mine_cards = page.locator('.mine-card, .field-based-card')
        card_count = await mine_cards.count()
        print(f"📋 Found {card_count} mine cards")
        
        if card_count > 0:
            print("✅ CONSOLIDATED AUTO-LOADING: SUCCESS!")
        else:
            print("❌ CONSOLIDATED AUTO-LOADING: STILL FAILED")
        
        # Test 2: Auto-Loading beim Statistics Tab
        print("\n📈 TEST: Auto-Loading Statistics Tab")  
        stats_tab = page.locator('.nav-item[data-tab="statistics"]')
        await stats_tab.click()
        print("✅ Clicked statistics tab")
        
        await page.wait_for_timeout(8000)
        
        # Check statistics content
        stats_rows = page.locator('.statistics-row, .model-stats-row, table tr')
        row_count = await stats_rows.count()
        print(f"📊 Found {row_count} statistics rows")
        
        if row_count > 1:
            print("✅ STATISTICS AUTO-LOADING: SUCCESS!")
        else:
            print("❌ STATISTICS AUTO-LOADING: STILL FAILED")
        
        # Test 3: Auto-Loading beim Sources Tab
        print("\n📚 TEST: Auto-Loading Sources Tab")
        sources_tab = page.locator('.nav-item[data-tab="sources"]')
        await sources_tab.click()  
        print("✅ Clicked sources tab")
        
        await page.wait_for_timeout(8000)
        
        # Check sources content
        source_items = page.locator('.source-item, .source-domain, .accordion-item')
        item_count = await source_items.count()
        print(f"📚 Found {item_count} source items")
        
        if item_count > 0:
            print("✅ SOURCES AUTO-LOADING: SUCCESS!")
        else:
            print("❌ SOURCES AUTO-LOADING: STILL FAILED")
        
        print("\n🎯 AUTO-LOADING TEST SUMMARY")
        print("============================")
        error_count = len([log for log in console_logs if 'error' in log.lower() and 'function not found' in log.lower()])
        print(f"Function-Not-Found Errors: {error_count}")
        
        success_count = (1 if card_count > 0 else 0) + (1 if row_count > 1 else 0) + (1 if item_count > 0 else 0)
        print(f"Successful Auto-Loads: {success_count}/3")
        
        if success_count == 3:
            print("🎉 ALL AUTO-LOADING FIXED!")
        elif success_count > 0:
            print("⚠️ PARTIAL SUCCESS - Some tabs work")
        else:
            print("❌ AUTO-LOADING STILL BROKEN")
        
        await browser.close()
        
        return success_count == 3

if __name__ == "__main__":
    asyncio.run(test_auto_loading())