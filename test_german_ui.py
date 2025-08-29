#!/usr/bin/env python3
"""
Author: rahn
Datum: 27.08.2025
Version: 1.0
Beschreibung: Test der deutschen UI-Übersetzungen
ZWECK: Prüfe ob alle englischen Begriffe korrekt übersetzt wurden
"""

from playwright.sync_api import sync_playwright
import time
import os

def test_german_ui():
    """Testet die deutsche UI nach den Übersetzungen"""
    
    print("🧪 [UI-TEST] Teste deutsche Übersetzungen...")
    
    # Konfiguration: Headless/SLOW_MO via Umgebungsvariablen
    # - In CI standardmäßig headless (schnell) und ohne Slow-Mo
    # - Lokal kann per HEADLESS und SLOW_MO überschrieben werden
    is_ci = any([
        os.getenv("CI"),
        os.getenv("GITHUB_ACTIONS"),
        os.getenv("GITLAB_CI"),
        os.getenv("BUILD_NUMBER"),
    ])
    headless_env = os.getenv("HEADLESS")
    if headless_env is None:
        headless = True if is_ci else False
    else:
        headless = headless_env.strip().lower() in ("1", "true", "yes", "on")

    slow_mo_env = os.getenv("SLOW_MO")
    try:
        slow_mo = int(slow_mo_env) if slow_mo_env is not None else 0
    except (TypeError, ValueError):
        slow_mo = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, slow_mo=slow_mo)
        context = browser.new_context()
        page = context.new_page()
        
        # Verwende relative Pfade für Screenshots (kein hartkodiertes /app/)
        screenshot_path = "./german_ui_test.png"
        error_screenshot_path = "./german_ui_error.png"
        
        try:
            # Lade die Seite
            page.goto("http://localhost:8000/static/index.html")
            page.wait_for_load_state('networkidle', timeout=15000)
            
            # Führe eine einfache Suche durch um Multi-Model Results zu bekommen
            print("🔍 [TEST] Starte Beispielsuche für UI-Test...")
            
            # Gehe zur Einzelsuche
            einzelsuche_tab = page.locator('[data-tab="single"]')
            if einzelsuche_tab.is_visible():
                einzelsuche_tab.click()
                time.sleep(1)
                
                # Eingabe: Eleonore
                mine_input = page.locator('input[name="mine_name"]')
                if mine_input.is_visible():
                    mine_input.fill("Eleonore")
                    time.sleep(0.5)
                    
                    # Wähle 3 schnelle Modelle aus
                    model_checkboxes = page.locator('input[name="models"]')
                    num_to_check = min(3, model_checkboxes.count())
                    for i in range(num_to_check):
                        model_checkboxes.nth(i).check()
                    
                    # Starte Suche
                    search_button = page.locator('button:has-text("🔍 Suchen")')
                    if search_button.is_visible():
                        print("🚀 [TEST] Starte Suche und warte 30 Sekunden...")
                        search_button.click()
                        
                        # Warte auf Ergebnisse (30 Sekunden)
                        time.sleep(30)
                        
                        # Prüfe deutsche Begriffe in den Ergebnissen
                        german_terms_to_check = [
                            "Multi-Modell Analyseergebnisse",
                            "Modell-Vergleichsanalyse", 
                            "Starker Konsens",
                            "Schwacher Konsens",
                            "Feld-für-Feld Analyse",
                            "Konsens-Daten exportieren",
                            "Einzelne Modell-Ergebnisse",
                            "Datenqualität",
                            "Diskrepanzen",
                            "Signifikante Diskrepanzen"
                        ]
                        
                        print("\n📋 [VALIDATION] Prüfe deutsche Begriffe:")
                        found_terms = []
                        
                        for term in german_terms_to_check:
                            elements = page.locator(f':has-text("{term}")')
                            if elements.count() > 0:
                                found_terms.append(term)
                                print(f"✅ '{term}' gefunden")
                            else:
                                print(f"❌ '{term}' NICHT gefunden")
                        
                        # Prüfe auf englische Begriffe (sollten NICHT mehr vorhanden sein)
                        english_terms_to_avoid = [
                            "Multi-Model Analysis Results",
                            "Model Comparison Analysis",
                            "Strong Consensus", 
                            "Weak Consensus",
                            "Field-by-Field Analysis",
                            "Export Consensus Data",
                            "Individual Model Results",
                            "Data Quality",
                            "Discrepancies",
                            "Significant Discrepancies"
                        ]
                        
                        print("\n🚫 [VALIDATION] Prüfe auf verbleibende englische Begriffe:")
                        remaining_english = []
                        
                        for term in english_terms_to_avoid:
                            elements = page.locator(f':has-text("{term}")')
                            if elements.count() > 0:
                                remaining_english.append(term)
                                print(f"❌ '{term}' noch vorhanden (FEHLER)")
                            else:
                                print(f"✅ '{term}' erfolgreich entfernt")
                        
                        # Ergebnis-Zusammenfassung
                        print(f"\n📊 [ZUSAMMENFASSUNG]")
                        print(f"✅ Deutsche Begriffe gefunden: {len(found_terms)}/{len(german_terms_to_check)}")
                        print(f"❌ Englische Begriffe übrig: {len(remaining_english)}/{len(english_terms_to_avoid)}")
                        
                        if len(found_terms) >= 5 and len(remaining_english) == 0:
                            print("🎉 [SUCCESS] UI erfolgreich auf Deutsch übersetzt!")
                        else:
                            print("⚠️ [PARTIAL] Teilweise Übersetzung - weitere Arbeit nötig")
                    
                    else:
                        print("❌ Such-Button nicht gefunden")
                else:
                    print("❌ Mine-Name Input nicht gefunden")
            else:
                print("❌ Einzelsuche Tab nicht gefunden")
            
            # Screenshot für Validierung
            page.screenshot(path=screenshot_path, full_page=True)
            print(f"📸 Screenshot gespeichert: {screenshot_path}")
            
        except Exception as e:
            print(f"❌ [ERROR] Fehler beim UI-Test: {e}")
            page.screenshot(path=error_screenshot_path)
            print(f"📸 Fehler-Screenshot gespeichert: {error_screenshot_path}")
            
        finally:
            browser.close()

if __name__ == "__main__":
    test_german_ui()