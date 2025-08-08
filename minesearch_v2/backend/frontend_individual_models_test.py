#!/usr/bin/env python3
"""
Author: rahn
Datum: 07.08.2025
Version: 1.0
Beschreibung: Frontend Test für Individual Models und Details Button
ÄNDERUNG 07.08.2025: Test der neuen Individual Models im Browser Interface
"""

import asyncio
from playwright.async_api import async_playwright
import json
import time

async def test_statistics_with_individual_models():
    """Test der Statistik-Seite mit Individual Models"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Console errors sammeln
        console_errors = []
        page.on('console', lambda msg: console_errors.append(msg.text) if msg.type == 'error' else None)
        
        try:
            print("=== FRONTEND INDIVIDUAL MODELS TEST ===")
            print()
            
            # 1. Lade Hauptseite
            print("🌐 Schritt 1: Hauptseite laden...")
            await page.goto('http://localhost:8000')
            await page.wait_for_load_state('networkidle')
            
            # 2. Navigiere zu Statistik-Tab
            print("📊 Schritt 2: Statistik-Tab aktivieren...")
            await page.click('label[for="statistics"]')
            await page.wait_for_timeout(2000)
            
            # 3. Warte auf Modell-Tabelle
            print("⏳ Schritt 3: Warte auf Statistik-Tabelle...")
            await page.wait_for_selector('table tbody tr', timeout=10000)
            
            # 4. Zähle Tabellenzeilen
            model_rows = await page.query_selector_all('table tbody tr')
            print(f"✅ Gefunden: {len(model_rows)} Modell-Zeilen")
            
            # 5. Teste ersten Details Button
            print("🔍 Schritt 5: Teste Details Button...")
            first_details_button = await page.query_selector('button[onclick*="showModelDetails"]')
            
            if first_details_button:
                # Hole onclick Attribut
                onclick_attr = await first_details_button.get_attribute('onclick')
                print(f"📝 Details Button onclick: {onclick_attr[:100]}...")
                
                # Klicke Details Button
                await first_details_button.click()
                await page.wait_for_timeout(1000)
                
                # Prüfe ob Modal erscheint
                modal = await page.query_selector('#detailsModal')
                if modal:
                    modal_visible = await modal.is_visible()
                    print(f"✅ Details Modal {'sichtbar' if modal_visible else 'nicht sichtbar'}")
                    
                    if modal_visible:
                        # Hole Modal Inhalt
                        modal_title = await page.query_selector('#detailsModal .modal-title')
                        if modal_title:
                            title_text = await modal_title.inner_text()
                            print(f"📋 Modal Titel: {title_text}")
                        
                        # Schließe Modal
                        close_button = await page.query_selector('#detailsModal .modal-close')
                        if close_button:
                            await close_button.click()
                            await page.wait_for_timeout(500)
                
                else:
                    print("❌ Details Modal nicht gefunden")
            else:
                print("❌ Details Button nicht gefunden")
            
            # 6. Teste weitere Details Buttons (erste 3)
            print("🔄 Schritt 6: Teste weitere Details Buttons...")
            details_buttons = await page.query_selector_all('button[onclick*="showModelDetails"]')
            
            working_buttons = 0
            for i, button in enumerate(details_buttons[:3]):  # Teste nur erste 3
                try:
                    print(f"  Testing Details Button {i+1}...")
                    await button.click()
                    await page.wait_for_timeout(500)
                    
                    modal = await page.query_selector('#detailsModal')
                    if modal and await modal.is_visible():
                        working_buttons += 1
                        print(f"    ✅ Button {i+1} funktioniert")
                        
                        # Schließe Modal
                        close_button = await page.query_selector('#detailsModal .modal-close')
                        if close_button:
                            await close_button.click()
                            await page.wait_for_timeout(300)
                    else:
                        print(f"    ❌ Button {i+1} zeigt kein Modal")
                        
                except Exception as e:
                    print(f"    ❌ Button {i+1} Fehler: {str(e)}")
            
            print(f"✅ {working_buttons}/{min(3, len(details_buttons))} Details Buttons funktionieren")
            
            # 7. Prüfe Console Errors
            print("🔍 Schritt 7: Prüfe JavaScript Console Errors...")
            if console_errors:
                print("❌ JavaScript Errors gefunden:")
                for error in console_errors[:5]:  # Zeige nur erste 5
                    print(f"  - {error}")
            else:
                print("✅ Keine JavaScript Errors")
            
            # 8. Screenshot
            screenshot_path = '/app/minesearch_v2/backend/individual_models_test_screenshot.png'
            await page.screenshot(path=screenshot_path)
            print(f"📷 Screenshot gespeichert: {screenshot_path}")
            
            # 9. Zusammenfassung
            print()
            print("=== TEST ZUSAMMENFASSUNG ===")
            print(f"✅ Modell-Zeilen: {len(model_rows)}")
            print(f"✅ Funktionierende Details Buttons: {working_buttons}")
            print(f"{'✅' if not console_errors else '❌'} JavaScript Errors: {len(console_errors)}")
            
            success = len(model_rows) == 14 and working_buttons >= 2 and len(console_errors) == 0
            print(f"{'🎉 TEST ERFOLGREICH' if success else '❌ TEST FEHLGESCHLAGEN'}")
            
            return {
                'success': success,
                'model_rows': len(model_rows),
                'working_buttons': working_buttons,
                'console_errors': len(console_errors),
                'screenshot': screenshot_path
            }
            
        except Exception as e:
            print(f"❌ Test Fehler: {str(e)}")
            return {'success': False, 'error': str(e)}
            
        finally:
            await browser.close()

if __name__ == "__main__":
    result = asyncio.run(test_statistics_with_individual_models())
    print(f"\nErgebnis: {json.dumps(result, indent=2)}")