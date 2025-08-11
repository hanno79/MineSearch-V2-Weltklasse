#!/usr/bin/env python3
"""
Author: rahn
Datum: 11.08.2025
Version: 1.0
Beschreibung: Validierung dass deprecated Modelle aus dem UI entfernt sind
"""

import asyncio
from playwright.async_api import async_playwright

async def validate_models_removed():
    """Validiert dass deprecated Modelle nicht mehr im Frontend verfügbar sind"""
    
    async with async_playwright() as p:
        print("🔍 [VALIDATION] Validiere deprecated Modelle im Frontend...")
        
        browser = await p.chromium.launch(headless=False, slow_mo=300)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # Lade MineSearch UI
            print("📱 [VALIDATION] Lade http://localhost:8000...")
            await page.goto('http://localhost:8000')
            await page.wait_for_load_state('domcontentloaded')
            await page.wait_for_timeout(3000)
            
            # Warte auf Modell-Auswahl
            print("⏳ [VALIDATION] Warte auf Modell-Auswahl...")
            await page.wait_for_selector('input[name="model"]', timeout=10000)
            
            # Hole alle verfügbaren Modelle aus dem UI
            model_elements = await page.query_selector_all('input[name="model"]')
            print(f"📊 [VALIDATION] {len(model_elements)} Modelle im UI gefunden")
            
            # Extrahiere Modell-IDs und Namen
            available_models = []
            deprecated_found = []
            
            for element in model_elements:
                value = await element.get_attribute('value')
                # Hole auch Label-Text
                label_element = await page.query_selector(f'label[for="{await element.get_attribute("id")}"]')
                label_text = await label_element.text_content() if label_element else "N/A"
                
                available_models.append({
                    'id': value,
                    'label': label_text.strip()
                })
                
                # Prüfe auf deprecated Modelle
                deprecated_keywords = ['grok-2', 'grok-2-mini', 'grok-beta', 'grok-vision-beta', 'horizon-beta']
                if any(dep in value for dep in deprecated_keywords):
                    deprecated_found.append(value)
            
            print(f"\n📋 [VALIDATION] VERFÜGBARE MODELLE ({len(available_models)}):")
            
            # Gruppiere nach Provider
            providers = {}
            for model in available_models:
                provider = model['id'].split(':')[0] if ':' in model['id'] else 'unknown'
                if provider not in providers:
                    providers[provider] = []
                providers[provider].append(model)
            
            for provider, models in sorted(providers.items()):
                print(f"  🔧 {provider.upper()}: {len(models)} Modelle")
                for model in sorted(models, key=lambda x: x['id']):
                    print(f"    - {model['id']}: {model['label']}")
            
            # Validierung
            print(f"\n🔍 [VALIDATION] DEPRECATED-MODELLE PRÜFUNG:")
            if deprecated_found:
                print(f"❌ DEPRECATED MODELLE IM UI GEFUNDEN:")
                for dep_model in deprecated_found:
                    print(f"  - {dep_model}")
                return False
            else:
                print("✅ KEINE DEPRECATED MODELLE IM UI GEFUNDEN")
                
            # Grok-spezifische Validierung
            grok_models = [m for m in available_models if 'grok:' in m['id']]
            print(f"\n🚀 [VALIDATION] GROK-MODELLE ({len(grok_models)}):")
            for model in grok_models:
                print(f"  ✅ {model['id']}: {model['label']}")
                
            expected_grok = ['grok:grok-4', 'grok:grok-3', 'grok:grok-3-mini', 'grok:grok-3-fast']
            found_grok = [m['id'] for m in grok_models]
            
            if set(found_grok) == set(expected_grok):
                print("✅ GROK-MODELLE KORREKT: Nur erwartete Modelle verfügbar")
                return True
            else:
                missing = set(expected_grok) - set(found_grok)
                extra = set(found_grok) - set(expected_grok)
                if missing:
                    print(f"❌ FEHLENDE GROK-MODELLE: {list(missing)}")
                if extra:
                    print(f"❌ UNERWARTETE GROK-MODELLE: {list(extra)}")
                return False
                
        except Exception as e:
            print(f"❌ [VALIDATION] Fehler: {e}")
            await page.screenshot(path='/app/validation_error.png')
            return False
            
        finally:
            await browser.close()

async def main():
    """Hauptfunktion"""
    print("🎯 DEPRECATED MODELLE VALIDATION")
    print("=" * 50)
    
    success = await validate_models_removed()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 VALIDATION ERFOLGREICH!")
        print("   ✅ Alle deprecated Modelle entfernt")
        print("   ✅ Frontend zeigt nur aktive Modelle")
        print("   ✅ Grok-Modelle korrekt (nur 3/4-Generation)")
    else:
        print("❌ VALIDATION FEHLGESCHLAGEN!")
        print("   ❌ Deprecated Modelle noch im System")
    
    print("=" * 50)
    return success

if __name__ == '__main__':
    result = asyncio.run(main())
    exit(0 if result else 1)