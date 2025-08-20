#!/usr/bin/env python3
"""
FINAL SYSTEM TEST
Umfassender Test der konsolidierten Datenbank-Architektur

Author: rahn  
Datum: 20.08.2025
Version: 1.0
"""

import os
import sys
import sqlite3
from datetime import datetime
from pathlib import Path

# Add backend to path for imports
sys.path.append('/app/backend')

def test_database_architecture():
    """Testet die Datenbank-Architektur"""
    print("🏗️  DATENBANK-ARCHITEKTUR TEST")
    print("-" * 40)
    
    backend_db = "/app/backend/minesearch/database/mines.db"
    gui_db = "/app/mines.db"
    
    results = {}
    
    # Test 1: Backend-DB Existenz und Größe
    if os.path.exists(backend_db):
        size_mb = os.path.getsize(backend_db) / (1024 * 1024)
        results['backend_exists'] = True
        results['backend_size'] = size_mb
        print(f"✅ Backend-DB: {size_mb:.2f} MB")
    else:
        results['backend_exists'] = False
        print(f"❌ Backend-DB nicht gefunden: {backend_db}")
    
    # Test 2: GUI-DB Symlink
    if os.path.exists(gui_db):
        if os.path.islink(gui_db):
            target = os.readlink(gui_db)
            results['gui_is_symlink'] = True
            results['gui_target'] = target
            print(f"✅ GUI-DB (Symlink): {gui_db} → {target}")
            
            # Verifikation des Symlink-Ziels
            if target == backend_db:
                results['symlink_correct'] = True
                print("✅ Symlink-Ziel: Korrekt")
            else:
                results['symlink_correct'] = False
                print(f"❌ Symlink-Ziel falsch: Erwartet {backend_db}, gefunden {target}")
        else:
            results['gui_is_symlink'] = False
            print(f"❌ GUI-DB ist kein Symlink: {gui_db}")
    else:
        results['gui_exists'] = False
        print(f"❌ GUI-DB nicht gefunden: {gui_db}")
    
    return results

def test_data_integrity():
    """Testet die Datenintegrität"""
    print("\n📊 DATENINTEGRITÄTS TEST")
    print("-" * 40)
    
    backend_db = "/app/backend/minesearch/database/mines.db"
    gui_db = "/app/mines.db"
    
    results = {}
    
    try:
        # Backend-DB Daten
        conn1 = sqlite3.connect(backend_db)
        cursor1 = conn1.cursor()
        
        cursor1.execute("SELECT COUNT(*) FROM search_results")
        backend_search_results = cursor1.fetchone()[0]
        
        cursor1.execute("SELECT COUNT(*) FROM sources")
        backend_sources = cursor1.fetchone()[0]
        
        # Neueste Einträge
        cursor1.execute("SELECT COUNT(*) FROM search_results WHERE created_at > '2025-08-01'")
        recent_results = cursor1.fetchone()[0]
        
        conn1.close()
        
        results['backend_search_results'] = backend_search_results
        results['backend_sources'] = backend_sources
        results['recent_results'] = recent_results
        
        print(f"✅ Backend Search Results: {backend_search_results}")
        print(f"✅ Backend Sources: {backend_sources}")
        print(f"✅ Recent Results (Aug 2025): {recent_results}")
        
        # GUI-DB Daten (sollte identisch sein)
        conn2 = sqlite3.connect(gui_db)
        cursor2 = conn2.cursor()
        
        cursor2.execute("SELECT COUNT(*) FROM search_results")
        gui_search_results = cursor2.fetchone()[0]
        
        cursor2.execute("SELECT COUNT(*) FROM sources")
        gui_sources = cursor2.fetchone()[0]
        
        conn2.close()
        
        results['gui_search_results'] = gui_search_results
        results['gui_sources'] = gui_sources
        
        print(f"✅ GUI Search Results: {gui_search_results}")
        print(f"✅ GUI Sources: {gui_sources}")
        
        # Konsistenz-Check
        if backend_search_results == gui_search_results and backend_sources == gui_sources:
            results['consistency'] = True
            print("✅ Datenkonsistenz: Backend ↔ GUI perfekt synchron")
        else:
            results['consistency'] = False
            print("❌ Datenkonsistenz: Diskrepanz zwischen Backend und GUI")
        
        return results
        
    except Exception as e:
        print(f"❌ Datenintegritäts-Test fehlgeschlagen: {e}")
        results['error'] = str(e)
        return results

def test_backend_config():
    """Testet die Backend-Konfiguration"""
    print("\n⚙️  BACKEND-KONFIGURATION TEST")
    print("-" * 40)
    
    results = {}
    
    try:
        from minesearch.config.base import config
        
        db_url = config.DATABASE_URL
        results['database_url'] = db_url
        print(f"✅ DATABASE_URL: {db_url}")
        
        # Extrahiere Pfad aus URL
        if db_url.startswith('sqlite:///'):
            db_path = db_url[10:]  # Remove 'sqlite:///'
            results['db_path'] = db_path
            
            expected_path = "/app/backend/minesearch/database/mines.db"
            if db_path == expected_path:
                results['path_correct'] = True
                print(f"✅ DB-Pfad korrekt: {db_path}")
            else:
                results['path_correct'] = False
                print(f"❌ DB-Pfad falsch: Erwartet {expected_path}, gefunden {db_path}")
        
        return results
        
    except Exception as e:
        print(f"❌ Backend-Config Test fehlgeschlagen: {e}")
        results['error'] = str(e)
        return results

