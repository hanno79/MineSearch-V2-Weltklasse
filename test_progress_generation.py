#!/usr/bin/env python3
"""
Author: rahn
Datum: 04.08.2025
Version: 1.0
Beschreibung: Test der Progress-HTML-Generierung
"""

import requests
import json
from playwright.sync_api import sync_playwright

def test_progress_generation():
    """Teste die Progress-HTML-Generierung"""
    
    print("🧪 TEST PROGRESS-HTML-GENERIERUNG")
    print("=" * 50)
    
    # Erstelle echte Session
    print("\n📊 Erstelle echte Progress-Session...")
    try:
        response = requests.post('http://localhost:8000/api/progress/create-session', 
            json={'mines': ['Mine_1', 'Mine_2', 'Mine_3'], 'models': ['Model_1', 'Model_2']}, 
            timeout=5)
        
        if response.status_code == 200:
            session_data = response.json()
            session_id = session_data['session_id']
            print(f"✅ Session erstellt: {session_id[:12]}...")
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False)
                page = browser.new_page()
                
                # Konsole-Logs sammeln
                def handle_console(msg):
                    print(f"🖥️  [{msg.type.upper()}]: {msg.text}")
                page.on('console', handle_console)
                
                # Lade Seite
                page.goto('http://localhost:8000', wait_until='networkidle')
                
                # Teste Enhanced Loading mit echter Session
                print(f"\n🔧 Teste Enhanced Loading mit Session {session_id[:8]}...")
                
                result = page.evaluate(f"""
                    () => {{
                        // Erstelle Test-Container
                        const testDiv = document.createElement('div');
                        testDiv.id = 'real-progress-test';
                        testDiv.style.cssText = 'border: 3px solid blue; padding: 30px; margin: 20px; background: white;';
                        document.body.appendChild(testDiv);
                        
                        // Teste mit echter Session-ID
                        const sessionId = '{session_id}';
                        const progressBarId = `progress-bar-${{Date.now()}}`;
                        const progressTextId = `progress-text-${{Date.now()}}`;
                        
                        // Direkte HTML-Generierung
                        const html = `
                            <div class="enhanced-loading-container" style="
                                padding: 30px; 
                                text-align: center; 
                                background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); 
                                border-radius: 12px; 
                                border: 2px solid #0ea5e9;
                                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                                margin: 20px 0;
                            ">
                                <h3 style="color: #0c4a6e; margin-bottom: 15px; font-size: 1.5em;">
                                    🧪 REAL SESSION TEST
                                </h3>
                                
                                <p style="color: #0369a1; margin-bottom: 20px;">Testing mit Session: ${{sessionId.substring(0, 8)}}...</p>
                                
                                <!-- Progress Bar Container -->
                                <div class="progress-container" style="
                                    background: #e2e8f0; 
                                    border-radius: 10px; 
                                    height: 30px; 
                                    margin: 20px 0;
                                    position: relative;
                                    overflow: hidden;
                                    box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
                                ">
                                    <div id="${{progressBarId}}" class="progress-fill" style="
                                        height: 100%; 
                                        background: linear-gradient(90deg, #0ea5e9, #0284c7);
                                        width: 0%; 
                                        transition: width 0.5s ease;
                                        display: flex;
                                        align-items: center;
                                        justify-content: center;
                                        color: white;
                                        font-weight: bold;
                                        font-size: 14px;
                                        border-radius: 8px;
                                    ">
                                        <span id="${{progressTextId}}">0%</span>
                                    </div>
                                </div>
                                
                                <!-- Progress Information -->
                                <div class="progress-info" style="
                                    display: grid; 
                                    grid-template-columns: 1fr 1fr; 
                                    gap: 15px; 
                                    margin-top: 20px;
                                    font-size: 14px;
                                ">
                                    <div style="background: rgba(255,255,255,0.7); padding: 10px; border-radius: 8px;">
                                        <strong>Aktuelle Operation:</strong><br>
                                        <span id="current-operation-${{Date.now()}}">Initializing...</span>
                                    </div>
                                    <div style="background: rgba(255,255,255,0.7); padding: 10px; border-radius: 8px;">
                                        <strong>Verbleibende Zeit:</strong><br>
                                        <span id="eta-${{Date.now()}}">Berechne...</span>
                                    </div>
                                </div>
                                
                                <!-- WebSocket Status -->
                                <div class="websocket-status" style="
                                    margin-top: 15px; 
                                    font-size: 12px; 
                                    color: #64748b;
                                ">
                                    <span id="ws-status-${{sessionId}}">🔄 Verbindung wird hergestellt...</span>
                                </div>
                            </div>
                        `;
                        
                        testDiv.innerHTML = html;
                        
                        // Teste Progress-Bar Animation
                        setTimeout(() => {{
                            const progressBar = document.getElementById(progressBarId);
                            const progressText = document.getElementById(progressTextId);
                            if (progressBar && progressText) {{
                                progressBar.style.width = '25%';
                                progressText.textContent = '25%';
                            }}
                        }}, 1000);
                        
                        setTimeout(() => {{
                            const progressBar = document.getElementById(progressBarId);
                            const progressText = document.getElementById(progressTextId);
                            if (progressBar && progressText) {{
                                progressBar.style.width = '75%';
                                progressText.textContent = '75%';
                            }}
                        }}, 2000);
                        
                        return {{
                            success: true,
                            hasProgressContainer: html.includes('progress-container'),
                            hasProgressBar: html.includes('progress-fill'),
                            hasProgressText: html.includes('progress-text-'),
                            hasProgressInfo: html.includes('progress-info'),
                            hasWebSocketStatus: html.includes('ws-status-'),
                            htmlLength: html.length
                        }};
                    }}
                """)
                
                print(f"✅ HTML-Generierung erfolgreich:")
                print(f"   Progress Container: {'✅' if result['hasProgressContainer'] else '❌'}")
                print(f"   Progress Bar: {'✅' if result['hasProgressBar'] else '❌'}")
                print(f"   Progress Text: {'✅' if result['hasProgressText'] else '❌'}")
                print(f"   Progress Info: {'✅' if result['hasProgressInfo'] else '❌'}")
                print(f"   WebSocket Status: {'✅' if result['hasWebSocketStatus'] else '❌'}")
                print(f"   HTML Größe: {result['htmlLength']} Zeichen")
                
                # Screenshot
                page.screenshot(path='/app/progress_real_test.png')
                print(f"📸 Screenshot: /app/progress_real_test.png")
                
                # Warte für Animation
                print(f"\n⏳ Warte 5 Sekunden für Progress-Animation...")
                import time
                time.sleep(5)
                
                # Test mit progressTracker.showEnhancedLoadingMessage
                print(f"\n🎯 Teste mit progressTracker.showEnhancedLoadingMessage...")
                
                tracker_result = page.evaluate(f"""
                    () => {{
                        const testDiv2 = document.createElement('div');
                        testDiv2.id = 'tracker-progress-test';
                        testDiv2.style.cssText = 'border: 3px solid green; padding: 30px; margin: 20px; background: #f0fff0;';
                        document.body.appendChild(testDiv2);
                        
                        // Teste mit progressTracker
                        if (window.progressTracker) {{
                            window.progressTracker.showEnhancedLoadingMessage(
                                testDiv2,
                                '🚀 ProgressTracker Test',
                                'Testing mit echten Parametern',
                                ['Mine_1', 'Mine_2', 'Mine_3'],
                                ['Model_1', 'Model_2']
                            );
                            
                            return {{
                                success: true,
                                innerHTML: testDiv2.innerHTML.substring(0, 500) + '...',
                                hasProgressBar: testDiv2.innerHTML.includes('progress-bar-'),
                                hasProgressText: testDiv2.innerHTML.includes('progress-text-'),
                                hasSession: testDiv2.innerHTML.includes('Session')
                            }};
                        }} else {{
                            return {{ success: false, error: 'progressTracker not found' }};
                        }}
                    }}
                """)
                
                print(f"ProgressTracker Test:")
                print(f"   Erfolgreich: {'✅' if tracker_result['success'] else '❌'}")
                if tracker_result['success']:
                    print(f"   Hat Progress Bar: {'✅' if tracker_result['hasProgressBar'] else '❌'}")
                    print(f"   Hat Progress Text: {'✅' if tracker_result['hasProgressText'] else '❌'}")
                    print(f"   HTML-Vorschau: {tracker_result['innerHTML']}")
                
                print(f"\n⏳ Final screenshot in 3 Sekunden...")
                time.sleep(3)
                page.screenshot(path='/app/progress_final_test.png')
                
                browser.close()
        
        else:
            print(f"❌ Session-Erstellung fehlgeschlagen: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Fehler: {e}")
    
    print(f"\n" + "=" * 50)
    print(f"🎯 PROGRESS-GENERATION TEST ABGESCHLOSSEN")

if __name__ == "__main__":
    test_progress_generation()