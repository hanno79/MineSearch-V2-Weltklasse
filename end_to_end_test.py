#!/usr/bin/env python3
"""
Author: rahn
Datum: 22.08.2025
Version: 1.0
Beschreibung: End-to-End Workflow-Test für MineSearch
"""

import requests
import time
import json
import sys

# Konfigurierbare Validierungsregeln für 'structured_data'
# Leere Liste bedeutet: keine Pflichtfelder; alle vorhandenen werden validiert
EXPECTED_STRUCTURED_KEYS = []
# Zahlenbereiche pro Feldname, z.B. {'score': (0, 1), 'year': (1900, 2100)}
NUMERIC_FIELD_RANGES = {}

class MineSearchE2ETest:
    def __init__(self):
        self.api_base = "http://localhost:8000"
        self.test_results = []
    
    def log(self, message, status="INFO"):
        emoji = {"INFO": "ℹ️", "SUCCESS": "✅", "ERROR": "❌", "WARNING": "⚠️"}
        print(f"{emoji.get(status, 'ℹ️')} {message}")
        self.test_results.append({"message": message, "status": status})
    
    def test_models_endpoint(self):
        """Test Models-Info Endpoint"""
        self.log("Teste Models-Info Endpoint...")
        try:
            response = requests.get(f"{self.api_base}/api/models", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and 'models' in data:
                    model_count = len(data['models'])
                    self.log(f"Models-Endpoint: {model_count} Modelle verfügbar", "SUCCESS")
                    return True
                else:
                    self.log(f"Models-Endpoint: Ungültige Antwortstruktur", "ERROR")
                    return False
            else:
                self.log(f"Models-Endpoint: HTTP {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"Models-Endpoint Fehler: {str(e)}", "ERROR")
            return False
    
    def test_search_workflow(self):
        """Test kompletter Search-Workflow"""
        self.log("Teste kompletten Search-Workflow...")
        try:
            # 1. Suche starten
            search_data = {
                "mine_name": "Test Mine E2E",
                "model": "openrouter:deepseek-free",
                "search_type": "quick"
            }
            
            response = requests.post(
                f"{self.api_base}/api/search",
                json=search_data,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code != 200:
                self.log(f"Search fehlgeschlagen: HTTP {response.status_code}", "ERROR")
                return False
            
            result = response.json()
            if not result.get('success'):
                self.log(f"Search fehlgeschlagen: {result.get('error', 'Unbekannter Fehler')}", "ERROR")
                return False
            
            # 2. Ergebnis prüfen
            data = result.get('data', {})
            structured = data.get('structured_data')

            # Validierung 'structured_data'
            if not isinstance(structured, dict):
                self.log("Search: 'structured_data' fehlt oder ist kein Objekt", "WARNING")
                return False

            if len(structured) == 0:
                self.log("Search: 'structured_data' ist leer", "WARNING")
                return False

            expected_keys = EXPECTED_STRUCTURED_KEYS
            numeric_ranges = NUMERIC_FIELD_RANGES

            def _is_valid_value(field_name, value):
                if value is None:
                    return False, "ist None"
                if isinstance(value, str):
                    if value.strip() == "":
                        return False, "leerer/Whitespace-String"
                    return True, ""
                if isinstance(value, (list, tuple)):
                    if len(value) == 0:
                        return False, "leere Liste"
                    return True, ""
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    if field_name in numeric_ranges:
                        min_v, max_v = numeric_ranges[field_name]
                        if value < min_v or value > max_v:
                            return False, f"Wert {value} außerhalb Bereich [{min_v}, {max_v}]"
                    return True, ""
                # Für andere Typen: Wahrheitswert prüfen
                if not value:
                    return False, f"ungültiger Wert vom Typ {type(value).__name__}"
                return True, ""

            invalid_fields = []
            filled_fields = 0

            # Validierung aller vorhandenen Felder
            for key, val in structured.items():
                ok, reason = _is_valid_value(key, val)
                if ok:
                    filled_fields += 1
                else:
                    invalid_fields.append(f"{key} ({reason})")

            # Pflichtfelder prüfen
            missing_required = []
            invalid_required = []
            if expected_keys:
                for key in expected_keys:
                    if key not in structured:
                        missing_required.append(key)
                    else:
                        ok, reason = _is_valid_value(key, structured[key])
                        if not ok:
                            invalid_required.append(f"{key} ({reason})")

            # Ergebnis entscheiden
            # Regel:
            # - Wenn EXPECTED_STRUCTURED_KEYS definiert: alle Pflichtfelder müssen vorhanden und gültig sein
            # - Wenn nicht definiert: alle vorhandenen Felder müssen gültig sein
            if expected_keys:
                if missing_required:
                    self.log(f"Search: Fehlende Pflichtfelder: {', '.join(missing_required)}", "WARNING")
                if invalid_required:
                    self.log(f"Search: Ungültige Pflichtfelder: {', '.join(invalid_required)}", "WARNING")
                if invalid_fields:
                    self.log(f"Search: Ungültige optionale Felder: {', '.join(invalid_fields)}", "WARNING")
                if not missing_required and not invalid_required:
                    self.log(f"Search erfolgreich: {filled_fields}/{len(structured)} Felder gültig", "SUCCESS")
                    return True
                else:
                    return False
            else:
                if invalid_fields:
                    self.log(f"Search: Ungültige Felder: {', '.join(invalid_fields)}", "WARNING")
                    return False
                self.log(f"Search erfolgreich: {filled_fields}/{len(structured)} Felder gültig", "SUCCESS")
                return True
                
        except Exception as e:
            self.log(f"Search-Workflow Fehler: {str(e)}", "ERROR")
            return False
    
    def test_statistics_endpoint(self):
        """Test Statistics-Endpoint"""
        self.log("Teste Statistics-Endpoint...")
        try:
            response = requests.get(f"{self.api_base}/api/statistics/overview", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'system_health' in data and 'search_performance' in data:
                    self.log("Statistics-Endpoint funktioniert", "SUCCESS")
                    return True
                else:
                    self.log("Statistics: Ungültige Datenstruktur", "ERROR")
                    return False
            else:
                self.log(f"Statistics: HTTP {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"Statistics Fehler: {str(e)}", "ERROR")
            return False
    
    def test_static_files(self):
        """Test Static Files"""
        self.log("Teste Static Files...")
        try:
            # Test Frontend
            response = requests.get(f"{self.api_base}/static/index.html", timeout=10)
            if response.status_code == 200 and "MineSearch" in response.text:
                self.log("Frontend HTML verfügbar", "SUCCESS")
            else:
                self.log(f"Frontend HTML Problem: HTTP {response.status_code}", "WARNING")
            
            # Test JavaScript
            response = requests.get(f"{self.api_base}/static/api.js", timeout=10)
            if response.status_code == 200:
                self.log("JavaScript-Dateien verfügbar", "SUCCESS")
                return True
            else:
                self.log(f"JavaScript Problem: HTTP {response.status_code}", "WARNING")
                return False
                
        except Exception as e:
            self.log(f"Static Files Fehler: {str(e)}", "ERROR")
            return False
    
    def test_error_handling(self):
        """Test Error-Handling"""
        self.log("Teste Error-Handling...")
        try:
            # Teste ungültige Search-Anfrage
            invalid_data = {
                "mine_name": "",  # Leerer Name
                "model": "invalid-model",
                "search_type": "invalid"
            }
            
            response = requests.post(
                f"{self.api_base}/api/search",
                json=invalid_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            # Sollte Fehler zurückgeben
            if response.status_code == 422:  # Validation Error
                self.log("Error-Handling funktioniert (Validation)", "SUCCESS")
                return True
            elif response.status_code != 200:
                self.log(f"Error-Handling funktioniert (HTTP {response.status_code})", "SUCCESS")
                return True
            else:
                result = response.json()
                if not result.get('success'):
                    self.log("Error-Handling funktioniert (API Level)", "SUCCESS")
                    return True
                else:
                    self.log("Error-Handling unvollständig", "WARNING")
                    return False
                    
        except Exception as e:
            self.log(f"Error-Handling Test Fehler: {str(e)}", "ERROR")
            return False
    
    def run_all_tests(self):
        """Führt alle Tests aus"""
        self.log("🚀 Starte End-to-End Tests...")
        
        tests = [
            ("Models-Endpoint", self.test_models_endpoint),
            ("Search-Workflow", self.test_search_workflow),
            ("Statistics-Endpoint", self.test_statistics_endpoint),
            ("Static Files", self.test_static_files),
            ("Error-Handling", self.test_error_handling),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            self.log(f"\n--- {test_name} ---")
            if test_func():
                passed += 1
        
        self.log(f"\n📊 TESTERGEBNISSE: {passed}/{total} Tests bestanden")
        
        if passed == total:
            self.log("🎉 ALLE TESTS ERFOLGREICH!", "SUCCESS")
            return True
        else:
            self.log(f"⚠️ {total - passed} Tests fehlgeschlagen", "WARNING")
            return False

if __name__ == "__main__":
    tester = MineSearchE2ETest()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)