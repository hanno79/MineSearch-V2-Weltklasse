#!/usr/bin/env python3
"""
Author: rahn  
Datum: 23.08.2025
Version: 1.0
Beschreibung: Test der Kategorie-Selektion in MineSearch 2.0
"""

import asyncio
from playwright.async_api import async_playwright
import sys
import time

async def test_category_selection():
    async with async_playwright() as p:
        try:
            # Browser starten 
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            print("🌐 Opening MineSearch frontend...")
            await page.goto("http://localhost:8000/static/index.html")
            
            # Warte auf vollständiges Laden der Progressive Model Selection
            print("⏳ Waiting for Progressive Model Selection to load...")
            await asyncio.sleep(5)
            
            # Browser Console Logs aktivieren
            page.on("console", lambda msg: print(f"[CONSOLE] {msg.type}: {msg.text}"))
            
            # Prüfe ob Kategorien geladen wurden
            category_pills = await page.query_selector_all(".quick-model-pill")
            print(f"📊 Found {len(category_pills)} category pills")
            
            # Test 1: "Kostenlos" Kategorie
            print("\n🧪 TEST 1: Testing 'Kostenlos' category...")
            free_pill = await page.query_selector('.smart-selection[data-selection-type="free"]')
            if free_pill:
                print("✅ Found 'Kostenlos' category pill")
                await free_pill.click()
                await asyncio.sleep(2)
                
                # Check selected count
                count_element = await page.query_selector('#selected-count')
                if count_element:
                    count = await count_element.inner_text()
                    print(f"📈 Selected count after 'Kostenlos' click: {count}")
                
                # Click again to deselect
                await free_pill.click()
                await asyncio.sleep(2)
                
                if count_element:
                    count = await count_element.inner_text()
                    print(f"📉 Selected count after deselect: {count}")
            else:
                print("❌ 'Kostenlos' category pill not found")
            
            # Test 2: "Top 3 Beste" Kategorie
            print("\n🧪 TEST 2: Testing 'Top 3 Beste' category...")
            top3_pill = await page.query_selector('.smart-selection[data-selection-type="top3"]')
            if top3_pill:
                print("✅ Found 'Top 3 Beste' category pill")
                await top3_pill.click()
                await asyncio.sleep(2)
                
                count_element = await page.query_selector('#selected-count')
                if count_element:
                    count = await count_element.inner_text()
                    print(f"📈 Selected count after 'Top 3' click: {count}")
                
                # Click again to deselect
                await top3_pill.click()
                await asyncio.sleep(2)
                
                if count_element:
                    count = await count_element.inner_text()
                    print(f"📉 Selected count after deselect: {count}")
            else:
                print("❌ 'Top 3 Beste' category pill not found")
            
            # Test 3: Provider Selection
            print("\n🧪 TEST 3: Testing provider selection...")
            provider_pills = await page.query_selector_all('.provider-selection')
            if provider_pills:
                print(f"✅ Found {len(provider_pills)} provider pills")
                first_provider = provider_pills[0]
                provider_name = await first_provider.get_attribute('data-provider')
                print(f"🏢 Testing provider: {provider_name}")
                
                await first_provider.click()
                await asyncio.sleep(2)
                
                count_element = await page.query_selector('#selected-count')
                if count_element:
                    count = await count_element.inner_text()
                    print(f"📈 Selected count after provider click: {count}")
                    
                # Click again to deselect
                await first_provider.click()
                await asyncio.sleep(2)
                
                if count_element:
                    count = await count_element.inner_text()
                    print(f"📉 Selected count after deselect: {count}")
            else:
                print("❌ No provider pills found")
                
            print("\n✅ Test completed successfully!")
            await asyncio.sleep(2)
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if 'browser' in locals():
                await browser.close()

if __name__ == "__main__":
    asyncio.run(test_category_selection())