#!/usr/bin/env python3
"""
Author: rahn
Datum: 07.08.2025
Version: 1.0
Beschreibung: Manueller Button Test - so einfach wie möglich
"""

import asyncio
from playwright.async_api import async_playwright

async def manual_button_test():
    """Einfachster Test: Browser öffnen und manuell prüfen"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=2000)
        page = await browser.new_page()
        
        console_errors = []
        page.on('console', lambda msg: console_errors.append(msg.text) if msg.type == 'error' else None)
        
        try:
            print("🔍 MANUELLER BUTTON TEST")
            print("=" * 40)
            
            # 1. Seite laden
            print("1. 🌐 Lade http://localhost:8000...")
            await page.goto('http://localhost:8000')
            await page.wait_for_load_state('networkidle')
            print("   ✅ Seite geladen")
            
            # 2. Warte und zeige URL
            current_url = page.url
            print(f"   📍 URL: {current_url}")
            
            # 3. Screenshot von der Hauptseite
            await page.screenshot(path='/app/minesearch_v2/backend/manual_test_1_main.png')
            print("   📷 Screenshot: manual_test_1_main.png")
            
            # 4. Versuche Statistics-Tab zu finden mit verschiedenen Selektoren
            print("2. 🔍 Suche Statistics Tab...")
            
            # Verschiedene mögliche Selektoren
            selectors_to_try = [
                'input[value="statistics"]',
                'input[name="search_method"][value="statistics"]', 
                '#statistics',
                'label[for="statistics"]',
                '[data-tab="statistics"]'
            ]
            
            stats_element = None
            for selector in selectors_to_try:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        print(f"   ✅ Statistics element gefunden mit: {selector}")
                        stats_element = element
                        break
                    else:
                        print(f"   ⏭️ Kein Element für: {selector}")
                except:
                    print(f"   ❌ Fehler bei Selector: {selector}")
            
            if not stats_element:
                print("   ⚠️ Statistics Tab nicht automatisch gefunden")
                print("   🔍 Schaue DOM-Struktur an...")
                
                # Hole alle radio inputs
                radio_inputs = await page.evaluate("""
                    const radios = document.querySelectorAll('input[type="radio"]');
                    return Array.from(radios).map(r => ({
                        name: r.name,
                        value: r.value,
                        id: r.id,
                        checked: r.checked
                    }));
                """)
                
                print("   📋 Gefundene Radio Inputs:")
                for radio in radio_inputs:
                    print(f"      - Name: {radio['name']}, Value: {radio['value']}, ID: {radio['id']}")
                
                # Screenshot für manuelle Inspektion
                await page.screenshot(path='/app/minesearch_v2/backend/manual_test_2_dom.png')
                print("   📷 DOM Screenshot: manual_test_2_dom.png")
            
            # 5. Warte 10 Sekunden für manuelle Inspektion
            print("3. ⏳ Warte 10 Sekunden für manuelle Browser-Inspektion...")
            print("   👁️ BITTE MANUELL PRÜFEN:")
            print("   1. Ist die Seite korrekt geladen?")
            print("   2. Sind die Tab-Optionen sichtbar?")
            print("   3. Gibt es einen 'Suchstatistiken' Tab?")
            
            await page.wait_for_timeout(10000)  # 10 Sekunden warten
            
            # 6. Versuche JavaScript direkt zu testen
            print("4. 🧪 Teste JavaScript Konsole...")
            
            # Sehr einfacher JavaScript Test
            await page.evaluate("console.log('🧪 TEST: JavaScript funktioniert')")
            
            # Test safeJSONStringify
            safe_json_test = await page.evaluate("""
                function safeJSONStringify(value) {
                    if (!value) return "''";
                    return JSON.stringify(value);
                }
                
                const testId = 'openrouter:deepseek-free';
                const result = safeJSONStringify(testId);
                console.log('🧪 safeJSONStringify Test:', result);
                result;
            """)
            print(f"   📋 safeJSONStringify Test: {safe_json_test}")
            
            # 7. Finaler Screenshot
            await page.screenshot(path='/app/minesearch_v2/backend/manual_test_3_final.png')
            print("5. 📷 Finaler Screenshot: manual_test_3_final.png")
            
            # 8. Console Errors prüfen
            if console_errors:
                print("6. 🚨 Console Errors gefunden:")
                for error in console_errors:
                    print(f"   ❌ {error}")
                return False
            else:
                print("6. ✅ Keine Console Errors")
                
            return True
            
        except Exception as e:
            print(f"❌ Test Fehler: {e}")
            return False
            
        finally:
            print("\n⏳ Browser bleibt 15 Sekunden geöffnet für manuelle Inspektion...")
            await page.wait_for_timeout(15000)  # 15 Sekunden für Inspektion
            await browser.close()

if __name__ == "__main__":
    result = asyncio.run(manual_button_test())
    print(f"\n🎯 MANUELLER TEST: {'✅ ERFOLGREICH' if result else '❌ FEHLGESCHLAGEN'}")
    print("\n📋 NÄCHSTE SCHRITTE:")
    print("1. Screenshots prüfen (manual_test_*.png)")
    print("2. Falls Statistics Tab sichtbar: manuell klicken und Details testen")
    print("3. Browser Console (F12) auf JavaScript Errors prüfen")