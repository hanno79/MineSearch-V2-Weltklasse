#!/usr/bin/env python3
"""
Simple test script to verify the frontend JavaScript fixes for field statistics and field comparison
"""
import requests
import json
import time

def test_api_endpoints():
    """Test the backend API endpoints"""
    base_url = "http://localhost:8000"
    
    print("Testing API endpoints...")
    
    # Test field statistics API
    try:
        response = requests.get(f"{base_url}/api/benchmark/field-statistics")
        field_stats = response.json()
        print(f"✅ Field Statistics API: {len(field_stats.get('by_field', {}))} fields found")
        
        # Check if data structure matches expected format
        if 'by_field' in field_stats:
            sample_field = next(iter(field_stats['by_field'].values()))
            print(f"   Sample field data: {sample_field[0]['field_name']} with {len(sample_field)} models")
            print(f"   Success rate: {sample_field[0]['success_rate']:.1%}")
        else:
            print("❌ Field Statistics API: Missing 'by_field' key")
            
    except Exception as e:
        print(f"❌ Field Statistics API failed: {e}")
    
    # Test field comparison API
    try:
        response = requests.get(f"{base_url}/api/benchmark/field-comparison")
        field_comparison = response.json()
        print(f"✅ Field Comparison API: {len(field_comparison.get('hardest_fields', []))} hardest fields, {len(field_comparison.get('easiest_fields', []))} easiest fields")
        
        # Check if data structure matches expected format
        if 'hardest_fields' in field_comparison and 'easiest_fields' in field_comparison:
            if field_comparison['hardest_fields']:
                print(f"   Hardest field: {field_comparison['hardest_fields'][0]['field_name']} ({field_comparison['hardest_fields'][0]['avg_success_rate']:.1%})")
            if field_comparison['easiest_fields']:
                print(f"   Easiest field: {field_comparison['easiest_fields'][0]['field_name']} ({field_comparison['easiest_fields'][0]['avg_success_rate']:.1%})")
        else:
            print("❌ Field Comparison API: Missing required keys")
            
    except Exception as e:
        print(f"❌ Field Comparison API failed: {e}")

def test_frontend_status():
    """Test that frontend is accessible"""
    try:
        response = requests.get("http://localhost:8000/static/index.html")
        if response.status_code == 200:
            print("✅ Frontend is accessible at http://localhost:8000/static/index.html")
            
            # Check if JavaScript fixes are in place
            html_content = response.text
            
            # Check for displayFieldStatistics function
            if 'displayFieldStatistics' in html_content:
                print("✅ displayFieldStatistics function found in HTML")
            else:
                print("❌ displayFieldStatistics function not found")
                
            # Check for displayFieldComparison function
            if 'displayFieldComparison' in html_content:
                print("✅ displayFieldComparison function found in HTML")
            else:
                print("❌ displayFieldComparison function not found")
                
            # Check for proper data handling
            if 'data.by_field' in html_content:
                print("✅ Field statistics data handling found")
            else:
                print("❌ Field statistics data handling might be missing")
                
            if 'data.hardest_fields' in html_content and 'data.easiest_fields' in html_content:
                print("✅ Field comparison data handling found")
            else:
                print("❌ Field comparison data handling might be missing")
        else:
            print(f"❌ Frontend not accessible: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Frontend test failed: {e}")

def main():
    print("🧪 Testing MineSearch v2.1 Frontend Fixes")
    print("=" * 50)
    
    # Test API endpoints first
    test_api_endpoints()
    
    print("\n" + "-" * 30)
    
    # Test frontend accessibility
    test_frontend_status()
    
    print("\n" + "=" * 50)
    print("✅ API Testing completed!")
    print("\n📋 Manual testing steps:")
    print("1. Navigate to: http://localhost:8000/static/index.html")
    print("2. Click on 'Suchstatistiken' tab (📈)")
    print("3. Click 'Feld-Statistiken' button")
    print("4. Verify table shows actual data with field names and success rates")
    print("5. Click 'Feld-Vergleich' button")
    print("6. Verify it shows hardest and easiest fields with percentages")
    print("7. Check browser console (F12) for any JavaScript errors")
    print("\n🔍 Expected results:")
    print("- Field Statistics should show 18 fields with success rates (~92.8%)")
    print("- Field Comparison should show fields sorted by difficulty")
    print("- No JavaScript errors in browser console")

if __name__ == "__main__":
    main()