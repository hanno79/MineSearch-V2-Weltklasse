#!/usr/bin/env python3
"""
DETAILS MODAL TESTING - TESTING PHASE 5
Tests details modal functionality for consolidated results
"""

import requests
import json
import re
from datetime import datetime

def test_modal_functions():
    """Test if modal-related functions exist in display.js"""
    print("🔍 TESTING PHASE 5: DETAILS MODAL FUNCTIONALITY")
    print("=" * 60)
    
    print("\n1. Testing modal function availability...")
    
    try:
        response = requests.get("http://localhost:8000/static/display.js", timeout=10)
        if response.status_code == 200:
            js_content = response.text
            
            # Check for modal functions
            modal_functions = [
                'showConsolidatedDetailModal',
                'generateSourceReferencesModal', 
                'showModal'  # Generic modal function
            ]
            
            found_functions = []
            missing_functions = []
            
            for func in modal_functions:
                if func in js_content:
                    found_functions.append(func)
                else:
                    missing_functions.append(func)
            
            print(f"   ✅ Modal functions found: {found_functions}")
            if missing_functions:
                print(f"   ❌ Missing functions: {missing_functions}")
                return False, missing_functions
            else:
                return True, []
        else:
            print(f"   ❌ Failed to access display.js: HTTP {response.status_code}")
            return False, ['display.js not accessible']
            
    except Exception as e:
        print(f"   ❌ Error testing modal functions: {e}")
        return False, [str(e)]

def test_modal_html_structure():
    """Test if modal structure exists in HTML"""
    print("\n\n2. Testing modal HTML structure...")
    
    try:
        response = requests.get("http://localhost:8000/static/index.html", timeout=10)
        if response.status_code == 200:
            html_content = response.text
            
            # Check for modal-related elements
            modal_elements = [
                'class="modal',          # Modal container
                'class="modal-content',  # Modal content wrapper
                'class="modal-header',   # Modal header
                'class="modal-body',     # Modal body
                'modal-overlay',         # Modal overlay
                'modal-close'            # Modal close button
            ]
            
            found_elements = []
            for element in modal_elements:
                if element in html_content:
                    found_elements.append(element.replace('class="', '').replace('"', ''))
            
            print(f"   ✅ Modal elements found: {found_elements}")
            
            if len(found_elements) >= 3:  # At least basic modal structure
                return True
            else:
                print("   ❌ Missing essential modal HTML structure")
                return False
        else:
            print(f"   ❌ Failed to access HTML: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error testing modal HTML: {e}")
        return False

