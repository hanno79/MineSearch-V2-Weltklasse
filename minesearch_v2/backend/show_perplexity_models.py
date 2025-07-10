"""
Author: rahn
Datum: 09.07.2025
Version: 1.0
Beschreibung: Zeige alle Perplexity Modelle in der Datenbank
"""

from database import db_manager, ModelSummary
from sqlalchemy import desc

with db_manager.get_session() as session:
    perplexity_models = session.query(ModelSummary).filter(
        ModelSummary.model_id.like('perplexity:%')
    ).order_by(
        desc(ModelSummary.avg_fields_found)
    ).all()
    
    print('\nPerplexity Modelle in Datenbank:\n')
    print(f"{'Modell':<35} {'Tests':<8} {'Erfolg':<10} {'Felder':<10} {'Zeit (s)':<10}")
    print('='*80)
    
    for model in perplexity_models:
        success_str = f"{model.success_rate:.0%}"
        print(f"{model.model_id:<35} {model.total_tests:<8} {success_str:<10} {model.avg_fields_found:<10.1f} {model.avg_response_time_ms/1000:<10.1f}")
        
    print(f"\nGesamt: {len(perplexity_models)} Perplexity Modelle")