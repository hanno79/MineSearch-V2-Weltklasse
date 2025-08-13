#!/usr/bin/env python3
"""
Author: rahn
Datum: 12.08.2025
Version: 1.0
Beschreibung: Comprehensive Tab System End-to-End Test für MineSearch 2.0
"""

import asyncio
from playwright.async_api import async_playwright

async def test_minesearch_tab_system():
    """Comprehensive test für das MineSearch 2.0 Tab-System"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        page = await browser.new_page()
        
        try:
            print("🧪 === MINESEARCH 2.0 TAB-SYSTEM TEST ===")
            
            # 1. SEITENAUFRUF
            print("\n📱 Lade MineSearch 2.0...")
            await page.goto("http://localhost:8000/static/index.html")
            await page.wait_for_load_state('networkidle')
            
            await page.wait_for_selector('.tab-navigation', timeout=10000)
            print("✅ MineSearch 2.0 geladen")
            
            # 2. PRÜFE STANDARD-ZUSTAND
            print("\n🔍 Prüfe Standard-Tab-Zustand...")
            single_visible = await page.locator('#single-search').is_visible()
            others_hidden = await page.evaluate("""
                () => {
                    const tabs = ['#csv-upload', '#sources', '#statistics', '#consolidated'];
                    return tabs.every(id => !document.querySelector(id).classList.contains('active'));
                }
            """)
            
            if single_visible and others_hidden:
                print("✅ NUR Single-Search Tab sichtbar (korrekt)")
            else:
                print("❌ Mehrere Tabs gleichzeitig sichtbar!")
                
            # 3. TESTE SOURCES TAB
            print("\n📚 Teste Sources Tab...")
            await page.locator('#sources-tab').click()
            await page.wait_for_timeout(3000)
            
            sources_visible = await page.locator('#sources').is_visible()
            single_hidden = await page.evaluate("() => !document.querySelector('#single-search').classList.contains('active')")
            
            if sources_visible and single_hidden:
                print("✅ Sources Tab aktiv, Single Tab versteckt")
                await page.wait_for_timeout(2000) # Warte auf API-Calls
            else:
                print("❌ Sources Tab-Wechsel fehlgeschlagen")
                
            # 4. TESTE STATISTICS TAB  
            print("\n📈 Teste Statistics Tab...")
            await page.locator('#statistics-tab').click()
            await page.wait_for_timeout(3000)
            
            stats_visible = await page.locator('#statistics').is_visible()
            if stats_visible:
                print("✅ Statistics Tab aktiv")
                await page.wait_for_timeout(2000)
            else:
                print("❌ Statistics Tab-Wechsel fehlgeschlagen")
                
            # 5. TESTE CONSOLIDATED TAB
            print("\n📋 Teste Consolidated Tab...")
            await page.locator('#consolidated-tab').click()
            await page.wait_for_timeout(3000)
            
            consolidated_visible = await page.locator('#consolidated').is_visible()
            if consolidated_visible:
                print("✅ Consolidated Tab aktiv")
                await page.wait_for_timeout(2000)
            else:
                print("❌ Consolidated Tab-Wechsel fehlgeschlagen")
                
            # 6. ZURÜCK ZUM SINGLE TAB
            print("\n🔍 Zurück zum Single Tab...")
            await page.locator('#single-tab').click()
            await page.wait_for_timeout(1000)
            
            final_single_visible = await page.locator('#single-search').is_visible()
            if final_single_visible:
                print("✅ Zurück zum Single Tab erfolgreich")
            else:
                print("❌ Single Tab Rückkehr fehlgeschlagen")
                
            # SCREENSHOT
            await page.screenshot(path='/app/tab_system_test_result.png', full_page=True)
            print("📸 Screenshot gespeichert: tab_system_test_result.png")
            
            print("\n🎉 === TAB-SYSTEM TEST ABGESCHLOSSEN ===")
            
        except Exception as e:
            print(f"❌ TEST FEHLER: {e}")
            await page.screenshot(path='/app/tab_system_error.png')
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_minesearch_tab_system())