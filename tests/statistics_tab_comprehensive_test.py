#!/usr/bin/env python3
"""
Author: rahn  
Datum: 19.08.2025
Version: 1.0
Beschreibung: Comprehensive Statistics Tab Test - Validiert Modell-Anzahl, Status und Performance Scores
"""

import asyncio
import json
from playwright.async_api import async_playwright
import time

async def test_statistics_tab_comprehensive():
    """
    Testet die Statistics-Tab vollumfänglich:
    1. Navigation zur Statistics-Tab
    2. Validierung der Modell-Anzahl (soll 55 sein)
    3. Überprüfung der Status-Indikatoren (Getestet vs Verfügbar)
    4. Validierung der Performance-Scores (nicht alle 0.0)
    5. Screenshots für Dokumentation
    """
    
    async with async_playwright() as p:
        # Browser starten
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()
        
        print("🚀 Starte Statistics Tab Comprehensive Test...")
        
        try:
            # 1. Zur Hauptseite navigieren
            print("\n📍 SCHRITT 1: Navigation zur Hauptseite")
            await page.goto("http://localhost:3000")
            await page.wait_for_load_state('networkidle')
            print("✅ Hauptseite geladen")
            
            # Screenshot der Hauptseite
            await page.screenshot(path="/app/tests/statistics_test_01_homepage.png")
            print("📸 Screenshot: Hauptseite gespeichert")
            
            # 2. Auf Statistics Tab klicken
            print("\n📍 SCHRITT 2: Klick auf Statistics Tab")
            statistics_tab = page.locator('a[href="#statistiken"], a[data-target="statistiken"], .nav-link:has-text("Statistiken")')
            
            if await statistics_tab.count() > 0:
                await statistics_tab.first.click()
                print("✅ Statistics Tab geklickt")
            else:
                # Alternative: Direkte Navigation
                await page.goto("http://localhost:3000#statistiken")
                print("✅ Direkte Navigation zu Statistics Tab")
            
            # Warten auf das Laden der Statistics
            await page.wait_for_timeout(3000)
            await page.wait_for_load_state('networkidle')
            
            # Screenshot nach Tab-Wechsel
            await page.screenshot(path="/app/tests/statistics_test_02_tab_loaded.png")
            print("📸 Screenshot: Statistics Tab geladen")
            
            # 3. Warten auf Statistik-Daten
            print("\n📍 SCHRITT 3: Warten auf Statistik-Daten")
            try:
                # Warten auf Statistics Container
                await page.wait_for_selector('[data-tab="statistiken"], .statistics-content, #statistiken', timeout=10000)
                print("✅ Statistics Container gefunden")
            except:
                print("⚠️ Statistics Container nicht gefunden - versuche alternative Selektoren")
            
            # 4. Modell-Anzahl zählen
            print("\n📍 SCHRITT 4: Modell-Anzahl Validierung")
            
            # Verschiedene Selektoren für Modell-Zeilen ausprobieren
            model_selectors = [
                '.model-row, tr.model-row',
                '.statistics-table tbody tr',
                '.model-item, .model-entry',
                '[data-model], [data-model-id]',
                '.table tbody tr',
                'tbody tr'
            ]
            
            total_models = 0
            found_selector = None
            
            for selector in model_selectors:
                model_count = await page.locator(selector).count()
                if model_count > 0:
                    total_models = model_count
                    found_selector = selector
                    print(f"✅ Gefunden mit Selektor '{selector}': {model_count} Modelle")
                    break
            
            if total_models == 0:
                print("⚠️ Keine Modell-Zeilen gefunden - prüfe Seiteninhalt")
                page_content = await page.content()
                print("📄 Seiteninhalt analysieren...")
                
                # Nach Statistik-relevanten Begriffen suchen
                if "modell" in page_content.lower() or "model" in page_content.lower():
                    print("✅ Statistik-Inhalte gefunden im HTML")
                else:
                    print("❌ Keine Statistik-Inhalte im HTML gefunden")
            
            # 5. Status-Indikatoren analysieren
            print("\n📍 SCHRITT 5: Status-Indikatoren Analyse")
            
            tested_models = 0
            available_models = 0
            
            status_selectors = [
                '.status-getestet, .tested, [data-status="tested"]',
                '.status-verfügbar, .available, [data-status="available"]',
                '.badge-success, .badge-primary',
                '.text-success, .text-primary'
            ]
            
            for selector in status_selectors:
                count = await page.locator(selector).count()
                if count > 0:
                    print(f"Status-Elemente gefunden: {selector} -> {count}")
            
            # Text-basierte Suche nach Status
            getestet_elements = await page.locator('text=/getestet/i').count()
            verfuegbar_elements = await page.locator('text=/verfügbar/i').count()
            
            print(f"📊 Status-Verteilung:")
            print(f"   - 'Getestet' gefunden: {getestet_elements} mal")
            print(f"   - 'Verfügbar' gefunden: {verfuegbar_elements} mal")
            
            # 6. Performance Scores analysieren
            print("\n📍 SCHRITT 6: Performance Scores Validierung")
            
            # Nach Performance-Score Elementen suchen
            score_selectors = [
                '.performance-score, .score',
                '[data-score], [data-performance]',
                '.metric-value, .score-value',
                'td:has-text("0."), td:has-text("1."), td:has-text("2.")'
            ]
            
            non_zero_scores = 0
            zero_scores = 0
            
            # Suche nach numerischen Werten > 0.0
            for i in range(1, 10):  # Suche nach Scores 0.1 bis 0.9
                score_pattern = f"0.{i}"
                score_elements = await page.locator(f'text=/{score_pattern}/').count()
                if score_elements > 0:
                    non_zero_scores += score_elements
                    print(f"✅ Non-Zero Scores gefunden: {score_pattern} -> {score_elements} mal")
            
            # Suche nach 0.0 Werten
            zero_elements = await page.locator('text=/0\.0/').count()
            if zero_elements > 0:
                zero_scores = zero_elements
                print(f"⚠️ Zero Scores gefunden: 0.0 -> {zero_elements} mal")
            
            # 7. Detaillierte Tabellen-Analyse
            print("\n📍 SCHRITT 7: Tabellen-Struktur Analyse")
            
            # Suche nach Tabellen-Headern
            headers = await page.locator('th, .table-header').all_text_contents()
            if headers:
                print(f"📋 Tabellen-Header gefunden: {headers}")
            
            # Screenshot nach Analyse
            await page.screenshot(path="/app/tests/statistics_test_03_analysis_complete.png")
            print("📸 Screenshot: Analyse abgeschlossen")
            
            # 8. API-Endpunkt direkt testen
            print("\n📍 SCHRITT 8: API-Endpunkt Validierung")
            
            try:
                # Models API aufrufen
                models_response = await page.evaluate("""
                    fetch('/api/models')
                        .then(response => response.json())
                        .catch(error => ({ error: error.message }))
                """)
                
                if isinstance(models_response, dict) and 'error' not in models_response:
                    print(f"✅ API Response erhalten: {len(models_response) if isinstance(models_response, list) else 'Object'}")
                else:
                    print(f"❌ API Error: {models_response}")
                    
            except Exception as e:
                print(f"⚠️ API Test fehlgeschlagen: {e}")
            
            # 9. Finales Ergebnis zusammenfassen
            print("\n" + "="*60)
            print("🎯 STATISTICS TAB TEST - ERGEBNISSE")
            print("="*60)
            print(f"📊 Gefundene Modelle: {total_models}")
            print(f"📋 Verwendeter Selektor: {found_selector}")
            print(f"✅ Getestete Modelle: {getestet_elements}")
            print(f"⏳ Verfügbare Modelle: {verfuegbar_elements}")
            print(f"🎯 Non-Zero Scores: {non_zero_scores}")
            print(f"0️⃣ Zero Scores: {zero_scores}")
            
            # Bewertung
            if total_models >= 50:
                print("🎉 ERFOLG: Modell-Anzahl ist ausreichend (>= 50)")
            elif total_models >= 25:
                print("⚠️ WARNUNG: Modell-Anzahl ist niedrig (< 50)")
            else:
                print("❌ FEHLER: Zu wenige Modelle gefunden (< 25)")
            
            if non_zero_scores > 0:
                print("✅ ERFOLG: Performance-Scores > 0.0 gefunden")
            else:
                print("❌ FEHLER: Alle Performance-Scores sind 0.0")
            
            print("="*60)
            
            # Final Screenshot
            await page.screenshot(path="/app/tests/statistics_test_04_final_result.png")
            print("📸 Final Screenshot gespeichert")
            
            # Test-Ergebnisse in JSON speichern
            test_results = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "total_models_found": total_models,
                "selector_used": found_selector,
                "tested_models": getestet_elements,
                "available_models": verfuegbar_elements,
                "non_zero_scores": non_zero_scores,
                "zero_scores": zero_scores,
                "table_headers": headers,
                "success": total_models >= 50 and non_zero_scores > 0
            }
            
            with open("/app/tests/statistics_test_results.json", "w", encoding="utf-8") as f:
                json.dump(test_results, f, indent=2, ensure_ascii=False)
            
            print("💾 Test-Ergebnisse in statistics_test_results.json gespeichert")
            
        except Exception as e:
            print(f"❌ FEHLER während Test: {e}")
            await page.screenshot(path="/app/tests/statistics_test_error.png")
            print("📸 Error Screenshot gespeichert")
            
        finally:
            await browser.close()
            print("🏁 Test abgeschlossen")

if __name__ == "__main__":
    asyncio.run(test_statistics_tab_comprehensive())