#!/usr/bin/env python3
"""
COMPLETE SYSTEM TEST FOR MINESEARCH 2.0
Tests Phase 1.1, 1.2, and 2.1 implementations end-to-end
"""

import requests
import json
import time
from datetime import datetime

def test_backend_api():
    """Test Phase 1.1 & 1.2 backend implementations"""
    print("🧪 TESTING BACKEND API (PHASE 1.1 & 1.2)")
    print("=" * 50)
    
    # Test 1: Source Index API (Phase 1.2)
    print("\n1. Testing Source Index API...")
    try:
        response = requests.get("http://localhost:8000/api/sources/index", timeout=10)
        if response.status_code == 200:
            data = response.json()
            source_count = len(data.get('data', {}).get('source_index', {}))
            print(f"   ✅ Source Index: {source_count} sources indexed")
        else:
            print(f"   ❌ Source Index failed: HTTP {response.status_code}")
    except Exception as e:
        print(f"   ❌ Source Index error: {e}")
    
    # Test 2: Consolidated Results API (Phase 1.1 & 1.2)
    print("\n2. Testing Consolidated Results API...")
    try:
        params = {
            'days_back': 365,
            'exclude_exa': 'false',
            'sort_by': 'mine_name'
        }
        
        response = requests.get("http://localhost:8000/api/consolidated/results", 
                              params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                result_data = data.get('data', {})
                consolidated_results = result_data.get('consolidated_results', [])
                global_source_index = result_data.get('global_source_index', {})
                
                print(f"   ✅ API Success: {len(consolidated_results)} mines processed")
                print(f"   ✅ Phase 1.2 Global Sources: {len(global_source_index)} indexed")
                
                if len(consolidated_results) > 0:
                    first_mine = consolidated_results[0]
                    structured_fields = first_mine.get('structured_fields', {})
                    metadata = first_mine.get('metadata', {})
                    
                    print(f"   ✅ Phase 1.1 Structured Fields: {len(structured_fields)} fields")
                    print(f"   ✅ Sample Mine: {metadata.get('mine_name', 'N/A')}")
                    
                    # Show sample structured field
                    if structured_fields:
                        field_name = list(structured_fields.keys())[0]
                        field_data = structured_fields[field_name]
                        confidence = field_data.get('confidence_score', 0)
                        source_count = field_data.get('source_count', 0)
                        print(f"   ✅ Sample Field: {field_name} (Confidence: {confidence}%, Sources: {source_count})")
                    
                    return True
                else:
                    print("   ❌ No consolidated results found")
                    return False
            else:
                print(f"   ❌ API returned error: {data}")
                return False
        else:
            print(f"   ❌ API failed: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Consolidated API error: {e}")
        return False

def test_frontend_integration():
    """Test that frontend files are correctly implemented"""
    print("\n\n🎨 TESTING FRONTEND INTEGRATION (PHASE 2.1)")
    print("=" * 50)
    
    try:
        # Test 1: Check if frontend files exist
        import os
        frontend_files = [
            '/app/frontend/display.js',
            '/app/frontend/style.css',
            '/app/frontend/index.html'
        ]
        
        for file_path in frontend_files:
            if os.path.exists(file_path):
                print(f"   ✅ Frontend file exists: {os.path.basename(file_path)}")
            else:
                print(f"   ❌ Missing frontend file: {os.path.basename(file_path)}")
                return False
        
        # Test 2: Check if displayConsolidatedResults function exists
        with open('/app/frontend/display.js', 'r') as f:
            content = f.read()
            if 'displayConsolidatedResults' in content:
                print("   ✅ displayConsolidatedResults function found")
            else:
                print("   ❌ displayConsolidatedResults function missing")
                return False
                
            if 'generateFieldBasedCard' in content:
                print("   ✅ generateFieldBasedCard function found")
            else:
                print("   ❌ generateFieldBasedCard function missing")
                return False
        
        # Test 3: Check if frontend calls correct API endpoint
        if '/api/consolidated/results' in content:
            print("   ✅ Frontend calls correct consolidated API endpoint")
            return True
        else:
            print("   ❌ Frontend not calling consolidated API endpoint")
            return False
            
    except Exception as e:
        print(f"   ❌ Frontend test error: {e}")
        return False

def main():
    print("🚀 MINESEARCH 2.0 COMPLETE SYSTEM TEST")
    print("Testing Phase 1.1, 1.2, and 2.1 implementations")
    print("=" * 60)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test backend
    backend_success = test_backend_api()
    
    # Test frontend
    frontend_success = test_frontend_integration()
    
    # Final assessment
    print("\n\n🏁 FINAL ASSESSMENT")
    print("=" * 50)
    
    if backend_success and frontend_success:
        print("🎉 ✅ ALL TESTS PASSED!")
        print("✅ Phase 1.1: Structured Fields API - WORKING")
        print("✅ Phase 1.2: Global Source Index - WORKING") 
        print("✅ Phase 2.1: Frontend Integration - WORKING")
        print("\n🌐 System is ready for browser testing!")
        print("   Navigate to: http://localhost:8000")
        print("   Click on: 'Konsolidierte Ergebnisse' tab")
        print("   Expected: Field-based cards with structured data")
        return True
    else:
        print("❌ SOME TESTS FAILED!")
        if not backend_success:
            print("❌ Backend API issues detected")
        if not frontend_success:
            print("❌ Frontend integration issues detected")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)