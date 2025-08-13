#!/usr/bin/env python3
"""
Author: rahn
Datum: 11.08.2025
Version: 1.0
Beschreibung: Debug JavaScript Loading für MineSearch 2.0
"""

import asyncio
from playwright.async_api import async_playwright

async def debug_js_loading():
    """Debug JavaScript Loading"""
    print("🐛 DEBUG JAVASCRIPT LOADING")
    print("=" * 50)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=500)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Console und Error Handler
        console_messages = []
        errors = []
        
        def handle_console(msg):
            console_messages.append(f"[{msg.type}] {msg.text}")
            print(f"Console [{msg.type}]: {msg.text}")
            
        def handle_error(error):
            errors.append(str(error))
            print(f"Page Error: {error}")
        
        page.on("console", handle_console)
        page.on("pageerror", handle_error)
        
        try:
            # Lade die Seite
            print("🌐 Loading MineSearch 2.0...")
            await page.goto("http://localhost:8000")
            await page.wait_for_load_state('networkidle')
            await page.wait_for_timeout(5000)  # Longer wait for JS loading
            
            print(f"\n📄 Console Messages ({len(console_messages)}):")
            for msg in console_messages[-10:]:  # Last 10 messages
                print(f"  {msg}")
            
            print(f"\n❌ Errors ({len(errors)}):")
            for error in errors:
                print(f"  {error}")
            
            # Test alle relevanten Funktionen
            print("\n🔍 Testing function availability:")
            
            functions_to_test = [
                'ModalManager',
                'showModelDetails', 
                'selectModelForSearch',
                'showComprehensiveModelDetails',
                'sanitizeHTML'
            ]
            
            for func_name in functions_to_test:
                try:
                    result = await page.evaluate(f'typeof window.{func_name}')
                    print(f"  {func_name}: {result}")
                except Exception as e:
                    print(f"  {func_name}: ERROR - {e}")
            
            # Check if ui.js actually loaded
            print("\n📁 Check if ui.js loaded:")
            ui_js_loaded = await page.evaluate('''
                // Check if any ui.js specific functions exist
                typeof window.ModalManager !== "undefined" && 
                typeof window.ModalManager.create === "function"
            ''')
            print(f"  ui.js functions loaded: {ui_js_loaded}")
            
            # Try to manually call showModelDetails
            if not ui_js_loaded:
                print("\n🔧 ui.js not loaded properly. Checking script tags...")
                script_tags = await page.evaluate('''
                    Array.from(document.querySelectorAll('script[src*="ui.js"]')).map(s => ({
                        src: s.src,
                        loaded: s.readyState || 'unknown'
                    }))
                ''')
                print(f"  ui.js script tags: {script_tags}")
                
            return ui_js_loaded and len(errors) == 0
                
        except Exception as e:
            print(f"❌ Debug failed: {e}")
            return False
            
        finally:
            print("🔍 Browser bleibt 5 Sekunden offen...")
            await page.wait_for_timeout(5000)
            await browser.close()

async def main():
    """Hauptfunktion"""
    success = await debug_js_loading()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ JAVASCRIPT LOADING: OK")
    else:
        print("❌ JAVASCRIPT LOADING: PROBLEMS DETECTED")
    print("=" * 50)
    
    return success

if __name__ == '__main__':
    result = asyncio.run(main())
    exit(0 if result else 1)