#!/usr/bin/env python3
"""
Browser-Automation für MineSearch Frontend Testing
Author: rahn
Datum: 02.08.2025
Version: 1.0
Beschreibung: Automatisiert den Browser-Test der Statistics-Seite
"""

import asyncio
from playwright.async_api import async_playwright
import json
import time
from pathlib import Path

class MineSearchUIInspector:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.screenshots_dir = Path("/app/minesearch_v2/backend/screenshots")
        self.screenshots_dir.mkdir(exist_ok=True)
        
    async def run_automation(self):
        """Hauptautomatisierung für MineSearch Frontend"""
        async with async_playwright() as p:
            # Browser starten (headless für Container-Umgebung)
            browser = await p.chromium.launch(headless=True, slow_mo=500)
            page = await browser.new_page()
            
            try:
                print("🚀 Starte Browser-Automation für MineSearch...")
                
                # 1. Zur Hauptseite navigieren
                print(f"📍 Navigiere zu {self.base_url}")
                await page.goto(self.base_url, timeout=60000)
                await page.wait_for_load_state('networkidle', timeout=60000)
                
                # Screenshot der Startseite
                await page.screenshot(path=self.screenshots_dir / "01_startseite.png")
                print("📸 Screenshot der Startseite gespeichert")
                
                # 2. Warten auf vollständiges Laden
                await page.wait_for_timeout(3000)
                
                # 3. Zum Statistics-Tab wechseln
                print("🔄 Wechsle zum Statistics-Tab...")
                
                # Zuerst prüfen welche Tabs verfügbar sind
                tabs = await page.locator('input[name="search_method"]').all()
                print(f"📋 Gefundene Tabs: {len(tabs)}")
                
                for i, tab in enumerate(tabs):
                    value = await tab.get_attribute('value')
                    print(f"  Tab {i}: {value}")
                
                # Statistics Tab suchen und klicken
                stats_tab = page.locator('input[name="search_method"][value="statistics"]')
                tab_count = await stats_tab.count()
                print(f"🎯 Statistics Tab gefunden: {tab_count}")
                
                if tab_count > 0:
                    # Force click mit JavaScript
                    await page.evaluate("document.querySelector('input[name=\"search_method\"][value=\"statistics\"]').click()")
                    print("✅ Statistics Tab geklickt (JavaScript)")
                else:
                    print("❌ Statistics Tab nicht gefunden")
                    # Versuche alternative Selektoren
                    alt_tab = page.locator('label:has-text("📈 Suchstatistiken")')
                    alt_count = await alt_tab.count()
                    print(f"🔄 Alternative Selector gefunden: {alt_count}")
                    if alt_count > 0:
                        await page.evaluate("document.querySelector('label').click()", alt_tab)
                        print("✅ Alternative Selector geklickt")
                
                await page.wait_for_timeout(2000)
                
                # Screenshot nach Tab-Wechsel
                await page.screenshot(path=self.screenshots_dir / "02_statistics_tab.png")
                print("📸 Screenshot des Statistics-Tabs gespeichert")
                
                # 4. Statistiken laden
                print("📊 Lade Statistiken...")
                
                # Suche spezifisch nach dem Statistics Load-Button
                stats_button = page.locator('button[onclick="loadStatistics()"]')
                button_count = await stats_button.count()
                print(f"🎯 Statistics Button gefunden: {button_count}")
                
                button_clicked = False
                if button_count > 0:
                    await stats_button.click()
                    print("✅ Statistics Button geklickt")
                    button_clicked = True
                
                if not button_clicked:
                    print("🔄 Kein Load-Button gefunden, versuche direktes Laden...")
                    # JavaScript zum direkten Laden der Statistiken
                    await page.evaluate("if (typeof loadStatistics === 'function') loadStatistics();")
                
                await page.wait_for_timeout(5000)  # Warten auf Laden
                
                # 5. Hauptstatistik-Tabelle finden und screenshot
                print("🔍 Suche Haupt-Statistik-Tabelle...")
                
                # Verschiedene Table-Selektoren versuchen
                table_selectors = [
                    '#statistics-table-container table',
                    '#enhanced-statistics-table-container table', 
                    '.statistics-table',
                    '.consolidated-table',
                    'table'
                ]
                
                table_found = False
                for selector in table_selectors:
                    try:
                        await page.wait_for_selector(selector, timeout=3000)
                        print(f"✅ Tabelle gefunden: {selector}")
                        table_found = True
                        break
                    except:
                        print(f"⏳ Tabelle nicht gefunden: {selector}")
                        continue
                
                if not table_found:
                    print("❌ Keine Tabelle gefunden - Screenshot für Debug")
                    await page.screenshot(path=self.screenshots_dir / "no_table_debug.png")
                    
                    # Alle verfügbaren Elemente auf der Seite anzeigen
                    content = await page.evaluate("""
                        () => {
                            const elements = document.querySelectorAll('*');
                            const info = [];
                            for (let el of elements) {
                                if (el.id || el.className) {
                                    info.push({
                                        tag: el.tagName,
                                        id: el.id || '',
                                        className: el.className || ''
                                    });
                                }
                            }
                            return info.slice(0, 20);  // Erste 20 Elemente
                        }
                    """)
                    print("🔍 Verfügbare Elemente:")
                    for el in content:
                        print(f"  {el['tag']} id='{el['id']}' class='{el['className']}'")
                    
                    # Versuche trotzdem weiter zu machen
                    return {"error": "No statistics table found", "debug_elements": content}
                else:
                    print("✅ Tabelle gefunden und bereit für Extraktion")
                
                # Screenshot der geladenen Statistiken
                await page.screenshot(path=self.screenshots_dir / "03_statistics_loaded.png")
                print("📸 Screenshot der geladenen Statistiken gespeichert")
                
                # 6. Tabellendaten extrahieren (erste 5 Zeilen)
                print("📋 Extrahiere erste 5 Tabellenzeilen...")
                table_data = await self.extract_table_data(page)
                
                # 7. Speichere extrahierte Daten
                data_file = self.screenshots_dir / "extracted_table_data.json"
                with open(data_file, 'w', encoding='utf-8') as f:
                    json.dump(table_data, f, indent=2, ensure_ascii=False)
                
                print(f"💾 Tabellendaten gespeichert in {data_file}")
                print(f"📊 Gefunden: {len(table_data.get('rows', []))} Datenzeilen")
                
                # 8. Finaler Screenshot der kompletten Seite
                await page.screenshot(path=self.screenshots_dir / "04_final_state.png", full_page=True)
                print("📸 Finaler Full-Page Screenshot gespeichert")
                
                return table_data
                
            except Exception as e:
                print(f"❌ Fehler bei Browser-Automation: {e}")
                await page.screenshot(path=self.screenshots_dir / "error_screenshot.png")
                return {"error": str(e)}
                
            finally:
                print("🔚 Schließe Browser...")
                await browser.close()
    
    async def extract_table_data(self, page):
        """Extrahiert Daten aus der Statistik-Tabelle"""
        try:
            # Versuche verschiedene Tabellen-Selektoren
            table_selectors = [
                '#enhanced-statistics-table-container table',
                '#statistics-table-container table',
                '.statistics-table',
                'table'
            ]
            
            working_selector = None
            for selector in table_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=5000)
                    working_selector = selector
                    print(f"✅ Tabelle für Extraktion gefunden: {selector}")
                    break
                except:
                    continue
            
            if not working_selector:
                return {"error": "No table found for extraction"}
            
            # Headers und Rows mit dem gefundenen Selector extrahieren
            table_data = await page.evaluate(f"""
                () => {{
                    const table = document.querySelector('{working_selector}');
                    if (!table) return {{error: 'Table not accessible'}};
                    
                    // Headers extrahieren
                    const headerCells = table.querySelectorAll('thead th, thead td');
                    const headers = Array.from(headerCells).map(th => th.textContent.trim());
                    
                    // Datenzeilen extrahieren
                    const dataRows = table.querySelectorAll('tbody tr');
                    const rows = [];
                    
                    for (let i = 0; i < Math.min(5, dataRows.length); i++) {{
                        const row = dataRows[i];
                        const cells = row.querySelectorAll('td');
                        const rowData = Array.from(cells).map(td => td.textContent.trim());
                        rows.push(rowData);
                    }}
                    
                    return {{
                        headers: headers,
                        rows: rows,
                        table_selector: '{working_selector}',
                        total_table_rows: dataRows.length
                    }};
                }}
            """)
            
            # Zusätzliche Metadaten hinzufügen
            table_data["total_rows_found"] = len(table_data.get("rows", []))
            table_data["extraction_timestamp"] = time.time()
            
            return table_data
            
        except Exception as e:
            print(f"❌ Fehler beim Extrahieren der Tabellendaten: {e}")
            return {"error": f"Table extraction failed: {e}"}

# Hauptausführung
async def main():
    inspector = MineSearchUIInspector()
    result = await inspector.run_automation()
    
    print("\n" + "="*50)
    print("🎯 BROWSER-AUTOMATION ABGESCHLOSSEN")
    print("="*50)
    
    if "error" in result:
        print(f"❌ Fehler: {result['error']}")
    else:
        print(f"✅ Erfolgreich abgeschlossen")
        print(f"📊 Headers: {result.get('headers', [])}")
        print(f"📋 Erste 5 Zeilen extrahiert: {result.get('total_rows_found', 0)}")
    
    return result

if __name__ == "__main__":
    result = asyncio.run(main())