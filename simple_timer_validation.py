#!/usr/bin/env python3
"""
Author: rahn
Datum: 11.08.2025
Version: 1.0
Beschreibung: MineSearch 2.0 - Einfache Timer Validation

ÄNDERUNG 11.08.2025: Direkte Timer-Funktions-Validation ohne API-Aufrufe
"""

import asyncio
import time
from playwright.async_api import async_playwright

async def simple_timer_test():
    """Direkte Timer-Test ohne API-Abhängigkeiten"""
    
    async with async_playwright() as p:
        print("🎯 [SIMPLE-TIMER] Starte vereinfachten Timer-Test...")
        
        # Browser starten (headless=False für Debug)
        browser = await p.chromium.launch(headless=False, slow_mo=200)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Console-Logs sammeln
        console_logs = []
        page.on('console', lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))
        
        try:
            # Lade MineSearch 2.0
            print("📱 [SIMPLE-TIMER] Lade http://localhost:8000...")
            await page.goto('http://localhost:8000')
            await page.wait_for_load_state('domcontentloaded')
            await page.wait_for_timeout(3000)
            
            # Prüfe Timer-Element
            loading_timer = await page.query_selector('#loading-timer')
            if not loading_timer:
                print("❌ [SIMPLE-TIMER] #loading-timer nicht gefunden!")
                return False
                
            print("✅ [SIMPLE-TIMER] #loading-timer Element gefunden")
            
            # Prüfe JavaScript-Timer-Verfügbarkeit
            timer_check = await page.evaluate("""
                () => {
                    const checks = {
                        searchTimerExists: typeof window.searchTimer !== 'undefined',
                        hasStartFunction: window.searchTimer && typeof window.searchTimer.start === 'function',
                        hasStopFunction: window.searchTimer && typeof window.searchTimer.stop === 'function',
                        hasFormatFunction: window.searchTimer && typeof window.searchTimer.formatTime === 'function'
                    };
                    return checks;
                }
            """)
            
            print(f"🔧 [SIMPLE-TIMER] Timer-Check: {timer_check}")
            
            if not timer_check['searchTimerExists']:
                print("❌ [SIMPLE-TIMER] window.searchTimer nicht verfügbar!")
                return False
                
            # Direkter Timer-Test
            print("🚀 [SIMPLE-TIMER] Starte direkten Timer-Test...")
            
            timer_before = await loading_timer.text_content()
            print(f"⏱️ [SIMPLE-TIMER] Timer VOR Start: '{timer_before.strip()}'")
            
            # Starte Timer direkt via JavaScript
            await page.evaluate("""
                () => {
                    console.log('🕒 [DIRECT-TEST] Starte Timer direkt...');
                    if (window.searchTimer && window.searchTimer.start) {
                        window.searchTimer.start();
                        console.log('🕒 [DIRECT-TEST] Timer gestartet');
                    } else {
                        console.error('❌ [DIRECT-TEST] Timer-Start fehlgeschlagen');
                    }
                }
            """)
            
            # Warte 5 Sekunden und messe Timer
            await page.wait_for_timeout(5000)
            
            timer_after = await loading_timer.text_content()
            print(f"⏱️ [SIMPLE-TIMER] Timer NACH 5s: '{timer_after.strip()}'")
            
            # Stoppe Timer
            await page.evaluate("""
                () => {
                    console.log('🛑 [DIRECT-TEST] Stoppe Timer...');
                    if (window.searchTimer && window.searchTimer.stop) {
                        window.searchTimer.stop();
                        console.log('🛑 [DIRECT-TEST] Timer gestoppt');
                    }
                }
            """)
            
            # Analysiere Ergebnis
            print(f"\n📊 [SIMPLE-TIMER] Timer-Analyse:")
            print(f"   Vorher: '{timer_before.strip()}'")
            print(f"   Nach 5s: '{timer_after.strip()}'")
            
            # Check ob Timer läuft
            timer_works = False
            if timer_before.strip() != timer_after.strip():
                # Timer hat sich geändert
                if '00:0' in timer_after and timer_after.strip() != '00:00':
                    timer_works = True
                    print("✅ [SIMPLE-TIMER] TIMER FUNKTIONIERT!")
                else:
                    print(f"⚠️ [SIMPLE-TIMER] Timer läuft, Format unexpected: '{timer_after.strip()}'")
            else:
                print(f"❌ [SIMPLE-TIMER] TIMER LÄUFT NICHT - Werte gleich")
                
            # Console-Logs filtern
            timer_logs = [log for log in console_logs if any(keyword in log.lower() for keyword in ['timer', '🕒', '🛑', 'direct-test'])]
            print(f"\n📋 [SIMPLE-TIMER] Timer Console-Logs ({len(timer_logs)}):")
            for log in timer_logs:
                print(f"   {log}")
                
            # Screenshot
            await page.screenshot(path='/app/simple_timer_test.png')
            print("📸 [SIMPLE-TIMER] Screenshot: simple_timer_test.png")
                
            return timer_works
            
        except Exception as e:
            print(f"❌ [SIMPLE-TIMER] Fehler: {e}")
            await page.screenshot(path='/app/simple_timer_error.png')
            return False
            
        finally:
            await browser.close()

async def main():
    """Hauptfunktion"""
    print("🎯 VEREINFACHTER TIMER-TEST")
    print("=" * 50)
    print("Test: Direkte Timer-Funktions-Validation")
    print("=" * 50)
    
    success = await simple_timer_test()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 TIMER FUNKTIONIERT!")
        print("   ✅ #loading-timer wird korrekt aktualisiert")
        print("   ✅ window.searchTimer funktioniert")
    else:
        print("❌ TIMER FUNKTIONIERT NICHT!")
        print("   ❌ Weitere Analyse erforderlich")
    
    print("=" * 50)
    
    return success

if __name__ == '__main__':
    result = asyncio.run(main())
    exit(0 if result else 1)