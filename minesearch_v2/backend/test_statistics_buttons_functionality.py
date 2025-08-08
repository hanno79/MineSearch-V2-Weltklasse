"""
Author: rahn
Datum: 07.08.2025
Version: 1.0
Beschreibung: Test der Statistics-Button Funktionalität
"""

import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime

async def test_statistics_buttons():
    """Testet die Funktionalität aller Statistics-Buttons"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=1500)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        
        console_logs = []
        network_requests = []
        
        page.on('console', lambda msg: console_logs.append({
            'type': msg.type, 'text': msg.text, 'timestamp': datetime.now().isoformat()
        }))
        
        page.on('request', lambda request: network_requests.append({
            'method': request.method, 'url': request.url, 'timestamp': datetime.now().isoformat()
        }))
        
        try:
            print("🎯 FUNKTIONSTEST: Statistics Buttons")
            print("=" * 50)
            
            # Navigiere zur Seite
            await page.goto('http://localhost:8000', wait_until='networkidle')
            await page.wait_for_timeout(2000)
            
            # Aktiviere Statistics Tab
            print("\n1. 📈 Aktiviere Statistics Tab")
            stats_label = await page.query_selector('label[for="method_statistics"]')
            await stats_label.click()
            await page.wait_for_timeout(2000)
            
            # Screenshot der Statistics-Oberfläche
            await page.screenshot(path='test_stats_01_interface.png')
            print("📸 Screenshot: test_stats_01_interface.png")
            
            # Teste alle Buttons im Statistics Bereich
            print("\n2. 🔍 Suche alle Statistics Buttons")
            stats_form = await page.query_selector('#statistics_form')
            all_buttons = await stats_form.query_selector_all('button') if stats_form else []
            
            print(f"   Gefundene Buttons: {len(all_buttons)}")
            
            button_info = []
            for i, btn in enumerate(all_buttons):
                text = await btn.inner_text()
                onclick = await btn.get_attribute('onclick')
                is_visible = await btn.is_visible()
                button_info.append({
                    'index': i+1,
                    'text': text.strip(),
                    'onclick': onclick,
                    'visible': is_visible
                })
                print(f"   Button {i+1}: '{text.strip()}' onclick='{onclick}' visible={is_visible}")
            
            # Teste den wichtigsten Button: "Statistiken laden"
            print("\n3. 🖱️ Test: 'Statistiken laden' Button")
            load_stats_btn = None
            for info in button_info:
                if 'Statistiken laden' in info['text'] and info['visible']:
                    # Finde den Button wieder
                    buttons = await stats_form.query_selector_all('button')
                    load_stats_btn = buttons[info['index']-1]
                    break
            
            if load_stats_btn:
                print("   ✅ 'Statistiken laden' Button gefunden und sichtbar")
                
                # Klick auf den Button
                await load_stats_btn.click()
                print("   🖱️ Button geklickt")
                
                # Warte und beobachte
                print("   ⏱️ Warte 10 Sekunden auf API-Antwort...")
                await page.wait_for_timeout(10000)
                
                # Screenshot nach Button-Klick
                await page.screenshot(path='test_stats_02_after_load.png')
                print("📸 Screenshot: test_stats_02_after_load.png")
                
                # Prüfe ob Tabelle erschienen ist
                stats_table = await page.query_selector('#enhanced-statistics-table-container table')
                if stats_table:
                    table_visible = await stats_table.is_visible()
                    table_rows = await stats_table.query_selector_all('tbody tr')
                    print(f"   ✅ Statistics Tabelle gefunden: Visible={table_visible}, Rows={len(table_rows)}")
                else:
                    print("   ❌ Keine Statistics Tabelle gefunden")
                
            else:
                print("   ❌ 'Statistiken laden' Button nicht gefunden oder nicht sichtbar")
            
            # Teste Filter-Funktionalität
            print("\n4. 🔍 Test: Filter-Funktionalität")
            filter_form = await page.query_selector('#statistics-filter-form')
            if filter_form:
                # Finde Filter-Buttons
                filter_buttons = await filter_form.query_selector_all('button')
                print(f"   Filter Buttons gefunden: {len(filter_buttons)}")
                
                for btn in filter_buttons:
                    btn_text = await btn.inner_text()
                    btn_onclick = await btn.get_attribute('onclick')
                    btn_visible = await btn.is_visible()
                    print(f"   Filter Button: '{btn_text.strip()}' onclick='{btn_onclick}' visible={btn_visible}")
                    
                    # Teste "Filter anwenden" Button
                    if 'Filter anwenden' in btn_text and btn_visible:
                        print("   🖱️ Klick auf 'Filter anwenden'")
                        await btn.click()
                        await page.wait_for_timeout(5000)
                        
                        # Screenshot nach Filter
                        await page.screenshot(path='test_stats_03_after_filter.png')
                        print("📸 Screenshot: test_stats_03_after_filter.png")
                        break
            
            # Analysiere API-Aufrufe
            print("\n5. 📊 API-Aufruf Analyse")
            api_calls = [req for req in network_requests if '/api/' in req['url']]
            statistics_calls = [req for req in api_calls if 'statistics' in req['url']]
            
            print(f"   Gesamt API-Aufrufe: {len(api_calls)}")
            print(f"   Statistics API-Aufrufe: {len(statistics_calls)}")
            
            for call in statistics_calls:
                print(f"   {call['method']} {call['url']}")
            
            # Console Logs analysieren
            print("\n6. 📋 Console Logs Analysis")
            error_logs = [log for log in console_logs if log['type'] == 'error']
            warning_logs = [log for log in console_logs if log['type'] == 'warning']
            
            print(f"   Error Logs: {len(error_logs)}")
            print(f"   Warning Logs: {len(warning_logs)}")
            
            for error in error_logs[-5:]:  # Letzte 5 Fehler
                print(f"   ERROR: {error['text']}")
            
            # Final Report
            report = {
                'timestamp': datetime.now().isoformat(),
                'buttons_found': button_info,
                'api_calls': statistics_calls,
                'console_logs': {
                    'total': len(console_logs),
                    'errors': len(error_logs), 
                    'warnings': len(warning_logs)
                },
                'screenshots': [
                    'test_stats_01_interface.png',
                    'test_stats_02_after_load.png', 
                    'test_stats_03_after_filter.png'
                ]
            }
            
            with open('test_statistics_buttons_report.json', 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            print("\n✅ Statistics Buttons Test abgeschlossen!")
            print("📊 Report: test_statistics_buttons_report.json")
            
        except Exception as e:
            print(f"❌ Fehler: {e}")
            await page.screenshot(path='test_stats_error.png')
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_statistics_buttons())