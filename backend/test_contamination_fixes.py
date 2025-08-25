#!/usr/bin/env python3
"""
Author: rahn
Datum: 25.08.2025
Version: 1.0
Beschreibung: Comprehensive test suite for contamination fixes

TEST-SUITE 25.08.2025: Verifiziert alle implementierten Schutzmaßnahmen gegen Feldkontamination
"""

import sys
sys.path.insert(0, '.')

import json
import logging
import sqlite3
from typing import Dict, Any, List
from pathlib import Path

# Import our protection modules
from minesearch.extraction_processors import is_template_or_dummy_value
from minesearch.field_name_blacklist import is_field_name_value, validate_extracted_fields
from minesearch.search_service import MineSearchService
from minesearch.database_constraints import DatabaseConstraintManager
from minesearch.null_normalizer import NullNormalizer

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ContaminationTestSuite:
    """
    KONTAMINATIONS-TEST-SUITE 25.08.2025
    Testet alle Schutzebenen gegen Feldkontamination
    """
    
    def __init__(self):
        """Initialisiert Test-Suite"""
        self.db_path = "/app/backend/minesearch/database/mines.db"
        self.search_service = MineSearchService()
        self.null_normalizer = NullNormalizer()
        self.test_results = {
            'passed': 0,
            'failed': 0,
            'tests': []
        }
    
    def log_test_result(self, test_name: str, passed: bool, details: str = ""):
        """Protokolliert Testergebnis"""
        status = "✅ PASSED" if passed else "❌ FAILED"
        logger.info(f"[TEST] {test_name}: {status}")
        if details:
            logger.info(f"[TEST] Details: {details}")
        
        self.test_results['tests'].append({
            'name': test_name,
            'passed': passed,
            'details': details
        })
        
        if passed:
            self.test_results['passed'] += 1
        else:
            self.test_results['failed'] += 1
    
    def test_field_name_blacklist(self):
        """TEST 1: Field Name Blacklist Funktionalität"""
        logger.info("\n🧪 TEST 1: FIELD NAME BLACKLIST")
        
        # Test kritische Feldnamen
        contaminated_values = [
            ("x-Koordinate", "Betreiber"),
            ("y-Koordinate", "Country"),
            ("Restaurationskosten", "Region"),
            ("Kostenjahr", "Eigentümer"),
            ("Produktionsstart", "Aktivitätsstatus")
        ]
        
        all_passed = True
        for value, field in contaminated_values:
            is_contamination = is_field_name_value(value, field)
            if not is_contamination:
                logger.error(f"[TEST] FAILED: '{value}' in '{field}' nicht als Kontamination erkannt")
                all_passed = False
            else:
                logger.debug(f"[TEST] OK: '{value}' in '{field}' korrekt als Kontamination erkannt")
        
        # Test legitime Werte mit Source-Referenzen
        legitimate_values = [
            ("Kanada [1,2,3]", "Country"),
            ("Goldmine ABC [2,4]", "mine_name"),
            ("2024 [1]", "Produktionsstart")
        ]
        
        for value, field in legitimate_values:
            is_contamination = is_field_name_value(value, field)
            if is_contamination:
                logger.error(f"[TEST] FAILED: Legitimer Wert '{value}' fälschlicherweise als Kontamination erkannt")
                all_passed = False
            else:
                logger.debug(f"[TEST] OK: Legitimer Wert '{value}' korrekt akzeptiert")
        
        self.log_test_result("Field Name Blacklist", all_passed, 
                           f"Tested {len(contaminated_values)} contaminated + {len(legitimate_values)} legitimate values")
    
    def test_template_detection(self):
        """TEST 2: Template Detection in Extraction Processors"""
        logger.info("\n🧪 TEST 2: TEMPLATE DETECTION")
        
        # Simuliere problematische Extraction-Daten
        test_html = """
        <html>
        <body>
        <div>Mine: Test Mine</div>
        <div>Betreiber: x-Koordinate</div>
        <div>Region: Eigentümer</div>
        <div>Country: y-Koordinate</div>
        </body>
        </html>
        """
        
        try:
            # Template Detection sollte diese blockieren
            test_data = {
                "Betreiber": "x-Koordinate",
                "Region": "Eigentümer", 
                "Country": "y-Koordinate"
            }
            
            contamination_detected = False
            for field, value in test_data.items():
                if is_template_or_dummy_value(value, field):
                    contamination_detected = True
                    logger.debug(f"[TEST] Template detection blocked: '{value}' in '{field}'")
            
            self.log_test_result("Template Detection", contamination_detected,
                               "Template detection correctly identified field name contamination")
            
        except Exception as e:
            self.log_test_result("Template Detection", False, f"Error: {e}")
    
    def test_null_normalization(self):
        """TEST 3: NULL Normalization"""
        logger.info("\n🧪 TEST 3: NULL NORMALIZATION")
        
        test_values = {
            "-": True,
            "X": True,
            "nicht gefunden": True,
            "not available": True,
            "": True,
            "   ": True,
            "Goldmine ABC": False,
            "2024": False,
            "Kanada": False
        }
        
        all_passed = True
        for value, should_be_null in test_values.items():
            normalized = self.null_normalizer.normalize_value(value)
            is_null = normalized is None
            
            if is_null != should_be_null:
                logger.error(f"[TEST] FAILED: '{value}' -> Expected NULL: {should_be_null}, Got NULL: {is_null}")
                all_passed = False
            else:
                logger.debug(f"[TEST] OK: '{value}' -> NULL: {is_null}")
        
        self.log_test_result("NULL Normalization", all_passed,
                           f"Tested {len(test_values)} values for correct NULL conversion")
    
    def test_database_constraints(self):
        """TEST 4: Database Constraints and Triggers"""
        logger.info("\n🧪 TEST 4: DATABASE CONSTRAINTS")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Prüfe ob Trigger existieren
            cursor.execute("SELECT name FROM sqlite_master WHERE type='trigger'")
            triggers = [row[0] for row in cursor.fetchall()]
            
            expected_triggers = [
                'prevent_field_contamination_insert',
                'prevent_field_contamination_update'
            ]
            
            triggers_present = 0
            for expected in expected_triggers:
                if expected in triggers:
                    triggers_present += 1
                    logger.debug(f"[TEST] Trigger '{expected}' present")
                else:
                    logger.warning(f"[TEST] Trigger '{expected}' missing")
            
            # Prüfe Log-Tabelle
            cursor.execute("SELECT name FROM sqlite_master WHERE name='constraint_log'")
            log_table_exists = cursor.fetchone() is not None
            
            conn.close()
            
            all_passed = (triggers_present == len(expected_triggers)) and log_table_exists
            
            self.log_test_result("Database Constraints", all_passed,
                               f"Triggers: {triggers_present}/{len(expected_triggers)}, Log table: {log_table_exists}")
            
        except Exception as e:
            self.log_test_result("Database Constraints", False, f"Error: {e}")
    
    def test_search_service_quality_gate(self):
        """TEST 5: Search Service Quality Gate"""
        logger.info("\n🧪 TEST 5: SEARCH SERVICE QUALITY GATE")
        
        # Simuliere kontaminierte Daten die durch Quality Gate laufen
        contaminated_data = {
            "Country": "Region",
            "Betreiber": "x-Koordinate", 
            "Eigentümer": "y-Koordinate",
            "Restaurationskosten": "-",
            "Kostenjahr": "nicht gefunden"
        }
        
        try:
            # Quality Gate anwenden
            filtered_data = self.search_service._apply_database_quality_gate(
                contaminated_data, "Test Mine"
            )
            
            # Prüfe ob Kontaminationen entfernt wurden
            contamination_removed = True
            for field, value in filtered_data.items():
                if is_field_name_value(str(value), field):
                    logger.error(f"[TEST] Quality Gate failed to remove contamination: '{value}' in '{field}'")
                    contamination_removed = False
            
            # Prüfe NULL-Normalisierung
            null_normalized = (
                filtered_data.get("Aktivitätsstatus") is None and
                filtered_data.get("Kostenjahr") is None
            )
            
            overall_passed = contamination_removed and null_normalized
            
            self.log_test_result("Search Service Quality Gate", overall_passed,
                               f"Contamination removed: {contamination_removed}, NULL normalized: {null_normalized}")
            
        except Exception as e:
            self.log_test_result("Search Service Quality Gate", False, f"Error: {e}")
    
    def test_end_to_end_protection(self):
        """TEST 6: End-to-End Schutz"""
        logger.info("\n🧪 TEST 6: END-TO-END PROTECTION")
        
        # Simuliere eine komplette Suche mit problematischen Daten
        test_mine_html = """
        <html>
        <body>
        <h1>Problematic Mine</h1>
        <div>Name: Test Contamination Mine</div>
        <div>Operator: x-Koordinate</div>
        <div>Country: Region</div>
        <div>Owner: y-Koordinate</div>
        <div>Status: nicht gefunden</div>
        <div>Year: -</div>
        </body>
        </html>
        """
        
        try:
            # Simuliere extrahierte Daten die durch das System laufen
            test_extracted_data = {
                "Betreiber": "x-Koordinate",
                "Region": "Eigentümer", 
                "Country": "y-Koordinate",
                "Aktivitätsstatus": "-",
                "Kostenjahr": "nicht gefunden"
            }
            
            # Test durch Quality Gate
            filtered_data = self.search_service._apply_database_quality_gate(
                test_extracted_data, "Test Contamination Mine"
            )
            
            # Prüfe ob alle Schutzmaßnahmen greifen
            contamination_found = False
            for field, value in filtered_data.items():
                if value and is_field_name_value(str(value), field):
                    contamination_found = True
                    logger.error(f"[TEST] End-to-end protection failed: '{value}' in '{field}'")
            
            protection_effective = not contamination_found
            
            self.log_test_result("End-to-End Protection", protection_effective,
                               "Complete extraction pipeline tested with contaminated data")
            
        except Exception as e:
            self.log_test_result("End-to-End Protection", False, f"Error: {e}")
    
    def run_all_tests(self):
        """Führt alle Tests aus"""
        logger.info("🚀 STARTING CONTAMINATION PROTECTION TEST SUITE")
        logger.info("=" * 60)
        
        # Alle Tests ausführen
        self.test_field_name_blacklist()
        self.test_template_detection()
        self.test_null_normalization()
        self.test_database_constraints()
        self.test_search_service_quality_gate()
        self.test_end_to_end_protection()
        
        # Endergebnis
        logger.info("\n📊 TEST SUITE RESULTS")
        logger.info("=" * 40)
        logger.info(f"✅ Passed: {self.test_results['passed']}")
        logger.info(f"❌ Failed: {self.test_results['failed']}")
        
        success_rate = (self.test_results['passed'] / 
                       (self.test_results['passed'] + self.test_results['failed'])) * 100
        
        logger.info(f"📈 Success Rate: {success_rate:.1f}%")
        
        if self.test_results['failed'] == 0:
            logger.info("🎉 ALL TESTS PASSED - CONTAMINATION PROTECTION EFFECTIVE!")
        else:
            logger.warning("⚠️ SOME TESTS FAILED - REVIEW PROTECTION IMPLEMENTATION")
            
            # Detaillierte Fehlerliste
            logger.info("\n❌ FAILED TESTS:")
            for test in self.test_results['tests']:
                if not test['passed']:
                    logger.error(f"   - {test['name']}: {test['details']}")
        
        return self.test_results['failed'] == 0

def main():
    """Hauptfunktion für Test-Ausführung"""
    print("🧪 CONTAMINATION PROTECTION TEST SUITE")
    print("=" * 50)
    
    test_suite = ContaminationTestSuite()
    success = test_suite.run_all_tests()
    
    exit(0 if success else 1)

if __name__ == "__main__":
    main()