#!/usr/bin/env python3
"""
KONFIGURATION VERIFIKATION TEST
Testet die einheitliche Datenbank-Konfiguration nach Konsolidierung

Author: rahn
Datum: 20.08.2025
Version: 1.0
"""

import os
import sys
from pathlib import Path

# Add backend to path
sys.path.append('/app/backend')

def test_backend_config():
    """Testet die Backend-Konfiguration"""
    print("⚙️  BACKEND-KONFIGURATION TEST")
    print("-" * 40)

    try:
        from minesearch.config.base import config

        print(f"✅ DATABASE_URL: {config.DATABASE_URL}")

        # Extrahiere DB-Pfad aus URL
        if config.DATABASE_URL.startswith('sqlite:///'):
            db_path = config.DATABASE_URL[10:]  # Remove 'sqlite:///'
            print(f"✅ Aufgelöster DB-Pfad: {db_path}")

            if os.path.exists(db_path):
                size_mb = os.path.getsize(db_path) / (1024 * 1024)
                print(f"✅ DB-Datei gefunden: {size_mb:.2f} MB")
                return db_path
            else:
                print(f"❌ DB-Datei nicht gefunden: {db_path}")
                return None
        else:
            print(f"⚠️  Nicht-SQLite URL: {config.DATABASE_URL}")
            return None

    except Exception as e:
        print(f"❌ Backend-Config Fehler: {e}")
        return None

def test_database_connection():
    """Testet die Datenbankverbindung"""
    print("\n🔌 DATENBANKVERBINDUNG TEST")
    print("-" * 40)

    try:
        # Direkte SQLite Verbindung für Test
        import sqlite3
        db_path = "/app/backend/minesearch/database/mines.db"

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM search_results")
        count = cursor.fetchone()[0]
        conn.close()

        print(f"✅ Datenbankverbindung: OK")
        print(f"✅ Search Results: {count}")
        return count

    except Exception as e:
        print(f"❌ Verbindungstest fehlgeschlagen: {e}")
        return None

def test_single_database_path():
    """ÄNDERUNG 28.08.2025: Testet dass nur noch eine Datenbank existiert"""
    print("\n🖥️  EINZELDATENBANK TEST")
    print("-" * 40)

    # Alte GUI-Datenbank sollte nicht mehr existieren
    old_gui_db = get_normalized_db_path()

    if os.path.exists(old_gui_db):
        print(f"⚠️ Alte GUI-Datenbank noch vorhanden: {old_gui_db}")
        print("⚠️ Diese sollte nach Konsolidierung entfernt werden!")
        return False
    else:
        print("✅ Konsolidierung erfolgreich: Nur noch eine Datenbank")

        # Prüfe aktive Datenbank
        active_db = "/app/backend/minesearch/database/mines.db"
        if os.path.exists(active_db):
            size_mb = os.path.getsize(active_db) / (1024 * 1024)
            print(f"✅ Aktive Datenbank: {active_db} ({size_mb:.2f} MB)")
            return True
        else:
            print(f"❌ Aktive Datenbank nicht gefunden: {active_db}")
            return False

def test_single_database_integrity():
    """ÄNDERUNG 28.08.2025: Testet die Integrität der einzigen Datenbank"""
    print("\n📊 DATENBANK-INTEGRITÄT TEST")
    print("-" * 40)

    try:
        import sqlite3
from minesearch.database.db_utils import get_normalized_db_path, get_sqlite_connection

        single_db = "/app/backend/minesearch/database/mines.db"

        # Datenbank-Integrität prüfen
        conn = sqlite3.connect(single_db)
        cursor = conn.cursor()

        # PRAGMA integrity_check
        cursor.execute("PRAGMA integrity_check")
        integrity_result = cursor.fetchone()[0]

        # Tabellen zählen
        cursor.execute("SELECT COUNT(*) FROM search_results")
        search_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM field_values")
        field_values_count = cursor.fetchone()[0]

        conn.close()

        print(f"📈 Search Results: {search_count}")
        print(f"📈 Field Values: {field_values_count}")

        if integrity_result == 'ok':
            print("✅ Datenbank-Integrität: OK")
            return True
        else:
            print(f"❌ Datenbank-Integrität: {integrity_result}")
            return False

    except Exception as e:
        print(f"❌ Integrität-Test fehlgeschlagen: {e}")
        return False

def main():
    """main - TODO: Dokumentation hinzufügen"""
    print("🧪 SYSTEM-KONFIGURATION VERIFIKATION")
    print("=" * 50)
    print(f"Zeitstempel: {os.popen('date').read().strip()}")
    print()

    # Test 1: Backend-Konfiguration
    backend_db_path = test_backend_config()

    # Test 2: Datenbankverbindung
    search_results_count = test_database_connection()

    # Test 3: Einzeldatenbank
    single_db_ok = test_single_database_path()

    # Test 4: Datenbank-Integrität
    integrity_ok = test_single_database_integrity()

    # Gesamtbewertung
    print("\n" + "=" * 50)
    print("📋 SYSTEM-STATUS ZUSAMMENFASSUNG")
    print("=" * 50)

    tests_passed = 0
    total_tests = 4

    if backend_db_path:
        print("✅ Backend-Konfiguration: OK")
        tests_passed += 1
    else:
        print("❌ Backend-Konfiguration: FEHLER")

    if search_results_count is not None:
        print(f"✅ Datenbankverbindung: OK ({search_results_count} Einträge)")
        tests_passed += 1
    else:
        print("❌ Datenbankverbindung: FEHLER")

    if single_db_ok:
        print("✅ Datenbank-Konsolidierung: OK")
        tests_passed += 1
    else:
        print("❌ Datenbank-Konsolidierung: FEHLER")

    if integrity_ok:
        print("✅ Datenbank-Integrität: OK")
        tests_passed += 1
    else:
        print("❌ Datenbank-Integrität: FEHLER")

    success_rate = (tests_passed / total_tests) * 100

    print()
    print(f"📊 ERFOLGSRATE: {tests_passed}/{total_tests} ({success_rate:.1f}%)")

    if tests_passed == total_tests:
        print("🎉 ALLE TESTS BESTANDEN - SYSTEM KONFIGURATION OK!")
        print("✅ Einheitliche Datenbank erfolgreich konfiguriert")
        print("✅ Split-Brain Problem gelöst")
        return True
    else:
        print(f"⚠️  {total_tests - tests_passed} TESTS FEHLGESCHLAGEN")
        print("🔧 Manuelle Überprüfung der Konfiguration erforderlich")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🚀 SYSTEM BEREIT FÜR PRODUKTIVEN EINSATZ!")
    else:
        print("\n❌ SYSTEM-KONFIGURATION UNVOLLSTÄNDIG")
