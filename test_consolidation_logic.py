#!/usr/bin/env python3
"""
Test consolidation logic with real data
"""
import sys
sys.path.append('/app/minesearch_v2/backend')

from database.manager import DatabaseManager
from sqlalchemy import text
import json
from collections import defaultdict

def test_consolidation():
    print('🔍 Testing consolidation logic directly...')
    db_manager = DatabaseManager()

    try:
        with db_manager.get_session() as session:
            # Get search results and group by mine
            query = '''
            SELECT mine_name, country, structured_data, model_used 
            FROM search_results 
            WHERE structured_data IS NOT NULL 
            ORDER BY mine_name
            '''
            results = session.execute(text(query)).fetchall()
            
            # Group by mine name
            mines = defaultdict(lambda: {'results': [], 'models': set()})
            
            for result in results:
                mine_name = result[0]
                country = result[1]
                structured_data = json.loads(result[2]) if result[2] else {}
                model_used = result[3]
                
                mines[mine_name]['results'].append({
                    'country': country,
                    'structured_data': structured_data,
                    'model_used': model_used
                })
                mines[mine_name]['models'].add(model_used)
            
            print(f'📊 Found {len(mines)} unique mines')
            
            # Test consolidation for first mine
            first_mine = list(mines.keys())[0]
            mine_data = mines[first_mine]
            
            print(f'\n🏔️ Testing consolidation for: {first_mine}')
            print(f'   Models used: {list(mine_data["models"])}')
            print(f'   Total results: {len(mine_data["results"])}')
            
            # Test multiple fields for duplicate detection
            test_fields = ['Country', 'Region', 'Name', 'Aktivitätsstatus']
            
            for test_field in test_fields:
                values = []
                
                for result in mine_data['results']:
                    field_value = result['structured_data'].get(test_field)
                    if field_value:
                        values.append(field_value)
                
                if values:
                    raw_values = ' / '.join(values)
                    print(f'\n📋 Field "{test_field}":')
                    print(f'   Values: {values}')
                    
                    # Test if this needs deduplication
                    unique_values = list(set(values))
                    if len(unique_values) != len(values):
                        print(f'   ✅ NEEDS DEDUPLICATION! {len(values)} total, {len(unique_values)} unique')
                        print(f'   Combined: {raw_values}')
                        
                        # Simulate deduplication result
                        value_counts = {}
                        for val in values:
                            value_counts[val] = value_counts.get(val, 0) + 1
                        
                        dedup_parts = []
                        for val, count in sorted(value_counts.items(), key=lambda x: x[1], reverse=True):
                            if count > 1:
                                dedup_parts.append(f"{val} ({count})")
                            else:
                                dedup_parts.append(val)
                        
                        print(f'   Expected deduplicated: {" / ".join(dedup_parts)}')
                    else:
                        print(f'   ℹ️  No duplicates ({len(values)} values, all unique)')
                else:
                    print(f'\n📋 Field "{test_field}": No values found')
            
            print(f'\n🎯 This mine has {len(mine_data["results"])} results from {len(mine_data["models"])} models')
            
            return len(mines) > 0
            
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_consolidation()