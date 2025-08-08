#!/usr/bin/env python3
"""
Author: rahn
Datum: 04.08.2025
Version: 1.0
Beschreibung: Frontend Progress-Tracking Debug-Script
"""

import requests
import json
import time
from playwright.sync_api import sync_playwright

def debug_progress_frontend():
    """Debug der Frontend Progress-Tracking Funktionalität"""
    
    print("🔍 FRONTEND PROGRESS-TRACKING DEBUG")
    print("=" * 50)
    
    with sync_playwright() as p:
        # Browser starten
        browser = p.chromium.launch(headless=False, args=['--disable-web-security'])
        page = browser.new_page()
        
        # Konsole-Nachrichten sammeln
        console_messages = []
        def handle_console(msg):
            console_messages.append(f"[{msg.type}] {msg.text}")
            print(f"🖥️  CONSOLE [{msg.type.upper()}]: {msg.text}")
        
        page.on('console', handle_console)
        
        # Fehler sammeln
        page_errors = []
        def handle_error(error):
            page_errors.append(str(error))
            print(f"❌ PAGE ERROR: {error}")
        
        page.on('pageerror', handle_error)
        
        try:
            # Seite laden
            print(f"\n📱 Lade http://localhost:8000")
            page.goto('http://localhost:8000', wait_until='networkidle')
            time.sleep(2)
            
            # JavaScript-Initialisierung prüfen
            print(f"\n🔍 Teste JavaScript-Initialisierung:")
            
            # 1. Prüfe ob progress-tracking.js geladen wurde
            progress_script_loaded = page.evaluate("""
                () => {
                    const scripts = Array.from(document.querySelectorAll('script[src]'));
                    return scripts.some(script => script.src.includes('progress-tracking.js'));
                }
            """)
            print(f"   progress-tracking.js geladen: {'✅' if progress_script_loaded else '❌'}")
            
            # 2. Prüfe window.progressTracker
            progress_tracker_exists = page.evaluate("() => typeof window.progressTracker !== 'undefined'")
            print(f"   window.progressTracker existiert: {'✅' if progress_tracker_exists else '❌'}")
            
            # 3. Prüfe showEnhancedLoadingMessage Funktion
            enhanced_loading_exists = page.evaluate("() => typeof window.showEnhancedLoadingMessage === 'function'")
            print(f"   showEnhancedLoadingMessage Funktion: {'✅' if enhanced_loading_exists else '❌'}")
            
            # 4. Teste ProgressTracker Klasse
            if progress_tracker_exists:
                tracker_methods = page.evaluate("""
                    () => {
                        const tracker = window.progressTracker;
                        return {
                            hasCreateSession: typeof tracker.createProgressSession === 'function',
                            hasShowEnhanced: typeof tracker.showEnhancedLoadingMessage === 'function',
                            hasConnectWS: typeof tracker.connectWebSocket === 'function',
                            baseUrl: tracker.baseUrl,
                            wsUrl: tracker.wsUrl
                        };
                    }
                """)
                print(f"   createProgressSession: {'✅' if tracker_methods['hasCreateSession'] else '❌'}")
                print(f"   showEnhancedLoadingMessage: {'✅' if tracker_methods['hasShowEnhanced'] else '❌'}")
                print(f"   connectWebSocket: {'✅' if tracker_methods['hasConnectWS'] else '❌'}")
                print(f"   baseUrl: {tracker_methods['baseUrl']}")
                print(f"   wsUrl: {tracker_methods['wsUrl']}")
            
            # 5. Test showEnhancedLoadingMessage direkt
            print(f"\n🧪 Teste showEnhancedLoadingMessage direkt:")
            
            # Erstelle Test-Element
            page.evaluate("""
                () => {
                    const testDiv = document.createElement('div');
                    testDiv.id = 'progress-test-div';
                    testDiv.style.cssText = 'border: 2px solid red; padding: 20px; margin: 20px; background: #f0f0f0;';
                    document.body.appendChild(testDiv);
                }
            """)
            
            # Teste Enhanced Loading Message
            test_result = page.evaluate("""
                () => {
                    try {
                        const testDiv = document.getElementById('progress-test-div');
                        if (typeof window.showEnhancedLoadingMessage === 'function') {
                            window.showEnhancedLoadingMessage(
                                testDiv, 
                                'TEST: Progress Tracking', 
                                'Dies ist ein Test der Progress-Anzeige',
                                ['Mine_1', 'Mine_2'], 
                                ['Model_1', 'Model_2']
                            );
                            return {
                                success: true,
                                innerHTML: testDiv.innerHTML.substring(0, 200) + '...',
                                hasProgressBar: testDiv.innerHTML.includes('progress-bar-'),
                                hasProgressText: testDiv.innerHTML.includes('progress-text-')
                            };
                        } else {
                            return { success: false, error: 'showEnhancedLoadingMessage function not found' };
                        }
                    } catch (error) {
                        return { success: false, error: error.toString() };
                    }
                }
            """)
            
            print(f"   Enhanced Loading Test: {'✅' if test_result['success'] else '❌'}")
            if test_result['success']:
                print(f"   Hat Progress Bar: {'✅' if test_result['hasProgressBar'] else '❌'}")
                print(f"   Hat Progress Text: {'✅' if test_result['hasProgressText'] else '❌'}")
                print(f"   HTML Preview: {test_result['innerHTML']}")
            else:
                print(f"   Fehler: {test_result.get('error', 'Unknown error')}")
            
            # Screenshot machen
            print(f"\n📸 Screenshot erstellen...")
            page.screenshot(path='/app/progress_debug_screenshot.png')
            print(f"   Screenshot gespeichert: /app/progress_debug_screenshot.png")
            
            # Warte ein bisschen um visuell zu sehen
            print(f"\n⏳ Warte 5 Sekunden für visuelle Inspektion...")
            time.sleep(5)
            
            # 6. Teste WebSocket-Verbindung  
            print(f"\n🔌 Teste WebSocket-Verbindung:")
            
            # Erstelle Test-Session über API
            try:
                response = requests.post('http://localhost:8000/api/progress/create-session', 
                    json={'mines': ['Mine_1', 'Mine_2'], 'models': ['Model_1', 'Model_2']}, 
                    timeout=5)
                
                if response.status_code == 200:
                    session_data = response.json()
                    session_id = session_data['session_id']
                    print(f"   API Session erstellt: ✅ {session_id[:8]}...")
                    
                    # Teste WebSocket-Verbindung im Browser
                    ws_test_result = page.evaluate(f"""
                        async () => {{
                            try {{
                                const wsUrl = 'ws://localhost:8000/ws/progress/{session_id}';
                                const ws = new WebSocket(wsUrl);
                                
                                return new Promise((resolve) => {{
                                    const timeout = setTimeout(() => {{
                                        ws.close();
                                        resolve({{ success: false, error: 'Timeout after 3 seconds' }});
                                    }}, 3000);
                                    
                                    ws.onopen = () => {{
                                        clearTimeout(timeout);
                                        ws.close();
                                        resolve({{ success: true, url: wsUrl }});
                                    }};
                                    
                                    ws.onerror = (error) => {{
                                        clearTimeout(timeout);
                                        resolve({{ success: false, error: 'WebSocket connection failed' }});
                                    }};
                                }});
                            }} catch (error) {{
                                return {{ success: false, error: error.toString() }};
                            }}
                        }}
                    """)
                    
                    print(f"   WebSocket-Verbindung: {'✅' if ws_test_result['success'] else '❌'}")
                    if not ws_test_result['success']:
                        print(f"   WebSocket Fehler: {ws_test_result.get('error', 'Unknown error')}")
                        
                else:
                    print(f"   API Session Fehler: ❌ Status {response.status_code}")
                    
            except Exception as e:
                print(f"   API Test Fehler: ❌ {e}")
            
        except Exception as e:
            print(f"❌ Browser-Test Fehler: {e}")
        
        finally:
            # Konsole-Nachrichten zusammenfassen
            print(f"\n📋 KONSOLE-NACHRICHTEN ZUSAMMENFASSUNG:")
            print(f"   Total Nachrichten: {len(console_messages)}")
            
            errors = [msg for msg in console_messages if '[error]' in msg.lower()]
            warnings = [msg for msg in console_messages if '[warning]' in msg.lower()]
            
            print(f"   Fehler: {len(errors)}")
            for error in errors[-5:]:  # Zeige letzte 5 Fehler
                print(f"     {error}")
                
            print(f"   Warnungen: {len(warnings)}")
            for warning in warnings[-3:]:  # Zeige letzte 3 Warnungen
                print(f"     {warning}")
            
            if page_errors:
                print(f"\n❌ PAGE ERRORS ({len(page_errors)}):")
                for error in page_errors:
                    print(f"   {error}")
            
            browser.close()
    
    print(f"\n" + "=" * 50)
    print(f"🎯 FRONTEND DEBUG ABGESCHLOSSEN")
    print(f"=" * 50)

if __name__ == "__main__":
    debug_progress_frontend()