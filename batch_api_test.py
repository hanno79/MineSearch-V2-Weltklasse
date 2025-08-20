#!/usr/bin/env python3
"""
Author: rahn
Datum: 19.08.2025
Version: 1.0
Beschreibung: Direct API test for MineSearch Batch functionality to validate data quality
"""

import requests
import json
import sys

def test_batch_api():
    """Test the batch API directly and validate response for 'k.A.' values"""
    
    base_url = "http://localhost:8000"
    
    try:
        print("📍 Step 1: Test batch API endpoints")
        
        # First check if models endpoint is working
        models_response = requests.get(f"{base_url}/api/models")
        if models_response.status_code == 200:
            models = models_response.json()
            print(f"✅ Models API working: {len(models)} models available")
        else:
            print(f"❌ Models API failed: {models_response.status_code}")
            return False
        
        print("📍 Step 2: Test batch search with Quebec mines")
        
        # Prepare batch data
        batch_data = {
            "mines": [
                {"mine_name": "Éléonore"},
                {"mine_name": "Lac Expanse"},
                {"mine_name": "Aubelle"}
            ],
            "models": ["gemini", "brightdata"],  # Top performers
            "search_type": "batch"
        }
        
        # Try correct batch endpoints based on code analysis
        batch_endpoints = [
            "/api/upload-csv",
            "/api/batch-search",
            "/api/process-batch"
        ]
        
        batch_success = False
        for endpoint in batch_endpoints:
            try:
                print(f"Trying endpoint: {endpoint}")
                response = requests.post(f"{base_url}{endpoint}", json=batch_data, timeout=30)
                if response.status_code in [200, 201, 202]:
                    print(f"✅ Batch API success at {endpoint}: {response.status_code}")
                    result = response.json()
                    
                    # Analyze response
                    print(f"Response structure: {list(result.keys())}")
                    
                    # Check for 'k.A.' values in response
                    response_text = json.dumps(result)
                    ka_count = response_text.count('k.A.')
                    
                    print(f"📊 'k.A.' occurrences in API response: {ka_count}")
                    
                    # Look for actual data
                    data_indicators = ['Quebec', 'Canada', 'Gold', 'mining', 'resource', 'production']
                    data_found = 0
                    for indicator in data_indicators:
                        if indicator.lower() in response_text.lower():
                            data_found += 1
                            print(f"✅ Found data indicator: {indicator}")
                    
                    print(f"📊 Data indicators found: {data_found}/{len(data_indicators)}")
                    
                    if data_found > ka_count:
                        print("✅ SUCCESS: Real data outweighs placeholders!")
                    else:
                        print(f"⚠️  WARNING: Too many placeholders ({ka_count}) vs data ({data_found})")
                    
                    batch_success = True
                    break
                    
            except requests.exceptions.RequestException as e:
                print(f"❌ Endpoint {endpoint} failed: {e}")
                continue
        
        if not batch_success:
            print("❌ No working batch endpoint found")
            
        print("📍 Step 3: Check existing results for validation")
        # Check existing results endpoint for comparison
        results_response = requests.get(f"{base_url}/api/results?days_back=30&sort_by=mine_name")
        if results_response.status_code == 200:
            results = results_response.json()
            print(f"✅ Found {len(results)} existing results for comparison")
            
            if results:
                # Analyze first few results for 'k.A.' pattern
                sample_results = results[:5]
                sample_text = json.dumps(sample_results)
                existing_ka = sample_text.count('k.A.')
                print(f"📊 'k.A.' in existing results sample: {existing_ka}")
                
                # Check for real data fields
                real_data_fields = 0
                for result in sample_results:
                    for key, value in result.items():
                        if value and str(value) != 'k.A.' and str(value) != '' and str(value) != 'null':
                            real_data_fields += 1
                
                print(f"📊 Real data fields in sample: {real_data_fields}")
                
                if real_data_fields > existing_ka:
                    print("✅ Existing data quality looks good")
                else:
                    print("⚠️  Existing data has quality issues - many 'k.A.' values")
        
        print("📍 Step 4: Test individual search for comparison")
        # Test single search to compare data quality
        single_search_data = {
            "query": "Éléonore mine Quebec gold",
            "models": ["gemini"]
        }
        
        single_endpoints = ["/api/search", "/api/single/search"]
        for endpoint in single_endpoints:
            try:
                response = requests.post(f"{base_url}{endpoint}", json=single_search_data, timeout=30)
                if response.status_code == 200:
                    result = response.json()
                    single_text = json.dumps(result)
                    single_ka = single_text.count('k.A.')
                    print(f"✅ Single search test: {single_ka} 'k.A.' values")
                    break
            except:
                continue
        
        return True
        
    except Exception as e:
        print(f"❌ Error during API test: {e}")
        return False

if __name__ == "__main__":
    success = test_batch_api()
    sys.exit(0 if success else 1)