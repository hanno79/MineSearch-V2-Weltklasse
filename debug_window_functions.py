#!/usr/bin/env python3
"""
Author: rahn
Datum: 14.08.2025
Version: 1.0
Beschreibung: Debug welche window-Funktionen tatsächlich verfügbar sind
"""

import asyncio
from playwright.async_api import async_playwright

async def debug_window_functions():
    """Debug welche Funktionen im window-Scope verfügbar sind"""
    print("🔍 WINDOW FUNCTIONS DEBUG")
    print("========================")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=['--no-sandbox'])
        page = await browser.new_page()
        
        print("🌐 Loading page...")
        await page.goto('http://localhost:8000/', wait_until='networkidle')
        await page.wait_for_timeout(6000)  # Extra wait for scripts
        
        print("\n🔍 Checking window object for our functions...")
        
        # Check which display functions exist
        result = await page.evaluate("""
            () => {
                const functions = [
                    'loadSources',
                    'loadConsolidatedResults', 
                    'loadModelStatistics',
                    'displayGroupedSources',
                    'displayConsolidatedResults',
                    'displayComprehensiveModelStatistics'
                ];
                
                const results = {};
                functions.forEach(func => {
                    results[func] = {
                        exists: typeof window[func] !== 'undefined',
                        type: typeof window[func],
                        isFunction: typeof window[func] === 'function'
                    };
                });
                
                // Also check complete window object for pattern
                const windowKeys = Object.keys(window).filter(key => 
                    key.includes('load') || key.includes('display')
                );
                
                return {
                    targetFunctions: results,
                    allWindowLoadFunctions: windowKeys
                };
            }
        """)
        
        print("📊 TARGET FUNCTIONS STATUS:")
        print("===========================")
        for func_name, status in result['targetFunctions'].items():
            if status['exists']:
                print(f"✅ {func_name}: {status['type']} ({'function' if status['isFunction'] else 'not function'})")
            else:
                print(f"❌ {func_name}: NOT FOUND")
        
        print(f"\n🔍 ALL WINDOW LOAD/DISPLAY FUNCTIONS:")
        print("=====================================")
        for func in result['allWindowLoadFunctions']:
            print(f"   - {func}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_window_functions())