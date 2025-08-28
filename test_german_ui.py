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

def test_german_ui():
    """Testet die deutsche UI nach den Übersetzungen"""
    
    print("🧪 [UI-TEST] Teste deutsche Übersetzungen...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=500)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            # Lade die Seite
            page.goto("http://localhost:8000/static/index.html")
            page.wait_for_load_state('networkidle', timeout=15000)
            
            # Führe eine einfache Suche durch um Multi-Model Results zu bekommen
            print("🔍 [TEST] Starte Beispielsuche für UI-Test...")
            
            # Gehe zur Einzelsuche
            einzelsuche_tab = page.locator('[data-tab="search"]')
            if einzelsuche_tab.is_visible():
                einzelsuche_tab.click()
                time.sleep(1)
                
                # Eingabe: Eleonore
                mine_input = page.locator('#mine-name')
                if mine_input.is_visible():
                    mine_input.fill("Eleonore")
                    time.sleep(0.5)
                    
                    # Wähle 3 schnelle Modelle aus
                    model_checkboxes = page.locator('input[type="checkbox"][id*="model"]')
                    for i in range(min(3, model_checkboxes.count())):
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
            page.screenshot(path="/app/german_ui_test.png", full_page=True)
            print("📸 Screenshot gespeichert: /app/german_ui_test.png")
            
        except Exception as e:
            print(f"❌ [ERROR] Fehler beim UI-Test: {e}")
            page.screenshot(path="/app/german_ui_error.png")
            
        finally:
            browser.close()

if __name__ == "__main__":
    test_german_ui()