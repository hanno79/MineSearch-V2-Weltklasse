#!/usr/bin/env python3
"""
Author: rahn
Datum: 14.08.2025  
Version: 1.0
Beschreibung: Test der manuellen Laden-Buttons als Fallback-System
"""

import asyncio
from playwright.async_api import async_playwright

async def test_manual_buttons():
    """Teste die manuellen Laden-Buttons"""
    print("🔘 MANUAL BUTTON TEST")
    print("====================")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=['--no-sandbox'])
        page = await browser.new_page()
        
        # Console-Logs sammeln
        console_logs = []
        def handle_console(msg):
            console_logs.append(f"[{msg.type}] {msg.text}")
            if 'error' in msg.type.lower():
                print(f"🖥️ CONSOLE ERROR: {msg.text}")
        page.on("console", handle_console)
        
        print("🌐 Loading page...")
        await page.goto('http://localhost:8000/', wait_until='networkidle')
        await page.wait_for_timeout(3000)
        
        # Test 1: Consolidated Manual Button
        print("\n📊 TEST 1: Consolidated Manual Button")
        consolidated_tab = page.locator('.nav-item[data-tab="consolidated"]')
        await consolidated_tab.click()
        await page.wait_for_timeout(2000)
        
        # Find and click manual button
        manual_button = page.locator('button:has-text("Filter anwenden")')
        if await manual_button.count() > 0:
            await manual_button.first.click()
            print("✅ Clicked 'Filter anwenden' button")
            await page.wait_for_timeout(5000)
            
            # Check for mine cards
            mine_cards = page.locator('.mine-card, .field-based-card')
            card_count = await mine_cards.count()
            print(f"📋 Found {card_count} mine cards")
            
            if card_count > 0:
                print("✅ CONSOLIDATED MANUAL LOADING: SUCCESS")
            else:
                print("❌ CONSOLIDATED MANUAL LOADING: FAILED")
        else:
            print("❌ Manual button not found")
        
        # Test 2: Statistics Manual Button  
        print("\n📈 TEST 2: Statistics Manual Button")
        stats_tab = page.locator('.nav-item[data-tab="statistics"]')
        await stats_tab.click()
        await page.wait_for_timeout(2000)
        
        # Find and click statistics button
        stats_button = page.locator('button:has-text("Statistiken laden")')
        if await stats_button.count() > 0:
            await stats_button.first.click()
            print("✅ Clicked 'Statistiken laden' button")
            await page.wait_for_timeout(5000)
            
            # Check for statistics content
            stats_content = page.locator('.statistics-row, .model-stats-row, table tr')
            row_count = await stats_content.count()
            print(f"📊 Found {row_count} statistics rows")
            
            if row_count > 1:  # More than header
                print("✅ STATISTICS MANUAL LOADING: SUCCESS")
            else:
                print("❌ STATISTICS MANUAL LOADING: FAILED")
        else:
            print("❌ Statistics manual button not found")
        
        # Test 3: Sources Manual Button
        print("\n📚 TEST 3: Sources Manual Button")
        sources_tab = page.locator('.nav-item[data-tab="sources"]')
        await sources_tab.click()
        await page.wait_for_timeout(2000)
        
        # Find and click sources button
        sources_button = page.locator('button:has-text("Quellen laden")')
        if await sources_button.count() > 0:
            await sources_button.first.click()
            print("✅ Clicked 'Quellen laden' button")
            await page.wait_for_timeout(5000)
            
            # Check for sources content
            source_items = page.locator('.source-item, .source-domain, .accordion-item')
            item_count = await source_items.count()
            print(f"📚 Found {item_count} source items")
            
            if item_count > 0:
                print("✅ SOURCES MANUAL LOADING: SUCCESS")
            else:
                print("❌ SOURCES MANUAL LOADING: FAILED")
        else:
            print("❌ Sources manual button not found")
        
        print("\n🎯 MANUAL BUTTON TEST SUMMARY")
        print("=============================")
        error_count = len([log for log in console_logs if 'error' in log.lower()])
        print(f"Console Errors: {error_count}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_manual_buttons())