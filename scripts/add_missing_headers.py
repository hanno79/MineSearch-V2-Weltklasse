#!/usr/bin/env python3
"""
Author: rahn
Datum: 11.09.2025
Version: 1.0
Beschreibung: Automatisches Hinzufügen von Author-Headern zu Python-Dateien ohne Header
"""

import os
import glob
from pathlib import Path

def has_author_header(filepath):
    """Prüft ob eine Datei bereits einen Author-Header hat"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            first_20_lines = [f.readline().strip() for _ in range(20)]
            return any('Author:' in line for line in first_20_lines)
    except:
        return False

def add_header_to_file(filepath):
    """Fügt einen Author-Header zu einer Datei hinzu"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Generiere Beschreibung basierend auf Dateinamen
        filename = Path(filepath).stem
        description = generate_description(filename, filepath)

        header = f'''"""
Author: rahn
Datum: 11.09.2025
Version: 1.0
Beschreibung: {description}
"""

'''

        # Füge Header hinzu, falls noch nicht vorhanden
        if not content.startswith('"""'):
            new_content = header + content
        else:
            new_content = content

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print(f"✅ Header hinzugefügt: {filepath}")
        return True

    except Exception as e:
        print(f"❌ Fehler bei {filepath}: {e}")
        return False

def generate_description(filename, filepath):
    """Generiert eine Beschreibung basierend auf Dateinamen und Pfad"""
    path_parts = Path(filepath).parts

    if 'test' in filename.lower():
        return f"Test-Datei für {filename.replace('test_', '').replace('_test', '')}"
    elif 'migration' in filename.lower():
        return f"Migration-Script für {filename.replace('migration', '').replace('_', ' ')}"
    elif 'cleanup' in filename.lower():
        return f"Cleanup-Script für {filename.replace('cleanup', '').replace('_', ' ')}"
    elif 'provider' in path_parts:
        return f"Provider-Implementation für {filename.replace('_provider', '')}"
    elif 'api' in path_parts:
        return f"API-Route für {filename}"
    elif 'database' in path_parts:
        return f"Database-Management für {filename}"
    elif 'config' in path_parts:
        return f"Konfiguration für {filename}"
    else:
        return f"Funktionalität für {filename.replace('_', ' ')}"

def main():
    """Hauptfunktion"""
    print("🔍 Suche nach Python-Dateien ohne Author-Header...")

    # Finde alle Python-Dateien
    python_files = []
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                python_files.append(filepath)

    print(f"📊 Gefunden: {len(python_files)} Python-Dateien")

    # Prüfe welche Header fehlen
    missing_headers = []
    for filepath in python_files:
        if not has_author_header(filepath):
            missing_headers.append(filepath)

    print(f"⚠️  Fehlende Header: {len(missing_headers)} Dateien")

    if not missing_headers:
        print("✅ Alle Dateien haben bereits Author-Header!")
        return

    # Füge Header hinzu
    success_count = 0
    for filepath in missing_headers:
        if add_header_to_file(filepath):
            success_count += 1

    print(f"\n🎯 Zusammenfassung:")
    print(f"   📁 Dateien verarbeitet: {success_count}/{len(missing_headers)}")
    print(f"   ✅ Erfolgreich: {success_count}")
    print(f"   ❌ Fehler: {len(missing_headers) - success_count}")

if __name__ == "__main__":
    main()
