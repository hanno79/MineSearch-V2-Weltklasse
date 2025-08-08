"""
Author: rahn
Datum: 07.08.2025
Version: 1.0
Beschreibung: Browser-basierte Validierung der Statistik-Funktionalität mit Playwright
"""

import asyncio
import json
import time
from datetime import datetime
from playwright.async_api import async_playwright
import requests

class BrowserStatisticsValidator:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "test_steps": [],
            "screenshots": [],
            "api_tests": [],
            "browser_tests": [],
            "success": False,
            "errors": []
        }
    
    def log_step(self, category, step, status, details=""):
        """Protokolliere einen Teststep"""
        step_info = {
            "category": category,
            "step": step,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "details": details
        }
        self.results["test_steps"].append(step_info)
        
        status_emoji = "✅" if status == "SUCCESS" else "⚠️" if status == "WARNING" else "❌"
        print(f"{status_emoji} [{category}] {step}: {details}")
    
    async def test_api_endpoints_first(self):
        """Teste zuerst die API-Endpunkte direkt"""
        print("🔍 Teste Statistik-API-Endpunkte...")
        
        # Bekannte Endpunkte basierend auf statistics_core.py
        endpoints_to_test = [
            "/api/statistics/overview",
            "/api/statistics/performance/system", 
            "/api/statistics/models/overview",
            "/api/statistics/models/comprehensive"
        ]
        
        api_success_count = 0
        
        for endpoint in endpoints_to_test:
            try:
                url = f"{self.base_url}{endpoint}"
                response = requests.get(url, timeout=15)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        has_models = False
                        
                        # Prüfe auf Modell-Daten
                        if isinstance(data, dict):
                            if 'models_overview' in data:
                                has_models = len(data['models_overview']) > 0
                            elif 'data' in data and 'models' in data['data']:
                                has_models = len(data['data']['models']) > 0
                        
                        self.results["api_tests"].append({
                            "endpoint": endpoint,
                            "status_code": response.status_code,
                            "success": True,
                            "has_data": has_models,
                            "response_size": len(response.text)
                        })
                        
                        self.log_step("API", f"Test {endpoint}", "SUCCESS", 
                                    f"Status: {response.status_code}, Daten: {'Ja' if has_models else 'Nein'}")
                        
                        if has_models:
                            api_success_count += 1
                            
                    except json.JSONDecodeError:
                        self.log_step("API", f"Test {endpoint}", "WARNING", "Keine JSON-Antwort")
                else:
                    self.log_step("API", f"Test {endpoint}", "FAILED", f"Status: {response.status_code}")
                    
            except Exception as e:
                self.log_step("API", f"Test {endpoint}", "ERROR", str(e))
                self.results["api_tests"].append({
                    "endpoint": endpoint,
                    "success": False,
                    "error": str(e)
                })
        
        return api_success_count > 0
    
    async def run_browser_validation(self):
        """Hauptvalidierung im Browser"""
        print("🌐 Starte Browser-Validierung...")
        
        async with async_playwright() as p:
            # Browser mit sichtbarem UI starten
            browser = await p.chromium.launch(headless=False, slow_mo=500)
            page = await browser.new_page()
            
            try:
                # SCHRITT 1: Hauptseite laden
                self.log_step("BROWSER", "Navigation", "START", f"Lade {self.base_url}")
                await page.goto(self.base_url)
                await page.wait_for_load_state("networkidle", timeout=10000)
                
                # Screenshot der Hauptseite
                screenshot_path = f"/app/minesearch_v2/backend/screenshots/01_main_page_{datetime.now().strftime('%H%M%S')}.png"
                await page.screenshot(path=screenshot_path)
                self.results["screenshots"].append(screenshot_path)
                
                self.log_step("BROWSER", "Navigation", "SUCCESS", "Hauptseite geladen")
                
                # SCHRITT 2: Suche Statistik-Tab
                self.log_step("BROWSER", "Tab-Suche", "START", "Suche Statistik-Tab")
                
                # Verschiedene Selektoren für den Statistik-Tab
                tab_selectors = [
                    'a[href="#statistics"]',
                    'button[data-target="#statistics"]',
                    '#statisticsTab',
                    'a:has-text("📈")',
                    'a:has-text("Suchstatistiken")',
                    'a:has-text("Statistik")',
                    '.nav-link:has-text("Statistik")'
                ]
                
                tab_found = False
                for selector in tab_selectors:
                    try:
                        element = page.locator(selector).first
                        if await element.is_visible():
                            await element.click()
                            tab_found = True
                            self.log_step("BROWSER", "Tab-Suche", "SUCCESS", f"Tab gefunden mit {selector}")
                            break
                    except:
                        continue
                
                if not tab_found:
                    # Alternative: Alle Links durchsuchen
                    all_links = await page.locator('a, button').all()
                    for link in all_links:
                        try:
                            text = await link.text_content()
                            if text and ("statistik" in text.lower() or "📈" in text):
                                await link.click()
                                tab_found = True
                                self.log_step("BROWSER", "Tab-Suche", "SUCCESS", f"Tab gefunden: {text}")
                                break
                        except:
                            continue
                
                if not tab_found:
                    self.log_step("BROWSER", "Tab-Suche", "WARNING", "Statistik-Tab nicht gefunden")
                
                await asyncio.sleep(2)
                
                # Screenshot nach Tab-Klick
                screenshot_path = f"/app/minesearch_v2/backend/screenshots/02_statistics_tab_{datetime.now().strftime('%H%M%S')}.png"
                await page.screenshot(path=screenshot_path)
                self.results["screenshots"].append(screenshot_path)
                
                # SCHRITT 3: Suche und klicke Filter-Button
                self.log_step("BROWSER", "Filter-Button", "START", "Suche Filter-Button")
                
                filter_selectors = [
                    'button:has-text("Filter anwenden")',
                    'button:has-text("Laden")',
                    'button:has-text("Aktualisieren")',
                    '#apply-filter',
                    '.btn-primary',
                    'input[type="submit"]'
                ]
                
                filter_clicked = False
                for selector in filter_selectors:
                    try:
                        element = page.locator(selector).first
                        if await element.is_visible():
                            await element.click()
                            filter_clicked = True
                            self.log_step("BROWSER", "Filter-Button", "SUCCESS", f"Button geklickt: {selector}")
                            break
                    except:
                        continue
                
                if not filter_clicked:
                    self.log_step("BROWSER", "Filter-Button", "WARNING", "Filter-Button nicht gefunden")
                
                await asyncio.sleep(3)
                
                # Screenshot nach Filter
                screenshot_path = f"/app/minesearch_v2/backend/screenshots/03_after_filter_{datetime.now().strftime('%H%M%S')}.png"
                await page.screenshot(path=screenshot_path)
                self.results["screenshots"].append(screenshot_path)
                
                # SCHRITT 4: Warte auf Datenladung und analysiere Inhalt
                self.log_step("BROWSER", "Daten-Analyse", "START", "Analysiere geladene Daten")
                
                # Warte zusätzliche Zeit für AJAX-Requests
                await asyncio.sleep(5)
                
                # Analysiere Seiteninhalt
                page_content = await page.content()
                page_text = await page.inner_text('body')
                
                # Prüfe auf Tabellen
                tables = await page.locator('table').count()
                
                # Prüfe auf spezifische Indikatoren
                indicators_found = {
                    "tables": tables,
                    "model_mentions": page_text.lower().count("gpt") + page_text.lower().count("claude") + page_text.lower().count("gemini"),
                    "success_rate": page_text.lower().count("success") + page_text.lower().count("erfolg"),
                    "provider_mentions": page_text.lower().count("openai") + page_text.lower().count("anthropic") + page_text.lower().count("google"),
                    "numeric_data": len([char for char in page_text if char.isdigit()]) > 50,
                    "no_errors": "error" not in page_text.lower() and "fehler" not in page_text.lower()
                }
                
                # Finaler Screenshot
                screenshot_path = f"/app/minesearch_v2/backend/screenshots/04_final_analysis_{datetime.now().strftime('%H%M%S')}.png"
                await page.screenshot(path=screenshot_path)
                self.results["screenshots"].append(screenshot_path)
                
                # Bewertung
                success_criteria = [
                    indicators_found["tables"] > 0,
                    indicators_found["model_mentions"] >= 3,
                    indicators_found["numeric_data"],
                    indicators_found["no_errors"]
                ]
                
                success_count = sum(success_criteria)
                success_rate = success_count / len(success_criteria)
                
                self.results["browser_tests"].append({
                    "indicators_found": indicators_found,
                    "success_criteria_met": success_count,
                    "success_rate": success_rate,
                    "tab_found": tab_found,
                    "filter_clicked": filter_clicked
                })
                
                if success_rate >= 0.75:
                    self.log_step("BROWSER", "Daten-Analyse", "SUCCESS", 
                                f"Erfolgskriterien: {success_count}/{len(success_criteria)}")
                else:
                    self.log_step("BROWSER", "Daten-Analyse", "PARTIAL", 
                                f"Erfolgskriterien: {success_count}/{len(success_criteria)}")
                
                # SCHRITT 5: Teste verschiedene Filter (falls vorhanden)
                self.log_step("BROWSER", "Filter-Test", "START", "Teste verfügbare Filter")
                
                # Suche nach Filter-Elementen
                selects = await page.locator('select').count()
                checkboxes = await page.locator('input[type="checkbox"]').count()
                
                filters_tested = 0
                if selects > 0:
                    try:
                        select = page.locator('select').first
                        options = await select.locator('option').count()
                        if options > 1:
                            await select.select_option(index=1)
                            await asyncio.sleep(1)
                            filters_tested += 1
                    except:
                        pass
                
                if checkboxes > 0:
                    try:
                        checkbox = page.locator('input[type="checkbox"]').first
                        await checkbox.click()
                        await asyncio.sleep(1)
                        filters_tested += 1
                    except:
                        pass
                
                self.log_step("BROWSER", "Filter-Test", "SUCCESS" if filters_tested > 0 else "INFO", 
                            f"Filter getestet: {filters_tested}")
                
                # Finaler Screenshot nach Filtern
                screenshot_path = f"/app/minesearch_v2/backend/screenshots/05_filter_test_{datetime.now().strftime('%H%M%S')}.png"
                await page.screenshot(path=screenshot_path)
                self.results["screenshots"].append(screenshot_path)
                
                # Gesamtbewertung
                overall_success = (
                    len([t for t in self.results["api_tests"] if t.get("success", False)]) > 0 and
                    success_rate >= 0.5
                )
                
                self.results["success"] = overall_success
                
            except Exception as e:
                self.log_step("BROWSER", "FEHLER", "ERROR", str(e))
                self.results["errors"].append({
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
            
            finally:
                await browser.close()
    
    def generate_report(self):
        """Generiere detaillierten Testbericht"""
        report_file = f"/app/minesearch_v2/backend/statistics_fixed_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📋 Detaillierter Bericht: {report_file}")
        return report_file
    
    def print_summary(self):
        """Drucke finale Zusammenfassung"""
        print("\n" + "="*60)
        print("🎯 STATISTIK-VALIDIERUNG ABGESCHLOSSEN")
        print("="*60)
        
        # API-Ergebnisse
        api_successful = len([t for t in self.results["api_tests"] if t.get("success", False)])
        api_total = len(self.results["api_tests"])
        print(f"🔌 API-Tests: {api_successful}/{api_total} erfolgreich")
        
        # Browser-Ergebnisse
        if self.results["browser_tests"]:
            browser_result = self.results["browser_tests"][0]
            print(f"🌐 Browser-Tests: {browser_result['success_criteria_met']}/4 Kriterien erfüllt")
            print(f"📊 Tabellen gefunden: {browser_result['indicators_found']['tables']}")
            print(f"🤖 Modell-Erwähnungen: {browser_result['indicators_found']['model_mentions']}")
        
        # Screenshots
        print(f"📸 Screenshots erstellt: {len(self.results['screenshots'])}")
        
        # Gesamtergebnis
        if self.results["success"]:
            print("🎉 GESAMTERGEBNIS: ✅ ERFOLGREICH")
            print("   → Statistik-Funktionalität ist repariert!")
        else:
            print("⚠️ GESAMTERGEBNIS: ❌ TEILWEISE ERFOLGREICH")
            print("   → Weitere Korrekturen benötigt")
        
        print("="*60)
    
    async def run_full_validation(self):
        """Führe die komplette Validierung durch"""
        print("🚀 STARTE FINALE STATISTIK-VALIDIERUNG")
        print("="*50)
        
        # Zuerst API testen
        api_success = await self.test_api_endpoints_first()
        
        # Dann Browser-Validierung
        await self.run_browser_validation()
        
        # Berichte generieren
        report_file = self.generate_report()
        self.print_summary()
        
        return self.results

async def main():
    validator = BrowserStatisticsValidator()
    results = await validator.run_full_validation()
    return results

if __name__ == "__main__":
    asyncio.run(main())