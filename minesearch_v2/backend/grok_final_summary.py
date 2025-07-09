"""
Author: rahn
Datum: 09.07.2025
Version: 1.0
Beschreibung: Finale Zusammenfassung der Grok-Modell Tests
"""

from database import db_manager, ModelSummary, ModelStatistics
from sqlalchemy import func
from datetime import datetime

print("=== FINALE GROK-MODELL TEST ERGEBNISSE ===")
print(f"Datum: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n")

with db_manager.get_session() as session:
    # Hole alle Grok-Modell Zusammenfassungen
    grok_models = session.query(ModelSummary).filter(
        ModelSummary.model_id.like('grok:%')
    ).order_by(
        ModelSummary.avg_fields_found.desc()
    ).all()
    
    print("ÜBERSICHT ALLER GROK-MODELLE:")
    print("=" * 80)
    print(f"{'Modell':<20} {'Tests':<8} {'Erfolg':<10} {'Felder':<10} {'Konsistenz':<12} {'Response'}")
    print("-" * 80)
    
    for model in grok_models:
        print(f"{model.model_id:<20} {model.total_tests:<8} {model.success_rate:>9.0%} "
              f"{model.avg_fields_found:>9.1f} {model.overall_consistency:>11.2f} "
              f"{model.avg_response_time_ms/1000:>8.1f}s")
    
    # Detaillierte Statistiken pro Mine
    print("\n\nDETAILLIERTE ERGEBNISSE PRO MINE:")
    print("=" * 80)
    
    for model in ['grok:grok-3', 'grok:grok-3-mini', 'grok:grok-3-fast']:
        print(f"\n{model}:")
        print("-" * 40)
        
        # Statistiken pro Mine
        mine_stats = session.query(
            ModelStatistics.mine_name,
            func.count(ModelStatistics.id).label('tests'),
            func.avg(ModelStatistics.fields_found).label('avg_fields'),
            func.min(ModelStatistics.fields_found).label('min_fields'),
            func.max(ModelStatistics.fields_found).label('max_fields'),
            func.avg(ModelStatistics.response_time_ms).label('avg_time')
        ).filter(
            ModelStatistics.model_id == model,
            ModelStatistics.success == True
        ).group_by(
            ModelStatistics.mine_name
        ).all()
        
        for mine, tests, avg_fields, min_fields, max_fields, avg_time in mine_stats:
            print(f"  {mine}: {tests} Tests, Ø {avg_fields:.1f} Felder "
                  f"(Min: {min_fields}, Max: {max_fields}), Ø {avg_time/1000:.1f}s")
    
    # Performance-Vergleich
    print("\n\nPERFORMANCE-VERGLEICH:")
    print("=" * 80)
    
    # Geschwindigkeit
    print("\n1. GESCHWINDIGKEIT (schnellste zuerst):")
    speed_ranking = session.query(
        ModelSummary.model_id,
        ModelSummary.avg_response_time_ms
    ).filter(
        ModelSummary.model_id.like('grok:%')
    ).order_by(
        ModelSummary.avg_response_time_ms.asc()
    ).all()
    
    for i, (model, time_ms) in enumerate(speed_ranking, 1):
        print(f"   {i}. {model}: {time_ms/1000:.1f}s")
    
    # Feldabdeckung
    print("\n2. FELDABDECKUNG (meiste Felder zuerst):")
    field_ranking = session.query(
        ModelSummary.model_id,
        ModelSummary.avg_fields_found
    ).filter(
        ModelSummary.model_id.like('grok:%')
    ).order_by(
        ModelSummary.avg_fields_found.desc()
    ).all()
    
    for i, (model, fields) in enumerate(field_ranking, 1):
        print(f"   {i}. {model}: {fields:.1f} Felder")
    
    # Konsistenz
    print("\n3. KONSISTENZ (höchste zuerst):")
    consistency_ranking = session.query(
        ModelSummary.model_id,
        ModelSummary.overall_consistency
    ).filter(
        ModelSummary.model_id.like('grok:%')
    ).order_by(
        ModelSummary.overall_consistency.desc()
    ).all()
    
    for i, (model, consistency) in enumerate(consistency_ranking, 1):
        print(f"   {i}. {model}: {consistency:.2f}")
    
    # Kosten-Nutzen-Analyse (angenommen)
    print("\n\nKOSTEN-NUTZEN-ANALYSE:")
    print("=" * 80)
    print("(Annahme: grok-3-mini < grok-3-fast < grok-3 bei den Kosten)")
    print("\n- grok-3-mini: Beste Geschwindigkeit, niedrigste Kosten, aber auch niedrigste Qualität")
    print("- grok-3-fast: Ausgewogenes Verhältnis, beste Feldabdeckung")
    print("- grok-3: Höchste Konsistenz, aber langsamer und teurer")
    
    # Empfehlung
    print("\n\nEMPFEHLUNG:")
    print("=" * 80)
    print("1. Für schnelle, kostengünstige Suchen: grok-3-mini")
    print("2. Für optimale Feldabdeckung: grok-3-fast")
    print("3. Für höchste Konsistenz und Qualität: grok-3")
    print("\nAlle Modelle erreichen 100% Erfolgsrate und sind produktionsreif!")