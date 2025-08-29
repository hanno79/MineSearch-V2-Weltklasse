#!/usr/bin/env python3
"""
PRIMÄRE DATENBANK ANALYZER - DEPRECATED

ÄNDERUNG 28.08.2025: Konsolidierung abgeschlossen
Nur noch eine Datenbank aktiv: /app/backend/minesearch/database/mines.db

Author: rahn  
Datum: 20.08.2025
Version: 1.1 (deprecated)
"""

import os
import sqlite3
from datetime import datetime
from pathlib import Path

def analyze_search_results_content(db_path):
    """Analysiert den Inhalt der search_results Tabelle detailliert"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Basis-Statistiken
        cursor.execute("SELECT COUNT(*) FROM search_results")
        total_count = cursor.fetchone()[0]
        
        if total_count == 0:
            conn.close()
            return {
                'total_results': 0,
                'unique_mines': 0,
                'date_range': None,
                'providers': [],
                'models': [],
                'data_quality': 0
            }
        
        # Unique Minen
        cursor.execute("SELECT COUNT(DISTINCT mine_name) FROM search_results")
        unique_mines = cursor.fetchone()[0]
        
        # Datums-Range
        cursor.execute("SELECT MIN(created_at), MAX(created_at) FROM search_results")
        date_range = cursor.fetchone()
        
        # Provider-Verteilung (flexibles Schema)
        providers = []
        try:
            cursor.execute("SELECT DISTINCT provider FROM search_results WHERE provider IS NOT NULL")
            providers = [row[0] for row in cursor.fetchall()]
        except:
            try:
                cursor.execute("SELECT DISTINCT model_used FROM search_results WHERE model_used IS NOT NULL")
                providers = [row[0] for row in cursor.fetchall()]
            except:
                providers = []
        
        # Model-Verteilung (flexibles Schema)
        models = []
        try:
            cursor.execute("SELECT DISTINCT model FROM search_results WHERE model IS NOT NULL")
            models = [row[0] for row in cursor.fetchall()]
        except:
            try:
                cursor.execute("SELECT DISTINCT model_used FROM search_results WHERE model_used IS NOT NULL")
                models = [row[0] for row in cursor.fetchall()]
            except:
                models = []
        
        # Datenqualitäts-Score (flexibles Schema)
        try:
            cursor.execute("""
                SELECT 
                    COUNT(CASE WHEN mine_name IS NOT NULL AND mine_name != '' THEN 1 END) as has_name,
                    COUNT(CASE WHEN country IS NOT NULL AND country != '' THEN 1 END) as has_country,
                    COUNT(CASE WHEN structured_data IS NOT NULL AND structured_data != '{}' THEN 1 END) as has_data,
                    COUNT(*) as total
                FROM search_results
            """)
        except:
            # Fallback für andere Schemas
            cursor.execute("SELECT COUNT(*), COUNT(*), 0, COUNT(*) FROM search_results")
        quality_data = cursor.fetchone()
        
        if quality_data and quality_data[3] > 0:  # total > 0
            # Durchschnittliche Feldvollständigkeit (3 Hauptfelder für flexibles Schema)
            field_completeness = sum(quality_data[:3]) / (3 * quality_data[3]) * 100
        else:
            field_completeness = 0
        
        conn.close()
        
        return {
            'total_results': total_count,
            'unique_mines': unique_mines,
            'date_range': date_range,
            'providers': providers,
            'models': models,
            'data_quality': field_completeness
        }
        
    except Exception as e:
        print(f"❌ Fehler bei Analyse von {db_path}: {e}")
        return None

def analyze_sources_content(db_path):
    """Analysiert den Inhalt der sources Tabelle"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM sources")
        total_sources = cursor.fetchone()[0]
        
        if total_sources == 0:
            conn.close()
            return {'total_sources': 0, 'unique_domains': 0}
        
        # Unique Domains
        cursor.execute("SELECT COUNT(DISTINCT url) FROM sources WHERE url IS NOT NULL")
        unique_domains = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_sources': total_sources,
            'unique_domains': unique_domains
        }
        
    except Exception as e:
        return {'total_sources': 0, 'unique_domains': 0}

def calculate_database_score(db_info):
    """Berechnet einen Gesamt-Score für eine Datenbank"""
    score = 0
    
    # Basis-Score für Dateninhalt
    if db_info.get('search_results'):
        search_data = db_info['search_results']
        
        # Anzahl Ergebnisse (max 40 Punkte)
        result_score = min(search_data['total_results'] / 50, 1.0) * 40
        score += result_score
        
        # Einzigartige Minen (max 30 Punkte)
        mine_score = min(search_data['unique_mines'] / 20, 1.0) * 30
        score += mine_score
        
        # Datenqualität (max 20 Punkte)
        quality_score = (search_data['data_quality'] / 100) * 20
        score += quality_score
        
        # Provider-Diversität (max 10 Punkte)
        provider_score = min(len(search_data['providers']) / 3, 1.0) * 10
        score += provider_score
    
    # Malus für problematische Pfade
    if 'backup' in db_info['path'].lower():
        score *= 0.9  # 10% Malus für Backup-DBs
        
    if db_info['path'] == '/app/mines.db':
        score += 10  # Bonus für GUI-DB (Split-Brain Problem)
    
    return round(score, 1)

