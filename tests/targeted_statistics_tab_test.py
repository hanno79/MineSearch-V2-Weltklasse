#!/usr/bin/env python3
"""
Author: rahn  
Datum: 19.08.2025
Version: 1.0
Beschreibung: Gezielter Statistics Tab Test - Fokussiert auf Navigation und Modell-Validierung
"""

import asyncio
import json
from playwright.async_api import async_playwright
import time

async def test_statistics_tab_targeted():
    """
    Gezielter Test der Statistics-Tab:
    1. Korrekte Navigation zur Statistics-Tab
    2. Warten auf Daten-Laden  
    3. Validierung der Modell-Anzahl
    4. Status und Performance-Scores prüfen
    """
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=1500)
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()
        
        print("🎯 Starte Gezielten Statistics Tab Test...")
        
        try:
            # 1. Zur Hauptseite navigieren
            print("\n📍 SCHRITT 1: Navigation zur Hauptseite")
            await page.goto("http://localhost:3000")
            await page.wait_for_load_state('networkidle')
            
            # Screenshot der Hauptseite
            await page.screenshot(path="/app/tests/targeted_test_01_homepage.png")
            print("✅ Hauptseite geladen und Screenshot gespeichert")
            
            # 2. Explizit auf Statistics Tab klicken
            print("\n📍 SCHRITT 2: Gezielter Klick auf Statistics Tab")
            
            # Verschiedene Selektoren für Statistics Tab versuchen
            statistics_selectors = [
                'a[href="#statistiken"]',
                'a:has-text("Statistiken")',
                '.nav-link:has-text("Statistiken")',
                'button:has-text("Statistiken")',
                '[data-tab="statistiken"]',
                '#statistiken-tab'
            ]
            
            clicked = False
            for selector in statistics_selectors:
                try:
                    element = page.locator(selector).first
                    if await element.count() > 0:
                        print(f"📍 Gefunden: {selector}")
                        await element.click()
                        clicked = True
                        break
                except:
                    continue
            
            if not clicked:
                print("⚠️ Kein Statistics Tab gefunden - versuche URL-Navigation")
                await page.goto("http://localhost:3000#statistiken")
            
            print("✅ Statistics Tab Navigation ausgeführt")
            
            # 3. Warten auf Tab-Content
            print("\n📍 SCHRITT 3: Warten auf Statistics Content")
            await page.wait_for_timeout(3000)  # 3 Sekunden warten
            
            # Screenshot nach Tab-Klick
            await page.screenshot(path="/app/tests/targeted_test_02_after_tab_click.png")
            print("📸 Screenshot nach Tab-Navigation gespeichert")
            
            # 4. Statistics Container suchen
            print("\n📍 SCHRITT 4: Statistics Container Lokalisierung")
            
            # Warten auf Statistics-spezifische Inhalte
            statistics_indicators = [
                '[id*="statistic"]',
                '[class*="statistic"]', 
                'text=Modell',
                'text=Performance',
                'text=Getestet',
                'text=Verfügbar'
            ]
            
            for indicator in statistics_indicators:
                try:
                    await page.wait_for_selector(indicator, timeout=5000)
                    print(f"✅ Statistics Indikator gefunden: {indicator}")
                    break
                except:
                    continue
            
            # 5. Seiteninhalt analysieren
            print("\n📍 SCHRITT 5: Detaillierte Content-Analyse")
            
            # HTML Content extrahieren
            page_html = await page.content()
            
            # Nach verschiedenen Modell-Patterns suchen
            model_patterns = [
                "gpt-", "claude-", "gemini-", "llama", "mistral", 
                "openai", "anthropic", "perplexity", "brightdata", "tavily"
            ]
            
            found_models = []
            for pattern in model_patterns:
                if pattern in page_html.lower():
                    found_models.append(pattern)
            
            print(f"📊 Gefundene Modell-Patterns: {len(found_models)}")
            print(f"🔍 Patterns: {found_models}")
            
            # 6. Tabellen-Zeilen zählen
            print("\n📍 SCHRITT 6: Tabellen-Struktur Analyse")
            
            # Verschiedene Table-Selektoren
            table_selectors = [
                'table tr',
                '.table-row', 
                '.model-row',
                '[data-model]',
                'tbody tr',
                '.statistics-row'
            ]
            
            max_rows = 0
            best_selector = None
            
            for selector in table_selectors:
                count = await page.locator(selector).count()
                if count > max_rows:
                    max_rows = count
                    best_selector = selector
                print(f"🔢 {selector}: {count} Zeilen")
            
            print(f"📊 Maximale Zeilen: {max_rows} mit Selektor: {best_selector}")
            
            # 7. Text-basierte Modell-Suche
            print("\n📍 SCHRITT 7: Text-basierte Modell-Erkennung")
            
            # Alle Text-Inhalte der Seite analysieren
            all_text = await page.text_content('body')
            
            # Zähle spezifische Begriffe
            getestet_count = all_text.lower().count('getestet') if all_text else 0
            verfuegbar_count = all_text.lower().count('verfügbar') if all_text else 0
            modell_count = all_text.lower().count('modell') if all_text else 0
            
            print(f"📊 Text-Analyse:")
            print(f"   - 'getestet': {getestet_count} mal")
            print(f"   - 'verfügbar': {verfuegbar_count} mal") 
            print(f"   - 'modell': {modell_count} mal")
            
            # 8. Performance Score Suche
            print("\n📍 SCHRITT 8: Performance Score Analyse")
            
            # Suche nach numerischen Performance-Werten
            score_patterns = [
                r'0\.[1-9]',  # 0.1 bis 0.9
                r'[1-9]\.\d',  # 1.0 bis 9.9
                r'100%',       # Prozent-Werte
                r'\d+\.\d+%'   # Dezimal-Prozent
            ]
            
            scores_found = 0
            for pattern in score_patterns:
                matches = await page.locator(f'text=/{pattern}/').count()
                scores_found += matches
                if matches > 0:
                    print(f"✅ Score-Pattern '{pattern}': {matches} Treffer")
            
            print(f"📊 Gesamt Performance-Scores gefunden: {scores_found}")
            
            # 9. API Direct Test
            print("\n📍 SCHRITT 9: Direkter API Test")
            
            try:
                api_response = await page.evaluate("""
                    async () => {
                        try {
                            const response = await fetch('http://localhost:8000/api/models');
                            const data = await response.json();
                            return { success: true, count: Array.isArray(data) ? data.length : Object.keys(data).length, data: data };
                        } catch (error) {
                            return { success: false, error: error.message };
                        }
                    }
                """)
                
                if api_response['success']:
                    print(f"✅ API Erfolgreich: {api_response['count']} Modelle")
                else:
                    print(f"❌ API Fehler: {api_response['error']}")
                    
            except Exception as e:
                print(f"⚠️ API Test Exception: {e}")
            
            # Final Screenshot
            await page.screenshot(path="/app/tests/targeted_test_03_final_analysis.png")
            print("📸 Final Screenshot gespeichert")
            
            # 10. Zusammenfassung
            print("\n" + "="*70)
            print("🎯 GEZIELTER STATISTICS TAB TEST - ERGEBNIS")
            print("="*70)
            print(f"📊 Tabellen-Zeilen (max): {max_rows}")
            print(f"🔍 Modell-Patterns gefunden: {len(found_models)}")
            print(f"✅ 'Getestet' Vorkommen: {getestet_count}")
            print(f"⏳ 'Verfügbar' Vorkommen: {verfuegbar_count}")
            print(f"🎯 Performance-Scores: {scores_found}")
            print(f"📋 Bester Tabellen-Selektor: {best_selector}")
            
            # Bewertung
            success = max_rows >= 50 and len(found_models) >= 5
            if success:
                print("🎉 ERFOLG: Statistics Tab funktioniert korrekt!")
            else:
                print("⚠️ PROBLEM: Statistics Tab zeigt nicht genügend Daten")
            
            print("="*70)
            
            # Detaillierte Ergebnisse speichern
            detailed_results = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "navigation_successful": clicked,
                "max_table_rows": max_rows,
                "best_selector": best_selector,
                "model_patterns_found": found_models,
                "text_analysis": {
                    "getestet_count": getestet_count,
                    "verfuegbar_count": verfuegbar_count,
                    "modell_count": modell_count
                },
                "performance_scores_found": scores_found,
                "api_test": api_response if 'api_response' in locals() else None,
                "success": success,
                "recommendations": [
                    "Check if Statistics tab loads data dynamically",
                    "Verify API endpoint responses",
                    "Ensure proper JavaScript execution",
                    "Check for console errors during tab switch"
                ]
            }
            
            with open("/app/tests/targeted_statistics_results.json", "w", encoding="utf-8") as f:
                json.dump(detailed_results, f, indent=2, ensure_ascii=False)
            
            print("💾 Detaillierte Ergebnisse in targeted_statistics_results.json gespeichert")
            
        except Exception as e:
            print(f"❌ KRITISCHER FEHLER: {e}")
            await page.screenshot(path="/app/tests/targeted_test_error.png")
            print("📸 Error Screenshot gespeichert")
            
        finally:
            await browser.close()
            print("🏁 Test abgeschlossen")

if __name__ == "__main__":
    asyncio.run(test_statistics_tab_targeted())