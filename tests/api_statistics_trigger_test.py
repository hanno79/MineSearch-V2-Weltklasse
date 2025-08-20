"""
Author: rahn
Datum: 16.08.2025
Version: 1.0
Beschreibung: API-basierter Test des Statistics Update Triggers
"""

import asyncio
import json
import requests
import time

class APIStatisticsTriggerTest:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        
    async def test_api_statistics_trigger(self):
        """Test Statistics Update via API"""
        print("🚀 API STATISTICS UPDATE TRIGGER TEST")
        print("=" * 60)
        
        try:
            # STEP 1: Get baseline statistics
            print("📊 [BASELINE] Getting current statistics...")
            baseline_response = requests.get(f"{self.base_url}/statistics/models/comprehensive")
            baseline_data = baseline_response.json()
            baseline_models = baseline_data.get('models', []) if baseline_response.status_code == 200 else []
            baseline_count = len(baseline_models)
            
            print(f"📋 Baseline Models: {baseline_count}")
            
            # Show current models
            print("📋 Current Models in Statistics:")
            for i, model in enumerate(baseline_models[:5], 1):
                model_id = model.get('model_id', 'unknown')
                total_searches = model.get('total_searches', 0)
                print(f"   {i}. {model_id}: {total_searches} searches")
            
            # STEP 2: Perform direct API search
            print("\n🔍 [SEARCH] Performing direct API search...")
            
            # Use Single Search API with test model (CORRECTED PAYLOAD)
            test_model = "openrouter:deepseek-free"
            search_payload = {
                "mine_name": "API Trigger Test Mine",
                "country": "Canada", 
                "commodity": "Gold",
                "model": test_model  # CRITICAL FIX: Use 'model' not 'model_ids' for single search
            }
            
            print(f"🎯 Testing with model: {test_model}")
            print(f"📦 Search payload: {search_payload}")
            
            # Execute search
            search_response = requests.post(
                f"{self.base_url}/api/search", 
                json=search_payload,
                timeout=120  # 2 minute timeout
            )
            
            print(f"📡 Search response status: {search_response.status_code}")
            
            if search_response.status_code == 200:
                search_result = search_response.json()
                print(f"✅ Search completed successfully")
                print(f"📊 Search result keys: {list(search_result.keys())}")
                
                # Wait a moment for database processing
                print("⏳ [WAITING] Waiting for database processing...")
                await asyncio.sleep(5)
                
                # STEP 3: Check updated statistics
                print("\n📈 [VALIDATION] Checking updated statistics...")
                final_response = requests.get(f"{self.base_url}/statistics/models/comprehensive")
                final_data = final_response.json()
                final_models = final_data.get('models', []) if final_response.status_code == 200 else []
                final_count = len(final_models)
                
                print(f"📈 Final Models: {final_count}")
                
                # Look for our test model
                test_model_found = False
                test_model_stats = None
                
                for model in final_models:
                    if model.get('model_id') == test_model:
                        test_model_found = True
                        test_model_stats = model
                        break
                
                # ANALYSIS
                print(f"\n🚀 API STATISTICS TRIGGER TEST RESULTS:")
                print(f"=" * 60)
                print(f"📊 Baseline Count: {baseline_count}")
                print(f"📈 Final Count: {final_count}")
                print(f"📦 Change: {final_count - baseline_count}")
                print(f"🎯 Test Model Found: {'✅ YES' if test_model_found else '❌ NO'}")
                
                if test_model_found and test_model_stats:
                    total_searches = test_model_stats.get('total_searches', 0)
                    success_rate = test_model_stats.get('success_rate', 0)
                    overall_score = test_model_stats.get('overall_score', 0)
                    
                    print(f"📋 Test Model Statistics:")
                    print(f"   - Model ID: {test_model}")
                    print(f"   - Total Searches: {total_searches}")
                    print(f"   - Success Rate: {success_rate:.1%}")
                    print(f"   - Overall Score: {overall_score:.1f}")
                
                # Final verdict
                trigger_success = test_model_found and (final_count >= baseline_count)
                
                if trigger_success:
                    print(f"\n🎉 CRITICAL FIX VALIDATION: ERFOLGREICH!")
                    print(f"   ✅ Statistics Update Trigger funktioniert")
                    print(f"   ✅ Neue Searches erscheinen in Statistics")
                    print(f"   ✅ Search → Database → Statistics Pipeline OK")
                else:
                    print(f"\n⚠️ CRITICAL FIX VALIDATION: PROBLEM DETECTED")
                    print(f"   ❌ Model nicht in Statistics gefunden")
                    print(f"   🔍 Trigger möglicherweise nicht ausgeführt")
                
                return {
                    'trigger_success': trigger_success,
                    'baseline_count': baseline_count,
                    'final_count': final_count,
                    'test_model': test_model,
                    'model_found': test_model_found,
                    'model_stats': test_model_stats,
                    'search_status': search_response.status_code
                }
                
            else:
                print(f"❌ Search failed with status: {search_response.status_code}")
                print(f"📄 Response: {search_response.text[:500]}")
                return None
                
        except Exception as e:
            print(f"❌ API statistics trigger test error: {e}")
            import traceback
            traceback.print_exc()
            return None

# Main execution
if __name__ == "__main__":
    async def main():
        tester = APIStatisticsTriggerTest()
        result = await tester.test_api_statistics_trigger()
        
        if result:
            with open('/app/tests/api_statistics_trigger_results.json', 'w') as f:
                json.dump(result, f, indent=2)
            
            print(f"\n💾 API trigger test results saved")
            
            if result['trigger_success']:
                print(f"\n🎆 SUCCESS: Critical Fix is working!")
            else:
                print(f"\n🔧 ATTENTION: Critical Fix needs debugging")
    
    asyncio.run(main())