#!/usr/bin/env python3
"""
Author: rahn
Datum: 07.09.2025
Version: 1.0
Beschreibung: Umbenennung von Feldnamen in der Datenbank und allen Abhängigkeiten

FELDNAMEN-UMBENENNUNG:
=====================
1. "Rohstoff" → "Rohstoff"
2. "Minentyp" → "Minentyp"

Dieses Skript:
- Benennt die Feldnamen in der Datenbank um
- Aktualisiert alle bestehenden Daten
- Stellt sicher, dass alle Constraints erhalten bleiben
"""

import sqlite3
import json
from datetime import datetime
import pandas as pd


def rename_database_fields():
    """Benennt die Feldnamen in der Datenbank um"""
    print("🔄 STARTE FELDNAMEN-UMBENENNUNG IN DATENBANK")
    print("=" * 60)

    conn = sqlite3.connect('mines.db')
    cursor = conn.cursor()

    try:
        # 1. Prüfe aktuelle field_values Einträge
        print("\n📊 Analysiere aktuelle Feldnamen...")
        cursor.execute("""
            SELECT DISTINCT field_name, COUNT(*) as count
            FROM field_values
            WHERE field_name IN (
                'Rohstoff',
                'Rohstoffabbau',
                'Minentyp',
                'Minentyp'
            )
            GROUP BY field_name
            ORDER BY field_name
        """)

        current_fields = cursor.fetchall()
        print("   Gefundene Felder:")
        for field, count in current_fields:
            print(f"   - '{field}': {count} Einträge")

        # 2. Backup erstellen
        print("\n💾 Erstelle Backup...")
        backup_df = pd.read_sql_query("""
            SELECT * FROM field_values
            WHERE field_name IN (
                'Rohstoff',
                'Rohstoffabbau',
                'Minentyp',
                'Minentyp'
            )
        """, conn)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f'field_rename_backup_{timestamp}.csv'
        backup_df.to_csv(backup_file, index=False)
        print(f"   ✅ Backup gespeichert: {backup_file}")

        # 3. Umbenennung durchführen
        print("\n🔧 Führe Umbenennungen durch...")

        # Rohstoffabbau → Rohstoff
        cursor.execute("""
            UPDATE field_values
            SET field_name = 'Rohstoff'
            WHERE field_name IN (
                'Rohstoff',
                'Rohstoffabbau'
            )
        """)
        rohstoff_updated = cursor.rowcount
        print(f"   ✅ 'Rohstoffabbau' → 'Rohstoff': {rohstoff_updated} Einträge aktualisiert")

        # Minentyp (vollständig) → Minentyp
        cursor.execute("""
            UPDATE field_values
            SET field_name = 'Minentyp'
            WHERE field_name = 'Minentyp'
        """)
        minentyp_updated = cursor.rowcount
        print(f"   ✅ 'Minentyp (...)' → 'Minentyp': {minentyp_updated} Einträge aktualisiert")

        # 4. Validierung
        print("\n🔍 Validiere Änderungen...")
        cursor.execute("""
            SELECT DISTINCT field_name, COUNT(*) as count
            FROM field_values
            WHERE field_name IN ('Rohstoff', 'Minentyp')
            GROUP BY field_name
            ORDER BY field_name
        """)

        new_fields = cursor.fetchall()
        print("   Neue Feldnamen:")
        for field, count in new_fields:
            print(f"   - '{field}': {count} Einträge")

        # 5. Prüfe auf Duplikate nach Umbenennung
        print("\n🔍 Prüfe auf mögliche Duplikate...")
        cursor.execute("""
            SELECT search_result_id, field_name, COUNT(*) as count
            FROM field_values
            WHERE field_name IN ('Rohstoff', 'Minentyp')
            GROUP BY search_result_id, field_name
            HAVING count > 1
        """)

        duplicates = cursor.fetchall()
        if duplicates:
            print(f"   ⚠️  {len(duplicates)} mögliche Duplikate gefunden")
            for result_id, field, count in duplicates[:5]:
                print(f"      SearchResult {result_id}, Feld '{field}': {count} Einträge")

            # Bereinige Duplikate
            print("\n   🧹 Bereinige Duplikate...")
            for result_id, field, _ in duplicates:
                # Behalte nur den ersten Eintrag
                cursor.execute("""
                    DELETE FROM field_values
                    WHERE id NOT IN (
                        SELECT MIN(id)
                        FROM field_values
                        WHERE search_result_id = ? AND field_name = ?
                    )
                    AND search_result_id = ? AND field_name = ?
                """, (result_id, field, result_id, field))

            print(f"   ✅ Duplikate bereinigt")
        else:
            print("   ✅ Keine Duplikate gefunden")

        # Commit
        conn.commit()
        print("\n✅ DATENBANK-ÄNDERUNGEN ERFOLGREICH COMMITTED")

        # 6. Statistik
        print("\n📈 ZUSAMMENFASSUNG:")
        print(f"   - Rohstoff-Felder aktualisiert: {rohstoff_updated}")
        print(f"   - Minentyp-Felder aktualisiert: {minentyp_updated}")
        print(f"   - Gesamt aktualisiert: {rohstoff_updated + minentyp_updated}")

        return True

    except Exception as e:
        conn.rollback()
        print(f"\n❌ FEHLER: {e}")
        return False

    finally:
        conn.close()


