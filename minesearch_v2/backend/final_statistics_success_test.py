"""
Author: rahn
Datum: 07.08.2025
Version: 1.0
Beschreibung: Finaler Erfolgstest für reparierte Statistik-Funktionalität
"""

import asyncio
import json
from datetime import datetime
from playwright.async_api import async_playwright
import requests

class FinalStatisticsSuccessTest:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.success_report = {
            "timestamp": datetime.now().isoformat(),
            "test_name": "Final Statistics Repair Validation",
            "overall_success": False,
            "api_success": False,
            "frontend_success": False,
            "detailed_results": {
                "api_tests": [],
                "frontend_tests": [],
                "screenshots": [],
                "data_validation": {}
            }
        }
    
    async def test_api_functionality(self):
        """Teste API-Funktionalität"""
        print("🔌 TESTE API-FUNKTIONALITÄT")
        print("-" * 40)
        
        api_endpoints = [
            {
                "name": "Models Overview",
                "url": "/api/statistics/models/overview",
                "expected_keys": ["success", "models_overview", "total_models"]
            },
            {
                "name": "Comprehensive Models",
                "url": "/api/statistics/models/comprehensive", 
                "expected_keys": ["success", "data"]
            }
        ]
        
        api_success_count = 0
        
        for endpoint in api_endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint['url']}", timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Validiere Struktur
                    structure_valid = all(key in data for key in endpoint["expected_keys"])
                    
                    # Validiere Daten
                    has_model_data = False
                    if "models_overview" in data:
                        has_model_data = len(data["models_overview"]) > 0
                    elif "data" in data and "models" in data["data"]:
                        has_model_data = len(data["data"]["models"]) > 0
                    
                    success = structure_valid and has_model_data
                    
                    self.success_report["detailed_results"]["api_tests"].append({
                        "endpoint": endpoint["name"],
                        "url": endpoint["url"],
                        "status_code": response.status_code,
                        "structure_valid": structure_valid,
                        "has_model_data": has_model_data,
                        "success": success,
                        "models_count": len(data.get("models_overview", data.get("data", {}).get("models", [])))
                    })
                    
                    if success:
                        api_success_count += 1
                        print(f"✅ {endpoint['name']}: OK - {len(data.get('models_overview', data.get('data', {}).get('models', [])))} Modelle")
                    else:
                        print(f"⚠️ {endpoint['name']}: Struktur OK, aber keine Daten")
                else:
                    print(f"❌ {endpoint['name']}: HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"❌ {endpoint['name']}: Fehler - {str(e)}")
        
        self.success_report["api_success"] = api_success_count >= 2
        print(f"\n📊 API-Tests: {api_success_count}/{len(api_endpoints)} erfolgreich")
        return api_success_count >= 2
    
    async def test_frontend_integration(self):
        """Teste Frontend-Integration"""
        print("\n🌐 TESTE FRONTEND-INTEGRATION")
        print("-" * 40)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False, slow_mo=500)
            page = await browser.new_page()
            
            try:
                # Direkt zur Hauptseite navigieren
                await page.goto(self.base_url)
                await page.wait_for_load_state("networkidle")
                
                # Screenshot der geladenen Seite
                screenshot_path = f"/app/minesearch_v2/backend/screenshots/final_test_main_{datetime.now().strftime('%H%M%S')}.png"
                await page.screenshot(path=screenshot_path)
                self.success_report["detailed_results"]["screenshots"].append(screenshot_path)
                
                print("✅ Hauptseite geladen")
                
                # Suche nach Statistik-Tab oder Button
                statistics_elements = [
                    'a:has-text("📈")',
                    'a:has-text("Suchstatistiken")',
                    'a:has-text("Statistik")',
                    '#statisticsTab',
                    'a[href="#statistics"]'
                ]
                
                tab_found = False
                for selector in statistics_elements:
                    try:
                        element = page.locator(selector).first
                        if await element.is_visible():
                            print(f"✅ Statistik-Element gefunden: {selector}")
                            await element.click()
                            tab_found = True
                            break
                    except:
                        continue
                
                if not tab_found:
                    print("⚠️ Statistik-Tab nicht gefunden - prüfe Seiten-Content")
                
                await asyncio.sleep(3)
                
                # Screenshot nach möglichem Tab-Klick
                screenshot_path = f"/app/minesearch_v2/backend/screenshots/final_test_after_tab_{datetime.now().strftime('%H%M%S')}.png"
                await page.screenshot(path=screenshot_path)
                self.success_report["detailed_results"]["screenshots"].append(screenshot_path)
                
                # Analysiere Seiten-Content
                page_text = await page.inner_text('body')
                
                # Suche nach Statistik-Indikatoren
                statistics_indicators = {
                    "model_names": any(model in page_text.lower() for model in ["gpt", "claude", "deepseek", "gemini"]),
                    "success_rate": any(term in page_text.lower() for term in ["success", "erfolg", "rate"]),
                    "numeric_data": any(char.isdigit() for char in page_text),
                    "provider_names": any(provider in page_text.lower() for provider in ["openrouter", "anthropic", "openai", "google"]),
                    "no_errors": not any(error in page_text.lower() for error in ["error", "fehler", "exception"])
                }
                
                # Button-Tests (Filter-Funktionalität)
                buttons_found = await page.locator('button').count()
                filter_button_clicked = False
                
                if buttons_found > 0:
                    try:
                        # Versuche einen "Laden" oder "Filter" Button zu finden
                        load_button = page.locator('button:has-text("Laden")')
                        if await load_button.is_visible():
                            await load_button.click()
                            filter_button_clicked = True
                            print("✅ Filter-Button geklickt")
                            await asyncio.sleep(2)
                    except:
                        pass
                
                # Finaler Screenshot
                screenshot_path = f"/app/minesearch_v2/backend/screenshots/final_test_complete_{datetime.now().strftime('%H%M%S')}.png"
                await page.screenshot(path=screenshot_path)
                self.success_report["detailed_results"]["screenshots"].append(screenshot_path)
                
                # Frontend-Erfolg bewerten
                frontend_score = sum([
                    statistics_indicators["model_names"],
                    statistics_indicators["numeric_data"],
                    statistics_indicators["no_errors"],
                    buttons_found > 5  # Zeigt dass UI geladen ist
                ])
                
                self.success_report["detailed_results"]["frontend_tests"] = [{
                    "tab_found": tab_found,
                    "buttons_found": buttons_found,
                    "filter_button_clicked": filter_button_clicked,
                    "statistics_indicators": statistics_indicators,
                    "frontend_score": frontend_score,
                    "success": frontend_score >= 3
                }]
                
                frontend_success = frontend_score >= 3
                self.success_report["frontend_success"] = frontend_success
                
                print(f"📊 Frontend-Score: {frontend_score}/4")
                if frontend_success:
                    print("✅ Frontend-Integration erfolgreich")
                else:
                    print("⚠️ Frontend-Integration teilweise erfolgreich")
                
                return frontend_success
                
            except Exception as e:
                print(f"❌ Frontend-Test Fehler: {str(e)}")
                return False
            
            finally:
                await browser.close()
    
    async def validate_data_quality(self):
        """Validiere Datenqualität"""
        print("\n🔍 VALIDIERE DATENQUALITÄT")
        print("-" * 40)
        
        try:
            # Hole Models Overview Daten
            response = requests.get(f"{self.base_url}/api/statistics/models/overview", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                models = data.get("models_overview", [])
                
                quality_checks = {
                    "has_models": len(models) > 0,
                    "models_have_data": all(model.get("total_searches", 0) > 0 for model in models),
                    "success_rates_valid": all(0 <= model.get("success_rate", 0) <= 100 for model in models),
                    "providers_present": len(set(model.get("provider", "") for model in models)) > 0,
                    "timestamps_present": all(model.get("last_used") for model in models)
                }
                
                self.success_report["detailed_results"]["data_validation"] = {
                    "total_models": len(models),
                    "quality_checks": quality_checks,
                    "sample_model": models[0] if models else None
                }
                
                quality_score = sum(quality_checks.values())
                print(f"📊 Datenqualität: {quality_score}/{len(quality_checks)} Checks bestanden")
                
                if models:
                    print(f"✅ {len(models)} Modelle gefunden")
                    print(f"✅ Modell-Beispiel: {models[0].get('model_name', 'Unknown')[:50]}...")
                
                return quality_score >= 4
            
        except Exception as e:
            print(f"❌ Datenqualität-Test Fehler: {str(e)}")
            return False
        
        return False
    
    async def run_complete_validation(self):
        """Führe komplette Validierung durch"""
        print("🎯 FINALE STATISTIK-REPARATUR VALIDIERUNG")
        print("=" * 50)
        
        # API-Tests
        api_success = await self.test_api_functionality()
        
        # Frontend-Tests
        frontend_success = await self.test_frontend_integration()
        
        # Datenqualitäts-Tests
        data_quality_success = await self.validate_data_quality()
        
        # Gesamtbewertung
        overall_success = api_success and (frontend_success or data_quality_success)
        self.success_report["overall_success"] = overall_success
        
        # Finaler Bericht
        print("\n" + "=" * 50)
        print("🏆 FINALE ERGEBNISSE")
        print("=" * 50)
        print(f"🔌 API-Funktionalität: {'✅ ERFOLGREICH' if api_success else '❌ FEHLGESCHLAGEN'}")
        print(f"🌐 Frontend-Integration: {'✅ ERFOLGREICH' if frontend_success else '⚠️ TEILWEISE'}")
        print(f"📊 Datenqualität: {'✅ ERFOLGREICH' if data_quality_success else '❌ FEHLGESCHLAGEN'}")
        print("-" * 50)
        
        if overall_success:
            print("🎉 GESAMTERGEBNIS: ✅ STATISTIK-REPARATUR ERFOLGREICH!")
            print("   → Backend-Fix hat funktioniert")
            print("   → API liefert korrekte Daten")
            print("   → Modell-Statistiken sind verfügbar")
        else:
            print("⚠️ GESAMTERGEBNIS: ❌ WEITERE ARBEITEN ERFORDERLICH")
            if not api_success:
                print("   → API-Endpunkte benötigen Korrekturen")
            if not frontend_success and not data_quality_success:
                print("   → Frontend-Integration oder Datenqualität problematisch")
        
        print("=" * 50)
        
        # Speichere Bericht
        report_file = f"/app/minesearch_v2/backend/final_statistics_success_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.success_report, f, indent=2, ensure_ascii=False)
        
        print(f"📋 Detaillierter Bericht: {report_file}")
        
        return self.success_report

async def main():
    test = FinalStatisticsSuccessTest()
    results = await test.run_complete_validation()
    return results

if __name__ == "__main__":
    asyncio.run(main())