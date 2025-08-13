#!/usr/bin/env python3
"""
Author: rahn
Datum: 12.08.2025
Version: 1.0
Beschreibung: Validierung des Tab-Systems nach PHASE 3 UI/UX Revolution
"""

import asyncio
from playwright.async_api import async_playwright
import time

async def test_tab_system():
    print("🧪 [TAB-TEST] Starte Tab-System Validierung...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            # Öffne MineSearch 2.0
            print("🌐 [TAB-TEST] Öffne MineSearch 2.0...")
            await page.goto("http://localhost:8000")
            await page.wait_for_load_state('networkidle', timeout=10000)
            
            # Warte auf Tab-System-Initialization
            await page.wait_for_timeout(2000)
            
            print("📋 [TAB-TEST] Teste Tab-Navigation...")
            
            # Test 1: Einzelsuche-Tab (Standard)
            single_tab = await page.locator('#single-search').is_visible()
            print(f"🔍 [TAB-TEST] Einzelsuche-Tab sichtbar: {'✅' if single_tab else '❌'}")
            
            # Test 2: CSV-Tab aktivieren
            print("📊 [TAB-TEST] Aktiviere CSV-Tab...")
            await page.click('#csv-tab')
            await page.wait_for_timeout(1000)
            
            csv_visible = await page.locator('#csv-upload').is_visible()
            single_hidden = not await page.locator('#single-search').is_visible()
            print(f"📊 [TAB-TEST] CSV-Tab sichtbar: {'✅' if csv_visible else '❌'}")
            print(f"🔍 [TAB-TEST] Einzelsuche-Tab versteckt: {'✅' if single_hidden else '❌'}")
            
            # Test 3: Quellen-Tab aktivieren  
            print("📚 [TAB-TEST] Aktiviere Quellen-Tab...")
            await page.click('#sources-tab')
            await page.wait_for_timeout(2000)  # Mehr Zeit für Quellen-Loading
            
            sources_visible = await page.locator('#sources').is_visible()
            csv_hidden = not await page.locator('#csv-upload').is_visible()
            print(f"📚 [TAB-TEST] Quellen-Tab sichtbar: {'✅' if sources_visible else '❌'}")
            print(f"📊 [TAB-TEST] CSV-Tab versteckt: {'✅' if csv_hidden else '❌'}")
            
            # Test 4: Statistiken-Tab aktivieren
            print("📈 [TAB-TEST] Aktiviere Statistiken-Tab...")
            await page.click('#statistics-tab')
            await page.wait_for_timeout(2000)
            
            stats_visible = await page.locator('#statistics').is_visible()
            sources_hidden = not await page.locator('#sources').is_visible()
            print(f"📈 [TAB-TEST] Statistiken-Tab sichtbar: {'✅' if stats_visible else '❌'}")
            print(f"📚 [TAB-TEST] Quellen-Tab versteckt: {'✅' if sources_hidden else '❌'}")
            
            # Test 5: Konsolidiert-Tab aktivieren
            print("📋 [TAB-TEST] Aktiviere Konsolidiert-Tab...")
            await page.click('#consolidated-tab')
            await page.wait_for_timeout(2000)
            
            consolidated_visible = await page.locator('#consolidated').is_visible()
            stats_hidden = not await page.locator('#statistics').is_visible()
            print(f"📋 [TAB-TEST] Konsolidiert-Tab sichtbar: {'✅' if consolidated_visible else '❌'}")
            print(f"📈 [TAB-TEST] Statistiken-Tab versteckt: {'✅' if stats_hidden else '❌'}")
            
            # Test 6: Zurück zu Einzelsuche
            print("🔍 [TAB-TEST] Zurück zu Einzelsuche...")
            await page.click('#single-tab')
            await page.wait_for_timeout(1000)
            
            single_visible_final = await page.locator('#single-search').is_visible()
            consolidated_hidden = not await page.locator('#consolidated').is_visible()
            print(f"🔍 [TAB-TEST] Einzelsuche-Tab sichtbar: {'✅' if single_visible_final else '❌'}")
            print(f"📋 [TAB-TEST] Konsolidiert-Tab versteckt: {'✅' if consolidated_hidden else '❌'}")
            
            # Zusammenfassung
            all_tests_passed = all([
                single_tab, csv_visible, single_hidden, sources_visible, csv_hidden,
                stats_visible, sources_hidden, consolidated_visible, stats_hidden,
                single_visible_final, consolidated_hidden
            ])
            
            print("\n" + "="*50)
            print("🎯 [TAB-TEST] ZUSAMMENFASSUNG:")
            print("="*50)
            print(f"✅ Tab-Navigation funktional: {'JA' if all_tests_passed else 'NEIN'}")
            print(f"🔄 Tab-Switching Logic: {'OK' if all_tests_passed else 'FEHLERHAFT'}")
            print(f"🎨 CSS Tab-Sichtbarkeit: {'OK' if all_tests_passed else 'FEHLERHAFT'}")
            
            if all_tests_passed:
                print("🎉 [TAB-TEST] PHASE 3 TAB-REVOLUTION ERFOLGREICH!")
                print("   Alle Tabs funktionieren korrekt - nur aktiver Tab sichtbar")
            else:
                print("⚠️ [TAB-TEST] Tab-System benötigt weitere Anpassungen")
                
        except Exception as e:
            print(f"❌ [TAB-TEST] Fehler: {str(e)}")
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_tab_system())