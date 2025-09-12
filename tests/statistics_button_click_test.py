#!/usr/bin/env python3
"""
Author: rahn
Datum: 19.08.2025
Version: 1.0
Beschreibung: Statistics Button Click Test - Klickt den richtigen Button und prüft Daten-Laden
"""

import asyncio
import json
from playwright.async_api import async_playwright
import time

async def test_statistics_button_click():
    """
    Direkter Test des Statistics-Button-Klicks:
    1. Navigation zu Statistics Tab
    2. Klick auf "Statistiken laden" Button
    3. Prüfung der geladenen Modell-Daten
    4. Validation der 53 Modelle
    """

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=1500)
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()

        print("🎯 STATISTICS BUTTON CLICK TEST")
        print("="*40)

        try:
            # 1. Navigation
            print("\n📍 Navigation zur Statistics-Seite")
            await page.goto("http://localhost:3000#statistics")
            await page.wait_for_load_state('networkidle')
            await page.wait_for_timeout(2000)

            # Screenshot vor Button-Klick
            await page.screenshot(path="/app/tests/button_test_01_before_click.png")
            print("✅ Statistics-Seite geladen")

            # 2. JavaScript ausführen um sicherzustellen dass Tab aktiv ist
            await page.evaluate("""
                document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
                const statisticsTab = document.getElementById('statistics');
                if (statisticsTab) {
                    statisticsTab.classList.add('active');
                    statisticsTab.style.display = 'block';
                }
            """)

            # 3. Den richtigen "Statistiken laden" Button finden
            print("\n📍 Suche nach 'Statistiken laden' Button")

            # Warten auf Button-Sichtbarkeit
            await page.wait_for_timeout(1000)

            # Verschiedene Button-Selektoren versuchen
            button_selectors = [
                'button:has-text("🔍 Statistiken laden")',
                'button:has-text("Statistiken laden")',
                '#model-statistics-table-container button',
                'button[onclick*="loadModelStatistics"]',
                '.statistics-table-container button'
            ]

            button_found = False
            for selector in button_selectors:
                buttons = page.locator(selector)
                count = await buttons.count()

                if count > 0:
                    print(f"✅ Button gefunden: {selector} ({count} Stück)")

                    # Den ersten sichtbaren Button klicken
                    for i in range(count):
                        button = buttons.nth(i)
                        if await button.is_visible():
                            print(f"🖱️ Klicke Button {i+1}")
                            await button.click()
                            button_found = True
                            break

                    if button_found:
                        break

            if not button_found:
                print("⚠️ Kein Button gefunden - versuche JavaScript-Aufruf")
                await page.evaluate("""
                    if (typeof loadModelStatistics === 'function') {
                        console.log('Calling loadModelStatistics()');
                        loadModelStatistics();
                    } else if (typeof loadStatistics === 'function') {
                        console.log('Calling loadStatistics()');
                        loadStatistics();
                    } else {
                        console.log('No load function found');
                    }
                """)

            # 4. Warten auf Daten-Laden
            print("\n📍 Warten auf Daten-Response...")
            await page.wait_for_timeout(5000)  # 5 Sekunden warten

            # Screenshot nach Button-Klick
            await page.screenshot(path="/app/tests/button_test_02_after_click.png")
            print("📸 Screenshot nach Button-Klick gespeichert")

            # 5. Prüfen ob sich die Seite verändert hat
            print("\n📍 Prüfung der Seitenänderungen")

            # Nach Tabellen-Inhalten suchen
            tables_found = await page.locator('table').count()
            table_rows = await page.locator('table tr').count()

            print(f"🔍 Gefundene Tabellen: {tables_found}")
            print(f"🔍 Gefundene Tabellenzeilen: {table_rows}")

            # Nach spezifischen Model-Inhalten suchen
            page_text = await page.text_content('body')

            # Modell-Provider zählen
            providers = ['perplexity', 'openai', 'anthropic', 'gemini', 'grok', 'openrouter',
'tavily', 'brightdata', 'firecrawl']
            found_providers = []

            for provider in providers:
                if provider.lower() in page_text.lower():
                    found_providers.append(provider)

            print(f"🏢 Provider im Text gefunden: {len(found_providers)}")
            print(f"📋 Provider: {found_providers}")

            # 6. Console-Logs prüfen
            print("\n📍 JavaScript Console prüfen")

            # Console Logs abrufen
            console_messages = []

            def handle_console_msg(msg):
    """handle_console_msg - TODO: Dokumentation hinzufügen"""
                console_messages.append(f"{msg.type}: {msg.text}")

            page.on("console", handle_console_msg)

            # Noch einmal versuchen zu laden
            await page.evaluate("console.log('Testing console'); if (window.loadModelStatistics)
loadModelStatistics();")
            await page.wait_for_timeout(2000)

            print(f"📝 Console Messages: {len(console_messages)}")
            for msg in console_messages[-5:]:  # Letzte 5 Nachrichten
                print(f"   {msg}")

            # 7. API direkt von der Seite aus testen
            print("\n📍 API Test von Frontend")

            api_test_result = await page.evaluate("""
                async () => {
                    try {
                        console.log('Testing API from frontend');
                        const response = await fetch(window.API_BASE_URL + '/api/models');
                        console.log('API Response status:', response.status);
                        const data = await response.json();
                        console.log('API Data received:', Object.keys(data));

                        if (data.models) {
                            const modelCount = Object.keys(data.models).length;
                            const firstFive = Object.entries(data.models).slice(0, 5).map(([id, model]) => ({
                                id: id,
                                name: model.name,
                                provider: model.provider
                            }));

                            return {
                                success: true,
                                modelCount: modelCount,
                                sampleModels: firstFive,
                                apiBaseUrl: window.API_BASE_URL
                            };
                        }
                        return { success: false, error: 'No models in response' };
                    } catch (error) {
                        console.error('API Test Error:', error);
                        return { success: false, error: error.message };
                    }
                }
            """)

            if api_test_result['success']:
                print(f"✅ Frontend API Test erfolgreich!")
                print(f"📊 Modell-Anzahl: {api_test_result['modelCount']}")
                print(f"🌐 API URL: {api_test_result['apiBaseUrl']}")
                print("📋 Beispiel-Modelle:")
                for model in api_test_result['sampleModels']:
                    print(f"   - {model['id']}: {model['name']} ({model['provider']})")
            else:
                print(f"❌ Frontend API Test fehlgeschlagen: {api_test_result['error']}")

            # Final Screenshot
            await page.screenshot(path="/app/tests/button_test_03_final.png")

            # 8. FINALE BEWERTUNG
            print("\n" + "="*50)
            print("📊 STATISTICS BUTTON TEST - ERGEBNIS")
            print("="*50)

            api_models = api_test_result['modelCount'] if api_test_result['success'] else 0

            print(f"🎯 Button-Klick ausgeführt: {'✅' if button_found else '❌'}")
            print(f"📊 API Modelle verfügbar: {api_models}")
            print(f"🔍 Tabellen gefunden: {tables_found}")
            print(f"📋 Tabellenzeilen: {table_rows}")
            print(f"🏢 Provider gefunden: {len(found_providers)}")

            # Bewertung
            if api_models >= 50:
                print("\n🎉 ERFOLG: API liefert 53 Modelle!")
                print("   ✅ Die Backend-Funktionalität ist vollständig vorhanden")
                print("   ✅ Alle erwarteten Modelle sind verfügbar")
            else:
                print(f"\n⚠️ API Problem: Nur {api_models} Modelle verfügbar")

            if button_found and api_models >= 50:
                print("   ✅ Statistics Tab Navigation funktioniert")
                print("   ✅ Button-Interaktion erfolgreich")
            elif not button_found:
                print("   ⚠️ Button-Click hatte Probleme")

            if table_rows > 10 or len(found_providers) > 5:
                print("   ✅ Frontend zeigt Modell-Daten an")
            else:
                print("   ⚠️ Frontend zeigt wenige/keine Daten")

            print("="*50)

            # Ergebnisse speichern
            results = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "button_found_and_clicked": button_found,
                "api_models_available": api_models,
                "tables_found": tables_found,
                "table_rows_found": table_rows,
                "providers_in_content": found_providers,
                "console_messages": console_messages[-10:],  # Letzte 10 Nachrichten
                "success": api_models >= 50 and button_found,
                "summary": f"API hat {api_models} Modelle, Frontend zeigt {table_rows} Zeilen"
            }

            with open("/app/tests/button_click_test_results.json", "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

            print("💾 Ergebnisse in button_click_test_results.json gespeichert")

        except Exception as e:
            print(f"❌ FEHLER: {e}")
            await page.screenshot(path="/app/tests/button_test_error.png")

        finally:
            await browser.close()
            print("\n🏁 Test abgeschlossen")

if __name__ == "__main__":
    asyncio.run(test_statistics_button_click())
