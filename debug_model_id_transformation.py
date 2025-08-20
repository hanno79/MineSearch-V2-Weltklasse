#!/usr/bin/env python3
"""
DEBUG: Track model_id transformation from DB to API response
Author: rahn
Date: 20.08.2025
"""

import requests
import json

def debug_model_id_transformation():
    """Debug where model_id gets converted to 'unknown'"""
    print("🔍 DEBUG: Model ID Transformation Analysis")
    print("=" * 60)
    
    try:
        # Test consolidated results API
        url = "http://localhost:8000/api/consolidated/results?sort_by=mine_name&order=asc&exclude_exa=true&days_back=30"
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ API ERROR: Status {response.status_code}")
            return
            
        data = response.json()
        
        if not data.get('success'):
            print(f"❌ API ERROR: {data}")
            return
            
        results = data.get('data', {}).get('consolidated_results', [])
        
        if not results:
            print("❌ No consolidated results found")
            return
            
        # Debug first result in detail
        first_result = results[0]
        mine_name = first_result.get('mine_name', 'Unknown')
        model_results = first_result.get('model_results', [])
        
        print(f"📊 Mine: {mine_name}")
        print(f"🤖 Total model_results: {len(model_results)}")
        
        if not model_results:
            print("❌ No model_results found")
            return
            
        # Analyze first 5 model results
        print("\n🔍 DETAILED MODEL_RESULTS ANALYSIS:")
        print("-" * 50)
        
        for i, model_result in enumerate(model_results[:5]):
            print(f"\nModel Result #{i+1}:")
            print(f"  ID: {model_result.get('id', 'N/A')}")
            print(f"  model_id: '{model_result.get('model_id', 'MISSING')}'")
            print(f"  model_used: '{model_result.get('model_used', 'MISSING')}'")
            print(f"  search_timestamp: {model_result.get('search_timestamp', 'N/A')}")
            
            # Check structured_data keys
            structured_data = model_result.get('structured_data', {})
            if structured_data:
                print(f"  structured_data keys: {list(structured_data.keys())[:3]}...")
            else:
                print(f"  structured_data: EMPTY")
                
        # Count unique model_ids vs unknown
        model_ids = [r.get('model_id', 'MISSING') for r in model_results]
        unique_models = set(model_ids)
        unknown_count = model_ids.count('unknown')
        missing_count = model_ids.count('MISSING')
        
        print(f"\n📊 MODEL_ID STATISTICS:")
        print(f"  Total model_results: {len(model_results)}")
        print(f"  Unique model_ids: {len(unique_models)}")
        print(f"  'unknown' count: {unknown_count}")
        print(f"  'MISSING' count: {missing_count}")
        print(f"  Unique model_ids: {unique_models}")
        
        # Check if model_used is also corrupted
        model_used_values = [r.get('model_used', 'MISSING') for r in model_results]
        unique_model_used = set(model_used_values)
        
        print(f"\n📊 MODEL_USED COMPARISON:")
        print(f"  Unique model_used: {len(unique_model_used)}")
        print(f"  Model_used values: {list(unique_model_used)[:3]}...")
        
        if unknown_count > 0:
            print(f"\n⚠️ CRITICAL ISSUE: {unknown_count} models showing as 'unknown'")
        else:
            print(f"\n✅ No 'unknown' model_ids found")
            
    except Exception as e:
        print(f"❌ DEBUG ERROR: {str(e)}")

if __name__ == "__main__":
    debug_model_id_transformation()