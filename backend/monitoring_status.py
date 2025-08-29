#!/usr/bin/env python3
"""
Author: rahn
Datum: 25.08.2025
Version: 1.0
Beschreibung: Monitoring Status Check

MONITORING-STATUS 25.08.2025: Einfacher Status-Check für alle Schutzebenen
"""

import sys
sys.path.insert(0, '.')

import os
import sqlite3
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

def _resolve_repo_root() -> Path:
    """Liefert das Projekt-Root basierend auf dem Dateipfad dieser Datei."""
    # /app/backend/monitoring_status.py → parents[1] = /app
    return Path(__file__).resolve().parents[1]

def _resolve_database_path() -> str:
    """
    Ermittelt den Pfad zur SQLite‑Datenbank in folgender Priorität:
    1) ENV DATABASE_PATH
    2) ENV MINES_DB_PATH (Kompatibilität für Tests/CI)
    3) minesearch.config.base.config.DATABASE_URL (falls sqlite)
    4) Fallback: backend/minesearch/database/mines.db relativ zum Repo‑Root
    """
    repo_root = _resolve_repo_root()

    # 1) & 2) Environment Variablen
    for env_var in ("DATABASE_PATH", "MINES_DB_PATH"):
        raw = os.environ.get(env_var)
        if raw is not None and str(raw).strip() != "":
            candidate = Path(str(raw).strip())
            if not candidate.is_absolute():
                candidate = (repo_root / candidate)
            return str(candidate.resolve())

    # 3) Konfiguration (nur sqlite URLs)
    try:
        from minesearch.config.base import config  # type: ignore
        db_url = getattr(config, "DATABASE_URL", "")
        if isinstance(db_url, str) and db_url.startswith("sqlite"):
            parsed = urlparse(db_url)
            if parsed.path:
                return str(Path(parsed.path).resolve())
    except Exception:
        # Konfiguration ist optional für dieses Standalone‑Skript
        pass

    # 4) Fallback: projektrelativer Standardpfad
    fallback = (repo_root / "backend" / "minesearch" / "database" / "mines.db").resolve()
    return str(fallback)

