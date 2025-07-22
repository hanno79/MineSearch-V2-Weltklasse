#!/usr/bin/env python3
"""
Author: rahn
Datum: 19.07.2025
Version: 1.0
Beschreibung: Manueller Database Clear für Debugging
"""

import sys
import os
sys.path.append('/app/minesearch_v2/backend')

from database import db_manager
from sqlalchemy import text

def clear_database(arg='result'):
    """Leere Datenbank-Tabellen"""
    
    # Definiere Tabellen
    STAT_TABLES = ['field_consistency', 'field_statistics', 'model_statistics', 'model_summary']
    RESULT_TABLES = ['search_results', 'mines']
    
    session = db_manager.get_session()
    try:
        print(f'🧹 Leere Datenbank-Tabellen: {arg}')
        print('=' * 50)
        
        tables_to_clear = []
        if arg in ['stat', 'all']:
            tables_to_clear.extend(STAT_TABLES)
        if arg in ['result', 'all']:
            tables_to_clear.extend(RESULT_TABLES)
        
        print(f"Zu löschende Tabellen: {tables_to_clear}")
        
        total_deleted = 0
        
        for table in tables_to_clear:
            try:
                # Zähle Einträge vor Löschung
                count_before = session.execute(text(f'SELECT COUNT(*) FROM {table}')).scalar()
                print(f"Tabelle {table}: {count_before} Einträge vor Löschung")
                
                # Lösche Einträge
                result = session.execute(text(f'DELETE FROM {table}'))
                deleted = result.rowcount if hasattr(result, 'rowcount') else count_before
                
                total_deleted += deleted
                print(f'✅ {table}: {deleted} Einträge gelöscht')
                
            except Exception as e:
                print(f'❌ Fehler bei {table}: {str(e)}')
                continue
        
        # Commit Änderungen
        session.commit()
        print("💾 Änderungen committed")
        
        print('=' * 50)
        print(f'✅ Erfolgreich {total_deleted} Einträge aus {len(tables_to_clear)} Tabellen gelöscht')
        
        # Verify deletion
        print("\n🔍 Verifikation nach Löschung:")
        for table in tables_to_clear:
            try:
                count_after = session.execute(text(f'SELECT COUNT(*) FROM {table}')).scalar()
                print(f"  {table}: {count_after} Einträge verbleibend")
            except Exception as e:
                print(f"  {table}: Fehler bei Verifikation - {e}")
        
        # Zeige verbleibende Tabellen
        try:
            sources_count = session.execute(text('SELECT COUNT(*) FROM sources')).scalar()
            print(f'\nℹ️  Quellen-Tabelle bleibt bestehen: {sources_count} Einträge')
        except:
            print(f'\nℹ️  Quellen-Tabelle nicht gefunden oder leer')
        
        print('\n🎯 Datenbank-Bereinigung abgeschlossen!')
        return True
        
    except Exception as e:
        print(f'❌ Fehler beim Leeren der Datenbank: {str(e)}')
        session.rollback()
        return False
        
    finally:
        session.close()

def main():
    # Parse command line arguments
    if len(sys.argv) > 1:
        arg = sys.argv[1].strip().lower()
    else:
        arg = 'result'  # Default für /clear_db result
    
    # Validiere Argument
    if arg not in ['stat', 'result', 'all']:
        print(f'❌ Ungültiges Argument: {arg}')
        print('Erlaubte Argumente: stat, result, all')
        return
    
    success = clear_database(arg)
    
    if success:
        print(f"\n✅ Datenbank ({arg}) erfolgreich geleert!")
    else:
        print(f"\n❌ Fehler beim Leeren der Datenbank ({arg})")

if __name__ == "__main__":
    main()