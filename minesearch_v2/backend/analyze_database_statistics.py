"""
Author: rahn
Datum: 09.07.2025
Version: 1.0
Beschreibung: Umfassende Analyse der Datenbank-Statistiken nach allen Tests
"""

import json
from datetime import datetime
from sqlalchemy import func, desc, and_
from database import DatabaseManager, ModelStatistics, ModelSummary, FieldConsistency, Source, SearchResult
from tabulate import tabulate
import statistics

def analyze_database_statistics():
    """Hauptfunktion für die Datenbank-Analyse"""
    db_manager = DatabaseManager()
    
    print("=" * 100)
    print("MINESEARCH V2 - UMFASSENDE DATENBANK-STATISTIK-ANALYSE")
    print(f"Datum: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    print("=" * 100)
    print()
    
    # 1. Modell-Statistiken
    print("1. GETESTETE MODELLE")
    print("-" * 50)
    
    with db_manager.get_session() as session:
        # Anzahl getesteter Modelle
        model_count = session.query(func.count(func.distinct(ModelStatistics.model_id))).scalar()
        print(f"Anzahl getesteter Modelle: {model_count}")
        
        # Liste aller Modelle
        models = session.query(ModelStatistics.model_id).distinct().all()
        print("\nGetestete Modelle:")
        for model in models:
            print(f"  - {model[0]}")
    
    # 2. Test-Statistiken
    print("\n\n2. TEST-STATISTIKEN")
    print("-" * 50)
    
    with db_manager.get_session() as session:
        total_tests = session.query(func.count(ModelStatistics.id)).scalar()
        successful_tests = session.query(func.count(ModelStatistics.id)).filter(
            ModelStatistics.success == True
        ).scalar()
        
        print(f"Gesamtanzahl Tests: {total_tests}")
        print(f"Erfolgreiche Tests: {successful_tests}")
        print(f"Erfolgsrate: {(successful_tests/total_tests*100):.1f}%")
        
        # Tests pro Mine
        mines_tested = session.query(func.count(func.distinct(ModelStatistics.mine_name))).scalar()
        print(f"\nAnzahl getesteter Minen: {mines_tested}")
    
    # 3. Quellen-Statistiken
    print("\n\n3. QUELLEN-STATISTIKEN")
    print("-" * 50)
    
    with db_manager.get_session() as session:
        total_sources = session.query(func.count(Source.id)).scalar()
        print(f"Gesamtanzahl Quellen in Datenbank: {total_sources}")
        
        # Quellen nach Typ
        source_types = session.query(
            Source.source_type,
            func.count(Source.id)
        ).group_by(Source.source_type).all()
        
        print("\nQuellen nach Typ:")
        for source_type, count in sorted(source_types, key=lambda x: x[1], reverse=True):
            print(f"  - {source_type}: {count}")
        
        # Quellen nach Land
        source_countries = session.query(
            Source.country,
            func.count(Source.id)
        ).group_by(Source.country).all()
        
        print("\nQuellen nach Land:")
        for country, count in sorted(source_countries, key=lambda x: x[1], reverse=True):
            country_name = country or "Global"
            print(f"  - {country_name}: {count}")
    
    # 4. Top 10 Modelle
    print("\n\n4. TOP 10 MODELLE NACH LEISTUNG")
    print("-" * 50)
    
    with db_manager.get_session() as session:
        # Hole alle ModelSummary Einträge
        summaries = session.query(ModelSummary).all()
        
        # Berechne Gesamtpunktzahl für Ranking
        model_scores = []
        
        for summary in summaries:
            # Punktesystem:
            # - Erfolgsrate: 40% Gewichtung
            # - Daten-Erfolgsrate: 30% Gewichtung
            # - Anzahl Felder: 20% Gewichtung
            # - Konsistenz: 10% Gewichtung
            
            success_score = summary.success_rate * 40
            data_success_score = summary.data_success_rate * 30
            fields_score = min(summary.avg_fields_found / 15, 1.0) * 20  # Normalisiert auf max 15 Felder
            consistency_score = summary.overall_consistency * 10
            
            total_score = success_score + data_success_score + fields_score + consistency_score
            
            model_scores.append({
                'model_id': summary.model_id,
                'total_score': total_score,
                'success_rate': summary.success_rate,
                'data_success_rate': summary.data_success_rate,
                'avg_fields_found': summary.avg_fields_found,
                'consistency': summary.overall_consistency,
                'total_tests': summary.total_tests,
                'avg_response_time': summary.avg_response_time_ms
            })
        
        # Sortiere nach Gesamtpunktzahl
        model_scores.sort(key=lambda x: x['total_score'], reverse=True)
        
        # Erstelle Tabelle für Top 10
        table_data = []
        for i, model in enumerate(model_scores[:10], 1):
            table_data.append([
                i,
                model['model_id'],
                f"{model['success_rate']:.1%}",
                f"{model['data_success_rate']:.1%}",
                f"{model['avg_fields_found']:.1f}",
                f"{model['consistency']:.2f}",
                f"{model['total_score']:.1f}",
                model['total_tests'],
                f"{model['avg_response_time']:.0f}ms"
            ])
        
        headers = ["Rang", "Modell", "Erfolg", "Daten-Erfolg", "Ø Felder", "Konsistenz", "Score", "Tests", "Ø Zeit"]
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
    
    # 5. Modelle mit Konsistenz > 0.8
    print("\n\n5. MODELLE MIT HOHER KONSISTENZ (> 0.8)")
    print("-" * 50)
    
    with db_manager.get_session() as session:
        high_consistency_models = session.query(ModelSummary).filter(
            ModelSummary.overall_consistency > 0.8
        ).order_by(desc(ModelSummary.overall_consistency)).all()
        
        if high_consistency_models:
            print(f"Anzahl Modelle mit Konsistenz > 0.8: {len(high_consistency_models)}\n")
            
            table_data = []
            for model in high_consistency_models:
                table_data.append([
                    model.model_id,
                    f"{model.overall_consistency:.3f}",
                    f"{model.success_rate:.1%}",
                    f"{model.avg_fields_found:.1f}",
                    model.total_mines_tested
                ])
            
            headers = ["Modell", "Konsistenz", "Erfolgsrate", "Ø Felder", "Minen getestet"]
            print(tabulate(table_data, headers=headers, tablefmt="grid"))
        else:
            print("Keine Modelle mit Konsistenz > 0.8 gefunden!")
    
    # 6. Detaillierte Modell-Analyse
    print("\n\n6. DETAILLIERTE MODELL-ANALYSE")
    print("-" * 50)
    
    with db_manager.get_session() as session:
        # Gruppiere Modelle nach Kategorie
        perplexity_models = []
        openrouter_models = []
        other_models = []
        
        for summary in summaries:
            model_info = {
                'id': summary.model_id,
                'success_rate': summary.success_rate,
                'data_success_rate': summary.data_success_rate,
                'fields': summary.avg_fields_found,
                'consistency': summary.overall_consistency,
                'tests': summary.total_tests
            }
            
            if summary.model_id.startswith('perplexity:'):
                perplexity_models.append(model_info)
            elif summary.model_id.startswith('openrouter:'):
                openrouter_models.append(model_info)
            else:
                other_models.append(model_info)
        
        # Sortiere nach Daten-Erfolgsrate
        perplexity_models.sort(key=lambda x: x['data_success_rate'], reverse=True)
        openrouter_models.sort(key=lambda x: x['data_success_rate'], reverse=True)
        other_models.sort(key=lambda x: x['data_success_rate'], reverse=True)
        
        print("\nPERPLEXITY MODELLE:")
        for model in perplexity_models:
            print(f"  {model['id']}")
            print(f"    - Erfolgsrate: {model['success_rate']:.1%}")
            print(f"    - Daten-Erfolg: {model['data_success_rate']:.1%}")
            print(f"    - Ø Felder: {model['fields']:.1f}")
            print(f"    - Konsistenz: {model['consistency']:.2f}")
            print(f"    - Tests: {model['tests']}")
        
        print("\nOPENROUTER MODELLE:")
        for model in openrouter_models:
            print(f"  {model['id']}")
            print(f"    - Erfolgsrate: {model['success_rate']:.1%}")
            print(f"    - Daten-Erfolg: {model['data_success_rate']:.1%}")
            print(f"    - Ø Felder: {model['fields']:.1f}")
            print(f"    - Konsistenz: {model['consistency']:.2f}")
            print(f"    - Tests: {model['tests']}")
        
        print("\nANDERE MODELLE:")
        for model in other_models:
            print(f"  {model['id']}")
            print(f"    - Erfolgsrate: {model['success_rate']:.1%}")
            print(f"    - Daten-Erfolg: {model['data_success_rate']:.1%}")
            print(f"    - Ø Felder: {model['fields']:.1f}")
            print(f"    - Konsistenz: {model['consistency']:.2f}")
            print(f"    - Tests: {model['tests']}")
    
    # 7. Zusammenfassung
    print("\n\n7. ZUSAMMENFASSUNG")
    print("-" * 50)
    
    with db_manager.get_session() as session:
        # Beste Modelle nach verschiedenen Kriterien
        best_success = session.query(ModelSummary).order_by(desc(ModelSummary.success_rate)).first()
        best_data_success = session.query(ModelSummary).order_by(desc(ModelSummary.data_success_rate)).first()
        best_fields = session.query(ModelSummary).order_by(desc(ModelSummary.avg_fields_found)).first()
        best_consistency = session.query(ModelSummary).order_by(desc(ModelSummary.overall_consistency)).first()
        
        print(f"Bestes Modell nach API-Erfolgsrate: {best_success.model_id} ({best_success.success_rate:.1%})")
        print(f"Bestes Modell nach Daten-Erfolgsrate: {best_data_success.model_id} ({best_data_success.data_success_rate:.1%})")
        print(f"Bestes Modell nach Anzahl Felder: {best_fields.model_id} ({best_fields.avg_fields_found:.1f} Felder)")
        print(f"Bestes Modell nach Konsistenz: {best_consistency.model_id} ({best_consistency.overall_consistency:.3f})")
        
        # Durchschnittswerte
        avg_success = session.query(func.avg(ModelSummary.success_rate)).scalar() or 0
        avg_data_success = session.query(func.avg(ModelSummary.data_success_rate)).scalar() or 0
        avg_fields = session.query(func.avg(ModelSummary.avg_fields_found)).scalar() or 0
        avg_consistency = session.query(func.avg(ModelSummary.overall_consistency)).scalar() or 0
        
        print(f"\nDurchschnittswerte über alle Modelle:")
        print(f"  - Ø API-Erfolgsrate: {avg_success:.1%}")
        print(f"  - Ø Daten-Erfolgsrate: {avg_data_success:.1%}")
        print(f"  - Ø Anzahl Felder: {avg_fields:.1f}")
        print(f"  - Ø Konsistenz: {avg_consistency:.2f}")
    
    # Speichere Analyse als JSON
    print("\n\nSpeichere detaillierte Analyse als JSON...")
    
    analysis_data = {
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'models_tested': model_count,
            'total_tests': total_tests,
            'successful_tests': successful_tests,
            'mines_tested': mines_tested,
            'total_sources': total_sources,
            'high_consistency_models': len(high_consistency_models)
        },
        'top_10_models': model_scores[:10],
        'high_consistency_models': [
            {
                'model_id': m.model_id,
                'consistency': m.overall_consistency,
                'success_rate': m.success_rate,
                'data_success_rate': m.data_success_rate,
                'avg_fields': m.avg_fields_found
            }
            for m in high_consistency_models
        ],
        'averages': {
            'avg_success_rate': avg_success,
            'avg_data_success_rate': avg_data_success,
            'avg_fields_found': avg_fields,
            'avg_consistency': avg_consistency
        }
    }
    
    with open('database_analysis_results.json', 'w', encoding='utf-8') as f:
        json.dump(analysis_data, f, indent=2, ensure_ascii=False)
    
    print("Analyse gespeichert als: database_analysis_results.json")
    print("\n" + "=" * 100)

if __name__ == "__main__":
    analyze_database_statistics()