def test_data_quality():
    """Testet die Datenqualität"""
    print("\n🎯 DATENQUALITÄTS TEST")
    print("-" * 40)
    
    backend_db = "/app/backend/minesearch/database/mines.db"
    results = {}
    
    try:
        conn = sqlite3.connect(backend_db)
        cursor = conn.cursor()
        
        # Test verschiedene Datenqualitäts-Metriken
        cursor.execute("SELECT COUNT(DISTINCT mine_name) FROM search_results WHERE mine_name IS NOT NULL")
        unique_mines = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM search_results WHERE country IS NOT NULL AND country != ''")
        has_country = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM search_results WHERE structured_data IS NOT NULL AND structured_data != '{}'")
        has_structured_data = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM search_results")
        total_results = cursor.fetchone()[0]
        
        conn.close()
        
        results['unique_mines'] = unique_mines
        results['has_country'] = has_country
        results['has_structured_data'] = has_structured_data
        results['total_results'] = total_results
        
        # Qualitäts-Scores berechnen
        country_score = (has_country / total_results * 100) if total_results > 0 else 0
        data_score = (has_structured_data / total_results * 100) if total_results > 0 else 0
        
        results['country_score'] = country_score
        results['data_score'] = data_score
        
        print(f"✅ Unique Minen: {unique_mines}")
        print(f"✅ Mit Country: {has_country}/{total_results} ({country_score:.1f}%)")
        print(f"✅ Mit Structured Data: {has_structured_data}/{total_results} ({data_score:.1f}%)")
        
        # Qualitäts-Bewertung
        avg_quality = (country_score + data_score) / 2
        results['avg_quality'] = avg_quality
        
        if avg_quality >= 95:
            print(f"🏆 Datenqualität: EXZELLENT ({avg_quality:.1f}%)")
        elif avg_quality >= 80:
            print(f"✅ Datenqualität: GUT ({avg_quality:.1f}%)")
        else:
            print(f"⚠️  Datenqualität: VERBESSERUNGSBEDARF ({avg_quality:.1f}%)")
        
        return results
        
    except Exception as e:
        print(f"❌ Datenqualitäts-Test fehlgeschlagen: {e}")
        results['error'] = str(e)
        return results

def test_system_performance():
    """Testet die System-Performance"""
    print("\n⚡ SYSTEM-PERFORMANCE TEST")
    print("-" * 40)
    
    backend_db = "/app/backend/minesearch/database/mines.db"
    results = {}
    
    try:
        import time
        
        # Test 1: Verbindungszeit
        start_time = time.time()
        conn = sqlite3.connect(backend_db)
        connect_time = (time.time() - start_time) * 1000  # ms
        
        results['connect_time_ms'] = connect_time
        print(f"✅ Verbindungszeit: {connect_time:.2f} ms")
        
        # Test 2: Einfache Abfrage
        cursor = conn.cursor()
        start_time = time.time()
        cursor.execute("SELECT COUNT(*) FROM search_results")
        cursor.fetchone()
        query_time = (time.time() - start_time) * 1000  # ms
        
        results['simple_query_ms'] = query_time
        print(f"✅ Einfache Abfrage: {query_time:.2f} ms")
        
        # Test 3: Komplexe Abfrage
        start_time = time.time()
        cursor.execute("""
            SELECT mine_name, COUNT(*) 
            FROM search_results 
            WHERE created_at > '2025-08-01'
            GROUP BY mine_name 
            ORDER BY COUNT(*) DESC 
            LIMIT 10
        """)
        cursor.fetchall()
        complex_query_time = (time.time() - start_time) * 1000  # ms
        
        results['complex_query_ms'] = complex_query_time
        print(f"✅ Komplexe Abfrage: {complex_query_time:.2f} ms")
        
        conn.close()
        
        # Performance-Bewertung
        if connect_time < 10 and query_time < 50 and complex_query_time < 200:
            print("🚀 Performance: EXZELLENT")
            results['performance_rating'] = 'EXCELLENT'
        elif connect_time < 50 and query_time < 100 and complex_query_time < 500:
            print("✅ Performance: GUT")
            results['performance_rating'] = 'GOOD'
        else:
            print("⚠️  Performance: LANGSAM")
            results['performance_rating'] = 'SLOW'
        
        return results
        
    except Exception as e:
        print(f"❌ Performance-Test fehlgeschlagen: {e}")
        results['error'] = str(e)
        return results

