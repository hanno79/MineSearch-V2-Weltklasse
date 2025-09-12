#!/usr/bin/env python3
"""
Author: rahn
Datum: 11.09.2025
Version: 1.0
Beschreibung: Automatisches Umbenennen von Dateien mit verbotenen Namen
"""

import os
import shutil
from pathlib import Path

def rename_file(old_path, new_path):
    """Benennt eine Datei um"""
    try:
        if os.path.exists(old_path):
            shutil.move(old_path, new_path)
            print(f"✅ Umbenannt: {old_path} → {new_path}")
            return True
        else:
            print(f"⚠️  Datei nicht gefunden: {old_path}")
            return False
    except Exception as e:
        print(f"❌ Fehler bei {old_path}: {e}")
        return False

def main():
    """Hauptfunktion für Datei-Umbenennungen"""
    print("🔧 Starte Datei-Umbenennungen...")

    # Liste der Umbenennungen
    renames = [
        # "_fixed" Dateien
        ("tests/statistics_tab_fixed_validation.py", "tests/statistics_tab_validation.py"),
        ("tests/statistics_fixed_validation_results.json", "tests/statistics_tab_validation_results.json"),
        ("tests/statistics_fixed_validation.png", "tests/statistics_tab_validation.png"),

        # "_final" Dateien (nur produktive, nicht Dokumentation)
        ("simple_final_test.js", "simple_test.js"),
        ("csv_final_verification.js", "csv_verification.js"),

        # "_old" Dateien nach to_delete
        ("frontend/index_old_tab_version.html", "to_delete/index_old_tab_version.html"),
        ("frontend/index_old_massive.html", "to_delete/index_old_massive.html"),

        # "_backup" Dateien nach to_delete (nur produktive)
        ("frontend/index_backup_before_refactor.html", "to_delete/index_backup_before_refactor.html"),
        ("frontend/index_backup_before_phase4_cleanup.html", "to_delete/index_backup_before_phase4_cleanup.html"),
        ("frontend/index_backup_before_duplicate_cleanup.html", "to_delete/index_backup_before_duplicate_cleanup.html"),
        ("frontend/index_minimal_backup.html", "to_delete/index_minimal_backup.html"),
    ]

    # Erstelle to_delete Ordner falls nicht vorhanden
    os.makedirs("to_delete", exist_ok=True)

    success_count = 0
    for old_path, new_path in renames:
        if rename_file(old_path, new_path):
            success_count += 1

    print(f"\n🎯 Zusammenfassung:")
    print(f"   📁 Dateien umbenannt: {success_count}/{len(renames)}")
    print(f"   ✅ Erfolgreich: {success_count}")
    print(f"   ❌ Fehler: {len(renames) - success_count}")

if __name__ == "__main__":
    main()
