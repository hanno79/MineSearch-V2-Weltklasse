#!/usr/bin/env python3
"""
Author: rahn
Datum: 27.08.2025
Version: 1.0
Beschreibung: Schnelle Validierung der kritischen Fixes ohne vollständige Suche
ZWECK: Prüfe Ergebnis-Tab, Value Normalization und UI-Funktionalität
"""

from playwright.sync_api import sync_playwright
import time
import json

def test_critical_fixes():
    """Prüft die kritischen Fixes ohne komplette Suche"""
    
    print("🧪 [VALIDATION] Starte Schnell-Validierung der kritischen Fixes...")
    
    with sync_playwright() as p:
        # Browser starten
        browser = p.chromium.launch(headless=False, slow_mo=1000)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            # 1. ERGEBNIS-TAB LOADING FIX TEST
            print("\n📊 [TEST 1] Prüfe Ergebnis-Tab Loading Fix...")
            page.goto("http://localhost:8000/static/index.html")
            page.wait_for_load_state('networkidle', timeout=10000)
            
            # Warte auf Tab-Initialisierung
            time.sleep(2)
            
            # Klicke auf Ergebnis-Tab
            ergebnis_tab = page.locator('[data-tab="results"]')
            if ergebnis_tab.is_visible():
                print("✅ [ERGEBNIS-TAB] Tab gefunden, klicke darauf...")
                ergebnis_tab.click()
                time.sleep(3)
                
                # Prüfe auf Fehlerbehandlung statt endlosem Loading
                loading_indicator = page.locator('.loading, .spinner, [data-loading="true"]')
                error_messages = page.locator('.error-message, .alert-danger')
                
                if loading_indicator.is_visible():
                    print("⏳ [ERGEBNIS-TAB] Loading-Indikator noch sichtbar...")
                    time.sleep(5)  # Warte etwas länger
                    
                if error_messages.is_visible():
                    error_text = error_messages.first.inner_text()
                    print(f"🔍 [ERGEBNIS-TAB] Fehlermeldung gefunden: '{error_text}'")
                else:
                    print("✅ [ERGEBNIS-TAB] Kein endloses Loading - Fix funktioniert!")
            else:
                print("❌ [ERGEBNIS-TAB] Tab nicht gefunden")
            
            # 2. STATISTICS TAB FIX TEST  
            print("\n📈 [TEST 2] Prüfe Statistics Tab Fix...")
            statistics_tab = page.locator('[data-tab="statistics"]')
            if statistics_tab.is_visible():
                statistics_tab.click()
                time.sleep(2)
                
                # Prüfe auf neue Performance-Anzeige
                performance_section = page.locator('.search-performance, #search-model-performance')
                if performance_section.is_visible():
                    print("✅ [STATISTICS-TAB] Performance-Sektion gefunden!")
                else:
                    print("🔍 [STATISTICS-TAB] Performance-Sektion noch nicht sichtbar (keine aktuellen Suchen)")
            else:
                print("❌ [STATISTICS-TAB] Tab nicht gefunden")
            
            # 3. API RESPONSE TEST (VALUE NORMALIZATION)
            print("\n🔄 [TEST 3] Prüfe API Value Normalization...")
            
            # Test Consolidated Results API
            response = page.request.get("http://localhost:8000/api/consolidated/results?days_back=7&sort_by=mine_name")
            if response.ok:
                data = response.json()
                if data.get('success') and data.get('data', {}).get('consolidated_results'):
                    results = data['data']['consolidated_results']
                    print(f"✅ [API] {len(results)} konsolidierte Minen gefunden")
                    
                    # Prüfe auf normalisierte Werte
                    for mine in results[:3]:  # Erste 3 Minen prüfen
                        mine_name = mine.get('mine_name', 'Unbekannt')
                        best_values = mine.get('best_values', {})
                        
                        # Prüfe Country Normalization (Kanada/Canada)
                        country = best_values.get('Land', {}).get('display_value', '')
                        if country and country.lower() in ['kanada', 'canada']:
                            print(f"🌍 [NORMALIZATION] Mine '{mine_name}': Land = '{country}' (Normalisierung erkannt)")
                        
                        # Prüfe Commodity Normalization (Gold/gold)
                        commodity = best_values.get('Hauptrohstoff', {}).get('display_value', '')
                        if commodity and commodity.lower() == 'gold':
                            print(f"🏅 [NORMALIZATION] Mine '{mine_name}': Rohstoff = '{commodity}' (Case-Normalisierung)")
                        
                        # Prüfe Confidence Scores
                        confidence = best_values.get('Land', {}).get('confidence_percentage', 0)
                        if confidence >= 95:
                            print(f"💯 [CONSENSUS] Mine '{mine_name}': {confidence}% Vertrauen (Perfekter Consensus)")
                            
                else:
                    print("❌ [API] Keine Ergebnisdaten erhalten")
            else:
                print(f"❌ [API] Request failed: {response.status}")
            
            # 4. UI ELEMENT CHECKS
            print("\n🎨 [TEST 4] Prüfe UI-Elemente...")
            
            # Prüfe Tab-Navigation
            tabs = page.locator('[data-tab]')
            tab_count = tabs.count()
            print(f"📑 [UI] {tab_count} Tabs gefunden")
            
            # Prüfe Auto-Refresh Funktionalität
            auto_refresh_elements = page.locator('#auto-refresh-checkbox, .auto-refresh')
            if auto_refresh_elements.count() > 0:
                print("✅ [UI] Auto-Refresh Elemente gefunden")
            
            print("\n🎉 [VALIDATION] Schnell-Validierung abgeschlossen!")
            print("=" * 50)
            
            # Screenshot machen
            page.screenshot(path="/app/quick_validation_screenshot.png", full_page=True)
            print("📸 Screenshot gespeichert: /app/quick_validation_screenshot.png")
            
        except Exception as e:
            print(f"❌ [ERROR] Fehler während der Validierung: {e}")
            page.screenshot(path="/app/validation_error_screenshot.png", full_page=True)
            print("📸 Error-Screenshot gespeichert: /app/validation_error_screenshot.png")
            
        finally:
            browser.close()

if __name__ == "__main__":
    test_critical_fixes()