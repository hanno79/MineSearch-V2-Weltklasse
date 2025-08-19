#!/usr/bin/env python3
"""
Author: rahn
Datum: 14.08.2025  
Version: 1.0
Beschreibung: Console-Debug-Test für Tab-Loading-Probleme
"""

import asyncio
from playwright.async_api import async_playwright

async def test_console_debugging():
    """Teste Console-Output für Tab-Loading-Probleme"""
    print("🔍 CONSOLE DEBUGGING TEST")
    print("=========================")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=['--no-sandbox'])
        page = await browser.new_page()
        
        # Console-Logs sammeln
        console_logs = []
        
        def handle_console(msg):
            console_logs.append(f"[{msg.type}] {msg.text}")
            print(f"🖥️ CONSOLE [{msg.type.upper()}]: {msg.text}")
        
        page.on("console", handle_console)
        
        print("🌐 Loading page with console monitoring...")
        await page.goto('http://localhost:8000/', wait_until='networkidle')
        await page.wait_for_timeout(3000)
        
        # Test Consolidated Tab mit Console-Monitoring
        print("\n📊 Testing Consolidated Tab...")
        consolidated_tab = page.locator('.nav-item[data-tab="consolidated"]')
        if await consolidated_tab.count() > 0:
            await consolidated_tab.click()
            print("✅ Clicked consolidated tab")
            await page.wait_for_timeout(5000)  # Warte auf Datenladung
        
        # Test Statistics Tab mit Console-Monitoring  
        print("\n📈 Testing Statistics Tab...")
        stats_tab = page.locator('.nav-item[data-tab="statistics"]')
        if await stats_tab.count() > 0:
            await stats_tab.click()
            print("✅ Clicked statistics tab")
            await page.wait_for_timeout(5000)  # Warte auf Datenladung
        
        # Test Sources Tab mit Console-Monitoring
        print("\n📚 Testing Sources Tab...")
        sources_tab = page.locator('.nav-item[data-tab="sources"]')
        if await sources_tab.count() > 0:
            await sources_tab.click()
            print("✅ Clicked sources tab")
            await page.wait_for_timeout(5000)  # Warte auf Datenladung
        
        print("\n🔍 CONSOLE ANALYSIS")
        print("===================")
        error_logs = [log for log in console_logs if 'error' in log.lower()]
        warn_logs = [log for log in console_logs if 'warn' in log.lower()]
        
        if error_logs:
            print(f"❌ Found {len(error_logs)} ERROR(S):")
            for error in error_logs[-5:]:  # Show last 5 errors
                print(f"   {error}")
        
        if warn_logs:
            print(f"⚠️ Found {len(warn_logs)} WARNING(S):")
            for warn in warn_logs[-3:]:  # Show last 3 warnings
                print(f"   {warn}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_console_debugging())