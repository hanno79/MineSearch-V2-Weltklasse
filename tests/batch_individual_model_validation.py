"""
Author: rahn
Datum: 17.08.2025
Version: 1.0
Beschreibung: Validation Test für Individual Batch Search Processing
"""

import asyncio
import json
import requests
import time
from datetime import datetime

class BatchIndividualModelValidation:
    def __init__(self):
    """__init__ - TODO: Dokumentation hinzufügen"""
        self.base_url = "http://localhost:8000"

    async def test_individual_batch_processing(self):
        """Test Individual Model Processing in Batch Search"""
        print("🚀 BATCH INDIVIDUAL MODEL PROCESSING VALIDATION")
        print("=" * 70)

        try:
            # STEP 1: Get baseline statistics count
            print("📊 [BASELINE] Getting baseline statistics...")
            baseline_response = requests.get(f"{self.base_url}/api/statistics/models/comprehensive")
            baseline_data = baseline_response.json()
            baseline_models = baseline_data.get("models", []) if baseline_response.status_code == 200 else []
            baseline_count = len(baseline_models)

            print(f"📋 Baseline Model Count: {baseline_count}")

            # Show current models in baseline
            existing_models = [model.get("model_id", 'unknown') for model in baseline_models]
            print(f"📋 Current Models: {existing_models[:10]}...")  # Show first 10

            # STEP 2: Check SearchResult database entries (before test)
            print("\n📊 [DATABASE] Checking SearchResult entries...")
            results_response = requests.get(f"{self.base_url}/api/results?days_back=1")

            if results_response.status_code == 200:
                results_data = results_response.json()
                before_search_count = len(results_data.get("results", []))
                print(f"📋 SearchResult Entries (Before): {before_search_count}")

                # Check for concatenated vs individual model entries
                recent_models = []
                for result in results_data.get("results", [])[:20]:  # Check last 20
                    model_used = result.get("model_used", '')
                    recent_models.append(model_used)

                # Count concatenated vs individual
                concatenated_count = sum(1 for m in recent_models if '_' in m and len(m) > 50)
                individual_count = sum(1 for m in recent_models if '_' not in m or len(m) < 50)

                print(f"📋 Recent Models Analysis:")
                print(f"   - Individual Model Entries: {individual_count}")
                print(f"   - Concatenated Model Entries: {concatenated_count}")

            # STEP 3: Perform test batch search with multiple models
            print("\n🔍 [TEST SEARCH] Performing batch search with individual models...")

            # Create minimal CSV for test
            csv_content = """mine_name,country,commodity,region
Batch Test Mine,Canada,Gold,Quebec"""

            # Upload CSV
            files = {'csv_file': ('test_batch.csv', csv_content, 'text/csv')}
            upload_response = requests.post(f"{self.base_url}/api/upload-csv", files=files)

            if upload_response.status_code == 200:
                print("✅ CSV uploaded successfully")

                # Extract session_id from HTML response
                html_content = upload_response.text
                session_start = html_content.find('value="') + len('value="')
                session_end = html_content.find('"', session_start)
                session_id = html_content[session_start:session_end]

                print(f"📋 Session ID: {session_id}")

                # Define test models (use small subset for quick validation)
                test_models = [
                    "openrouter:deepseek-free",
                    "perplexity:sonar",
                    "openrouter:kimi-k2"
                ]

                # Perform batch search
                batch_payload = {
                    'session_id': session_id,
                    'selected_models': ','.join(test_models),
                    'search_type': 'standard',
                    'count': '1',
                    'search_all': 'false'
                }

                print(f"🎯 Testing with models: {test_models}")
                print(f"📦 Batch payload: {batch_payload}")

                # Execute batch search
                search_response = requests.post(
                    f"{self.base_url}/api/batch-search",
                    data=batch_payload,
                    timeout=300  # 5 minute timeout
                )

                print(f"📡 Batch search response status: {search_response.status_code}")

                if search_response.status_code == 200:
                    print("✅ Batch search completed successfully")

                    # Wait for database processing
                    print("⏳ [WAITING] Waiting for database processing...")
                    await asyncio.sleep(10)

                    # STEP 4: Validate individual model entries in database
                    print("\n📈 [VALIDATION] Checking individual model database entries...")

                    # Check SearchResult entries (after test)
                    after_results_response = requests.get(f"{self.base_url}/api/results?days_back=1")

                    if after_results_response.status_code == 200:
                        after_results_data = after_results_response.json()
                        after_search_count = len(after_results_data.get("results", []))

                        print(f"📋 SearchResult Entries (After): {after_search_count}")
                        print(f"📈 New Entries Created: {after_search_count - before_search_count}")

                        # Check for individual model entries from our test
                        test_mine_results = []
                        for result in after_results_data.get("results", []):
                            if result.get('mine_name') == 'Batch Test Mine':
                                test_mine_results.append(result)

                        print(f"🎯 Test Mine Results Found: {len(test_mine_results)}")

                        # Validate each test model got individual entry
                        found_models = []
                        for result in test_mine_results:
                            model_used = result.get("model_used", '')
                            found_models.append(model_used)
                            print(f"   ✅ Found individual entry: {model_used}")

                        # Check if all test models are represented individually
                        individual_success = all(model in found_models for model in test_models)

                        # STEP 5: Validate updated statistics
                        print("\n📈 [VALIDATION] Checking updated model statistics...")

                        final_response = requests.get(f"{self.base_url}/api/statistics/models/comprehensive")
                        final_data = final_response.json()
                        final_models = final_data.get("models", []) if final_response.status_code == 200 else []
                        final_count = len(final_models)

                        print(f"📈 Final Model Count: {final_count}")
                        print(f"📊 Models Added to Statistics: {final_count - baseline_count}")

                        # Check if test models appear in statistics
                        stats_models = [model.get("model_id", '') for model in final_models]
                        stats_success = all(model in stats_models for model in test_models)

                        # Print test model statistics
                        print(f"📋 Test Model Statistics:")
                        for test_model in test_models:
                            if test_model in stats_models:
                                model_stats = next((m for m in final_models if m.get('model_id') == test_model), {})
                                total_searches = model_stats.get("total_searches", 0)
                                success_rate = model_stats.get("success_rate", 0)
                                print(f"   ✅ {test_model}: {total_searches} searches, {success_rate:.1%} success")
                            else:
                                print(f"   ❌ {test_model}: NOT FOUND in statistics")

                        # FINAL VALIDATION RESULT
                        print(f"\n🚀 INDIVIDUAL BATCH PROCESSING VALIDATION RESULTS:")
                        print(f"=" * 70)
                        print(f"📊 Database Individual Entries: {'✅ SUCCESS' if individual_success else '❌ FAILED'}")
                        print(f"📈 Statistics Updates: {'✅ SUCCESS' if stats_success else '❌ FAILED'}")
                        print(f"📋 Models Tested: {len(test_models)}")
                        print(f"📋 Individual DB Entries: {len(test_mine_results)}")
                        print(f"📈 New Statistics Cards: {final_count - baseline_count}")

                        validation_success = individual_success and stats_success

                        if validation_success:
                            print(f"\n🎉 CRITICAL FIX VALIDATION: VOLLSTÄNDIG ERFOLGREICH!")
                            print(f"   ✅ Individual Model Processing funktioniert")
                            print(f"   ✅ Each Model gets separate Database Entry")
                            print(f"   ✅ Statistics Update Triggers arbeiten korrekt")
                            print(f"   ✅ Batch → Individual → Database → Statistics Pipeline OK")
                        else:
                            print(f"\n⚠️ CRITICAL FIX VALIDATION: PROBLEME ERKANNT")
                            print(f"   🔍 Individual Processing: {'✅' if individual_success else '❌'}")
                            print(f"   🔍 Statistics Updates: {'✅' if stats_success else '❌'}")

                        return {
                            'validation_success': validation_success,
                            'individual_success': individual_success,
                            'stats_success': stats_success,
                            'test_models': test_models,
                            'found_models': found_models,
                            'baseline_count': baseline_count,
                            'final_count': final_count,
                            'new_entries': after_search_count - before_search_count,
                            'test_mine_results': len(test_mine_results)
                        }

                else:
                    print(f"❌ Batch search failed with status: {search_response.status_code}")
                    print(f"📄 Response snippet: {search_response.text[:500]}")
                    return None
            else:
                print(f"❌ CSV upload failed with status: {upload_response.status_code}")
                return None

        except Exception as e:
            print(f"❌ Batch individual model validation error: {e}")
            import traceback
            traceback.print_exc()
            return None

# Main execution
if __name__ == "__main__":
    async def main():
        validator = BatchIndividualModelValidation()
        result = await validator.test_individual_batch_processing()

        if result:
            with open('/app/tests/batch_individual_validation_results.json', 'w') as f:
                json.dump(result, f, indent=2)

            print(f"\n💾 Batch individual validation results saved")

            if result['validation_success']:
                print(f"\n🎆 SUCCESS: Individual Batch Processing Fix is working perfectly!")
            else:

    asyncio.run(main())
