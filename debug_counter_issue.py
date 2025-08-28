#!/usr/bin/env python3
"""
Author: rahn  
Datum: 23.08.2025
Version: 1.0
Beschreibung: Erweiterte Debugging für Counter-Issue mit Event Monitoring
"""

import asyncio
from playwright.async_api import async_playwright
import sys
import time

async def debug_counter_issue():
    browser = None  # Initialize browser variable at function scope
    async with async_playwright() as p:
        try:
            # Browser starten 
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            print("🌐 Opening MineSearch frontend...")
            await page.goto("http://localhost:8000/static/index.html")
            
            # Warte auf vollständiges Laden
            print("⏳ Waiting for Progressive Model Selection to load...")
            await asyncio.sleep(5)
            
            # Monitor ALL JavaScript activity that modifies the counter
            print("🔍 Setting up comprehensive console monitoring...")
            
            def enhanced_console_monitor(msg):
                text = msg.text
                # Log all counter-related activity
                if any(keyword in text for keyword in ["selected-count", "updateSelection", "MODEL-UX", "SEARCH-JS"]):
                    print(f"[JS-MONITOR] {text}")
                # Log any DOM manipulation
                if "textContent" in text or "innerHTML" in text:
                    print(f"[DOM-MONITOR] {text}")
                    
            page.on("console", enhanced_console_monitor)
            
            # Inject JavaScript to monitor DOM changes on counter element
            await page.evaluate("""
                const counterElement = document.getElementById('selected-count');
                if (counterElement) {
                    // Monitor all changes to the counter element
                    const observer = new MutationObserver((mutations) => {
                        mutations.forEach((mutation) => {
                            if (mutation.type === 'childList' || mutation.type === 'characterData') {
                                console.log('🔍 [DOM-MUTATION] Counter changed to:', counterElement.textContent, 'by:', new Error().stack.split('\\n')[2]);
                            }
                        });
                    });
                    observer.observe(counterElement, { childList: true, characterData: true, subtree: true });
                    
                    // Override textContent setter to track changes
                    let originalTextContent = Object.getOwnPropertyDescriptor(Node.prototype, 'textContent');
                    Object.defineProperty(counterElement, 'textContent', {
                        get: originalTextContent.get,
                        set: function(value) {
                            console.log('🔍 [COUNTER-SET] Setting counter to:', value, 'from:', new Error().stack.split('\\n')[2]);
                            return originalTextContent.set.call(this, value);
                        }
                    });
                    
                    console.log('🔍 [MONITORING] Counter monitoring activated');
                } else {
                    console.log('❌ [MONITORING] Counter element not found');
                }
            """)
            
            await asyncio.sleep(2)
            
            # Test: Klicke auf "Kostenlos" Kategorie
            print("\n🧪 ENHANCED TEST: Clicking 'Kostenlos' category...")
            free_pill = await page.query_selector('.smart-selection[data-selection-type="free"]')
            
            if free_pill:
                await free_pill.click()
                print("⏱️ Waiting 5 seconds to observe all counter changes...")
                await asyncio.sleep(5)
                
                # Prüfe Counter-Status
                count_element = await page.query_selector('#selected-count')
                if count_element:
                    count_value = await count_element.inner_text()
                    print(f"📊 Final counter value: {count_value}")
                    
                # Prüfe auch Progressive Model Selection Status
                selection_status = await page.evaluate("""
                    if (window.progressiveModelSelection && window.progressiveModelSelection.selectedModels) {
                        return {
                            exists: true,
                            size: window.progressiveModelSelection.selectedModels.size,
                            models: Array.from(window.progressiveModelSelection.selectedModels)
                        };
                    }
                    return { exists: false };
                """)
                
                print(f"📊 Progressive Model Selection Status: {selection_status}")
                
            else:
                print("❌ 'Kostenlos' category pill not found")
                
            print("\n✅ Enhanced debug completed!")
            await asyncio.sleep(3)
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if browser is not None:
                await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_counter_issue())