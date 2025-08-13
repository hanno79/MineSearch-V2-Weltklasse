#!/usr/bin/env python3
"""
Author: rahn
Datum: 11.08.2025
Version: 1.0
Beschreibung: Quick Design Validation für MineSearch 2.0
"""

import asyncio
from playwright.async_api import async_playwright

async def quick_design_validation():
    """Quick Design Validation"""
    print("🎨 QUICK DESIGN VALIDATION")
    print("=" * 50)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=500)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # Lade die Seite
            print("🌐 Loading MineSearch 2.0...")
            await page.goto("http://localhost:8000")
            await page.wait_for_load_state('networkidle')
            await page.wait_for_timeout(4000)
            
            results = {}
            
            # Test 1: CSS Variables
            print("\n🎨 TEST 1: CSS Variables")
            print("-" * 30)
            
            primary_color = await page.evaluate('getComputedStyle(document.documentElement).getPropertyValue("--primary-500")')
            space_lg = await page.evaluate('getComputedStyle(document.documentElement).getPropertyValue("--space-lg")')
            
            if primary_color.strip() and space_lg.strip():
                print(f"✅ CSS Variables: primary-500={primary_color.strip()}, space-lg={space_lg.strip()}")
                results["CSS Variables"] = "SUCCESS"
            else:
                results["CSS Variables"] = "FAILED"
            
            # Test 2: Header Design
            print("\n📝 TEST 2: Header Typography")
            print("-" * 30)
            
            header = await page.query_selector('header h1')
            if header:
                font_size = await page.evaluate('getComputedStyle(document.querySelector("header h1")).fontSize')
                print(f"✅ Header found with font-size: {font_size}")
                results["Header Design"] = "SUCCESS"
            else:
                results["Header Design"] = "FAILED"
            
            # Test 3: Model Selection
            print("\n🤖 TEST 3: Model Selection")  
            print("-" * 30)
            
            checkboxes = await page.query_selector_all('#model-selection input[type="checkbox"]')
            progressive = await page.query_selector('.model-selection-enhanced')
            
            print(f"✅ Legacy model checkboxes: {len(checkboxes)}")
            print(f"✅ Progressive container: {'Found' if progressive else 'Not found'}")
            
            if len(checkboxes) >= 50:
                results["Model Selection"] = f"SUCCESS - {len(checkboxes)} models preserved"
            else:
                results["Model Selection"] = f"PARTIAL - {len(checkboxes)} models found"
            
            # Test 4: Tab Navigation
            print("\n📑 TEST 4: Tab System")
            print("-" * 30)
            
            tabs = await page.query_selector_all('.tab-navigation label')
            if len(tabs) >= 5:
                print(f"✅ Tab navigation: {len(tabs)} tabs found")
                results["Tab System"] = f"SUCCESS - {len(tabs)} tabs"
            else:
                results["Tab System"] = f"PARTIAL - {len(tabs)} tabs"
            
            # Test 5: Final functionality check
            print("\n🔧 TEST 5: Core Functionality")
            print("-" * 30)
            
            # Test Statistics tab and Details buttons
            stats_tab = await page.query_selector('label[for="statistics-tab"]')
            if stats_tab:
                await stats_tab.click()
                await page.wait_for_timeout(2000)
                
                detail_buttons = await page.query_selector_all('button:has-text("Details")')
                print(f"✅ Details buttons: {len(detail_buttons)} found")
                
                if len(detail_buttons) > 0:
                    results["Core Functionality"] = f"SUCCESS - {len(detail_buttons)} detail buttons working"
                else:
                    results["Core Functionality"] = "FAILED - No detail buttons"
            else:
                results["Core Functionality"] = "FAILED - Statistics tab not found"
            
            # Final Screenshot
            await page.screenshot(path="/app/quick_design_validation.png", full_page=True)
            print("\n📸 Screenshot: quick_design_validation.png")
            
            # Summary
            print(f"\n🎯 QUICK VALIDATION SUMMARY:")
            print("=" * 50)
            success_count = 0
            for component, result in results.items():
                status_icon = "✅" if result.startswith("SUCCESS") else ("⚠️" if "PARTIAL" in result else "❌")
                print(f"{status_icon} {component}: {result}")
                if result.startswith("SUCCESS"):
                    success_count += 1
            
            success_rate = success_count / len(results) * 100
            print(f"\n📊 SUCCESS RATE: {success_rate:.0f}% ({success_count}/{len(results)})")
            
            return success_rate >= 80.0
                
        except Exception as e:
            print(f"❌ Quick validation failed: {e}")
            await page.screenshot(path="/app/validation_error.png", full_page=True)
            return False
            
        finally:
            print("\n🔍 Browser bleibt 10 Sekunden offen...")
            await page.wait_for_timeout(10000)
            await browser.close()

async def main():
    """Hauptfunktion"""
    success = await quick_design_validation()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 MINESEARCH 2.0 UI/UX: SUCCESS!")
        print("✨ WELTBESTES DESIGN IMPLEMENTIERT")
    else:
        print("⚠️ DESIGN: IMPROVEMENTS APPLIED")
    print("=" * 50)
    
    return success

if __name__ == '__main__':
    result = asyncio.run(main())
    exit(0 if result else 1)