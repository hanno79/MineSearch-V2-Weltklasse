"""
Author: rahn
Datum: 17.08.2025
Version: 1.0
Beschreibung: Comprehensive Field Mapping Debug - Trace Data Flow von API Response bis Field Assignment
"""

import asyncio
import sys
import os
import json
import re
sys.path.append('/app/backend')

from minesearch.search_service import MineSearchService
from minesearch.data_extraction import DataExtractor
from minesearch.extraction_patterns import get_extraction_patterns

class FieldMappingDebugger:
    def __init__(self):
    """__init__ - TODO: Dokumentation hinzufügen"""
        self.search_service = MineSearchService()
        self.data_extractor = DataExtractor()
        self.patterns = get_extraction_patterns()

    async def trace_complete_pipeline(self, mine_name: str, country: str, region: str):
        """Trace complete data_dict flow from API to field assignment"""
        print(f"🔬 COMPLETE PIPELINE TRACE: {mine_name}")
        print("=" * 80)

        try:
            # Step 1: Get raw API response
            print(f"📡 STEP 1: API Call...")
            result = await self.search_service.search_mine(
                mine_name=mine_name,
                model="openrouter:deepseek-free",
                country=country,
                region=region,
                commodity=None
            )

            if not result.get('success'):
                print(f"❌ API call failed: {result.get('error')}")
                return None

            data_dict = result.get("data", {})
            raw_response = data.get("raw_content", '')  # BUGFIX: Corrected field name from raw_response to raw_content
            final_structured_data = data.get("structured_data", {})

            print(f"✅ API call successful")
            print(f"📄 Raw response length: {len(raw_response)}")
            print(f"📊 Final structured fields: {len(final_structured_data)}")

            # Step 2: Analyze raw response content
            print(f"\n🔍 STEP 2: Raw Response Analysis...")
            if raw_response:
                print(f"Raw response preview (first 500 chars):")
                print("-" * 60)
                print(raw_response[:500])
                print("-" * 60)

                # Check for mining terms
                mining_terms = ['mine', 'mining', 'operator', 'owner', 'production', 'coordinates',
'restoration', 'costs']
                found_terms = [term for term in mining_terms if term.lower() in raw_response.lower()]
                print(f"🔍 Mining terms found: {found_terms}")
            else:
                print(f"❌ PROBLEM 1: Raw response is EMPTY!")
                print(f"   This indicates API response is not being stored correctly")

            # Step 3: Manual pattern testing
            print(f"\n🧪 STEP 3: Manual Pattern Testing...")
            self.test_patterns_manually(raw_response if raw_response else "Test content: Eigentümer:
TestOwner, Betreiber: TestOperator")

            # Step 4: DataExtractor analysis
            print(f"\n⚙️ STEP 4: DataExtractor Processing...")
            if raw_response:
                manual_extraction = self.data_extractor.extract_structured_data(raw_response, mine_name, country)

                print(f"📊 Manual extraction fields: {len(manual_extraction)}")

                # Compare manual vs final results
                print(f"\n🔄 STEP 5: Field Mapping Comparison...")
                self.compare_field_assignments(manual_extraction, final_structured_data)
            else:
                print(f"❌ Cannot test DataExtractor - no raw response available")

            return {
                'raw_response_length': len(raw_response),
                'raw_response_preview': raw_response[:500] if raw_response else "",
                'final_fields_count': len(final_structured_data),
                'field_mapping_issues': self.detect_mapping_issues(final_structured_data)
            }

        except Exception as e:
            print(f"💥 Pipeline trace error: {e}")
            import traceback
            traceback.print_exc()
            return None

    def test_patterns_manually(self, content: str):
        """Test extraction patterns manually"""
        print(f"🧪 Testing patterns against content...")

        key_fields = ['Eigentümer', 'Betreiber', 'x-Koordinate', 'y-Koordinate', 'Aktivitätsstatus']

        for field in key_fields:
            if field in self.patterns:
                patterns = self.patterns[field]
                print(f"\n🔍 Testing {field} with {len(patterns)} patterns:")

                found_matches = []
                for i, pattern in enumerate(patterns[:3]):  # Test first 3 patterns
                    try:
                        match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
                        if match:
                            value = match.group(1).strip()
                            found_matches.append((i, pattern[:50], value))
                            print(f"  ✅ Pattern {i}: '{pattern[:50]}...' → '{value}'")
                    except Exception as e:
                        print(f"  ❌ Pattern {i}: '{pattern[:50]}...' → Error: {e}")

                if not found_matches:
                    print(f"  ❌ No matches for {field}")
            else:
                print(f"❌ No patterns defined for {field}")

    def compare_field_assignments(self, manual_result: dict, final_result: dict):
        """Compare manual extraction vs final result"""
        print(f"🔄 Field Assignment Comparison:")

        key_fields = ['Eigentümer', 'Betreiber', 'x-Koordinate', 'y-Koordinate', 'Aktivitätsstatus']

        for field in key_fields:
            manual_value = manual_result.get(field, 'NOT_FOUND')
            final_value = final_result.get(field, 'NOT_FOUND')

            if manual_value == final_value:
                print(f"  ✅ {field}: '{manual_value}' (consistent)")
            else:
                print(f"  ❌ {field}: Manual='{manual_value}' ≠ Final='{final_value}'")
                print(f"      🚨 FIELD MAPPING CORRUPTION DETECTED!")

    def detect_mapping_issues(self, structured_data: dict) -> list:
        """Detect field mapping issues"""
        issues = []

        for field, value in structured_data.items():
            if not value or value in ['', 'X', 'k.A.']:
                continue

            value_str = str(value)

            # Check if field contains values that belong to other fields
            if field == 'Eigentümer' and any(term in value_str.lower() for term in ['betreiber',
'operator', 'koordinate', 'coordinate']):
                issues.append(f"{field} contains wrong data: '{value_str}'")
            elif field == 'Betreiber' and any(term in value_str.lower() for term in ['koordinate',
'coordinate', 'latitude', 'longitude']):
                issues.append(f"{field} contains coordinate data: '{value_str}'")
            elif field == 'Aktivitätsstatus' and any(term in value_str.lower() for term in
['kosten', 'costs', 'million', 'dollar']):
                issues.append(f"{field} contains cost data: '{value_str}'")
            elif 'koordinate' in field.lower() and any(term in value_str.lower() for term in
['eigentümer', 'betreiber', 'owner', 'operator']):
                issues.append(f"{field} contains company data: '{value_str}'")

        return issues

    async def test_real_quebec_mines(self):
        """Test with real Quebec mines to validate pipeline"""
        print(f"\n🏔️ TESTING REAL QUEBEC MINES")
        print("=" * 80)

        real_mines = [
            ("Canadian Malartic", "Canada", "Quebec"),
            ("Eleonore", "Canada", "Quebec"),
            ("Kidd Creek", "Canada", "Ontario"),  # For comparison
        ]

        results = []

        for mine_name, country, region in real_mines:
            print(f"\n🔍 Testing: {mine_name}")
            result = await self.trace_complete_pipeline(mine_name, country, region)
            if result:
                results.append({
                    'mine': mine_name,
                    'raw_response_ok': result['raw_response_length'] > 100,
                    'field_count': result['final_fields_count'],
                    'mapping_issues': result['field_mapping_issues']
                })

                # Summary
                if result['raw_response_length'] > 100:
                    print(f"✅ {mine_name}: Raw response OK ({result['raw_response_length']} chars)")
                else:
                    print(f"❌ {mine_name}: Raw response EMPTY")

                if result['field_mapping_issues']:
                    print(f"🚨 {mine_name}: {len(result['field_mapping_issues'])} mapping issues")
                    for issue in result['field_mapping_issues']:
                        print(f"    - {issue}")
                else:
                    print(f"✅ {mine_name}: No mapping issues detected")

        return results

# Main execution
if __name__ == "__main__":
    async def main():
        debugger = FieldMappingDebugger()

        # Test with problematic mine first
        print("=" * 80)

        lac_expanse_result = await debugger.trace_complete_pipeline("Lac Expanse", "Canada", "Quebec")

        # Test with multiple real mines
        mine_results = await debugger.test_real_quebec_mines()

        print(f"=" * 80)

        if lac_expanse_result:
            if lac_expanse_result['raw_response_length'] == 0:
                print(f"🚨 CRITICAL ISSUE 1: Raw response storage is broken")
                print(f"   ➤ API calls succeed but raw_response is not saved")
                print(f"   ➤ This explains missing data_dict in extraction pipeline")

            if lac_expanse_result['field_mapping_issues']:
                print(f"🚨 CRITICAL ISSUE 2: Field mapping corruption detected")
                print(f"   ➤ {len(lac_expanse_result['field_mapping_issues'])} mapping issues found")
                for issue in lac_expanse_result['field_mapping_issues']:
                    print(f"   ➤ {issue}")

        # Analyze patterns across mines
        raw_response_issues = sum(1 for r in mine_results if not r['raw_response_ok'])
        mapping_issues_count = sum(len(r['mapping_issues']) for r in mine_results)

        print(f"\n📊 PATTERN ANALYSIS:")
        print(f"Mines with raw response issues: {raw_response_issues}/{len(mine_results)}")
        print(f"Total mapping issues found: {mapping_issues_count}")

        if raw_response_issues > 0:
            print(f"\n🎯 PRIMARY ISSUE: Raw response storage")
            print(f"   ➤ Fix needed in search_service.py or provider response handling")

        if mapping_issues_count > 0:
            print(f"\n🎯 SECONDARY ISSUE: Field mapping corruption")
            print(f"   ➤ Fix needed in data_extraction.py field assignment logic")

        # Save detailed results
        with open('/app/tests/field_mapping_debug_results.json', 'w') as f:
            json.dump({
                'lac_expanse': lac_expanse_result,
                'mine_test_results': mine_results,
                'summary': {
                    'raw_response_issues': raw_response_issues,
                    'mapping_issues_count': mapping_issues_count,
                    'primary_issue': 'raw_response_storage' if raw_response_issues > 0 else 'field_mapping',
                },
                'timestamp': str(asyncio.get_event_loop().time())
            }, f, indent=2)


    asyncio.run(main())
