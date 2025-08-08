#!/usr/bin/env python3
"""
Author: rahn
Datum: 04.08.2025
Version: 1.0
Beschreibung: Test der korrigierten Progress-Anzeige
"""

from playwright.sync_api import sync_playwright
import time

def test_fixed_progress():
    """Teste die korrigierte Progress-Anzeige"""
    
    print("🔧 TEST KORRIGIERTE PROGRESS-ANZEIGE")
    print("=" * 50)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # Konsole-Logs sammeln
        def handle_console(msg):
            if 'progress' in msg.text.lower() or 'session' in msg.text.lower():
                print(f"🖥️  [{msg.type.upper()}]: {msg.text}")
        page.on('console', handle_console)
        
        # Lade Seite
        print("📱 Lade http://localhost:8000...")
        page.goto('http://localhost:8000', wait_until='networkidle')
        time.sleep(2)
        
        # Test 1: Mit Mines/Models (sollte Progress Bar zeigen)
        print(f"\n🧪 Test 1: Enhanced Loading mit Mines/Models")
        
        result1 = page.evaluate("""
            () => {
                const testDiv = document.createElement('div');
                testDiv.id = 'test-with-mines';
                testDiv.style.cssText = 'border: 3px solid green; padding: 20px; margin: 20px; background: #f0fff0;';
                document.body.appendChild(testDiv);
                
                // Teste mit Mines und Models
                window.showEnhancedLoadingMessage(
                    testDiv,
                    '🔧 TEST: Mit Mines/Models',
                    'Dies sollte eine Progress Bar zeigen',
                    ['Mine_1', 'Mine_2', 'Mine_3'],
                    ['Model_1', 'Model_2']
                );
                
                return {
                    success: true,
                    immediately: {
                        hasProgressBar: testDiv.innerHTML.includes('progress-bar-'),
                        hasProgressContainer: testDiv.innerHTML.includes('progress-container'),
                        hasProgressFill: testDiv.innerHTML.includes('progress-fill'),
                        hasTempSession: testDiv.innerHTML.includes('temp-'),
                        innerHTML: testDiv.innerHTML.substring(0, 300) + '...'
                    }
                };
            }
        """)
        
        print(f"✅ Sofortiges Ergebnis (ohne Async):")
        print(f"   Progress Bar: {'✅' if result1['immediately']['hasProgressBar'] else '❌'}")
        print(f"   Progress Container: {'✅' if result1['immediately']['hasProgressContainer'] else '❌'}")
        print(f"   Progress Fill: {'✅' if result1['immediately']['hasProgressFill'] else '❌'}")
        print(f"   Temp Session: {'✅' if result1['immediately']['hasTempSession'] else '❌'}")
        
        # Warte 3 Sekunden für Session-Erstellung
        print(f"\n⏳ Warte 3 Sekunden für Session-Erstellung...")
        time.sleep(3)
        
        result1_after = page.evaluate("""
            () => {
                const testDiv = document.getElementById('test-with-mines');
                return {
                    hasProgressBar: testDiv.innerHTML.includes('progress-bar-'),
                    hasRealSession: !testDiv.innerHTML.includes('temp-') && testDiv.innerHTML.includes('ws-status-'),
                    innerHTML: testDiv.innerHTML.substring(0, 300) + '...'
                };
            }
        """)
        
        print(f"✅ Nach Session-Erstellung:")
        print(f"   Progress Bar: {'✅' if result1_after['hasProgressBar'] else '❌'}")
        print(f"   Echte Session: {'✅' if result1_after['hasRealSession'] else '❌'}")
        
        # Test 2: Ohne Mines/Models (sollte trotzdem Progress Bar zeigen)
        print(f"\n🧪 Test 2: Enhanced Loading ohne Mines/Models")
        
        result2 = page.evaluate("""
            () => {
                const testDiv = document.createElement('div');
                testDiv.id = 'test-without-mines';
                testDiv.style.cssText = 'border: 3px solid orange; padding: 20px; margin: 20px; background: #fff8f0;';
                document.body.appendChild(testDiv);
                
                // Teste ohne Mines und Models  
                window.showEnhancedLoadingMessage(
                    testDiv,
                    '🔧 TEST: Ohne Mines/Models',
                    'Dies sollte trotzdem eine Progress Bar zeigen (temp session)'
                );
                
                return {
                    hasProgressBar: testDiv.innerHTML.includes('progress-bar-'),
                    hasProgressContainer: testDiv.innerHTML.includes('progress-container'),
                    hasTempSession: testDiv.innerHTML.includes('temp-'),
                    innerHTML: testDiv.innerHTML.substring(0, 300) + '...'
                };
            }
        """)
        
        print(f"✅ Ohne Mines/Models:")
        print(f"   Progress Bar: {'✅' if result2['hasProgressBar'] else '❌'}")
        print(f"   Progress Container: {'✅' if result2['hasProgressContainer'] else '❌'}")
        print(f"   Temp Session: {'✅' if result2['hasTempSession'] else '❌'}")
        
        # Test 3: Teste Progress-Simulation
        print(f"\n🧪 Test 3: Progress-Simulation")
        
        page.evaluate("""
            () => {
                // Simuliere Progress-Updates für beide Test-Divs
                const testDiv1 = document.getElementById('test-with-mines');
                const testDiv2 = document.getElementById('test-without-mines');
                
                [testDiv1, testDiv2].forEach((div, index) => {
                    if (div) {
                        const progressBar = div.querySelector('.progress-fill');
                        const progressText = div.querySelector('.progress-fill span');
                        
                        if (progressBar && progressText) {
                            let progress = 0;
                            const interval = setInterval(() => {
                                progress += 20;
                                progressBar.style.width = progress + '%';
                                progressText.textContent = progress + '%';
                                
                                if (progress >= 100) {
                                    clearInterval(interval);
                                    progressText.textContent = '✅ Abgeschlossen';
                                }
                            }, 500);
                        }
                    }
                });
            }
        """)
        
        print(f"✅ Progress-Simulation gestartet...")
        
        # Screenshot
        page.screenshot(path='/app/progress_fixed_test.png')
        print(f"📸 Screenshot: /app/progress_fixed_test.png")
        
        # Warte für Animation
        print(f"\n⏳ Warte 5 Sekunden für Progress-Animation...")
        time.sleep(5)
        
        # Final Screenshot
        page.screenshot(path='/app/progress_fixed_final.png')
        print(f"📸 Final Screenshot: /app/progress_fixed_final.png")
        
        browser.close()
    
    print(f"\n" + "=" * 50)
    print(f"🎯 KORRIGIERTE PROGRESS-ANZEIGE TEST ABGESCHLOSSEN")

if __name__ == "__main__":
    test_fixed_progress()