#!/usr/bin/env python3
"""
Author: Pattern Enhancement Researcher
Datum: 31.07.2025
Version: 1.0
Beschreibung: Test Suite für erweiterte Pattern-Erkennung

TEST-SCENARIOS:
1. "derzeit etwa [ZAHL] [EINHEIT] [ROHSTOFF] pro [ZEITRAUM]" Pattern
2. "[ROHSTOFF]. [Beschreibung] so primary commodity..." Pattern  
3. Cross-Field Pattern: Rohstoff + Menge in einem Text
4. Minentyp-Bereinigung für komplexe Auflistungen
5. Mehrsprachige Pattern-Erkennung
"""

import sys
import os
import unittest
from typing import Dict, Any

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from enhanced_extraction_patterns import (
    extract_cross_field_data,
    extract_commodity_from_explanation,
    extract_mine_type_from_complex_text,
    normalize_commodity_name,
    normalize_mine_type,
    apply_enhanced_patterns_to_field,
    enhance_field_with_patterns
)


class TestEnhancedPatterns(unittest.TestCase):
    """Test Suite für erweiterte Pattern-Erkennung"""
    
    def test_cross_field_extraction_german(self):
        """Test Cross-Field Extraktion für deutsche Texte"""
        print("\n=== TEST: Cross-Field Extraktion (Deutsch) ===")
        
        test_cases = [
            {
                "input": "derzeit etwa 270.000 Unzen Gold pro Jahr. Die Mine befindet sich in der Nähe von Eeyou Istchee James Bay in Nord-Quebec",
                "expected_commodity": "Gold",
                "expected_production": "270.000 Unzen/Jahr"
            },
            {
                "input": "produziert jährlich 50.000 Tonnen Kupfer aus dem Tagebau",
                "expected_commodity": "Kupfer", 
                "expected_production": "50.000 Tonnen/Jahr"
            },
            {
                "input": "jährliche Förderung von 1.2 Millionen Tonnen Eisenerz",
                "expected_commodity": "Eisenerz",
                "expected_production": "1.2 Millionen Tonnen/Jahr"
            }
        ]
        
        for i, case in enumerate(test_cases):
            with self.subTest(i=i):
                result = extract_cross_field_data(case["input"])
                print(f"Input: {case['input'][:60]}...")
                print(f"Expected: {case['expected_commodity']} + {case['expected_production']}")
                print(f"Got: {result['commodity']} + {result['production']}")
                
                self.assertEqual(result['commodity'], case['expected_commodity'])
                self.assertEqual(result['production'], case['expected_production'])
                print("✓ PASSED\n")
    
    def test_cross_field_extraction_english(self):
        """Test Cross-Field Extraktion für englische Texte"""
        print("\n=== TEST: Cross-Field Extraktion (Englisch) ===")
        
        test_cases = [
            {
                "input": "currently produces 125,000 ounces of gold annually from underground operations",
                "expected_commodity": "Gold",
                "expected_production": "125,000 ounces/Jahr"
            },
            {
                "input": "annual production of 80,000 tonnes copper concentrate",
                "expected_commodity": "Kupfer",
                "expected_production": "80,000 tonnes/Jahr"
            }
        ]
        
        for i, case in enumerate(test_cases):
            with self.subTest(i=i):
                result = extract_cross_field_data(case["input"])
                print(f"Input: {case['input']}")
                print(f"Expected: {case['expected_commodity']} + {case['expected_production']}")
                print(f"Got: {result['commodity']} + {result['production']}")
                
                self.assertEqual(result['commodity'], case['expected_commodity'])
                self.assertEqual(result['production'], case['expected_production'])
                print("✓ PASSED\n")
    
    def test_commodity_from_explanation(self):
        """Test Rohstoff-Extraktion aus Erklärungstexten"""
        print("\n=== TEST: Rohstoff aus Erklärungen ===")
        
        test_cases = [
            {
                "input": "Gold. Lapa is a gold mine, so primary commodity is gold",
                "expected": "Gold"
            },
            {
                "input": "Copper. This mine extracts copper ore from open pit operations",
                "expected": "Kupfer"
            },
            {
                "input": "Iron ore. The facility mines iron ore as primary commodity",
                "expected": "Eisenerz"
            },
            {
                "input": "Some random text without clear commodity pattern",
                "expected": "X"
            }
        ]
        
        for i, case in enumerate(test_cases):
            with self.subTest(i=i):
                result = extract_commodity_from_explanation(case["input"])
                print(f"Input: {case['input']}")
                print(f"Expected: {case['expected']}")
                print(f"Got: {result}")
                
                self.assertEqual(result, case['expected'])
                print("✓ PASSED\n")
    
    def test_mine_type_extraction(self):
        """Test Minentyp-Extraktion aus komplexen Texten"""
        print("\n=== TEST: Minentyp-Extraktion ===")
        
        test_cases = [
            {
                "input": "(Untertage/ Open-Pit/ usw.): Open-Pit",
                "expected": "Open-Pit"
            },
            {
                "input": "Type: Underground mining operation",
                "expected": "Untertage"
            },
            {
                "input": "Tagebau und Untertage kombiniert",
                "expected": "Tagebau/Untertage"
            },
            {
                "input": "is an open-pit mine in Quebec",
                "expected": "Open-Pit"
            },
            {
                "input": "Some text without mine type information",
                "expected": "X"
            }
        ]
        
        for i, case in enumerate(test_cases):
            with self.subTest(i=i):
                result = extract_mine_type_from_complex_text(case["input"])
                print(f"Input: {case['input']}")
                print(f"Expected: {case['expected']}")
                print(f"Got: {result}")
                
                self.assertEqual(result, case['expected'])
                print("✓ PASSED\n")
    
    def test_commodity_normalization(self):
        """Test Rohstoff-Normalisierung verschiedener Sprachen"""
        print("\n=== TEST: Rohstoff-Normalisierung ===")
        
        test_cases = [
            # Englisch → Deutsch
            ("gold", "Gold"),
            ("copper", "Kupfer"),
            ("silver", "Silber"),
            ("iron ore", "Eisenerz"),
            
            # Französisch → Deutsch  
            ("or", "Gold"),
            ("cuivre", "Kupfer"),
            ("minerai de fer", "Eisenerz"),
            
            # Spanisch → Deutsch
            ("oro", "Gold"),
            ("cobre", "Kupfer"),
            ("mineral de hierro", "Eisenerz"),
            
            # Indonesisch → Deutsch
            ("emas", "Gold"),
            ("tembaga", "Kupfer"),
            ("bijih besi", "Eisenerz"),
            
            # Unbekannt → Capitalize
            ("Lithium", "Lithium"),
            ("", "X")
        ]
        
        for input_val, expected in test_cases:
            with self.subTest(input=input_val):
                result = normalize_commodity_name(input_val)
                print(f"'{input_val}' → '{result}' (expected: '{expected}')")
                self.assertEqual(result, expected)
        
        print("✓ All normalization tests PASSED\n")
    
    def test_mine_type_normalization(self):
        """Test Minentyp-Normalisierung verschiedener Sprachen"""
        print("\n=== TEST: Minentyp-Normalisierung ===")
        
        test_cases = [
            # Englisch → Deutsch
            ("open-pit", "Open-Pit"),
            ("underground", "Untertage"),
            ("surface", "Tagebau"),
            ("quarry", "Steinbruch"),
            
            # Französisch → Deutsch
            ("ciel ouvert", "Open-Pit"),
            ("souterraine", "Untertage"),
            
            # Kombinierte Typen
            ("open-pit und underground", "Open-Pit/Untertage"),
            ("surface and underground", "Tagebau/Untertage"),
            
            # Unbekannt → Capitalize
            ("Special Type", "Special Type"),
            ("", "X")
        ]
        
        for input_val, expected in test_cases:
            with self.subTest(input=input_val):
                result = normalize_mine_type(input_val)
                print(f"'{input_val}' → '{result}' (expected: '{expected}')")
                self.assertEqual(result, expected)
        
        print("✓ All mine type normalization tests PASSED\n")
    
    def test_field_enhancement(self):
        """Test Feld-Enhancement mit erweiterten Patterns"""
        print("\n=== TEST: Feld-Enhancement ===")
        
        test_cases = [
            {
                "field": "Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)",
                "input": "Gold. Lapa is a gold mine, so primary commodity is gold",
                "expected": "Gold"
            },
            {
                "field": "Fördermenge/Jahr", 
                "input": "derzeit etwa 270.000 Unzen Gold pro Jahr",
                "expected": "270.000 Unzen/Jahr"
            },
            {
                "field": "Minentyp (Untertage/ Open-Pit/ usw.)",
                "input": "(Untertage/ Open-Pit/ usw.): Open-Pit mining",
                "expected": "Open-Pit"
            },
            {
                "field": "Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)",
                "input": "Some random text without clear patterns",
                "expected": "Some random text without clear patterns"  # Keine Verbesserung
            }
        ]
        
        for i, case in enumerate(test_cases):
            with self.subTest(i=i):
                result = apply_enhanced_patterns_to_field(case["input"], case["field"])
                print(f"Field: {case['field']}")
                print(f"Input: {case['input']}")
                print(f"Expected: {case['expected']}")
                print(f"Got: {result}")
                
                self.assertEqual(result, case['expected'])
                print("✓ PASSED\n")
    
    def test_multilingual_patterns(self):
        """Test mehrsprachige Pattern-Erkennung"""
        print("\n=== TEST: Mehrsprachige Pattern ===")
        
        # Französisch (Quebec)
        result_fr = extract_cross_field_data("production annuelle de 50.000 tonnes de cuivre")
        self.assertEqual(result_fr['commodity'], "Kupfer")
        self.assertEqual(result_fr['production'], "50.000 tonnes/Jahr")
        print("✓ Französisch: Kupfer-Produktion erkannt")
        
        # Spanisch (Südamerika)
        result_es = extract_cross_field_data("produce anualmente 75.000 onzas de oro")
        self.assertEqual(result_es['commodity'], "Gold")
        self.assertEqual(result_es['production'], "75.000 onzas/Jahr")
        print("✓ Spanisch: Gold-Produktion erkannt")
        
        # Indonesisch
        result_id = extract_cross_field_data("memproduksi 60.000 ton tembaga per tahun")
        self.assertEqual(result_id['commodity'], "Kupfer") 
        self.assertEqual(result_id['production'], "60.000 ton/Jahr")
        print("✓ Indonesisch: Kupfer-Produktion erkannt")
        
        print("✓ All multilingual tests PASSED\n")
    
    def test_integration_with_clean_field_value(self):
        """Test Integration mit bestehender clean_field_value Logik"""
        print("\n=== TEST: Integration mit clean_field_value ===")
        
        test_cases = [
            {
                "field": "Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)",
                "input": "X",  # Bereits bereinigter "leer" Wert
                "original": "Gold. This is a gold mining operation so primary commodity is gold",
                "expected": "Gold"  # Sollte Pattern anwenden
            },
            {
                "field": "Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)",
                "input": "Kupfer",  # Bereits guter Wert
                "original": "Kupfer",
                "expected": "Kupfer"  # Sollte unverändert bleiben
            }
        ]
        
        for i, case in enumerate(test_cases):
            with self.subTest(i=i):
                # Simuliere enhance_field_with_patterns Aufruf
                if case["input"] in ["X", "N/A", "", "LEER"]:
                    result = apply_enhanced_patterns_to_field(case["original"], case["field"])
                else:
                    result = case["input"]
                
                print(f"Field: {case['field']}")
                print(f"Clean value: {case['input']}")
                print(f"Original: {case['original'][:50]}...")
                print(f"Expected: {case['expected']}")
                print(f"Got: {result}")
                
                self.assertEqual(result, case['expected'])
                print("✓ PASSED\n")


def run_enhanced_pattern_tests():
    """Führt alle Tests für erweiterte Pattern aus"""
    print("🔍 ERWEITERTE PATTERN-ERKENNUNG TEST SUITE")
    print("=" * 60)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestEnhancedPatterns)
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("✅ ALLE TESTS ERFOLGREICH!")
    else:
        print(f"❌ {len(result.failures)} Fehler, {len(result.errors)} Errors")
        
        for test, traceback in result.failures:
            print(f"\nFEHLER in {test}:")
            print(traceback)
            
        for test, traceback in result.errors:
            print(f"\nERROR in {test}:")
            print(traceback)
    
    print(f"\nTests gelaufen: {result.testsRun}")
    print(f"Erfolgreich: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Fehlgeschlagen: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_enhanced_pattern_tests()
    sys.exit(0 if success else 1)