#!/usr/bin/env python3
"""
Author: rahn
Datum: 11.08.2025
Version: 1.0
Beschreibung: Test echte Details-Buttons für MineSearch 2.0
"""

import asyncio
from playwright.async_api import async_playwright

async def test_real_details_buttons():
    """Test echte Details-Buttons"""
    print("🧪 TEST REAL DETAILS BUTTONS")
    print("=" * 50)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=800)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # Lade die Seite
            print("🌐 Loading MineSearch 2.0...")
            await page.goto("http://localhost:8000")
            await page.wait_for_load_state('networkidle')
            await page.wait_for_timeout(5000)  # Wait for full loading
            
            # Test Statistics Tab (wo die Details-Buttons sind)
            print("📊 Switching to Statistics tab...")
            
            # Klicke direkt auf das Statistics Tab Label
            stats_label = await page.query_selector('label[for="statistics-tab"]')
            if stats_label:
                await stats_label.click()
                await page.wait_for_timeout(3000)  # Wait for content loading
                print("✅ Statistics tab clicked")
                
                # Screenshot nach Tab-Switch
                await page.screenshot(path="/app/statistics_tab_loaded.png", full_page=True)
                print("📸 Screenshot: statistics_tab_loaded.png")
                
                # Suche Details-Buttons
                detail_buttons = await page.query_selector_all('button:has-text("Details")')
                print(f"🔍 Found {len(detail_buttons)} Details buttons")
                
                if len(detail_buttons) > 0:
                    # Teste ersten Details-Button
                    print("🖱️ Clicking first Details button...")
                    
                    # Get model ID from button
                    first_button = detail_buttons[0]
                    model_id = await first_button.get_attribute('data-model-id')
                    print(f"📋 Testing button with model-id: {model_id}")
                    
                    # Klicke auf Button
                    await first_button.click()
                    await page.wait_for_timeout(2000)
                    
                    # Screenshot nach Button-Click
                    await page.screenshot(path="/app/after_details_button_click.png", full_page=True)
                    print("📸 Screenshot: after_details_button_click.png")
                    
                    # Prüfe ob Modal geöffnet wurde
                    modals = await page.query_selector_all('.model-details-modal')
                    print(f"🔍 Model details modals found: {len(modals)}")
                    
                    if len(modals) > 0:
                        print("🎉 SUCCESS: Modal opened via real Details button!")
                        
                        # Teste mehrere Buttons
                        print("🔄 Testing multiple buttons...")
                        tested_buttons = 0
                        for i, button in enumerate(detail_buttons[:3]):  # Test 3 buttons max
                            try:
                                # Close any open modals first
                                await page.evaluate('window.ModalManager.closeAll()')
                                await page.wait_for_timeout(500)
                                
                                model_id = await button.get_attribute('data-model-id') 
                                print(f"  Button {i+1}: Testing {model_id}")
                                
                                await button.click()
                                await page.wait_for_timeout(1500)
                                
                                # Check if modal opened
                                test_modals = await page.query_selector_all('.model-details-modal')
                                if len(test_modals) > 0:
                                    print(f"  Button {i+1}: ✅ SUCCESS")
                                    tested_buttons += 1
                                else:
                                    print(f"  Button {i+1}: ❌ FAILED")
                                    
                            except Exception as e:
                                print(f"  Button {i+1}: ❌ ERROR: {e}")
                        
                        print(f"\n📊 RESULTS: {tested_buttons}/{min(3, len(detail_buttons))} buttons working")
                        
                        # Close all modals
                        await page.evaluate('window.ModalManager.closeAll()')
                        
                        return tested_buttons > 0
                    else:
                        print("❌ No modal opened")
                        return False
                else:
                    print("❌ No Details buttons found")
                    return False
            else:
                print("❌ Statistics tab label not found")
                return False
                
        except Exception as e:
            print(f"❌ Test failed: {e}")
            await page.screenshot(path="/app/test_error_screenshot.png", full_page=True)
            return False
            
        finally:
            print("🔍 Browser bleibt 8 Sekunden offen für manuelle Verifikation...")
            await page.wait_for_timeout(8000)
            await browser.close()

async def main():
    """Hauptfunktion"""
    success = await test_real_details_buttons()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 REAL DETAILS BUTTONS TEST: SUCCESS!")
    else:
        print("❌ REAL DETAILS BUTTONS TEST: FAILED")
    print("=" * 50)
    
    return success

if __name__ == '__main__':
    result = asyncio.run(main())
    exit(0 if result else 1)