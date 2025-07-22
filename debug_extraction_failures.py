#!/usr/bin/env python3
import sqlite3, json

conn = sqlite3.connect('/app/minesearch_v2/backend/mines.db')
cursor = conn.cursor()

print("🔍 DATENEXTRAKTIONS-ANALYSE")
print("=" * 50)

# Prüfe alle Ergebnisse
cursor.execute('SELECT mine_name, model_used, structured_data FROM search_results')
results = cursor.fetchall()

for mine_name, model_used, structured_data_json in results:
    print(f'\n📊 Mine: {mine_name}')
    print(f'   Model: {model_used}')
    
    if structured_data_json:
        data = json.loads(structured_data_json)
        x_fields = [k for k, v in data.items() if str(v) == 'X']
        filled_fields = [k for k, v in data.items() if v and str(v) != 'X']
        
        print(f'   X-markierte Felder: {len(x_fields)} von {len(data)}')
        print(f'   Gefüllte Felder: {len(filled_fields)}')
        
        if filled_fields:
            print(f'   ✅ Gefüllt: {filled_fields}')
        
        if len(x_fields) > len(filled_fields):
            print(f'   ❌ Problem: {len(x_fields)} Felder nicht gefunden')
            print(f'   ❌ X-Felder: {x_fields[:8]}...')

conn.close()