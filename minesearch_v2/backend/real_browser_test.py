#!/usr/bin/env python3
"""
Author: rahn
Datum: 07.08.2025
Version: 1.0
Beschreibung: ECHTER Browser Test - Details Button klicken
"""

import asyncio
from playwright.async_api import async_playwright

async def real_details_button_test():
    """Echter Test: Browser öffnen, zu Statistiken navigieren, Details Button klicken"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        page = await browser.new_page()
        
        console_errors = []
        page.on('console', lambda msg: console_errors.append(msg.text) if msg.type == 'error' else None)
        
        try:
            print("🔍 ECHTER DETAILS BUTTON TEST")
            print("=" * 40)
            
            # 1. Seite laden
            print("1. 🌐 Lade http://localhost:8000...")
            await page.goto('http://localhost:8000')
            await page.wait_for_load_state('networkidle')
            print("   ✅ Seite geladen")
            
            # 2. Nach unten scrollen um Tab-Navigation zu sehen
            print("2. 📜 Scrolle nach unten...")
            await page.evaluate("window.scrollTo(0, 300)")
            await page.wait_for_timeout(1000)
            
            # 3. Suchstatistiken Tab klicken
            print("3. 📊 Klicke auf Suchstatistiken Tab...")
            await page.click('label[for="statistics"]')
            await page.wait_for_timeout(3000)  # Warten auf Daten
            print("   ✅ Suchstatistiken Tab aktiviert")
            
            # 4. Nach unten zur Tabelle scrollen
            print("4. 📜 Scrolle zur Statistik-Tabelle...")
            await page.evaluate("window.scrollTo(0, 800)")
            await page.wait_for_timeout(2000)
            
            # 5. Warte auf Tabelle und finde Details Button
            print("5. 🔍 Suche Details Button in Tabelle...")
            try:
                await page.wait_for_selector('table tbody tr', timeout=10000)
                details_buttons = await page.query_selector_all('button[onclick*="showModelDetails"]')
                
                if not details_buttons:
                    print("   ❌ KEINE Details Buttons gefunden!")
                    return False
                    
                print(f"   ✅ {len(details_buttons)} Details Buttons gefunden")
                
                # Hole onclick Attribut vom ersten Button
                first_button = details_buttons[0]
                onclick_attr = await first_button.get_attribute('onclick')
                print(f"   📋 Onclick Attribut: {onclick_attr}")
                
            except Exception as e:
                print(f"   ❌ Fehler beim Laden der Tabelle: {e}")
                return False
            
            # 6. KRITISCH: Details Button klicken
            print("6. 🎯 KLICKE DETAILS BUTTON...")
            console_errors.clear()  # Lösche alte Fehler
            
            await first_button.click()
            await page.wait_for_timeout(2000)  # Warte auf Reaktion
            
            # 7. Prüfe JavaScript Fehler
            print("7. 🚨 Prüfe JavaScript Console Errors...")
            if console_errors:
                print("   ❌ JAVASCRIPT FEHLER GEFUNDEN:")
                for error in console_errors:
                    print(f"      {error}")
                    
                # Speichere Screenshot mit Fehler
                await page.screenshot(path='/app/minesearch_v2/backend/error_screenshot.png')
                print("   📷 Fehler-Screenshot: error_screenshot.png")
                return False
            else:
                print("   ✅ Keine JavaScript Fehler")
            
            # 8. Prüfe ob Details Modal/Accordion geöffnet wurde
            print("8. 📋 Prüfe ob Details geöffnet wurden...")
            
            # Suche nach verschiedenen Möglichkeiten
            modal_found = False
            
            # Suche Accordion
            try:
                accordion = await page.query_selector('[id*="model-details-"]')
                if accordion and await accordion.is_visible():
                    print("   ✅ Details ACCORDION geöffnet!")
                    modal_found = True
            except:
                pass
                
            # Suche Modal
            if not modal_found:
                try:
                    modal = await page.query_selector('#detailsModal')
                    if modal and await modal.is_visible():
                        print("   ✅ Details MODAL geöffnet!")
                        modal_found = True
                except:
                    pass
            
            if not modal_found:
                print("   ❌ KEINE Details Modal/Accordion gefunden!")
                await page.screenshot(path='/app/minesearch_v2/backend/no_details_screenshot.png')
                print("   📷 Screenshot: no_details_screenshot.png")
                return False
            
            # 9. Screenshot vom Erfolg
            await page.screenshot(path='/app/minesearch_v2/backend/success_screenshot.png')
            print("9. 📷 Erfolg-Screenshot: success_screenshot.png")
            
            return True
            
        except Exception as e:
            print(f"❌ Test Fehler: {e}")
            await page.screenshot(path='/app/minesearch_v2/backend/test_error_screenshot.png')
            return False
            
        finally:
            await page.wait_for_timeout(3000)  # Zeit zum Anschauen
            await browser.close()

if __name__ == "__main__":
    result = asyncio.run(real_details_button_test())
    print(f"\n🎯 ECHTER TEST ERGEBNIS: {'✅ ERFOLGREICH' if result else '❌ FEHLGESCHLAGEN'}")