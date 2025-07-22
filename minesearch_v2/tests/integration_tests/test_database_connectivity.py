#!/usr/bin/env python3
"""
Author: rahn
Datum: 14.07.2025
Version: 1.0
Beschreibung: Test Database-Konnektivität nach Database-Pfad Konsolidierung
"""

from database import db_manager
from database.models import ModelStatistics
from config import Config

def test_database_connectivity():
    """
    Testet Database-Konnektivität und prüft aktuelle Daten
    """
    print("🔧 DATABASE CONNECTIVITY TEST")
    print("="*50)
    
    # Zeige aktuelle Konfiguration
    print(f"📂 Database URL: {Config.DATABASE_URL}")
    
    try:
        # Teste Database-Verbindung
        with db_manager.get_session() as session:
            # Zähle ModelStatistics Einträge
            total_model_stats = session.query(ModelStatistics).count()
            print(f"📊 ModelStatistics Einträge: {total_model_stats}")
            
            # Teste aktuellste Einträge
            latest_entries = session.query(ModelStatistics).order_by(
                ModelStatistics.id.desc()
            ).limit(5).all()
            
            print(f"\n🔍 Neueste 5 Database-Einträge:")
            for entry in latest_entries:
                print(f"  - ID {entry.id}: {entry.model_id} | {entry.mine_name} | Run {entry.run_number}")
                print(f"    → {entry.fields_found} Felder | Erfolg: {entry.success}")
            
            # Prüfe Individual Model Coverage
            unique_models = session.query(ModelStatistics.model_id).distinct().count()
            print(f"\n🎯 Unique Models in Database: {unique_models}")
            
            # Prüfe Premium LLM Models (sollten nach dem Fix vorhanden sein)
            premium_models = ['anthropic:claude-sonnet-4', 'openai:o4-mini', 'gemini:gemini-2.5-flash']
            for model in premium_models:
                count = session.query(ModelStatistics).filter_by(model_id=model).count()
                status = "✅" if count > 0 else "❌"
                print(f"  {status} {model}: {count} Einträge")
                
        print(f"\n✅ Database-Verbindung erfolgreich!")
        return True
        
    except Exception as e:
        print(f"❌ Database-Verbindung fehlgeschlagen: {e}")
        return False

if __name__ == "__main__":
    test_database_connectivity()