#!/usr/bin/env python3
"""
Browser test for provider categorization fix
"""

from playwright.sync_api import sync_playwright
import time

def test_provider_categories():
    with sync_playwright() as p:
        print("🔍 TESTE PROVIDER-KATEGORISIERUNG IM BROWSER")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            # Navigate to frontend
            print("📍 Navigiere zu Frontend...")
            page.goto("http://localhost:8000", wait_until="networkidle", timeout=10000)
            page.wait_for_timeout(3000)  # Allow time for JS to load
            
            # Take screenshot before interaction
            print("📸 Screenshot vor Interaktion...")
            page.screenshot(path="provider_test_before.png")
            
            # Look for quick selection buttons
            print("🔍 Suche Quick Selection Buttons...")
            buttons = page.locator(".quick-select-provider").all()
            
            print(f"Gefundene Provider-Buttons: {len(buttons)}")
            
            # List all provider buttons found
            for i, button in enumerate(buttons):
                try:
                    text = button.inner_text()
                    print(f"  {i+1}. {text}")
                except:
                    print(f"  {i+1}. [Button ohne Text]")
            
            # Check if we see the expected providers
            expected_providers = [
                "OpenRouter", "Anthropic", "OpenAI", "Google Gemini", 
                "xAI Grok", "Perplexity", "Abacus AI", "Tavily", 
                "Exa", "ScrapingBee", "Firecrawl", "BrightData"
            ]
            
            print(f"\n🎯 Erwartete Provider: {len(expected_providers)}")
            found_providers = []
            
            for expected in expected_providers:
                try:
                    button = page.locator(f"text={expected}").first
                    if button.is_visible(timeout=1000):
                        found_providers.append(expected)
                        print(f"  ✅ {expected}: Gefunden")
                    else:
                        print(f"  ❌ {expected}: Nicht sichtbar")
                except:
                    print(f"  ❌ {expected}: Nicht gefunden")
            
            # Take final screenshot
            print("📸 Screenshot nach Test...")
            page.screenshot(path="provider_test_result.png")
            
            print(f"\n📊 ERGEBNIS:")
            print(f"   Gefundene Provider: {len(found_providers)}/{len(expected_providers)}")
            print(f"   Erfolgsrate: {(len(found_providers)/len(expected_providers)*100):.1f}%")
            
            if len(found_providers) >= 8:  # Erwarten mindestens 8 der 11 Provider
                print("   ✅ PROVIDER-KATEGORISIERUNG ERFOLGREICH")
            else:
                print("   ❌ PROVIDER-KATEGORISIERUNG FEHLGESCHLAGEN")
            
            # Keep browser open for inspection
            print("\n🔍 Halte Browser 15 Sekunden für Inspektion offen...")
            time.sleep(15)
            
        except Exception as e:
            print(f"❌ Test-Fehler: {e}")
            page.screenshot(path="provider_test_error.png")
        
        finally:
            browser.close()

if __name__ == "__main__":
    test_provider_categories()