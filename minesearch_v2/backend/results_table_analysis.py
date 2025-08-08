"""
Author: rahn
Datum: 29.07.2025
Version: 1.0
Beschreibung: Analyse der MineSearch v2 konsolidierten Ergebnistabelle über API und HTML-Analyse
"""

import requests
import json
import time
from bs4 import BeautifulSoup
import os

class ResultsTableAnalyzer:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.findings = []
        
    def add_finding(self, category, title, details, status="INFO"):
        """Füge ein Analyse-Finding hinzu"""
        finding = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "category": category,
            "title": title,
            "details": details,
            "status": status
        }
        self.findings.append(finding)
        print(f"[{status}] {category}: {title}")
        if isinstance(details, dict):
            for key, value in details.items():
                print(f"    {key}: {value}")
        else:
            print(f"    {details}")
        
    def test_server_connection(self):
        """Test der Server-Verbindung"""
        print("\n=== TEST 1: Server-Verbindung ===")
        
        try:
            response = requests.get(self.base_url, timeout=5)
            if response.status_code == 200:
                self.add_finding("Verbindung", "Server erreichbar", 
                               f"Status: {response.status_code}", "SUCCESS")
                return True
            else:
                self.add_finding("Verbindung", "Server-Fehler", 
                               f"Status: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.add_finding("Verbindung", "Verbindungsfehler", str(e), "ERROR")
            return False
            
    def analyze_main_page_structure(self):
        """Analysiere die Hauptseiten-Struktur"""
        print("\n=== TEST 2: Hauptseiten-Struktur ===")
        
        try:
            response = requests.get(self.base_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Suche nach Tab-Struktur
            tabs = soup.find_all(['a', 'button', 'div'], text=lambda t: t and 'results' in t.lower())
            if tabs:
                self.add_finding("Seitenstruktur", "Results-Tab gefunden", 
                               f"Anzahl möglicher Results-Tabs: {len(tabs)}", "SUCCESS")
            else:
                self.add_finding("Seitenstruktur", "Keine Results-Tab gefunden", 
                               "Möglicherweise dynamisch geladen", "WARNING")
                
            # Suche nach Tabellen-Struktur
            tables = soup.find_all('table')
            if tables:
                self.add_finding("Seitenstruktur", f"Tabellen gefunden: {len(tables)}", 
                               "HTML enthält Tabellen-Elemente", "INFO")
                
                # Analysiere erste Tabelle
                first_table = tables[0]
                headers = first_table.find_all('th')
                if headers:
                    header_texts = [h.get_text().strip() for h in headers]
                    self.add_finding("Tabellenstruktur", f"Tabellen-Header: {len(header_texts)}", 
                                   {"Headers": header_texts}, "INFO")
                    
                rows = first_table.find_all('tr')
                self.add_finding("Tabellenstruktur", f"Tabellen-Zeilen: {len(rows)}", 
                               "Inklusive Header-Zeile", "INFO")
            else:
                self.add_finding("Seitenstruktur", "Keine statischen Tabellen", 
                               "Tabellen möglicherweise dynamisch geladen", "WARNING")
                
        except Exception as e:
            self.add_finding("Seitenstruktur", "Fehler bei HTML-Analyse", str(e), "ERROR")
            
    def test_api_endpoints(self):
        """Teste relevante API-Endpoints"""
        print("\n=== TEST 3: API-Endpoints ===")
        
        endpoints = [
            "/api/results",
            "/api/mines",
            "/api/consolidated-results",
            "/api/export/csv",
            "/api/batch/results"
        ]
        
        for endpoint in endpoints:
            try:
                url = f"{self.base_url}{endpoint}"
                response = requests.get(url, timeout=5)
                
                if response.status_code == 200:
                    self.add_finding("API", f"Endpoint verfügbar: {endpoint}", 
                                   f"Status: {response.status_code}", "SUCCESS")
                    
                    # Analysiere JSON-Response falls möglich
                    try:
                        data = response.json()
                        if isinstance(data, list):
                            self.add_finding("API", f"Daten für {endpoint}", 
                                           f"Anzahl Einträge: {len(data)}", "INFO")
                        elif isinstance(data, dict):
                            keys = list(data.keys())[:5]  # Erste 5 Keys
                            self.add_finding("API", f"Datenstruktur für {endpoint}", 
                                           f"Keys: {keys}", "INFO")
                    except:
                        self.add_finding("API", f"Nicht-JSON Response für {endpoint}", 
                                       f"Content-Type: {response.headers.get('content-type', 'unknown')}", "INFO")
                        
                elif response.status_code == 404:
                    self.add_finding("API", f"Endpoint nicht gefunden: {endpoint}", 
                                   f"Status: {response.status_code}", "WARNING")
                else:
                    self.add_finding("API", f"Endpoint-Fehler: {endpoint}", 
                                   f"Status: {response.status_code}", "ERROR")
                    
            except Exception as e:
                self.add_finding("API", f"Verbindungsfehler für {endpoint}", str(e), "ERROR")
                
    def analyze_database_structure(self):
        """Analysiere die Datenbankstruktur"""
        print("\n=== TEST 4: Datenbankstruktur ===")
        
        db_path = "/app/data/minesearch.db"
        if os.path.exists(db_path):
            try:
                import sqlite3
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Hole Tabellennamen
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                
                self.add_finding("Datenbank", f"Tabellen gefunden: {len(tables)}", 
                               f"Tabellen: {[t[0] for t in tables]}", "INFO")
                
                # Analysiere Haupttabelle (falls vorhanden)
                main_tables = ['mines', 'search_results', 'consolidated_results']
                for table_name in main_tables:
                    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';")
                    if cursor.fetchone():
                        cursor.execute(f"PRAGMA table_info({table_name});")
                        columns = cursor.fetchall()
                        column_names = [col[1] for col in columns]
                        
                        self.add_finding("Datenbank", f"Spalten in {table_name}: {len(column_names)}", 
                                       f"Spalten: {column_names}", "INFO")
                        
                        # Zähle Einträge
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                        count = cursor.fetchone()[0]
                        self.add_finding("Datenbank", f"Einträge in {table_name}: {count}", 
                                       "Aktuelle Datenmenge", "INFO")
                        
                        # Analysiere X-Werte falls möglich
                        for col in column_names[2:]:  # Skip ID und Name-Spalten
                            try:
                                cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {col} = 'X';")
                                x_count = cursor.fetchone()[0]
                                if x_count > 0:
                                    self.add_finding("X-Werte", f"X-Werte in {table_name}.{col}: {x_count}", 
                                                   "X-Markierungen gefunden", "INFO")
                            except:
                                continue
                                
                conn.close()
                
            except Exception as e:
                self.add_finding("Datenbank", "Fehler bei Datenbankanalyse", str(e), "ERROR")
        else:
            self.add_finding("Datenbank", "Datenbankdatei nicht gefunden", 
                           f"Pfad: {db_path}", "WARNING")
            
    def test_csv_export_functionality(self):
        """Teste CSV-Export Funktionalität"""
        print("\n=== TEST 5: CSV-Export Funktionalität ===")
        
        export_endpoints = [
            "/api/export/csv",
            "/export/csv",
            "/csv",
            "/api/results/export"
        ]
        
        for endpoint in export_endpoints:
            try:
                url = f"{self.base_url}{endpoint}"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    content_type = response.headers.get('content-type', '')
                    
                    if 'csv' in content_type or 'text/csv' in content_type:
                        self.add_finding("CSV-Export", f"CSV-Export verfügbar: {endpoint}", 
                                       f"Content-Type: {content_type}", "SUCCESS")
                        
                        # Analysiere CSV-Inhalt
                        csv_content = response.text
                        lines = csv_content.split('\n')
                        if lines:
                            header_line = lines[0]
                            headers = header_line.split(',')
                            self.add_finding("CSV-Export", f"CSV-Header: {len(headers)} Spalten", 
                                           f"Headers: {headers[:5]}...", "INFO")
                            
                            data_lines = [line for line in lines[1:] if line.strip()]
                            self.add_finding("CSV-Export", f"CSV-Daten: {len(data_lines)} Zeilen", 
                                           "Datenzeilen ohne Header", "INFO")
                    else:
                        self.add_finding("CSV-Export", f"Falscher Content-Type für {endpoint}", 
                                       f"Erhalten: {content_type}", "WARNING")
                        
                elif response.status_code == 404:
                    continue  # Endpoint nicht gefunden, normal
                else:
                    self.add_finding("CSV-Export", f"Export-Fehler für {endpoint}", 
                                   f"Status: {response.status_code}", "ERROR")
                    
            except Exception as e:
                self.add_finding("CSV-Export", f"Fehler bei {endpoint}", str(e), "ERROR")
                
    def analyze_frontend_files(self):
        """Analysiere Frontend-Dateien auf Results-Tab Implementierung"""
        print("\n=== TEST 6: Frontend-Dateien Analyse ===")
        
        frontend_files = [
            "/app/frontend/index.html",
            "/app/minesearch_v2/frontend/js/app.js", 
            "/app/minesearch_v2/frontend/js/results-display.js",
            "/app/frontend/style.css"
        ]
        
        for file_path in frontend_files:
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Suche nach Results-Tab relevanten Begriffen
                    keywords = ['results', 'consolidated', 'table', 'csv', 'export', 'felder']
                    found_keywords = []
                    
                    for keyword in keywords:
                        if keyword.lower() in content.lower():
                            count = content.lower().count(keyword.lower())
                            found_keywords.append(f"{keyword}({count})")
                            
                    self.add_finding("Frontend", f"Analyse: {os.path.basename(file_path)}", 
                                   f"Keywords: {', '.join(found_keywords)}", "INFO")
                    
                    # Spezielle Analyse für HTML
                    if file_path.endswith('.html'):
                        soup = BeautifulSoup(content, 'html.parser')
                        tables = soup.find_all('table')
                        buttons = soup.find_all('button')
                        
                        self.add_finding("Frontend", f"HTML-Struktur: {os.path.basename(file_path)}", 
                                       f"Tabellen: {len(tables)}, Buttons: {len(buttons)}", "INFO")
                        
                except Exception as e:
                    self.add_finding("Frontend", f"Fehler beim Lesen: {file_path}", str(e), "ERROR")
            else:
                self.add_finding("Frontend", f"Datei nicht gefunden: {file_path}", 
                               "Frontend-Datei fehlt", "WARNING")
                
    def run_comprehensive_analysis(self):
        """Führe alle Analysen durch"""
        print("=== MINESEARCH V2 KONSOLIDIERTE ERGEBNISTABELLE ANALYSE ===")
        print(f"Analyse gestartet: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if not self.test_server_connection():
            print("Server nicht erreichbar - beende Analyse")
            return
            
        self.analyze_main_page_structure()
        self.test_api_endpoints()
        self.analyze_database_structure()
        self.test_csv_export_functionality()
        self.analyze_frontend_files()
        
        self.generate_report()
        
    def generate_report(self):
        """Generiere Analyse-Report"""
        print("\n=== ANALYSE-ABSCHLUSS ===")
        
        # Erstelle Report
        report = {
            "analysis_session": {
                "start_time": time.strftime('%Y-%m-%d %H:%M:%S'),
                "total_findings": len(self.findings)
            },
            "findings": self.findings,
            "summary": self.generate_summary()
        }
        
        report_file = f"/app/minesearch_v2/backend/results_table_analysis_report_{int(time.time())}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
            
        print(f"Analyse-Report gespeichert: {report_file}")
        
        # Zeige Zusammenfassung
        summary = self.generate_summary()
        print(f"\nZusammenfassung:")
        print(f"  Gesamt-Findings: {summary['total_findings']}")
        print(f"  Erfolg: {summary['success']}")
        print(f"  Warnungen: {summary['warnings']}")
        print(f"  Fehler: {summary['errors']}")
        print(f"  Status: {summary['analysis_status']}")
        
    def generate_summary(self):
        """Generiere Analyse-Zusammenfassung"""
        success_count = len([f for f in self.findings if f["status"] == "SUCCESS"])
        warning_count = len([f for f in self.findings if f["status"] == "WARNING"])
        error_count = len([f for f in self.findings if f["status"] == "ERROR"])
        
        return {
            "total_findings": len(self.findings),
            "success": success_count,
            "warnings": warning_count,
            "errors": error_count,
            "analysis_status": "COMPLETE" if error_count < 3 else "ISSUES_FOUND"
        }

if __name__ == "__main__":
    analyzer = ResultsTableAnalyzer()
    analyzer.run_comprehensive_analysis()