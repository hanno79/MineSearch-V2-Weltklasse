#!/usr/bin/env python3
"""
Author: rahn
Datum: 06.09.2025
Version: 1.0
Beschreibung: Prüft aktuelles Database-Schema und Count-Problem
"""

import sqlite3

def check_current_schema():
    """Prüft das aktuelle Database-Schema"""

    conn = sqlite3.connect('mines.db')
    cursor = conn.cursor()

    print("🔍 AKTUELLES DATABASE-SCHEMA ANALYSE")
    print("=" * 60)

    try:
        # 1. Alle Tabellen mit Counts
        print("1. ALLE TABELLEN MIT ROW-COUNTS:")
        cursor.execute("""
            SELECT name, type FROM sqlite_master
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        all_tables = cursor.fetchall()

        for table_name, table_type in all_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
                count = cursor.fetchone()[0]
                print(f"   📊 {table_name:<25}: {count} Einträge")
            except Exception as e:
                print(f"   ❌ {table_name:<25}: Fehler - {e}")

        print(f"\n📈 TOTAL: {len(all_tables)} Tabellen gefunden")

        # 2. Prüfe spezifisch die Lookup-Tabellen
        lookup_tables = ['countries', 'regions', 'commodities', 'companies', 'activity_statuses', 'mine_types']
        print(f"\n2. LOOKUP-TABELLEN STATUS:")

        for table in lookup_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
                count = cursor.fetchone()[0]

                # Zeige auch Beispiele
                if count > 0:
                    cursor.execute(f"SELECT * FROM `{table}` LIMIT 3")
                    examples = cursor.fetchall()
                    print(f"   ✅ {table:<20}: {count} Einträge")
                    for example in examples[:2]:  # Nur erste 2
                        print(f"     Beispiel: {example}")
                else:
                    print(f"   ⚠️  {table:<20}: {count} Einträge (LEER!)")
            except Exception as e:
                print(f"   ❌ {table:<20}: Tabelle nicht gefunden")

        # 3. Prüfe Hauptdatentabellen
        main_tables = ['mines', 'search_sessions', 'mine_data_fields']
        print(f"\n3. HAUPTDATEN-TABELLEN:")

        for table in main_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
                count = cursor.fetchone()[0]
                print(f"   📊 {table:<20}: {count} Einträge")

                if table == 'mine_data_fields' and count > 0:
                    # Analysiere field_type Verteilung
                    cursor.execute("""
                        SELECT field_type, COUNT(*)
                        FROM mine_data_fields
                        GROUP BY field_type
                    """)
                    field_types = cursor.fetchall()
                    print("     Field-Type Verteilung:")
                    for ft, cnt in field_types:
                        print(f"       {ft}: {cnt}")

            except Exception as e:
                print(f"   ❌ {table:<20}: Fehler - {e}")

        # 4. Teste API-Response Format
        print(f"\n4. SIMULIERE API-RESPONSE:")

        tables_for_api = []
        for table_name, table_type in all_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
                count = cursor.fetchone()[0]
                tables_for_api.append({
                    "name": table_name,
                    "type": table_type,
                    "row_count": count
                })
            except:
                tables_for_api.append({
                    "name": table_name,
                    "type": table_type,
                    "row_count": 0
                })

        print("   API würde folgende Counts zurückgeben:")
        for table_info in tables_for_api:
            name = table_info['name']
            count = table_info['row_count']
            print(f"     {name}: {count}")

        return tables_for_api

    except Exception as e:
        print(f"❌ Fehler bei Schema-Analyse: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    check_current_schema()
