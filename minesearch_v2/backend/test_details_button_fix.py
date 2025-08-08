#!/usr/bin/env python3
"""
Author: rahn
Datum: 07.08.2025  
Version: 1.0
Beschreibung: Test für Details Button Fix (URL /model/ → /models/)
"""

import asyncio
from playwright.async_api import async_playwright
import json

async def test_details_button_fix():
    """Test ob Details Buttons nach URL-Fix funktionieren"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        console_errors = []
        page.on('console', lambda msg: console_errors.append(msg.text) if msg.type == 'error' else None)
        
        try:
            print("🔧 DETAILS BUTTON FIX TEST")
            print("=" * 40)
            
            # 1. Lade Seite
            print("1. 🌐 Lade Hauptseite...")
            await page.goto('http://localhost:8000')
            await page.wait_for_load_state('networkidle')
            
            # 2. Aktiviere Statistics Tab
            print("2. 📊 Aktiviere Statistics Tab...")
            await page.click('label[for="statistics"]')
            await page.wait_for_timeout(3000)  # Warte auf Daten
            
            # 3. Finde Details Button
            print("3. 🔍 Suche Details Button...")
            details_buttons = await page.query_selector_all('button[onclick*="showModelDetails"]')
            
            if not details_buttons:
                print("❌ Keine Details Buttons gefunden!")
                return False
                
            print(f"   ✅ {len(details_buttons)} Details Buttons gefunden")
            
            # 4. Teste ersten Details Button
            print("4. 🎯 Teste ersten Details Button...")
            first_button = details_buttons[0]
            
            # Hole onclick Attribut zur Verifizierung
            onclick = await first_button.get_attribute('onclick')
            print(f"   📝 Onclick: {onclick[:50]}...")
            
            # Klicke Button
            print("   ⏳ Klicke Details Button...")
            await first_button.click()
            await page.wait_for_timeout(2000)
            
            # 5. Prüfe Console Errors
            if console_errors:
                print("❌ JAVASCRIPT ERRORS:")
                for error in console_errors:
                    print(f"   - {error}")
                return False
            else:
                print("   ✅ Keine JavaScript Errors!")
            
            # 6. Prüfe ob Accordion Details erscheinen
            print("5. 📋 Prüfe Details Accordion...")
            
            # Warte auf Accordion-Zeile oder Modal
            accordion_found = False
            try:
                # Suche nach Accordion-Zeile (könnte dynamisch erstellt werden)
                await page.wait_for_selector('[id*="model-details-"]', timeout=5000)
                accordion_found = True
                print("   ✅ Details Accordion gefunden!")
            except:
                # Falls kein Accordion, prüfe auf Modal
                try:
                    modal = await page.query_selector('#detailsModal')
                    if modal and await modal.is_visible():
                        print("   ✅ Details Modal geöffnet!")
                        accordion_found = True
                    else:
                        print("   ⚠️ Weder Accordion noch Modal gefunden")
                except:
                    print("   ⚠️ Weder Accordion noch Modal gefunden")
            
            # 7. Teste zweiten Button
            print("6. 🔄 Teste zweiten Details Button...")
            if len(details_buttons) > 1:
                await details_buttons[1].click()
                await page.wait_for_timeout(1000)
                
                if not console_errors:
                    print("   ✅ Zweiter Button: Keine Errors!")
                else:
                    print("   ❌ Zweiter Button: Errors gefunden")
            
            # 8. Screenshot
            screenshot_path = '/app/minesearch_v2/backend/details_button_fix_test.png'
            await page.screenshot(path=screenshot_path)
            print(f"7. 📷 Screenshot: {screenshot_path}")
            
            # 9. Zusammenfassung
            print("\n" + "=" * 40)
            print("🎯 TESTERGEBNIS:")
            print(f"   ✅ Details Buttons gefunden: {len(details_buttons)}")
            print(f"   {'✅' if not console_errors else '❌'} Console Errors: {len(console_errors)}")
            print(f"   {'✅' if accordion_found else '❌'} Details angezeigt: {accordion_found}")
            
            success = len(details_buttons) > 0 and len(console_errors) == 0
            print(f"\n{'🎉 FIX ERFOLGREICH!' if success else '❌ FIX FEHLGESCHLAGEN!'}")
            
            return success
            
        except Exception as e:
            print(f"❌ Test Fehler: {e}")
            return False
            
        finally:
            await browser.close()

if __name__ == "__main__":
    result = asyncio.run(test_details_button_fix())
    print(f"\nTest Result: {'SUCCESS' if result else 'FAILED'}")