#!/usr/bin/env python3
"""
Author: rahn
Datum: 11.08.2025
Version: 1.0
Beschreibung: MineSearch 2.0 - Timer Debug Test mit Playwright

ÄNDERUNG 11.08.2025: Browser-Test für Timer-Problem 
Timer Debug: Echte Browser-Session um Timer-Bug zu reproduzieren und zu fixen
"""

import asyncio
import time
from playwright.async_api import async_playwright, expect

async def test_timer_functionality():
    """Test der Timer-Funktionalität im echten Browser"""
    
    async with async_playwright() as p:
        print("🚀 [TIMER-DEBUG] Starte Browser für Timer-Test...")
        
        # Browser starten
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Console-Logs sammeln
        console_logs = []
        page.on('console', lambda msg: console_logs.append(f"{msg.type}: {msg.text}"))
        
        try:
            print("📱 [TIMER-DEBUG] Lade MineSearch 2.0...")
            await page.goto('http://localhost:8000')
            await page.wait_for_load_state('domcontentloaded')
            
            # Warte bis alles geladen ist
            print("⏳ [TIMER-DEBUG] Warte auf vollständiges Laden...")
            await page.wait_for_timeout(3000)
            
            # Prüfe ob Timer-Element vorhanden ist
            timer_elements = await page.query_selector_all('.search-timer')
            print(f"🕒 [TIMER-DEBUG] Timer-Elemente gefunden: {len(timer_elements)}")
            
            # Prüfe JavaScript-Objekte
            searchTimer_available = await page.evaluate('typeof window.searchTimer !== "undefined"')
            print(f"🔧 [TIMER-DEBUG] window.searchTimer verfügbar: {searchTimer_available}")
            
            if searchTimer_available:
                searchTimer_has_start = await page.evaluate('typeof window.searchTimer.start === "function"')
                print(f"🔧 [TIMER-DEBUG] window.searchTimer.start() verfügbar: {searchTimer_has_start}")
            
            # Test 1: Single Search mit Timer-Überwachung
            print("\n=== TEST 1: SINGLE SEARCH TIMER ===")
            
            # Fülle Single-Search-Form aus
            await page.fill('input[name="mine_name"]', 'Test Mine')
            await page.fill('input[name="country"]', 'Canada')
            
            # Wähle mindestens ein Modell aus
            model_checkbox = await page.query_selector('input[name="model"][value*="openrouter:deepseek-free"]')
            if model_checkbox:
                await model_checkbox.check()
                print("✅ [TIMER-DEBUG] Modell ausgewählt: openrouter:deepseek-free")
            else:
                # Versuche erstes verfügbares Modell
                first_model = await page.query_selector('input[name="model"]')
                if first_model:
                    await first_model.check()
                    model_value = await first_model.get_attribute('value')
                    print(f"✅ [TIMER-DEBUG] Erstes Modell ausgewählt: {model_value}")
            
            # Timer vor Suche prüfen
            timer_before = await page.text_content('.search-timer')
            print(f"🕒 [TIMER-DEBUG] Timer VOR Suche: '{timer_before}'")
            
            # Starte Single Search
            print("🔍 [TIMER-DEBUG] Starte Single Search...")
            await page.click('button[type="submit"]')  # Single Search Button
            
            # Warte kurz und prüfe Timer-Anzeige
            await page.wait_for_timeout(2000)
            timer_during = await page.text_content('.search-timer')
            print(f"🕒 [TIMER-DEBUG] Timer WÄHREND Suche: '{timer_during}'")
            
            # Warte weitere 3 Sekunden um zu sehen ob Timer läuft
            print("⏱️  [TIMER-DEBUG] Warte 3 Sekunden um Timer-Lauf zu beobachten...")
            await page.wait_for_timeout(3000)
            timer_after_3s = await page.text_content('.search-timer')
            print(f"🕒 [TIMER-DEBUG] Timer NACH 3s: '{timer_after_3s}'")
            
            # Resultat analysieren
            if timer_before == timer_during == timer_after_3s:
                print("❌ [TIMER-DEBUG] TIMER-BUG BESTÄTIGT: Timer läuft nicht!")
                print(f"   Alle Werte gleich: {timer_before}")
            else:
                print("✅ [TIMER-DEBUG] Timer funktioniert korrekt")
                print(f"   Vorher: {timer_before} | Während: {timer_during} | Nach 3s: {timer_after_3s}")
            
            # Console-Logs auswerten
            print(f"\n📋 [TIMER-DEBUG] Console-Logs ({len(console_logs)} Einträge):")
            timer_logs = [log for log in console_logs if '🕒' in log or 'TIMER' in log]
            for log in timer_logs[-10:]:  # Nur letzte 10 Timer-Logs
                print(f"   {log}")
            
            # Screenshot für Dokumentation
            await page.screenshot(path='/app/timer_debug_screenshot.png')
            print("📸 [TIMER-DEBUG] Screenshot gespeichert: timer_debug_screenshot.png")
            
            # Test 2: Batch Search Timer (wenn Zeit)
            print("\n=== TEST 2: BATCH SEARCH TIMER ===")
            
            # Wechsle zu Batch-Tab
            batch_tab = await page.query_selector('input[value="batch"]')
            if batch_tab:
                await batch_tab.click()
                await page.wait_for_timeout(1000)
                print("📑 [TIMER-DEBUG] Zu Batch-Tab gewechselt")
                
                # CSV-Datei hochladen (simuliert)
                print("📁 [TIMER-DEBUG] Batch-Search würde CSV benötigen - übersprungen")
            
            print("\n🎯 [TIMER-DEBUG] Browser-Test abgeschlossen")
            
        except Exception as e:
            print(f"❌ [TIMER-DEBUG] Fehler während Browser-Test: {e}")
            await page.screenshot(path='/app/timer_debug_error.png')
            
        finally:
            print("🔄 [TIMER-DEBUG] Browser wird geschlossen...")
            await browser.close()
            
        return console_logs

async def main():
    """Hauptfunktion für Timer-Debug-Test"""
    print("🔥 [TIMER-DEBUG] MineSearch 2.0 Timer Debug Test")
    print("=" * 60)
    
    console_logs = await test_timer_functionality()
    
    print("\n" + "=" * 60)
    print("📊 [TIMER-DEBUG] Test-Zusammenfassung:")
    print(f"   📋 Console-Logs gesammelt: {len(console_logs)}")
    
    # Relevante Logs extrahieren
    relevant_logs = []
    for log in console_logs:
        if any(keyword in log.lower() for keyword in ['timer', '🕒', 'search', 'start', 'stop']):
            relevant_logs.append(log)
    
    if relevant_logs:
        print(f"   🔍 Relevante Timer-Logs: {len(relevant_logs)}")
        print("\n📋 TOP TIMER-LOGS:")
        for log in relevant_logs[:15]:  # Top 15
            print(f"     {log}")
    else:
        print("   ❌ Keine relevanten Timer-Logs gefunden!")
    
    print("\n🎯 [TIMER-DEBUG] Analyse abgeschlossen")

if __name__ == '__main__':
    asyncio.run(main())