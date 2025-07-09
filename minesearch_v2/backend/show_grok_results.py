"""
Author: rahn
Datum: 09.07.2025
Version: 1.0
Beschreibung: Zeige Grok-Modell Ergebnisse aus der Datenbank
"""

from database import db_manager, ModelSummary, ModelStatistics
from sqlalchemy import func
import json

# Hole alle Grok-Modelle
with db_manager.get_session() as session:
    # Alle Grok-Modell Zusammenfassungen
    grok_models = session.query(
        ModelSummary.model_id,
        ModelSummary.success_rate,
        ModelSummary.avg_fields_found,
        ModelSummary.overall_consistency,
        ModelSummary.total_tests,
        ModelSummary.data_success_rate
    ).filter(
        ModelSummary.model_id.like('grok:%')
    ).order_by(
        ModelSummary.avg_fields_found.desc()
    ).all()
    
    print("=== GROK-MODELL ERGEBNISSE ===\n")
    
    for model_id, success_rate, avg_fields, consistency, total_tests, data_success in grok_models:
        print(f"Modell: {model_id}")
        print(f"  - Durchschnittliche Felder: {avg_fields:.1f}")
        print(f"  - Erfolgsrate: {success_rate:.0%}")
        print(f"  - Daten-Erfolgsrate: {data_success:.0%}")
        print(f"  - Konsistenz: {consistency:.2f}")
        print(f"  - Anzahl Tests: {total_tests}")
        print()
    
    # Detaillierte Statistiken für die letzten Tests
    print("\n=== LETZTE TEST ERGEBNISSE ===\n")
    
    for model in ['grok:grok-3-mini', 'grok:grok-3-fast']:
        print(f"\n{model}:")
        
        # Hole die letzten 3 Tests für jedes Modell
        recent_tests = session.query(
            ModelStatistics.mine_name,
            ModelStatistics.success,
            ModelStatistics.fields_found,
            ModelStatistics.response_time_ms
        ).filter(
            ModelStatistics.model_id == model
        ).order_by(
            ModelStatistics.id.desc()
        ).limit(3).all()
        
        for mine, success, fields, response_time_ms in recent_tests:
            status = "✅" if success else "❌"
            print(f"  {status} {mine}: {fields} Felder, {response_time_ms/1000:.1f}s")
    
    # Vergleich aller Grok-Modelle
    print("\n=== GROK-MODELL VERGLEICH ===\n")
    print("Modell            | Felder | Erfolg | Konsistenz | Tests")
    print("-" * 60)
    
    for model_id, success_rate, avg_fields, consistency, total_tests, _ in grok_models:
        model_name = model_id.replace('grok:', '').ljust(15)
        print(f"{model_name} | {avg_fields:6.1f} | {success_rate:5.0%} | {consistency:10.2f} | {total_tests:5d}")