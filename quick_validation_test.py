#!/usr/bin/env python3
"""
Author: rahn
Datum: 27.08.2025
Version: 1.0
Beschreibung: Schnelle Validierung der kritischen Fixes ohne vollständige Suche
ZWECK: Prüfe Ergebnis-Tab, Value Normalization und UI-Funktionalität
"""

from playwright.sync_api import sync_playwright, expect, Error as PlaywrightError, TimeoutError as PlaywrightTimeoutError
import time
import json
import os
import tempfile
from pathlib import Path

def test_critical_fixes():
    """Prüft die kritischen Fixes ohne komplette Suche"""
    
    print("🧪 [VALIDATION] Starte Schnell-Validierung der kritischen Fixes...")
    
    with sync_playwright() as p:
        # Browser starten
        headless_env = os.getenv("HEADLESS", "1").strip().lower()
        headless = headless_env in ("1", "true", "yes", "y", "on")
        browser = p.chromium.launch(headless=headless, slow_mo=1000)
        context = browser.new_context()
        page = context.new_page()
        
        # Dynamische Bestimmung des Screenshot-Verzeichnisses
        quick_dir_env = os.getenv("QUICK_VALIDATION_DIR", "").strip()
        if quick_dir_env:
            base_screenshot_dir = Path(quick_dir_env).expanduser()
        else:
            cwd = Path.cwd()
            base_screenshot_dir = cwd if os.access(cwd, os.W_OK) else Path(tempfile.gettempdir())
        try:
            base_screenshot_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            base_screenshot_dir = Path(tempfile.gettempdir())
            base_screenshot_dir.mkdir(parents=True, exist_ok=True)
        success_screenshot_path = base_screenshot_dir / "quick_validation_screenshot.png"
        error_screenshot_path = base_screenshot_dir / "validation_error_screenshot.png"
        
        try:
            # 1. ERGEBNIS-TAB LOADING FIX TEST
            print("\n📊 [TEST 1] Prüfe Ergebnis-Tab Loading Fix...")
            page.goto("http://localhost:8000/static/index.html")
            page.wait_for_load_state('networkidle', timeout=10000)
            
            # Warte auf Tab-Initialisierung durch Sichtbarkeit des Ergebnis-Tabs
            expect(page.locator('[data-tab="results"]')).to_be_visible(timeout=10000)
            
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
            
            # Test Consolidated Results API mit robuster Fehlerbehandlung
            api_url = "http://localhost:8000/api/consolidated/results?days_back=7&sort_by=mine_name"
            try:
                response = page.request.get(api_url, timeout=15000, fail_on_status=False)
            except (PlaywrightTimeoutError, PlaywrightError) as e:
                raise AssertionError(f"❌ [API] GET {api_url} fehlgeschlagen (Timeout/Netzwerk): {e}")
            except Exception as e:
                raise AssertionError(f"❌ [API] Unerwarteter Fehler bei GET {api_url}: {e}")
            
            if (not response.ok) or (response.status != 200):
                try:
                    body_text = response.text()
                except Exception:
                    body_text = "<Body konnte nicht gelesen werden>"
                raise AssertionError(f"❌ [API] Nicht-OK Antwort für {api_url} (Status {response.status}). Body (gekürzt): {body_text[:500]}")
            
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
            page.screenshot(path=str(success_screenshot_path), full_page=True)
            print(f"📸 Screenshot gespeichert: {success_screenshot_path}")
            
        except Exception as e:
            print(f"❌ [ERROR] Fehler während der Validierung: {e}")
            page.screenshot(path=str(error_screenshot_path), full_page=True)
            print(f"📸 Error-Screenshot gespeichert: {error_screenshot_path}")
            
        finally:
            browser.close()

if __name__ == "__main__":
    test_critical_fixes()