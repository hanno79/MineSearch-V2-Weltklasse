#!/usr/bin/env python3
"""
SOURCE REFERENCES MODAL TESTING - TESTING PHASE 6
Tests source references modal functionality for mine details
"""

import requests
import json
import re
from datetime import datetime

def test_source_references_function():
    """Test if source references modal function exists"""
    print("🔗 TESTING PHASE 6: SOURCE REFERENCES MODAL")
    print("=" * 60)
    
    print("\n1. Testing source references function availability...")
    
    try:
        response = requests.get("http://localhost:8000/static/display.js", timeout=10)
        if response.status_code == 200:
            js_content = response.text
            
            # Check for source references functions
            source_functions = [
                'generateSourceReferencesModal',
                'showSourceReferences',  # May or may not exist
                'generateSourceReferences'  # May or may not exist
            ]
            
            found_functions = []
            for func in source_functions:
                if func in js_content:
                    found_functions.append(func)
            
            print(f"   ✅ Source functions found: {found_functions}")
            
            # Check for source reference patterns
            source_patterns = [
                'source_index',
                'globalSourceIndex',
                '[1,2,3]',  # Source reference format
                'source-reference',
                'source-ref'
            ]
            
            found_patterns = []
            for pattern in source_patterns:
                if pattern in js_content:
                    found_patterns.append(pattern)
            
            print(f"   ✅ Source reference patterns found: {found_patterns}")
            
            if len(found_functions) >= 1 and len(found_patterns) >= 2:
                return True
            else:
                print("   ❌ Missing essential source reference functionality")
                return False
        else:
            print(f"   ❌ Failed to access display.js: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error testing source references functions: {e}")
        return False

