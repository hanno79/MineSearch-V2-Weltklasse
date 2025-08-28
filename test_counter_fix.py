#!/usr/bin/env python3
"""
Author: rahn  
Datum: 23.08.2025
Version: 1.0
Beschreibung: Test ob Zähler-Fix funktioniert und Console-Spam reduziert ist
"""

import asyncio
from playwright.async_api import async_playwright
import sys
import time

async def test_counter_fix():
    async with async_playwright() as p:
        try:
            # Browser starten 
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            print("🌐 Opening MineSearch frontend...")
            await page.goto("http://localhost:8000/static/index.html")
            
            # Warte auf vollständiges Laden
            print("⏳ Waiting for Progressive Model Selection to load...")
            await asyncio.sleep(5)
            
            # Console Log Counter für Status-Updates
            status_update_count = 0
            
            def count_status_updates(msg):
                nonlocal status_update_count
                if "STATUS" in msg.text and "Updating settings" in msg.text:
                    status_update_count += 1
                print(f"[CONSOLE] {msg.type}: {msg.text}")
            
            page.on("console", count_status_updates)
            
            # Test: Klicke auf "Kostenlos" Kategorie
            print("\n🧪 TEST: Clicking 'Kostenlos' category...")
            free_pill = await page.query_selector('.smart-selection[data-selection-type="free"]')
            
            if free_pill:
                await free_pill.click()
                await asyncio.sleep(2)
                
                # Prüfe beide Zähler
                count1 = await page.query_selector('#selected-count')
                count2 = await page.query_selector('#selected-models-count')
                
                if count1:
                    count1_text = await count1.inner_text()
                    print(f"📊 selected-count: {count1_text}")
                else:
                    print("❌ selected-count element not found")
                
                if count2:
                    count2_text = await count2.inner_text()
                    print(f"📊 selected-models-count: {count2_text}")
                else:
                    print("❌ selected-models-count element not found")
                    
                # Warte und prüfe ob Status-Updates zu häufig sind (sollten < 3 in 15 Sekunden sein)
                print(f"\n⏱️ Waiting 15 seconds to count status updates...")
                await asyncio.sleep(15)
                
                print(f"\n📈 RESULT: {status_update_count} status updates in 15 seconds")
                if status_update_count <= 2:
                    print("✅ Console-Spam erfolgreich reduziert!")
                else:
                    print("⚠️ Immer noch zu viele Status-Updates")
                    
            else:
                print("❌ 'Kostenlos' category pill not found")
                
            print("\n✅ Test completed!")
            await asyncio.sleep(2)
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if 'browser' in locals():
                await browser.close()

if __name__ == "__main__":
    asyncio.run(test_counter_fix())