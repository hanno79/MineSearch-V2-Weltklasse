import sqlite3
import json

conn = sqlite3.connect('mines.db')
cursor = conn.cursor()

print('=== FÖRDERMENGE-EXTRAKTION ANALYSE ===')

# Alle Einträge mit Fördermenge-Feld
cursor.execute('SELECT mine_name, model_used, structured_data FROM search_results WHERE structured_data LIKE "%Fördermenge/Jahr%" LIMIT 10')
results = cursor.fetchall()

print(f'Gefundene Einträge mit Fördermenge-Feld: {len(results)}')

foerdermenge_filled = 0
foerdermenge_empty = 0

for result in results:
    data = json.loads(result[2])
    foerdermenge = data.get('Fördermenge/Jahr', '')
    
    if foerdermenge and foerdermenge not in ['X', '']:
        foerdermenge_filled += 1
        print(f'\n✓ {result[0]} ({result[1]}): "{foerdermenge}"')
    else:
        foerdermenge_empty += 1

print(f'\n=== STATISTIK ===')
print(f'Fördermenge gefüllt: {foerdermenge_filled}')
print(f'Fördermenge leer/X: {foerdermenge_empty}')

# Suche nach Einträgen wo Rohstoffe Gold-Mengen enthalten aber Fördermenge leer ist
print(f'\n=== CROSS-FIELD PROBLEM ===')
cursor.execute('SELECT mine_name, model_used, structured_data FROM search_results WHERE structured_data LIKE "%Gold%" AND structured_data LIKE "%Unzen%" LIMIT 5')
gold_results = cursor.fetchall()

for result in gold_results:
    data = json.loads(result[2])
    rohstoffe = data.get('Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)', '')
    foerdermenge = data.get('Fördermenge/Jahr', '')
    
    if 'Unzen' in rohstoffe and (not foerdermenge or foerdermenge in ['X', '']):
        print(f'\n❌ PROBLEM: {result[0]}')
        print(f'   Rohstoffe: "{rohstoffe[:100]}..."')
        print(f'   Fördermenge: "{foerdermenge}"')
        print(f'   → Gold-Menge steht in Rohstoffe, nicht in Fördermenge!')

conn.close()