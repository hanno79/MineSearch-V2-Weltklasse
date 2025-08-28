#!/usr/bin/env python3
"""
Provider Status UI Test - Prüft ob das Frontend die Provider-Status-Informationen korrekt anzeigt
"""
import asyncio
from playwright.async_api import async_playwright
import time

async def test_provider_status_ui():
    print("🧪 TEST: Provider Status Frontend Integration")
    print("=" * 60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        page = await browser.new_page()
        
        # Gehe zur Hauptseite
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state('networkidle')
        
        # Warte bis Progressive Model Selection geladen ist
        await page.wait_for_selector('#model-selection', timeout=10000)
        
        # Erwarte Provider-Status-Informationen in der Konsole
        await page.wait_for_timeout(3000)
        
        # Prüfe ob verfügbare und nicht verfügbare Modelle unterschiedlich angezeigt werden
        print("🔍 Prüfe Model-Cards...")
        
        # Zähle verfügbare vs nicht verfügbare Modelle
        available_cards = await page.locator('.model-card.model-available').count()
        unavailable_cards = await page.locator('.model-card.model-unavailable').count()
        
        print(f"✅ Verfügbare Modelle in UI: {available_cards}")
        print(f"❌ Nicht verfügbare Modelle in UI: {unavailable_cards}")
        
        # Prüfe ob disabled checkboxes korrekt sind
        disabled_checkboxes = await page.locator('input[type="checkbox"]:disabled').count()
        print(f"🚫 Deaktivierte Checkboxes: {disabled_checkboxes}")
        
        # Prüfe auf Error-Messages
        error_messages = await page.locator('.error-message').count()
        print(f"⚠️  Error-Messages: {error_messages}")
        
        # Teste Smart-Selection nur für verfügbare Modelle
        print("\n🎯 Teste Smart Selection...")
        await page.click('[data-selection-type="all"]')
        await page.wait_for_timeout(2000)
        
        selected_count = await page.locator('input[type="checkbox"]:checked').count()
        print(f"✅ Nach 'Alle' Selection: {selected_count} Modelle ausgewählt")
        
        # Prüfe dass keine deaktivierten Modelle ausgewählt wurden
        selected_disabled = await page.locator('input[type="checkbox"]:checked:disabled').count()
        print(f"🚫 Deaktivierte aber ausgewählte: {selected_disabled}")
        
        if selected_disabled == 0:
            print("✅ ERFOLGREICH: Keine deaktivierten Modelle wurden ausgewählt")
        else:
            print("❌ FEHLER: Deaktivierte Modelle wurden ausgewählt")
        
        # Screenshot machen
        await page.screenshot(path='/app/provider_status_test.png')
        print("📸 Screenshot gespeichert: provider_status_test.png")
        
        print("\n🎉 Provider Status UI Test abgeschlossen!")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_provider_status_ui())