"""
Author: rahn
Datum: 07.08.2025
Version: 1.0
Beschreibung: Finaler Test nach Statistics API Fix
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime

async def test_statistics_fix():
    """Testet ob das Statistics API Fix funktioniert"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=1500)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        
        console_logs = []
        network_requests = []
        
        page.on('console', lambda msg: console_logs.append(f"{msg.type.upper()}: {msg.text}"))
        page.on('request', lambda request: network_requests.append(f"{request.method} {request.url}"))
        
        try:
            print("🔧 FINAL TEST: Statistics API Fix")
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
            await page.screenshot(path='final_test_01_statistics_tab.png')
            print("📸 Screenshot: final_test_01_statistics_tab.png")
            
            # Klicke auf "Statistiken laden" Button
            print("\n2. 🖱️ Klick auf 'Statistiken laden'")
            stats_form = await page.query_selector('#statistics_form')
            load_btn = None
            
            if stats_form:
                buttons = await stats_form.query_selector_all('button')
                for btn in buttons:
                    text = await btn.inner_text()
                    if 'Statistiken laden' in text:
                        load_btn = btn
                        break
            
            if load_btn:
                await load_btn.click()
                print("✅ Button geklickt")
                
                # Warte auf API-Antwort
                print("⏱️ Warte 15 Sekunden auf API-Antwort und Tabellen-Rendering...")
                await page.wait_for_timeout(15000)
                
                # Screenshot nach Button-Klick
                await page.screenshot(path='final_test_02_after_statistics_load.png')
                print("📸 Screenshot: final_test_02_after_statistics_load.png")
                
                # Prüfe ob Tabelle erschienen ist
                stats_container = await page.query_selector('#enhanced-statistics-table-container')
                if stats_container:
                    container_html = await stats_container.inner_html()
                    has_table = 'table' in container_html.lower()
                    has_data_rows = '<tbody>' in container_html and '<tr>' in container_html
                    
                    print(f"\n3. 📊 Tabellen-Analyse")
                    print(f"   Container gefunden: ✅")
                    print(f"   Enthält Tabelle: {'✅' if has_table else '❌'}")
                    print(f"   Enthält Datenzeilen: {'✅' if has_data_rows else '❌'}")
                    print(f"   HTML Länge: {len(container_html)} Zeichen")
                    
                    if has_data_rows:
                        # Zähle Datenzeilen
                        rows = await stats_container.query_selector_all('tbody tr')
                        print(f"   Anzahl Datenzeilen: {len(rows)}")
                        
                        # Zeige erste Zeile als Beispiel
                        if len(rows) > 0:
                            first_row_text = await rows[0].inner_text()
                            print(f"   Erste Zeile: {first_row_text[:100]}...")
                    
                else:
                    print("\n3. ❌ Statistics Container nicht gefunden")
            
            else:
                print("❌ 'Statistiken laden' Button nicht gefunden")
            
            # API-Aufrufe analysieren
            print(f"\n4. 🌐 Network-Analyse")
            api_calls = [req for req in network_requests if '/api/' in req]
            stats_calls = [req for req in api_calls if 'statistics' in req]
            
            print(f"   Gesamt API-Aufrufe: {len(api_calls)}")
            print(f"   Statistics API-Aufrufe: {len(stats_calls)}")
            
            for call in stats_calls:
                print(f"   📡 {call}")
            
            # Console Logs
            print(f"\n5. 📋 Console Logs ({len(console_logs)} entries)")
            error_logs = [log for log in console_logs if log.startswith('ERROR:')]
            warning_logs = [log for log in console_logs if log.startswith('WARNING:')]
            success_logs = [log for log in console_logs if 'success' in log.lower() or '✅' in log]
            
            print(f"   Errors: {len(error_logs)}")
            print(f"   Warnings: {len(warning_logs)}")  
            print(f"   Success: {len(success_logs)}")
            
            for log in error_logs[-3:]:  # Letzte 3 Errors
                print(f"   ❌ {log}")
            
            for log in success_logs[-3:]:  # Letzte 3 Success
                print(f"   ✅ {log}")
            
            # FINAL VERDICT
            print(f"\n🎯 FINAL VERDICT:")
            successful_stats_calls = len([c for c in stats_calls if 'comprehensive' in c])
            has_successful_rendering = len(success_logs) > 0
            no_critical_errors = len(error_logs) == 0
            
            if successful_stats_calls > 0 and has_successful_rendering:
                print("   ✅ STATISTICS FIX ERFOLGREICH!")
                print("   ✅ API-Aufrufe funktionieren") 
                print("   ✅ Tabellen werden gerendert")
            elif successful_stats_calls > 0:
                print("   ⚠️ TEILWEISE ERFOLGREICH - API funktioniert, aber Rendering-Probleme")
            else:
                print("   ❌ FIX FEHLGESCHLAGEN - API-Aufrufe funktionieren nicht")
            
        except Exception as e:
            print(f"❌ Fehler während Test: {e}")
            await page.screenshot(path='final_test_error.png')
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_statistics_fix())