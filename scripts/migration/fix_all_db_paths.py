#!/usr/bin/env python3
"""
Author: rahn
Datum: 04.09.2025
Version: 1.0
Beschreibung: Automatische Korrektur aller hardcodierten Datenbankpfade
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Tuple

# Mapping von hardcodierten Pfaden zu korrekten Lösungen
DB_PATH_FIXES = {
    # Alte hardcodierte Pfade
    "get_normalized_db_path()": "get_normalized_db_path()",
    'get_normalized_db_path()': "get_normalized_db_path()",
    "get_normalized_db_path()": "get_normalized_db_path()",
    'get_normalized_db_path()': "get_normalized_db_path()",
    "get_normalized_db_path()": "get_normalized_db_path()",
    'get_normalized_db_path()': "get_normalized_db_path()",

    # Sqlite3.connect Aufrufe
    "sqlite3.connect(get_normalized_db_path())": "get_sqlite_connection()",
    'sqlite3.connect(get_normalized_db_path())': "get_sqlite_connection()",
    "sqlite3.connect(get_normalized_db_path())": "get_sqlite_connection()",
    'sqlite3.connect(get_normalized_db_path())': "get_sqlite_connection()",
    "sqlite3.connect(get_normalized_db_path())": "get_sqlite_connection()",
    'sqlite3.connect(get_normalized_db_path())': "get_sqlite_connection()",

    # Alte relative Pfade
    "get_normalized_db_path()": "get_normalized_db_path()",
    'get_normalized_db_path()': "get_normalized_db_path()",
    "get_normalized_db_path()": "get_normalized_db_path()",
    'get_normalized_db_path()': "get_normalized_db_path()",

    # Legacy-Pfade in minesearch_v2
    "get_normalized_db_path()": "get_normalized_db_path()",
    'get_normalized_db_path()': "get_normalized_db_path()",
    "sqlite3.connect(get_normalized_db_path())": "get_sqlite_connection()",
    'sqlite3.connect(get_normalized_db_path())': "get_sqlite_connection()",
}

# Import-Statement das hinzugefügt werden soll
REQUIRED_IMPORT = "from minesearch.database.db_utils import get_normalized_db_path, get_sqlite_connection"

def needs_import_fix(file_path: Path, content: str) -> bool:
    """Prüft ob die Datei den Import benötigt"""
    return (
        ("get_normalized_db_path" in content or "get_sqlite_connection" in content) and
        "from minesearch.database.db_utils import" not in content and
        not file_path.name.endswith("db_utils.py")
    )

def add_import_statement(content: str) -> str:
    """Fügt Import-Statement am richtigen Ort hinzu"""
    lines = content.split('\n')

    # Finde die letzte Import-Zeile
    last_import_idx = -1
    for i, line in enumerate(lines):
        if line.strip().startswith(('import ', 'from ')) and not line.strip().startswith('#'):
            last_import_idx = i

    if last_import_idx >= 0:
        # Füge nach dem letzten Import hinzu
        lines.insert(last_import_idx + 1, REQUIRED_IMPORT)
    else:
        # Falls keine Imports gefunden, füge nach Docstring/Comments hinzu
        insert_idx = 0
        for i, line in enumerate(lines):
            if line.strip() and not line.strip().startswith('#') and not
line.strip().startswith('"""') and not line.strip().startswith("'''"):
                insert_idx = i
                break
        lines.insert(insert_idx, REQUIRED_IMPORT)
        lines.insert(insert_idx + 1, "")  # Leerzeile nach Import

    return '\n'.join(lines)

def fix_file_db_paths(file_path: Path) -> Tuple[bool, List[str]]:
    """Korrigiert alle DB-Pfade in einer Datei"""
    if not file_path.exists():
        return False, [f"Datei existiert nicht: {file_path}"]

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        changes_made = []

        # Ersetze alle hardcodierten Pfade
        for old_path, new_path in DB_PATH_FIXES.items():
            if old_path in content:
                content = content.replace(old_path, new_path)
                changes_made.append(f"  Ersetzt: {old_path} → {new_path}")

        # Füge Import hinzu falls nötig
        if needs_import_fix(file_path, content):
            content = add_import_statement(content)
            changes_made.append(f"  Import hinzugefügt: {REQUIRED_IMPORT}")

        # Schreibe nur zurück wenn Änderungen gemacht wurden
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, changes_made

        return False, []

    except Exception as e:
        return False, [f"Fehler bei {file_path}: {e}"]

def fix_all_db_paths():
    """Hauptfunktion - korrigiert alle DB-Pfade in der Codebase"""
    print("🔧 STARTE AUTOMATISCHE DB-PFAD-KORREKTUR")
    print("="*60)

    # Verzeichnisse die durchsucht werden sollen
    search_dirs = [
        Path("/app/backend"),
        Path("/app"),  # Für Root-Level Scripts
    ]

    # Dateierweiterungen die bearbeitet werden sollen
    file_extensions = [".py"]

    total_files_checked = 0
    total_files_changed = 0
    all_changes = []

    for search_dir in search_dirs:
        if not search_dir.exists():
            continue

        print(f"\n🔍 Durchsuche: {search_dir}")

        for file_path in search_dir.rglob("*.py"):
            # Überspringe bestimmte Verzeichnisse
            if any(part in str(file_path) for part in [
                ".venv", "venv", "__pycache__", ".git",
                "to_delete", "backup", "test-results"
            ]):
                continue

            total_files_checked += 1

            changed, changes = fix_file_db_paths(file_path)
            if changed:
                total_files_changed += 1
                rel_path = file_path.relative_to(Path("/app"))
                print(f"✅ {rel_path}")
                for change in changes:
                    print(change)
                all_changes.append((str(rel_path), changes))

    # Zusammenfassung
    print(f"\n" + "="*60)
    print(f"📊 ZUSAMMENFASSUNG:")
    print(f"   📁 Dateien geprüft: {total_files_checked}")
    print(f"   ✏️  Dateien geändert: {total_files_changed}")
    print(f"   🔧 Gesamt-Änderungen: {sum(len(changes) for _, changes in all_changes)}")

    if total_files_changed > 0:
        print(f"\n🎯 GEÄNDERTE DATEIEN:")
        for file_path, changes in all_changes:
            print(f"   📝 {file_path} ({len(changes)} Änderungen)")

    print(f"\n✅ DB-PFAD-KORREKTUR ABGESCHLOSSEN!")

if __name__ == "__main__":
    fix_all_db_paths()
