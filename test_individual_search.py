#!/usr/bin/env python3
"""
Test Individual Mine Search with Abacus Provider
Testing Horne Mine from Quebec with Copper commodity
"""

import asyncio
import json
import time
import aiohttp
from datetime import datetime

async def test_individual_search():
    """Test individual mine search with Abacus provider"""
    
    # API endpoints
    base_url = "http://localhost:5001"
    models_url = f"{base_url}/api/models"
    search_url = f"{base_url}/api/search/multi"
    
    print("🔍 Testing Individual Mine Search")
    print("=" * 50)
    
    # Test 1: Check available models
    print("\n1. Checking available models...")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(models_url) as response:
                if response.status == 200:
                    models_data = await response.json()
                    print(f"✅ Found {len(models_data.get('models', {}))} available models")
                    
                    # Look for Abacus models
                    abacus_models = {k: v for k, v in models_data.get('models', {}).items() 
                                   if 'abacus' in k.lower()}
                    
                    if abacus_models:
                        print(f"🎯 Found {len(abacus_models)} Abacus models:")
                        for model_id, model_info in abacus_models.items():
                            print(f"   - {model_id}: {model_info.get('name', 'Unknown')}")
                        
                        # Use the first Abacus model found
                        selected_model = list(abacus_models.keys())[0]
                        print(f"🔧 Selected model: {selected_model}")
                    else:
                        print("❌ No Abacus models found! Using perplexity:sonar as fallback")
                        selected_model = "perplexity:sonar"
                else:
                    print(f"❌ Failed to load models: {response.status}")
                    return
        except Exception as e:
            print(f"❌ Error loading models: {e}")
            return
    
    # Test 2: Perform individual search
    print("\n2. Starting individual search for Horne Mine...")
    search_payload = {
        "mine_name": "Horne Mine",
        "country": "Canada",
        "commodity": "Copper", 
        "model_ids": [selected_model]
    }
    
    print(f"📤 Search payload: {json.dumps(search_payload, indent=2)}")
    
    start_time = time.time()
    async with aiohttp.ClientSession() as session:
        try:
            print("\n⏳ Sending search request...")
            async with session.post(search_url, json=search_payload) as response:
                print(f"📊 Response status: {response.status}")
                
                if response.status == 200:
                    result = await response.json()
                    elapsed_time = time.time() - start_time
                    
                    print(f"✅ Search completed in {elapsed_time:.2f} seconds")
                    print("\n📋 Search Results:")
                    print("=" * 30)
                    
                    if result.get('success'):
                        data = result.get('data', {})
                        print(f"Mine Name: {data.get('mine_name', 'N/A')}")
                        print(f"Country: {data.get('country', 'N/A')}")
                        print(f"Commodity: {data.get('commodity', 'N/A')}")
                        print(f"Model Used: {data.get('model_id', 'N/A')}")
                        print(f"Fields Found: {data.get('fields_found', 0)}")
                        print(f"Score: {data.get('score', 'N/A')}")
                        
                        # Show sources found
                        sources = data.get('sources', [])
                        print(f"Sources Found: {len(sources)}")
                        if sources:
                            print("\n🔗 Source URLs:")
                            for i, source in enumerate(sources[:5], 1):
                                print(f"   {i}. {source.get('url', 'No URL')}")
                            if len(sources) > 5:
                                print(f"   ... and {len(sources) - 5} more sources")
                        
                        # Show extracted data
                        extracted_data = data.get('extracted_data', {})
                        if extracted_data:
                            print("\n📊 Extracted Data:")
                            for field, value in extracted_data.items():
                                if value:
                                    print(f"   {field}: {value}")
                        
                        print(f"\n💾 Search completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                        
                        # Save results to file
                        result_file = f"horne_mine_individual_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                        with open(result_file, 'w') as f:
                            json.dump(result, f, indent=2)
                        print(f"💾 Results saved to: {result_file}")
                        
                    else:
                        print(f"❌ Search failed: {result.get('error', 'Unknown error')}")
                        
                elif response.status == 422:
                    error_data = await response.json()
                    print(f"❌ Validation error: {error_data}")
                else:
                    response_text = await response.text()
                    print(f"❌ Search failed with status {response.status}")
                    print(f"Response: {response_text[:500]}...")
                    
        except asyncio.TimeoutError:
            elapsed_time = time.time() - start_time
            print(f"⏰ Search timed out after {elapsed_time:.2f} seconds")
        except Exception as e:
            elapsed_time = time.time() - start_time
            print(f"❌ Error during search after {elapsed_time:.2f} seconds: {e}")

if __name__ == "__main__":
    asyncio.run(test_individual_search())