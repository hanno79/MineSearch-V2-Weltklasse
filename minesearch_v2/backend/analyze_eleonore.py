import sqlite3
import json

conn = sqlite3.connect('mines.db')
cursor = conn.cursor()

# Suche nach Éléonore Goldmengen-Problem
cursor.execute('SELECT mine_name, model_used, search_timestamp, structured_data FROM search_results WHERE mine_name = "Éléonore" AND structured_data LIKE "%270%" LIMIT 1')
result = cursor.fetchone()

if result:
    print('=== ÉLÉONORE GOLDMENGEN-PROBLEM ===')
    print(f'Mine: {result[0]}')
    print(f'Model: {result[1]}')
    print(f'Timestamp: {result[2]}')
    
    data = json.loads(result[3])
    print('\n--- EXTRAHIERTE FELDER ---')
    for key, value in data.items():
        if key != '_source_mapping':
            print(f'{key}: {value}')
            
    # Schaue nach dem Rohstoffe-Feld
    if 'Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)' in data:
        rohstoffe = data['Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)']
        print(f'\n=== ROHSTOFFE PROBLEM ===')
        print(f'Rohstoffe-Feld: {rohstoffe}')
        
        # Das ist das Problem - Gold info steht im Rohstoffe-Feld aber nicht in Fördermenge
        if '270' in rohstoffe and 'Gold' in rohstoffe:
            print('PROBLEM IDENTIFIZIERT: Gold + Menge steht in Rohstoff-Feld, nicht in Fördermenge!')

conn.close()