#!/usr/bin/env python3
"""
Author: rahn
Datum: 07.08.2025
Version: 1.0
Beschreibung: Navigation zur Statistics Tabelle und Button Test
"""

import asyncio
from playwright.async_api import async_playwright

async def navigate_to_statistics():
    """Navigiere zur Statistics Tabelle und teste Details Button"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=2000)
        page = await browser.new_page()
        
        console_messages = []
        def handle_console(msg):
            console_messages.append({
                'type': msg.type,
                'text': msg.text,
                'timestamp': asyncio.get_event_loop().time()
            })
        
        page.on('console', handle_console)
        
        try:
            print("🎯 NAVIGATE TO STATISTICS TEST")
            print("=" * 50)
            
            # 1. Seite laden
            print("1. 🌐 Lade http://localhost:8000...")
            await page.goto('http://localhost:8000')
            await page.wait_for_load_state('networkidle')
            print("   ✅ Seite geladen")
            
            # 2. Screenshot der Hauptseite
            await page.screenshot(path='/app/minesearch_v2/backend/nav_1_main.png')
            print("   📷 Screenshot: nav_1_main.png")
            
            # 3. Statistics Tab klicken
            print("2. 📊 Klicke Statistics Tab...")
            
            try:
                # Finde Statistics Radio Button
                stats_input = await page.query_selector('input[value="statistics"]')
                if stats_input:
                    await stats_input.check()
                    print("   ✅ Statistics Radio Button aktiviert")
                    await page.wait_for_timeout(3000)  # Warte auf Tab-Wechsel
                else:
                    print("   ❌ Statistics Radio Button nicht gefunden")
                    return False
                    
            except Exception as e:
                print(f"   ❌ Fehler beim Aktivieren des Statistics Tab: {e}")
                return False
            
            # 4. Screenshot nach Tab-Wechsel
            await page.screenshot(path='/app/minesearch_v2/backend/nav_2_stats_tab.png')
            print("   📷 Screenshot nach Tab-Wechsel: nav_2_stats_tab.png")
            
            # 5. Warte auf Tabelle
            print("3. ⏳ Warte auf Statistics Tabelle...")
            
            try:
                # Warte auf Tabelle mit erhöhtem Timeout
                await page.wait_for_selector('table tbody tr', timeout=20000)
                
                # Zähle Tabellenzeilen
                table_rows = await page.query_selector_all('table tbody tr')
                print(f"   ✅ Tabelle geladen mit {len(table_rows)} Zeilen")
                
                # Screenshot der Tabelle
                await page.screenshot(path='/app/minesearch_v2/backend/nav_3_table_loaded.png')
                print("   📷 Screenshot mit Tabelle: nav_3_table_loaded.png")
                
            except Exception as e:
                print(f"   ❌ Tabelle nicht geladen: {e}")
                await page.screenshot(path='/app/minesearch_v2/backend/nav_3_table_error.png')
                print("   📷 Error Screenshot: nav_3_table_error.png")
                return False
            
            # 6. Suche Details Buttons
            print("4. 🔍 Suche Details Buttons...")
            
            try:
                # Verschiedene Selektoren für Details Buttons
                details_selectors = [
                    'button[onclick*="showModelDetails"]',
                    'button:has-text("Details")',
                    'button:has-text("📊")',
                    '.details-btn'
                ]
                
                details_buttons = []
                for selector in details_selectors:
                    buttons = await page.query_selector_all(selector)
                    if buttons:
                        details_buttons.extend(buttons)
                        print(f"   ✅ {len(buttons)} Buttons gefunden mit: {selector}")
                        break
                
                if not details_buttons:
                    print("   ❌ KEINE Details Buttons gefunden!")
                    
                    # Debug: Alle Buttons suchen
                    all_buttons = await page.query_selector_all('button')
                    print(f"   🔍 Gefundene Buttons insgesamt: {len(all_buttons)}")
                    
                    for i, btn in enumerate(all_buttons[:5]):  # Nur erste 5
                        btn_text = await btn.inner_text()
                        onclick = await btn.get_attribute('onclick')
                        print(f"      Button {i+1}: '{btn_text}' onclick='{onclick}'")
                    
                    await page.screenshot(path='/app/minesearch_v2/backend/nav_4_no_details.png')
                    return False
                else:
                    print(f"   ✅ {len(details_buttons)} Details Buttons gefunden")
                
            except Exception as e:
                print(f"   ❌ Fehler beim Suchen der Details Buttons: {e}")
                return False
            
            # 7. Teste ersten Details Button
            print("5. 🎯 Teste ersten Details Button...")
            
            try:
                first_button = details_buttons[0]
                
                # Hole Button Informationen
                btn_text = await first_button.inner_text()
                onclick_attr = await first_button.get_attribute('onclick')
                
                print(f"   📋 Button Text: '{btn_text}'")
                print(f"   📋 Onclick: '{onclick_attr}'")
                
                # Lösche Console Messages vor Klick
                console_messages.clear()
                
                # Button klicken
                print("   🎯 KLICKE BUTTON...")
                await first_button.click()
                await page.wait_for_timeout(3000)  # Warte auf Reaktion
                
                # Screenshot nach Klick
                await page.screenshot(path='/app/minesearch_v2/backend/nav_5_after_click.png')
                print("   📷 Screenshot nach Klick: nav_5_after_click.png")
                
                # Console Messages prüfen
                js_errors = [msg for msg in console_messages if msg['type'] == 'error']
                
                if js_errors:
                    print("   ❌ JAVASCRIPT ERRORS nach Klick:")
                    for error in js_errors:
                        print(f"      {error['text']}")
                        
                        # Prüfe auf den spezifischen User-Error
                        if 'Uncaught SyntaxError: Unexpected end of input' in error['text']:
                            print("      🎯 DAS IST DER FEHLER VOM USER!")
                    return False
                else:
                    print("   ✅ Keine JavaScript Errors")
                
                # Prüfe ob Details Modal/Accordion geöffnet wurde
                print("6. 📋 Prüfe ob Details geöffnet wurden...")
                
                # Suche nach Details Modal
                modal_selectors = [
                    '#detailsModal',
                    '[id*="model-details-"]',
                    '.modal:visible',
                    '.details-modal'
                ]
                
                details_opened = False
                for selector in modal_selectors:
                    try:
                        modal = await page.query_selector(selector)
                        if modal and await modal.is_visible():
                            print(f"   ✅ Details Modal geöffnet: {selector}")
                            details_opened = True
                            break
                    except:
                        continue
                
                if not details_opened:
                    print("   ❌ KEIN Details Modal geöffnet")
                    return False
                
                return True
                
            except Exception as e:
                print(f"   ❌ Fehler beim Testen des Details Button: {e}")
                return False
            
        except Exception as e:
            print(f"❌ Test Fehler: {e}")
            return False
            
        finally:
            print("\n⏳ Browser bleibt 10 Sekunden für Inspektion...")
            await page.wait_for_timeout(10000)
            await browser.close()

if __name__ == "__main__":
    result = asyncio.run(navigate_to_statistics())
    print(f"\n🎯 NAVIGATION TEST: {'✅ ERFOLGREICH' if result else '❌ FEHLGESCHLAGEN'}")
    
    if result:
        print("✅ Details Buttons funktionieren!")
        print("✅ Kein JavaScript Error")
        print("✅ Details Modal öffnet sich")
    else:
        print("❌ Details Buttons haben noch Probleme")
        print("📷 Siehe Screenshots: nav_*.png")
        print("🔍 Prüfe Console für JavaScript Errors")