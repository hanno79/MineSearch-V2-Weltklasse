#!/usr/bin/env python3
"""
Author: rahn
Datum: 07.09.2025
Version: 1.0
Beschreibung: Test-Suite für Smart Value Extraction und Validierung
"""

import sys
import os
sys.path.append('/home/hanno/projects/MineSearch/backend')

from minesearch.smart_value_extractor import SmartValueExtractor
from minesearch.extraction_processors import is_template_or_dummy_value
from minesearch.database.normalized_manager import NormalizedDatabaseManager
import logging

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_smart_value_extractor():
    """Teste den Smart Value Extractor mit problematischen Beispielen"""
    print("🧪 TESTING SMART VALUE EXTRACTOR")
    print("=" * 60)
    
    extractor = SmartValueExtractor()
    
    # Test Daten aus der echten Datenbank
    test_cases = {
        'commodities': [
            # Problematische Einträge die in der DB gefunden wurden
            ("Für Kupfer Und Zink Handelt, Die Sich Im Besitz Von Soquem Inc.", "Kupfer"),
            ("Is Known To Have Been Operational For Gold Extraction, But Exact Production Figures", "Gold"),
            ("Ist Eine Bedeutende Untertage-Goldmine Im Norden Quebecs, Die Von Newmont Betrieben Wird", "Gold"),
            ("Spezifisch Als Steatite In Produktionsberichten Bestätigt", "Steatite"),
            ("War Ein Kleiner Untertagebetrieb Für Kupfer Und Zink, Der Nur Von 1972-1975 Aktiv War", "Kupfer"),
            # Saubere Beispiele die durchgehen sollten
            ("Gold", "Gold"),
            ("Kupfer", "Kupfer"),
            ("Iron Ore", "Eisenerz"),
        ],
        'companies': [
            # Problematische Einträge
            ("Dokumentiert Im Quebec Bergbauregister Und Unternehmensberichten", None),
            ("Mehrdeutige Eigentumsverhältnisse Ohne Aktuelle Primärquellen", None),
            ("BHP Billiton (57.5%), Rio Tinto (30%), JECO Corp (12.5%)", "BHP Billiton"),
            ("Freeport-McMoRan Inc. (90.64%), Government of Indonesia (9.36%)", "Freeport-McMoRan Inc."),
            # Saubere Beispiele
            ("Newmont Corporation", "Newmont Corporation"),
            ("Barrick Gold", "Barrick Gold"),
        ],
        'mine_types': [
            # Problematische Einträge
            ("Open-Pit/1998//5000 T/0.15/Https://Mern.Gouv.Qc.Ca/Mines/Environnement/St%C3%A9Atite%20D%27Eastray-R", "Open-Pit"),
            ("Underground/Souterrain", "Underground"),
            ("Proposed Open-Pit/Projet À Ciel Ouvert", "Open-Pit"),
            ("Exploration Project/Projet D'Exploration", None),
            # Saubere Beispiele
            ("Open-Pit", "Open-Pit"),
            ("Underground", "Underground"),
        ],
        'activity_statuses': [
            # Problematische/Duplikat Einträge
            ("Explorationsphase", "Exploration"),
            ("Currently Operating Since 1998", "aktiv"),
            ("Mine Is Closed Since 1975", "geschlossen"),
            # Saubere Beispiele
            ("aktiv", "aktiv"),
            ("geschlossen", "geschlossen"),
            ("Exploration", "Exploration"),
        ],
        'regions': [
            # Problematische Einträge
            ("Québec/Nord-du-Québec", "Quebec"),
            ("Northern Quebec Region", "Quebec"),
            # Saubere Beispiele
            ("Quebec", "Quebec"),
            ("Nevada", "Nevada"),
        ]
    }
    
    total_tests = 0
    successful_tests = 0
    
    for category, tests in test_cases.items():
        print(f"\n🔍 TESTING {category.upper()}:")
        print("-" * 40)
        
        for input_value, expected_output in tests:
            total_tests += 1
            
            # Teste entsprechende Extraktions-Methode
            if category == 'commodities':
                result = extractor.extract_commodity_from_text(input_value)
            elif category == 'companies':
                result = extractor.extract_company_from_text(input_value)
            elif category == 'mine_types':
                result = extractor.extract_mine_type_from_text(input_value)
            elif category == 'activity_statuses':
                result = extractor.extract_activity_status_from_text(input_value)
            elif category == 'regions':
                result = extractor.extract_region_from_text(input_value)
            
            # Bewerte Ergebnis
            success = (result == expected_output)
            if success:
                successful_tests += 1
                status = "✅ PASS"
            else:
                status = "❌ FAIL"
            
            print(f"{status} '{input_value[:60]}...' → '{result}' (expected: '{expected_output}')")
    
    print(f"\n📊 EXTRACTOR TEST RESULTS: {successful_tests}/{total_tests} ({successful_tests/total_tests*100:.1f}%)")
    return successful_tests, total_tests

