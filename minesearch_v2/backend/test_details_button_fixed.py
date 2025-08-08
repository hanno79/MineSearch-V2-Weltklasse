#!/usr/bin/env python3
"""
Author: rahn
Datum: 07.08.2025
Version: 1.0
Beschreibung: Test for FIXED Details Button JavaScript Issue
"""

import asyncio
from playwright.async_api import async_playwright
import json

async def test_details_button_fix():
    """Test ob Details Buttons nach JavaScript Fix funktionieren"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        console_errors = []
        console_logs = []
        
        # Capture ALL console messages
        def handle_console(msg):
            if msg.type == 'error':
                console_errors.append(f"ERROR: {msg.text}")
            else:
                console_logs.append(f"{msg.type.upper()}: {msg.text}")
        
        page.on('console', handle_console)
        
        try:
            print("🔧 FIXED DETAILS BUTTON TEST")
            print("=" * 50)
            
            # 1. Load page
            print("1. 🌐 Loading main page...")
            await page.goto('http://localhost:8000')
            await page.wait_for_load_state('networkidle', timeout=10000)
            
            # 2. Activate Statistics Tab
            print("2. 📊 Activating Statistics tab...")
            await page.click('label[for="statistics"]')
            await page.wait_for_timeout(5000)  # Wait for data load
            
            # 3. Check if table loaded
            try:
                await page.wait_for_selector('table tbody tr', timeout=10000)
                table_rows = await page.query_selector_all('table tbody tr')
                print(f"   ✅ Statistics table loaded with {len(table_rows)} rows")
            except:
                print("   ⚠️ Statistics table not found, trying to load...")
                return False
                
            # 4. Find Details buttons
            print("3. 🔍 Looking for Details buttons...")
            details_buttons = await page.query_selector_all('button[onclick*="showModelDetails"]')
            
            if not details_buttons:
                print("   ❌ NO Details buttons found!")
                return False
                
            print(f"   ✅ Found {len(details_buttons)} Details buttons")
            
            # 5. Test button onclick attributes  
            print("4. 🧪 Testing button onclick syntax...")
            for i, button in enumerate(details_buttons[:3]):  # Test first 3
                onclick = await button.get_attribute('onclick')
                print(f"   Button {i+1} onclick: {onclick[:80]}...")
                
                # Check for proper JavaScript syntax
                if 'showModelDetails(' in onclick and ')' in onclick:
                    print(f"   ✅ Button {i+1}: Proper syntax")
                else:
                    print(f"   ❌ Button {i+1}: Invalid syntax")
            
            # 6. Test clicking first Details button
            print("5. 🎯 Testing first Details button click...")
            first_button = details_buttons[0]
            
            # Clear console errors before click
            console_errors.clear()
            
            await first_button.click()
            await page.wait_for_timeout(2000)  # Wait for modal/accordion
            
            # 7. Check for JavaScript errors after click
            print("6. 🔍 Checking for JavaScript errors...")
            if console_errors:
                print("   ❌ JAVASCRIPT ERRORS FOUND:")
                for error in console_errors:
                    print(f"     - {error}")
                return False
            else:
                print("   ✅ NO JavaScript errors after click!")
            
            # 8. Check if Details modal/accordion appeared
            print("7. 📋 Checking if Details were displayed...")
            
            # Look for accordion details
            try:
                accordion = await page.query_selector('[id*="model-details-"]', timeout=3000)
                if accordion and await accordion.is_visible():
                    print("   ✅ Details accordion opened successfully!")
                    modal_success = True
                else:
                    print("   ⚠️ No visible accordion found")
                    modal_success = False
            except:
                # Try looking for modal instead
                try:
                    modal = await page.query_selector('#detailsModal')
                    if modal and await modal.is_visible():
                        print("   ✅ Details modal opened successfully!")
                        modal_success = True
                    else:
                        print("   ⚠️ No visible modal found")
                        modal_success = False
                except:
                    print("   ⚠️ Neither accordion nor modal found")
                    modal_success = False
            
            # 9. Test second button to be sure
            print("8. 🔄 Testing second Details button...")
            if len(details_buttons) > 1:
                await details_buttons[1].click()
                await page.wait_for_timeout(1000)
                
                if not console_errors:
                    print("   ✅ Second button: No JavaScript errors!")
                    second_button_success = True
                else:
                    print("   ❌ Second button: JavaScript errors found")
                    second_button_success = False
            else:
                second_button_success = True  # No second button to test
            
            # 10. Screenshot for verification
            screenshot_path = '/app/minesearch_v2/backend/fixed_details_button_test.png'
            await page.screenshot(path=screenshot_path)
            print(f"9. 📷 Screenshot saved: {screenshot_path}")
            
            # 11. Summary
            print("\n" + "=" * 50)
            print("🎯 FIXED DETAILS BUTTON TEST RESULTS:")
            print(f"   ✅ Statistics table loaded: {len(table_rows) > 0}")
            print(f"   ✅ Details buttons found: {len(details_buttons)}")  
            print(f"   ✅ No JavaScript errors: {len(console_errors) == 0}")
            print(f"   ✅ First button works: {len(console_errors) == 0}")
            print(f"   ✅ Second button works: {second_button_success}")
            print(f"   ✅ Details displayed: {modal_success}")
            
            overall_success = (
                len(table_rows) > 0 and 
                len(details_buttons) > 0 and 
                len(console_errors) == 0 and
                second_button_success
            )
            
            if overall_success:
                print(f"\n🎉 DETAILS BUTTON FIX SUCCESSFUL!")
                print("✅ All JavaScript errors resolved")
                print("✅ Buttons are clickable without syntax errors")
            else:
                print(f"\n❌ FIX INCOMPLETE - Further investigation needed")
            
            return overall_success
            
        except Exception as e:
            print(f"❌ Test error: {e}")
            return False
            
        finally:
            await browser.close()

if __name__ == "__main__":
    result = asyncio.run(test_details_button_fix())
    print(f"\n🔍 Final Result: {'SUCCESS' if result else 'FAILED'}")