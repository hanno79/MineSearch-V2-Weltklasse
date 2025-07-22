#!/usr/bin/env python3
import sqlite3, json

conn = sqlite3.connect('/app/minesearch_v2/backend/mines.db')
cursor = conn.cursor()

cursor.execute('SELECT mine_name, structured_data FROM search_results WHERE id = 2')
result = cursor.fetchone()

if result:
    mine_name, structured_data_json = result
    structured_data = json.loads(structured_data_json) if structured_data_json else {}
    
    print(f'Mine: {mine_name}')
    print('Structured Data Fields:')
    for key, value in structured_data.items():
        if value and str(value) != 'X':
            print(f'  {key}: {value}')

conn.close()