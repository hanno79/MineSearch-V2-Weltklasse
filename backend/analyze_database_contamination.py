#!/usr/bin/env python3
"""
Author: rahn
Datum: 25.08.2025
Version: 1.1
Beschreibung: Analyse-Script für Datenbank-Kontamination (nur Lesen, keine Änderungen)

ANALYSE-TOOL 25.08.2025: Prüft die Feldkontamination ohne DB-Änderungen

Konfiguration:
- Dieses Skript liest den Datenbankpfad aus folgenden Quellen (in Prioritätsreihenfolge):
  1) Environment Variable "DATABASE_PATH"
  2) Environment Variable "MINES_DB_PATH" (Kompatibilität für Tests/CI)
  3) `minesearch.config.config.DATABASE_URL` (falls SQLite)
  4) Fallback: backend/minesearch/database/mines.db relativ zum Repo-Root

Der aufgelöste Pfad wird vor Nutzung validiert (existiert und ist eine Datei).
So kann der Pfad ohne Codeänderung via Environment/Config überschrieben werden.
"""

import os
import sys
import sqlite3
import json
import logging
from pathlib import Path
from urllib.parse import urlparse
from collections import defaultdict

# Logging konfigurieren
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Backend-Path hinzufügen
backend_path = Path(__file__).parent / "minesearch"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from field_name_blacklist import is_field_name_value


def _resolve_repo_root() -> Path:
    """Ermittelt den Repo-Root basierend auf dieser Datei."""
    backend_dir = Path(__file__).resolve().parent  # /app/backend
    return backend_dir.parent  # /app


def _resolve_database_path() -> str:
    """Liest den DB-Pfad aus ENV/Config mit robustem Fallback.

    Priorität:
    1) ENV DATABASE_PATH
    2) ENV MINES_DB_PATH (für Tests/CI)
    3) minesearch.config.config.DATABASE_URL (nur sqlite)
    4) Fallback: backend/minesearch/database/mines.db relativ zum Repo-Root
    """
    repo_root = _resolve_repo_root()

    # 1) & 2) Environment Variablen
    for env_var in ("DATABASE_PATH", "MINES_DB_PATH"):
        value = os.getenv(env_var, "").strip()
        if value:
            candidate = Path(value).expanduser()
            if not candidate.is_absolute():
                candidate = (repo_root / candidate).resolve()
            return str(candidate)

    # 3) Konfigurationsobjekt (nur wenn verfügbar)
    try:
        # minesearch liegt bereits im sys.path (siehe oben)
        from config import config  # type: ignore
    except Exception:
        config = None  # noqa: N806

    if config is not None:
        db_url = getattr(config, "DATABASE_URL", "")
        if isinstance(db_url, str) and db_url.startswith("sqlite"):
            parsed = urlparse(db_url)
            # Erwartete Form: sqlite:////abs/path/to/db.sqlite
            if parsed.path:
                return str(Path(parsed.path).resolve())

    # 4) Fallback
    fallback = (repo_root / "backend" / "minesearch" / "database" / "mines.db").resolve()
    return str(fallback)

