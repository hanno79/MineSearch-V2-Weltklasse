#!/usr/bin/env python3
"""
PHASE 4 VALIDATION: Test all implemented fixes
Author: rahn
Date: 20.08.2025
"""

import requests
import json

def test_consolidated_results_fixes():
    """Test all consolidated results fixes"""
    print("🚀 PHASE 4 VALIDATION: Testing all implemented fixes")
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
        print(f"✅ API SUCCESS: {len(results)} consolidated results found")
        
        if not results:
            print("❌ No consolidated results found")
            return
            
        # Test first result
        first_result = results[0]
        mine_name = first_result.get('mine_name', 'Unknown')
        model_count = first_result.get('model_count', 0)
        total_sources = first_result.get('total_sources', 0)
        
        print(f"📊 Example Mine: {mine_name}")
        print(f"🤖 Model Count: {model_count} (should be ≤55)")
        print(f"📈 Total Sources: {total_sources}")
        
        # PHASE 1 FIX: Template Pattern Check
        if 'best_values' in first_result:
            placeholder_count = 0
            total_fields = 0
            for field, value in first_result['best_values'].items():
                total_fields += 1
                if value in ['k.A.', 'Not specified', 'not specified', 'nichts gefunden']:
                    placeholder_count += 1
            
            print(f"🔍 Template Pattern Check: {placeholder_count}/{total_fields} placeholder values")
            if placeholder_count == 0:
                print("✅ PHASE 1 FIX SUCCESS: No template patterns found")
            else:
                print("⚠️ PHASE 1 FIX PARTIAL: Some template patterns remain")
        
        # PHASE 1 FIX: Eigentümer/Betreiber field mapping check
        if 'best_values' in first_result:
            eigentuemer = first_result['best_values'].get('Eigentümer', '')
            betreiber = first_result['best_values'].get('Betreiber', '')
            
            if eigentuemer == betreiber and eigentuemer and eigentuemer != 'nichts gefunden':
                print("⚠️ PHASE 1 FIX ISSUE: Eigentümer and Betreiber are identical")
                print(f"   Both show: {eigentuemer}")
            else:
                print("✅ PHASE 1 FIX SUCCESS: Eigentümer/Betreiber properly differentiated")
                print(f"   Eigentümer: {eigentuemer}")
                print(f"   Betreiber: {betreiber}")
        
        # PHASE 3 FIX: Model count validation
        if model_count > 55:
            print(f"⚠️ PHASE 3 FIX ISSUE: Model count {model_count} exceeds 55")
        elif model_count > 0:
            print(f"✅ PHASE 3 FIX SUCCESS: Model count {model_count} within expected range")
        else:
            print("⚠️ PHASE 3 FIX ISSUE: Model count is 0")
        
        # Test multiple results for consistency
        print("\n🔍 CONSISTENCY CHECK across multiple mines:")
        model_counts = []
        source_counts = []
        
        for result in results[:5]:  # Check first 5 mines
            model_counts.append(result.get('model_count', 0))
            source_counts.append(result.get('total_sources', 0))
        
        print(f"Model counts: {model_counts}")
        print(f"Source counts: {source_counts}")
        
        # Check for unrealistic values
        max_model_count = max(model_counts) if model_counts else 0
        if max_model_count > 55:
            print(f"⚠️ INCONSISTENCY: Some mines show {max_model_count} models (>55)")
        else:
            print("✅ CONSISTENCY: All model counts within expected range")
            
    except Exception as e:
        print(f"❌ PROCESSING ERROR: {str(e)}")

def test_statistics_api():
    """Test statistics API for model count"""
    print("\n📊 STATISTICS API TEST:")
    print("-" * 30)
    
    try:
        url = "http://localhost:8000/api/statistics/models/comprehensive"
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Statistics API ERROR: Status {response.status_code}")
            return
            
        data = response.json()
        
        if data.get('success'):
            summary = data.get('data', {}).get('summary', {})
            total_models = summary.get('total_models', 0)
            tested_models = summary.get('tested_models', 0)
            available_models = summary.get('available_untested_models', 0)
            
            print(f"📊 Total Models: {total_models}")
            print(f"🧪 Tested Models: {tested_models}")
            print(f"💤 Available Models: {available_models}")
            
            if total_models == 55:
                print("✅ STATISTICS SUCCESS: Exactly 55 models as expected")
            else:
                print(f"⚠️ STATISTICS ISSUE: Expected 55 models, got {total_models}")
        else:
            print(f"❌ Statistics API returned error: {data}")
            
    except Exception as e:
        print(f"❌ Statistics API ERROR: {str(e)}")

if __name__ == "__main__":
    test_consolidated_results_fixes()
    test_statistics_api()
    
    print("\n🎉 PHASE 4 VALIDATION COMPLETE!")
    print("=" * 60)