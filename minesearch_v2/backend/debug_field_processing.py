#!/usr/bin/env python3
"""
Debug field processing logic to identify why critical fields are missing
"""

from database import db_manager
from database.models import SearchResult
from collections import defaultdict

def debug_field_processing():
    """Debug the field processing for critical fields"""
    
    with db_manager.get_session() as session:
        # Get one mine with multiple results
        results = session.query(SearchResult).filter(SearchResult.mine_name == 'Aubelle').all()
        
        print(f'=== DEBUGGING MINE: Aubelle ===')
        print(f'Total results: {len(results)}')
        
        # Simulate field consolidation processing
        mine_data = {
            'mine_name': 'Aubelle',
            'consolidated_fields': {}
        }
        
        for result in results:
            print(f'\nResult ID: {result.id}, Model: {result.model_used}')
            if result.structured_data:
                print(f'  Raw fields: {list(result.structured_data.keys())}')
                
                # Check for critical fields
                critical = ['Restaurationskosten', 'Kostenjahr', 'Dokumentenjahr']
                for field in critical:
                    if field in result.structured_data:
                        value = result.structured_data[field]
                        has_data = value and str(value).strip() and str(value).strip().upper() != 'X'
                        print(f'  {field}: "{value}" (has_data: {has_data})')
                        
                        # Simulate the field processing logic
                        if has_data:
                            if field not in mine_data['consolidated_fields']:
                                mine_data['consolidated_fields'][field] = []
                            mine_data['consolidated_fields'][field].append(value)
        
        print(f'\n=== FINAL CONSOLIDATED FIELDS ===')
        for field, values in mine_data['consolidated_fields'].items():
            print(f'{field}: {values}')
            
        # Now let's check what fields different mines have
        print(f'\n=== ALL MINES WITH CRITICAL FIELDS ===')
        all_results = session.query(SearchResult).all()
        mines_with_critical = defaultdict(lambda: defaultdict(list))
        
        for result in all_results:
            if result.structured_data:
                for field in ['Restaurationskosten', 'Kostenjahr', 'Dokumentenjahr']:
                    if field in result.structured_data:
                        value = result.structured_data[field] 
                        if value and str(value).strip() and str(value).strip().upper() != 'X':
                            mines_with_critical[result.mine_name][field].append({
                                'value': value,
                                'model': result.model_used
                            })
        
        for mine_name, fields in mines_with_critical.items():
            print(f'\n{mine_name}:')
            for field, entries in fields.items():
                print(f'  {field}: {len(entries)} entries')
                for entry in entries:
                    print(f'    "{entry["value"]}" ({entry["model"]})')

if __name__ == '__main__':
    debug_field_processing()