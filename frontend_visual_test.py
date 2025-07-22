#!/usr/bin/env python3
"""
Visual test generator for MineSearch v2.1 frontend fixes
Creates expected output samples for manual verification
"""
import requests
import json

def generate_expected_output():
    """Generate expected output samples for manual verification"""
    base_url = "http://localhost:8000"
    
    print("🎯 Expected Frontend Output After Fixes")
    print("=" * 60)
    
    # Get field statistics data
    try:
        response = requests.get(f"{base_url}/api/benchmark/field-statistics")
        field_stats = response.json()
        
        print("\n📊 FIELD STATISTICS TABLE - Expected Output:")
        print("-" * 50)
        print("| Feld                    | Gefunden | Erfolgsrate | Konsistenz | Bestes Modell")
        print("| ----------------------- | -------- | ----------- | ---------- | -------------")
        
        if 'by_field' in field_stats:
            for field_name, models in list(field_stats['by_field'].items())[:5]:  # Show first 5
                total_found = sum(model.get('times_found', 0) for model in models)
                total_success_rate = sum(model.get('success_rate', 0) for model in models)
                avg_success_rate = (total_success_rate / len(models) * 100) if models else 0
                best_model = max(models, key=lambda m: m.get('success_rate', 0))['model_id'] if models else 'N/A'
                
                print(f"| {field_name:<23} | {total_found:>8} | {avg_success_rate:>9.1f}% | {avg_success_rate:>8.1f}% | {best_model}")
        
        print(f"| ... and {len(field_stats.get('by_field', {})) - 5} more fields")
        
    except Exception as e:
        print(f"❌ Could not generate field statistics preview: {e}")
    
    # Get field comparison data
    try:
        response = requests.get(f"{base_url}/api/benchmark/field-comparison")
        field_comparison = response.json()
        
        print("\n📈 FIELD COMPARISON - Expected Output:")
        print("-" * 50)
        
        if 'hardest_fields' in field_comparison:
            print("🔴 Schwierigste Felder:")
            for field in field_comparison['hardest_fields'][:5]:
                print(f"   • {field['field_name']} - {field['avg_success_rate']*100:.1f}% Erfolgsrate")
        
        if 'easiest_fields' in field_comparison:
            print("\n🟢 Einfachste Felder:")
            for field in field_comparison['easiest_fields'][:5]:
                print(f"   • {field['field_name']} - {field['avg_success_rate']*100:.1f}% Erfolgsrate")
                
    except Exception as e:
        print(f"❌ Could not generate field comparison preview: {e}")

def show_testing_instructions():
    """Show detailed testing instructions"""
    print("\n" + "=" * 60)
    print("🧪 MANUAL TESTING INSTRUCTIONS")
    print("=" * 60)
    
    print("\n1. Open Browser and Navigate:")
    print("   http://localhost:8000/static/index.html")
    
    print("\n2. Switch to Statistics Tab:")
    print("   • Click on the radio button: 📈 Suchstatistiken")
    print("   • Wait for the statistics form to become active")
    
    print("\n3. Test Field Statistics:")
    print("   • Click the purple button: 📊 Feld-Statistiken")
    print("   • Expected result: Table with 18 fields showing actual success rates")
    print("   • ✅ SUCCESS: You see percentages like 92.8%, 100.0%")
    print("   • ❌ FAILURE: You see zeros (0%) in the success rate column")
    
    print("\n4. Test Field Comparison:")
    print("   • Click the orange button: 📈 Feld-Vergleich")
    print("   • Expected result: Two lists showing hardest and easiest fields")
    print("   • ✅ SUCCESS: You see fields with success rate percentages")
    print("   • ❌ FAILURE: You see error messages or no data")
    
    print("\n5. Check Browser Console:")
    print("   • Press F12 to open Developer Tools")
    print("   • Go to Console tab")
    print("   • ✅ SUCCESS: No JavaScript errors (or only minor warnings)")
    print("   • ❌ FAILURE: Red error messages about undefined functions")
    
    print("\n6. Verify Sources Table Still Works:")
    print("   • Click on: 📚 Quellen-Datenbank")
    print("   • Click: Filter anwenden")
    print("   • ✅ SUCCESS: Sources table loads with domain data")
    print("   • ❌ FAILURE: Table doesn't load or shows errors")

def main():
    print("🎯 MineSearch v2.1 Frontend Testing Guide")
    
    # Generate expected output
    generate_expected_output()
    
    # Show testing instructions
    show_testing_instructions()
    
    print("\n" + "=" * 60)
    print("📋 SUMMARY OF FIXES APPLIED")
    print("=" * 60)
    print("✅ displayFieldStatistics() now handles 'by_field' API format")
    print("✅ displayFieldComparison() now handles direct array format")
    print("✅ Success rates properly calculated and displayed as percentages")
    print("✅ Error handling for missing/malformed data")
    print("✅ Maintains compatibility with existing Sources table")
    
    print("\n🚀 Status: READY FOR MANUAL TESTING")

if __name__ == "__main__":
    main()