"""
Author: rahn
Datum: 09.07.2025
Version: 1.0
Beschreibung: Bereinigung der Statistik- und Ergebnis-Datenbanken für sauberen Neustart
"""

import sys
from database import db_manager, ModelStatistics, FieldConsistency, ModelSummary, FieldStatistics, SearchResult, Source
from sqlalchemy import func

def show_current_stats():
    """Zeige aktuelle Statistiken vor dem Löschen"""
    with db_manager.get_session() as session:
        # Zähle Einträge in jeder Tabelle
        model_stats_count = session.query(func.count(ModelStatistics.id)).scalar()
        field_consistency_count = session.query(func.count(FieldConsistency.id)).scalar()
        model_summary_count = session.query(func.count(ModelSummary.model_id)).scalar()
        field_stats_count = session.query(func.count(FieldStatistics.id)).scalar()
        search_results_count = session.query(func.count(SearchResult.id)).scalar()
        sources_count = session.query(func.count(Source.id)).scalar()
        
        print("\n=== AKTUELLE DATENBANK-STATISTIKEN ===")
        print(f"\nStatistik-Tabellen:")
        print(f"  - model_statistics: {model_stats_count} Einträge")
        print(f"  - field_consistency: {field_consistency_count} Einträge")
        print(f"  - model_summary: {model_summary_count} Einträge")
        print(f"  - field_statistics: {field_stats_count} Einträge")
        print(f"\nErgebnis-Tabellen:")
        print(f"  - search_results: {search_results_count} Einträge")
        print(f"\nQuellen-Tabellen (WIRD BEHALTEN):")
        print(f"  - sources: {sources_count} Einträge")
        
        total_to_delete = (model_stats_count + field_consistency_count + 
                          model_summary_count + field_stats_count + search_results_count)
        
        print(f"\n=> {total_to_delete} Einträge werden gelöscht")
        print(f"=> {sources_count} Quellen bleiben erhalten")
        
        return total_to_delete

def cleanup_statistics():
    """Lösche alle Statistik- und Ergebnis-Daten"""
    with db_manager.get_session() as session:
        try:
            # Lösche Statistik-Tabellen
            deleted_model_stats = session.query(ModelStatistics).delete()
            print(f"✓ {deleted_model_stats} Einträge aus model_statistics gelöscht")
            
            deleted_field_consistency = session.query(FieldConsistency).delete()
            print(f"✓ {deleted_field_consistency} Einträge aus field_consistency gelöscht")
            
            deleted_model_summary = session.query(ModelSummary).delete()
            print(f"✓ {deleted_model_summary} Einträge aus model_summary gelöscht")
            
            deleted_field_stats = session.query(FieldStatistics).delete()
            print(f"✓ {deleted_field_stats} Einträge aus field_statistics gelöscht")
            
            # Lösche Ergebnis-Tabellen
            deleted_search_results = session.query(SearchResult).delete()
            print(f"✓ {deleted_search_results} Einträge aus search_results gelöscht")
            
            # Commit der Änderungen
            session.commit()
            
            print("\n✅ Alle Statistik- und Ergebnis-Daten wurden erfolgreich gelöscht!")
            
            # Zeige verbleibende Quellen
            sources_count = session.query(func.count(Source.id)).scalar()
            print(f"\n📊 {sources_count} Quellen sind weiterhin in der Datenbank vorhanden")
            
        except Exception as e:
            session.rollback()
            print(f"\n❌ Fehler beim Löschen: {str(e)}")
            raise

def verify_cleanup():
    """Verifiziere dass alle Tabellen leer sind"""
    with db_manager.get_session() as session:
        errors = []
        
        if session.query(ModelStatistics).count() > 0:
            errors.append("model_statistics ist nicht leer!")
        if session.query(FieldConsistency).count() > 0:
            errors.append("field_consistency ist nicht leer!")
        if session.query(ModelSummary).count() > 0:
            errors.append("model_summary ist nicht leer!")
        if session.query(FieldStatistics).count() > 0:
            errors.append("field_statistics ist nicht leer!")
        if session.query(SearchResult).count() > 0:
            errors.append("search_results ist nicht leer!")
            
        if errors:
            print("\n❌ Verifizierung fehlgeschlagen:")
            for error in errors:
                print(f"  - {error}")
            return False
        else:
            print("\n✅ Verifizierung erfolgreich: Alle Statistik- und Ergebnis-Tabellen sind leer")
            return True

def main():
    """Hauptfunktion"""
    print("=== MINESEARCH v2 - STATISTIK-BEREINIGUNG ===")
    print("\nDieses Skript löscht alle Statistik- und Ergebnis-Daten.")
    print("Die Quellen-Datenbank bleibt unverändert.")
    
    # Zeige aktuelle Statistiken
    total_to_delete = show_current_stats()
    
    if total_to_delete == 0:
        print("\n✓ Keine Daten zum Löschen vorhanden.")
        return
    
    # Bestätigung - im Skript-Modus automatisch fortfahren
    print("\n⚠️  WARNUNG: Diese Aktion kann nicht rückgängig gemacht werden!")
    
    # Prüfe ob wir im interaktiven Modus sind
    import os
    if os.environ.get('CLEANUP_CONFIRM', 'no').lower() == 'yes':
        print("\n✓ Automatische Bestätigung durch CLEANUP_CONFIRM=yes")
    else:
        print("\n❌ Abgebrochen. Setze CLEANUP_CONFIRM=yes um fortzufahren.")
        return
    
    print("\n🔄 Lösche Daten...")
    cleanup_statistics()
    
    print("\n🔍 Verifiziere...")
    verify_cleanup()
    
    print("\n✨ Bereinigung abgeschlossen! Die Datenbank ist bereit für neue Tests.")

if __name__ == "__main__":
    main()