---
description: "Leert MineSearch v2 Datenbank-Tabellen (stat/result/all)"
---

# MineSearch v2 Database Cleaner

Leert die Statistik- und/oder Ergebnis-Datenbank für einen frischen Start.

**Verwendung:**
- `/clear_db` oder `/clear_db all` - Leert alle Statistik- und Ergebnis-Tabellen
- `/clear_db stat` - Leert nur Statistik-Tabellen
- `/clear_db result` - Leert nur Ergebnis-Tabellen

**Quellen-Tabellen bleiben immer bestehen für bessere Performance.**

!python3 -c "
import sys
import os
sys.path.append('/app/minesearch_v2/backend')

from database.manager import DatabaseManager
from sqlalchemy import text

# Parse Arguments dynamisch
args = '''{{args}}'''
arg = args.strip().lower() if args.strip() else 'all'

print(f'🧹 Leere Datenbank-Tabellen: {arg}')
print('=' * 50)

# Definiere Tabellen
STAT_TABLES = ['field_consistency', 'field_statistics', 'model_statistics', 'model_summary']
RESULT_TABLES = ['search_results', 'mines']

tables_to_clear = []
if arg in ['stat', 'all']:
    tables_to_clear.extend(STAT_TABLES)
if arg in ['result', 'all']:
    tables_to_clear.extend(RESULT_TABLES)

if not tables_to_clear:
    print(f'❌ Unbekanntes Argument: {args}')
    print('Verwende: all, stat, oder result')
    exit(1)

db_manager = DatabaseManager()

try:
    total_deleted = 0
    
    with db_manager.get_session() as session:
        for table in tables_to_clear:
            try:
                # Zähle Einträge vor Löschung
                count_result = session.execute(text(f'SELECT COUNT(*) FROM {table}'))
                count_before = count_result.scalar()
                
                if count_before > 0:
                    # Lösche Einträge
                    session.execute(text(f'DELETE FROM {table}'))
                    deleted = count_before
                    total_deleted += deleted
                    print(f'✅ {table}: {deleted} Einträge gelöscht')
                else:
                    print(f'ℹ️  {table}: bereits leer')
                    
            except Exception as e:
                print(f'❌ Fehler bei {table}: {str(e)}')
                continue
        
        # Commit Änderungen
        session.commit()
        
        print('=' * 50)
        print(f'✅ Erfolgreich {total_deleted} Einträge aus {len(tables_to_clear)} Tabellen gelöscht')
        
        # Zeige verbleibende Tabellen
        try:
            sources_result = session.execute(text('SELECT COUNT(*) FROM sources'))
            sources_count = sources_result.scalar()
            print(f'ℹ️  Quellen-Tabelle bleibt bestehen: {sources_count} Einträge')
        except Exception as e:
            print(f'ℹ️  Quellen-Tabelle Fehler: {e}')
        
        print('🎯 Datenbank bereit für neue Tests!')
        
except Exception as e:
    print(f'❌ Fehler beim Leeren der Datenbank: {str(e)}')
    raise
"