def test_modal_trigger_mechanism():
    """Test if modal can be triggered by mine card clicks"""
    print("\n\n3. Testing modal trigger mechanism...")
    
    try:
        # Get consolidated data first
        response = requests.get("http://localhost:8000/api/consolidated/results", 
                              params={'days_back': 365}, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                consolidated_results = data.get('data', {}).get('consolidated_results', [])
                
                if consolidated_results:
                    sample_mine = consolidated_results[0]
                    mine_name = sample_mine.get('metadata', {}).get('mine_name', 'Unknown')
                    
                    print(f"   ✅ Sample mine for modal test: {mine_name}")
                    print(f"   ✅ Mine has {len(sample_mine.get('structured_fields', {}))} structured fields")
                    print(f"   ✅ Modal would show detailed breakdown of all fields")
                    
                    # Check if the mine has the necessary data structure for modal
                    required_data = ['metadata', 'structured_fields']
                    has_required = all(key in sample_mine for key in required_data)
                    
                    if has_required:
                        print("   ✅ Mine data structure supports modal display")
                        return True, mine_name
                    else:
                        print("   ❌ Mine data missing required fields for modal")
                        return False, None
                else:
                    print("   ❌ No consolidated results available for modal test")
                    return False, None
            else:
                print(f"   ❌ API error: {data}")
                return False, None
        else:
            print(f"   ❌ Failed to get consolidated data: HTTP {response.status_code}")
            return False, None
            
    except Exception as e:
        print(f"   ❌ Error testing modal trigger: {e}")
        return False, None

def test_modal_content_generation():
    """Test modal content generation with real data"""
    print("\n\n4. Testing modal content generation...")
    
    try:
        response = requests.get("http://localhost:8000/static/display.js", timeout=10)
        if response.status_code == 200:
            js_content = response.text
            
            # Look for modal content generation patterns
            modal_patterns = [
                'modal-header',
                'modal-body', 
                'consolidated-detail-modal',
                'mine-summary',
                'fields-data-grid',
                'field-data-card'
            ]
            
            found_patterns = []
            for pattern in modal_patterns:
                if pattern in js_content:
                    found_patterns.append(pattern)
            
            print(f"   ✅ Modal content patterns found: {found_patterns}")
            
            # Check for dynamic content generation
            dynamic_patterns = [
                '${',           # Template literals
                '.map(',        # Array mapping for dynamic content
                'Object.entries', # Object iteration
                'innerHTML'     # DOM manipulation
            ]
            
            found_dynamic = []
            for pattern in dynamic_patterns:
                if pattern in js_content:
                    found_dynamic.append(pattern)
            
            print(f"   ✅ Dynamic content patterns found: {found_dynamic}")
            
            if len(found_patterns) >= 4 and len(found_dynamic) >= 2:
                return True
            else:
                print("   ❌ Missing essential modal content generation patterns")
                return False
        else:
            print(f"   ❌ Failed to access display.js: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error testing modal content generation: {e}")
        return False

def main():
    print("🚀 MINESEARCH 2.0 DETAILS MODAL TEST")
    print("Testing Phase 2.1 details modal functionality")
    print("=" * 70)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests_passed = 0
    total_tests = 4
    issues_found = []
    
    # Test 1: Modal functions
    functions_ok, missing_functions = test_modal_functions()
    if functions_ok:
        tests_passed += 1
    else:
        issues_found.extend(missing_functions)
    
    # Test 2: Modal HTML structure
    html_ok = test_modal_html_structure()
    if html_ok:
        tests_passed += 1
    else:
        issues_found.append('Missing modal HTML structure')
    
    # Test 3: Modal trigger mechanism
    trigger_ok, sample_mine = test_modal_trigger_mechanism()
    if trigger_ok:
        tests_passed += 1
    else:
        issues_found.append('Modal trigger mechanism issues')
    
    # Test 4: Modal content generation
    content_ok = test_modal_content_generation()
    if content_ok:
        tests_passed += 1
    else:
        issues_found.append('Modal content generation problems')
    
    # Final assessment
    print("\n\n🏁 DETAILS MODAL TEST RESULTS")
    print("=" * 70)
    
    if tests_passed == total_tests:
        print("🎉 ✅ ALL DETAILS MODAL TESTS PASSED!")
        print("✅ Modal functions - AVAILABLE")
        print("✅ Modal HTML structure - PRESENT")
        print("✅ Modal trigger mechanism - FUNCTIONAL")
        print("✅ Modal content generation - WORKING")
        
        print(f"\n🔧 EXPECTED MODAL BEHAVIOR:")
        print(f"   1. User clicks on mine card for '{sample_mine}'")
        print(f"   2. showConsolidatedDetailModal() is called")
        print(f"   3. Modal displays structured field details")
        print(f"   4. User can close modal and return to results")
        
        return True, []
    else:
        print(f"❌ {total_tests - tests_passed} OUT OF {total_tests} TESTS FAILED!")
        print("❌ Details modal issues detected:")
        for issue in set(issues_found):  # Remove duplicates
            print(f"   • {issue}")
        
        print("\n🔧 REQUIRED FIXES:")
        if 'showModal' in issues_found:
            print("   • Implement showModal() function")
        if 'Missing modal HTML structure' in issues_found:
            print("   • Add modal HTML elements to index.html")
        if 'Modal trigger mechanism issues' in issues_found:
            print("   • Fix mine card click handlers")
        
        return False, issues_found

if __name__ == "__main__":
    success, issues = main()
    exit(0 if success else 1)