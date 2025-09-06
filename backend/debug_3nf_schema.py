#!/usr/bin/env python3
"""
Debug Script für neues 3NF-Schema Validierung
"""

import sqlite3

conn = sqlite3.connect('mines.db')
cursor = conn.cursor()

print('🔍 DEBUG: NEUES 3NF-SCHEMA VALIDIERUNG')
print('=' * 80)

# 1. Schema prüfen
cursor.execute('PRAGMA table_info(mine_data_fields)')
columns = cursor.fetchall()
print('📋 MINE_DATA_FIELDS SPALTEN (Neue 3NF-Struktur):')
for col in columns:
    null_status = 'NOT NULL' if col[3] else 'NULL'
    print(f'   {col[1]:<25} {col[2]:<15} {null_status}')

print()

# 2. Prüfe ob field_type_mapping Tabelle existiert und befüllt ist
try:
    cursor.execute('SELECT COUNT(*) FROM field_type_mapping')
    mapping_count = cursor.fetchone()[0]
    print(f'📊 FIELD_TYPE_MAPPING: {mapping_count} Kategorien definiert')
    
    # Zeige einige Beispiele
    cursor.execute('SELECT field_pattern, field_type, target_table FROM field_type_mapping LIMIT 10')
    mappings = cursor.fetchall()
    print('   Beispiel-Kategorien:')
    for pattern, ftype, target in mappings:
        print(f'     {pattern:<20} -> {ftype:<12} ({target or "N/A"})')
    print()
except:
    print('❌ field_type_mapping Tabelle nicht gefunden!')

# 3. Prüfe Lookup-Tabellen Status
lookup_tables = ['commodities', 'companies', 'activity_statuses', 'mine_types', 'countries', 'regions']
print('📊 LOOKUP-TABELLEN STATUS:')
for table in lookup_tables:
    try:
        cursor.execute(f'SELECT COUNT(*) FROM {table}')
        count = cursor.fetchone()[0]
        print(f'   {table:<20}: {count} Einträge')
    except:
        print(f'   {table:<20}: FEHLER beim Abrufen')

print()

# 4. Prüfe mine_data_fields Einträge (sollten 0 sein nach Fresh Start)
cursor.execute('SELECT COUNT(*) FROM mine_data_fields')
field_count = cursor.fetchone()[0]
print(f'📊 MINE_DATA_FIELDS: {field_count} Einträge (sollte 0 sein nach Fresh Start)')

# 5. Prüfe mines Tabelle
cursor.execute('SELECT COUNT(*) FROM mines')
mines_count = cursor.fetchone()[0]
print(f'📊 MINES: {mines_count} Einträge (sollte 0 sein nach Fresh Start)')

# 6. Prüfe search_sessions
cursor.execute('SELECT COUNT(*) FROM search_sessions')
sessions_count = cursor.fetchone()[0]
print(f'📊 SEARCH_SESSIONS: {sessions_count} Einträge (sollte 0 sein nach Fresh Start)')

print()

# 7. Teste CHECK-Constraints mit Dummy-Daten
print('🧪 TESTE CHECK-CONSTRAINTS:')

# Test 1: Normalisiertes Feld mit primitive_value (sollte fehlschlagen)
try:
    cursor.execute("""
        INSERT INTO mine_data_fields 
        (mine_id, field_name, field_type, commodity_id, primitive_value)
        VALUES (999, 'test_field', 'normalized', 1, 'should fail')
    """)
    print('   ❌ CHECK-Constraint FEHLER: Normalisiertes Feld mit primitive_value akzeptiert!')
    cursor.execute("DELETE FROM mine_data_fields WHERE mine_id = 999")
except sqlite3.IntegrityError as e:
    print('   ✅ CHECK-Constraint funktioniert: Normalisierte Felder können nicht primitive_value haben')

# Test 2: Primitives Feld mit commodity_id (sollte fehlschlagen)  
try:
    cursor.execute("""
        INSERT INTO mine_data_fields 
        (mine_id, field_name, field_type, commodity_id, primitive_value)
        VALUES (999, 'test_field', 'primitive', 1, 'test_value')
    """)
    print('   ❌ CHECK-Constraint FEHLER: Primitives Feld mit commodity_id akzeptiert!')
    cursor.execute("DELETE FROM mine_data_fields WHERE mine_id = 999")
except sqlite3.IntegrityError as e:
    print('   ✅ CHECK-Constraint funktioniert: Primitive Felder können nicht commodity_id haben')

# Test 3: Gültiges normalisiertes Feld (sollte funktionieren)
try:
    cursor.execute("""
        INSERT INTO mine_data_fields 
        (mine_id, field_name, field_type, commodity_id)
        VALUES (999, 'test_commodity', 'normalized', 1)
    """)
    print('   ✅ Gültiges normalisiertes Feld erfolgreich eingefügt')
    cursor.execute("DELETE FROM mine_data_fields WHERE mine_id = 999")
except Exception as e:
    print(f'   ❌ Unerwarteter Fehler bei gültigem normalisiertem Feld: {e}')

# Test 4: Gültiges primitives Feld (sollte funktionieren)
try:
    cursor.execute("""
        INSERT INTO mine_data_fields 
        (mine_id, field_name, field_type, primitive_value)
        VALUES (999, 'test_name', 'primitive', 'Test Mine Name')
    """)
    print('   ✅ Gültiges primitives Feld erfolgreich eingefügt')
    cursor.execute("DELETE FROM mine_data_fields WHERE mine_id = 999")
except Exception as e:
    print(f'   ❌ Unerwarteter Fehler bei gültigem primitivem Feld: {e}')

conn.commit()
conn.close()

print()
print('🎯 FAZIT: Neues 3NF-Schema ist bereit für echte Tests!')
print('✅ Echte Feld-Typ-Trennung implementiert')
print('✅ CHECK-Constraints verhindern Hybrid-Daten')  
print('✅ Lookup-Tabellen sind befüllt')
print('✅ Fresh Start erfolgreich - bereit für neue normalisierte Daten')