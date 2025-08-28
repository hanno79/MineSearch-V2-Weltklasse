#!/usr/bin/env python3
"""
Author: rahn  
Datum: 23.08.2025
Version: 1.0
Beschreibung: Finaler Test der Zähler-Korrektur mit erweiterten Debug-Infos
"""

import asyncio
from playwright.async_api import async_playwright
import sys
import time

async def test_final_counter_fix():
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
            
            # Browser Console Logs aktivieren mit Filter für Counter-Updates
            page.on("console", lambda msg: print(f"[CONSOLE] {msg.type}: {msg.text}") if "🔢" in msg.text or "MODEL-UX" in msg.text else None)
            
            # Test: Klicke auf "Kostenlos" Kategorie
            print("\n🧪 FINAL TEST: Clicking 'Kostenlos' category...")
            free_pill = await page.query_selector('.smart-selection[data-selection-type="free"]')
            
            if free_pill:
                await free_pill.click()
                await asyncio.sleep(3)
                
                # Finde ALLE Elemente die "Modelle ausgewählt" enthalten
                print("\n🔍 Searching for ALL counter elements...")
                
                # Suche mit verschiedenen Selektoren
                selectors_to_try = [
                    '#selected-count',
                    '#selected-models-count', 
                    '.selected-models-count strong',
                    '.selection-summary strong',
                    '[id*="count"]',
                    '[id*="selected"]'
                ]
                
                found_counters = 0
                for selector in selectors_to_try:
                    elements = await page.query_selector_all(selector)
                    for i, element in enumerate(elements):
                        if element:
                            text = await element.inner_text()
                            print(f"📊 Selector '{selector}' #{i}: '{text}'")
                            found_counters += 1
                
                print(f"\n📈 Found {found_counters} potential counter elements")
                
                # Suche auch nach Text "Modelle ausgewählt"
                print("\n🔍 Searching for text 'Modelle ausgewählt'...")
                elements_with_text = await page.query_selector_all('*:has-text("Modelle ausgewählt")')
                for i, element in enumerate(elements_with_text):
                    if element:
                        text = await element.inner_text()
                        print(f"📊 'Modelle ausgewählt' #{i}: '{text}'")
                        
                await asyncio.sleep(2)
                        
            else:
                print("❌ 'Kostenlos' category pill not found")
                
            print("\n✅ Debug completed!")
            await asyncio.sleep(2)
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if 'browser' in locals():
                await browser.close()

if __name__ == "__main__":
    asyncio.run(test_final_counter_fix())