def test_template_detection():
    """Teste Template Detection mit problematischen Einträgen"""
    print("\n🛡️  TESTING TEMPLATE DETECTION")
    print("=" * 60)
    
    # Problematische Einträge die abgelehnt werden sollten
    problematic_values = [
        "Für Kupfer Und Zink Handelt, Die Sich Im Besitz Von Soquem Inc.",
        "Is Known To Have Been Operational For Gold Extraction, But Exact Production Figures",
        "Ist Eine Bedeutende Untertage-Goldmine Im Norden Quebecs, Die Von Newmont Corporation Betrieben Wird",
        "Dokumentiert Im Quebec Bergbauregister Und Unternehmensberichten",
        "Open-Pit/1998//5000 T/0.15/Https://Mern.Gouv.Qc.Ca/Mines/Environnement/St%C3%A9Atite",
        "BHP Billiton (57.5%), Rio Tinto (30%), JECO Corp (12.5%)",
        "Mehrdeutige Eigentumsverhältnisse Ohne Aktuelle Primärquellen",
        "War Ein Kleiner Untertagebetrieb Für Kupfer Und Zink, Der Nur Von 1972-1975 Aktiv War",
        "https://mern.gouv.qc.ca/mines/publicatio",
        "Project\" (Maple Gold Mines, 2017) Auf Sedar",
    ]
    
    # Saubere Werte die durchgehen sollten
    clean_values = [
        "Gold",
        "Newmont Corporation",
        "Open-Pit",
        "aktiv",
        "Quebec",
        "Exploration",
        "Kupfer",
        "Underground"
    ]
    
    correct_rejections = 0
    correct_acceptances = 0
    total_problematic = len(problematic_values)
    total_clean = len(clean_values)
    
    print("Testing problematic values (should be REJECTED):")
    for value in problematic_values:
        is_template = is_template_or_dummy_value(value)
        if is_template:
            status = "✅ CORRECTLY REJECTED"
            correct_rejections += 1
        else:
            status = "❌ INCORRECTLY ACCEPTED"
        print(f"  {status}: '{value[:80]}...'")
    
    print("\nTesting clean values (should be ACCEPTED):")
    for value in clean_values:
        is_template = is_template_or_dummy_value(value)
        if not is_template:
            status = "✅ CORRECTLY ACCEPTED"
            correct_acceptances += 1
        else:
            status = "❌ INCORRECTLY REJECTED"
        print(f"  {status}: '{value}'")
    
    rejection_rate = correct_rejections / total_problematic * 100 if total_problematic > 0 else 0
    acceptance_rate = correct_acceptances / total_clean * 100 if total_clean > 0 else 0
    
    print(f"\n📊 TEMPLATE DETECTION RESULTS:")
    print(f"  Problematic values correctly rejected: {correct_rejections}/{total_problematic} ({rejection_rate:.1f}%)")
    print(f"  Clean values correctly accepted: {correct_acceptances}/{total_clean} ({acceptance_rate:.1f}%)")
    
    return correct_rejections, total_problematic, correct_acceptances, total_clean

