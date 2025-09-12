#!/usr/bin/env python3
"""
DATENBANK-KONSOLIDIERUNG ANALYSE
Analysiert alle Datenbanken im System zur Konsolidierung

Author: rahn
Datum: 20.08.2025
Version: 1.0
"""

import os
import sqlite3
import glob
from datetime import datetime

def analyze_database(db_path):
    """Analysiert eine einzelne Datenbank"""
    result = {
        'path': db_path,
        'size_bytes': 0,
        'size_human': '0B',
        'tables': {},
        'status': 'ERROR',
        'error': None
    }

    try:
        if not os.path.exists(db_path):
            result['status'] = 'NOT_FOUND'
            return result

        result['size_bytes'] = os.path.getsize(db_path)
        result['size_human'] = format_bytes(result['size_bytes'])

        if result['size_bytes'] == 0:
            result['status'] = 'EMPTY'
            return result

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Tabellen finden
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()

        for table in tables:
            table_name = table[0]
            try:
                cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
                count = cursor.fetchone()[0]
                result['tables'][table_name] = count
            except Exception as e:
                result['tables'][table_name] = f'ERROR: {e}'

        conn.close()
        result['status'] = 'ACTIVE' if result['tables'] else 'NO_TABLES'

    except Exception as e:
        result['error'] = str(e)
        result['status'] = 'ERROR'

    return result

def format_bytes(bytes_size):
    """Formatiert Bytes in menschenlesbare Form"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f}{unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f}TB"

def main():
    """main - TODO: Dokumentation hinzufügen"""
    print("🔍 DATENBANK-KONSOLIDIERUNG ANALYSE")
    print("=" * 50)
    print(f"Zeitstempel: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Finde alle .db Dateien (außer in to_delete)
    db_files = []
    for root, dirs, files in os.walk('/app'):
        # Skip to_delete Ordner
        if '/to_delete/' in root:
            continue
        for file in files:
            if file.endswith('.db'):
                db_files.append(os.path.join(root, file))

    db_files.sort()

    print(f"📊 GEFUNDENE DATENBANKEN: {len(db_files)}")
    print("-" * 40)

    analyses = []

    for db_file in db_files:
        print(f"\n🔍 Analysiere: {db_file}")
        analysis = analyze_database(db_file)
        analyses.append(analysis)

        print(f"   Status: {analysis['status']}")
        print(f"   Größe: {analysis['size_human']} ({analysis['size_bytes']} bytes)")

        if analysis['tables']:
            print("   Tabellen:")
            for table, count in analysis['tables'].items():
                print(f"     • {table}: {count}")
        elif analysis['status'] == 'EMPTY':
            print("   📝 Leere Datei")
        elif analysis['error']:
            print(f"   ❌ Fehler: {analysis['error']}")

    print("\n" + "=" * 50)
    print("📋 ZUSAMMENFASSUNG:")
    print("=" * 50)

    # Kategorisiere Datenbanken
    active_dbs = [a for a in analyses if a['status'] == 'ACTIVE']
    empty_dbs = [a for a in analyses if a['status'] == 'EMPTY']
    error_dbs = [a for a in analyses if a['status'] == 'ERROR']
    swarm_dbs = [a for a in analyses if '.swarm/' in a['path']]
    backup_dbs = [a for a in analyses if 'backup' in a['path'].lower()]

    print(f"✅ AKTIVE DATENBANKEN: {len(active_dbs)}")
    for db in active_dbs:
        total_records = sum(v for v in db['tables'].values() if isinstance(v, int))
        print(f"   📄 {db['path']} ({db['size_human']}, {total_records} records)")

    print(f"\n📁 BACKUP DATENBANKEN: {len(backup_dbs)}")
    for db in backup_dbs:
        print(f"   📄 {db['path']} ({db['size_human']})")

    print(f"\n🔧 SWARM DATENBANKEN: {len(swarm_dbs)}")
    for db in swarm_dbs:
        print(f"   📄 {db['path']} ({db['size_human']})")

    print(f"\n📝 LEERE DATENBANKEN: {len(empty_dbs)}")
    for db in empty_dbs:
        print(f"   📄 {db['path']}")

    if error_dbs:
        print(f"\n❌ FEHLERHAFTE DATENBANKEN: {len(error_dbs)}")
        for db in error_dbs:
            print(f"   📄 {db['path']} - {db['error']}")

    # Identifiziere Hauptkandidaten
    print("\n🎯 KONSOLIDIERUNG EMPFEHLUNG:")
    print("-" * 30)

    main_candidates = [db for db in active_dbs if 'search_results' in db['tables']]

    if main_candidates:
        # Sortiere nach Anzahl der search_results
        main_candidates.sort(key=lambda x: x['tables'].get('search_results', 0), reverse=True)

        print("🏆 HAUPTKANDIDATEN (mit search_results):")
        for i, db in enumerate(main_candidates, 1):
            search_results = db['tables'].get('search_results', 0)
            print(f"   {i}. {db['path']}")
            print(f"      • {search_results} search_results")
            print(f"      • {db['size_human']}")
            if i == 1:
                print("      ⭐ EMPFOHLEN als primäre DB")

    print(f"\n💡 NÄCHSTE SCHRITTE:")
    print("1. Backups aller aktiven DBs erstellen")
    print("2. Primäre DB wählen (größte mit search_results)")
    print("3. Daten konsolidieren")
    print("4. Konfiguration anpassen")
    print("5. Verwaiste DBs entfernen")

if __name__ == "__main__":
    main()
