#!/usr/bin/env python3
"""
Author: rahn
Datum: 14.08.2025
Version: 1.0
Beschreibung: Debug JavaScript-Fehler die display.js stoppen könnten
"""

import asyncio
from playwright.async_api import async_playwright

async def debug_javascript_errors():
    """Debug alle JavaScript-Fehler und Loading-Status"""
    print("🚨 JAVASCRIPT ERROR DEBUG")
    print("=========================")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=['--no-sandbox'])
        page = await browser.new_page()
        
        # Track all errors and console messages
        errors = []
        console_messages = []
        
        def handle_page_error(error):
            errors.append(f"PAGE ERROR: {error}")
            print(f"🚨 PAGE ERROR: {error}")
        
        def handle_console(msg):
            console_messages.append(f"[{msg.type}] {msg.text}")
            if msg.type in ['error', 'warning']:
                print(f"🖥️ CONSOLE {msg.type.upper()}: {msg.text}")
        
        page.on("pageerror", handle_page_error)
        page.on("console", handle_console)
        
        print("🌐 Loading page and tracking errors...")
        await page.goto('http://localhost:8000/', wait_until='networkidle')
        await page.wait_for_timeout(8000)  # Extra wait
        
        # Check which scripts were actually loaded
        loaded_scripts = await page.evaluate("""
            () => {
                const scripts = Array.from(document.querySelectorAll('script[src]'));
                return scripts.map(script => ({
                    src: script.src,
                    loaded: script.complete || script.readyState === 'complete'
                }));
            }
        """)
        
        print("\n📜 SCRIPT LOADING STATUS:")
        print("========================")
        for script in loaded_scripts:
            status = "✅" if script['loaded'] else "❌"
            print(f"{status} {script['src']}")
        
        # Check if display.js content is accessible
        display_content = await page.evaluate("""
            () => {
                try {
                    // Try to see if any functions from display.js are at least defined in some scope
                    const hasLoadSources = typeof loadSources !== 'undefined';
                    const hasLoadConsolidated = typeof loadConsolidatedResults !== 'undefined';
                    const hasDisplayFunctions = typeof displayConsolidatedResults !== 'undefined';
                    
                    return {
                        loadSources: hasLoadSources,
                        loadConsolidatedResults: hasLoadConsolidated,
                        displayConsolidatedResults: hasDisplayFunctions,
                        error: null
                    };
                } catch (e) {
                    return {
                        loadSources: false,
                        loadConsolidatedResults: false,
                        displayConsolidatedResults: false,
                        error: e.toString()
                    };
                }
            }
        """)
        
        print("\n🔍 DISPLAY.JS FUNCTION CHECK:")
        print("============================")
        if display_content['error']:
            print(f"❌ Error checking functions: {display_content['error']}")
        else:
            for func, exists in display_content.items():
                if func != 'error':
                    status = "✅" if exists else "❌"
                    print(f"{status} {func}: {'Found' if exists else 'Not Found'}")
        
        print(f"\n📊 ERROR SUMMARY:")
        print("================")
        print(f"Total Page Errors: {len(errors)}")
        print(f"Total Console Messages: {len(console_messages)}")
        
        if errors:
            print("\n🚨 PAGE ERRORS:")
            for error in errors:
                print(f"   - {error}")
        
        error_messages = [msg for msg in console_messages if 'error' in msg.lower()]
        if error_messages:
            print("\n🖥️ CONSOLE ERRORS:")
            for msg in error_messages[:10]:  # Show first 10
                print(f"   - {msg}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_javascript_errors())