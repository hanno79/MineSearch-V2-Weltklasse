"""
Author: rahn
Datum: 09.07.2025
Version: 1.0
Beschreibung: Detaillierte Analyse der Feld-Konsistenz über alle Modelle
"""

from database import DatabaseManager, FieldConsistency, ModelSummary
from sqlalchemy import func, desc
from tabulate import tabulate
from collections import defaultdict

def analyze_field_consistency():
    """Analysiere Feld-Konsistenz über alle Modelle"""
    db_manager = DatabaseManager()
    
    print("=" * 100)
    print("FELD-KONSISTENZ-ANALYSE")
    print("=" * 100)
    print()
    
    with db_manager.get_session() as session:
        # Hole alle Feld-Konsistenz-Daten
        all_consistencies = session.query(FieldConsistency).all()
        
        # Gruppiere nach Feld
        field_data = defaultdict(list)
        
        for consistency in all_consistencies:
            field_data[consistency.field_name].append({
                'model_id': consistency.model_id,
                'consistency_score': consistency.consistency_score,
                'is_consistent': consistency.is_consistent,
                'mine_name': consistency.mine_name
            })
        
        # Kritische Felder
        critical_fields = [
            'Eigentümer', 
            'Betreiber', 
            'Restaurationskosten',
            'x-Koordinate',
            'y-Koordinate',
            'Aktivitätsstatus'
        ]
        
        print("1. KRITISCHE FELDER - KONSISTENZ-ANALYSE")
        print("-" * 50)
        
        for field in critical_fields:
            if field in field_data:
                print(f"\n{field}:")
                
                # Berechne Durchschnittskonsistenz
                scores = [d['consistency_score'] for d in field_data[field]]
                avg_consistency = sum(scores) / len(scores) if scores else 0
                
                print(f"  Durchschnittliche Konsistenz: {avg_consistency:.2%}")
                print(f"  Anzahl Modelle mit Daten: {len(set(d['model_id'] for d in field_data[field]))}")
                
                # Top 3 Modelle für dieses Feld
                model_scores = defaultdict(list)
                for d in field_data[field]:
                    model_scores[d['model_id']].append(d['consistency_score'])
                
                model_avg = [(model, sum(scores)/len(scores)) for model, scores in model_scores.items()]
                model_avg.sort(key=lambda x: x[1], reverse=True)
                
                print("  Top 3 Modelle:")
                for i, (model, score) in enumerate(model_avg[:3], 1):
                    print(f"    {i}. {model}: {score:.2%}")
            else:
                print(f"\n{field}: KEINE DATEN")
        
        # Gesamtübersicht
        print("\n\n2. ALLE FELDER - KONSISTENZ-ÜBERSICHT")
        print("-" * 50)
        
        field_summary = []
        for field_name, data in field_data.items():
            # Berechne Statistiken
            scores = [d['consistency_score'] for d in data]
            avg_score = sum(scores) / len(scores) if scores else 0
            consistent_count = sum(1 for d in data if d['is_consistent'])
            model_count = len(set(d['model_id'] for d in data))
            
            field_summary.append({
                'field': field_name,
                'avg_consistency': avg_score,
                'consistent_count': consistent_count,
                'total_entries': len(data),
                'model_count': model_count
            })
        
        # Sortiere nach durchschnittlicher Konsistenz
        field_summary.sort(key=lambda x: x['avg_consistency'], reverse=True)
        
        # Erstelle Tabelle
        table_data = []
        for fs in field_summary[:20]:  # Top 20 Felder
            table_data.append([
                fs['field'],
                f"{fs['avg_consistency']:.2%}",
                f"{fs['consistent_count']}/{fs['total_entries']}",
                fs['model_count']
            ])
        
        headers = ["Feld", "Ø Konsistenz", "Konsistent", "Modelle"]
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
        
        # Modell-Ranking basierend auf kritischen Feldern
        print("\n\n3. MODELL-RANKING NACH KRITISCHEN FELDERN")
        print("-" * 50)
        
        model_critical_scores = defaultdict(lambda: {'scores': [], 'fields': []})
        
        for field in critical_fields:
            if field in field_data:
                for d in field_data[field]:
                    model_critical_scores[d['model_id']]['scores'].append(d['consistency_score'])
                    model_critical_scores[d['model_id']]['fields'].append(field)
        
        # Berechne Durchschnittswerte
        model_ranking = []
        for model_id, data in model_critical_scores.items():
            if data['scores']:
                avg_score = sum(data['scores']) / len(data['scores'])
                model_ranking.append({
                    'model': model_id,
                    'avg_critical_consistency': avg_score,
                    'critical_fields_found': len(set(data['fields'])),
                    'total_critical_fields': len(critical_fields)
                })
        
        # Sortiere nach Konsistenz
        model_ranking.sort(key=lambda x: x['avg_critical_consistency'], reverse=True)
        
        # Erstelle Tabelle
        table_data = []
        for mr in model_ranking:
            table_data.append([
                mr['model'],
                f"{mr['avg_critical_consistency']:.2%}",
                f"{mr['critical_fields_found']}/{mr['total_critical_fields']}"
            ])
        
        headers = ["Modell", "Ø Kritische Konsistenz", "Kritische Felder"]
        print(tabulate(table_data, headers=headers, tablefmt="grid"))

if __name__ == "__main__":
    analyze_field_consistency()