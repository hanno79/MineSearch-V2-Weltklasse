#!/usr/bin/env python3
"""
Author: rahn
Datum: 19.08.2025
Version: 1.0
Beschreibung: Complete CSV Batch API test for MineSearch with file upload and result validation
"""

import requests
import json
import sys

def test_csv_batch_workflow():
    """Test complete CSV batch workflow via API"""
    
    base_url = "http://localhost:8000"
    
    try:
        print("📍 Step 1: Test CSV upload endpoint")
        
        # Prepare CSV file for upload
        csv_content = """mine_name
Éléonore
Lac Expanse
Aubelle
Detour Lake"""
        
        files = {'csv_file': ('test_mines.csv', csv_content, 'text/csv')}
        
        # Upload CSV
        upload_response = requests.post(f"{base_url}/api/upload-csv", files=files)
        
        if upload_response.status_code == 200:
            print("✅ CSV upload successful")
            upload_result = upload_response.text  # HTML response
            print(f"Upload response type: {type(upload_result)}")
            
            # Check if response contains upload confirmation
            if 'csv-upload-success' in upload_result or 'batch-search-interface' in upload_result:
                print("✅ CSV upload interface confirmed")
            else:
                print("⚠️  Upload response structure different than expected")
        else:
            print(f"❌ CSV upload failed: {upload_response.status_code}")
            print(f"Error: {upload_response.text}")
            return False
        
        print("📍 Step 2: Test batch search endpoint")
        
        # Test batch search with form data (as the frontend would do)
        batch_data = {
            'model': ['gemini', 'brightdata']  # Top performers from the interface
        }
        
        batch_response = requests.post(f"{base_url}/api/batch-search", data=batch_data)
        
        if batch_response.status_code == 200:
            print("✅ Batch search started successfully")
            batch_result = batch_response.text
            
            # Look for results in the response
            if 'batch-results' in batch_result or 'results-table' in batch_result:
                print("✅ Batch results table generated")
                
                # Analyze content for 'k.A.' values
                ka_count = batch_result.count('k.A.')
                print(f"📊 'k.A.' placeholders found: {ka_count}")
                
                # Look for actual mining data
                mining_terms = ['Quebec', 'Canada', 'Gold', 'Mining', 'Exploration', 'Resource', 'Production', 'Tonnage']
                data_found = 0
                
                for term in mining_terms:
                    if term.lower() in batch_result.lower():
                        data_found += 1
                        print(f"✅ Found mining data term: {term}")
                
                print(f"📊 Mining data terms found: {data_found}/{len(mining_terms)}")
                
                # Assessment
                if data_found > ka_count:
                    print("\n✅ SUCCESS: Batch results contain more real data than placeholders!")
                    print(f"   Real data indicators: {data_found}")
                    print(f"   'k.A.' placeholders: {ka_count}")
                elif ka_count > data_found * 2:
                    print(f"\n⚠️  WARNING: High number of placeholders ({ka_count}) vs data terms ({data_found})")
                    print("   This suggests the batch search may have data quality issues")
                else:
                    print(f"\n🔍 MIXED RESULTS: {ka_count} placeholders, {data_found} data terms")
                    print("   Batch functionality working but data quality needs review")
                
            else:
                print("⚠️  Batch response doesn't contain expected results structure")
                print("Response preview:", batch_result[:500])
                
        else:
            print(f"❌ Batch search failed: {batch_response.status_code}")
            print(f"Error: {batch_response.text}")
        
        print("📍 Step 3: Test existing results for baseline")
        # Check existing data quality for comparison
        results_response = requests.get(f"{base_url}/api/results?days_back=7&sort_by=mine_name")
        if results_response.status_code == 200:
            existing_results = results_response.json()
            if existing_results:
                existing_text = json.dumps(existing_results[:5])  # Sample
                existing_ka = existing_text.count('k.A.')
                print(f"📊 Existing results baseline: {existing_ka} 'k.A.' values in sample")
        
        print("\n📈 BATCH FUNCTIONALITY TEST COMPLETED")
        print("Check the output above to evaluate:")
        print("  1. CSV upload functionality")
        print("  2. Batch search processing") 
        print("  3. Data quality in results (real data vs 'k.A.' placeholders)")
        print("  4. Comparison with existing data baseline")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during CSV batch test: {e}")
        return False

if __name__ == "__main__":
    success = test_csv_batch_workflow()
    sys.exit(0 if success else 1)