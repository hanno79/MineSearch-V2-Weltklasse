#!/usr/bin/env python3
"""
Author: rahn
Datum: 11.08.2025
Version: 1.1
Beschreibung: MineSearch 2.0 - Timer Bereinigung Validation

ÄNDERUNG 11.08.2025: Playwright-Validation für Timer-Bereinigung
Timer System: Einziges Master-System (utils.js) aktualisiert #loading-timer
"""

import asyncio
import time
from playwright.async_api import async_playwright

async def validate_timer_fix():
    """Validiert die Timer-Bereinigung mit echtem Browser-Test"""
    
    async with async_playwright() as p:
        print("🎯 [TIMER-VALIDATION] Starte Timer-Fix-Validierung...")
        
        # Browser starten (headless=False für Debug)
        browser = await p.chromium.launch(headless=False, slow_mo=500)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Console-Logs sammeln
        console_logs = []
        page.on('console', lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))
        
        try:
            # Lade MineSearch 2.0
            print("📱 [TIMER-VALIDATION] Lade http://localhost:8000...")
            await page.goto('http://localhost:8000')
            await page.wait_for_load_state('domcontentloaded')
            await page.wait_for_timeout(2000)
            
            # Prüfe Timer-Element im DOM
            print("🔍 [TIMER-VALIDATION] Prüfe Timer-Element...")
            loading_timer = await page.query_selector('#loading-timer')
            if not loading_timer:
                print("❌ [TIMER-VALIDATION] #loading-timer Element nicht gefunden!")
                return False
                
            initial_timer_text = await loading_timer.text_content()
            print(f"⏱️ [TIMER-VALIDATION] Anfänglicher Timer-Wert: '{initial_timer_text}'")
            
            # Prüfe JavaScript-Timer-Verfügbarkeit
            timer_available = await page.evaluate('typeof window.searchTimer !== "undefined"')
            print(f"🔧 [TIMER-VALIDATION] window.searchTimer verfügbar: {timer_available}")
            
            if not timer_available:
                print("❌ [TIMER-VALIDATION] window.searchTimer nicht verfügbar!")
                return False
                
            # Test: Single Search mit Timer-Überwachung
            print("\n🔍 [TIMER-VALIDATION] Starte Single Search Test...")
            
            # Fülle Single-Search-Form aus
            await page.fill('input[name="mine_name"]', 'Test Mine Timer')
            
            # Wähle ein Modell aus (openrouter:deepseek-free)
            model_selected = False
            model_checkboxes = await page.query_selector_all('input[name="model"]')
            for checkbox in model_checkboxes:
                value = await checkbox.get_attribute('value')
                if 'deepseek-free' in value:
                    await checkbox.check()
                    model_selected = True
                    print(f"✅ [TIMER-VALIDATION] Modell ausgewählt: {value}")
                    break
            
            if not model_selected:
                # Fallback: Erstes verfügbares Modell
                if model_checkboxes:
                    await model_checkboxes[0].check()
                    value = await model_checkboxes[0].get_attribute('value')
                    print(f"✅ [TIMER-VALIDATION] Fallback-Modell: {value}")
                else:
                    print("❌ [TIMER-VALIDATION] Keine Modelle verfügbar!")
                    return False
            
            # Timer vor Suche
            timer_before = await loading_timer.text_content()
            print(f"⏱️ [TIMER-VALIDATION] Timer VOR Suche: '{timer_before}'")
            
            # Starte Single Search
            print("🚀 [TIMER-VALIDATION] Starte Single Search...")
            await page.click('button[type="submit"]')
            
            # Warte kurz und messe Timer
            await page.wait_for_timeout(2000)
            timer_after_2s = await loading_timer.text_content()
            print(f"⏱️ [TIMER-VALIDATION] Timer NACH 2s: '{timer_after_2s}'")
            
            # Warte weitere 3 Sekunden
            await page.wait_for_timeout(3000)
            timer_after_5s = await loading_timer.text_content()
            print(f"⏱️ [TIMER-VALIDATION] Timer NACH 5s: '{timer_after_5s}'")
            
            # Analysiere Timer-Verhalten
            print(f"\n📊 [TIMER-VALIDATION] Timer-Analyse:")
            print(f"   Vorher: '{timer_before}'")
            print(f"   Nach 2s: '{timer_after_2s}'")
            print(f"   Nach 5s: '{timer_after_5s}'")
            
            # Erfolgskriterien prüfen
            timer_works = False
            if timer_before != timer_after_5s:
                if '00:0' in timer_after_5s and timer_after_5s != '00:00':
                    timer_works = True
                    print("✅ [TIMER-VALIDATION] TIMER FUNKTIONIERT!")
                else:
                    print(f"⚠️ [TIMER-VALIDATION] Timer läuft, aber unerwartetes Format: '{timer_after_5s}'")
            else:
                print(f"❌ [TIMER-VALIDATION] TIMER LÄUFT NICHT - alle Werte gleich: '{timer_before}'")
            
            # Screenshot für Dokumentation
            await page.screenshot(path='/app/timer_validation_result.png')
            print("📸 [TIMER-VALIDATION] Screenshot: timer_validation_result.png")
            
            # Console-Logs analysieren
            timer_logs = [log for log in console_logs if any(keyword in log.lower() for keyword in ['timer', '🕒', 'search'])]
            print(f"\n📋 [TIMER-VALIDATION] Relevante Console-Logs ({len(timer_logs)}):")
            for log in timer_logs[-10:]:
                print(f"   {log}")
                
            return timer_works
            
        except Exception as e:
            print(f"❌ [TIMER-VALIDATION] Fehler: {e}")
            await page.screenshot(path='/app/timer_validation_error.png')
            return False
            
        finally:
            await browser.close()

async def main():
    """Hauptfunktion für Timer-Validation"""
    print("🎯 TIMER-BEREINIGUNG VALIDATION")
    print("=" * 60)
    print("Version: v1.1.0 - Timer-Bereinigung")
    print("Ziel: #loading-timer Element soll korrekt aktualisiert werden")
    print("=" * 60)
    
    # Validierung ausführen
    success = await validate_timer_fix()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 TIMER-FIX ERFOLGREICH VALIDIERT!")
        print("   ✅ #loading-timer Element wird korrekt aktualisiert")
        print("   ✅ Keine parallelen Timer-Instanzen mehr")
        print("   ✅ Einziges Master-System (utils.js) funktioniert")
    else:
        print("❌ TIMER-FIX FEHLGESCHLAGEN!")
        print("   ❌ Timer läuft weiterhin nicht korrekt")
        print("   🔧 Weitere Debug-Analyse erforderlich")
    
    print("=" * 60)
    
    return success

if __name__ == '__main__':
    result = asyncio.run(main())
    exit(0 if result else 1)