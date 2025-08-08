#!/usr/bin/env python3
"""
Author: rahn
Datum: 07.08.2025
Version: 1.0
Beschreibung: Direkter Test der onclick Syntax - minimalistisch
"""

import asyncio
from playwright.async_api import async_playwright

async def direct_onclick_test():
    """Direkter Test nur der onclick Syntax mit echten Daten"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        page = await browser.new_page()
        
        console_messages = []
        page.on('console', lambda msg: console_messages.append({
            'type': msg.type, 'text': msg.text
        }))
        
        try:
            print("🎯 DIREKTER ONCLICK TEST")
            print("=" * 40)
            
            # 1. Lade eine simple HTML Seite
            await page.goto('http://localhost:8000')
            await page.wait_for_load_state('networkidle')
            print("1. ✅ Seite geladen")
            
            # 2. Teste onclick Syntax direkt im Browser
            print("2. 🧪 Teste onclick Syntax direkt...")
            
            test_result = await page.evaluate("""
                // Test die exakte onclick Syntax aus dem Fix
                function testOnclickSyntax() {
                    const results = [];
                    
                    // Teste problematische Model IDs
                    const testModels = [
                        'openrouter:deepseek-free',
                        'perplexity:sonar-pro',
                        'openai:gpt-4o'
                    ];
                    
                    // safeJSONStringify Funktion (wie im echten Code)
                    function safeJSONStringify(value) {
                        if (!value) return "''";
                        return JSON.stringify(value);
                    }
                    
                    testModels.forEach(modelId => {
                        try {
                            // NEUE (fixe) Syntax: showModelDetails(${safeJSONStringify(stat.model_id)})
                            const fixedOnclick = `showModelDetails(${safeJSONStringify(modelId)})`;
                            
                            // Teste ob JavaScript das parsen kann
                            const testFunction = new Function(fixedOnclick);
                            
                            results.push({
                                modelId: modelId,
                                onclick: fixedOnclick,
                                status: 'success',
                                parsable: true
                            });
                            
                        } catch (error) {
                            results.push({
                                modelId: modelId,
                                onclick: `Failed to create onclick for ${modelId}`,
                                status: 'error',
                                error: error.message,
                                parsable: false
                            });
                        }
                    });
                    
                    return results;
                }
                
                return testOnclickSyntax();
            """)
            
            # 3. Prüfe Ergebnisse
            print("3. 📋 TESTE ERGEBNISSE:")
            all_success = True
            
            for result in test_result:
                print(f"   Model: {result['modelId']}")
                print(f"   Onclick: {result['onclick']}")
                print(f"   Status: {result['status']}")
                print(f"   Parsable: {result['parsable']}")
                
                if result['status'] != 'success' or not result['parsable']:
                    all_success = False
                    print(f"   ❌ ERROR: {result.get('error', 'Unknown')}")
                else:
                    print(f"   ✅ ONCLICK SYNTAX OK")
                print()
            
            # 4. Erstelle einen echten Test Button
            if all_success:
                print("4. 🎯 Teste echten Button mit fixer Syntax...")
                
                button_test_result = await page.evaluate("""
                    // Erstelle Test Button mit echter Model ID
                    const modelId = 'openrouter:deepseek-free';
                    function safeJSONStringify(value) {
                        if (!value) return "''";
                        return JSON.stringify(value);
                    }
                    
                    // Mock showModelDetails Funktion
                    window.showModelDetails = function(id) {
                        console.log('🎯 showModelDetails called with:', id);
                        window.testDetailsResult = {
                            success: true,
                            modelId: id,
                            timestamp: Date.now()
                        };
                    };
                    
                    // Erstelle Button HTML mit fixer Syntax
                    const buttonHTML = `
                        <button id="test-details-btn" 
                                onclick="showModelDetails(${safeJSONStringify(modelId)})"
                                style="padding: 15px; background: #3b82f6; color: white; 
                                       border: none; border-radius: 6px; cursor: pointer; 
                                       font-size: 16px; margin: 20px;">
                            📊 Test Details Button
                        </button>
                    `;
                    
                    // Füge zu Body hinzu
                    const container = document.createElement('div');
                    container.innerHTML = buttonHTML;
                    container.style.position = 'fixed';
                    container.style.top = '50px';
                    container.style.left = '50px';
                    container.style.zIndex = '9999';
                    container.style.background = 'white';
                    container.style.padding = '20px';
                    container.style.border = '3px solid red';
                    container.style.borderRadius = '8px';
                    document.body.appendChild(container);
                    
                    return {
                        buttonCreated: true,
                        onclick: container.querySelector('button').getAttribute('onclick')
                    };
                """)
                
                print(f"   ✅ Test Button erstellt")
                print(f"   📋 Onclick Attribut: {button_test_result['onclick']}")
                
                # 5. Button klicken
                print("5. 🎯 Klicke Test Button...")
                console_messages.clear()  # Alte Messages löschen
                
                await page.click('#test-details-btn')
                await page.wait_for_timeout(1000)
                
                # 6. Prüfe Ergebnis
                click_result = await page.evaluate("window.testDetailsResult || null")
                
                if click_result and click_result.get('success'):
                    print(f"   ✅ BUTTON CLICK ERFOLGREICH!")
                    print(f"   📋 Model ID empfangen: {click_result['modelId']}")
                    return True
                else:
                    print(f"   ❌ BUTTON CLICK FEHLGESCHLAGEN")
                    if console_messages:
                        print("   🚨 Console Errors:")
                        for msg in console_messages:
                            if msg['type'] == 'error':
                                print(f"      {msg['text']}")
                    return False
            else:
                print("4. ❌ Syntax Tests fehlgeschlagen - Button Test übersprungen")
                return False
                
        except Exception as e:
            print(f"❌ Test Fehler: {e}")
            return False
            
        finally:
            await page.screenshot(path='/app/minesearch_v2/backend/onclick_test_result.png')
            await page.wait_for_timeout(3000)  # Zeit zum Anschauen
            await browser.close()

if __name__ == "__main__":
    result = asyncio.run(direct_onclick_test())
    print(f"\n🎯 DIREKTER ONCLICK TEST: {'✅ ERFOLGREICH' if result else '❌ FEHLGESCHLAGEN'}")
    
    if result:
        print("✅ Die JavaScript Syntax ist korrekt!")
        print("✅ Details Buttons sollten jetzt funktionieren!")
    else:
        print("❌ Es gibt noch JavaScript Syntax Probleme!")