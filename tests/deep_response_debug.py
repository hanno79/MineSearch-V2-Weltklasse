"""
Author: rahn
Datum: 17.08.2025
Version: 1.0
Beschreibung: Deep Response Debug - Capture RAW API responses vor Datenextraktion
"""

import asyncio
import sys
import os
import json
sys.path.append('/app/backend')

# Patch the MineSearchService to capture raw responses
import logging
from minesearch.search_service import MineSearchService
from minesearch.enhanced_source_discovery import EnhancedSourceDiscovery

# Set up debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class DeepResponseDebugger:
    def __init__(self):
        self.test_mine_name = "Lac Expanse"
        self.test_country = "Canada"
        self.test_region = "Quebec"
        self.captured_responses = {}
        
    async def test_raw_api_response(self):
        """Test RAW API Response Capture"""
        print("🔬 DEEP API RESPONSE DEBUG")
        print("=" * 80)
        
        # Patch the search service to capture raw responses
        search_service = MineSearchService()
        
        print(f"🧪 Testing: {self.test_mine_name} ({self.test_country}, {self.test_region})")
        
        try:
            # Source Discovery first
            discovery = EnhancedSourceDiscovery()
            sources = discovery.discover_sources_for_mine(
                mine_name=self.test_mine_name,
                country=self.test_country,
                region=self.test_region
            )
            print(f"📊 Sources discovered: {len(sources)}")
            
            # Test with OpenRouter (free model)
            print(f"\n🚀 [RAW API CALL] OpenRouter DeepSeek Free...")
            
            result = await search_service.search_mine(
                mine_name=self.test_mine_name,
                model="openrouter:deepseek-free",
                country=self.test_country,
                region=self.test_region,
                commodity=None
            )
            
            print(f"✅ Search completed: {result.get('success', False)}")
            
            # Analyze the result structure
            if result.get('success'):
                data = result.get('data', {})
                raw_response = data.get('raw_response', '')
                structured_data = data.get('structured_data', {})
                sources_found = data.get('sources', [])
                
                print(f"\n📋 DETAILED ANALYSIS:")
                print(f"Raw response length: {len(raw_response)}")
                print(f"Structured fields: {len(structured_data)}")
                print(f"Sources in result: {len(sources_found)}")
                
                # Check if raw_response is actually there
                if raw_response:
                    print(f"\n📄 RAW RESPONSE PREVIEW (first 500 chars):")
                    print(f"{raw_response[:500]}...")
                    
                    # Check for mining terms
                    mining_terms = ['mine', 'mining', 'exploration', 'gold', 'copper', 'quebec', 'lac expanse', 'operator', 'owner', 'production']
                    found_terms = [term for term in mining_terms if term.lower() in raw_response.lower()]
                    print(f"\n🔍 Mining terms found: {found_terms}")
                    
                    # Save raw response for analysis
                    self.captured_responses['openrouter_raw'] = raw_response
                else:
                    print(f"\n❌ PROBLEM: Raw response is EMPTY!")
                    print(f"   This means either:")
                    print(f"   1. API returned no content")
                    print(f"   2. Raw response is not being captured/stored")
                    print(f"   3. Response processing is consuming/losing the content")
                
                # Analyze structured data
                print(f"\n📊 STRUCTURED DATA ANALYSIS:")
                filled_fields = [(k, v) for k, v in structured_data.items() if v and str(v).strip() not in ['', 'X', 'k.A.']]
                x_fields = [(k, v) for k, v in structured_data.items() if str(v).strip() == 'X']
                
                print(f"Filled fields ({len(filled_fields)}):")
                for key, value in filled_fields[:10]:
                    print(f"  ✅ {key}: {repr(value)[:100]}...")
                    
                print(f"\nX-marked fields ({len(x_fields)}):")
                for key, value in x_fields[:10]:
                    print(f"  ❌ {key}: {value}")
                
                # Check _source_mapping for debugging
                source_mapping = structured_data.get('_source_mapping', {})
                if source_mapping:
                    print(f"\n🗄️ SOURCE MAPPING:")
                    print(f"Sources tracked: {len(source_mapping.get('sources', {}))}")
                    print(f"Field sources: {len(source_mapping.get('field_sources', {}))}")
                
                return {
                    'success': True,
                    'raw_response_length': len(raw_response),
                    'raw_response_empty': len(raw_response) == 0,
                    'filled_fields': len(filled_fields),
                    'x_fields': len(x_fields),
                    'mining_terms_found': len(found_terms) if raw_response else 0,
                    'has_source_mapping': bool(source_mapping),
                    'structured_data_sample': dict(list(structured_data.items())[:5])
                }
            else:
                error = result.get('error', 'Unknown error')
                print(f"❌ Search failed: {error}")
                return {'success': False, 'error': error}
                
        except Exception as e:
            print(f"💥 Deep debug error: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}
    
    async def test_with_simple_mine(self):
        """Test with a well-known mine for comparison"""
        print(f"\n🔬 COMPARISON TEST: Well-known mine")
        print("=" * 60)
        
        search_service = MineSearchService()
        
        # Test with a famous Canadian mine
        famous_mine = "Canadian Malartic"
        
        try:
            result = await search_service.search_mine(
                mine_name=famous_mine,
                model="openrouter:deepseek-free",
                country="Canada",
                region="Quebec",
                commodity="Gold"
            )
            
            if result.get('success'):
                data = result.get('data', {})
                raw_response = data.get('raw_response', '')
                structured_data = data.get('structured_data', {})
                
                filled_fields = [(k, v) for k, v in structured_data.items() if v and str(v).strip() not in ['', 'X', 'k.A.']]
                
                print(f"📊 {famous_mine} Results:")
                print(f"Raw response: {len(raw_response)} chars")
                print(f"Filled fields: {len(filled_fields)}")
                
                if len(raw_response) > 100:
                    print(f"✅ Raw response looks good: {raw_response[:200]}...")
                else:
                    print(f"❌ Raw response too short: {repr(raw_response)}")
                    
                return len(raw_response) > 100
            else:
                print(f"❌ {famous_mine} search failed")
                return False
                
        except Exception as e:
            print(f"💥 Comparison test error: {e}")
            return False

# Main execution
if __name__ == "__main__":
    async def main():
        debugger = DeepResponseDebugger()
        
        # Deep debug of Lac Expanse
        result = await debugger.test_raw_api_response()
        
        # Comparison with famous mine
        comparison_ok = await debugger.test_with_simple_mine()
        
        print(f"\n🎯 DEEP DEBUG CONCLUSION:")
        print(f"=" * 80)
        
        if result.get('success'):
            if result['raw_response_empty']:
                print(f"🚨 CRITICAL ISSUE: RAW RESPONSE IS EMPTY")
                print(f"   ➤ API calls succeed but return no content")
                print(f"   ➤ This explains why all fields are 'X' (not found)")
                print(f"   ➤ Problem is in API response, not data extraction")
                if comparison_ok:
                    print(f"   ➤ BUT comparison mine works → Problem specific to 'Lac Expanse'")
                else:
                    print(f"   ➤ AND comparison mine also fails → Systematic API issue")
            else:
                print(f"✅ Raw response contains {result['raw_response_length']} characters")
                print(f"   ➤ Problem is in data extraction patterns")
                print(f"   ➤ Need to debug extraction patterns against this content")
        else:
            print(f"💥 API calls are failing: {result.get('error')}")
            
        # Save detailed results
        with open('/app/tests/deep_debug_results.json', 'w') as f:
            json.dump({
                'lac_expanse': result,
                'comparison_mine_ok': comparison_ok,
                'timestamp': str(asyncio.get_event_loop().time())
            }, f, indent=2)
        
        print(f"\n💾 Detailed results saved to deep_debug_results.json")
    
    asyncio.run(main())