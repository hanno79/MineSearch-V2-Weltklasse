#!/usr/bin/env python3
"""
Author: rahn
Datum: 14.07.2025
Version: 1.0
Beschreibung: Prüft, ob Tests ausgeführt wurden und wo die Ergebnisse gespeichert sind
"""

import os
import sqlite3
import json
from datetime import datetime
from pathlib import Path

def check_test_execution():
    """Prüft alle möglichen Speicherorte für Testergebnisse"""
    
    print("="*60)
    print("PRÜFUNG DER TEST-AUSFÜHRUNG")
    print("="*60)
    
    # 1. Prüfe Dateisystem nach Test-Outputs
    print("\n1. DATEISYSTEM-PRÜFUNG:")
    search_patterns = [
        "*deepseek*", "*cipher*", "*cypher*", "*openrouter*", "*test*result*"
    ]
    
    for pattern in search_patterns:
        print(f"\n  Pattern: {pattern}")
        files = list(Path("/app/minesearch_v2/backend").glob(pattern))
        for file in files[:5]:  # Limit to first 5 results
            if file.is_file():
                print(f"    {file} - {file.stat().st_mtime}")
    
    # 2. Prüfe alle Log-Dateien
    print("\n2. LOG-DATEIEN-PRÜFUNG:")
    log_dir = Path("/app/minesearch_v2/backend/logs")
    if log_dir.exists():
        log_files = list(log_dir.glob("*.log"))
        for log_file in log_files:
            print(f"  {log_file.name} - {datetime.fromtimestamp(log_file.stat().st_mtime)}")
            
            # Prüfe letzten Log auf deepseek/cipher
            try:
                with open(log_file, 'r') as f:
                    content = f.read()
                    if 'deepseek-chat' in content or 'cipher-alpha' in content or 'cypher-alpha' in content:
                        print(f"    -> Enthält deepseek-chat/cipher-alpha Referenzen")
            except:
                pass
    
    # 3. Prüfe Dokumentation
    print("\n3. DOKUMENTATIONS-PRÜFUNG:")
    doc_dir = Path("/app/minesearch_v2/backend/documentation")
    if doc_dir.exists():
        doc_files = list(doc_dir.glob("*.md"))
        for doc_file in doc_files:
            if any(keyword in doc_file.name.lower() for keyword in ['openrouter', 'deepseek', 'cipher', 'cypher']):
                print(f"  {doc_file.name} - {datetime.fromtimestamp(doc_file.stat().st_mtime)}")
    
    # 4. Prüfe temporäre Dateien
    print("\n4. TEMPORÄRE DATEIEN:")
    temp_patterns = ["*.json", "*.csv", "*.tmp"]
    for pattern in temp_patterns:
        files = list(Path("/app/minesearch_v2/backend").glob(pattern))
        for file in files[:3]:
            if file.is_file() and file.stat().st_size > 0:
                print(f"  {file.name} - {file.stat().st_size} bytes")
    
    # 5. Prüfe JSON-Dateien nach Testergebnissen
    print("\n5. JSON-DATEIEN-PRÜFUNG:")
    json_files = list(Path("/app/minesearch_v2/backend").glob("*.json"))
    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
                if isinstance(data, dict) and any(key in str(data) for key in ['deepseek', 'cipher', 'cypher', 'openrouter']):
                    print(f"  {json_file.name} - Enthält OpenRouter/DeepSeek/Cipher Daten")
        except:
            pass
    
    # 6. Prüfe Cache-Dateien
    print("\n6. CACHE-PRÜFUNG:")
    cache_dirs = ["/tmp", "/var/tmp", "/app/minesearch_v2/backend/cache"]
    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            try:
                files = os.listdir(cache_dir)
                relevant_files = [f for f in files if any(keyword in f.lower() for keyword in ['deepseek', 'cipher', 'cypher', 'openrouter'])]
                if relevant_files:
                    print(f"  {cache_dir}: {len(relevant_files)} relevante Dateien")
                    for file in relevant_files[:3]:
                        print(f"    - {file}")
            except:
                pass
    
    # 7. Prüfe Prozess-Historie
    print("\n7. PROZESS-HISTORIE:")
    try:
        # Prüfe ob Test-Skripte kürzlich ausgeführt wurden
        test_scripts = [
            "run_openrouter_complete_tests.py",
            "complete_remaining_openrouter_tests.py",
            "provider_test_framework.py"
        ]
        
        for script in test_scripts:
            script_path = Path(f"/app/minesearch_v2/backend/{script}")
            if script_path.exists():
                mtime = datetime.fromtimestamp(script_path.stat().st_mtime)
                print(f"  {script} - Letzte Änderung: {mtime}")
    except:
        pass
    
    # 8. Prüfe Datenbankverbindung
    print("\n8. DATENBANKVERBINDUNG-TEST:")
    try:
        # Import des DatabaseManagers
        import sys
        sys.path.append("/app/minesearch_v2/backend")
        from database import db_manager
        
        session = db_manager.get_session()
        print("  ✅ Datenbankverbindung erfolgreich")
        
        # Prüfe ob Tabellen korrekt erstellt wurden
        from database.models import ModelStatistics, SearchResult
        
        # Test-Query
        stats_count = session.query(ModelStatistics).count()
        results_count = session.query(SearchResult).count()
        
        print(f"  ModelStatistics: {stats_count} Einträge")
        print(f"  SearchResult: {results_count} Einträge")
        
        session.close()
        
    except Exception as e:
        print(f"  ❌ Datenbankfehler: {e}")
    
    print("\n" + "="*60)
    print("ZUSAMMENFASSUNG:")
    print("- Datenbank ist leer - keine Suchergebnisse gespeichert")
    print("- Tests wurden möglicherweise nicht vollständig ausgeführt")
    print("- Oder Tests liefen, aber Ergebnisse wurden nicht in DB gespeichert")
    print("="*60)

if __name__ == "__main__":
    check_test_execution()