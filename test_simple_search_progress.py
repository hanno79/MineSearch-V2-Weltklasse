#!/usr/bin/env python3
"""
Author: rahn
Datum: 04.08.2025
Version: 1.0
Beschreibung: Test Progress-Anzeige mit einfacher Single-Search
"""

from playwright.sync_api import sync_playwright
import time

def test_simple_search_progress():
    """Teste Progress-Anzeige mit einfacher Single-Search"""
    
    print("🔍 TEST PROGRESS MIT EINFACHER SINGLE-SEARCH")
    print("=" * 50)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # Konsole-Logs sammeln
        def handle_console(msg):
            if any(keyword in msg.text.lower() for keyword in ['progress', 'session', 'search', 'enhanced', 'creating']):
                print(f"🖥️  [{msg.type.upper()}]: {msg.text}")
        page.on('console', handle_console)
        
        # Lade Seite
        print("📱 Lade http://localhost:8000...")
        page.goto('http://localhost:8000', wait_until='networkidle')
        time.sleep(3)
        
        # Warte auf Model-Loading
        print(f"\n⏳ Warte auf Model-Loading...")
        page.wait_for_selector('.model-checkbox', timeout=10000)
        time.sleep(2)
        
        # Deselektiere alle Modelle und wähle nur 2 schnelle
        print(f"\n🤖 Konfiguriere schnelle Test-Modelle...")
        page.evaluate("""
            () => {
                // Deselektiere alle
                document.querySelectorAll('.model-checkbox').forEach(cb => cb.checked = false);
                
                // Wähle nur 2 sehr schnelle Modelle
                const fastModels = ['openrouter:deepseek-free', 'perplexity:sonar'];
                let selectedCount = 0;
                
                fastModels.forEach(modelId => {
                    const checkbox = document.querySelector(`input[value="${modelId}"]`);
                    if (checkbox) {
                        checkbox.checked = true;
                        selectedCount++;
                        console.log(`✅ Selected model: ${modelId}`);
                    }
                });
                
                // Trigger update event
                const firstCheckbox = document.querySelector('.model-checkbox');
                if (firstCheckbox) {  
                    firstCheckbox.dispatchEvent(new Event('change', { bubbles: true }));
                }
                
                return selectedCount;
            }
        """)
        
        time.sleep(1)
        
        # Gebe Mine-Name ein
        print(f"\n📝 Gebe Mine-Name ein...")
        page.fill('input[name="mine_name"]', 'Eleonore')
        time.sleep(1)
        
        # Starte Search
        print(f"\n🚀 Starte Single-Search...")
        page.click('#search-single')
        
        # Warte kurz und prüfe Progress-Anzeige
        time.sleep(2)
        
        progress_check = page.evaluate("""
            () => {
                const resultsDiv = document.getElementById('results');
                if (!resultsDiv) return { error: 'Results div not found' };
                
                const html = resultsDiv.innerHTML;
                return {
                    hasContent: html.length > 50,
                    hasProgressBar: html.includes('progress-bar-'),
                    hasProgressContainer: html.includes('progress-container'),
                    hasEnhancedLoading: html.includes('enhanced-loading-container'),
                    hasProgressFill: html.includes('progress-fill'),
                    hasWebSocketStatus: html.includes('ws-status-'),
                    contentPreview: html.substring(0, 400) + '...'
                };
            }
        """)
        
        print(f"\n📊 Progress-Anzeige Analyse:")
        print(f"   Hat Inhalt: {'✅' if progress_check.get('hasContent') else '❌'}")
        print(f"   Progress Bar: {'✅' if progress_check.get('hasProgressBar') else '❌'}")
        print(f"   Progress Container: {'✅' if progress_check.get('hasProgressContainer') else '❌'}")
        print(f"   Enhanced Loading: {'✅' if progress_check.get('hasEnhancedLoading') else '❌'}")
        print(f"   Progress Fill: {'✅' if progress_check.get('hasProgressFill') else '❌'}")
        print(f"   WebSocket Status: {'✅' if progress_check.get('hasWebSocketStatus') else '❌'}")
        
        if progress_check.get('contentPreview'):
            print(f"   Content Preview: {progress_check['contentPreview'][:200]}...")
        
        # Screenshot der Progress-Anzeige
        page.screenshot(path='/app/simple_search_progress.png')
        print(f"📸 Screenshot: /app/simple_search_progress.png")
        
        # Überwache Progress Updates
        print(f"\n⏳ Überwache Progress Updates (20 Sekunden)...")
        
        for i in range(4):  # 4 × 5 Sekunden = 20 Sekunden
            time.sleep(5)
            
            status = page.evaluate("""
                () => {
                    const resultsDiv = document.getElementById('results');
                    if (!resultsDiv) return { error: 'No results div' };
                    
                    const progressBar = resultsDiv.querySelector('.progress-fill');
                    const progressText = progressBar?.querySelector('span');
                    const wsStatus = resultsDiv.querySelector('[id^="ws-status-"]');
                    const operation = resultsDiv.querySelector('[id^="current-operation-"]');
                    
                    return {
                        progressWidth: progressBar?.style.width || 'N/A',
                        progressText: progressText?.textContent || 'N/A',
                        wsStatus: wsStatus?.textContent?.substring(0, 30) + '...' || 'N/A',
                        currentOperation: operation?.textContent?.substring(0, 40) + '...' || 'N/A',
                        hasResults: resultsDiv.innerHTML.includes('Mine gefunden') || resultsDiv.innerHTML.includes('search_results'),
                        isStillLoading: resultsDiv.innerHTML.includes('enhanced-loading-container')
                    };
                }
            """)
            
            print(f"   📊 Update {i+1}: Width={status['progressWidth']} | Text={status['progressText']} | Status={status['wsStatus']} | Op={status['currentOperation']}")
            
            # Wenn Ergebnisse da sind, beende
            if status['hasResults']:
                print(f"   ✅ Search abgeschlossen - Ergebnisse gefunden!")
                break
            elif not status['isStillLoading']:
                print(f"   ⚠️  Loading beendet, aber keine Ergebnisse sichtbar")
                break
        
        # Final Check
        final_status = page.evaluate("""
            () => {
                const resultsDiv = document.getElementById('results');
                const html = resultsDiv?.innerHTML || '';
                
                return {
                    hasResults: html.includes('Mine gefunden') || html.includes('search_results') || html.includes('Suchergebnisse'),
                    hasError: html.includes('Fehler') || html.includes('Error'),
                    stillLoading: html.includes('enhanced-loading-container'),
                    contentLength: html.length,
                    finalContent: html.substring(0, 300) + '...'
                };
            }
        """)
        
        print(f"\n📋 Final Status:")
        print(f"   Hat Ergebnisse: {'✅' if final_status['hasResults'] else '❌'}")
        print(f"   Hat Fehler: {'❌' if final_status['hasError'] else '✅'}")
        print(f"   Noch Loading: {'⚠️' if final_status['stillLoading'] else '✅'}")
        print(f"   Content Länge: {final_status['contentLength']} Zeichen")
        
        # Final Screenshot
        page.screenshot(path='/app/simple_search_final.png')
        print(f"📸 Final Screenshot: /app/simple_search_final.png")
        
        browser.close()
    
    print(f"\n" + "=" * 50)
    print(f"🎯 SIMPLE SEARCH PROGRESS TEST ABGESCHLOSSEN")

if __name__ == "__main__":
    test_simple_search_progress()