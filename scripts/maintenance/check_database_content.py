#!/usr/bin/env python
"""
Author: rahn
Datum: 23.08.2025
Version: 1.0
Beschreibung: Prüfe Datenbank-Inhalte für Statistik-Debug
"""

import sys
import os
from pathlib import Path
import importlib.util

def _ensure_backend_on_sys_path() -> None:
    # Bevor wir sys.path verändern, prüfen wir, ob das Paket bereits installiert/auffindbar ist
    if importlib.util.find_spec('minesearch') is not None:
        return

    backend_env = os.environ.get('BACKEND_PATH')
    candidate_paths = []

    if backend_env:
        env_path = Path(backend_env).expanduser().resolve()
        # Entweder zeigt BACKEND_PATH direkt auf den Backend-Ordner
        if (env_path / 'minesearch').is_dir():
            candidate_paths.append(env_path)
        # ...oder auf das Repo-Root und wir hängen 'backend' an
        elif (env_path / 'backend' / 'minesearch').is_dir():
            candidate_paths.append(env_path / 'backend')

    # Fallback: relativ zum aktuellen Skript nach /backend suchen
    start_dir = Path(__file__).resolve().parent
    if (start_dir / 'backend' / 'minesearch').is_dir():
        candidate_paths.append(start_dir / 'backend')
    else:
        for parent in start_dir.parents:
            candidate = parent / 'backend'
            if (candidate / 'minesearch').is_dir():
                candidate_paths.append(candidate)
                break

    for candidate in candidate_paths:
        candidate_str = str(candidate)
        if candidate.is_dir() and candidate_str not in sys.path:
            sys.path.append(candidate_str)
            break

_ensure_backend_on_sys_path()

from minesearch.database import db_manager
from sqlalchemy import text
import json

print('🔍 PRÜFE DATENBANK-INHALTE')
print('=' * 60)

with db_manager.get_session() as session:
    # 1. Prüfe search_results Tabelle mit korrekten Spalten
    print('\n📊 SEARCH_RESULTS TABELLE:')
    result = session.execute(text('''
        SELECT 
            id,
            mine_name,
            model_used,
            search_duration,
            structured_data,
            success,
            search_timestamp
        FROM search_results 
        ORDER BY search_timestamp DESC 
        LIMIT 3
    '''))
    
    for row in result:
        print(f'\n🔍 ID: {row[0]} | Mine: {row[1]}')
        print(f'📱 Model: {row[2]}')
        print(f'⏱️ Duration: {row[3]}ms')
        print(f'✅ Success: {row[5]}')
        
        # Parse structured_data
        if row[4]:
            try:
                data = json.loads(row[4]) if isinstance(row[4], str) else row[4]
                if isinstance(data, dict):
                    na_values = ['N/A', '', None, 'null']
                    filled_fields = len([v for v in data.values() if v and str(v) not in na_values])
                    total_fields = len(data)
                    print(f'📊 Structured Data: {filled_fields}/{total_fields} Felder gefüllt')
                    
                    # Zeige alle Felder mit Werten
                    filled = [(k,v) for k,v in data.items() if v and str(v) not in na_values]
                    print(f'🎯 Gefüllte Felder ({len(filled)}):')
                    for k,v in filled[:5]:  # Erste 5
                        value_str = str(v)
                        if len(value_str) > 60:
                            print(f'   • {k}: {value_str[:60]}...')
                        else:
                            print(f'   • {k}: {value_str}')
                    if len(filled) > 5:
                        print(f'   ... und {len(filled) - 5} weitere')
                else:
                    print(f'📊 Structured Data: Kein Dict-Format')
            except Exception as e:
                print(f'❌ Structured Data: Parse-Fehler - {e}')
        else:
            print(f'📊 Structured Data: NULL/Leer')
    
    # 2. Prüfe model_statistics_comprehensive Tabelle
    print('\n\n📊 MODEL_STATISTICS_COMPREHENSIVE TABELLE:')
    result = session.execute(text('''
        SELECT 
            model_id,
            total_searches,
            successful_searches,
            avg_fields_filled,
            completeness_score,
            consistency_score,
            overall_score
        FROM model_statistics_comprehensive
        WHERE model_id LIKE '%glm-4.5-air%'
        LIMIT 3
    '''))
    
    for row in result:
        print(f'\n📱 Model: {row[0]}')
        print(f'🔍 Total Searches: {row[1]} | Successful: {row[2]}')
        print(f'📊 Avg Fields Filled: {row[3]}')
        print(f'🎯 Completeness Score: {row[4]}')
        print(f'🔄 Consistency Score: {row[5]}')
        print(f'🏆 Overall Score: {row[6]}')
    
    # 3. Prüfe ob Aggregation funktioniert
    print('\n\n📊 AGGREGATION CHECK:')
    result = session.execute(text('''
        SELECT 
            model_used,
            COUNT(*) as count,
            AVG(search_duration) as avg_duration
        FROM search_results
        WHERE model_used LIKE '%glm-4.5-air%'
        GROUP BY model_used
    '''))
    
    for row in result:
        print(f'\n📱 Model: {row[0]}')
        print(f'🔍 Count: {row[1]}')
        if row[2] is not None:
            print(f'⏱️ Avg Duration: {row[2]:.2f}ms')
        else:
            print('Avg Duration: None')