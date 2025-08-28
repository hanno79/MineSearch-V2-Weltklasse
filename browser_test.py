#!/usr/bin/env python3
"""
Author: rahn
Datum: 22.08.2025
Version: 1.0
Beschreibung: Einfacher Browser-Test für MineSearch
"""

from playwright.sync_api import sync_playwright
import time
import sys

def test_minesearch_ui():
    """Testet die MineSearch UI im Browser"""
    print("🚀 Starte Browser-Test für MineSearch...")
    
    with sync_playwright() as p:
        # Allocate browser variable outside try block
        browser = None
        try:
            # Browser starten
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # 1. Seite laden
            print("📄 Lade MineSearch Hauptseite...")
            page.goto("http://localhost:8000")
            page.wait_for_load_state('networkidle')
            
            # 2. Titel prüfen
            title = page.title()
            print(f"📋 Seitentitel: {title}")
            assert "MineSearch" in title, f"Titel sollte MineSearch enthalten, ist aber: {title}"
            
            # 3. Header prüfen
            header = page.locator('h1').first
            if header.is_visible():
                header_text = header.text_content()
                print(f"🏷️  Header-Text: {header_text}")
            
            # 4. Navigation-Tabs prüfen
            print("🔍 Prüfe Navigation-Tabs...")
            search_tab = page.locator('a[href="#search-tab"]')
            if search_tab.is_visible():
                print("✅ Search-Tab gefunden")
            else:
                print("⚠️  Search-Tab nicht sichtbar")
            
            batch_tab = page.locator('a[href="#batch-tab"]')
            if batch_tab.is_visible():
                print("✅ Batch-Tab gefunden")
            else:
                print("⚠️  Batch-Tab nicht sichtbar")
            
            results_tab = page.locator('a[href="#results-tab"]')
            if results_tab.is_visible():
                print("✅ Results-Tab gefunden")
            else:
                print("⚠️  Results-Tab nicht sichtbar")
            
            # 5. JavaScript-Fehler prüfen
            errors = []
            def handle_console(msg):
                if msg.type == 'error':
                    errors.append(msg.text)
            
            page.on('console', handle_console)
            time.sleep(2)  # Warte auf potentielle JS-Fehler
            
            if errors:
                print(f"❌ JavaScript-Fehler gefunden: {len(errors)}")
                for error in errors[:3]:  # Zeige nur erste 3
                    print(f"   • {error}")
            else:
                print("✅ Keine JavaScript-Fehler gefunden")
            
            # 6. Suchfeld prüfen
            search_input = page.locator('input[placeholder*="mine"], input[id*="mine"]')
            if search_input.is_visible():
                print("✅ Suchfeld gefunden")
                
                # Testsuche durchführen
                print("🔬 Führe Testsuche durch...")
                search_input.fill("Test Mine")
                
                # Suche-Button finden und klicken
                search_btn = page.locator('button:has-text("Suche starten"), button:has-text("Search")')
                if search_btn.is_visible():
                    search_btn.click()
                    print("✅ Suchvorgang gestartet")
                    time.sleep(3)  # Warte auf Antwort
                else:
                    print("⚠️  Such-Button nicht gefunden")
            else:
                print("⚠️  Suchfeld nicht gefunden")
            
            # Screenshot für Debugging
            page.screenshot(path="/app/minesearch_test_screenshot.png")
            print("📸 Screenshot gespeichert: minesearch_test_screenshot.png")
            
            print("\n🎉 Browser-Test erfolgreich abgeschlossen!")
            return True
            
        except Exception as e:
            print(f"❌ Browser-Test fehlgeschlagen: {str(e)}")
            return False
        finally:
            # Ensure browser is always closed if it was created
            if browser:
                browser.close()

if __name__ == "__main__":
    success = test_minesearch_ui()
    sys.exit(0 if success else 1)