def update_python_configs():
    """Aktualisiert die Python-Konfigurationsdateien"""
    print("\n🔧 AKTUALISIERE PYTHON-KONFIGURATIONEN...")

    files_to_update = [
        {
            'path': '/home/hanno/projects/MineSearch/backend/minesearch/config/base.py',
            'replacements': [
                ('Rohstoffabbau', 'Rohstoff'),
                ('Minentyp', 'Minentyp')  # Bleibt gleich
            ]
        },
        {
            'path': '/home/hanno/projects/MineSearch/backend/minesearch/extraction_patterns.py',
            'replacements': [
                ('"Rohstoff"', '"Rohstoff"'),
                ('"Minentyp"', '"Minentyp"')
            ]
        },
        {
            'path': '/home/hanno/projects/MineSearch/backend/minesearch/extraction_validators.py',
            'replacements': [
                ("'Rohstoff'", "'Rohstoff'"),
                ("'Minentyp'", "'Minentyp'")
            ]
        }
    ]

    for file_info in files_to_update:
        try:
            with open(file_info['path'], 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content
            for old, new in file_info['replacements']:
                content = content.replace(old, new)

            if content != original_content:
                with open(file_info['path'], 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"   ✅ {file_info['path']} aktualisiert")
            else:
                print(f"   ℹ️  {file_info['path']} - keine Änderungen nötig")

        except Exception as e:
            print(f"   ❌ Fehler bei {file_info['path']}: {e}")


def generate_update_script():
    """Generiert ein Skript für alle weiteren Updates"""
    print("\n📝 GENERIERE UPDATE-SKRIPT FÜR ALLE DATEIEN...")

    update_script = '''#!/usr/bin/env python3
"""
Automatisch generiertes Update-Skript für Feldnamen-Umbenennung
Generiert: ''' + datetime.now().isoformat() + '''
"""

import os
import re

# Definiere alle Ersetzungen
REPLACEMENTS = [
    # Vollständige Namen
    (r'"Rohstoffabbau \\(Gold/ Kupfer/ Kohle/ usw\\.\\)"', '"Rohstoff"'),
    (r"'Rohstoffabbau \\(Gold/ Kupfer/ Kohle/ usw\\.\\)'", "'Rohstoff'"),
    (r'"Minentyp \\(Untertage/ Open-Pit/ usw\\.\\)"', '"Minentyp"'),
    (r"'Minentyp \\(Untertage/ Open-Pit/ usw\\.\\)'", "'Minentyp'"),

    # In Kommentaren und Strings
    (r'Rohstoffabbau \\(Gold/ Kupfer/ Kohle/ usw\\.\\)', 'Rohstoff'),
    (r'Minentyp \\(Untertage/ Open-Pit/ usw\\.\\)', 'Minentyp'),

    # Kurze Versionen (nur Rohstoffabbau → Rohstoff)
    (r'"Rohstoffabbau"', '"Rohstoff"'),
    (r"'Rohstoffabbau'", "'Rohstoff'"),
]

# Dateien die aktualisiert werden sollen
FILES_TO_UPDATE = [
    # Backend Python-Dateien
    'backend/minesearch/extraction_processors.py',
    'backend/minesearch/enhanced_extraction_patterns.py',
    'backend/minesearch/comprehensive_search_orchestrator.py',
    'backend/minesearch/multi_model_search_orchestrator.py',
    'backend/minesearch/sequential_field_orchestrator.py',
    'backend/minesearch/search_utils.py',
    'backend/minesearch/data_extraction.py',
    'backend/minesearch/api/routes/batch.py',
    'backend/minesearch/api/routes/consolidated_field_utils.py',
    'backend/minesearch/providers/base_provider.py',
    'backend/minesearch/unified_extraction_service.py',

    # Frontend-Dateien
    'frontend/display.js',
    'frontend/comparison-engine.js',
    'frontend/index.html',
]

def update_file(filepath):
    """Aktualisiert eine einzelne Datei"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        original = content
        for pattern, replacement in REPLACEMENTS:
            content = re.sub(pattern, replacement, content)

        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"Fehler bei {filepath}: {e}")
        return None

# Führe Updates durch
updated = 0
failed = 0
skipped = 0

for file in FILES_TO_UPDATE:
    filepath = f"/home/hanno/projects/MineSearch/{file}"
    if os.path.exists(filepath):
        result = update_file(filepath)
        if result is True:
            print(f"✅ {file}")
            updated += 1
        elif result is False:
            print(f"ℹ️  {file} - keine Änderungen")
            skipped += 1
        else:
            print(f"❌ {file} - Fehler")
            failed += 1
    else:
        print(f"⚠️  {file} - nicht gefunden")
        failed += 1

print(f"\\n📊 Zusammenfassung:")
print(f"   ✅ Aktualisiert: {updated}")
print(f"   ℹ️  Übersprungen: {skipped}")
print(f"   ❌ Fehler: {failed}")
'''

    with open('update_all_field_names.py', 'w', encoding='utf-8') as f:
        f.write(update_script)

    print("   ✅ Update-Skript erstellt: update_all_field_names.py")

    return True


def main():
    """Hauptfunktion für die Feldnamen-Umbenennung"""
    print("🔄 FELDNAMEN-UMBENENNUNG")
    print("=" * 60)
    print("Folgende Umbenennungen werden durchgeführt:")
    print('1. "Rohstoff" → "Rohstoff"')
    print('2. "Minentyp" → "Minentyp"')
    print()

    user_confirm = input("Umbenennung durchführen? (y/N): ").strip().lower()

    if user_confirm in ['y', 'yes']:
        # 1. Datenbank aktualisieren
        if rename_database_fields():
            print("\n✅ Datenbank erfolgreich aktualisiert")

            # 2. Python-Configs aktualisieren
            update_python_configs()

            # 3. Update-Skript generieren
            generate_update_script()

            print("\n🎉 FELDNAMEN-UMBENENNUNG ABGESCHLOSSEN!")
            print("\n📋 Nächste Schritte:")
            print("   1. Führe update_all_field_names.py aus")
            print("   2. Teste die Anwendung")
            print("   3. Committe alle Änderungen")

        else:
            print("\n❌ Umbenennung fehlgeschlagen")
    else:
        print("❌ Umbenennung abgebrochen")


if __name__ == "__main__":
    main()
