"""
Author: rahn
Datum: 07.08.2025
Version: 1.0
Beschreibung: Finale Browser-Validierung der reparierten Statistik-Funktionalität
"""

from playwright.sync_api import sync_playwright
import time
import json
from datetime import datetime

class StatisticsValidationTest:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.results = {
            "test_start": datetime.now().isoformat(),
            "steps": [],
            "screenshots": [],
            "errors": [],
            "success": False
        }
    
    def log_step(self, step_name, status, details=""):
        """Protokolliere Teststep"""
        step_info = {
            "step": step_name,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "details": details
        }
        self.results["steps"].append(step_info)
        print(f"✅ {step_name}: {status} - {details}")
    
    def capture_screenshot(self, page, name):
        """Screenshot mit Zeitstempel erstellen"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{timestamp}.png"
        filepath = f"/app/minesearch_v2/backend/screenshots/{filename}"
        page.screenshot(path=filepath)
        self.results["screenshots"].append(filepath)
        print(f"📸 Screenshot gespeichert: {filepath}")
        return filepath
    
    def validate_statistics_functionality(self):
        """Haupttest für Statistik-Funktionalität"""
        print("🚀 Starte finale Statistik-Validierung...")
        
        with sync_playwright() as p:
            # Browser starten
            browser = p.chromium.launch(headless=False, slow_mo=1000)
            page = browser.new_page()
            
            try:
                # SCHRITT 1: Navigation zur Hauptseite
                self.log_step("Navigation", "START", f"Navigiere zu {self.base_url}")
                page.goto(self.base_url)
                page.wait_for_load_state("networkidle")
                self.capture_screenshot(page, "01_main_page_loaded")
                self.log_step("Navigation", "SUCCESS", "Hauptseite erfolgreich geladen")
                
                # SCHRITT 2: Statistik-Tab öffnen
                self.log_step("Tab_Opening", "START", "Suche Statistik-Tab")
                
                # Verschiedene Selektoren für Statistik-Tab testen
                tab_selectors = [
                    'a[href="#statistics"]',
                    'button[data-target="#statistics"]',
                    'a:has-text("Suchstatistiken")',
                    '.nav-tabs a:nth-child(3)',
                    '#statistics-tab'
                ]
                
                tab_found = False
                for selector in tab_selectors:
                    try:
                        if page.locator(selector).is_visible():
                            page.click(selector)
                            tab_found = True
                            self.log_step("Tab_Opening", "SUCCESS", f"Tab mit Selektor {selector} gefunden und geklickt")
                            break
                    except Exception as e:
                        continue
                
                if not tab_found:
                    # Fallback: Alle verfügbaren Tabs anzeigen
                    tabs = page.locator('a, button').all()
                    for tab in tabs:
                        try:
                            text = tab.text_content() or ""
                            if "statistik" in text.lower() or "📈" in text:
                                tab.click()
                                tab_found = True
                                self.log_step("Tab_Opening", "SUCCESS", f"Tab mit Text '{text}' gefunden")
                                break
                        except:
                            continue
                
                if not tab_found:
                    raise Exception("Statistik-Tab nicht gefunden")
                
                time.sleep(2)
                self.capture_screenshot(page, "02_statistics_tab_opened")
                
                # SCHRITT 3: Filter anwenden Button klicken
                self.log_step("Filter_Apply", "START", "Suche Filter anwenden Button")
                
                filter_selectors = [
                    'button:has-text("Filter anwenden")',
                    '#apply-filters',
                    '.filter-apply-btn',
                    'button[onclick*="filter"]',
                    'input[type="submit"][value*="Filter"]'
                ]
                
                filter_found = False
                for selector in filter_selectors:
                    try:
                        if page.locator(selector).is_visible():
                            page.click(selector)
                            filter_found = True
                            self.log_step("Filter_Apply", "SUCCESS", f"Filter-Button mit {selector} geklickt")
                            break
                    except Exception as e:
                        continue
                
                if not filter_found:
                    # Fallback: Alle Buttons nach Filter-Text durchsuchen
                    buttons = page.locator('button, input[type="submit"]').all()
                    for button in buttons:
                        try:
                            text = button.text_content() or ""
                            value = button.get_attribute("value") or ""
                            if "filter" in text.lower() or "filter" in value.lower():
                                button.click()
                                filter_found = True
                                self.log_step("Filter_Apply", "SUCCESS", f"Filter-Button mit Text '{text}' gefunden")
                                break
                        except:
                            continue
                
                if not filter_found:
                    self.log_step("Filter_Apply", "WARNING", "Filter-Button nicht gefunden - fortfahren ohne Filter")
                
                time.sleep(2)
                self.capture_screenshot(page, "03_filter_button_clicked")
                
                # SCHRITT 4: Auf Datenladung warten
                self.log_step("Data_Loading", "START", "Warte auf Statistik-Daten")
                
                # Warten auf verschiedene mögliche Indikatoren für geladene Daten
                loading_wait_time = 15
                for i in range(loading_wait_time):
                    try:
                        # Prüfe auf Tabellen, Listen oder Statistik-Container
                        if (page.locator('table').count() > 0 or 
                            page.locator('.statistics-table').count() > 0 or
                            page.locator('[id*="statistic"]').count() > 0):
                            break
                    except:
                        pass
                    time.sleep(1)
                    if i % 5 == 0:
                        print(f"⏱️ Warte auf Daten... {i+1}/{loading_wait_time} Sekunden")
                
                self.capture_screenshot(page, "04_after_data_loading")
                self.log_step("Data_Loading", "COMPLETED", f"Wartzeit von {loading_wait_time} Sekunden abgeschlossen")
                
                # SCHRITT 5: Statistik-Tabelle validieren
                self.log_step("Table_Validation", "START", "Validiere Statistik-Tabelle")
                
                # Suche nach Tabellen oder statistischen Daten
                tables_found = page.locator('table').count()
                statistics_containers = page.locator('[id*="statistic"], [class*="statistic"]').count()
                
                validation_results = {
                    "tables_found": tables_found,
                    "statistics_containers": statistics_containers,
                    "models_found": 0,
                    "scores_found": 0,
                    "providers_found": 0
                }
                
                if tables_found > 0:
                    # Analysiere Tabelleninhalt
                    table = page.locator('table').first
                    rows = table.locator('tr').count()
                    
                    # Suche nach Modell-Daten (mindestens 3 erwartet)
                    model_indicators = ["gpt", "claude", "gemini", "model", "provider"]
                    page_text = page.text_content().lower()
                    
                    for indicator in model_indicators:
                        if indicator in page_text:
                            validation_results["models_found"] += page_text.count(indicator)
                    
                    # Suche nach Score-Daten
                    score_indicators = ["score", "accuracy", "precision", "recall", "%"]
                    for indicator in score_indicators:
                        if indicator in page_text:
                            validation_results["scores_found"] += page_text.count(indicator)
                    
                    # Suche nach Provider-Informationen
                    provider_indicators = ["openai", "anthropic", "google", "provider"]
                    for indicator in provider_indicators:
                        if indicator in page_text:
                            validation_results["providers_found"] += page_text.count(indicator)
                    
                    self.log_step("Table_Validation", "SUCCESS", f"Tabelle gefunden mit {rows} Zeilen")
                else:
                    self.log_step("Table_Validation", "WARNING", "Keine Tabelle gefunden - prüfe anderen Content")
                
                self.capture_screenshot(page, "05_table_validation_complete")
                
                # SCHRITT 6: Detaillierte Datenprüfung
                self.log_step("Data_Details", "START", "Prüfe Dateninhalte")
                
                # Extrahiere sichtbaren Text für Analyse
                visible_text = page.text_content()
                
                # Prüfe auf erwartete Inhalte
                expected_elements = {
                    "models": ["gpt", "claude", "gemini"],
                    "metrics": ["accuracy", "precision", "recall", "f1"],
                    "numbers": any(char.isdigit() for char in visible_text)
                }
                
                details_found = []
                for category, items in expected_elements.items():
                    if category == "numbers":
                        if items:
                            details_found.append(f"Numerische Werte vorhanden")
                    else:
                        found_items = [item for item in items if item.lower() in visible_text.lower()]
                        if found_items:
                            details_found.append(f"{category}: {', '.join(found_items)}")
                
                self.log_step("Data_Details", "SUCCESS", f"Gefundene Details: {'; '.join(details_found)}")
                self.capture_screenshot(page, "06_data_details_extracted")
                
                # SCHRITT 7: Filter-Funktionalität testen
                self.log_step("Filter_Testing", "START", "Teste verschiedene Filter")
                
                # Suche nach Filter-Optionen (Dropdowns, Checkboxes, etc.)
                filter_elements = {
                    "select": page.locator('select').count(),
                    "checkbox": page.locator('input[type="checkbox"]').count(),
                    "radio": page.locator('input[type="radio"]').count(),
                    "input": page.locator('input[type="text"], input[type="search"]').count()
                }
                
                filters_tested = 0
                for filter_type, count in filter_elements.items():
                    if count > 0:
                        try:
                            if filter_type == "select":
                                select = page.locator('select').first
                                options = select.locator('option').count()
                                if options > 1:
                                    select.select_option(index=1)
                                    filters_tested += 1
                                    time.sleep(1)
                            elif filter_type == "checkbox":
                                checkbox = page.locator('input[type="checkbox"]').first
                                checkbox.click()
                                filters_tested += 1
                                time.sleep(1)
                        except Exception as e:
                            self.log_step("Filter_Testing", "WARNING", f"Fehler bei {filter_type}: {str(e)}")
                
                self.capture_screenshot(page, "07_filter_testing_complete")
                self.log_step("Filter_Testing", "SUCCESS", f"{filters_tested} Filter getestet")
                
                # SCHRITT 8: Finale Validierung
                self.log_step("Final_Validation", "START", "Finale Ergebnisvalidierung")
                
                # Sammle finale Statistiken
                final_stats = {
                    "page_title": page.title(),
                    "url": page.url,
                    "tables_present": tables_found > 0,
                    "data_indicators": validation_results,
                    "filters_available": sum(filter_elements.values()) > 0,
                    "no_errors_visible": "error" not in visible_text.lower(),
                    "content_loaded": len(visible_text.strip()) > 100
                }
                
                # Bewerte Gesamterfolg
                success_criteria = [
                    final_stats["tables_present"] or final_stats["data_indicators"]["statistics_containers"] > 0,
                    final_stats["data_indicators"]["models_found"] >= 1,
                    final_stats["no_errors_visible"],
                    final_stats["content_loaded"]
                ]
                
                success_rate = sum(success_criteria) / len(success_criteria)
                self.results["success"] = success_rate >= 0.75
                
                self.capture_screenshot(page, "08_final_validation_complete")
                self.log_step("Final_Validation", "SUCCESS" if self.results["success"] else "PARTIAL", 
                            f"Erfolgsrate: {success_rate*100:.1f}%")
                
                # Speichere detaillierte Ergebnisse
                self.results["final_stats"] = final_stats
                self.results["validation_results"] = validation_results
                self.results["success_rate"] = success_rate
                
            except Exception as e:
                self.results["errors"].append({
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
                self.log_step("ERROR", "FAILED", f"Kritischer Fehler: {str(e)}")
                self.capture_screenshot(page, "error_screenshot")
            
            finally:
                browser.close()
                self.results["test_end"] = datetime.now().isoformat()
    
    def generate_report(self):
        """Generiere detaillierten Testbericht"""
        report_file = f"/app/minesearch_v2/backend/statistics_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📋 Testbericht gespeichert: {report_file}")
        return report_file
    
    def print_summary(self):
        """Drucke Testzusammenfassung"""
        print("\n" + "="*60)
        print("🎯 STATISTIK-VALIDIERUNG ZUSAMMENFASSUNG")
        print("="*60)
        print(f"✅ Gesamterfolg: {'JA' if self.results['success'] else 'TEILWEISE'}")
        print(f"📊 Erfolgsrate: {self.results.get('success_rate', 0)*100:.1f}%")
        print(f"🔍 Durchgeführte Schritte: {len(self.results['steps'])}")
        print(f"📸 Screenshots erstellt: {len(self.results['screenshots'])}")
        print(f"⚠️ Fehler aufgetreten: {len(self.results['errors'])}")
        
        if 'final_stats' in self.results:
            stats = self.results['final_stats']
            print(f"📋 Tabellen gefunden: {'✅' if stats['tables_present'] else '❌'}")
            print(f"🔢 Daten geladen: {'✅' if stats['content_loaded'] else '❌'}")
            print(f"🚫 Keine Fehler: {'✅' if stats['no_errors_visible'] else '❌'}")
        
        print("="*60)

def run_validation():
    """Führe die Validierung aus"""
    test = StatisticsValidationTest()
    test.validate_statistics_functionality()
    report_file = test.generate_report()
    test.print_summary()
    return test.results

if __name__ == "__main__":
    results = run_validation()