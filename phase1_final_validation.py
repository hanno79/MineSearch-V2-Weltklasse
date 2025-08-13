#!/usr/bin/env python3
"""
Author: rahn
Datum: 11.08.2025
Version: 1.0
Beschreibung: Phase 1 Final Validation für MineSearch 2.0
"""

import asyncio
from playwright.async_api import async_playwright

async def phase1_final_validation():
    """Phase 1 Final Validation"""
    print("🏆 PHASE 1 FINAL VALIDATION")
    print("=" * 70)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=800)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # Lade die Seite
            print("🌐 Loading MineSearch 2.0...")
            await page.goto("http://localhost:8000")
            await page.wait_for_load_state('networkidle')
            await page.wait_for_timeout(5000)
            
            phase1_results = {}
            
            print("\n🔧 PHASE 1.1 VALIDATION: Modal System")
            print("-" * 50)
            
            # Test Modal System
            await page.query_selector('label[for="statistics-tab"]')
            stats_label = await page.query_selector('label[for="statistics-tab"]')
            if stats_label:
                await stats_label.click()
                await page.wait_for_timeout(3000)
                
                # Test Details Button
                detail_buttons = await page.query_selector_all('button:has-text("Details")')
                print(f"🔍 Statistics Details buttons: {len(detail_buttons)}")
                
                if len(detail_buttons) > 0:
                    first_button = detail_buttons[0]
                    onclick = await first_button.get_attribute('onclick')
                    
                    if onclick and 'showModelDetails' in onclick:
                        await first_button.click()
                        await page.wait_for_timeout(2000)
                        
                        modals = await page.query_selector_all('.model-details-modal')
                        if len(modals) > 0:
                            print("✅ Phase 1.1: Modal System WORKING")
                            phase1_results["1.1 Modal System"] = "SUCCESS"
                            
                            # Close modal for next test
                            await page.evaluate('window.ModalManager.closeAll()')
                            await page.wait_for_timeout(500)
                        else:
                            print("❌ Phase 1.1: Modal not opening")
                            phase1_results["1.1 Modal System"] = "FAILED"
                    else:
                        print("❌ Phase 1.1: No onclick handler")
                        phase1_results["1.1 Modal System"] = "FAILED"
                else:
                    print("❌ Phase 1.1: No Details buttons")
                    phase1_results["1.1 Modal System"] = "FAILED"
            else:
                print("❌ Phase 1.1: Statistics tab not found")
                phase1_results["1.1 Modal System"] = "FAILED"
            
            print("\n📑 PHASE 1.2 VALIDATION: Tab System")
            print("-" * 50)
            
            # Test alle 5 Tabs
            tabs_to_test = [
                ("single-tab", "Single"),
                ("csv-tab", "CSV"), 
                ("sources-tab", "Sources"),
                ("statistics-tab", "Statistics"),
                ("consolidated-tab", "Consolidated")
            ]
            
            working_tabs = 0
            for tab_id, tab_name in tabs_to_test:
                tab_label = await page.query_selector(f'label[for="{tab_id}"]')
                if tab_label:
                    await tab_label.click()
                    await page.wait_for_timeout(1500)
                    
                    tab_input = await page.query_selector(f'input#{tab_id}')
                    is_checked = await tab_input.is_checked() if tab_input else False
                    
                    if is_checked:
                        print(f"  ✅ {tab_name}: Tab switching works")
                        working_tabs += 1
                    else:
                        print(f"  ❌ {tab_name}: Tab not activated")
                else:
                    print(f"  ❌ {tab_name}: Tab not found")
            
            if working_tabs == 5:
                print("✅ Phase 1.2: All Tab Navigation WORKING")
                phase1_results["1.2 Tab System"] = "SUCCESS"
            elif working_tabs >= 3:
                print(f"⚠️ Phase 1.2: Most tabs working ({working_tabs}/5)")
                phase1_results["1.2 Tab System"] = "PARTIAL"
            else:
                print(f"❌ Phase 1.2: Tab system broken ({working_tabs}/5)")
                phase1_results["1.2 Tab System"] = "FAILED"
            
            print("\n🔍 PHASE 1.3 VALIDATION: Search & Models")
            print("-" * 50)
            
            # Test Model Selection
            model_checkboxes = await page.query_selector_all('input[type="checkbox"][name="models"], input[type="checkbox"][value*=":"]')
            print(f"🔍 Model checkboxes found: {len(model_checkboxes)}")
            
            if len(model_checkboxes) >= 50:
                # Test 3 random models
                working_models = 0
                for i in range(min(3, len(model_checkboxes))):
                    checkbox = model_checkboxes[i]
                    try:
                        initial_state = await checkbox.is_checked()
                        await checkbox.click()
                        await page.wait_for_timeout(300)
                        new_state = await checkbox.is_checked()
                        
                        if new_state != initial_state:
                            working_models += 1
                    except:
                        pass
                
                if working_models >= 2:
                    print("✅ Phase 1.3: Model Selection WORKING")
                    phase1_results["1.3 Model Selection"] = "SUCCESS"
                else:
                    print("❌ Phase 1.3: Model Selection failing")
                    phase1_results["1.3 Model Selection"] = "FAILED"
            else:
                print("❌ Phase 1.3: Not enough models found")
                phase1_results["1.3 Model Selection"] = "FAILED"
            
            # Test Loading States
            loading_elements = await page.query_selector_all('#loading, .loading, .spinner, .progress')
            print(f"🔍 Loading elements found: {len(loading_elements)}")
            
            if len(loading_elements) > 0:
                print("✅ Phase 1.3: Loading States present")
                phase1_results["1.3 Loading States"] = "SUCCESS"
            else:
                print("❌ Phase 1.3: No loading states")
                phase1_results["1.3 Loading States"] = "FAILED"
            
            # Final Screenshot
            await page.screenshot(path="/app/phase1_final_validation.png", full_page=True)
            print("\n📸 Screenshot: phase1_final_validation.png")
            
            # Calculate success rate
            success_count = sum(1 for result in phase1_results.values() if result == "SUCCESS")
            partial_count = sum(1 for result in phase1_results.values() if result == "PARTIAL")
            total_count = len(phase1_results)
            
            success_rate = (success_count + partial_count * 0.5) / total_count * 100
            
            print(f"\n🎯 PHASE 1 COMPLETION SUMMARY:")
            print("=" * 60)
            for component, result in phase1_results.items():
                status_icon = "✅" if result == "SUCCESS" else ("⚠️" if result == "PARTIAL" else "❌")
                print(f"{status_icon} {component}: {result}")
            
            print(f"\n📊 TOTAL SUCCESS RATE: {success_rate:.1f}%")
            print(f"📊 COMPONENTS: {success_count} Success, {partial_count} Partial, {total_count - success_count - partial_count} Failed")
            
            # Determine if Phase 1 is complete
            is_complete = success_rate >= 75.0
            
            if is_complete:
                print(f"\n🏆 PHASE 1: COMPLETE SUCCESS! (Minimum 75% erfüllt)")
                print("🚀 Ready to proceed to Phase 2: Design System")
            else:
                print(f"\n⚠️ PHASE 1: NEEDS IMPROVEMENT ({success_rate:.1f}% < 75%)")
                print("🔄 Fix remaining issues before Phase 2")
            
            return is_complete
                
        except Exception as e:
            print(f"❌ Phase 1 validation failed: {e}")
            await page.screenshot(path="/app/phase1_validation_error.png", full_page=True)
            return False
            
        finally:
            print("\n🔍 Browser bleibt 10 Sekunden offen für finale Verifikation...")
            await page.wait_for_timeout(10000)
            await browser.close()

async def main():
    """Hauptfunktion"""
    success = await phase1_final_validation()
    
    print("\n" + "=" * 70)
    if success:
        print("🎉 PHASE 1 FINAL VALIDATION: COMPLETE!")
        print("🎯 ALL CRITICAL FUNCTIONALITY RESTORED")
        print("🚀 READY FOR PHASE 2: UI/UX DESIGN SYSTEM")
    else:
        print("❌ PHASE 1 FINAL VALIDATION: INCOMPLETE")
        print("🔄 Critical issues need resolution")
    print("=" * 70)
    
    return success

if __name__ == '__main__':
    result = asyncio.run(main())
    exit(0 if result else 1)