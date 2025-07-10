"""
Author: rahn
Datum: 09.07.2025
Version: 1.0
Beschreibung: Zeige Statistiken aller Modelle in der Datenbank
"""

from database import db_manager, ModelSummary
from sqlalchemy import desc

with db_manager.get_session() as session:
    all_models = session.query(ModelSummary).order_by(
        desc(ModelSummary.avg_fields_found),
        ModelSummary.avg_response_time_ms
    ).all()
    
    print('\nAlle Modelle in Datenbank nach Feldabdeckung:\n')
    print(f"{'Modell':<40} {'Tests':<8} {'Erfolg':<10} {'Felder':<10} {'Zeit (s)':<10}")
    print('='*85)
    
    for model in all_models:
        success_str = f"{model.success_rate:.0%}"
        print(f"{model.model_id:<40} {model.total_tests:<8} {success_str:<10} {model.avg_fields_found:<10.1f} {model.avg_response_time_ms/1000:<10.1f}")
        
    print(f"\nGesamt: {len(all_models)} Modelle getestet")
    
    # Zeige Top 10
    print("\n\nTOP 10 MODELLE NACH FELDABDECKUNG:")
    print("="*85)
    for i, model in enumerate(all_models[:10], 1):
        print(f"{i:2}. {model.model_id:<35} - {model.avg_fields_found:.1f} Felder ({model.avg_response_time_ms/1000:.1f}s)")