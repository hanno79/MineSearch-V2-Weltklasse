#!/usr/bin/env python3
"""
COMPREHENSIVE PROMPT OPTIMIZATION TEST
Testet alle 18 CSV_COLUMNS auf verbesserte Anti-Template Prompts

Author: rahn
Datum: 20.08.2025
Version: 1.0
"""

import sys
sys.path.append('/app/backend')

from minesearch.specialized_prompts_impl import SpecializedPrompts
from minesearch.config.base import CSV_COLUMNS

def test_enhanced_prompt_system():
    """Testet das verbesserte Anti-Template Prompt System"""
    
    print("🧪 COMPREHENSIVE PROMPT OPTIMIZATION TEST")
    print("=" * 60)
    print(f"🎯 Testet alle {len(CSV_COLUMNS)} CSV_COLUMNS auf Anti-Template Qualität")
    print("")
    
    # Test 1: Universal Anti-Template Instructions
    print("1️⃣ UNIVERSAL ANTI-TEMPLATE INSTRUCTIONS:")
    print("-" * 50)
    anti_template = SpecializedPrompts.get_universal_anti_template_instructions()
    
    # Prüfe auf wichtige Anti-Template Elemente
    template_checks = [
        ("TEMPLATE: verboten", "TEMPLATE:" in anti_template),
        ("Not specified verboten", "Not specified" in anti_template),
        ("/usw. Pattern verboten", "/usw." in anti_template),
        ("$1.0 million verboten", "$1.0 million" in anti_template),
        ("Quality Self-Check", "QUALITY SELF-CHECK" in anti_template),
        ("Goldene Regel", "GOLDENE REGEL" in anti_template)
    ]
    
    for check_name, result in template_checks:
        status = "✅" if result else "❌"
        print(f"{status} {check_name}: {'Implementiert' if result else 'FEHLT'}")
    
    print("")
    
    # Test 2: Field-Specific Instructions für alle 18 Felder
    print("2️⃣ FIELD-SPECIFIC INSTRUCTIONS - ALL 18 CSV_COLUMNS:")
    print("-" * 50)
    
    field_instructions = SpecializedPrompts.get_csv_field_quality_instructions()
    
    # Prüfe alle 18 CSV_COLUMNS
    csv_field_coverage = []
    for i, field in enumerate(CSV_COLUMNS, 1):
        # Prüfe ob Feld in den Instructions erwähnt wird
        field_found = str(i) + "." in field_instructions or field.upper() in field_instructions.upper()
        csv_field_coverage.append((field, field_found))
        status = "✅" if field_found else "❌"
        print(f"{status} {field}: {'Abgedeckt' if field_found else 'NICHT GEFUNDEN'}")
    
    covered_fields = sum(1 for _, found in csv_field_coverage if found)
    coverage_percent = (covered_fields / len(CSV_COLUMNS)) * 100
    
    print(f"\n📊 FIELD COVERAGE: {covered_fields}/{len(CSV_COLUMNS)} = {coverage_percent:.1f}%")
    
    print("")
    
    # Test 3: Quality Gate Instructions
    print("3️⃣ UNIVERSAL QUALITY GATE INSTRUCTIONS:")
    print("-" * 50)
    
    quality_gate = SpecializedPrompts.get_universal_quality_gate_instructions()
    
    quality_checks = [
        ("Template-Pattern Check", "TEMPLATE-PATTERN CHECK" in quality_gate),
        ("Konkretheit Check", "KONKRETHEIT CHECK" in quality_gate),
        ("Qualitäts-Entscheidung", "QUALITÄTS-ENTSCHEIDUNG" in quality_gate),
        ("Final Check", "FINAL CHECK" in quality_gate),
        ("Goldene Regel", "GOLDENE REGEL" in quality_gate)
    ]
    
    for check_name, result in quality_checks:
        status = "✅" if result else "❌"
        print(f"{status} {check_name}: {'Vorhanden' if result else 'FEHLT'}")
    
    print("")
    
    # Test 4: Enhanced Prompt Integration
    print("4️⃣ ENHANCED PROMPT INTEGRATION TEST:")
    print("-" * 50)
    
    # Test mit Canadian Malartic Mine
    test_prompt = SpecializedPrompts.get_comprehensive_extraction_prompt(
        mine_name="Canadian Malartic Mine",
        name_variants=["Malartic", "Canadian Malartic"],
        country="Kanada",
        commodity="Gold"
    )
    
    integration_checks = [
        ("Anti-Template Instructions integriert", "🚫 UNIVERSAL ANTI-TEMPLATE" in test_prompt),
        ("Field-Specific Instructions integriert", "📋 FIELD-SPECIFIC QUALITY" in test_prompt),
        ("Quality Gate Instructions integriert", "🛡️ UNIVERSAL QUALITY GATE" in test_prompt),
        ("CSV_COLUMNS Coverage", "NAME:" in test_prompt and "EIGENTÜMER:" in test_prompt),
        ("Template-Pattern Verbote", "Gold/ Kupfer/ Kohle/ usw.)" in test_prompt)
    ]
    
    for check_name, result in integration_checks:
        status = "✅" if result else "❌"
        print(f"{status} {check_name}: {'Integriert' if result else 'FEHLT'}")
    
    print("")
    
    # Test 5: Specialized Prompts Enhancement
    print("5️⃣ SPECIALIZED PROMPTS ENHANCEMENT:")
    print("-" * 50)
    
    # Test Restaurationskosten Prompt
    resto_prompt = SpecializedPrompts.get_restoration_costs_prompt("Test Mine", "Kanada")
    resto_enhanced = "🚫 UNIVERSAL ANTI-TEMPLATE" in resto_prompt
    
    # Test Koordinaten Prompt  
    coord_prompt = SpecializedPrompts.get_coordinates_prompt("Test Mine", "Quebec")
    coord_enhanced = "🚫 UNIVERSAL ANTI-TEMPLATE" in coord_prompt
    
    # Test Eigentümer Prompt
    owner_prompt = SpecializedPrompts.get_ownership_prompt("Test Mine", "Kanada")
    owner_enhanced = "🚫 UNIVERSAL ANTI-TEMPLATE" in owner_prompt
    
    specialized_checks = [
        ("Restaurationskosten Enhanced", resto_enhanced),
        ("Koordinaten Enhanced", coord_enhanced),
        ("Eigentümer Enhanced", owner_enhanced)
    ]
    
    for check_name, result in specialized_checks:
        status = "✅" if result else "❌"
        print(f"{status} {check_name}: {'Enhanced' if result else 'NICHT ENHANCED'}")
    
    print("")
    
    # ZUSAMMENFASSUNG
    print("📊 COMPREHENSIVE TEST SUMMARY:")
    print("=" * 60)
    
    total_checks = len(template_checks) + len(quality_checks) + len(integration_checks) + len(specialized_checks)
    passed_checks = (sum(1 for _, r in template_checks if r) + 
                    sum(1 for _, r in quality_checks if r) + 
                    sum(1 for _, r in integration_checks if r) + 
                    sum(1 for _, r in specialized_checks if r))
    
    test_score = (passed_checks / total_checks) * 100
    field_coverage_score = coverage_percent
    
    print(f"🎯 Test Score: {passed_checks}/{total_checks} = {test_score:.1f}%")
    print(f"📋 Field Coverage: {covered_fields}/{len(CSV_COLUMNS)} = {field_coverage_score:.1f}%")
    print(f"🎭 Overall Quality: {(test_score + field_coverage_score) / 2:.1f}%")
    
    if test_score >= 90 and field_coverage_score >= 90:
        print("\n🏆 EXCELLENT: Anti-Template System vollständig implementiert!")
        print("🚀 Ready für Produktionseinsatz mit maximaler Datenqualität")
    elif test_score >= 80:
        print("\n✅ GOOD: System funktional, kleinere Verbesserungen möglich")
    else:
        print("\n⚠️  NEEDS IMPROVEMENT: System erfordert weitere Optimierung")
    
    print("")
    print("🔗 NEXT STEPS:")
    print("1. Live-Test mit problematischen Minen")
    print("2. Before/After Template-Rate Vergleich")
    print("3. Integration mit bestehenden Quality Gates validieren")

if __name__ == "__main__":
    test_enhanced_prompt_system()