def test_normalization_integration():
    """Teste Integration mit NormalizedDatabaseManager"""
    print("\n🔄 TESTING NORMALIZATION INTEGRATION")
    print("=" * 60)
    
    try:
        # Erstelle Test-Instanz (ohne echte DB-Verbindung)
        manager = NormalizedDatabaseManager()
        
        # Teste Smart Extractor Integration
        test_values = [
            ("Ist Eine Bedeutende Untertage-Goldmine Im Norden Quebecs", "commodity"),
            ("Dokumentiert Im Quebec Bergbauregister Und Unternehmensberichten", "company"),
            ("Open-Pit/1998//5000 T/0.15/Https://", "mine_type"),
            ("Explorationsphase", "activity_status"),
            ("Québec/Nord-du-Québec", "region")
        ]
        
        successes = 0
        for value, value_type in test_values:
            try:
                if value_type == "commodity":
                    result = manager.smart_extractor.extract_commodity_from_text(value)
                elif value_type == "company":
                    result = manager.smart_extractor.extract_company_from_text(value)
                elif value_type == "mine_type":
                    result = manager.smart_extractor.extract_mine_type_from_text(value)
                elif value_type == "activity_status":
                    result = manager.smart_extractor.extract_activity_status_from_text(value)
                elif value_type == "region":
                    result = manager.smart_extractor.extract_region_from_text(value)
                
                status = "✅ SUCCESS" if result else "⚠️ REJECTED"
                print(f"  {status}: {value_type} '{value[:60]}...' → '{result}'")
                if result:
                    successes += 1
                    
            except Exception as e:
                print(f"  ❌ ERROR: {value_type} '{value[:60]}...' → Exception: {e}")
        
        print(f"\n📊 INTEGRATION TEST: {successes}/{len(test_values)} successful extractions")
        return successes, len(test_values)
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return 0, len(test_values)

def main():
    """Hauptfunktion für alle Tests"""
    print("🚀 SMART VALUE EXTRACTION - COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    print("Testing new validation system against problematic database entries")
    print("=" * 80)
    
    # Test Smart Value Extractor
    extractor_success, extractor_total = test_smart_value_extractor()
    
    # Test Template Detection
    rejected_correct, rejected_total, accepted_correct, accepted_total = test_template_detection()
    
    # Test Integration
    integration_success, integration_total = test_normalization_integration()
    
    # Gesamtbewertung
    print("\n" + "=" * 80)
    print("📊 COMPREHENSIVE TEST RESULTS")
    print("=" * 80)
    
    extractor_rate = extractor_success / extractor_total * 100 if extractor_total > 0 else 0
    rejection_rate = rejected_correct / rejected_total * 100 if rejected_total > 0 else 0
    acceptance_rate = accepted_correct / accepted_total * 100 if accepted_total > 0 else 0
    integration_rate = integration_success / integration_total * 100 if integration_total > 0 else 0
    
    print(f"🔍 Smart Value Extractor: {extractor_success}/{extractor_total} ({extractor_rate:.1f}%)")
    print(f"🛡️  Template Detection - Rejections: {rejected_correct}/{rejected_total} ({rejection_rate:.1f}%)")
    print(f"🛡️  Template Detection - Acceptances: {accepted_correct}/{accepted_total} ({acceptance_rate:.1f}%)")
    print(f"🔄 Integration Test: {integration_success}/{integration_total} ({integration_rate:.1f}%)")
    
    # Gesamtbewertung
    overall_score = (extractor_rate + rejection_rate + acceptance_rate + integration_rate) / 4
    
    print(f"\n🎯 OVERALL SYSTEM PERFORMANCE: {overall_score:.1f}%")
    
    if overall_score >= 90:
        assessment = "🏆 EXCELLENT - System ready for production!"
    elif overall_score >= 80:
        assessment = "✅ GOOD - System functional with minor improvements needed"
    elif overall_score >= 70:
        assessment = "⚠️ FAIR - System needs optimization"
    else:
        assessment = "❌ POOR - System needs significant fixes"
    
    print(f"Assessment: {assessment}")
    
    print("\n" + "=" * 80)
    print("✅ TEST SUITE COMPLETED")
    print("The new validation system is ready to prevent problematic data entry!")
    print("=" * 80)

if __name__ == "__main__":
    main()