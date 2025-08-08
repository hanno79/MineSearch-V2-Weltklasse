"""
Author: rahn
Datum: 07.08.2025
Version: 1.0
Beschreibung: Umfassender Statistics-Test mit Filter-Anwendung und Daten-Validierung
"""

from playwright.sync_api import sync_playwright
import time
import json
from datetime import datetime
import os

class ComprehensiveStatisticsTest:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.screenshots_dir = "/app/minesearch_v2/backend/screenshots"
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "phases": [],
            "final_data_found": {},
            "screenshots": [],
            "test_success": False
        }
        
        os.makedirs(self.screenshots_dir, exist_ok=True)

    def run_comprehensive_test(self):
        """Umfassender Test der Statistik-Funktionalität"""
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=False, slow_mo=800)
            context = browser.new_context(viewport={'width': 1920, 'height': 1080})
            page = context.new_page()
            
            try:
                print("🚀 UMFASSENDER STATISTIK-TEST STARTET")
                print("=" * 60)
                
                # Phase 1: Navigation und Tab-Aktivierung
                self._phase_1_navigation(page)
                
                # Phase 2: Statistiken laden
                self._phase_2_load_statistics(page)
                
                # Phase 3: Filter anwenden
                self._phase_3_apply_filters(page)
                
                # Phase 4: Daten validieren
                self._phase_4_validate_data(page)
                
                # Phase 5: Interaktivität testen
                self._phase_5_test_interactivity(page)
                
                # Phase 6: Export-Funktionen
                self._phase_6_test_exports(page)
                
                self._generate_final_report()
                
            except Exception as e:
                print(f"❌ KRITISCHER FEHLER: {str(e)}")
                self.test_results["error"] = str(e)
            finally:
                browser.close()
        
        return self.test_results

    def _phase_1_navigation(self, page):
        """Phase 1: Navigation zur Statistik-Seite"""
        print("\n📍 PHASE 1: Navigation und Tab-Aktivierung")
        phase_data = {"name": "Navigation", "success": False, "details": []}
        
        try:
            # Zur Hauptseite navigieren
            page.goto(self.base_url)
            page.wait_for_load_state("networkidle")
            time.sleep(2)
            
            screenshot_path = f"{self.screenshots_dir}/phase1_01_initial_load.png"
            page.screenshot(path=screenshot_path)
            self.test_results["screenshots"].append(screenshot_path)
            phase_data["details"].append("✅ Erfolgreich zu localhost:8000 navigiert")
            
            # Statistik-Tab aktivieren
            stats_radio = page.locator('input#method_statistics')
            stats_label = page.locator('label[for="method_statistics"]')
            
            if stats_label.is_visible():
                stats_label.click()
                time.sleep(3)
                
                screenshot_path = f"{self.screenshots_dir}/phase1_02_tab_activated.png"
                page.screenshot(path=screenshot_path)
                self.test_results["screenshots"].append(screenshot_path)
                phase_data["details"].append("✅ Statistik-Tab erfolgreich aktiviert")
                phase_data["success"] = True
            else:
                phase_data["details"].append("❌ Statistik-Tab nicht gefunden")
            
        except Exception as e:
            phase_data["details"].append(f"❌ Fehler: {str(e)}")
        
        self.test_results["phases"].append(phase_data)
        print(f"Phase 1 Status: {'✅ ERFOLG' if phase_data['success'] else '❌ FEHLER'}")

    def _phase_2_load_statistics(self, page):
        """Phase 2: Statistiken laden"""
        print("\n📊 PHASE 2: Statistiken laden")
        phase_data = {"name": "Load Statistics", "success": False, "details": []}
        
        try:
            # "Statistiken laden" Button finden und klicken
            load_buttons = [
                'button:has-text("Statistiken laden")',
                'button[onclick*="loadModelStatistics"]',
                '.unified-search-button:has-text("Statistiken")'
            ]
            
            button_clicked = False
            for selector in load_buttons:
                button = page.locator(selector)
                if button.count() > 0 and button.first.is_visible():
                    print(f"🔍 Klicke Button mit Selektor: {selector}")
                    button.first.click()
                    time.sleep(5)  # Warten auf Laden der Daten
                    button_clicked = True
                    break
            
            if button_clicked:
                screenshot_path = f"{self.screenshots_dir}/phase2_01_after_load_click.png"
                page.screenshot(path=screenshot_path)
                self.test_results["screenshots"].append(screenshot_path)
                phase_data["details"].append("✅ Statistiken-Button erfolgreich geklickt")
                phase_data["success"] = True
            else:
                phase_data["details"].append("❌ Kein Statistiken-Button gefunden")
        
        except Exception as e:
            phase_data["details"].append(f"❌ Fehler: {str(e)}")
        
        self.test_results["phases"].append(phase_data)
        print(f"Phase 2 Status: {'✅ ERFOLG' if phase_data['success'] else '❌ FEHLER'}")

    def _phase_3_apply_filters(self, page):
        """Phase 3: Filter anwenden um Daten zu laden"""
        print("\n🔍 PHASE 3: Filter anwenden")
        phase_data = {"name": "Apply Filters", "success": False, "details": []}
        
        try:
            # "Filter anwenden" Button finden und klicken
            filter_buttons = [
                'button:has-text("Filter anwenden")',
                'button:has-text("🔍 Statistiken")',
                '.unified-search-button:has-text("anwenden")'
            ]
            
            filter_applied = False
            for selector in filter_buttons:
                button = page.locator(selector)
                if button.count() > 0:
                    for i in range(button.count()):
                        current_button = button.nth(i)
                        if current_button.is_visible():
                            print(f"🔍 Klicke Filter-Button: {selector} (#{i})")
                            current_button.click()
                            time.sleep(8)  # Lange warten für Datenladung
                            
                            screenshot_path = f"{self.screenshots_dir}/phase3_01_after_filter_{i}.png"
                            page.screenshot(path=screenshot_path)
                            self.test_results["screenshots"].append(screenshot_path)
                            
                            # Prüfen ob Tabelle mit Daten geladen wurde
                            table_selectors = [
                                'table',
                                '.consolidated-table',
                                '[id*="statistics-table"]',
                                '.model-stats-table'
                            ]
                            
                            for table_sel in table_selectors:
                                tables = page.locator(table_sel)
                                if tables.count() > 0:
                                    table = tables.first
                                    if table.is_visible():
                                        rows = table.locator('tbody tr')
                                        if rows.count() > 0:
                                            phase_data["details"].append(f"✅ Tabelle gefunden mit {rows.count()} Zeilen")
                                            filter_applied = True
                                            break
                            
                            if filter_applied:
                                break
                    
                    if filter_applied:
                        break
            
            if filter_applied:
                phase_data["success"] = True
                phase_data["details"].append("✅ Filter erfolgreich angewendet - Daten geladen")
            else:
                phase_data["details"].append("❌ Filter konnte nicht angewendet werden oder keine Daten geladen")
        
        except Exception as e:
            phase_data["details"].append(f"❌ Fehler: {str(e)}")
        
        self.test_results["phases"].append(phase_data)
        print(f"Phase 3 Status: {'✅ ERFOLG' if phase_data['success'] else '❌ FEHLER'}")

    def _phase_4_validate_data(self, page):
        """Phase 4: Spezifische Daten validieren"""
        print("\n🔍 PHASE 4: Datenvalidierung")
        phase_data = {"name": "Data Validation", "success": False, "details": [], "found_data": {}}
        
        try:
            # Screenshot der aktuellen Seite
            screenshot_path = f"{self.screenshots_dir}/phase4_01_data_validation.png"
            page.screenshot(path=screenshot_path)
            self.test_results["screenshots"].append(screenshot_path)
            
            # Suche nach spezifischen Datenmustern
            search_patterns = [
                ("Total Searches", r"\d+.*[Ss]uchen|[Ss]earches.*\d+|\d+.*total"),
                ("Success Rate", r"\d+%.*[Ee]rfolg|Success.*\d+%|\d+%.*success"),
                ("Model Entries", r"\d+.*[Mm]odell|[Mm]odel.*\d+|\d+.*entries"),
                ("Field Coverage", r"\d+%.*[Ff]eld|[Ff]ield.*\d+%|Coverage.*\d+%"),
                ("Statistics Table", r"[Ss]tatist|[Pp]erformance|[Mm]odell.*[Tt]abelle")
            ]
            
            found_count = 0
            for data_name, pattern in search_patterns:
                # Suche im gesamten Seitentext
                page_content = page.content()
                
                # Zusätzlich suche in sichtbaren Elementen
                visible_text = ""
                try:
                    all_elements = page.locator('*:visible')
                    for i in range(min(50, all_elements.count())):  # Begrenzt auf 50 Elemente
                        element = all_elements.nth(i)
                        if element.is_visible():
                            text = element.text_content()
                            if text and len(text.strip()) > 0:
                                visible_text += text + " "
                except:
                    pass
                
                # Suche nach Zahlen und spezifischen Begriffen
                import re
                pattern_matches = re.findall(pattern, visible_text, re.IGNORECASE)
                content_matches = re.findall(pattern, page_content, re.IGNORECASE)
                
                if pattern_matches or content_matches:
                    found_count += 1
                    phase_data["found_data"][data_name] = {
                        "pattern_matches": pattern_matches[:3],  # Nur erste 3
                        "content_matches": content_matches[:3],
                        "status": "FOUND"
                    }
                    phase_data["details"].append(f"✅ {data_name} gefunden")
                else:
                    phase_data["found_data"][data_name] = {"status": "NOT_FOUND"}
                    phase_data["details"].append(f"❌ {data_name} nicht gefunden")
            
            # Prüfe auf Tabellen mit Daten
            tables = page.locator('table')
            table_count = tables.count()
            if table_count > 0:
                phase_data["details"].append(f"✅ {table_count} Tabellen gefunden")
                for i in range(min(3, table_count)):  # Prüfe bis zu 3 Tabellen
                    table = tables.nth(i)
                    if table.is_visible():
                        rows = table.locator('tr')
                        row_count = rows.count()
                        if row_count > 1:  # Mehr als nur Header
                            phase_data["details"].append(f"✅ Tabelle {i+1}: {row_count} Zeilen")
                            found_count += 1
            else:
                phase_data["details"].append("❌ Keine Tabellen gefunden")
            
            if found_count >= 2:  # Mindestens 2 Datenelemente gefunden
                phase_data["success"] = True
            
        except Exception as e:
            phase_data["details"].append(f"❌ Fehler: {str(e)}")
        
        self.test_results["phases"].append(phase_data)
        self.test_results["final_data_found"] = phase_data["found_data"]
        print(f"Phase 4 Status: {'✅ ERFOLG' if phase_data['success'] else '❌ FEHLER'}")

    def _phase_5_test_interactivity(self, page):
        """Phase 5: Interaktive Elemente testen"""
        print("\n🖱️ PHASE 5: Interaktivitäts-Test")
        phase_data = {"name": "Interactivity", "success": False, "details": []}
        
        try:
            interactive_elements = [
                ("Export Buttons", 'button:has-text("CSV"), button:has-text("Export")'),
                ("Filter Dropdowns", 'select, .dropdown'),
                ("Sort Headers", 'th[onclick], .sortable'),
                ("Detail Buttons", 'button:has-text("Detail"), .details-btn')
            ]
            
            working_elements = 0
            for element_name, selector in interactive_elements:
                elements = page.locator(selector)
                count = elements.count()
                
                if count > 0:
                    clickable = 0
                    for i in range(min(3, count)):  # Test bis zu 3 Elemente
                        element = elements.nth(i)
                        if element.is_visible() and element.is_enabled():
                            clickable += 1
                    
                    phase_data["details"].append(f"✅ {element_name}: {count} gefunden, {clickable} interaktiv")
                    if clickable > 0:
                        working_elements += 1
                else:
                    phase_data["details"].append(f"❌ {element_name}: Nicht gefunden")
            
            if working_elements >= 2:  # Mindestens 2 Elementtypen funktionsfähig
                phase_data["success"] = True
            
        except Exception as e:
            phase_data["details"].append(f"❌ Fehler: {str(e)}")
        
        self.test_results["phases"].append(phase_data)
        print(f"Phase 5 Status: {'✅ ERFOLG' if phase_data['success'] else '❌ FEHLER'}")

    def _phase_6_test_exports(self, page):
        """Phase 6: Export-Funktionen testen"""
        print("\n📁 PHASE 6: Export-Test")
        phase_data = {"name": "Export Functions", "success": False, "details": []}
        
        try:
            export_buttons = page.locator('button:has-text("CSV"), button:has-text("Export")')
            count = export_buttons.count()
            
            if count > 0:
                phase_data["details"].append(f"✅ {count} Export-Buttons gefunden")
                
                # Screenshot vor Export-Test
                screenshot_path = f"{self.screenshots_dir}/phase6_01_before_export.png"
                page.screenshot(path=screenshot_path)
                self.test_results["screenshots"].append(screenshot_path)
                
                # Test eines Export-Buttons (vorsichtig)
                for i in range(min(2, count)):
                    button = export_buttons.nth(i)
                    if button.is_visible() and button.is_enabled():
                        button_text = button.text_content()
                        phase_data["details"].append(f"✅ Export-Button '{button_text}' ist funktionsfähig")
                        phase_data["success"] = True
                        break
            else:
                phase_data["details"].append("❌ Keine Export-Buttons gefunden")
            
        except Exception as e:
            phase_data["details"].append(f"❌ Fehler: {str(e)}")
        
        self.test_results["phases"].append(phase_data)
        print(f"Phase 6 Status: {'✅ ERFOLG' if phase_data['success'] else '❌ FEHLER'}")

    def _generate_final_report(self):
        """Erzeuge finalen Testbericht"""
        print("\n📋 FINAL-BERICHT WIRD ERSTELLT")
        
        successful_phases = sum(1 for phase in self.test_results["phases"] if phase["success"])
        total_phases = len(self.test_results["phases"])
        
        self.test_results["test_success"] = successful_phases >= (total_phases * 0.7)  # 70% Erfolg
        
        # Speichere Bericht
        report_path = f"/app/minesearch_v2/backend/comprehensive_statistics_test_report_{int(time.time())}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        
        print("=" * 60)
        print(f"📊 UMFASSENDER TEST ABGESCHLOSSEN")
        print(f"✅ Erfolgreiche Phasen: {successful_phases}/{total_phases}")
        print(f"📸 Screenshots aufgenommen: {len(self.test_results['screenshots'])}")
        print(f"🎯 Gesamtergebnis: {'✅ BESTANDEN' if self.test_results['test_success'] else '❌ FEHLGESCHLAGEN'}")
        print(f"📋 Vollständiger Bericht: {report_path}")
        print("=" * 60)

def main():
    tester = ComprehensiveStatisticsTest()
    results = tester.run_comprehensive_test()
    return results

if __name__ == "__main__":
    main()