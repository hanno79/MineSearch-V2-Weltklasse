"""
Author: rahn
Datum: 19.08.2025
Version: 1.0
Beschreibung: Playwright Test für MineSearch Web Interface - Browser-Initialisierung und Screenshot
"""

import asyncio
from playwright.async_api import async_playwright
import os
from datetime import datetime

async def test_minesearch_interface():
    """
    Test der MineSearch Web Interface durch Browser-Initialisierung und Screenshot-Aufnahme
    """
    
    print("🚀 Starte Playwright Browser Test für MineSearch Interface...")
    
    async with async_playwright() as p:
        # Browser starten (Chromium für bessere Kompatibilität)
        browser = await p.chromium.launch(
            headless=False,  # Browser sichtbar für Debugging
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage'
            ]
        )
        
        # Neue Browser-Seite erstellen
        page = await browser.new_page()
        
        # Viewport setzen für konsistente Screenshots
        await page.set_viewport_size({"width": 1920, "height": 1080})
        
        try:
            print("📡 Navigiere zu MineSearch Interface: http://localhost:8000")
            
            # Zu MineSearch Interface navigieren
            response = await page.goto("http://localhost:8000", wait_until="networkidle")
            
            # Prüfen ob Seite erfolgreich geladen
            if response.status != 200:
                print(f"❌ FEHLER: HTTP Status {response.status}")
                return False
                
            print(f"✅ Seite erfolgreich geladen - Status: {response.status}")
            
            # Warten bis die Seite vollständig geladen ist
            await page.wait_for_load_state("networkidle")
            
            # Kurz warten damit alle dynamischen Inhalte geladen sind
            await asyncio.sleep(2)
            
            # Titel der Seite prüfen
            title = await page.title()
            print(f"📄 Seitentitel: {title}")
            
            # Screenshot vom initialen Zustand erstellen
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = f"/app/tests/minesearch_initial_state_{timestamp}.png"
            
            await page.screenshot(path=screenshot_path, full_page=True)
            print(f"📸 Screenshot gespeichert: {screenshot_path}")
            
            # Grundlegende Elemente der Seite prüfen
            print("\n🔍 Prüfe Hauptelemente der Seite...")
            
            # Navigation/Header prüfen
            header = await page.query_selector("header, .header, #header")
            if header:
                print("✅ Header-Element gefunden")
            else:
                print("⚠️  Kein Header-Element erkannt")
            
            # Suchformular prüfen
            search_form = await page.query_selector("form, .search-form, #search-form")
            if search_form:
                print("✅ Such-Formular gefunden")
            else:
                print("⚠️  Kein Such-Formular erkannt")
            
            # Tab-Navigation prüfen
            tabs = await page.query_selector_all(".tab, .nav-tab, [role='tab']")
            if tabs:
                print(f"✅ {len(tabs)} Tab(s) gefunden")
            else:
                print("⚠️  Keine Tab-Navigation erkannt")
            
            # JavaScript-Fehler in der Konsole prüfen
            print("\n📋 Console-Logs überprüfen...")
            
            # Console-Handler für Fehlerprotokollierung
            page.on("console", lambda msg: print(f"CONSOLE [{msg.type}]: {msg.text}"))
            page.on("pageerror", lambda error: print(f"PAGE ERROR: {error}"))
            
            # Seite noch einmal neu laden um Console-Events zu erfassen
            await page.reload(wait_until="networkidle")
            await asyncio.sleep(1)
            
            print("\n✅ Browser-Test erfolgreich abgeschlossen!")
            print(f"📄 URL: http://localhost:8000")
            print(f"📸 Screenshot: {screenshot_path}")
            print(f"🖥️  Viewport: 1920x1080")
            print(f"📊 Status: Seite erfolgreich geladen und dokumentiert")
            
            return True
            
        except Exception as e:
            print(f"❌ FEHLER beim Browser-Test: {e}")
            
            # Error-Screenshot bei Fehlern
            error_screenshot = f"/app/tests/minesearch_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            try:
                await page.screenshot(path=error_screenshot)
                print(f"📸 Error-Screenshot gespeichert: {error_screenshot}")
            except:
                print("❌ Konnte keinen Error-Screenshot erstellen")
            
            return False
            
        finally:
            # Browser schließen
            await browser.close()
            print("🔒 Browser geschlossen")

if __name__ == "__main__":
    print("=" * 60)
    print("MINESEARCH PLAYWRIGHT INTERFACE TEST")
    print("=" * 60)
    
    result = asyncio.run(test_minesearch_interface())
    
    if result:
        print("\n🎉 TEST ERFOLGREICH - MineSearch Interface ist bereit für weitere Tests!")
    else:
        print("\n❌ TEST FEHLGESCHLAGEN - Bitte Fehler prüfen und korrigieren")
    
    print("=" * 60)