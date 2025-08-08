"""
Author: rahn
Datum: 07.08.2025
Version: 1.0
Beschreibung: Browser-Test-Agent zur Validierung der Statistik-Funktionalität
"""

from playwright.sync_api import Playwright, sync_playwright
import time
import json
from datetime import datetime
import os

class StatisticsBrowserValidator:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.screenshots_dir = "/app/minesearch_v2/backend/screenshots"
        self.results = {
            "test_timestamp": datetime.now().isoformat(),
            "navigation_success": False,
            "statistics_tab_accessible": False,
            "screenshots_taken": [],
            "data_validation": {},
            "interactive_elements": {},
            "visual_problems": [],
            "missing_data": [],
            "success_metrics": {}
        }
        
        # Ensure screenshots directory exists
        os.makedirs(self.screenshots_dir, exist_ok=True)

    def run_validation(self):
        """Führe vollständige Statistik-Validierung durch"""
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=False, slow_mo=1000)
            context = browser.new_context(viewport={'width': 1920, 'height': 1080})
            page = context.new_page()
            
            try:
                # Step 1: Navigate to localhost:8000
                print("🌐 SCHRITT 1: Navigation zu http://localhost:8000")
                page.goto(self.base_url)
                page.wait_for_load_state("networkidle")
                time.sleep(2)
                
                # Take initial screenshot
                screenshot_path = f"{self.screenshots_dir}/01_initial_page_load.png"
                page.screenshot(path=screenshot_path)
                self.results["screenshots_taken"].append(screenshot_path)
                print(f"📸 Screenshot gespeichert: {screenshot_path}")
                self.results["navigation_success"] = True
                
                # Step 2: Click Statistics Tab (Radio Button)
                print("📊 SCHRITT 2: Statistik-Tab öffnen")
                
                # Try to find and click the statistics radio button
                stats_radio = page.locator('input#method_statistics')
                stats_label = page.locator('label[for="method_statistics"]')
                
                if stats_radio.count() > 0:
                    # Click the label to activate the radio button
                    stats_label.click()
                    page.wait_for_timeout(3000)  # Wait longer for content to load
                    self.results["statistics_tab_accessible"] = True
                    print("✅ Statistik-Tab erfolgreich geöffnet")
                    
                    # Screenshot after tab click
                    screenshot_path = f"{self.screenshots_dir}/02_statistics_tab_opened.png"
                    page.screenshot(path=screenshot_path)
                    self.results["screenshots_taken"].append(screenshot_path)
                    print(f"📸 Screenshot gespeichert: {screenshot_path}")
                    
                    # Wait for statistics to auto-load and then click "Statistiken laden"
                    page.wait_for_timeout(2000)
                    
                    # Look for and click the "Statistiken laden" button
                    load_button = page.locator('button:has-text("Statistiken laden"), button[onclick*="loadModelStatistics"]')
                    if load_button.count() > 0:
                        print("🔍 Klicke auf 'Statistiken laden' Button")
                        load_button.first.click()
                        # Wait for statistics to load
                        page.wait_for_timeout(5000)  # Wait longer for data loading
                        
                        # Screenshot after loading
                        screenshot_path = f"{self.screenshots_dir}/03_statistics_loaded.png"
                        page.screenshot(path=screenshot_path)
                        self.results["screenshots_taken"].append(screenshot_path)
                        print(f"📸 Screenshot nach Laden: {screenshot_path}")
                    else:
                        print("⚠️ 'Statistiken laden' Button nicht gefunden")
                    
                else:
                    print("❌ Statistik-Tab Radio-Button nicht gefunden!")
                    self.results["visual_problems"].append("Statistics tab radio button not found")
                
                # Step 3: Capture all statistics areas
                print("📋 SCHRITT 3: Screenshots aller Statistik-Bereiche")
                self._capture_statistics_areas(page)
                
                # Step 4: Validate specific data
                print("🔍 SCHRITT 4: Datenvalidierung")
                self._validate_statistics_data(page)
                
                # Step 5: Test interactive elements
                print("🖱️ SCHRITT 5: Test interaktiver Elemente")
                self._test_interactive_elements(page)
                
                # Final overview screenshot
                screenshot_path = f"{self.screenshots_dir}/99_final_statistics_overview.png"
                page.screenshot(path=screenshot_path)
                self.results["screenshots_taken"].append(screenshot_path)
                print(f"📸 Finaler Screenshot gespeichert: {screenshot_path}")
                
            except Exception as e:
                print(f"❌ Fehler während Test: {str(e)}")
                self.results["visual_problems"].append(f"Test error: {str(e)}")
            finally:
                browser.close()
        
        return self._generate_report()

    def _capture_statistics_areas(self, page):
        """Capture screenshots of specific statistics areas"""
        areas_to_capture = [
            ("Model Performance Statistics", "#model-statistics-table-container, .statistics-table-container, #enhanced-statistics-table-container"),
            ("Statistics Summary", ".statistics-summary, #statistics-summary, [id*='summary']"),
            ("Model Statistics Tables", ".consolidated-table, .model-stats-table, #model-statistics-table"),
            ("Export Controls", ".unified-search-button, [onclick*='exportModelStatistics'], [onclick*='loadModelStatistics']"),
            ("Filter Options", ".filter-section, .search-filters, [class*='filter']")
        ]
        
        for area_name, selector in areas_to_capture:
            try:
                # Try multiple selectors
                selectors = selector.split(", ")
                element_found = False
                
                for sel in selectors:
                    if page.locator(sel).count() > 0:
                        element = page.locator(sel).first
                        if element.is_visible():
                            # Scroll element into view
                            element.scroll_into_view_if_needed()
                            time.sleep(1)
                            
                            # Take screenshot of specific area
                            screenshot_path = f"{self.screenshots_dir}/area_{area_name.lower().replace(' ', '_')}.png"
                            element.screenshot(path=screenshot_path)
                            self.results["screenshots_taken"].append(screenshot_path)
                            print(f"📸 {area_name} Screenshot: {screenshot_path}")
                            element_found = True
                            break
                
                if not element_found:
                    print(f"⚠️ {area_name} nicht gefunden mit Selektoren: {selector}")
                    self.results["missing_data"].append(f"{area_name} section not found")
                    
            except Exception as e:
                print(f"❌ Fehler beim Screenshotten von {area_name}: {str(e)}")
                self.results["visual_problems"].append(f"Screenshot error for {area_name}: {str(e)}")

    def _validate_statistics_data(self, page):
        """Validate specific data points"""
        validations = [
            ("Total Searches", "13", "text"),
            ("Success Rate", "100%", "text"),
            ("Model Statistics Entries", "76", "text"),
            ("Field Coverage", "75%", "text")
        ]
        
        for data_name, expected_value, value_type in validations:
            try:
                # Try multiple approaches to find the data
                found = False
                actual_value = None
                
                # Search by text content
                elements = page.get_by_text(expected_value)
                if elements.count() > 0:
                    actual_value = elements.first.text_content()
                    found = True
                
                # Search by partial text
                if not found and data_name.lower() in ["total", "success", "entries", "coverage"]:
                    keyword = data_name.split()[-1].lower()  # Get last word
                    elements = page.locator(f"*:has-text('{keyword}')")
                    if elements.count() > 0:
                        for i in range(min(3, elements.count())):  # Check first 3 matches
                            element = elements.nth(i)
                            text = element.text_content()
                            if expected_value in text or any(char.isdigit() for char in text):
                                actual_value = text
                                found = True
                                break
                
                self.results["data_validation"][data_name] = {
                    "expected": expected_value,
                    "actual": actual_value,
                    "found": found,
                    "status": "PASS" if (found and expected_value in str(actual_value)) else "FAIL"
                }
                
                print(f"📊 {data_name}: {'✅ PASS' if found else '❌ FAIL'} - Expected: {expected_value}, Found: {actual_value}")
                
            except Exception as e:
                print(f"❌ Validierungsfehler für {data_name}: {str(e)}")
                self.results["data_validation"][data_name] = {
                    "expected": expected_value,
                    "actual": None,
                    "found": False,
                    "status": "ERROR",
                    "error": str(e)
                }

    def _test_interactive_elements(self, page):
        """Test buttons, dropdowns, and filters"""
        interactive_tests = [
            ("Buttons", "button"),
            ("Dropdowns", "select"),
            ("Filter inputs", "input[type='text'], input[placeholder*='filter']"),
            ("Checkboxes", "input[type='checkbox']"),
            ("Radio buttons", "input[type='radio']")
        ]
        
        for element_type, selector in interactive_tests:
            try:
                elements = page.locator(selector)
                count = elements.count()
                clickable_count = 0
                
                if count > 0:
                    # Test up to 5 elements of each type
                    for i in range(min(5, count)):
                        element = elements.nth(i)
                        if element.is_visible() and element.is_enabled():
                            clickable_count += 1
                            
                            # Take screenshot before interaction
                            screenshot_path = f"{self.screenshots_dir}/interactive_{element_type.lower().replace(' ', '_')}_before_{i}.png"
                            page.screenshot(path=screenshot_path)
                            self.results["screenshots_taken"].append(screenshot_path)
                            
                            # Try to interact (carefully)
                            try:
                                if selector == "button":
                                    # Don't click buttons that might cause navigation
                                    button_text = element.text_content().lower()
                                    if not any(word in button_text for word in ['submit', 'send', 'delete', 'clear']):
                                        element.click()
                                        time.sleep(1)
                                        
                                        # Screenshot after interaction
                                        screenshot_path = f"{self.screenshots_dir}/interactive_{element_type.lower().replace(' ', '_')}_after_{i}.png"
                                        page.screenshot(path=screenshot_path)
                                        self.results["screenshots_taken"].append(screenshot_path)
                                        
                                elif selector == "select":
                                    element.click()
                                    time.sleep(0.5)
                                    
                            except Exception as interaction_error:
                                print(f"⚠️ Interaktionsfehler mit {element_type} #{i}: {str(interaction_error)}")
                
                self.results["interactive_elements"][element_type] = {
                    "total_found": count,
                    "clickable": clickable_count,
                    "status": "PASS" if clickable_count > 0 else ("NONE_FOUND" if count == 0 else "NOT_CLICKABLE")
                }
                
                print(f"🖱️ {element_type}: {count} gefunden, {clickable_count} interaktiv")
                
            except Exception as e:
                print(f"❌ Fehler beim Testen von {element_type}: {str(e)}")
                self.results["interactive_elements"][element_type] = {
                    "error": str(e),
                    "status": "ERROR"
                }

    def _generate_report(self):
        """Generate comprehensive test report"""
        report = {
            "test_summary": {
                "timestamp": self.results["test_timestamp"],
                "navigation_success": self.results["navigation_success"],
                "statistics_tab_accessible": self.results["statistics_tab_accessible"],
                "total_screenshots": len(self.results["screenshots_taken"]),
                "data_validations_passed": sum(1 for v in self.results["data_validation"].values() if v.get("status") == "PASS"),
                "interactive_elements_working": sum(1 for v in self.results["interactive_elements"].values() if v.get("status") == "PASS"),
                "visual_problems_count": len(self.results["visual_problems"]),
                "missing_data_count": len(self.results["missing_data"])
            },
            "detailed_results": self.results
        }
        
        # Save report to file
        report_path = f"/app/minesearch_v2/backend/statistics_validation_report_{int(time.time())}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📋 VOLLSTÄNDIGER BERICHT gespeichert unter: {report_path}")
        
        return report

def main():
    print("🚀 STARTE STATISTIK-BROWSER-VALIDIERUNG")
    print("=" * 50)
    
    validator = StatisticsBrowserValidator()
    report = validator.run_validation()
    
    print("\n" + "=" * 50)
    print("📊 TEST-ZUSAMMENFASSUNG:")
    print(f"✅ Navigation erfolgreich: {report['test_summary']['navigation_success']}")
    print(f"📊 Statistik-Tab zugänglich: {report['test_summary']['statistics_tab_accessible']}")
    print(f"📸 Screenshots aufgenommen: {report['test_summary']['total_screenshots']}")
    print(f"✅ Datenvalidierungen bestanden: {report['test_summary']['data_validations_passed']}")
    print(f"🖱️ Interaktive Elemente funktionsfähig: {report['test_summary']['interactive_elements_working']}")
    print(f"⚠️ Visuelle Probleme gefunden: {report['test_summary']['visual_problems_count']}")
    print(f"❌ Fehlende Daten: {report['test_summary']['missing_data_count']}")
    print("=" * 50)
    
    return report

if __name__ == "__main__":
    main()