#!/usr/bin/env python3
"""
Test script to verify the search service fix
"""

import asyncio
from search_service import search_service
import logging
logging.basicConfig(level=logging.INFO)

async def test_search():
    try:
        result = await search_service.search_mine(
            mine_name='Eleonore Mine',
            model='openrouter:anthropic/claude-3.5-sonnet', 
            country='Canada'
        )
        print('\n=== SEARCH RESULT ===')
        print('Success:', result.get('success', False))
        if result.get('success'):
            data = result.get('data', {})
            structured_data = data.get('structured_data', {})
            print('Fields with data:')
            for field, value in structured_data.items():
                if value and value != 'X' and not field.startswith('_'):
                    print(f'  {field}: {value}')
            print('Sources found:', len(data.get('sources', [])))
        else:
            print('Error:', result.get('error', 'Unknown error'))
        return result
    except Exception as e:
        print('Error:', str(e))
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = asyncio.run(test_search())
    print('Final result:', 'SUCCESS' if result and result.get('success') else 'FAILED')