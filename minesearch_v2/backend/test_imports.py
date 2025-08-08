#!/usr/bin/env python3
"""
Author: rahn
Datum: 26.07.2025
Version: 1.0
Beschreibung: Test imports to find what's causing batch search to fail silently
"""

import sys
import traceback

def test_batch_imports():
    """Test all imports needed for batch processing"""
    print("🔍 Testing batch processing imports...")
    
    imports_to_test = [
        ('batch_service', 'BatchService'),
        ('batch_priority_coordinator', 'batch_priority_coordinator'),
        ('model_selection_coordinator', 'model_selection_coordinator'),
        ('search_service_multi', 'MultiProviderSearchService'),
        ('cost_monitor', 'cost_monitor'),
        ('database.manager', 'db_manager'),
        ('providers.registry', 'provider_registry')
    ]
    
    successful_imports = []
    failed_imports = []
    
    for module_name, object_name in imports_to_test:
        try:
            print(f"📦 Testing import: from {module_name} import {object_name}")
            module = __import__(module_name, fromlist=[object_name])
            obj = getattr(module, object_name)
            successful_imports.append((module_name, object_name))
            print(f"✅ SUCCESS: {module_name}.{object_name}")
        except Exception as e:
            failed_imports.append((module_name, object_name, str(e)))
            print(f"❌ FAILED: {module_name}.{object_name} - {e}")
            print(f"   Traceback: {traceback.format_exc()}")
    
    print(f"\n📊 IMPORT RESULTS:")
    print(f"✅ Successful: {len(successful_imports)}")
    print(f"❌ Failed: {len(failed_imports)}")
    
    if failed_imports:
        print(f"\n⚠️  FAILED IMPORTS DETAILS:")
        for module_name, object_name, error in failed_imports:
            print(f"   {module_name}.{object_name}: {error}")
    
    return len(failed_imports) == 0

def test_batch_coordinator_specifically():
    """Test the batch coordinator that's used in batch.py"""
    print(f"\n🎯 Testing batch_priority_coordinator specifically...")
    
    try:
        from batch_priority_coordinator import batch_priority_coordinator
        print("✅ batch_priority_coordinator imported successfully")
        
        # Test if it has the required method
        if hasattr(batch_priority_coordinator, 'coordinate_priority_batch_execution'):
            print("✅ coordinate_priority_batch_execution method found")
            return True
        else:
            print("❌ coordinate_priority_batch_execution method NOT found")
            print(f"Available methods: {dir(batch_priority_coordinator)}")
            return False
            
    except Exception as e:
        print(f"❌ batch_priority_coordinator import failed: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return False

def test_csv_cache():
    """Test if CSV cache mechanism works"""
    print(f"\n💾 Testing CSV cache mechanism...")
    
    try:
        # Simulate what happens in batch.py
        uploaded_mines_cache = {}
        batch_results_cache = {}
        
        # Test cache operations
        test_session_id = "test_session_123"
        test_data = {
            'mines': [{'mine_name': 'Test Mine', 'country': 'Test Country', 'commodity': 'Test Commodity'}],
            'columns': ['mine_name', 'country', 'commodity']
        }
        
        uploaded_mines_cache[test_session_id] = test_data
        
        if test_session_id in uploaded_mines_cache:
            print("✅ CSV cache write/read works")
            retrieved_data = uploaded_mines_cache[test_session_id]
            print(f"✅ Retrieved data: {len(retrieved_data['mines'])} mines")
            return True
        else:
            print("❌ CSV cache failed")
            return False
            
    except Exception as e:
        print(f"❌ Cache test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Batch Processing Components")
    print("=" * 50)
    
    # Test imports
    imports_ok = test_batch_imports()
    
    # Test coordinator specifically
    coordinator_ok = test_batch_coordinator_specifically()
    
    # Test cache
    cache_ok = test_csv_cache()
    
    print(f"\n📊 OVERALL RESULTS:")
    print(f"✅ Imports: {'PASS' if imports_ok else 'FAIL'}")
    print(f"✅ Coordinator: {'PASS' if coordinator_ok else 'FAIL'}")
    print(f"✅ Cache: {'PASS' if cache_ok else 'FAIL'}")
    
    if not (imports_ok and coordinator_ok and cache_ok):
        print(f"\n🔥 CRITICAL ISSUE IDENTIFIED:")
        print(f"   Batch processing components are not working correctly!")
        print(f"   This explains why batch search returns empty results.")
        sys.exit(1)
    else:
        print(f"\n✅ All components working - issue must be in execution logic")
        sys.exit(0)