#!/usr/bin/env python3
"""
Author: rahn  
Datum: 02.08.2025
Version: 1.0
Beschreibung: Debug Frontend Tabs - Prüft verfügbare Tabs und Inhalte
"""

import asyncio
from playwright.async_api import async_playwright

async def debug_frontend():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            print("🔍 Debug Frontend Tabs")
            
            # Lade Frontend
            await page.goto("http://localhost:8000")
            await page.wait_for_load_state("networkidle")
            
            # Screenshot der Startseite
            await page.screenshot(path="/app/minesearch_v2/backend/debug_start.png")
            print("📸 Startseite Screenshot gespeichert")
            
            # Finde alle Tab-Labels
            tab_labels = await page.query_selector_all('.tab-navigation label')
            print(f"\n📋 Verfügbare Tabs: {len(tab_labels)}")
            
            for i, label in enumerate(tab_labels):
                tab_text = await label.text_content()
                print(f"   {i+1}. {tab_text}")
            
            # Prüfe Statistiken-Tab
            print("\n📊 Teste Statistiken-Tab...")
            stats_radio = await page.query_selector('input[value="statistics"]')
            if stats_radio:
                await stats_radio.click()
                await page.wait_for_timeout(1000)
                
                # Screenshot nach Tab-Wechsel
                await page.screenshot(path="/app/minesearch_v2/backend/debug_statistics_tab.png")
                print("📸 Statistiken-Tab Screenshot gespeichert")
                
                # Prüfe ob Load-Button sichtbar ist
                load_button = await page.query_selector('#load-statistics-btn')
                if load_button:
                    print("✅ Load-Statistics Button gefunden")
                    
                    # Klicke auf Load-Button
                    await load_button.click()
                    print("🖱️ Load-Button geklickt")
                    
                    # Warte kurz und prüfe Response
                    await page.wait_for_timeout(3000)
                    
                    # Prüfe ob Tabelle erscheint
                    table = await page.query_selector('#enhanced-statistics-table')
                    if table:
                        print("✅ Statistiken-Tabelle gefunden")
                        
                        # Prüfe Tabelleninhalt
                        rows = await page.query_selector_all('#enhanced-statistics-table tbody tr')
                        print(f"📊 Tabellenzeilen: {len(rows)}")
                        
                        if len(rows) > 0:
                            # Prüfe Details-Buttons
                            details_buttons = await page.query_selector_all('button[onclick*="showDetails"]')
                            print(f"🔍 Details-Buttons: {len(details_buttons)}")
                            
                            if len(details_buttons) > 0:
                                # Teste ersten Details-Button
                                print("\n🎯 Teste ersten Details-Button...")
                                await details_buttons[0].click()
                                await page.wait_for_timeout(2000)
                                
                                # Prüfe ob Modal erscheint
                                modal = await page.query_selector('#detailsModal')
                                if modal:
                                    is_visible = await modal.is_visible()
                                    print(f"📋 Modal sichtbar: {is_visible}")
                                    
                                    if is_visible:
                                        # Screenshot des Modals
                                        await page.screenshot(path="/app/minesearch_v2/backend/debug_modal.png")
                                        print("📸 Modal Screenshot gespeichert")
                                        
                                        # Modal-Inhalt extrahieren
                                        modal_content = await page.text_content('#detailsModal .modal-body')
                                        print(f"📝 Modal-Inhalt Länge: {len(modal_content)} Zeichen")
                                        print(f"📄 Modal-Inhalt Vorschau: {modal_content[:200]}...")
                                    else:
                                        print("❌ Modal nicht sichtbar")
                                else:
                                    print("❌ Modal nicht gefunden")
                            else:
                                print("❌ Keine Details-Buttons gefunden")
                        else:
                            print("❌ Keine Tabellenzeilen gefunden")
                    else:
                        print("❌ Statistiken-Tabelle nicht gefunden")
                        
                        # Prüfe ob ein Ladezustand angezeigt wird
                        loading = await page.query_selector('.loading, .spinner, #loading')
                        if loading:
                            print("⏳ Loading-Indikator gefunden")
                else:
                    print("❌ Load-Statistics Button nicht gefunden")
            else:
                print("❌ Statistiken-Tab nicht gefunden")
                
            # Zusätzliche Zeit für Beobachtung
            await page.wait_for_timeout(5000)
            
        except Exception as e:
            print(f"❌ Fehler: {e}")
            await page.screenshot(path="/app/minesearch_v2/backend/debug_error.png")
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_frontend())