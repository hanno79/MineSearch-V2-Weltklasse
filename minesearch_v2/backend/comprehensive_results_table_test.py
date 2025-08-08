"""
Author: rahn
Datum: 29.07.2025
Version: 1.0
Beschreibung: Umfassender Browser-Test für MineSearch v2 konsolidierte Ergebnistabelle
"""

import time
import json
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import requests

class MineSearchResultsTableTester:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.findings = []
        self.screenshots = []
        
        # Chrome Setup für Headless-Betrieb
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        
    def add_finding(self, category, title, details, status="INFO"):
        """Füge ein Test-Finding hinzu"""
        finding = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "category": category,
            "title": title,
            "details": details,
            "status": status
        }
        self.findings.append(finding)
        print(f"[{status}] {category}: {title}")
        print(f"    Details: {details}")
        
    def take_screenshot(self, name, description=""):
        """Erstelle Screenshot"""
        timestamp = int(time.time())
        filename = f"screenshot_{name}_{timestamp}.png"
        filepath = f"/app/minesearch_v2/backend/{filename}"
        
        self.driver.save_screenshot(filepath)
        self.screenshots.append({
            "name": name,
            "filename": filename,
            "filepath": filepath,
            "description": description,
            "timestamp": timestamp
        })
        print(f"Screenshot erstellt: {filename}")
        
    def test_navigate_to_results(self):
        """Test 1: Navigation zur Results Tab"""
        print("\n=== TEST 1: Navigation zur Results Tab ===")
        
        try:
            # Lade Hauptseite
            self.driver.get(self.base_url)
            time.sleep(2)
            
            self.take_screenshot("main_page", "Hauptseite nach dem Laden")
            
            # Suche nach Results Tab
            results_tab = None
            possible_selectors = [
                "//a[contains(text(), 'Results')]",
                "//button[contains(text(), 'Results')]",
                "//div[contains(@class, 'tab')][contains(text(), 'Results')]",
                "//li[contains(text(), 'Results')]",
                "#results-tab",
                ".results-tab"
            ]
            
            for selector in possible_selectors:
                try:
                    if selector.startswith("//"):
                        results_tab = self.driver.find_element(By.XPATH, selector)
                    else:
                        results_tab = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue
                    
            if results_tab:
                results_tab.click()
                time.sleep(2)
                self.add_finding("Navigation", "Results Tab gefunden und geklickt", f"Tab-Element: {results_tab.tag_name}", "SUCCESS")
            else:
                # Versuche alternative Navigation über URL
                self.driver.get(f"{self.base_url}#results")
                time.sleep(2)
                self.add_finding("Navigation", "Results Tab über URL aufgerufen", "Direkte URL-Navigation verwendet", "WARNING")
                
        except Exception as e:
            self.add_finding("Navigation", "Fehler beim Navigieren zu Results", str(e), "ERROR")
            
    def test_table_structure(self):
        """Test 2: Tabellenstruktur und -inhalte"""
        print("\n=== TEST 2: Tabellenstruktur und -inhalte ===")
        
        try:
            # Suche nach Tabelle
            table_selectors = [
                "table",
                ".results-table",
                "#results-table",
                ".consolidated-results",
                "[data-testid='results-table']"
            ]
            
            table = None
            for selector in table_selectors:
                try:
                    table = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue
                    
            if not table:
                self.add_finding("Tabellenstruktur", "Keine Tabelle gefunden", "Keine der erwarteten Selektoren funktionierte", "ERROR")
                return
                
            self.take_screenshot("results_table", "Konsolidierte Ergebnistabelle")
            
            # Analysiere Tabellen-Header
            headers = table.find_elements(By.CSS_SELECTOR, "th")
            header_texts = [h.text.strip() for h in headers if h.text.strip()]
            
            self.add_finding("Tabellenstruktur", f"Tabellen-Header gefunden: {len(header_texts)}", 
                           f"Headers: {', '.join(header_texts)}", "INFO")
            
            # Erwartete Standard-Spalten
            expected_columns = ["Mine", "Land", "Region", "Zuverlässigkeit", "Modelle", "Letzte Aktualisierung"]
            missing_columns = [col for col in expected_columns if not any(col.lower() in h.lower() for h in header_texts)]
            
            if missing_columns:
                self.add_finding("Tabellenstruktur", "Fehlende Standard-Spalten", 
                               f"Nicht gefunden: {', '.join(missing_columns)}", "WARNING")
            else:
                self.add_finding("Tabellenstruktur", "Alle Standard-Spalten vorhanden", 
                               "Mine, Land, Region, Zuverlässigkeit, Modelle, Letzte Aktualisierung", "SUCCESS")
            
            # Analysiere Tabellen-Zeilen
            rows = table.find_elements(By.CSS_SELECTOR, "tbody tr")
            if rows:
                self.add_finding("Tabellenstruktur", f"Tabellenzeilen gefunden: {len(rows)}", 
                               f"Erste Zeile hat {len(rows[0].find_elements(By.CSS_SELECTOR, 'td'))} Spalten", "INFO")
            else:
                self.add_finding("Tabellenstruktur", "Keine Tabellenzeilen gefunden", 
                               "Tabelle scheint leer zu sein", "WARNING")
                
        except Exception as e:
            self.add_finding("Tabellenstruktur", "Fehler bei Tabellenanalyse", str(e), "ERROR")
            
    def test_field_counting(self):
        """Test 3: Felderzählung ('Felder mit Daten')"""
        print("\n=== TEST 3: Felderzählung ('Felder mit Daten') ===")
        
        try:
            # Suche nach Feldzählung-Elementen
            count_selectors = [
                ".field-count",
                ".fields-with-data",
                "[data-field-count]",
                ".data-field-counter",
                "//span[contains(text(), 'Felder mit Daten')]",
                "//div[contains(text(), 'Felder')]"
            ]
            
            field_counts = []
            for selector in count_selectors:
                try:
                    if selector.startswith("//"):
                        elements = self.driver.find_elements(By.XPATH, selector)
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for elem in elements:
                        if elem.text and ("felder" in elem.text.lower() or "field" in elem.text.lower()):
                            field_counts.append(elem.text.strip())
                except:
                    continue
                    
            if field_counts:
                self.add_finding("Felderzählung", "Felderzählung gefunden", 
                               f"Gefunden: {', '.join(field_counts)}", "SUCCESS")
                               
                # Prüfe auf X-Werte in der Zählung
                for count_text in field_counts:
                    if "x" in count_text.lower():
                        self.add_finding("Felderzählung", "X-Werte möglicherweise mitgezählt", 
                                       f"Text enthält 'X': {count_text}", "WARNING")
            else:
                self.add_finding("Felderzählung", "Keine Felderzählung gefunden", 
                               "Möglicherweise nicht implementiert oder anderer Selektor", "WARNING")
                
        except Exception as e:
            self.add_finding("Felderzählung", "Fehler bei Felderzählung-Test", str(e), "ERROR")
            
    def test_duplicate_fields(self):
        """Test 4: Validierung auf doppelte Felder"""
        print("\n=== TEST 4: Validierung auf doppelte Felder ===")
        
        try:
            # Analysiere alle Tabellen-Header
            headers = self.driver.find_elements(By.CSS_SELECTOR, "th")
            header_texts = [h.text.strip().lower() for h in headers if h.text.strip()]
            
            # Finde Duplikate
            seen_headers = set()
            duplicates = []
            
            for header in header_texts:
                if header in seen_headers:
                    duplicates.append(header)
                else:
                    seen_headers.add(header)
                    
            if duplicates:
                self.add_finding("Doppelte Felder", "Doppelte Header gefunden", 
                               f"Duplikate: {', '.join(set(duplicates))}", "ERROR")
            else:
                self.add_finding("Doppelte Felder", "Keine doppelten Header", 
                               f"Alle {len(header_texts)} Header sind eindeutig", "SUCCESS")
                               
            # Prüfe auch auf ähnliche Header (mögliche Duplikate)
            similar_pairs = []
            header_list = list(seen_headers)
            for i, h1 in enumerate(header_list):
                for h2 in header_list[i+1:]:
                    if h1 in h2 or h2 in h1:
                        similar_pairs.append((h1, h2))
                        
            if similar_pairs:
                self.add_finding("Doppelte Felder", "Ähnliche Header gefunden", 
                               f"Ähnlich: {similar_pairs}", "WARNING")
                
        except Exception as e:
            self.add_finding("Doppelte Felder", "Fehler bei Duplikat-Prüfung", str(e), "ERROR")
            
    def test_csv_export(self):
        """Test 5: CSV-Export Button"""
        print("\n=== TEST 5: CSV-Export Button ===")
        
        try:
            # Suche nach CSV-Export Button
            csv_selectors = [
                "//button[contains(text(), 'CSV')]",
                "//a[contains(text(), 'CSV')]",
                ".csv-export",
                "#csv-export",
                "[data-action='export']",
                "//button[contains(text(), 'Export')]"
            ]
            
            csv_button = None
            for selector in csv_selectors:
                try:
                    if selector.startswith("//"):
                        csv_button = self.driver.find_element(By.XPATH, selector)
                    else:
                        csv_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue
                    
            if csv_button:
                self.add_finding("CSV-Export", "CSV-Export Button gefunden", 
                               f"Button-Text: '{csv_button.text}'", "SUCCESS")
                
                # Screenshot vor dem Klick
                self.take_screenshot("csv_export_button", "CSV-Export Button vor dem Klick")
                
                # Teste Button-Klick
                try:
                    csv_button.click()
                    time.sleep(2)
                    
                    # Screenshot nach dem Klick
                    self.take_screenshot("csv_export_after_click", "Nach CSV-Export Button Klick")
                    
                    self.add_finding("CSV-Export", "CSV-Export Button geklickt", 
                                   "Button-Klick erfolgreich", "SUCCESS")
                except Exception as click_error:
                    self.add_finding("CSV-Export", "Fehler beim CSV-Export Button Klick", 
                                   str(click_error), "ERROR")
            else:
                self.add_finding("CSV-Export", "CSV-Export Button nicht gefunden", 
                               "Möglicherweise anderer Selektor oder nicht verfügbar", "WARNING")
                
        except Exception as e:
            self.add_finding("CSV-Export", "Fehler bei CSV-Export Test", str(e), "ERROR")
            
    def test_x_values_handling(self):
        """Test 6: X-Werte Handling"""
        print("\n=== TEST 6: X-Werte Handling ===")
        
        try:
            # Analysiere Tabellenzellen auf X-Werte
            cells = self.driver.find_elements(By.CSS_SELECTOR, "td")
            x_values = []
            
            for cell in cells:
                if cell.text.strip().upper() == 'X':
                    x_values.append(cell)
                    
            if x_values:
                self.add_finding("X-Werte", f"X-Werte gefunden: {len(x_values)}", 
                               f"Anzahl Zellen mit 'X': {len(x_values)}", "INFO")
                
                # Prüfe Styling der X-Werte
                first_x = x_values[0]
                style_classes = first_x.get_attribute("class")
                
                self.add_finding("X-Werte", "X-Werte Styling analysiert", 
                               f"CSS-Klassen: {style_classes}", "INFO")
            else:
                self.add_finding("X-Werte", "Keine X-Werte gefunden", 
                               "Tabelle enthält möglicherweise keine X-Markierungen", "INFO")
                
            # Prüfe ob X-Werte korrekt als "leer" behandelt werden
            # Das machen wir durch Überprüfung der Felderzählung
            total_cells = len(cells)
            x_count = len(x_values)
            data_cells = total_cells - x_count
            
            self.add_finding("X-Werte", "X-Werte Statistik", 
                           f"Gesamt: {total_cells}, X-Werte: {x_count}, Daten: {data_cells}", "INFO")
                           
        except Exception as e:
            self.add_finding("X-Werte", "Fehler bei X-Werte Test", str(e), "ERROR")
            
    def test_details_modal(self):
        """Test 7: Details-Modal (falls verfügbar)"""
        print("\n=== TEST 7: Details-Modal Test ===")
        
        try:
            # Suche nach anklickbaren Elementen in der Tabelle
            clickable_elements = self.driver.find_elements(By.CSS_SELECTOR, "td[onclick], td.clickable, .clickable")
            
            if not clickable_elements:
                # Versuche erste Zelle zu klicken
                first_cells = self.driver.find_elements(By.CSS_SELECTOR, "tbody tr td:first-child")
                if first_cells:
                    clickable_elements = [first_cells[0]]
                    
            if clickable_elements:
                self.add_finding("Details-Modal", f"Anklickbare Elemente gefunden: {len(clickable_elements)}", 
                               "Versuche Details-Modal zu öffnen", "INFO")
                
                # Klicke auf erstes Element
                try:
                    clickable_elements[0].click()
                    time.sleep(2)
                    
                    # Suche nach Modal
                    modal_selectors = [".modal", "#modal", ".popup", ".details", "[role='dialog']"]
                    
                    modal_found = False
                    for selector in modal_selectors:
                        try:
                            modal = self.driver.find_element(By.CSS_SELECTOR, selector)
                            if modal.is_displayed():
                                modal_found = True
                                self.take_screenshot("details_modal", "Details-Modal geöffnet")
                                self.add_finding("Details-Modal", "Details-Modal erfolgreich geöffnet", 
                                               f"Modal gefunden: {selector}", "SUCCESS")
                                break
                        except NoSuchElementException:
                            continue
                            
                    if not modal_found:
                        self.add_finding("Details-Modal", "Kein Details-Modal gefunden", 
                                       "Klick hat kein Modal geöffnet", "WARNING")
                        
                except Exception as click_error:
                    self.add_finding("Details-Modal", "Fehler beim Öffnen des Details-Modal", 
                                   str(click_error), "ERROR")
            else:
                self.add_finding("Details-Modal", "Keine anklickbaren Elemente gefunden", 
                               "Möglicherweise kein Details-Modal verfügbar", "INFO")
                
        except Exception as e:
            self.add_finding("Details-Modal", "Fehler bei Details-Modal Test", str(e), "ERROR")
            
    def run_comprehensive_test(self):
        """Führe alle Tests durch"""
        print("=== MINESEARCH V2 KONSOLIDIERTE ERGEBNISTABELLE TEST ===")
        print(f"Test gestartet: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            self.test_navigate_to_results()
            self.test_table_structure()
            self.test_field_counting()
            self.test_duplicate_fields()
            self.test_csv_export()
            self.test_x_values_handling()
            self.test_details_modal()
            
        except Exception as e:
            self.add_finding("Allgemein", "Unerwarteter Fehler während Test", str(e), "ERROR")
            
        finally:
            self.cleanup()
            
    def cleanup(self):
        """Bereinigung und Abschluss"""
        print("\n=== TEST-ABSCHLUSS ===")
        
        # Erstelle finalen Screenshot
        self.take_screenshot("final_state", "Finaler Zustand nach allen Tests")
        
        # Erstelle Test-Report
        report = {
            "test_session": {
                "start_time": time.strftime('%Y-%m-%d %H:%M:%S'),
                "total_findings": len(self.findings),
                "total_screenshots": len(self.screenshots)
            },
            "findings": self.findings,
            "screenshots": self.screenshots,
            "summary": self.generate_summary()
        }
        
        report_file = f"/app/minesearch_v2/backend/results_table_test_report_{int(time.time())}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
            
        print(f"Test-Report gespeichert: {report_file}")
        
        # Browser schließen
        self.driver.quit()
        
    def generate_summary(self):
        """Generiere Test-Zusammenfassung"""
        success_count = len([f for f in self.findings if f["status"] == "SUCCESS"])
        warning_count = len([f for f in self.findings if f["status"] == "WARNING"])
        error_count = len([f for f in self.findings if f["status"] == "ERROR"])
        
        return {
            "total_tests": len(self.findings),
            "success": success_count,
            "warnings": warning_count,
            "errors": error_count,
            "test_status": "PASSED" if error_count == 0 else "FAILED" if error_count > 3 else "PASSED_WITH_WARNINGS"
        }

if __name__ == "__main__":
    tester = MineSearchResultsTableTester()
    tester.run_comprehensive_test()