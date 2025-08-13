#!/usr/bin/env python3
"""
Author: rahn
Datum: 11.08.2025
Version: 1.0
Beschreibung: Debug onclick Event für Details-Buttons
"""

import asyncio
from playwright.async_api import async_playwright

async def debug_onclick_event():
    """Debug onclick Event"""
    print("🐛 DEBUG ONCLICK EVENT")
    print("=" * 50)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Console Logger
        def handle_console(msg):
            print(f"Console [{msg.type}]: {msg.text}")
        
        def handle_error(error):
            print(f"Page Error: {error}")
        
        page.on("console", handle_console)
        page.on("pageerror", handle_error)
        
        try:
            # Lade die Seite
            print("🌐 Loading MineSearch 2.0...")
            await page.goto("http://localhost:8000")
            await page.wait_for_load_state('networkidle')
            await page.wait_for_timeout(5000)
            
            # Gehe zu Statistics Tab
            print("📊 Switching to Statistics tab...")
            stats_label = await page.query_selector('label[for="statistics-tab"]')
            if stats_label:
                await stats_label.click()
                await page.wait_for_timeout(3000)
                
                # Finde Details-Buttons und analysiere onclick
                detail_buttons = await page.query_selector_all('button:has-text("Details")')
                print(f"🔍 Found {len(detail_buttons)} Details buttons")
                
                if len(detail_buttons) > 0:
                    first_button = detail_buttons[0]
                    
                    # Analysiere Button-Attribute
                    onclick = await first_button.get_attribute('onclick')
                    model_id = await first_button.get_attribute('data-model-id')
                    
                    print(f"📋 Button onclick: {onclick}")
                    print(f"📋 Button data-model-id: {model_id}")
                    
                    # Teste manuell den onclick Code
                    if onclick:
                        print("🔄 Testing onclick code manually...")
                        try:
                            result = await page.evaluate(f'({onclick})')
                            print(f"✅ onclick executed: {result}")
                        except Exception as e:
                            print(f"❌ onclick failed: {e}")
                    
                    # Teste showModelDetails direkt mit model_id
                    if model_id:
                        print(f"🔄 Testing showModelDetails directly with {model_id}...")
                        try:
                            await page.evaluate(f'window.showModelDetails("{model_id}")')
                            
                            await page.wait_for_timeout(2000)
                            
                            # Screenshot nach direktem Aufruf
                            await page.screenshot(path="/app/direct_showModelDetails_call.png", full_page=True)
                            print("📸 Screenshot: direct_showModelDetails_call.png")
                            
                            # Prüfe Modals
                            modals = await page.query_selector_all('.model-details-modal')
                            print(f"🔍 Modals after direct call: {len(modals)}")
                            
                            if len(modals) > 0:
                                print("✅ Direct call SUCCESS!")
                                return True
                            else:
                                print("❌ Direct call failed")
                        except Exception as e:
                            print(f"❌ Direct call error: {e}")
                    
                    # Alternative: Teste mit programmatischem Click
                    print("🔄 Testing programmatic click...")
                    try:
                        await page.evaluate(f'document.querySelector("button[data-model-id=\\"{model_id}\\"]").click()')
                        await page.wait_for_timeout(2000)
                        
                        modals = await page.query_selector_all('.model-details-modal')
                        print(f"🔍 Modals after programmatic click: {len(modals)}")
                        
                        return len(modals) > 0
                        
                    except Exception as e:
                        print(f"❌ Programmatic click error: {e}")
                        
                else:
                    print("❌ No Details buttons found")
                    
            else:
                print("❌ Statistics tab not found")
                
            return False
                
        except Exception as e:
            print(f"❌ Debug failed: {e}")
            return False
            
        finally:
            print("🔍 Browser bleibt 10 Sekunden offen...")
            await page.wait_for_timeout(10000)
            await browser.close()

async def main():
    """Hauptfunktion"""
    success = await debug_onclick_event()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ ONCLICK DEBUG: SUCCESS!")
    else:
        print("❌ ONCLICK DEBUG: FAILED")
    print("=" * 50)
    
    return success

if __name__ == '__main__':
    result = asyncio.run(main())
    exit(0 if result else 1)