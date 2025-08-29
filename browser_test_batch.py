#!/usr/bin/env python3
"""
Browser-Test für MineSearch Batch-Suche
Direkte Beobachtung der Frontend-Werte mit Playwright
"""

import asyncio
from playwright.async_api import async_playwright
import time
import os
import json

# Standard-Feldnamen als Fallback
DEFAULT_FIELD_NAMES = [
    'Name',
    'Country',
    'Region',
    'Eigentümer',
    'Betreiber',
    'x-Koordinate',
    'y-Koordinate',
    'Aktivitätsstatus',
    'Restaurationskosten',
    'Jahr der Aufnahme der Kosten',
    'Jahr der Erstellung des Dokumentes',
    'Rohstoffabbau',
    'Minentyp',
    'Produktionsstart',
    'Produktionsende',
    'Fördermenge/Jahr',
    'Fläche der Mine in qkm',
    'Quellenangaben',
]

# Pfad zur optionalen Konfigurationsdatei (kann via Env überschrieben werden)
CONFIG_FIELD_NAMES_PATH = os.getenv('FIELD_NAMES_CONFIG', '/app/config/field_names.json')

def load_field_names_config(path: str = CONFIG_FIELD_NAMES_PATH):
    """
    Lädt Feldnamen aus einer JSON-Datei. Erwartet eine Liste von Strings.
    Fällt bei Fehlern oder ungültiger Struktur auf DEFAULT_FIELD_NAMES zurück.
    """
    try:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if not isinstance(data, list):
                print("⚠️ Feldnamen-Konfiguration ist kein Array. Fallback auf Default.")
                return DEFAULT_FIELD_NAMES
            cleaned = []
            for idx, item in enumerate(data):
                if isinstance(item, str) and item.strip():
                    cleaned.append(item.strip())
                else:
                    print(f"⚠️ Ungültiger Eintrag in Feldnamen-Konfiguration an Position {idx}: {repr(item)}")
            if not cleaned:
                print("⚠️ Feldnamen-Konfiguration ist leer nach Bereinigung. Fallback auf Default.")
                return DEFAULT_FIELD_NAMES
            return cleaned
        else:
            print(f"ℹ️ Feldnamen-Konfigurationsdatei nicht gefunden: {path}. Verwende Default.")
            return DEFAULT_FIELD_NAMES
    except Exception as e:
        print(f"⚠️ Fehler beim Laden der Feldnamen-Konfiguration ({path}): {e}. Verwende Default.")
        return DEFAULT_FIELD_NAMES

# Global geladene Feldnamen
FIELD_NAMES = load_field_names_config()

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
                                # Zeige die nächsten Zellen entsprechend der Feldnamen-Anzahl (Éléonore + Felder)
                                eleonore_row = cell_texts[i:i+1+len(FIELD_NAMES)]
                                for j, field_value in enumerate(eleonore_row):
                                    if j < len(FIELD_NAMES):
                                        status = '✅' if field_value and field_value.strip() and 'nichts gefunden' not in field_value else '❌'
                                        print(f"     {status} {FIELD_NAMES[j]}: {repr(field_value)}")
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