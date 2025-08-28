#!/usr/bin/env python3
"""
FIXED BATCH-TEST: Mit korrekter Modell-Auswahl
"""

import asyncio
from playwright.async_api import async_playwright

async def test_batch_with_model_selection():
    print("🎬 [FIXED-TEST] Starting browser test with correct model selection...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        page = await browser.new_page()
        
        try:
            # 1. Lade Website
            print("📄 [TEST] Loading website...")
            await page.goto("http://localhost:8000/static/index.html#csv")
            await page.wait_for_timeout(3000)
            
            # 2. WICHTIG: Modelle zuerst auswählen!
            print("🎯 [TEST] Selecting models first...")
            
            # Klicke auf den Modell-Auswahl-Bereich
            model_selection_area = page.locator(".model-selection-container, #model-selection")
            if await model_selection_area.count() > 0:
                await model_selection_area.click()
                await page.wait_for_timeout(1000)
            
            # Suche nach DeepSeek-Free Checkbox/Button
            deepseek_selectors = [
                "input[value='openrouter:deepseek-free']",
                "input[id*='deepseek']", 
                "label:has-text('DeepSeek')",
                ".model-card:has-text('DeepSeek')",
                "button:has-text('DeepSeek')"
            ]
            
            model_selected = False
            for selector in deepseek_selectors:
                element = page.locator(selector)
                element_count = await element.count()
                
                if element_count > 0:
                    print(f"🔍 [TEST] Found {element_count} elements for selector: {selector}")
                    
                    try:
                        # Wait for element to be visible with timeout
                        await page.wait_for_selector(selector, state="visible", timeout=3000)
                        
                        # Check first element for visibility and enabled state
                        first_element = element.first
                        is_visible = await first_element.is_visible()
                        is_enabled = await first_element.is_enabled()
                        
                        print(f"📊 [TEST] Element state - visible: {is_visible}, enabled: {is_enabled}")
                        
                        if is_visible and is_enabled:
                            print(f"✅ [TEST] Clicking visible/enabled DeepSeek option: {selector}")
                            await first_element.click()
                            model_selected = True
                            await page.wait_for_timeout(1000)
                            break
                        else:
                            print(f"⚠️ [TEST] Element not interactable - visible: {is_visible}, enabled: {is_enabled}")
                            
                            # Fallback: Try force click if element exists but not interactable
                            try:
                                print(f"🔄 [TEST] Attempting force click on: {selector}")
                                await first_element.click(force=True)
                                model_selected = True
                                await page.wait_for_timeout(1000)
                                break
                            except Exception as force_error:
                                print(f"❌ [TEST] Force click failed: {force_error}")
                                continue
                        
                    except Exception as selector_error:
                        print(f"❌ [TEST] Selector failed: {selector} - {selector_error}")
                        continue
            
            if not model_selected:
                # Fallback: Erste verfügbare Option wählen mit robuster Überprüfung
                print("🔄 [TEST] Trying fallback: first available model")
                fallback_selector = "input[type='checkbox'][value*='openrouter'], input[type='radio'][value*='openrouter']"
                fallback_element = page.locator(fallback_selector).first
                
                try:
                    if await fallback_element.count() > 0:
                        # Check visibility and enabled state
                        is_visible = await fallback_element.is_visible()
                        is_enabled = await fallback_element.is_enabled()
                        
                        print(f"📊 [TEST] Fallback element state - visible: {is_visible}, enabled: {is_enabled}")
                        
                        if is_visible and is_enabled:
                            await fallback_element.click()
                            model_selected = True
                            print("✅ [TEST] Selected first available model")
                        else:
                            # Try force click as last resort
                            try:
                                print("🔄 [TEST] Attempting force click on fallback")
                                await fallback_element.click(force=True)
                                model_selected = True
                                print("✅ [TEST] Force-selected first available model")
                            except Exception as fallback_error:
                                print(f"❌ [TEST] Fallback force click failed: {fallback_error}")
                except Exception as e:
                    print(f"❌ [TEST] Fallback selection failed: {e}")
            
            if not model_selected:
                print("❌ [TEST] Could not select any model!")
                await page.screenshot(path="/tmp/no_model_selection.png")
                return
            
            # 3. Warte bis Modell-Counter sich aktualisiert
            await page.wait_for_timeout(2000)
            
            # Prüfe ob Modell-Counter > 0
            model_counter_text = await page.locator(".model-selection-info, .selection-summary").inner_text()
            print(f"📊 [TEST] Model selection status: {model_counter_text}")
            
            # 4. Jetzt CSV upload
            print("📊 [TEST] Uploading CSV...")
            csv_content = """Name,Country,Region,Commodity
Éléonore,Canada,Quebec,Gold
Canadian Malartic,Canada,Quebec,Gold"""
            
            with open("/tmp/test_fixed.csv", "w") as f:
                f.write(csv_content)
            
            file_input = page.locator("input[type='file']").first
            await file_input.set_input_files("/tmp/test_fixed.csv")
            await page.wait_for_timeout(2000)
            print("✅ [TEST] CSV uploaded")
            
            # 5. Batch-Button suchen und klicken
            batch_button = page.locator("button:has-text('Batch-Suche'), .batch-search-button, input[value*='Batch']")
            if await batch_button.count() > 0:
                print("🚀 [TEST] Starting batch search...")
                await batch_button.click()
                
                # 6. Warte auf Ergebnisse
                print("⏳ [TEST] Waiting for results...")
                
                try:
                    # Warte auf Progress oder Ergebnisse
                    progress_or_results = page.locator("#batch-results, .batch-progress, .results-table")
                    await progress_or_results.wait_for(state="visible", timeout=60000)
                    
                    # Warte noch etwas für komplette Ergebnisse
                    await page.wait_for_timeout(5000)
                    
                    # Analysiere Éléonore Ergebnisse
                    eleonore_row = page.locator("tr:has-text('Éléonore')")
                    if await eleonore_row.count() > 0:
                        row_content = await eleonore_row.inner_text()
                        print(f"🔍 [TEST] Éléonore row: {row_content}")
                        
                        # Zähle echte Daten vs "nichts gefunden"
                        canada_found = "Canada" in row_content
                        quebec_found = "Quebec" in row_content
                        nichts_count = row_content.count("nichts gefunden")
                        
                        print(f"📊 [TEST] Results analysis:")
                        print(f"  - Canada found: {canada_found}")
                        print(f"  - Quebec found: {quebec_found}")  
                        print(f"  - 'nichts gefunden': {nichts_count} times")
                        
                        if canada_found and quebec_found:
                            print("🎉 [TEST] SUCCESS! Fixed route working - real data found!")
                        else:
                            print("❌ [TEST] Still showing empty results")
                            
                        # Speichere Ergebnisse
                        full_results = await page.locator("#batch-results, .results-table").inner_html()
                        with open("/tmp/final_test_results.html", "w") as f:
                            f.write(full_results)
                        print("💾 [TEST] Results saved to /tmp/final_test_results.html")
                    else:
                        print("❌ [TEST] Éléonore row not found!")
                        
                except Exception as e:
                    print(f"⏰ [TEST] Timeout or error: {e}")
                    await page.screenshot(path="/tmp/timeout_error.png")
                    
            else:
                print("❌ [TEST] Batch button not found!")
                await page.screenshot(path="/tmp/no_batch_button.png")
                
        except Exception as e:
            print(f"❌ [TEST] Error: {e}")
            await page.screenshot(path="/tmp/test_error.png")
            
        finally:
            print("🏁 [TEST] Closing browser...")
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_batch_with_model_selection())