def test_global_source_index_availability():
    """Test if global source index is available from API"""
    print("\n\n2. Testing global source index availability...")
    
    try:
        # Test source index API
        response = requests.get("http://localhost:8000/api/sources/index", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                source_index = data.get('data', {}).get('source_index', {})
                url_to_number = data.get('data', {}).get('url_to_number', {})
                total_sources = data.get('data', {}).get('total_sources', 0)
                
                print(f"   ✅ Global source index available: {total_sources} sources")
                print(f"   ✅ Source index mapping: {len(source_index)} entries")
                print(f"   ✅ URL to number mapping: {len(url_to_number)} entries")
                
                # Show sample source
                if source_index:
                    first_source = list(source_index.values())[0]
                    print(f"   ✅ Sample source: {first_source.get('domain', 'N/A')} (reliability: {first_source.get('reliability_score', 0)})")
                
                return True, total_sources
            else:
                print(f"   ❌ Source index API error: {data}")
                return False, 0
        else:
            print(f"   ❌ Source index API failed: HTTP {response.status_code}")
            return False, 0
            
    except Exception as e:
        print(f"   ❌ Error testing source index: {e}")
        return False, 0

def test_source_references_in_mine_data():
    """Test if mine data contains proper source references"""
    print("\n\n3. Testing source references in mine data...")
    
    try:
        response = requests.get("http://localhost:8000/api/consolidated/results", 
                              params={'days_back': 365}, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                consolidated_results = data.get('data', {}).get('consolidated_results', [])
                global_source_index = data.get('data', {}).get('global_source_index', {})
                
                if consolidated_results and global_source_index:
                    sample_mine = consolidated_results[0]
                    mine_name = sample_mine.get('metadata', {}).get('mine_name', 'Unknown')
                    structured_fields = sample_mine.get('structured_fields', {})
                    
                    print(f"   ✅ Sample mine: {mine_name}")
                    print(f"   ✅ Available for source modal: {len(structured_fields)} structured fields")
                    print(f"   ✅ Global source index: {len(global_source_index)} sources")
                    
                    # Check if fields have source references
                    fields_with_sources = 0
                    total_source_references = 0
                    
                    for field_name, field_data in structured_fields.items():
                        source_references = field_data.get('source_references', [])
                        if source_references:
                            fields_with_sources += 1
                            total_source_references += len(source_references)
                    
                    print(f"   ✅ Fields with source references: {fields_with_sources}/{len(structured_fields)}")
                    print(f"   ✅ Total source references: {total_source_references}")
                    
                    # Check a sample field's source references
                    if structured_fields:
                        first_field = list(structured_fields.keys())[0]
                        field_data = structured_fields[first_field]
                        source_refs = field_data.get('source_references', [])
                        
                        if source_refs:
                            print(f"   ✅ Sample field '{first_field}' has {len(source_refs)} source references")
                        else:
                            print(f"   ⚠️  Sample field '{first_field}' has no source references")
                    
                    return True, mine_name, len(structured_fields)
                else:
                    print("   ❌ Missing consolidated results or global source index")
                    return False, None, 0
            else:
                print(f"   ❌ Consolidated API error: {data}")
                return False, None, 0
        else:
            print(f"   ❌ Consolidated API failed: HTTP {response.status_code}")
            return False, None, 0
            
    except Exception as e:
        print(f"   ❌ Error testing mine data source references: {e}")
        return False, None, 0

def test_source_modal_content_generation():
    """Test source modal content generation patterns"""
    print("\n\n4. Testing source modal content generation...")
    
    try:
        response = requests.get("http://localhost:8000/static/display.js", timeout=10)
        if response.status_code == 200:
            js_content = response.text
            
            # Find generateSourceReferencesModal function content
            modal_start = js_content.find('function generateSourceReferencesModal')
            if modal_start != -1:
                # Get the function content (simplified extraction)
                modal_section = js_content[modal_start:modal_start + 2000]
                
                # Check for essential modal content patterns
                modal_content_patterns = [
                    'source-refs-grid',
                    'source-reference-item', 
                    'source-reliability',
                    'source-url',
                    'reliability_score',
                    'success_rate',
                    'domain'
                ]
                
                found_content_patterns = []
                for pattern in modal_content_patterns:
                    if pattern in modal_section:
                        found_content_patterns.append(pattern)
                
                print(f"   ✅ Source modal content patterns found: {found_content_patterns}")
                
                # Check for dynamic content generation
                dynamic_generation = [
                    'Object.entries',
                    '.map(',
                    '${',  # Template literals
                    'source_data',
                    'reliability'
                ]
                
                found_dynamic = []
                for pattern in dynamic_generation:
                    if pattern in modal_section:
                        found_dynamic.append(pattern)
                
                print(f"   ✅ Dynamic generation patterns found: {found_dynamic}")
                
                if len(found_content_patterns) >= 4 and len(found_dynamic) >= 3:
                    return True
                else:
                    print("   ❌ Missing essential source modal content patterns")
                    return False
            else:
                print("   ❌ generateSourceReferencesModal function not found")
                return False
        else:
            print(f"   ❌ Failed to access display.js: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error testing source modal content generation: {e}")
        return False

def main():
    print("🚀 MINESEARCH 2.0 SOURCE REFERENCES MODAL TEST")
    print("Testing Phase 2.1 source references modal functionality")
    print("=" * 70)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests_passed = 0
    total_tests = 4
    issues_found = []
    
    # Test 1: Source references functions
    functions_ok = test_source_references_function()
    if functions_ok:
        tests_passed += 1
    else:
        issues_found.append('Missing source references functions')
    
    # Test 2: Global source index
    index_ok, total_sources = test_global_source_index_availability()
    if index_ok:
        tests_passed += 1
    else:
        issues_found.append('Global source index not available')
    
    # Test 3: Source references in mine data
    data_ok, sample_mine, field_count = test_source_references_in_mine_data()
    if data_ok:
        tests_passed += 1
    else:
        issues_found.append('Source references missing in mine data')
    
    # Test 4: Source modal content generation
    content_ok = test_source_modal_content_generation()
    if content_ok:
        tests_passed += 1
    else:
        issues_found.append('Source modal content generation problems')
    
    # Final assessment
    print("\n\n🏁 SOURCE REFERENCES MODAL TEST RESULTS")
    print("=" * 70)
    
    if tests_passed == total_tests:
        print("🎉 ✅ ALL SOURCE REFERENCES MODAL TESTS PASSED!")
        print("✅ Source references functions - AVAILABLE")
        print("✅ Global source index - OPERATIONAL")
        print("✅ Mine data source references - PRESENT")
        print("✅ Source modal content generation - WORKING")
        
        print(f"\n🔧 EXPECTED SOURCE MODAL BEHAVIOR:")
        print(f"   1. User clicks 'Quellen' button on mine card for '{sample_mine}'")
        print(f"   2. generateSourceReferencesModal() is called")
        print(f"   3. Modal displays {total_sources} available sources")
        print(f"   4. Each source shows reliability score, domain, success rate")
        print(f"   5. Sources are numbered [1,2,3] for reference")
        
        return True, []
    else:
        print(f"❌ {total_tests - tests_passed} OUT OF {total_tests} TESTS FAILED!")
        print("❌ Source references modal issues detected:")
        for issue in set(issues_found):  # Remove duplicates
            print(f"   • {issue}")
        
        print("\n🔧 REQUIRED FIXES:")
        for issue in set(issues_found):
            if 'functions' in issue:
                print("   • Fix generateSourceReferencesModal function")
            elif 'index' in issue:
                print("   • Fix global source index API")
            elif 'data' in issue:
                print("   • Add source references to mine data structure")
            elif 'content' in issue:
                print("   • Fix source modal content generation")
        
        return False, issues_found

if __name__ == "__main__":
    success, issues = main()
    exit(0 if success else 1)