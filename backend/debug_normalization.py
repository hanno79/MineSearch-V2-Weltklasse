#!/usr/bin/env python3
"""
Debug Script für Normalisierungs-Validierung
"""

import sqlite3

conn = sqlite3.connect('mines.db')
cursor = conn.cursor()

print('🔍 DEBUG: NORMALISIERUNGS-VALIDIERUNG')
print('=' * 80)

# 1. Schema prüfen
cursor.execute('PRAGMA table_info(mine_data_fields)')
columns = cursor.fetchall()
print('📋 MINE_DATA_FIELDS SPALTEN:')
for col in columns:
    null_status = 'NOT NULL' if col[3] else 'NULL'
    print(f'   {col[1]:<25} {col[2]:<15} {null_status}')

print()

# 2. Letzte Einträge mit allen Fremdschlüssel-Spalten
cursor.execute('''
SELECT id, field_name, field_value, 
       commodity_id, company_id, activity_status_id, mine_type_id,
       country_id_ref, region_id_ref, extraction_timestamp
FROM mine_data_fields 
ORDER BY id DESC 
LIMIT 5
''')

recent_entries = cursor.fetchall()
print('📊 LETZTE 5 EINTRÄGE:')
for entry in recent_entries:
    id_val, field_name, field_value, comm_id, comp_id, status_id, type_id, country_id, region_id, timestamp = entry
    print(f'   ID {id_val}: {field_name} = "{field_value}"')
    
    fk_values = []
    if comm_id: fk_values.append(f'commodity_id={comm_id}')
    if comp_id: fk_values.append(f'company_id={comp_id}')
    if status_id: fk_values.append(f'status_id={status_id}')
    if type_id: fk_values.append(f'type_id={type_id}')
    if country_id: fk_values.append(f'country_id={country_id}')
    if region_id: fk_values.append(f'region_id={region_id}')
    
    if fk_values:
        fk_str = ', '.join(fk_values)
        print(f'        FKs: {fk_str}')
    else:
        print('        FKs: Alle NULL')

print()

# 3. Spezifische Feldtypen checken
print('🎯 SPEZIFISCHE FELDTYPEN:')

# Country Felder
cursor.execute("SELECT field_name, field_value, country_id_ref FROM mine_data_fields WHERE field_name LIKE '%country%' OR field_name LIKE '%Country%'")
country_fields = cursor.fetchall()
if country_fields:
    print(f'   Countries ({len(country_fields)}):')
    for field_name, field_value, country_id in country_fields:
        print(f'      {field_name}: "{field_value}" -> country_id_ref={country_id}')
else:
    print('   ❌ Keine Country-Felder gefunden')

# Rohstoff Felder
cursor.execute("SELECT field_name, field_value, commodity_id FROM mine_data_fields WHERE field_name LIKE '%rohstoff%' OR field_name LIKE '%commodity%'")
commodity_fields = cursor.fetchall()
if commodity_fields:
    print(f'   Commodities ({len(commodity_fields)}):')
    for field_name, field_value, commodity_id in commodity_fields:
        print(f'      {field_name}: "{field_value}" -> commodity_id={commodity_id}')
else:
    print('   ❌ Keine Commodity-Felder gefunden')

# Firmen Felder
cursor.execute("SELECT field_name, field_value, company_id FROM mine_data_fields WHERE field_name LIKE '%eigentümer%' OR field_name LIKE '%betreiber%' OR field_name LIKE '%owner%' OR field_name LIKE '%operator%'")
company_fields = cursor.fetchall()
if company_fields:
    print(f'   Companies ({len(company_fields)}):')
    for field_name, field_value, company_id in company_fields:
        print(f'      {field_name}: "{field_value}" -> company_id={company_id}')
else:
    print('   ❌ Keine Company-Felder gefunden')

conn.close()

print()
print('🎯 FAZIT: Normalisierung läuft aber Fremdschlüssel werden nicht gesetzt!')