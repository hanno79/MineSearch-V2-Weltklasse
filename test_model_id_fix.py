#!/usr/bin/env python3
"""
Test model_id fix for unknown values
"""

import requests
import json
from collections import Counter

def test_model_id_fix():
    """Test if model_id fix resolves unknown model issue"""
    try:
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
        
        # Check Aubelle mine specifically
        aubelle = next((r for r in results if r.get('mine_name') == 'Aubelle'), None)
        if aubelle:
            model_results = aubelle.get('model_results', [])
            model_ids = [r.get('model_id', 'unknown') for r in model_results]
            
            print(f"Aubelle total model_results: {len(model_results)}")
            print(f"Unique model_ids: {len(set(model_ids))}")
            
            # Count occurrences of each model
            model_counts = Counter(model_ids)
            
            # Show unique models count
            unknown_count = model_counts.get('unknown', 0)
            non_unknown_count = len([model for model in model_counts.keys() if model != 'unknown'])
            
            print(f"Unknown models: {unknown_count}")
            print(f"Non-unknown models: {non_unknown_count}")
            
            # Show top 5 models
            print("\nTop 5 model occurrences:")
            for model_id, count in model_counts.most_common(5):
                print(f"  {model_id}: {count} times")
            
            # Check actual model count field
            model_count_field = aubelle.get('model_count', 0)
            print(f"\nmodel_count field: {model_count_field}")
            print(f"Unique models actual: {len(set(model_ids))}")
            
            if unknown_count == 0:
                print("✅ PHASE 4 FIX SUCCESS: No more 'unknown' models!")
            else:
                print(f"⚠️ PHASE 4 FIX PARTIAL: Still {unknown_count} unknown models")
                
            if len(set(model_ids)) <= 55:
                print("✅ Model count fix working - showing reasonable number of unique models")
            else:
                print("⚠️ Model count still too high")
                
            # Now test the unique model count fix
            if model_count_field == len(set(model_ids)):
                print("✅ PHASE 3 FIX SUCCESS: model_count matches unique models!")
            else:
                print(f"⚠️ PHASE 3 FIX ISSUE: model_count ({model_count_field}) != unique models ({len(set(model_ids))})")
            
    except Exception as e:
        print(f"❌ PROCESSING ERROR: {str(e)}")

if __name__ == "__main__":
    test_model_id_fix()