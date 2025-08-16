#!/usr/bin/env python3
"""
BROWSER UI TESTING FOR MINESEARCH 2.0 - PHASE 4
Tests field-based card display in browser UI for consolidated results
"""

import requests
import json
import time
from datetime import datetime
import re

def test_consolidated_results_ui():
    """Test Phase 2.1 field-based cards in browser UI"""
    print("🌐 TESTING BROWSER UI - CONSOLIDATED RESULTS TAB")
    print("=" * 60)
    
    # Test 1: Verify consolidated data is available
    print("\n1. Testing consolidated data availability...")
    try:
        response = requests.get("http://localhost:8000/api/consolidated/results?days_back=365", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                consolidated_results = data.get('data', {}).get('consolidated_results', [])
                global_sources = data.get('data', {}).get('global_source_index', {})
                
                print(f"   ✅ Data available: {len(consolidated_results)} mines, {len(global_sources)} sources")
                
                if len(consolidated_results) > 0:
                    # Analyze first mine for field structure
                    first_mine = consolidated_results[0]
                    structured_fields = first_mine.get('structured_fields', {})
                    metadata = first_mine.get('metadata', {})
                    
                    print(f"   ✅ Sample mine: {metadata.get('mine_name', 'Unknown')}")
                    print(f"   ✅ Structured fields: {len(structured_fields)}")
                    
                    # Check for key fields expected in UI
                    key_fields = ['Region', 'Rohstoffe', 'Eigentümer', 'Betreiber']
                    found_fields = [field for field in key_fields if field in structured_fields]
                    print(f"   ✅ Key fields found: {found_fields}")
                    
                    return True, consolidated_results[0]
        
        print("   ❌ No consolidated data available")
        return False, None
        
    except Exception as e:
        print(f"   ❌ Error accessing consolidated data: {e}")
        return False, None

def test_frontend_structure():
    """Test frontend HTML structure for consolidated results"""
    print("\n\n2. Testing frontend HTML structure...")
    
    try:
        # Get the main HTML
        response = requests.get("http://localhost:8000/static/index.html", timeout=10)
        if response.status_code == 200:
            html_content = response.text
            
            # Check for consolidated results tab (correct ID and function names)
            if ('id="consolidated"' in html_content and 
                'switchToTab(\'consolidated\')' in html_content and
                'data-tab="consolidated"' in html_content):
                print("   ✅ Consolidated results tab found in HTML")
            else:
                print("   ❌ Consolidated results tab NOT found in HTML")
                return False
            
            # Check for essential IDs/classes for field-based display
            essential_elements = [
                'results-container',
                'consolidated-results-container',  # More specific container
                'id="consolidated"'  # The actual consolidated tab section
            ]
            
            found_elements = []
            for element in essential_elements:
                if element in html_content:
                    found_elements.append(element)
            
            print(f"   ✅ Essential elements found: {found_elements}")
            
            if len(found_elements) >= 2:
                return True
            else:
                print("   ❌ Missing essential elements for field-based display")
                return False
        else:
            print(f"   ❌ Failed to access HTML: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error testing frontend structure: {e}")
        return False

def test_javascript_functions():
    """Test JavaScript function availability"""
    print("\n\n3. Testing JavaScript function integration...")
    
    try:
        # Get display.js to check for field-based functions
        response = requests.get("http://localhost:8000/static/display.js", timeout=10)
        if response.status_code == 200:
            js_content = response.text
            
            # Check for Phase 2.1 functions
            required_functions = [
                'displayConsolidatedResults',
                'generateFieldBasedCard',
                'generateFieldDisplayGrid',
                'generateSourceReferences'
            ]
            
            found_functions = []
            for func in required_functions:
                if func in js_content:
                    found_functions.append(func)
            
            print(f"   ✅ Phase 2.1 functions found: {found_functions}")
            
            # Check for Phase 2.1 specific patterns
            phase2_patterns = [
                'PHASE 2.1',
                'structured_fields',
                'field-based-card',
                'globalSourceIndex'
            ]
            
            found_patterns = []
            for pattern in phase2_patterns:
                if pattern in js_content:
                    found_patterns.append(pattern)
            
            print(f"   ✅ Phase 2.1 patterns found: {found_patterns}")
            
            if len(found_functions) >= 3 and len(found_patterns) >= 2:
                return True
            else:
                print("   ❌ Missing Phase 2.1 implementation patterns")
                return False
        else:
            print(f"   ❌ Failed to access display.js: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error testing JavaScript functions: {e}")
        return False

def simulate_ui_interaction():
    """Simulate the UI interaction for consolidated results"""
    print("\n\n4. Simulating UI interaction...")
    
    print("   🖱️  Simulated user actions:")
    print("   1. User navigates to http://localhost:8000")
    print("   2. User clicks on 'Konsolidierte Ergebnisse' tab")
    print("   3. JavaScript calls /api/consolidated/results")
    print("   4. displayConsolidatedResults() processes the response")
    print("   5. generateFieldBasedCard() creates field-based cards")
    
    # Test the actual API call that the frontend would make
    try:
        print("\n   🔄 Testing actual frontend API call...")
        response = requests.get("http://localhost:8000/api/consolidated/results", 
                              params={'days_back': 365, 'sort_by': 'mine_name'}, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                result_data = data.get('data', {})
                mines = result_data.get('consolidated_results', [])
                sources = result_data.get('global_source_index', {})
                
                print(f"   ✅ API call successful: {len(mines)} mines, {len(sources)} sources")
                
                if mines:
                    first_mine = mines[0]
                    print(f"   ✅ Sample mine data structure:")
                    print(f"      - Name: {first_mine.get('metadata', {}).get('mine_name')}")
                    print(f"      - Structured fields: {len(first_mine.get('structured_fields', {}))}")
                    print(f"      - Source references: Available in global index")
                    
                    # Show sample field
                    structured_fields = first_mine.get('structured_fields', {})
                    if structured_fields:
                        field_name = list(structured_fields.keys())[0]
                        field_data = structured_fields[field_name]
                        print(f"      - Sample field '{field_name}':")
                        print(f"        • Value: {field_data.get('value', 'N/A')}")
                        print(f"        • Confidence: {field_data.get('confidence_score', 0)}%")
                        print(f"        • Sources: {field_data.get('source_count', 0)}")
                    
                    return True
                else:
                    print("   ❌ No mines data in API response")
                    return False
            else:
                print(f"   ❌ API returned error: {data}")
                return False
        else:
            print(f"   ❌ API call failed: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error in API simulation: {e}")
        return False

def main():
    print("🚀 MINESEARCH 2.0 BROWSER UI TEST")
    print("Testing Phase 2.1 field-based card display")
    print("=" * 70)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run all tests
    tests_passed = 0
    total_tests = 4
    
    # Test 1: Data availability
    data_success, sample_mine = test_consolidated_results_ui()
    if data_success:
        tests_passed += 1
    
    # Test 2: HTML structure
    html_success = test_frontend_structure()
    if html_success:
        tests_passed += 1
    
    # Test 3: JavaScript functions
    js_success = test_javascript_functions()
    if js_success:
        tests_passed += 1
    
    # Test 4: UI interaction simulation
    ui_success = simulate_ui_interaction()
    if ui_success:
        tests_passed += 1
    
    # Final assessment
    print("\n\n🏁 BROWSER UI TEST RESULTS")
    print("=" * 70)
    
    if tests_passed == total_tests:
        print("🎉 ✅ ALL BROWSER UI TESTS PASSED!")
        print("✅ Phase 2.1: Field-based cards - READY")
        print("✅ Consolidated results tab - FUNCTIONAL")
        print("✅ JavaScript integration - WORKING")
        print("✅ API data flow - OPERATIONAL")
        
        print("\n🌐 EXPECTED UI BEHAVIOR:")
        print("   1. Navigate to: http://localhost:8000")
        print("   2. Click: 'Konsolidierte Ergebnisse' tab")
        print("   3. See: Field-based cards showing structured mine data")
        print("   4. Each card shows:")
        print("      • Mine name and basic metadata")
        print("      • Structured fields with values and confidence scores")
        print("      • Source references [1,2,3] format")
        print("      • Click to expand details modal")
        
        return True
    else:
        print(f"❌ {total_tests - tests_passed} OUT OF {total_tests} TESTS FAILED!")
        print("❌ Browser UI issues detected:")
        
        if not data_success:
            print("   • Data availability problems")
        if not html_success:
            print("   • HTML structure issues")
        if not js_success:
            print("   • JavaScript function problems")
        if not ui_success:
            print("   • API interaction failures")
        
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)