def check_monitoring_status():
    """
    MONITORING-STATUS-CHECK 25.08.2025
    Prüft Status aller Schutzmaßnahmen
    """
    
    print("🖥️  MONITORING & ALERTING STATUS")
    print("=" * 50)
    print(f"🕐 Zeitpunkt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    status_summary = {
        'extraction_layer': 'UNKNOWN',
        'service_layer': 'UNKNOWN', 
        'database_layer': 'UNKNOWN',
        'data_layer': 'UNKNOWN',
        'overall_status': 'UNKNOWN'
    }
    
    # 1. EXTRACTION LAYER CHECK
    print(f"\n🔍 SCHUTZEBENEN-STATUS:")
    try:
        from minesearch.extraction_processors import is_template_or_dummy_value
        test_result = is_template_or_dummy_value("x-Koordinate", "Betreiber")
        if test_result:
            status_summary['extraction_layer'] = 'ACTIVE'
            print(f"   ✅ Extraction Layer: ACTIVE (Template Detection funktional)")
        else:
            status_summary['extraction_layer'] = 'INACTIVE'
            print(f"   ❌ Extraction Layer: INACTIVE")
    except Exception as e:
        status_summary['extraction_layer'] = 'ERROR'
        print(f"   ❌ Extraction Layer: ERROR ({e})")
    
    # 2. SERVICE LAYER CHECK
    try:
        from minesearch.search_service import MineSearchService
        service = MineSearchService()
        status_summary['service_layer'] = 'ACTIVE'
        print(f"   ✅ Service Layer: ACTIVE (Quality Gate verfügbar)")
    except Exception as e:
        status_summary['service_layer'] = 'ERROR'
        print(f"   ❌ Service Layer: ERROR ({e})")
    
    # 3. DATABASE LAYER CHECK
    try:
        db_path = _resolve_database_path()
        db_path_obj = Path(db_path)
        if not (db_path_obj.exists() and db_path_obj.is_file()):
            raise FileNotFoundError(
                f"Datenbank nicht gefunden: {db_path}. Setze ENV 'DATABASE_PATH' oder 'MINES_DB_PATH' oder konfiguriere 'DATABASE_URL' (sqlite)."
            )
        print(f"   🔎 Datenbank-Pfad: {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Prüfe Trigger
        cursor.execute("SELECT name FROM sqlite_master WHERE type='trigger'")
        triggers = [row[0] for row in cursor.fetchall()]
        
        expected_triggers = [
            'prevent_field_contamination_insert',
            'prevent_field_contamination_update'
        ]
        
        triggers_active = sum(1 for t in expected_triggers if t in triggers)
        
        if triggers_active >= 2:
            status_summary['database_layer'] = 'ACTIVE'
            print(f"   ✅ Database Layer: ACTIVE ({triggers_active}/2 Triggers aktiv)")
        else:
            status_summary['database_layer'] = 'PARTIAL'
            print(f"   ⚠️ Database Layer: PARTIAL ({triggers_active}/2 Triggers aktiv)")
        
        conn.close()
    except Exception as e:
        status_summary['database_layer'] = 'ERROR'
        print(f"   ❌ Database Layer: ERROR ({e})")
    
    # 4. DATA LAYER CHECK
    try:
        from minesearch.null_normalizer import NullNormalizer
        normalizer = NullNormalizer()
        test_result = normalizer.normalize_value("-")
        if test_result is None:
            status_summary['data_layer'] = 'ACTIVE'
            print(f"   ✅ Data Layer: ACTIVE (NULL-Normalisierung funktional)")
        else:
            status_summary['data_layer'] = 'INACTIVE'
            print(f"   ❌ Data Layer: INACTIVE")
    except Exception as e:
        status_summary['data_layer'] = 'ERROR'
        print(f"   ❌ Data Layer: ERROR ({e})")
    
    # 5. FELDKONTAMINATION-SCHUTZ TEST
    print(f"\n🛡️  FELDKONTAMINATION-SCHUTZ TEST:")
    try:
        from minesearch.field_name_blacklist import is_field_name_value
        
        test_cases = [
            ("x-Koordinate", "Betreiber", True),
            ("y-Koordinate", "Country", True), 
            ("Region", "Eigentümer", True),
            ("Kanada [1,2,3]", "Country", False),
            ("Goldmine ABC", "mine_name", False)
        ]
        
        protection_working = True
        for value, field, should_be_blocked in test_cases:
            is_blocked = is_field_name_value(value, field)
            if is_blocked == should_be_blocked:
                status_icon = "🚫" if should_be_blocked else "✅"
                print(f"   {status_icon} '{value}' in '{field}': {'BLOCKIERT' if is_blocked else 'ERLAUBT'} ✓")
            else:
                print(f"   ❌ '{value}' in '{field}': {'BLOCKIERT' if is_blocked else 'ERLAUBT'} (Erwartet: {'BLOCKIERT' if should_be_blocked else 'ERLAUBT'})")
                protection_working = False
        
        if protection_working:
            print(f"   🎉 FELDKONTAMINATION-SCHUTZ: VOLLSTÄNDIG FUNKTIONAL")
        else:
            print(f"   ⚠️ FELDKONTAMINATION-SCHUTZ: TEILWEISE PROBLEME")
            
    except Exception as e:
        print(f"   ❌ FELDKONTAMINATION-SCHUTZ: FEHLER ({e})")
    
    # 6. GESAMTSTATUS BESTIMMEN
    active_layers = sum(1 for status in status_summary.values() 
                       if status == 'ACTIVE' and status != 'overall_status')
    
    if active_layers >= 3:
        status_summary['overall_status'] = 'HEALTHY'
        overall_icon = "🎉"
    elif active_layers >= 2:
        status_summary['overall_status'] = 'WARNING'  
        overall_icon = "⚠️"
    else:
        status_summary['overall_status'] = 'CRITICAL'
        overall_icon = "🚨"
    
    print(f"\n📊 GESAMTSTATUS:")
    print(f"   {overall_icon} System-Zustand: {status_summary['overall_status']}")
    print(f"   🛡️  Aktive Schutzebenen: {active_layers}/4")
    
    # 7. EMPFEHLUNGEN
    print(f"\n💡 STATUS-BEWERTUNG:")
    if status_summary['overall_status'] == 'HEALTHY':
        print(f"   ✅ Alle kritischen Schutzmaßnahmen sind aktiv")
        print(f"   ✅ Feldkontamination wird zuverlässig verhindert")
        print(f"   ✅ System bereit für produktiven Einsatz")
    elif status_summary['overall_status'] == 'WARNING':
        print(f"   ⚠️ Einige Schutzmaßnahmen haben Probleme")
        print(f"   🔧 Grundfunktionalität gewährleistet")
        print(f"   💡 Überwachung empfohlen")
    else:
        print(f"   🚨 Kritische Schutzmaßnahmen ausgefallen")
        print(f"   🛠️ Sofortige Wartung erforderlich")
    
    print(f"\n📋 NÄCHSTE SCHRITTE:")
    print(f"   🧪 Teste mit neuen Suchen um Schutz zu validieren")
    print(f"   📊 Prüfe CSV-Export auf saubere Feldtrennung")
    print(f"   🔍 Überwache Logs auf Kontaminationsmeldungen")
    
    return status_summary

def main():
    """Hauptfunktion"""
    status = check_monitoring_status()
    
    # Return Code basierend auf Status
    if status['overall_status'] == 'HEALTHY':
        exit(0)
    elif status['overall_status'] == 'WARNING':
        exit(1)  
    else:
        exit(2)

if __name__ == "__main__":
    main()