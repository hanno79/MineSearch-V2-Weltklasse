#!/usr/bin/env python3
"""
Author: rahn
Datum: 11.08.2025
Version: 1.0
Beschreibung: Manueller Modal-Test für MineSearch 2.0
"""

import asyncio
from playwright.async_api import async_playwright

async def manual_modal_test():
    """Manueller Modal-Test"""
    print("🧪 MANUAL MODAL TEST")
    print("=" * 50)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # Lade die Seite
            print("🌐 Loading MineSearch 2.0...")
            await page.goto("http://localhost:8000")
            await page.wait_for_load_state('networkidle')
            await page.wait_for_timeout(3000)
            
            # Teste Funktion einzeln
            print("🔍 Testing function availability...")
            
            # Test ModalManager
            modal_manager_test = await page.evaluate('window.ModalManager')
            print(f"ModalManager available: {modal_manager_test is not None}")
            
            # Test showModelDetails
            show_details_test = await page.evaluate('window.showModelDetails')
            print(f"showModelDetails available: {show_details_test is not None}")
            
            # Teste Modal-Creation direkt
            print("🔄 Creating test modal...")
            await page.evaluate('''
                if (window.ModalManager) {
                    const testModal = window.ModalManager.create({
                        content: '<div style="padding: 20px;"><h2>Test Modal</h2><p>Modal system is working!</p></div>'
                    });
                    console.log("Test modal created:", testModal);
                } else {
                    console.error("ModalManager not available");
                }
            ''')
            
            await page.wait_for_timeout(2000)
            
            # Screenshot mit Modal
            await page.screenshot(path="/app/test_modal_created.png", full_page=True)
            print("📸 Screenshot: test_modal_created.png")
            
            # Prüfe ob Modal da ist
            modals = await page.query_selector_all('.modal')
            print(f"Modals found: {len(modals)}")
            
            if len(modals) > 0:
                print("✅ Modal creation successful!")
                
                # Teste showModelDetails mit echtem Model
                print("🔄 Testing showModelDetails...")
                await page.evaluate('window.showModelDetails("openrouter:test-model")')
                
                await page.wait_for_timeout(2000)
                
                # Screenshot mit showModelDetails Modal
                await page.screenshot(path="/app/show_model_details_modal.png", full_page=True)
                print("📸 Screenshot: show_model_details_modal.png")
                
                # Prüfe model-details-modal
                model_modals = await page.query_selector_all('.model-details-modal')
                print(f"Model detail modals found: {len(model_modals)}")
                
                if len(model_modals) > 0:
                    print("🎉 SUCCESS: showModelDetails working!")
                    return True
                else:
                    print("❌ showModelDetails modal not found")
                    return False
            else:
                print("❌ No modals created")
                return False
                
        except Exception as e:
            print(f"❌ Test failed: {e}")
            return False
            
        finally:
            # Halte Browser offen für manuelle Inspektion
            print("🔍 Browser bleibt 10 Sekunden offen für manuelle Inspektion...")
            await page.wait_for_timeout(10000)
            await browser.close()

async def main():
    """Hauptfunktion"""
    success = await manual_modal_test()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 MANUAL MODAL TEST: SUCCESS!")
    else:
        print("❌ MANUAL MODAL TEST: FAILED")
    print("=" * 50)
    
    return success

if __name__ == '__main__':
    result = asyncio.run(main())
    exit(0 if result else 1)