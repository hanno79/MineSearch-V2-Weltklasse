#!/usr/bin/env python3
"""
Author: rahn
Datum: 04.08.2025
Version: 1.0
Beschreibung: Test der Progress-Anzeige in echter Search-Situation
"""

from playwright.sync_api import sync_playwright
import time

def test_real_search_progress():
    """Teste Progress-Anzeige in echter Search-Situation"""
    
    print("🔍 TEST PROGRESS IN ECHTER SEARCH-SITUATION")
    print("=" * 50)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # Konsole-Logs sammeln
        def handle_console(msg):
            if any(keyword in msg.text.lower() for keyword in ['progress', 'session', 'search', 'enhanced']):
                print(f"🖥️  [{msg.type.upper()}]: {msg.text}")
        page.on('console', handle_console)
        
        # Lade Seite
        print("📱 Lade http://localhost:8000...")
        page.goto('http://localhost:8000', wait_until='networkidle')
        time.sleep(3)
        
        # Gehe zum CSV Tab
        print(f"\n📁 Wechsle zum CSV Tab...")
        page.click('a[data-tab="csv"]')
        time.sleep(1)
        
        # Upload Test-CSV
        print(f"\n📤 Lade Test-CSV hoch...")
        
        # Erstelle Test-CSV im Browser
        page.evaluate("""
            () => {
                // Erstelle Test-CSV Daten
                const csvContent = `mine_name,location,province
Eleonore,Quebec,Quebec
Canadian Malartic,Quebec,Quebec
Agnico Eagle,Quebec,Quebec`;
                
                // Erstelle Blob und File
                const blob = new Blob([csvContent], { type: 'text/csv' });
                const file = new File([blob], 'test_mines.csv', { type: 'text/csv' });
                
                // Simuliere File-Upload
                const fileInput = document.querySelector('input[type="file"]');
                if (fileInput) {
                    const dataTransfer = new DataTransfer();
                    dataTransfer.items.add(file);
                    fileInput.files = dataTransfer.files;
                    
                    // Triggere Change-Event
                    const event = new Event('change', { bubbles: true });
                    fileInput.dispatchEvent(event);
                    
                    return true;
                } else {
                    return false;
                }
            }
        """)
        
        time.sleep(2)
        
        # Wähle wenige Modelle für schnellen Test
        print(f"\n🤖 Wähle Test-Modelle...")
        page.evaluate("""
            () => {
                // Deselektiere alle Modelle erst
                document.querySelectorAll('.model-checkbox').forEach(cb => cb.checked = false);
                
                // Wähle nur 2 schnelle Modelle
                const fastModels = ['openrouter:deepseek-free', 'perplexity:sonar'];
                fastModels.forEach(modelId => {
                    const checkbox = document.querySelector(`input[value="${modelId}"]`);
                    if (checkbox) {
                        checkbox.checked = true;
                    }
                });
                
                // Update Provider-Checkboxes
                const updateEvent = new Event('change', { bubbles: true });
                document.querySelectorAll('.model-checkbox')[0]?.dispatchEvent(updateEvent);
            }
        """)
        
        time.sleep(1)
        
        # Starte Search und überwache Progress
        print(f"\n🚀 Starte Batch-Search und überwache Progress...")
        
        # Klicke Start-Button
        page.click('#start-search')
        
        # Warte kurz und überwache Results-Div
        time.sleep(2)
        
        # Prüfe ob Progress-Anzeige erschienen ist
        progress_check = page.evaluate("""
            () => {
                const resultsDiv = document.getElementById('results');
                if (resultsDiv) {
                    return {
                        hasContent: resultsDiv.innerHTML.length > 100,
                        hasProgressBar: resultsDiv.innerHTML.includes('progress-bar-'),
                        hasProgressContainer: resultsDiv.innerHTML.includes('progress-container'),
                        hasEnhancedLoading: resultsDiv.innerHTML.includes('enhanced-loading-container'),
                        hasWebSocketStatus: resultsDiv.innerHTML.includes('ws-status-'),
                        innerHTML: resultsDiv.innerHTML.substring(0, 500) + '...'
                    };
                } else {
                    return { error: 'Results div not found' };
                }
            }
        """)
        
        print(f"📊 Progress-Anzeige Status:")
        print(f"   Has Content: {'✅' if progress_check.get('hasContent') else '❌'}")
        print(f"   Progress Bar: {'✅' if progress_check.get('hasProgressBar') else '❌'}")
        print(f"   Progress Container: {'✅' if progress_check.get('hasProgressContainer') else '❌'}")
        print(f"   Enhanced Loading: {'✅' if progress_check.get('hasEnhancedLoading') else '❌'}")
        print(f"   WebSocket Status: {'✅' if progress_check.get('hasWebSocketStatus') else '❌'}")
        
        # Screenshot der Progress-Anzeige
        page.screenshot(path='/app/real_search_progress.png')
        print(f"📸 Screenshot: /app/real_search_progress.png")
        
        # Überwache Progress für 30 Sekunden
        print(f"\n⏳ Überwache Progress für 30 Sekunden...")
        
        for i in range(6):  # 6 × 5 Sekunden = 30 Sekunden
            time.sleep(5)
            
            progress_status = page.evaluate("""
                () => {
                    const resultsDiv = document.getElementById('results');
                    const progressBar = resultsDiv?.querySelector('.progress-fill');
                    const progressText = progressBar?.querySelector('span');
                    const wsStatus = resultsDiv?.querySelector('[id^="ws-status-"]');
                    
                    return {
                        progressWidth: progressBar?.style.width || '0%',
                        progressText: progressText?.textContent || '0%',
                        wsStatus: wsStatus?.textContent || 'No status',
                        hasResults: resultsDiv?.innerHTML.includes('search_results') || false
                    };
                }
            """)
            
            print(f"   🔄 Status ({i*5+5}s): Progress {progress_status['progressWidth']} | Text: {progress_status['progressText']} | WS: {progress_status['wsStatus'][:50]}...")
            
            # Wenn Ergebnisse da sind, stoppe Überwachung
            if progress_status['hasResults']:
                print(f"   ✅ Search abgeschlossen! Ergebnisse gefunden.")
                break
                
        # Final Screenshot
        page.screenshot(path='/app/real_search_final.png')
        print(f"📸 Final Screenshot: /app/real_search_final.png")
        
        # Prüfe finale Ergebnisse
        final_check = page.evaluate("""
            () => {
                const resultsDiv = document.getElementById('results');
                return {
                    hasSearchResults: resultsDiv?.innerHTML.includes('search_results') || false,
                    hasCompletedProgress: resultsDiv?.innerHTML.includes('100%') || false,
                    stillHasProgressBar: resultsDiv?.innerHTML.includes('progress-bar-') || false,
                    content: resultsDiv?.innerHTML.substring(0, 200) + '...' || 'No content'
                };
            }
        """)
        
        print(f"\n📋 Finale Ergebnisse:")
        print(f"   Search Results: {'✅' if final_check['hasSearchResults'] else '❌'}")
        print(f"   Completed Progress: {'✅' if final_check['hasCompletedProgress'] else '❌'}")
        print(f"   Still Has Progress Bar: {'⚠️' if final_check['stillHasProgressBar'] else '✅'}")
        
        browser.close()
    
    print(f"\n" + "=" * 50)
    print(f"🎯 REAL SEARCH PROGRESS TEST ABGESCHLOSSEN")

if __name__ == "__main__":
    test_real_search_progress()