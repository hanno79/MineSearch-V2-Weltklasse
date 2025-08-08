import sqlite3
import json

conn = sqlite3.connect('mines.db')
cursor = conn.cursor()

# Suche nach problematischen Minentyp-Einträgen
cursor.execute('SELECT mine_name, model_used, search_timestamp, structured_data FROM search_results WHERE structured_data LIKE "%Untertage/ Open-Pit/ usw.%" LIMIT 3')
results = cursor.fetchall()

print('=== MINENTYP-PROBLEM ANALYSE ===')
for i, result in enumerate(results, 1):
    print(f'\n--- FALL {i} ---')
    print(f'Mine: {result[0]}')
    print(f'Model: {result[1]}')
    print(f'Timestamp: {result[2]}')
    
    data = json.loads(result[3])
    
    # Schaue nach dem Minentyp-Feld
    minentyp_field = 'Minentyp (Untertage/ Open-Pit/ usw.)'
    if minentyp_field in data:
        minentyp = data[minentyp_field]
        print(f'Minentyp-Feld: "{minentyp}"')
        
        if 'usw.)' in minentyp:
            print('PROBLEM: Placeholder-Text "usw.)" wurde nicht ersetzt!')

print('\n=== ÄLTERE VS NEUERE EINTRÄGE ===')

# Suche nach neueren Einträgen mit besseren Werten  
cursor.execute('SELECT mine_name, model_used, search_timestamp, structured_data FROM search_results WHERE search_timestamp > "2025-07-29" AND structured_data LIKE "%Minentyp%" LIMIT 3')
newer_results = cursor.fetchall()

print(f'Neuere Einträge (nach 2025-07-29): {len(newer_results)}')
for result in newer_results:
    data = json.loads(result[3])
    minentyp_field = 'Minentyp (Untertage/ Open-Pit/ usw.)'
    if minentyp_field in data:
        print(f'{result[0]}: "{data[minentyp_field]}"')

conn.close()