def main():
    print("🎯 PRIMÄRE DATENBANK IDENTIFIKATION")
    print("=" * 50)
    print(f"Zeitstempel: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Kandidaten aus der Backup-Analyse
    candidate_dbs = [
        '/app/backend/minesearch/database/mines_backup_pre_cleanup_20250819_070936.db',
        '/app/backend/minesearch/database/mines.db',
        '/app/mines.db'
    ]
    
    print("🔍 DETAILLIERTE KANDIDATEN-ANALYSE")
    print("-" * 40)
    
    db_analyses = []
    
    for db_path in candidate_dbs:
        print(f"\n📊 Analysiere: {db_path}")
        
        if not os.path.exists(db_path):
            print("   ❌ Datei nicht gefunden")
            continue
            
        size_mb = os.path.getsize(db_path) / (1024 * 1024)
        
        # Analyse search_results
        search_analysis = analyze_search_results_content(db_path)
        
        # Analyse sources  
        sources_analysis = analyze_sources_content(db_path)
        
        db_info = {
            'path': db_path,
            'size_mb': size_mb,
            'search_results': search_analysis,
            'sources': sources_analysis
        }
        
        # Score berechnen
        score = calculate_database_score(db_info)
        db_info['score'] = score
        
        db_analyses.append(db_info)
        
        print(f"   📏 Größe: {size_mb:.2f} MB")
        if search_analysis:
            print(f"   🔍 Search Results: {search_analysis['total_results']} total")
            print(f"   🏔️  Unique Minen: {search_analysis['unique_mines']}")
            print(f"   📈 Datenqualität: {search_analysis['data_quality']:.1f}%")
            print(f"   🛠️  Provider: {len(search_analysis['providers'])} ({', '.join(search_analysis['providers'][:3])})")
            if search_analysis['date_range'] and search_analysis['date_range'][0]:
                print(f"   📅 Zeitraum: {search_analysis['date_range'][0]} bis {search_analysis['date_range'][1]}")
        
        if sources_analysis:
            print(f"   🌐 Sources: {sources_analysis['total_sources']} total, {sources_analysis['unique_domains']} unique")
            
        print(f"   ⭐ Gesamt-Score: {score:.1f}/100")
    
    if not db_analyses:
        print("❌ Keine gültigen Kandidaten gefunden!")
        return
    
    # Sortiere nach Score
    db_analyses.sort(key=lambda x: x['score'], reverse=True)
    
    print("\n" + "=" * 50)
    print("🏆 RANKING & EMPFEHLUNG")
    print("=" * 50)
    
    for i, db in enumerate(db_analyses, 1):
        print(f"\n{i}. PLATZ - Score: {db['score']:.1f}/100")
        print(f"   📄 {db['path']}")
        print(f"   📊 {db['search_results']['total_results'] if db['search_results'] else 0} Ergebnisse, {db['size_mb']:.2f} MB")
        
        if i == 1:
            print("   🥇 EMPFOHLEN ALS PRIMÄRE DATENBANK")
            primary_db = db
    
    # Migration Plan
    print("\n" + "=" * 50)
    print("📋 MIGRATIONS-PLAN")
    print("=" * 50)
    
    if db_analyses:
        primary = db_analyses[0]
        
        print(f"🎯 PRIMÄRE DATENBANK: {primary['path']}")
        print(f"   • {primary['search_results']['total_results']} Ergebnisse behalten")
        print(f"   • {primary['sources']['total_sources']} Quellen behalten")
        print(f"   • Datenqualität: {primary['search_results']['data_quality']:.1f}%")
        
        # Migration von anderen DBs
        for other_db in db_analyses[1:]:
            if other_db['search_results'] and other_db['search_results']['total_results'] > 0:
                print(f"\n📦 MIGRATION VON: {other_db['path']}")
                print(f"   • {other_db['search_results']['total_results']} Ergebnisse zu migrieren")
                print(f"   • {other_db['sources']['total_sources']} Quellen zu migrieren")
                print("   • Duplikat-Check erforderlich")
        
        # Konfiguration Update
        print(f"\n⚙️  KONFIGURATION UPDATE:")
        print("   1. DATABASE_URL → sqlite:///" + primary['path'])
        print("   2. Backend connection.py → update path")
        print("   3. GUI config → update path")
        
        # Cleanup Plan
        print(f"\n🧹 CLEANUP NACH MIGRATION:")
        for db in db_analyses[1:]:
            print(f"   • {db['path']} → archivieren oder entfernen")
    
    print("\n💡 NÄCHSTE SCHRITTE:")
    print("1. ✅ Primäre DB identifiziert")
    print("2. 🔄 Datenmigration durchführen")
    print("3. ⚙️  System-Konfiguration anpassen")
    print("4. 🧪 Tests für einheitliche DB-Nutzung")
    print("5. 🧹 Verwaiste Datenbanken entfernen")
    
    return primary['path'] if db_analyses else None

if __name__ == "__main__":
    primary_db_path = main()
    if primary_db_path:
        print(f"\n🎉 PRIMÄRE DATENBANK IDENTIFIZIERT: {primary_db_path}")
    else:
        print(f"\n❌ PRIMÄRE DATENBANK KONNTE NICHT BESTIMMT WERDEN")