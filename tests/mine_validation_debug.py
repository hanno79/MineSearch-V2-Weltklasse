"""
Author: rahn
Datum: 17.08.2025
Version: 1.0
Beschreibung: Validate if test mines are real or fictional
"""

import asyncio
import sys
import os
import json
sys.path.append('/app/backend')

from minesearch.search_service import MineSearchService

class MineValidationDebugger:
    def __init__(self):
        self.search_service = MineSearchService()

    async def test_mine_existence(self, mine_name: str, country: str, region: str = None):
        """Test if a mine actually exists"""
        print(f"\n🔍 TESTING MINE EXISTENCE: {mine_name}")
        print("=" * 60)
        
        try:
            result = await self.search_service.search_mine(
                mine_name=mine_name,
                model="openrouter:deepseek-free",
                country=country,
                region=region,
                commodity=None
            )
            
            if result.get('success'):
                data = result.get('data', {})
                structured_data = data.get('structured_data', {})
                
                # Count meaningful data (not just default values)
                meaningful_fields = []
                template_indicators = []
                
                for key, value in structured_data.items():
                    if value and str(value).strip() not in ['', 'X', 'k.A.']:
                        if key in ['Name', 'Country', 'Region', 'Quellenangaben', '_source_mapping']:
                            # These are always filled by default
                            continue
                        if 'LEER' in str(value):
                            template_indicators.append(key)
                        else:
                            meaningful_fields.append((key, value))
                
                print(f"📊 Meaningful mining data found: {len(meaningful_fields)}")
                print(f"📋 Template indicators: {len(template_indicators)}")
                
                if meaningful_fields:
                    print(f"✅ Real data found:")
                    for key, value in meaningful_fields[:5]:
                        print(f"  - {key}: {repr(value)[:80]}...")
                
                if template_indicators:
                    print(f"❌ Template responses in:")
                    for key in template_indicators[:3]:
                        print(f"  - {key}")
                
                # Determine if this appears to be a real mine
                is_real_mine = len(meaningful_fields) >= 3
                
                return {
                    'mine_name': mine_name,
                    'appears_real': is_real_mine,
                    'meaningful_fields': len(meaningful_fields),
                    'template_indicators': len(template_indicators),
                    'sample_data': dict(meaningful_fields[:3])
                }
            else:
                print(f"❌ Search failed: {result.get('error')}")
                return {'mine_name': mine_name, 'appears_real': False, 'error': result.get('error')}
                
        except Exception as e:
            print(f"💥 Test error: {e}")
            return {'mine_name': mine_name, 'appears_real': False, 'error': str(e)}

    async def test_multiple_mines(self):
        """Test multiple mines to understand the pattern"""
        
        # Test mines: mix of real and potentially fictional
        test_mines = [
            # Known real mines
            ("Canadian Malartic", "Canada", "Quebec"),
            ("Kidd Creek", "Canada", "Ontario"),
            ("Highland Valley Copper", "Canada", "British Columbia"),
            
            # Potentially fictional or very small
            ("Lac Expanse", "Canada", "Quebec"),
            
            # Definitely fictional (to test false positive detection)
            ("Fake Mine Test", "Canada", "Quebec"),
            ("Nonexistent Gold Mine", "Canada", "Ontario"),
        ]
        
        results = []
        
        print("🔬 MINE EXISTENCE VALIDATION TEST")
        print("=" * 80)
        
        for mine_name, country, region in test_mines:
            result = await self.test_mine_existence(mine_name, country, region)
            results.append(result)
            
            if result['appears_real']:
                print(f"✅ {mine_name}: APPEARS REAL ({result['meaningful_fields']} fields)")
            else:
                print(f"❌ {mine_name}: APPEARS FICTIONAL/UNKNOWN")
        
        return results

# Main execution
if __name__ == "__main__":
    async def main():
        debugger = MineValidationDebugger()
        
        # Test multiple mines
        results = await debugger.test_multiple_mines()
        
        print(f"\n🎯 MINE VALIDATION SUMMARY:")
        print(f"=" * 80)
        
        real_mines = [r for r in results if r['appears_real']]
        fictional_mines = [r for r in results if not r['appears_real']]
        
        print(f"✅ REAL MINES ({len(real_mines)}):")
        for mine in real_mines:
            print(f"  - {mine['mine_name']}: {mine['meaningful_fields']} meaningful fields")
        
        print(f"\n❌ FICTIONAL/UNKNOWN MINES ({len(fictional_mines)}):")
        for mine in fictional_mines:
            print(f"  - {mine['mine_name']}: No meaningful mining data")
        
        # Focus on Lac Expanse
        lac_expanse = next((r for r in results if r['mine_name'] == 'Lac Expanse'), None)
        if lac_expanse:
            print(f"\n🎯 LAC EXPANSE ANALYSIS:")
            if lac_expanse['appears_real']:
                print(f"✅ Lac Expanse appears to be a REAL mine")
                print(f"   Found {lac_expanse['meaningful_fields']} meaningful data fields")
            else:
                print(f"❌ Lac Expanse appears to be FICTIONAL or very obscure")
                print(f"   AI cannot find real mining data for this location")
                print(f"   This explains why searches return template structures with 'LEER'")
        
        # Save results
        with open('/app/tests/mine_validation_results.json', 'w') as f:
            json.dump({
                'validation_results': results,
                'real_mines_count': len(real_mines),
                'fictional_mines_count': len(fictional_mines),
                'lac_expanse_real': lac_expanse['appears_real'] if lac_expanse else False,
                'timestamp': str(asyncio.get_event_loop().time())
            }, f, indent=2)
        
        print(f"\n💾 Validation results saved to mine_validation_results.json")
        
        if not lac_expanse or not lac_expanse['appears_real']:
            print(f"\n🚨 CONCLUSION: Root cause identified!")
            print(f"   ➤ User is testing with fictional mine 'Lac Expanse'")
            print(f"   ➤ AI cannot find real data for non-existent mines")
            print(f"   ➤ System responds with template structures when no real data exists")
            print(f"   ➤ Need to either:")
            print(f"     1. Test with real mines like 'Canadian Malartic'")
            print(f"     2. Improve 'no data found' handling to avoid template responses")
    
    asyncio.run(main())