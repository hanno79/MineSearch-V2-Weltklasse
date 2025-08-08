#!/usr/bin/env python3
"""
Author: rahn
Datum: 07.08.2025
Version: 1.0
Beschreibung: Sehr einfacher Test - nur onclick Attribut und JavaScript prüfen
"""

import asyncio
from playwright.async_api import async_playwright

async def simple_onclick_test():
    """Sehr einfacher Test: Nur onclick Attribut prüfen und JavaScript ausführen"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=500)
        page = await browser.new_page()
        
        console_errors = []
        page.on('console', lambda msg: console_errors.append(msg.text) if msg.type == 'error' else None)
        
        try:
            print("🧪 EINFACHER ONCLICK TEST")
            print("=" * 40)
            
            # 1. Lade Seite
            await page.goto('http://localhost:8000')
            await page.wait_for_load_state('networkidle')
            print("1. ✅ Seite geladen")
            
            # 2. Lade Statistics Daten direkt per JavaScript
            print("2. 🔄 Lade Statistics direkt per JavaScript...")
            
            await page.evaluate("""
                // Lade Statistics HTML direkt
                async function loadStatsDirectly() {
                    try {
                        const response = await fetch('/api/statistics/models/comprehensive');
                        const data = await response.json();
                        
                        if (data.success && data.data.models.length > 0) {
                            console.log('📊 Statistics geladen:', data.data.models.length, 'Modelle');
                            
                            // Erstelle Test HTML direkt
                            const testModel = data.data.models[0];
                            const modelId = testModel.model_id;
                            
                            console.log('🎯 Test Model ID:', modelId);
                            
                            // Erstelle Button HTML wie im echten Code
                            const buttonHTML = `
                                <button onclick="showModelDetails(${safeJSONStringify(modelId)})"
                                        id="test-details-button"
                                        style="padding: 10px; background: #3b82f6; color: white; border: none; border-radius: 4px; cursor: pointer;">
                                    📊 Test Details Button
                                </button>
                            `;
                            
                            // Füge Button zu Body hinzu
                            const container = document.createElement('div');
                            container.innerHTML = buttonHTML;
                            container.style.position = 'fixed';
                            container.style.top = '100px';
                            container.style.left = '100px';
                            container.style.zIndex = '9999';
                            container.style.background = 'white';
                            container.style.padding = '20px';
                            container.style.border = '2px solid red';
                            document.body.appendChild(container);
                            
                            console.log('✅ Test Button erstellt');
                            console.log('📋 Button onclick:', container.querySelector('button').onclick);
                            console.log('📋 Button onclick attribut:', container.querySelector('button').getAttribute('onclick'));
                            
                            return true;
                        }
                    } catch (e) {
                        console.error('❌ Fehler beim Laden:', e);
                        return false;
                    }
                }
                
                return await loadStatsDirectly();
            """)
            
            await page.wait_for_timeout(3000)
            
            # 3. Finde Test Button
            print("3. 🔍 Suche Test Button...")
            test_button = await page.query_selector('#test-details-button')
            
            if not test_button:
                print("   ❌ Test Button nicht gefunden!")
                return False
                
            print("   ✅ Test Button gefunden")
            
            # 4. Hole onclick Attribut
            onclick_attr = await test_button.get_attribute('onclick')
            print(f"   📋 Onclick Attribut: {onclick_attr}")
            
            # 5. Test Button klicken
            print("4. 🎯 Klicke Test Button...")
            console_errors.clear()
            
            await test_button.click()
            await page.wait_for_timeout(2000)
            
            # 6. Prüfe Errors
            if console_errors:
                print("   ❌ JAVASCRIPT ERRORS:")
                for error in console_errors:
                    print(f"     {error}")
                    if 'SyntaxError' in error:
                        print("     🎯 SYNTAX ERROR GEFUNDEN!")
                        
                await page.screenshot(path='/app/minesearch_v2/backend/onclick_error.png')
                return False
            else:
                print("   ✅ Keine JavaScript Errors")
            
            # 7. Screenshot
            await page.screenshot(path='/app/minesearch_v2/backend/onclick_test.png')
            print("5. 📷 Screenshot: onclick_test.png")
            
            return True
            
        except Exception as e:
            print(f"❌ Test Fehler: {e}")
            return False
            
        finally:
            await page.wait_for_timeout(3000)
            await browser.close()

if __name__ == "__main__":
    result = asyncio.run(simple_onclick_test())
    print(f"\n🎯 ONCLICK TEST: {'✅ SUCCESS' if result else '❌ FAILED'}")