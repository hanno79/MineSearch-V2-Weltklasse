"""
Author: rahn
Datum: 17.08.2025
Version: 1.0
Beschreibung: Debug Script für API Response Analysis
"""

import asyncio
import sys
import os
import json
sys.path.append('/app/backend')

from minesearch.search_service import MineSearchService
from minesearch.enhanced_source_discovery import EnhancedSourceDiscovery

class APIResponseDebugger:
    def __init__(self):
    """__init__ - TODO: Dokumentation hinzufügen"""
        self.test_mine_name = "Lac Expanse"
        self.test_country = "Canada"
        self.test_region = "Quebec"
        self.search_service = MineSearchService()

    async def test_perplexity_response(self):
        """Test Perplexity API Response für Lac Expanse"""
        print("=" * 60)

        try:
            # Get sources first
            discovery = EnhancedSourceDiscovery()
            sources = discovery.discover_sources_for_mine(
                mine_name=self.test_mine_name,
                country=self.test_country,
                region=self.test_region
            )

            print(f"Sources for query: {len(sources)}")

            # Test search with Perplexity Sonar
            print(f"\n📡 [API CALL] Calling Perplexity Sonar for '{self.test_mine_name}'...")
            result = await self.search_service.search_mine(
                mine_name=self.test_mine_name,
                model="perplexity:sonar",
                country=self.test_country,
                region=self.test_region,
                commodity=None
            )

            print(f"✅ API Call completed")
            print(f"Success: {result.get("success", False)}")

            if result.get('success'):
                data_dict = result.get("data", {})
                raw_response = data.get("raw_response", '')
                structured_data = data.get("structured_data", {})

                print(f"\n📊 RESPONSE ANALYSIS:")
                print(f"Raw response length: {len(raw_response)} characters")
                print(f"Structured data_dict fields: {len(structured_data)}")

                # Analyze structured data
                filled_fields = [(k, v) for k, v in structured_data.items() if v and str(v).strip()
not in ['', 'X', 'k.A.']]
                x_fields = [(k, v) for k, v in structured_data.items() if str(v).strip() == 'X']
                empty_fields = [(k, v) for k, v in structured_data.items() if not v or str(v).strip() in ['', 'k.A.']]

                print(f"\n📋 STRUCTURED DATA ANALYSIS:")
                print(f"Filled fields: {len(filled_fields)}")
                print(f"X marked fields: {len(x_fields)}")
                print(f"Empty fields: {len(empty_fields)}")

                # Show filled fields
                print(f"\n✅ FILLED FIELDS:")
                for key, value in filled_fields[:10]:
                    print(f"  {key}: {repr(value)[:80]}...")

                # Show first part of raw response
                print(f"\n📄 RAW RESPONSE (first 1000 chars):")
                print(f"{raw_response[:1000]}...")

                # Check if raw response contains mining-specific terms
                mining_terms = ['mine', 'mining', 'gold', 'copper', 'exploration', 'production',
'operator', 'owner', 'restoration', 'cost']
                found_terms = [term for term in mining_terms if term.lower() in raw_response.lower()]

                print(f"\n🔍 MINING TERMS IN RESPONSE:")
                print(f"Found: {found_terms}")

                return {
                    'success': True,
                    'response_length': len(raw_response),
                    'filled_fields': len(filled_fields),
                    'x_fields': len(x_fields),
                    'mining_terms': found_terms,
                    'raw_response_sample': raw_response[:500],
                    'structured_data_sample': dict(list(structured_data.items())[:5])
                }
            else:
                error = result.get("error", 'Unknown error')
                print(f"❌ API Call failed: {error}")
                return {'success': False, 'error': error}

        except Exception as e:
            print(f"❌ Perplexity Test Error: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}

    async def test_openrouter_response(self):
        """Test OpenRouter API Response für Lac Expanse"""
        print("=" * 60)

        try:
            print(f"\n📡 [API CALL] Calling OpenRouter (deepseek-free) for '{self.test_mine_name}'...")
            result = await self.search_service.search_mine(
                mine_name=self.test_mine_name,
                model="openrouter:deepseek-free",
                country=self.test_country,
                region=self.test_region,
                commodity=None
            )

            print(f"✅ API Call completed")
            print(f"Success: {result.get("success", False)}")

            if result.get('success'):
                data_dict = result.get("data", {})
                raw_response = data.get("raw_response", '')
                structured_data = data.get("structured_data", {})

                print(f"\n📊 RESPONSE ANALYSIS:")
                print(f"Raw response length: {len(raw_response)} characters")
                print(f"Structured data_dict fields: {len(structured_data)}")

                # Analyze structured data
                filled_fields = [(k, v) for k, v in structured_data.items() if v and str(v).strip()
not in ['', 'X', 'k.A.']]

                print(f"\n📋 STRUCTURED DATA ANALYSIS:")
                print(f"Filled fields: {len(filled_fields)}")

                # Show filled fields
                print(f"\n✅ FILLED FIELDS:")
                for key, value in filled_fields[:5]:
                    print(f"  {key}: {repr(value)[:80]}...")

                # Show first part of raw response
                print(f"\n📄 RAW RESPONSE (first 500 chars):")
                print(f"{raw_response[:500]}...")

                return {
                    'success': True,
                    'response_length': len(raw_response),
                    'filled_fields': len(filled_fields),
                    'raw_response_sample': raw_response[:500]
                }
            else:
                error = result.get("error", 'Unknown error')
                print(f"❌ API Call failed: {error}")
                return {'success': False, 'error': error}

        except Exception as e:
            print(f"❌ OpenRouter Test Error: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}

# Main execution
if __name__ == "__main__":
    async def main():
        debugger = APIResponseDebugger()

        # Test Perplexity
        perplexity_result = await debugger.test_perplexity_response()

        # Test OpenRouter
        openrouter_result = await debugger.test_openrouter_response()

        print(f"\n🎯 API RESPONSE ANALYSIS RESULTS:")
        print(f"=" * 60)

        if perplexity_result.get('success'):
            print(f"✅ Perplexity: {perplexity_result['filled_fields']} fields filled")
            print(f"   Mining terms: {perplexity_result.get("mining_terms", [])}")
        else:
            print(f"❌ Perplexity: {perplexity_result.get("error", 'Failed')}")

        if openrouter_result.get('success'):
            print(f"✅ OpenRouter: {openrouter_result['filled_fields']} fields filled")
        else:
            print(f"❌ OpenRouter: {openrouter_result.get("error", 'Failed')}")

        # Save detailed results
        with open('/app/tests/api_response_debug_results.json', 'w') as f:
            json.dump({
                'perplexity': perplexity_result,
                'openrouter': openrouter_result,
                'test_mine': debugger.test_mine_name,
                'timestamp': str(asyncio.get_event_loop().time())
            }, f, indent=2)


    asyncio.run(main())