def analyze_database_contamination():
    """
    ANALYSE-FUNKTION 25.08.2025: Analysiert Feldkontamination ohne DB-Änderungen
    """
    
    # Datenbank-Pfad ermitteln und validieren
    db_path = _resolve_database_path()
    db_path_obj = Path(db_path)
    if not (db_path_obj.exists() and db_path_obj.is_file()):
        print(f"❌ Datenbank nicht gefunden oder keine Datei: {db_path}")
        print("   Hinweis: Setze ENV 'DATABASE_PATH' oder 'MINES_DB_PATH' oder konfiguriere 'DATABASE_URL' (sqlite).")
        return
    
    print("🔍 DATENBANK-KONTAMINATIONS-ANALYSE")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect(str(db_path_obj))
        cursor = conn.cursor()
        
        # Tabellen-Info
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"📋 Gefundene Tabellen: {', '.join(tables)}")
        
        # Search_results Tabelle analysieren
        if 'search_results' not in tables:
            print("❌ search_results Tabelle nicht gefunden!")
            return
        
        # Schema der search_results Tabelle anzeigen
        cursor.execute("PRAGMA table_info(search_results)")
        columns = cursor.fetchall()
        print(f"\n📊 search_results Schema: {len(columns)} Spalten")
        for col in columns:
            print(f"   - {col[1]} ({col[2]})")
        
        # Gesamtanzahl Einträge
        cursor.execute("SELECT COUNT(*) FROM search_results")
        total_count = cursor.fetchone()[0]
        print(f"\n📈 Gesamte Einträge: {total_count}")
        
        # Einträge mit structured_data
        cursor.execute("SELECT COUNT(*) FROM search_results WHERE structured_data IS NOT NULL AND structured_data != ''")
        structured_count = cursor.fetchone()[0]
        print(f"📊 Einträge mit structured_data: {structured_count}")
        
        if structured_count == 0:
            print("ℹ️  Keine structured_data gefunden - möglicherweise andere Spalten-Struktur")
            
            # Prüfe andere mögliche Datenstrukturen
            cursor.execute("SELECT * FROM search_results LIMIT 1")
            sample = cursor.fetchone()
            if sample:
                print("🔍 Beispiel-Eintrag Struktur:")
                for i, col_info in enumerate(columns):
                    col_name = col_info[1]
                    col_value = sample[i] if i < len(sample) else "N/A"
                    print(f"   {col_name}: {str(col_value)[:100]}...")
        
        # HAUPTANALYSE: structured_data Kontamination
        if structured_count > 0:
            # Limit konfigurierbar (ENV ANALYZE_SAMPLE_LIMIT), Standard 100; <=0 bedeutet kein Limit
            sample_limit_env = os.getenv("ANALYZE_SAMPLE_LIMIT", "").strip()
            sample_limit = 100
            if sample_limit_env:
                try:
                    sample_limit = int(sample_limit_env)
                except ValueError:
                    print(f"⚠️  Ungültiger Wert in ENV ANALYZE_SAMPLE_LIMIT='{sample_limit_env}', verwende Standard 100.")
                    sample_limit = 100

            if sample_limit > 0:
                print(f"\n🔍 ANALYSIERE bis zu {sample_limit} STRUCTURED_DATA EINTRÄGE (insgesamt {structured_count})...")
                if structured_count > sample_limit:
                    print(f"Hinweis: Ausgabe auf {sample_limit} Einträge begrenzt, insgesamt {structured_count} Einträge gefunden")
                cursor.execute("""
                    SELECT id, mine_name, structured_data 
                    FROM search_results 
                    WHERE structured_data IS NOT NULL AND structured_data != ''
                    LIMIT ?
                """, (sample_limit,))
            else:
                print(f"\n🔍 ANALYSIERE ALLE {structured_count} STRUCTURED_DATA EINTRÄGE...")
                cursor.execute("""
                    SELECT id, mine_name, structured_data 
                    FROM search_results 
                    WHERE structured_data IS NOT NULL AND structured_data != ''
                """)

            sample_results = cursor.fetchall()
            
            contamination_stats = {
                'total_checked': 0,
                'field_name_contaminations': defaultdict(list),
                'null_issues': defaultdict(int),
                'problematic_entries': []
            }
            
            for entry_id, mine_name, structured_data_json in sample_results:
                try:
                    structured_data = json.loads(structured_data_json)
                    contamination_stats['total_checked'] += 1
                    
                    entry_issues = {}
                    
                    for field_name, field_value in structured_data.items():
                        if field_value and str(field_value).strip():
                            value_str = str(field_value).strip()
                            
                            # FELDNAMEN-CHECK
                            if is_field_name_value(value_str, field_name):
                                contamination_stats['field_name_contaminations'][field_name].append({
                                    'id': entry_id,
                                    'mine': mine_name,
                                    'value': value_str
                                })
                                entry_issues[field_name] = f"FELDNAME: {value_str}"
                            
                            # NULL-ISSUE CHECK
                            elif value_str in ['-', 'X', 'nicht gefunden', 'nichts gefunden']:
                                contamination_stats['null_issues'][field_name] += 1
                                if field_name not in entry_issues:
                                    entry_issues[field_name] = f"NULL-ISSUE: {value_str}"
                    
                    if entry_issues:
                        contamination_stats['problematic_entries'].append({
                            'id': entry_id,
                            'mine': mine_name,
                            'issues': entry_issues
                        })
                
                except json.JSONDecodeError:
                    print(f"⚠️  JSON-Parse-Fehler bei Entry {entry_id}")
                    continue
            
            # ERGEBNISSE ANZEIGEN
            print(f"\n📊 KONTAMINATIONS-ANALYSE ERGEBNISSE:")
            print(f"   Analysierte Einträge: {contamination_stats['total_checked']}")
            print(f"   Problematische Einträge: {len(contamination_stats['problematic_entries'])}")
            
            # Feldnamen-Kontaminationen
            if contamination_stats['field_name_contaminations']:
                print(f"\n🚨 FELDNAMEN-KONTAMINATIONEN ({len(contamination_stats['field_name_contaminations'])} Felder betroffen):")
                for field, contaminations in contamination_stats['field_name_contaminations'].items():
                    print(f"   🔴 Feld '{field}': {len(contaminations)} Kontaminationen")
                    for i, cont in enumerate(contaminations[:3]):  # Nur erste 3 anzeigen
                        print(f"      - Entry {cont['id']} ({cont['mine']}): '{cont['value']}'")
                    if len(contaminations) > 3:
                        print(f"      ... und {len(contaminations)-3} weitere")
            else:
                print("\n✅ KEINE FELDNAMEN-KONTAMINATIONEN gefunden")
            
            # NULL-Issues
            if contamination_stats['null_issues']:
                print(f"\n🔄 NULL-NORMALISIERUNG NÖTIG ({sum(contamination_stats['null_issues'].values())} Fälle):")
                for field, count in contamination_stats['null_issues'].items():
                    print(f"   - {field}: {count} Fälle")
            else:
                print("\n✅ KEINE NULL-NORMALISIERUNGEN nötig")
            
            # Detaillierte Probleme (erste 5)
            if contamination_stats['problematic_entries']:
                print(f"\n🔍 DETAILLIERTE PROBLEME (erste 5 von {len(contamination_stats['problematic_entries'])}):")
                for entry in contamination_stats['problematic_entries'][:5]:
                    print(f"   📝 Entry {entry['id']} ({entry['mine']}):")
                    for field, issue in entry['issues'].items():
                        print(f"      - {field}: {issue}")
        
        conn.close()
        print(f"\n✅ ANALYSE ABGESCHLOSSEN")
        
    except Exception as e:
        print(f"❌ FEHLER bei der Analyse: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_database_contamination()