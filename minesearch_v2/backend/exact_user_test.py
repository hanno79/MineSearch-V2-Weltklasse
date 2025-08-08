#!/usr/bin/env python3
"""
Author: rahn
Datum: 07.08.2025  
Version: 1.0
Beschreibung: EXAKTE Nachstellung des User-Tests
"""

import asyncio
from playwright.async_api import async_playwright

async def exact_user_test():
    """Genau das was der User beschrieben hat: Scroll runter, Suchstatistiken, Details Button"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=1500)
        page = await browser.new_page()
        
        console_messages = []
        
        def handle_console(msg):
            console_messages.append({
                'type': msg.type,
                'text': msg.text,
                'location': msg.location
            })
            print(f"🖥️ Console {msg.type}: {msg.text}")
        
        page.on('console', handle_console)
        
        try:
            print("🎯 EXAKTER USER TEST")
            print("=" * 50)
            
            # 1. Seite laden
            print("1. 🌐 Lade localhost:8000...")
            await page.goto('http://localhost:8000', wait_until='networkidle')
            await page.wait_for_timeout(2000)
            print("   ✅ Seite geladen")
            
            # 2. Nach unten scrollen (wie User beschrieben)
            print("2. 📜 Scrolle das Bild nach unten...")
            await page.evaluate("window.scrollTo(0, 400)")
            await page.wait_for_timeout(1000)
            
            # 3. Auf Suchstatistiken klicken (wie User beschrieben)  
            print("3. 📊 Klicke auf Suchstatistiken...")
            
            # Suche den Statistics Radio Button
            statistics_radio = await page.query_selector('input[name="search_method"][value="statistics"]')
            if not statistics_radio:
                print("   ❌ Statistics Radio Button nicht gefunden!")
                return False
                
            await statistics_radio.check()
            await page.wait_for_timeout(3000)  # Warte auf Tab-Wechsel
            print("   ✅ Statistics Tab aktiviert")
            
            # 4. Warte bis Tabelle geladen ist
            print("4. ⏳ Warte auf Tabellen-Daten...")
            try:
                await page.wait_for_selector('table tbody tr', timeout=15000)
                table_rows = await page.query_selector_all('table tbody tr')
                print(f"   ✅ Tabelle geladen mit {len(table_rows)} Zeilen")
            except Exception as e:
                print(f"   ❌ Tabelle nicht geladen: {e}")
                # Screenshot vom Problem
                await page.screenshot(path='/app/minesearch_v2/backend/table_load_error.png')
                return False
            
            # 5. In der Tabelle unten nach Details Button suchen (wie User beschrieben)
            print("5. 🔍 Suche Details Button in der ganz rechten Spalte...")
            
            # Finde alle Details Buttons
            details_buttons = await page.query_selector_all('button[onclick*="showModelDetails"]')
            if not details_buttons:
                print("   ❌ KEINE Details Buttons gefunden!")
                await page.screenshot(path='/app/minesearch_v2/backend/no_details_buttons.png')
                return False
                
            print(f"   ✅ {len(details_buttons)} Details Buttons gefunden")
            
            # 6. Onclick Attribut prüfen (Debug)
            first_button = details_buttons[0]
            onclick_attr = await first_button.get_attribute('onclick')
            print(f"   📋 Onclick: {onclick_attr}")
            
            # 7. Details Button klicken (wie User beschrieben)
            print("6. 🎯 Klicke auf den Details Button in der ganz rechten Spalte...")
            
            # Console errors vor Klick leeren
            console_messages.clear()
            
            # Button klicken
            await first_button.click()
            await page.wait_for_timeout(3000)  # Warte auf Reaktion
            
            # 8. Console Errors prüfen
            print("7. 🚨 Prüfe Console Errors nach Klick...")
            
            # Filtere nur JavaScript Errors
            js_errors = [msg for msg in console_messages if msg['type'] == 'error']
            
            if js_errors:
                print(f"   ❌ {len(js_errors)} JAVASCRIPT ERRORS GEFUNDEN:")
                for error in js_errors:
                    print(f"      {error['text']}")
                    if 'Uncaught SyntaxError' in error['text']:
                        print(f"      🎯 DAS IST DER FEHLER VOM USER!")
                await page.screenshot(path='/app/minesearch_v2/backend/js_error_screenshot.png')
                return False
            else:
                print("   ✅ Keine JavaScript Errors")
            
            # 9. Prüfe ob Detailseite sich öffnet (wie User fragt)
            print("8. 📋 Prüfe ob sich die Detailseite öffnet...")
            
            details_opened = False
            
            # Suche nach verschiedenen Detail-Anzeigen
            try:
                # Suche Accordion
                accordion = await page.query_selector('[id*="model-details-"]')
                if accordion:
                    is_visible = await accordion.is_visible()
                    if is_visible:
                        print("   ✅ Details ACCORDION geöffnet!")
                        details_opened = True
                        
                # Suche Modal
                if not details_opened:
                    modal = await page.query_selector('#detailsModal')
                    if modal:
                        is_visible = await modal.is_visible()
                        if is_visible:
                            print("   ✅ Details MODAL geöffnet!")
                            details_opened = True
                
                if not details_opened:
                    print("   ❌ DETAILSEITE ÖFFNET SICH NICHT!")
                    await page.screenshot(path='/app/minesearch_v2/backend/no_details_opened.png')
                    return False
                    
            except Exception as e:
                print(f"   ❌ Fehler beim Prüfen der Details: {e}")
                return False
            
            # 10. Screenshot vom Erfolg/Fehler
            await page.screenshot(path='/app/minesearch_v2/backend/final_test_result.png')
            print("9. 📷 Screenshot gespeichert: final_test_result.png")
            
            print(f"\n🎯 ANTWORT AUF USER FRAGE:")
            print(f"   Details Button geklickt: ✅ JA")
            print(f"   JavaScript Fehler: {'❌ JA' if js_errors else '✅ NEIN'}")
            print(f"   Detailseite öffnet sich: {'✅ JA' if details_opened else '❌ NEIN'}")
            
            return details_opened and not js_errors
            
        except Exception as e:
            print(f"❌ Test Fehler: {e}")
            await page.screenshot(path='/app/minesearch_v2/backend/test_exception.png')
            return False
            
        finally:
            await page.wait_for_timeout(5000)  # Zeit zum Anschauen
            await browser.close()

if __name__ == "__main__":
    result = asyncio.run(exact_user_test())
    print(f"\n{'🎉 SUCCESS' if result else '❌ FAILED'} - Genau wie beim User getestet")