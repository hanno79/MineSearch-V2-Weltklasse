#!/usr/bin/env python3
"""
Author: rahn
Datum: 07.09.2025
Version: 1.0
Beschreibung: Browser-Test für Mont Wright Mine mit neuen Fördermenge-Feldern
"""

import asyncio
import sys
from playwright.async_api import async_playwright

async def test_mont_wright_mine():
    """Führt einen End-to-End Browser-Test für Mont Wright Mine durch"""
    print("🚀 Starte Browser-Test für Mont Wright Mine...")

    async with async_playwright() as p:
        # Browser starten (sichtbar für bessere Überwachung)
        browser = await p.chromium.launch(
            headless=False,
            args=['--disable-web-security', '--disable-features=VizDisplayCompositor']
        )

        page = await browser.new_page()

        try:
            print("📡 Verbinde zu MineSearch Frontend...")
            await page.goto('http://localhost:8000', wait_until='networkidle')

            # Screenshot der Startseite
            await page.screenshot(path='mont_wright_test_1_homepage.png', full_page=True)
            print("📸 Screenshot: Homepage gespeichert")

            # Warte auf das Laden der Seite
            await page.wait_for_timeout(3000)

            # Suche nach Einzelsuche Link/Button
            print("🔍 Suche Einzelsuche-Navigation...")

            # Versuche verschiedene Selektoren für Einzelsuche
            selectors_to_try = [
                'text=Einzelsuche',
                'text=Single Search',
                'text=Mine Search',
                'a[href*="search"]',
                'button:has-text("Search")',
                'input[type="text"]'  # Fallback: Direkte Eingabe wenn schon auf Suchseite
            ]

            navigation_successful = False
            for selector in selectors_to_try:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        print(f"✅ Gefunden: {selector}")
                        if selector != 'input[type="text"]':  # Nicht für input klicken
                            await element.click()
                            await page.wait_for_timeout(2000)
                        navigation_successful = True
                        break
                except:
                    continue

            if not navigation_successful:
                print("⚠️ Navigation zur Einzelsuche nicht gefunden, versuche direkte Eingabe...")

            # Screenshot vor der Eingabe
            await page.screenshot(path='mont_wright_test_2_before_input.png', full_page=True)

            # Mont Wright Daten eingeben
            print("✍️ Gebe Mont Wright Suchparameter ein...")

            # Versuche Mine-Name Eingabe
            mine_input_selectors = [
                'input[placeholder*="Mine"]',
                'input[placeholder*="mine"]',
                'input[name*="mine"]',
                'input[id*="mine"]',
                '#mineName',
                'input[type="text"]'
            ]

            for selector in mine_input_selectors:
                try:
                    await page.fill(selector, 'Mont Wright')
                    print(f"✅ Mine-Name eingegeben: {selector}")
                    break
                except:
                    continue

            # Versuche Land Eingabe
            country_input_selectors = [
                'input[placeholder*="Land"]',
                'input[placeholder*="Country"]',
                'input[name*="country"]',
                'input[id*="country"]',
                '#country'
            ]

            for selector in country_input_selectors:
                try:
                    await page.fill(selector, 'Kanada')
                    print(f"✅ Land eingegeben: {selector}")
                    break
                except:
                    continue

            # Versuche Modell-Auswahl
            print("🤖 Versuche AI-Modelle auszuwählen...")
            model_selectors = [
                'input[value="openrouter:deepseek-free"]',
                'input[value*="deepseek"]',
                'input[type="checkbox"]'
            ]

            models_selected = 0
            for selector in model_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    for element in elements[:3]:  # Maximal 3 Modelle
                        await element.check()
                        models_selected += 1
                except:
                    continue

            print(f"✅ {models_selected} Modelle ausgewählt")

            # Screenshot vor dem Suche-Start
            await page.screenshot(path='mont_wright_test_3_before_search.png', full_page=True)

            # Suche starten
            print("🚀 Versuche Suche zu starten...")
            search_button_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Search")',
                'button:has-text("Suchen")',
                '.search-button',
                '#searchButton'
            ]

            search_started = False
            for selector in search_button_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        await element.click()
                        print(f"✅ Suche gestartet mit: {selector}")
                        search_started = True
                        break
                except:
                    continue

            if not search_started:
                print("⚠️ Suche-Button nicht gefunden, versuche Enter-Taste...")
                await page.keyboard.press('Enter')

            # Warte auf Ergebnisse oder Änderung der Seite
            print("⏳ Warte auf Suchergebnisse...")

            # Warte auf verschiedene mögliche Ergebnis-Selektoren
            result_selectors = [
                '.results-table',
                'table',
                '.search-results',
                '#results',
                '.result-container'
            ]

            results_found = False
            for selector in result_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=60000)  # 1 Minute
                    print(f"✅ Ergebnisse gefunden: {selector}")
                    results_found = True
                    break
                except:
                    continue

            # Screenshot der aktuellen Seite (auch wenn keine Ergebnisse)
            await page.screenshot(path='mont_wright_test_4_current_state.png', full_page=True)

            if not results_found:
                print("⚠️ Keine Ergebnistabelle gefunden, analysiere aktuelle Seite...")

                # Prüfe Seiten-Inhalt
                page_content = await page.content()

                # Suche nach Fördermenge-Begriffen im Seiteninhalt
                if 'Fördermenge/Jahr Rohstoff' in page_content:
                    print("✅ Neues Feld 'Fördermenge/Jahr Rohstoff' im Seiteninhalt gefunden!")

                if 'Fördermenge/Jahr Abraum' in page_content:
                    print("✅ Neues Feld 'Fördermenge/Jahr Abraum' im Seiteninhalt gefunden!")

                if 'Fördermenge/Jahr' in page_content and 'Rohstoff' not in page_content:
                    print("⚠️ Altes Feld 'Fördermenge/Jahr' noch vorhanden!")

                # Versuche trotzdem Tabellen zu finden
                tables = await page.query_selector_all('table')
                if tables:
                    print(f"📋 {len(tables)} Tabelle(n) auf der Seite gefunden")
                    results_found = True

            # KRITISCHE VALIDIERUNG: Prüfe neue Felder
            print("🔍 Validiere neue Fördermenge-Felder...")

            table_headers = []
            table_data = []

            try:
                # Versuche Tabellen-Header zu extrahieren
                headers = await page.query_selector_all('table thead th, table th, .header')
                if headers:
                    table_headers = [await h.text_content() for h in headers]
                    table_headers = [h.strip() for h in table_headers if h and h.strip()]

                print(f"📋 Gefundene Tabellen-Header: {table_headers}")

                # Versuche erste Datenzeile zu extrahieren
                data_cells = await page.query_selector_all('table tbody tr:first-child td, table tr:first-child td')
                if data_cells:
                    table_data = [await cell.text_content() for cell in data_cells]
                    table_data = [d.strip() if d else '' for d in table_data]

                print(f"📋 Erste Datenzeile: {table_data[:5]}...")  # Nur erste 5 Werte zeigen

            except Exception as e:
                print(f"⚠️ Fehler beim Extrahieren der Tabellendaten: {e}")

            # Validierung der neuen Felder
            has_rohstoff_field = any('Fördermenge/Jahr Rohstoff' in str(h) for h in table_headers)
            has_abraum_field = any('Fördermenge/Jahr Abraum' in str(h) for h in table_headers)
            has_old_field = any(h == 'Fördermenge/Jahr' for h in table_headers)

            print("✅ VALIDIERUNGSERGEBNISSE:")
            print(f"   - Fördermenge/Jahr Rohstoff: {'✅ VORHANDEN' if has_rohstoff_field else '❌ FEHLT'}")
            print(f"   - Fördermenge/Jahr Abraum: {'✅ VORHANDEN' if has_abraum_field else '❌ FEHLT'}")
            print(f"   - Alte Fördermenge/Jahr: {'❌ NOCH VORHANDEN (FEHLER)' if has_old_field else '✅ ENTFERNT'}")

            # Analysiere Dateninhalt wenn verfügbar
            if table_data:
                rohstoff_index = None
                abraum_index = None

                for i, header in enumerate(table_headers):
                    if 'Fördermenge/Jahr Rohstoff' in str(header):
                        rohstoff_index = i
                    elif 'Fördermenge/Jahr Abraum' in str(header):
                        abraum_index = i

                if rohstoff_index is not None and rohstoff_index < len(table_data):
                    print(f"📈 Rohstoff-Produktion: {table_data[rohstoff_index]}")

                if abraum_index is not None and abraum_index < len(table_data):
                    print(f"🏔️ Abraum-Extraktion: {table_data[abraum_index]}")

            # Finale Screenshots
            await page.screenshot(path='mont_wright_test_5_final_validation.png', full_page=True)
            print("📸 Screenshot: Finale Validierung gespeichert")

            # Test-Zusammenfassung
            test_success = has_rohstoff_field and has_abraum_field and not has_old_field
            print("\n🎯 TEST-ZUSAMMENFASSUNG:")
            print(f"   Status: {'✅ ERFOLGREICH' if test_success else '❌ FEHLGESCHLAGEN'}")
            print(f"   Mine: Mont Wright, Quebec, Kanada")
            print(f"   Feldaufteilung: {'Korrekt implementiert' if test_success else 'Probleme erkannt'}")
            print(f"   Ergebnisse gefunden: {'✅ JA' if results_found else '❌ NEIN'}")

            return {
                'success': test_success,
                'results_found': results_found,
                'headers': table_headers,
                'data': table_data,
                'screenshots': [
                    'mont_wright_test_1_homepage.png',
                    'mont_wright_test_2_before_input.png',
                    'mont_wright_test_3_before_search.png',
                    'mont_wright_test_4_current_state.png',
                    'mont_wright_test_5_final_validation.png'
                ]
            }

        except Exception as error:
            print(f"❌ Test-Fehler: {error}")
            await page.screenshot(path='mont_wright_test_error.png', full_page=True)
            raise error

        finally:
            # Browser schließen
            await browser.close()
            print("🔚 Browser geschlossen")

async def main():
    """Haupt-Testfunktion"""
    try:
        result = await test_mont_wright_mine()
        print(f"\n🏁 Test abgeschlossen: {'ERFOLGREICH ✅' if result['success'] else 'FEHLGESCHLAGEN ❌'}")
        return 0 if result['success'] else 1

    except Exception as error:
        print(f"\n💥 Test-Ausführung fehlgeschlagen: {error}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
