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

def test_gui_database_path():
    """Testet den GUI-Datenbankpfad"""
    print("\n🖥️  GUI-DATENBANK TEST")
    print("-" * 40)
    
    gui_db = "/app/mines.db"
    
    if os.path.exists(gui_db):
        if os.path.islink(gui_db):
            target = os.readlink(gui_db)
            print(f"✅ GUI-DB (Symlink): {gui_db} → {target}")
            
            if os.path.exists(target):
                size_mb = os.path.getsize(target) / (1024 * 1024)
                print(f"✅ Ziel gefunden: {size_mb:.2f} MB")
                return target
            else:
                print(f"❌ Symlink-Ziel nicht gefunden: {target}")
                return None
        else:
            size_mb = os.path.getsize(gui_db) / (1024 * 1024)
            print(f"✅ GUI-DB (Datei): {size_mb:.2f} MB")
            return gui_db
    else:
        print(f"❌ GUI-DB nicht gefunden: {gui_db}")
        return None

def test_data_consistency():
    """Testet die Datenkonsistenz zwischen Backend und GUI"""
    print("\n📊 DATENKONSISTENZ TEST")
    print("-" * 40)
    
    try:
        import sqlite3
        
        backend_db = "/app/backend/minesearch/database/mines.db"
        gui_db = "/app/mines.db"
        
        # Backend count
        conn1 = sqlite3.connect(backend_db)
        cursor1 = conn1.cursor()
        cursor1.execute("SELECT COUNT(*) FROM search_results")
        backend_count = cursor1.fetchone()[0]
        conn1.close()
        
        # GUI count
        conn2 = sqlite3.connect(gui_db)
        cursor2 = conn2.cursor()
        cursor2.execute("SELECT COUNT(*) FROM search_results")
        gui_count = cursor2.fetchone()[0]
        conn2.close()
        
        print(f"📈 Backend Search Results: {backend_count}")
        print(f"📈 GUI Search Results: {gui_count}")
        
        if backend_count == gui_count:
            print("✅ Daten synchron: Backend ↔ GUI")
            return True
        else:
            print(f"❌ Daten-Inkonsistenz: {backend_count} ≠ {gui_count}")
            return False
            
    except Exception as e:
        print(f"❌ Konsistenz-Test fehlgeschlagen: {e}")
        return False

def main():
    print("🧪 SYSTEM-KONFIGURATION VERIFIKATION")
    print("=" * 50)
    print(f"Zeitstempel: {os.popen('date').read().strip()}")
    print()
    
    # Test 1: Backend-Konfiguration
    backend_db_path = test_backend_config()
    
    # Test 2: Datenbankverbindung  
    search_results_count = test_database_connection()
    
    # Test 3: GUI-Datenbank
    gui_db_path = test_gui_database_path()
    
    # Test 4: Datenkonsistenz
    consistency_ok = test_data_consistency()
    
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
    
    if gui_db_path:
        print("✅ GUI-Datenbank: OK")
        tests_passed += 1
    else:
        print("❌ GUI-Datenbank: FEHLER")
    
    if consistency_ok:
        print("✅ Datenkonsistenz: OK")
        tests_passed += 1
    else:
        print("❌ Datenkonsistenz: FEHLER")
    
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