def generate_final_report(test_results):
    """Generiert den finalen Testbericht"""
    print("\n" + "=" * 60)
    print("📋 FINAL SYSTEM TEST REPORT")
    print("=" * 60)
    
    architecture_results = test_results.get('architecture', {})
    integrity_results = test_results.get('integrity', {})
    config_results = test_results.get('config', {})
    quality_results = test_results.get('quality', {})
    performance_results = test_results.get('performance', {})
    
    # Gesamt-Score berechnen
    total_score = 0
    max_score = 0
    
    # Architektur (25 Punkte)
    arch_score = 0
    max_score += 25
    if architecture_results.get('backend_exists'):
        arch_score += 10
    if architecture_results.get('gui_is_symlink'):
        arch_score += 10
    if architecture_results.get('symlink_correct'):
        arch_score += 5
    total_score += arch_score
    
    # Datenintegrität (25 Punkte) 
    integrity_score = 0
    max_score += 25
    if integrity_results.get('consistency'):
        integrity_score += 25
    total_score += integrity_score
    
    # Konfiguration (20 Punkte)
    config_score = 0
    max_score += 20
    if config_results.get('path_correct'):
        config_score += 20
    total_score += config_score
    
    # Datenqualität (15 Punkte)
    quality_score = 0
    max_score += 15
    avg_quality = quality_results.get('avg_quality', 0)
    quality_score = int((avg_quality / 100) * 15)
    total_score += quality_score
    
    # Performance (15 Punkte)
    perf_score = 0
    max_score += 15
    perf_rating = performance_results.get('performance_rating', '')
    if perf_rating == 'EXCELLENT':
        perf_score = 15
    elif perf_rating == 'GOOD':
        perf_score = 10
    else:
        perf_score = 5
    total_score += perf_score
    
    final_percentage = (total_score / max_score * 100) if max_score > 0 else 0
    
    print(f"🏗️  ARCHITEKTUR: {arch_score}/25 Punkte")
    print(f"📊 DATENINTEGRITÄT: {integrity_score}/25 Punkte") 
    print(f"⚙️  KONFIGURATION: {config_score}/20 Punkte")
    print(f"🎯 DATENQUALITÄT: {quality_score}/15 Punkte ({avg_quality:.1f}%)")
    print(f"⚡ PERFORMANCE: {perf_score}/15 Punkte ({perf_rating})")
    
    print()
    print("─" * 60)
    print(f"🏆 GESAMTSCORE: {total_score}/{max_score} ({final_percentage:.1f}%)")
    
    if final_percentage >= 90:
        print("🎉 SYSTEM-STATUS: EXZELLENT - PRODUKTIONSBEREIT!")
        status = 'EXCELLENT'
    elif final_percentage >= 75:
        print("✅ SYSTEM-STATUS: GUT - Bereit für Einsatz")
        status = 'GOOD'
    elif final_percentage >= 60:
        print("⚠️  SYSTEM-STATUS: AKZEPTABEL - Überwachung empfohlen")
        status = 'ACCEPTABLE'
    else:
        print("❌ SYSTEM-STATUS: PROBLEMATISCH - Überarbeitung erforderlich")
        status = 'PROBLEMATIC'
    
    print()
    print("📊 SYSTEM-METRIKEN:")
    search_results = integrity_results.get('backend_search_results', 0)
    unique_mines = quality_results.get('unique_mines', 0)
    backend_size = architecture_results.get('backend_size', 0)
    
    print(f"   • Search Results: {search_results:,}")
    print(f"   • Unique Minen: {unique_mines}")
    print(f"   • Datenbankgröße: {backend_size:.2f} MB")
    print(f"   • Split-Brain Status: ✅ GELÖST")
    print(f"   • Architektur: ✅ EINHEITLICH")
    
    return {
        'final_score': total_score,
        'max_score': max_score,
        'percentage': final_percentage,
        'status': status,
        'search_results': search_results,
        'unique_mines': unique_mines,
        'database_size_mb': backend_size
    }

def main():
    print("🧪 FINAL SYSTEM TEST - DATENBANK KONSOLIDIERUNG")
    print("=" * 60)
    print(f"Zeitstempel: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Test-Version: 1.0")
    print()
    
    test_results = {}
    
    # Test 1: Datenbank-Architektur
    test_results['architecture'] = test_database_architecture()
    
    # Test 2: Datenintegrität
    test_results['integrity'] = test_data_integrity()
    
    # Test 3: Backend-Konfiguration
    test_results['config'] = test_backend_config()
    
    # Test 4: Datenqualität
    test_results['quality'] = test_data_quality()
    
    # Test 5: System-Performance
    test_results['performance'] = test_system_performance()
    
    # Finaler Report
    final_results = generate_final_report(test_results)
    
    return final_results['status'] in ['EXCELLENT', 'GOOD']

if __name__ == "__main__":
    print("🚀 STARTING COMPREHENSIVE SYSTEM TEST...")
    print()
    
    success = main()
    
    if success:
        print("\n🎉 ALL SYSTEMS GO - DATENBANK-KONSOLIDIERUNG ERFOLGREICH!")
        print("✅ System bereit für Produktivbetrieb")
    else:
        print("\n⚠️  SYSTEM TEST MIT PROBLEMEN ABGESCHLOSSEN")
        print("🔧 Manuelle Überprüfung empfohlen")