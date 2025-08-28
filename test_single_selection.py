#!/usr/bin/env python3
"""
Author: rahn  
Datum: 23.08.2025
Version: 1.0
Beschreibung: Test der Einzelauswahl im Erweitert-Modus
"""

import asyncio
from playwright.async_api import async_playwright
import sys
import time

async def test_single_selection():
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
            
            # Console monitoring nur für relevante Infos
            page.on("console", lambda msg: print(f"[CONSOLE] {msg.text}") if "MODEL-UX" in msg.text or "COUNTER" in msg.text else None)
            
            # Test 1: Erweitert-Modus öffnen
            print("\n🧪 TEST 1: Opening 'Erweitert' mode...")
            advanced_btn = await page.query_selector('.advanced-toggle-btn')
            if advanced_btn:
                await advanced_btn.click()
                await asyncio.sleep(2)
                print("✅ Advanced mode opened")
            else:
                print("❌ Advanced toggle button not found")
                return
            
            # Test 2: Einzelnes Modell auswählen
            print("\n🧪 TEST 2: Selecting individual model...")
            model_cards = await page.query_selector_all('.model-card')
            if model_cards:
                print(f"📊 Found {len(model_cards)} model cards")
                first_model = model_cards[0]
                
                # Get model name
                model_name = await first_model.query_selector('.model-name')
                if model_name:
                    name_text = await model_name.inner_text()
                    print(f"🎯 Testing model: {name_text}")
                
                await first_model.click()
                await asyncio.sleep(2)
                
                # Check counter
                count_element = await page.query_selector('#selected-count')
                if count_element:
                    count_value = await count_element.inner_text()
                    print(f"📈 Counter after single selection: {count_value}")
                    
                # Test deselection
                await first_model.click()
                await asyncio.sleep(2)
                
                if count_element:
                    count_value = await count_element.inner_text()
                    print(f"📉 Counter after deselection: {count_value}")
                    
            else:
                print("❌ No model cards found")
                
            print("\n✅ Single selection test completed!")
            await asyncio.sleep(2)
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if 'browser' in locals():
                await browser.close()

if __name__ == "__main__":
    asyncio.run(test_single_selection())