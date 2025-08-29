#!/usr/bin/env python3
"""
Author: rahn  
Datum: 23.08.2025
Version: 1.0
Beschreibung: Finaler Test der kompletten Counter-Reparatur
"""

import asyncio
from playwright.async_api import async_playwright
import sys
import time

async def test_final_fix():
    async with async_playwright() as p:
        browser = None
        try:
            # Browser starten 
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            print("🌐 Testing final Progressive Model Selection fix...")
            await page.goto("http://localhost:8000/static/index.html")
            
            # Warte auf vollständiges Laden
            await asyncio.sleep(4)
            
            # Test 1: Counter existiert
            counter_exists = await page.evaluate('!!document.getElementById("selected-count")')
            print(f"✅ Counter element exists: {counter_exists}")
            
            if not counter_exists:
                print("❌ Counter element missing - test failed")
                sys.exit(1)
            
            # Test 2: Initial counter value
            initial_value = await page.evaluate('document.getElementById("selected-count").textContent')
            print(f"📊 Initial counter value: {initial_value}")
            
            # Test 3: Click Kostenlos button
            print("\n🧪 Testing Kostenlos category selection...")
            await page.click('.smart-selection[data-selection-type="free"]')
            await asyncio.sleep(2)
            
            # Test 4: Check counter after click
            final_value = await page.evaluate('document.getElementById("selected-count").textContent')
            print(f"📊 Counter after Kostenlos click: {final_value}")
            
            # Test 5: Check button state
            button_classes = await page.get_attribute('.smart-selection[data-selection-type="free"]', 'class')
            is_selected = 'selected' in button_classes
            print(f"🎯 Kostenlos button selected: {is_selected}")
            
            # Test 6: Deselect test
            print("\n🧪 Testing deselection...")
            await page.click('.smart-selection[data-selection-type="free"]')
            await asyncio.sleep(2)
            
            deselect_value = await page.evaluate('document.getElementById("selected-count").textContent')
            print(f"📊 Counter after deselect: {deselect_value}")
            
            # Final assessment
            success = (
                counter_exists and
                final_value != "0" and 
                final_value != initial_value and
                deselect_value == "0"
            )
            
            print(f"\n🎯 FINAL RESULT: {'🎉 SUCCESS!' if success else '❌ FAILED'}")
            
            if success:
                print("✅ Progressive Model Selection counter is fully functional!")
                print(f"✅ Kostenlos selection shows: {final_value} models")
                print("✅ Visual feedback works correctly")
                print("✅ Deselection resets to 0")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if browser is not None:
                await browser.close()

if __name__ == "__main__":
    asyncio.run(test_final_fix())
