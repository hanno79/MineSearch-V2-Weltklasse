#!/usr/bin/env python3
"""
DIREKTER BATCH-TEST: Fixed Route validieren
Testet die reparierte Batch-Route direkt im Browser
"""

import asyncio
from playwright.async_api import async_playwright
import time
import logging

async def test_fixed_batch_route():
    print("🎬 [FIXED-BATCH-TEST] Starting direct browser test...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=500)  # Sichtbar für Debug
        page = await browser.new_page()
        
        try:
            # 1. Lade die Website
            print("📄 [TEST] Loading http://localhost:8000/static/index.html")
            await page.goto("http://localhost:8000/static/index.html")
            await page.wait_for_timeout(3000)
            
            # 2. Überprüfe URL-Fragment für CSV
            current_url = page.url
            print(f"🔗 [TEST] Current URL: {current_url}")
            
            # Navigiere direkt zum CSV-Bereich
            await page.goto("http://localhost:8000/static/index.html#csv")
            await page.wait_for_timeout(2000)
            
            # 3. Suche CSV-Upload-Bereich
            print("📊 [TEST] Looking for CSV upload area...")
            csv_section = page.locator("#csv-section")
            if await csv_section.count() == 0:
                # Alternative: Suche nach File-Input
                file_input = page.locator("input[type='file']")
                if await file_input.count() > 0:
                    print("✅ [TEST] Found file input")
                else:
                    print("❌ [TEST] No file input found, checking page structure...")
                    # Debug: Alle sichtbaren Elemente
                    all_sections = await page.locator("div[id*='section'], div[class*='csv'], div[class*='batch']").count()
                    print(f"🔍 [TEST] Found {all_sections} potential sections")
                    
                    # Prüfe alle verfügbaren IDs
                    all_ids = await page.evaluate("Array.from(document.querySelectorAll('*[id]')).map(el => el.id)")
                    print(f"🔍 [TEST] Available IDs: {all_ids[:10]}")  # Erste 10
                    
                    return
            else:
                print("✅ [TEST] Found CSV section")
            
            # 4. Erstelle Test-CSV
            csv_content = """Name,Country,Region,Commodity
Éléonore,Canada,Quebec,Gold
Canadian Malartic,Canada,Quebec,Gold
Lac Expanse,Canada,Quebec,Gold"""
            
            with open("/tmp/test_batch.csv", "w", encoding="utf-8", newline="") as f:
                f.write(csv_content)
            print("📝 [TEST] Created test CSV with 3 mines")
            
            # 5. Upload CSV
            file_input = page.locator("input[type='file']").first
            if await file_input.count() > 0:
                await file_input.set_input_files("/tmp/test_batch.csv")
                await page.wait_for_timeout(2000)
                print("✅ [TEST] CSV uploaded")
                
                # 6. Wähle Modell (falls Select vorhanden)
                model_selectors = ["select#model-selector", "select[name*='model']", ".model-select select"]
                for selector in model_selectors:
                    model_select = page.locator(selector)
                    if await model_select.count() > 0:
                        await model_select.select_option("openrouter:deepseek-free")
                        print("✅ [TEST] Model selected: deepseek-free")
                        break
                else:
                    print("⚠️ [TEST] No model selector found, continuing...")
                
                # 7. Suche und klicke Batch-Button
                batch_buttons = [
                    "button:has-text('Batch-Suche starten')",
                    "button:has-text('Batch Search')", 
                    "button[class*='batch']",
                    "input[type='submit'][value*='Batch']",
                    ".batch-search-button"
                ]
                
                batch_clicked = False
                for btn_selector in batch_buttons:
                    batch_button = page.locator(btn_selector)
                    if await batch_button.count() > 0:
                        print(f"🚀 [TEST] Found batch button: {btn_selector}")
                        await batch_button.click()
                        batch_clicked = True
                        break
                
                if not batch_clicked:
                    print("❌ [TEST] No batch button found!")
                    # Debug: Zeige alle Buttons
                    all_buttons = await page.locator("button, input[type='submit']").count()
                    print(f"🔍 [TEST] Total buttons on page: {all_buttons}")
                    return
                
                # 8. Warte auf Ergebnisse
                print("⏳ [TEST] Waiting for batch results (max 90 seconds)...")
                
                try:
                    # Mehrere mögliche Result-Container
                    result_selectors = [
                        "#batch-results",
                        ".batch-results", 
                        "#results",
                        ".results-container",
                        "table:has(tr:has-text('Éléonore'))"
                    ]
                    
                    result_found = False
                    for selector in result_selectors:
                        try:
                            results_element = page.locator(selector)
                            await results_element.wait_for(state="visible", timeout=30000)
                            result_found = True
                            print(f"✅ [TEST] Results found with selector: {selector}")
                            
                            # Analysiere Ergebnisse
                            results_html = await results_element.inner_html()
                            print(f"📊 [TEST] Results HTML length: {len(results_html)} chars")
                            
                            # Suche nach Éléonore-Zeile
                            eleonore_row = page.locator("tr:has-text('Éléonore')").first
                            if await eleonore_row.count() > 0:
                                row_text = await eleonore_row.inner_text()
                                print(f"🔍 [TEST] Éléonore row found: {row_text[:150]}...")
                                
                                # Zähle "nichts gefunden" vs echte Daten
                                nichts_count = row_text.count("nichts gefunden")
                                canada_found = "Canada" in row_text
                                quebec_found = "Quebec" in row_text
                                
                                print(f"📈 [TEST] Analysis:")
                                print(f"  - 'nichts gefunden': {nichts_count} occurrences")
                                print(f"  - Contains 'Canada': {canada_found}")
                                print(f"  - Contains 'Quebec': {quebec_found}")
                                
                                if canada_found and quebec_found:
                                    print("🎉 [TEST] SUCCESS! Fixed route is working - real data found!")
                                elif nichts_count < 10:  # Weniger als 10 leere Felder
                                    print("✅ [TEST] IMPROVED! Some real data found, fixed route partially working")
                                else:
                                    print("❌ [TEST] STILL FAILING! Mostly empty results")
                                    
                                # Speichere komplette Tabelle für Debug
                                with open("/tmp/fixed_batch_results.html", "w") as f:
                                    f.write(results_html)
                                print("💾 [TEST] Complete results saved to /tmp/fixed_batch_results.html")
                            else:
                                print("❌ [TEST] Éléonore row not found in results!")
                            
                            break
                            
                        except Exception as wait_err:
                            continue
                    
                    if not result_found:
                        print("❌ [TEST] No results container found after 90 seconds!")
                        # Debug screenshot
                        await page.screenshot(path="/tmp/no_results_debug.png")
                        print("📸 [TEST] Debug screenshot saved")
                        
                except Exception as results_error:
                    print(f"❌ [TEST] Error waiting for results: {results_error}")
                    
            else:
                print("❌ [TEST] File input not found!")
                
        except Exception as e:
            print(f"❌ [TEST] Critical error: {e}")
            await page.screenshot(path="/tmp/critical_error.png")
            print("📸 [TEST] Error screenshot saved")
            
        finally:
            print("🏁 [TEST] Test completed, closing browser...")
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_fixed_batch_route())