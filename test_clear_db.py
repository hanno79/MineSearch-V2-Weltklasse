#!/usr/bin/env python3
"""
Test-Script für das clear_db Command
"""

import sys
import os
sys.path.append('/app/minesearch_v2/backend')

# CRITICAL FIX: Print debugging info to identify the issue
print('=== DEBUG INFO ===')
print('Raw arguments passed:', repr(''))
print('sys.argv:', sys.argv)
print('==================')

from database.manager import DatabaseManager
from sqlalchemy import text, inspect
import shutil
from datetime import datetime
import sqlite3

# FIXED: Handle template argument correctly
import sys
raw_args = ''

# DEBUG: Print all argument sources
print('=== ARGUMENT SOURCES ===')
print(f'Template args: {repr(raw_args)}')
print(f'sys.argv: {sys.argv}')
if len(sys.argv) > 1:
    print(f'sys.argv args: {sys.argv[1:]}')

# ROBUST: Use sys.argv as primary source, template as fallback
if len(sys.argv) > 1:
    # Direct Python execution - use sys.argv
    arg = ' '.join(sys.argv[1:]).strip().lower()
    print(f'Using sys.argv: {arg}')
elif raw_args != '{{args}}' and raw_args.strip():
    # Template replaced successfully
    arg = raw_args.strip().lower()
    print(f'Using template: {arg}')
else:
    # Template not replaced or empty - use default
    arg = 'all'
    print('Using default: all')

# Clean argument parsing validation (extra safety)
if not arg or arg in ['{{args}}', '']:
    # Template not replaced or invalid, default to 'all'  
    arg = 'all'
    print('Template not replaced or invalid, using default: all')

print(f'🧹 Leere Datenbank-Tabellen: {arg}')
print('=' * 50)

# Definiere Tabellen
STAT_TABLES = ['field_consistency', 'field_statistics', 'model_statistics', 'model_summary']
RESULT_TABLES = ['search_results', 'mines']

tables_to_clear = []
create_backup = False

if arg in ['backup']:
    # Special case: create backup and clear all
    create_backup = True
    tables_to_clear.extend(STAT_TABLES)
    tables_to_clear.extend(RESULT_TABLES)
    print('🔄 Backup-Modus aktiviert: Erstelle Backup vor dem Leeren')
elif arg in ['stat', 'all']:
    tables_to_clear.extend(STAT_TABLES)
    if arg == 'all':
        tables_to_clear.extend(RESULT_TABLES)
elif arg in ['result']:
    tables_to_clear.extend(RESULT_TABLES)
else:
    print(f'❌ Unbekanntes Argument: {arg}')
    print('Verwende: all, stat, result oder backup')
    exit(1)

print(f'📋 Zu leerende Tabellen: {tables_to_clear}')

db_manager = DatabaseManager()


# ENHANCED: Create backup if requested
if create_backup:
    try:
        backup_dir = '/app/minesearch_v2/backups'
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f'{backup_dir}/mines_backup_{timestamp}.db'
        
        # Copy database file for backup
        db_path = db_manager.database_url.replace('sqlite:///', '')
        if os.path.exists(db_path):
            shutil.copy2(db_path, backup_file)
            print(f'✅ Backup erstellt: {backup_file}')
        else:
            print(f'⚠️  Database file not found: {db_path}')
    except Exception as e:
        print(f'❌ Backup-Fehler: {e}')
        print('Fortfahren ohne Backup...')

try:
    total_deleted = 0
    
    # ENHANCED: Add connection verification
    print('🔍 Verifying database connection...')
    inspector = inspect(db_manager.engine)
    existing_tables = inspector.get_table_names()
    print(f'📋 Available tables: {existing_tables}')
    
    with db_manager.get_session() as session:
        # Verify tables exist before attempting deletion
        verified_tables = []
        for table in tables_to_clear:
            if table in existing_tables:
                verified_tables.append(table)
                print(f'✅ Table {table} exists')
            else:
                print(f'⚠️  Table {table} does not exist, skipping')
        
        print(f'🎯 Processing {len(verified_tables)} verified tables: {verified_tables}')
        
        for table in verified_tables:
            try:
                # Zähle Einträge vor Löschung
                count_result = session.execute(text(f'SELECT COUNT(*) FROM {table}'))
                count_before = count_result.scalar()
                
                print(f'📊 {table}: {count_before} entries before deletion')
                
                if count_before > 0:
                    # Lösche Einträge
                    delete_result = session.execute(text(f'DELETE FROM {table}'))
                    deleted = count_before  # SQLite doesn't return rowcount reliably
                    total_deleted += deleted
                    print(f'✅ {table}: {deleted} Einträge gelöscht')
                else:
                    print(f'ℹ️  {table}: bereits leer')
                    
            except Exception as e:
                print(f'❌ Fehler bei {table}: {str(e)}')
                import traceback
                print('Full traceback:')
                traceback.print_exc()
                continue
        
        # ENHANCED: Commit with verification
        print('💾 Committing changes...')
        session.commit()
        print('✅ Commit successful')
        
        # ENHANCED: Verify deletion was successful
        print('🔍 Verifying deletion results:')
        verification_passed = True
        for table in verified_tables:
            try:
                count_result = session.execute(text(f'SELECT COUNT(*) FROM {table}'))
                count_after = count_result.scalar()
                if count_after == 0:
                    print(f'✅ {table}: Successfully cleared (0 entries)')
                else:
                    print(f'⚠️  {table}: Still has {count_after} entries!')
                    verification_passed = False
            except Exception as e:
                print(f'❌ Verification error for {table}: {e}')
                verification_passed = False
        
        print('=' * 50)
        if verification_passed:
            print(f'✅ Erfolgreich {total_deleted} Einträge aus {len(verified_tables)} Tabellen gelöscht')
        else:
            print(f'⚠️  Deletion completed but some tables may still contain data')
        
        # Zeige verbleibende Tabellen (sources bleibt bestehen)
        try:
            sources_result = session.execute(text('SELECT COUNT(*) FROM sources'))
            sources_count = sources_result.scalar()
            print(f'ℹ️  Quellen-Tabelle bleibt bestehen: {sources_count} Einträge')
        except Exception as e:
            print(f'ℹ️  Quellen-Tabelle Status unbekannt: {e}')
        
        if verification_passed:
            print('🎯 Datenbank erfolgreich geleert und bereit für neue Tests!')
        else:
            print('⚠️  Datenbank-Clearing mit Warnungen abgeschlossen')
        
except Exception as e:
    print(f'❌ Fehler beim Leeren der Datenbank: {str(e)}')
    raise