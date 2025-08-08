"""
Author: rahn
Datum: 07.08.2025
Version: 1.0
Beschreibung: Detaillierte Browser-Analyse des Statistik-Tab Problems
"""

import asyncio
from playwright.async_api import async_playwright
import json
import time
from datetime import datetime

async def detailed_statistics_analysis():
    """Führt eine detaillierte Analyse des Statistik-Tab Problems durch"""
    
    async with async_playwright() as p:
        # Browser starten mit erweiterten Debug-Optionen
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=1000,  # Langsamer für bessere Beobachtung
            args=['--disable-web-security', '--disable-features=VizDisplayCompositor']
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        
        # Console und Network Events sammeln
        console_logs = []
        network_requests = []
        
        page = await context.new_page()
        
        # Event Listener für Console
        page.on('console', lambda msg: console_logs.append({
            'timestamp': datetime.now().isoformat(),
            'type': msg.type,
            'text': msg.text,
            'location': msg.location
        }))
        
        # Event Listener für Network Requests
        page.on('request', lambda request: network_requests.append({
            'timestamp': datetime.now().isoformat(),
            'method': request.method,
            'url': request.url,
            'headers': dict(request.headers) if request.headers else {},
            'type': 'request'
        }))
        
        page.on('response', lambda response: network_requests.append({
            'timestamp': datetime.now().isoformat(),
            'status': response.status,
            'url': response.url,
            'headers': dict(response.headers) if response.headers else {},
            'type': 'response'
        }))
        
        try:
            print("🔍 SCHRITT 1: Navigation zu http://localhost:8000")
            await page.goto('http://localhost:8000', wait_until='networkidle')
            await page.wait_for_timeout(2000)
            
            # Screenshot der Hauptseite
            await page.screenshot(path='debug_stats_01_main_page.png')
            print("📸 Screenshot: debug_stats_01_main_page.png")
            
            print("\n🔍 SCHRITT 2: Klick auf Statistiken Tab")
            # Suche nach dem Statistiken Tab
            stats_tab = await page.query_selector('button[onclick="switchTab(\'statistics\')"]')
            if not stats_tab:
                stats_tab = await page.query_selector('button:has-text("Suchstatistiken")')
            
            if stats_tab:
                print("✅ Statistiken Tab gefunden")
                await stats_tab.click()
                print("✅ Statistiken Tab geklickt")
            else:
                print("❌ Statistiken Tab NICHT gefunden!")
                # Alle verfügbaren Tabs auflisten
                all_buttons = await page.query_selector_all('button')
                print(f"Verfügbare Buttons: {len(all_buttons)}")
                for i, btn in enumerate(all_buttons):
                    text = await btn.inner_text()
                    onclick = await btn.get_attribute('onclick')
                    print(f"  Button {i}: '{text}' onclick='{onclick}'")
            
            print("\n🔍 SCHRITT 3: Warte 3 Sekunden für Tab-Ladung")
            await page.wait_for_timeout(3000)
            
            # Screenshot nach Tab-Wechsel
            await page.screenshot(path='debug_stats_02_statistics_tab.png')
            print("📸 Screenshot: debug_stats_02_statistics_tab.png")
            
            print("\n🔍 SCHRITT 4: DOM-Inspektion des Statistik-Containers")
            # Prüfe ob der Statistics Container sichtbar ist
            stats_container = await page.query_selector('#statistics')
            if stats_container:
                is_visible = await stats_container.is_visible()
                display_style = await stats_container.evaluate('el => getComputedStyle(el).display')
                innerHTML = await stats_container.inner_html()
                print(f"✅ Statistics Container gefunden")
                print(f"   Sichtbar: {is_visible}")
                print(f"   Display Style: {display_style}")
                print(f"   HTML Länge: {len(innerHTML)} Zeichen")
            else:
                print("❌ Statistics Container NICHT gefunden!")
            
            print("\n🔍 SCHRITT 5: Suche nach Filter-Button")
            filter_button = await page.query_selector('button:has-text("Filter anwenden")')
            if not filter_button:
                filter_button = await page.query_selector('button[onclick*="filter"]')
            
            if filter_button:
                print("✅ Filter-Button gefunden")
                button_text = await filter_button.inner_text()
                onclick_attr = await filter_button.get_attribute('onclick')
                is_visible = await filter_button.is_visible()
                print(f"   Text: '{button_text}'")
                print(f"   onclick: '{onclick_attr}'")
                print(f"   Sichtbar: {is_visible}")
                
                if is_visible:
                    print("\n🔍 SCHRITT 6: Klick auf Filter-Button")
                    await filter_button.click()
                    print("✅ Filter-Button geklickt")
                    
                    print("⏱️ Warte 10 Sekunden und beobachte...")
                    await page.wait_for_timeout(10000)
                    
                    # Screenshot nach Filter-Klick
                    await page.screenshot(path='debug_stats_03_after_filter.png')
                    print("📸 Screenshot: debug_stats_03_after_filter.png")
            else:
                print("❌ Filter-Button NICHT gefunden!")
            
            print("\n🔍 SCHRITT 7: Suche nach Statistiken-Laden-Button")
            load_stats_button = await page.query_selector('button:has-text("Statistiken laden")')
            if not load_stats_button:
                load_stats_button = await page.query_selector('button[onclick*="loadStatistics"]')
                if not load_stats_button:
                    load_stats_button = await page.query_selector('button[onclick*="statistics"]')
            
            if load_stats_button:
                print("✅ Statistiken-Laden-Button gefunden")
                button_text = await load_stats_button.inner_text()
                onclick_attr = await load_stats_button.get_attribute('onclick')
                is_visible = await load_stats_button.is_visible()
                print(f"   Text: '{button_text}'")
                print(f"   onclick: '{onclick_attr}'")
                print(f"   Sichtbar: {is_visible}")
                
                if is_visible:
                    print("\n🔍 SCHRITT 8: Klick auf Statistiken-Laden-Button")
                    await load_stats_button.click()
                    print("✅ Statistiken-Laden-Button geklickt")
                    
                    print("⏱️ Warte 10 Sekunden und beobachte...")
                    await page.wait_for_timeout(10000)
                    
                    # Screenshot nach Statistiken-Laden-Klick
                    await page.screenshot(path='debug_stats_04_after_load.png')
                    print("📸 Screenshot: debug_stats_04_after_load.png")
            else:
                print("❌ Statistiken-Laden-Button NICHT gefunden!")
            
            print("\n🔍 SCHRITT 9: DOM-Inspektion nach Button-Klicks")
            # Prüfe alle statistik-relevanten Elemente
            stats_table = await page.query_selector('table')
            if stats_table:
                table_html = await stats_table.inner_html()
                is_visible = await stats_table.is_visible()
                print(f"✅ Tabelle gefunden - Sichtbar: {is_visible}, HTML Länge: {len(table_html)}")
            else:
                print("❌ Keine Tabelle gefunden")
            
            # Prüfe auf Spinner/Loading-Indikatoren
            spinners = await page.query_selector_all('.spinner, .loading, [class*="load"]')
            print(f"🔄 Loading-Indikatoren gefunden: {len(spinners)}")
            
            print("\n🔍 SCHRITT 10: Alle Button-Event-Handler prüfen")
            buttons_in_stats = await page.query_selector_all('#statistics button')
            print(f"📊 Buttons im Statistics Container: {len(buttons_in_stats)}")
            
            for i, btn in enumerate(buttons_in_stats):
                text = await btn.inner_text()
                onclick = await btn.get_attribute('onclick')
                is_visible = await btn.is_visible()
                print(f"  Button {i+1}: '{text}' onclick='{onclick}' sichtbar={is_visible}")
            
            print("\n🔍 FINAL: Analyse-Ergebnisse")
            
            # Finale DOM-Struktur analysieren
            final_stats_html = await page.query_selector('#statistics')
            if final_stats_html:
                final_html = await final_stats_html.inner_html()
                with open('debug_stats_final_html.html', 'w', encoding='utf-8') as f:
                    f.write(final_html)
                print("💾 Finale HTML Struktur gespeichert: debug_stats_final_html.html")
            
            # Analysiere Console Logs
            print(f"\n📋 Console Logs: {len(console_logs)} Einträge")
            for log in console_logs[-10:]:  # Letzte 10 Logs
                print(f"   {log['type'].upper()}: {log['text']}")
            
            # Analysiere Network Requests
            print(f"\n🌐 Network Requests: {len(network_requests)} Einträge")
            api_calls = [req for req in network_requests if '/api/' in req.get('url', '')]
            print(f"   API-Aufrufe: {len(api_calls)}")
            
            for api_call in api_calls[-5:]:  # Letzte 5 API-Aufrufe
                print(f"   {api_call.get('method', 'GET')} {api_call['url']} - Status: {api_call.get('status', 'N/A')}")
            
            # Detaillierte Analyse speichern
            analysis_report = {
                'timestamp': datetime.now().isoformat(),
                'console_logs': console_logs,
                'network_requests': network_requests,
                'api_calls': api_calls,
                'screenshots_taken': [
                    'debug_stats_01_main_page.png',
                    'debug_stats_02_statistics_tab.png', 
                    'debug_stats_03_after_filter.png',
                    'debug_stats_04_after_load.png'
                ]
            }
            
            with open('debug_statistics_detailed_analysis_report.json', 'w', encoding='utf-8') as f:
                json.dump(analysis_report, f, indent=2, ensure_ascii=False)
            
            print("\n✅ Detaillierte Analyse abgeschlossen!")
            print("📊 Report gespeichert: debug_statistics_detailed_analysis_report.json")
            
        except Exception as e:
            print(f"❌ Fehler während der Analyse: {e}")
            # Notfall-Screenshot
            await page.screenshot(path='debug_stats_error.png')
            
        finally:
            await browser.close()

if __name__ == "__main__":
    print("🎯 STARTE DETAILLIERTE STATISTIK-TAB ANALYSE")
    print("=" * 50)
    asyncio.run(detailed_statistics_analysis())