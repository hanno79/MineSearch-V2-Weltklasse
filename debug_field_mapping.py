#!/usr/bin/env python3
import sqlite3, json

conn = sqlite3.connect('/app/minesearch_v2/backend/mines.db')
cursor = conn.cursor()

# Deutsche Feldnamen in der DB
deutscher_feldname_map = {
    'Eigentümer': 'owner',
    'Betreiber': 'operator', 
    'x-Koordinate': 'longitude',
    'y-Koordinate': 'latitude',
    'Aktivitätsstatus': 'status',
    'Minentyp (Untertage/ Open-Pit/ usw.)': 'mine_type',
    'Produktionsstart': 'production_start',
    'Produktionsende': 'production_end',
    'Restaurationskosten': 'restoration_costs'
}

cursor.execute('SELECT mine_name, structured_data FROM search_results WHERE id = 2')
result = cursor.fetchone()

if result:
    mine_name, structured_data_json = result
    structured_data = json.loads(structured_data_json) if structured_data_json else {}
    
    print(f'Mine: {mine_name}')
    print('\nMapping deutsche -> englische Feldnamen:')
    
    for deutscher_name, englischer_name in deutscher_feldname_map.items():
        deutscher_wert = structured_data.get(deutscher_name, '')
        print(f'{deutscher_name} -> {englischer_name}: "{deutscher_wert}"')

conn.close()