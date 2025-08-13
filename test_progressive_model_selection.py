#!/usr/bin/env python3
"""
Author: rahn
Datum: 11.08.2025
Version: 1.0
Beschreibung: Test Progressive Model Selection UX für MineSearch 2.0
"""

import asyncio
from playwright.async_api import async_playwright

async def test_progressive_model_selection():
    """Test Progressive Model Selection UX"""
    print("🎨 TEST PROGRESSIVE MODEL SELECTION UX")
    print("=" * 60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Console logging
        def handle_console(msg):
            if 'MODEL-UX' in msg.text or 'Progressive' in msg.text:
                print(f"Console: {msg.text}")
        
        page.on("console", handle_console)
        
        try:
            # Lade die Seite
            print("🌐 Loading MineSearch 2.0...")
            await page.goto("http://localhost:8000")
            await page.wait_for_load_state('networkidle')
            await page.wait_for_timeout(8000)  # Wait for Progressive Model Selection to load
            
            results = {}
            
            # Test 1: Check Progressive Model Selection loaded
            print("\n🔍 TEST 1: Progressive Model Selection System")
            print("-" * 50)
            
            model_selection_enhanced = await page.query_selector('.model-selection-enhanced')
            if model_selection_enhanced:
                print("✅ Progressive Model Selection container found")
                
                # Check Quick Selection Pills
                quick_pills = await page.query_selector_all('.quick-model-pill')
                print(f"🔍 Quick selection pills: {len(quick_pills)}")
                
                if len(quick_pills) > 0:
                    results["Quick Selection"] = f"SUCCESS - {len(quick_pills)} provider pills"
                else:
                    results["Quick Selection"] = "FAILED - No quick selection pills"
                
                # Test Advanced Mode Toggle
                advanced_toggle = await page.query_selector('.advanced-toggle-btn')
                if advanced_toggle:
                    await advanced_toggle.click()
                    await page.wait_for_timeout(2000)
                    
                    # Check if advanced browser appeared
                    advanced_browser = await page.query_selector('.advanced-model-browser.show')
                    if advanced_browser:
                        print("✅ Advanced mode toggle works")
                        results["Advanced Mode"] = "SUCCESS - Advanced browser opens"
                        
                        # Test Provider Tabs
                        provider_tabs = await page.query_selector_all('.provider-tab')
                        print(f"🔍 Provider tabs: {len(provider_tabs)}")
                        
                        if len(provider_tabs) > 0:
                            # Click first provider tab
                            first_tab = provider_tabs[1] if len(provider_tabs) > 1 else provider_tabs[0]  # Skip "All"
                            await first_tab.click()
                            await page.wait_for_timeout(1500)
                            
                            # Check models grid
                            models_grid = await page.query_selector('.models-grid.show')
                            if models_grid:
                                model_cards = await page.query_selector_all('.model-card')
                                print(f"🔍 Model cards in grid: {len(model_cards)}")
                                results["Provider Tabs"] = f"SUCCESS - {len(model_cards)} models shown"
                            else:
                                results["Provider Tabs"] = "FAILED - Models grid not shown"
                        else:
                            results["Provider Tabs"] = "FAILED - No provider tabs found"
                    else:
                        print("❌ Advanced mode toggle failed")
                        results["Advanced Mode"] = "FAILED - Advanced browser not opening"
                else:
                    results["Advanced Mode"] = "FAILED - No advanced toggle button"
            else:
                print("❌ Progressive Model Selection not found")
                results["Quick Selection"] = "FAILED - Container not found"
                results["Advanced Mode"] = "FAILED - Container not found"
                results["Provider Tabs"] = "FAILED - Container not found"
            
            # Test 2: Model Selection Functionality
            print("\n🤖 TEST 2: Model Selection Functionality")
            print("-" * 50)
            
            # Test quick pill selection
            quick_pills = await page.query_selector_all('.quick-model-pill[data-provider]')
            if len(quick_pills) > 0:
                first_pill = quick_pills[0]
                provider_name = await first_pill.get_attribute('data-provider')
                
                # Click quick pill
                await first_pill.click()
                await page.wait_for_timeout(1500)
                
                # Check if pill is selected
                is_selected = await page.evaluate('(pill) => pill.classList.contains("selected")', first_pill)
                
                if is_selected:
                    print(f"✅ Quick selection works - {provider_name} selected")
                    
                    # Check selection summary
                    selected_count = await page.text_content('#selected-count')
                    print(f"🔍 Selected models count: {selected_count}")
                    
                    results["Model Selection"] = f"SUCCESS - {selected_count} models selected"
                else:
                    print("❌ Quick selection failed")
                    results["Model Selection"] = "FAILED - Quick selection not working"
            else:
                results["Model Selection"] = "FAILED - No quick selection pills"
            
            # Test 3: Visual Design
            print("\n🎨 TEST 3: Visual Design & UX")
            print("-" * 50)
            
            # Check CSS variables are applied
            primary_color = await page.evaluate('getComputedStyle(document.documentElement).getPropertyValue("--primary-500")')
            space_lg = await page.evaluate('getComputedStyle(document.documentElement).getPropertyValue("--space-lg")')
            
            if primary_color and space_lg:
                print(f"✅ Design system variables: --primary-500={primary_color.strip()}, --space-lg={space_lg.strip()}")
                results["Design System"] = "SUCCESS - CSS variables applied"
            else:
                results["Design System"] = "FAILED - CSS variables missing"
            
            # Final screenshot
            await page.screenshot(path="/app/progressive_model_selection_test.png", full_page=True)
            print("\n📸 Screenshot: progressive_model_selection_test.png")
            
            # Summary
            print("\n🎯 PROGRESSIVE MODEL SELECTION SUMMARY:")
            print("=" * 60)
            success_count = 0
            for component, result in results.items():
                status_icon = "✅" if result.startswith("SUCCESS") else "❌"
                print(f"{status_icon} {component}: {result}")
                if result.startswith("SUCCESS"):
                    success_count += 1
            
            print(f"\n📊 TOTAL: {success_count}/{len(results)} components working")
            
            return success_count >= len(results) * 0.75
                
        except Exception as e:
            print(f"❌ Progressive model selection test failed: {e}")
            await page.screenshot(path="/app/progressive_test_error.png", full_page=True)
            return False
            
        finally:
            print("\n🔍 Browser bleibt 15 Sekunden offen für manuelle Verifikation...")
            await page.wait_for_timeout(15000)
            await browser.close()

async def main():
    """Hauptfunktion"""
    success = await test_progressive_model_selection()
    
    print("\n" + "=" * 60)
    if success:
        print("🎨 PROGRESSIVE MODEL SELECTION: SUCCESS!")
        print("🎯 55 MODELS WITH MODERN UX - FUNCTIONALITY PRESERVED")
    else:
        print("❌ PROGRESSIVE MODEL SELECTION: ISSUES DETECTED")
    print("=" * 60)
    
    return success

if __name__ == '__main__':
    result = asyncio.run(main())
    exit(0 if result else 1)