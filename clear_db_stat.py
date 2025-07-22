#!/usr/bin/env python3
"""
Author: rahn
Datum: 19.07.2025
Version: 1.0
Beschreibung: Clear database statistics tables
"""

import sys
import os
sys.path.append('/app/minesearch_v2/backend')

from database import db_manager
from sqlalchemy import text

def clear_stat_tables():
    """Leere nur Statistik-Tabellen"""
    
    # Definiere Statistik-Tabellen
    STAT_TABLES = ['field_consistency', 'field_statistics', 'model_statistics', 'model_summary']
    
    session = db_manager.get_session()
    try:
        print('🧹 Leere Statistik-Tabellen')
        print('=' * 50)
        
        total_deleted = 0
        
        for table in STAT_TABLES:
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
        print(f'✅ Erfolgreich {total_deleted} Einträge aus {len(STAT_TABLES)} Statistik-Tabellen gelöscht')
        
        # Zeige verbleibende Tabellen
        try:
            sources_count = session.execute(text('SELECT COUNT(*) FROM sources')).scalar()
            print(f'ℹ️  Quellen-Tabelle bleibt bestehen: {sources_count} Einträge')
        except:
            print(f'ℹ️  Quellen-Tabelle nicht gefunden')
        
        try:
            results_count = session.execute(text('SELECT COUNT(*) FROM search_results')).scalar()
            print(f'ℹ️  Ergebnis-Tabellen nicht geleert: {results_count} Einträge in search_results')
        except:
            print(f'ℹ️  Ergebnis-Tabellen nicht gefunden')
        
        print('\n🎯 Statistik-Tabellen bereinigt!')
        return True
        
    except Exception as e:
        print(f'❌ Fehler beim Leeren der Statistik-Tabellen: {str(e)}')
        session.rollback()
        return False
        
    finally:
        session.close()

def main():
    print("🧪 Clear Database Statistics")
    print("=" * 40)
    
    success = clear_stat_tables()
    
    if success:
        print("\n✅ Statistik-Tabellen erfolgreich geleert!")
    else:
        print("\n❌ Fehler beim Leeren der Statistik-Tabellen")

if __name__ == "__main__":
    main()