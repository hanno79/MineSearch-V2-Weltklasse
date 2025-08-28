#!/usr/bin/env python3
"""
Browser-Test für MineSearch Batch-Suche
Direkte Beobachtung der Frontend-Werte mit Playwright
"""

import asyncio
from playwright.async_api import async_playwright
import time
import os

async def test_batch_search():
    print("🔍 STARTE BROWSER-TEST FÜR BATCH-SUCHE")
    
    async with async_playwright() as p:
        # Starte Browser
        browser = await p.chromium.launch(headless=True, slow_mo=500)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # Navigiere zur MineSearch-Seite
            print("📍 Navigiere zu http://localhost:8000")
            await page.goto("http://localhost:8000")
            await page.wait_for_load_state('networkidle')
            
            # Prüfe ob Seite geladen
            title = await page.title()
            print(f"📄 Seiten-Titel: {title}")
            
            # Erstelle Test-CSV
            csv_content = """Name,Country,Region
Éléonore,Canada,Quebec
Lac Expanse,Canada,Quebec
Aubelle,Canada,Quebec"""
            
            with open('/tmp/test_playwright.csv', 'w', encoding='utf-8', newline='') as f:
                f.write(csv_content)
            print("📁 Test-CSV erstellt: /tmp/test_playwright.csv")
            
            # Upload CSV
            print("📤 Lade CSV hoch...")
            file_input = await page.query_selector('input[type="file"]')
            if file_input:
                await file_input.set_input_files('/tmp/test_playwright.csv')
                print("✅ CSV-Datei hochgeladen")
                
                # Warte auf Upload-Success
                await page.wait_for_selector('.csv-upload-success', timeout=10000)
                print("✅ CSV-Upload erfolgreich bestätigt")
                
                # Warte etwas und schaue nach Batch-Konfiguration
                await asyncio.sleep(2)
                
                # Konfiguriere Batch-Suche
                print("⚙️ Konfiguriere Batch-Suche...")
                
                # Wähle "Alle Minen durchsuchen"
                all_mines_radio = await page.query_selector('input[value="true"]')
                if all_mines_radio:
                    await all_mines_radio.check()
                    print("✅ 'Alle Minen durchsuchen' ausgewählt")
                
                # Starte Batch-Suche
                print("🚀 Starte Batch-Suche...")
                start_button = await page.query_selector('.batch-search-button')
                if start_button:
                    await start_button.click()
                    print("✅ Batch-Suche gestartet")
                    
                    # Warte auf Ergebnisse (maximal 2 Minuten)
                    print("⏳ Warte auf Batch-Ergebnisse...")
                    try:
                        await page.wait_for_selector('table', timeout=120000)
                        print("✅ Batch-Ergebnisse-Tabelle erschienen")
                        
                        # Warte zusätzlich, dass alle Suchen abgeschlossen sind
                        await asyncio.sleep(5)
                        
                        # Analysiere die Tabelle
                        print("\n🔍 ANALYSIERE BATCH-ERGEBNISSE IN TABELLE:")
                        
                        # Hole alle Tabellenzellen
                        cells = await page.query_selector_all('td')
                        
                        nichts_gefunden_count = 0
                        real_data_count = 0
                        total_cells = len(cells)
                        
                        cell_texts = []
                        for i, cell in enumerate(cells):
                            text = await cell.inner_text()
                            cell_texts.append(text.strip())
                            
                            if 'nichts gefunden' in text:
                                nichts_gefunden_count += 1
                            elif text.strip() and text.strip() not in ['✅', 'Éléonore', 'Lac Expanse', 'Aubelle', 'Canada', 'Quebec']:
                                # Echte Daten (außer Status, Namen und Basis-Daten)
                                real_data_count += 1
                        
                        print(f"📊 TABELLEN-ANALYSE:")
                        print(f"   📋 Gesamt Zellen: {total_cells}")
                        print(f"   ❌ 'nichts gefunden': {nichts_gefunden_count}")
                        print(f"   ✅ Echte Daten: {real_data_count}")
                        
                        # Zeige ersten Teil der Zell-Inhalte
                        print(f"\n📄 ERSTE 20 ZELLEN-INHALTE:")
                        for i, text in enumerate(cell_texts[:20]):
                            print(f"   {i+1:2d}: {repr(text)}")
                        
                        # Suche speziell nach Éléonore-Zeile
                        print(f"\n🔍 SUCHE NACH ÉLÉONORE-ZEILE:")
                        eleonore_found = False
                        for i, text in enumerate(cell_texts):
                            if text == 'Éléonore':
                                print(f"   Éléonore gefunden bei Index {i}")
                                # Zeige die nächsten 18 Zellen (alle Felder)
                                eleonore_row = cell_texts[i:i+19]  # Include Éléonore + 18 fields
                                for j, field_value in enumerate(eleonore_row):
                                    field_names = ['Name', 'Country', 'Region', 'Eigentümer', 'Betreiber', 'x-Koordinate', 'y-Koordinate', 'Aktivitätsstatus', 'Restaurationskosten', 'Jahr der Aufnahme der Kosten', 'Jahr der Erstellung des Dokumentes', 'Rohstoffabbau', 'Minentyp', 'Produktionsstart', 'Produktionsende', 'Fördermenge/Jahr', 'Fläche der Mine in qkm', 'Quellenangaben']
                                    if j < len(field_names):
                                        status = '✅' if field_value and field_value.strip() and 'nichts gefunden' not in field_value else '❌'
                                        print(f"     {status} {field_names[j]}: {repr(field_value)}")
                                eleonore_found = True
                                break
                        
                        if not eleonore_found:
                            print("   ❌ Éléonore-Zeile nicht identifiziert")
                        
                        # Ergebnis-Bewertung
                        print(f"\n🎯 TESTERGEBNIS:")
                        if nichts_gefunden_count > total_cells * 0.8:
                            print(f"   ❌ FEHLGESCHLAGEN: {nichts_gefunden_count}/{total_cells} Zellen sind 'nichts gefunden'")
                            print(f"   🔧 PROBLEM: Backend-Reparaturen kommen nicht im Frontend an!")
                        elif real_data_count >= 5:
                            print(f"   ✅ ERFOLGREICH: {real_data_count} Zellen mit echten Daten gefunden")
                        else:
                            print(f"   ⚠️ TEILWEISE: {real_data_count} echte Daten, aber noch zu wenige")
                        
                        # Screenshot für Debugging
                        await page.screenshot(path='/app/batch_test_screenshot.png')
                        print("📸 Screenshot gespeichert: /app/batch_test_screenshot.png")
                        
                    except Exception as e:
                        print(f"❌ Fehler beim Warten auf Ergebnisse: {e}")
                        # Screenshot bei Fehler
                        await page.screenshot(path='/app/batch_error_screenshot.png')
                        print("📸 Error-Screenshot: /app/batch_error_screenshot.png")
                else:
                    print("❌ Batch-Search Button nicht gefunden")
            else:
                print("❌ CSV-Upload Input nicht gefunden")
                
        except Exception as e:
            print(f"❌ Browser-Test Fehler: {e}")
            await page.screenshot(path='/app/browser_error_screenshot.png')
        finally:
            # Halte Browser kurz offen für Inspektion
            print("🔍 Halte Browser 10 Sekunden offen für manuelle Inspektion...")
            await asyncio.sleep(10)
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_batch_search())