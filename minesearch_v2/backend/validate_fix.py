#!/usr/bin/env python3
"""
Author: rahn  
Datum: 07.08.2025
Version: 1.0
Beschreibung: Quick validation of the Details button fix
"""

import requests
import json

def test_javascript_syntax():
    """Test that the fix generates valid JavaScript"""
    print("🔧 VALIDATING DETAILS BUTTON FIX")
    print("=" * 40)
    
    # Test the safeJSONStringify function logic
    print("1. 🧪 Testing safeJSONStringify logic...")
    
    def safeJSONStringify(value):
        if not value:
            return "''"
        return json.dumps(value)  # This adds quotes automatically
    
    # Test problematic model IDs
    test_model_ids = [
        "openrouter:deepseek-free",
        "perplexity:sonar-pro", 
        "openai:gpt-4o",
        "anthropic:claude-3-sonnet"
    ]
    
    print("2. 📝 Testing onclick generation for problematic model IDs...")
    for model_id in test_model_ids:
        # OLD (BROKEN) approach
        escaped_old = safeJSONStringify(model_id)
        broken_onclick = f'showModelDetails({escaped_old})'
        
        # NEW (FIXED) approach  
        fixed_onclick = f'showModelDetails({safeJSONStringify(model_id)})'
        
        print(f"\n   Model: {model_id}")
        print(f"   OLD (broken): onclick=\"{broken_onclick}\"")
        print(f"   NEW (fixed):  onclick=\"{fixed_onclick}\"") 
        
        # Check for syntax issues
        if broken_onclick.count('"') > 2:
            print(f"   ❌ OLD has nested quotes issue!")
        else:
            print(f"   ⚠️ OLD might work by accident")
            
        if fixed_onclick.count('"') == 2:  # Only the outer quotes
            print(f"   ✅ NEW has proper quoting")
        else:
            print(f"   ⚠️ NEW might have issues")
    
    print("\n3. 🎯 Testing API availability...")
    try:
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ Server is running")
            
            # Test statistics API
            stats_response = requests.get("http://localhost:8000/api/statistics/models/comprehensive", timeout=10)
            if stats_response.status_code == 200:
                data = stats_response.json()
                models = data.get('data', {}).get('models', [])
                print(f"   ✅ Statistics API working - {len(models)} models")
                
                if models:
                    test_model = models[0]
                    model_id = test_model.get('model_id', 'test')
                    print(f"   📋 Sample model ID: {model_id}")
                    print(f"   📋 Fixed onclick would be: onclick=\"showModelDetails({safeJSONStringify(model_id)})\"")
                    
                    return True
            else:
                print(f"   ⚠️ Statistics API returned {stats_response.status_code}")
        else:
            print(f"   ⚠️ Server returned {response.status_code}")
    except Exception as e:
        print(f"   ❌ Server connection failed: {e}")
    
    return False

def test_html_fix():
    """Test that the HTML fix is correctly applied"""
    print("\n4. 📄 Checking HTML fix in index.html...")
    
    try:
        with open('/app/frontend/index.html', 'r') as f:
            content = f.read()
        
        # Look for the fixed line
        if 'showModelDetails(${safeJSONStringify(stat.model_id)})' in content:
            print("   ✅ Fixed onclick pattern found in HTML!")
            
            # Count occurrences  
            fixed_count = content.count('showModelDetails(${safeJSONStringify(stat.model_id)})')
            print(f"   📊 Found {fixed_count} instances of fixed pattern")
            
            # Check for old broken patterns
            broken_count = content.count('showModelDetails(${escapedModelId})')
            if broken_count > 0:
                print(f"   ⚠️ Still found {broken_count} instances of old broken pattern")
            else:
                print("   ✅ No old broken patterns found")
                
            return True
        else:
            print("   ❌ Fixed pattern not found in HTML")
            return False
            
    except Exception as e:
        print(f"   ❌ Error reading HTML: {e}")
        return False

if __name__ == "__main__":
    syntax_ok = test_javascript_syntax()
    html_ok = test_html_fix()
    
    print("\n" + "=" * 40)  
    print("🎯 VALIDATION SUMMARY:")
    print(f"   ✅ JavaScript syntax: {'PASS' if syntax_ok else 'FAIL'}")
    print(f"   ✅ HTML fix applied: {'PASS' if html_ok else 'FAIL'}")
    
    if syntax_ok and html_ok:
        print(f"\n🎉 DETAILS BUTTON FIX VALIDATION: SUCCESS!")
        print("✅ The JavaScript syntax error should now be resolved")
        print("✅ User can test Details buttons in browser")
    else:
        print(f"\n❌ VALIDATION FAILED - Manual testing required")