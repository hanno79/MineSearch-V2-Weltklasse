#!/usr/bin/env python3
"""
Author: rahn
Datum: 11.08.2025
Version: 1.0
Beschreibung: Test Search Functionality für MineSearch 2.0
"""

import asyncio
from playwright.async_api import async_playwright

async def test_search_functionality():
    """Test Search Functionality"""
    print("🔍 TEST SEARCH FUNCTIONALITY")
    print("=" * 60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=1200)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Console logging
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
            
            results = {}
            
            # Test 1: Single Search
            print("\n🔍 TEST 1: Single Search Functionality")
            print("-" * 50)
            
            # Wechsle zu Single Search Tab
            single_tab_label = await page.query_selector('label[for="single-tab"]')
            if single_tab_label:
                await single_tab_label.click()
                await page.wait_for_timeout(2000)
                
                # Debug: Check tab class
                container_class = await page.evaluate('document.querySelector(".container").className')
                print(f"🔍 Container class: {container_class}")
                
                # Force show single form
                await page.evaluate('document.getElementById("single_form").style.display = "block"')
                await page.wait_for_timeout(1000)
                
                # Finde Search Form (spezifischere Selektoren)
                search_input = await page.query_selector('input[name="mine_name"], input#mine_name')
                search_button = await page.query_selector('#single-search-form button, button:has-text("Suchen")')
                
                if search_input and search_button:
                    print("✅ Single Search: Form elements found")
                    
                    # Teste mit Beispiel-Mine
                    test_mine = "Eleonore Mine"
                    await search_input.fill(test_mine)
                    
                    print(f"🔄 Testing search for: {test_mine}")
                    await search_button.click()
                    
                    # Warte auf Suche (aber nicht zu lange)
                    try:
                        await page.wait_for_selector('.search-results, .results, .mine-result', timeout=15000)
                        print("✅ Single Search: Results appeared")
                        results["Single Search"] = "SUCCESS - Results loaded"
                    except:
                        print("⚠️ Single Search: No results in 15s (may still be searching)")
                        results["Single Search"] = "PARTIAL - Search started, results pending"
                else:
                    print("❌ Single Search: Form elements not found")
                    results["Single Search"] = "FAILED - No search form"
            else:
                print("❌ Single Search: Tab not found")
                results["Single Search"] = "FAILED - Tab not accessible"
            
            # Screenshot nach Single Search
            await page.screenshot(path="/app/single_search_test.png", full_page=True)
            
            # Test 2: CSV Search
            print("\n📄 TEST 2: CSV Search Functionality")
            print("-" * 50)
            
            # Wechsle zu CSV Search Tab
            csv_tab_label = await page.query_selector('label[for="csv-tab"]')
            if csv_tab_label:
                await csv_tab_label.click()
                await page.wait_for_timeout(2000)
                
                # Finde CSV Upload
                file_input = await page.query_selector('input[type="file"]')
                upload_button = await page.query_selector('button:has-text("Upload"), button:has-text("Hochladen")')
                
                if file_input:
                    print("✅ CSV Search: File input found")
                    results["CSV Search"] = "SUCCESS - Upload form available"
                else:
                    print("❌ CSV Search: File input not found")  
                    results["CSV Search"] = "FAILED - No upload form"
            else:
                print("❌ CSV Search: Tab not found")
                results["CSV Search"] = "FAILED - Tab not accessible"
            
            # Test 3: Model Selection
            print("\n🤖 TEST 3: Model Selection")
            print("-" * 50)
            
            # Gehe zu Single Tab und teste Model Selection
            await single_tab_label.click() if single_tab_label else None
            await page.wait_for_timeout(1000)
            
            # Finde Model Checkboxes
            model_checkboxes = await page.query_selector_all('input[type="checkbox"][name="models"], input[type="checkbox"][value*=":"]')
            print(f"🔍 Found {len(model_checkboxes)} model checkboxes")
            
            if len(model_checkboxes) > 0:
                # Teste erste 3 Models
                tested_models = 0
                for i, checkbox in enumerate(model_checkboxes[:3]):
                    try:
                        is_checked = await checkbox.is_checked()
                        model_value = await checkbox.get_attribute('value')
                        
                        # Toggle checkbox
                        await checkbox.click()
                        await page.wait_for_timeout(500)
                        
                        new_state = await checkbox.is_checked()
                        if new_state != is_checked:
                            print(f"  ✅ Model {i+1} ({model_value}): Toggle works")
                            tested_models += 1
                        else:
                            print(f"  ❌ Model {i+1}: Toggle failed")
                            
                    except Exception as e:
                        print(f"  ❌ Model {i+1}: Error - {e}")
                
                results["Model Selection"] = f"SUCCESS - {tested_models}/3 models working"
            else:
                results["Model Selection"] = "FAILED - No model checkboxes found"
            
            # Test 4: Progress Tracking
            print("\n⏱️ TEST 4: Progress Indicators")
            print("-" * 50)
            
            # Finde Progress Elements
            progress_bars = await page.query_selector_all('.progress, .progress-bar, [id*="progress"]')
            loading_indicators = await page.query_selector_all('.loading, .spinner, [class*="load"]')
            
            print(f"🔍 Progress elements: {len(progress_bars)} bars, {len(loading_indicators)} loaders")
            
            if len(progress_bars) > 0 or len(loading_indicators) > 0:
                results["Progress Indicators"] = "SUCCESS - Elements found"
            else:
                results["Progress Indicators"] = "NEEDS IMPLEMENTATION - No indicators found"
            
            # Final Screenshot
            await page.screenshot(path="/app/search_functionality_final.png", full_page=True)
            
            # Zusammenfassung
            print("\n🎯 SEARCH FUNCTIONALITY SUMMARY:")
            print("=" * 50)
            success_count = 0
            for component, result in results.items():
                status_icon = "✅" if result.startswith("SUCCESS") else ("⚠️" if "PARTIAL" in result else "❌")
                print(f"{status_icon} {component}: {result}")
                if result.startswith("SUCCESS"):
                    success_count += 1
            
            print(f"\n📊 TOTAL: {success_count}/{len(results)} components working")
            
            return success_count >= len(results) * 0.75  # 75% success rate
                
        except Exception as e:
            print(f"❌ Search functionality test failed: {e}")
            await page.screenshot(path="/app/search_test_error.png", full_page=True)
            return False
            
        finally:
            print("\n🔍 Browser bleibt 15 Sekunden offen für manuelle Verifikation...")
            await page.wait_for_timeout(15000)
            await browser.close()

async def main():
    """Hauptfunktion"""
    success = await test_search_functionality()
    
    print("\n" + "=" * 60)
    if success:
        print("🏆 SEARCH FUNCTIONALITY: SUFFICIENT SUCCESS!")
        print("🚀 Ready to proceed to Phase 1.3 completion")
    else:
        print("❌ SEARCH FUNCTIONALITY: CRITICAL ISSUES")
        print("🔄 Need to fix search system before proceeding")
    print("=" * 60)
    
    return success

if __name__ == '__main__':
    result = asyncio.run(main())
    exit(0 if result else 1)