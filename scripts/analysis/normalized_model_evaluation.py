#!/usr/bin/env python3
"""
Author: rahn
Datum: 04.09.2025
Version: 1.0
Beschreibung: NORMALISIERTES Modell-Bewertungssystem basierend auf der normalisierten Datenbankstruktur
"""

import sqlite3
import json
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, Counter
import sys
import os
# Import für Root-Level-Scripts
try:
    # Versuche Backend-Import  
    from minesearch.database.db_utils import get_normalized_db_path, get_sqlite_connection
except ImportError:
    # Fallback für Root-Level-Scripts
    from db_utils_root.db_utils import get_normalized_db_path, get_sqlite_connection

class NormalizedModelEvaluationSystem:
    """Bewertungssystem für AI-Modelle basierend auf normalisierter Datenbankstruktur"""
    
    def __init__(self, db_path: str = get_normalized_db_path()):
        self.db_path = db_path
        
    def get_mine_search_data(self, mine_name: str = None, days_back: int = 30) -> Dict[str, Any]:
        """Hole alle Suchdaten für eine bestimmte Mine aus normalisierter Struktur"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Parameter für Mine-Filter
            if mine_name:
                mine_filter = "AND m.name LIKE ?"
                params = [f"%{mine_name}%"]
            else:
                mine_filter = ""
                params = []
            
            # Query für normalisierte Struktur
            query = f"""
                SELECT 
                    ss.session_id,
                    ss.search_timestamp,
                    ss.search_duration_ms,
                    ss.success,
                    m.id as mine_id,
                    m.name as mine_name,
                    c.name as country,
                    r.name as region,
                    am.full_model_id as model_used,
                    
                    -- Feldwerte aus mine_data_fields (primäre Quelle)
                    mdf.field_name,
                    mdf.raw_value,
                    mdf.normalized_value,
                    mdf.numeric_value,
                    mdf.confidence_score,
                    mdf.is_template_value,
                    mdf.validation_status,
                    mdf.model_used as field_model_used
                FROM search_sessions ss
                JOIN mines m ON ss.mine_id = m.id
                LEFT JOIN countries c ON m.country_id = c.id
                LEFT JOIN regions r ON m.region_id = r.id
                LEFT JOIN ai_models am ON ss.ai_model_id = am.id
                LEFT JOIN mine_data_fields mdf ON mdf.search_result_id = ss.id
                WHERE 1=1 {mine_filter}
                ORDER BY ss.search_timestamp DESC, ss.session_id, mdf.field_name
            """
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Organisiere Daten nach Session
            sessions = {}
            for row in rows:
                session_id = row['session_id']
                if session_id not in sessions:
                    sessions[session_id] = {
                        'session_id': session_id,
                        'mine_id': row['mine_id'],
                        'mine_name': row['mine_name'],
                        'country': row['country'],
                        'region': row['region'],
                        'search_timestamp': row['search_timestamp'],
                        'search_duration_ms': row['search_duration_ms'],
                        'success': row['success'],
                        'model_used': row['model_used'] or 'unknown',
                        'fields': {}
                    }
                
                # Füge Feldwerte hinzu
                if row['field_name']:
                    sessions[session_id]['fields'][row['field_name']] = {
                        'raw_value': row['raw_value'],
                        'normalized_value': row['normalized_value'],
                        'numeric_value': row['numeric_value'],
                        'confidence_score': row['confidence_score'],
                        'is_template_value': row['is_template_value'],
                        'validation_status': row['validation_status'],
                        'model_used': row['field_model_used'] or row['model_used'] or 'unknown'
                    }
            
            return {'sessions': list(sessions.values())}
    
    def calculate_field_consistency(self, sessions: List[Dict], field_name: str) -> Dict[str, Any]:
        """Berechne Konsistenz für ein spezifisches Feld über alle Sessions"""
        field_values = []
        models_used = []
        confidence_scores = []
        
        for session in sessions:
            if field_name in session['fields']:
                field_data = session['fields'][field_name]
                # Nur valide, nicht-template Werte verwenden
                if (field_data['normalized_value'] and 
                    not field_data['is_template_value'] and 
                    field_data['validation_status'] != 'template'):
                    
                    field_values.append(field_data['normalized_value'])
                    models_used.append(field_data['model_used'])
                    if field_data['confidence_score']:
                        confidence_scores.append(field_data['confidence_score'])
        
        if not field_values:
            return {
                'field_name': field_name,
                'total_values': 0,
                'unique_values': 0,
                'consistency_score': 0.0,
                'most_common_value': None,
                'most_common_count': 0,
                'confidence': 0.0,
                'avg_confidence_score': 0.0
            }
        
        # Zähle Werte
        value_counts = Counter(field_values)
        most_common_value, most_common_count = value_counts.most_common(1)[0]
        
        # Konsistenz-Score: Je öfter der häufigste Wert vorkommt, desto höher
        consistency_score = most_common_count / len(field_values)
        
        # Vertrauensscore basierend auf Anzahl Bestätigungen
        confidence = min(1.0, most_common_count / 5.0)
        
        # Durchschnittlicher Confidence-Score der AI-Modelle
        avg_confidence_score = statistics.mean(confidence_scores) if confidence_scores else 0.0
        
        return {
            'field_name': field_name,
            'total_values': len(field_values),
            'unique_values': len(value_counts),
            'unique_values_list': list(value_counts.keys()),
            'value_counts': dict(value_counts),
            'consistency_score': consistency_score,
            'most_common_value': most_common_value,
            'most_common_count': most_common_count,
            'confidence': confidence,
            'avg_confidence_score': avg_confidence_score,
            'models_contributing': list(set(models_used))
        }
    
    def calculate_model_performance(self, sessions: List[Dict]) -> Dict[str, Dict[str, Any]]:
        """Berechne Performance-Metriken pro Modell"""
        model_stats = defaultdict(lambda: {
            'total_searches': 0,
            'successful_searches': 0,
            'total_fields_found': 0,
            'total_duration_ms': 0,
            'template_values_count': 0,
            'confidence_scores': [],
            'fields_found_per_search': [],
            'valid_fields_per_search': []
        })
        
        for session in sessions:
            model_used = session['model_used']
            stats = model_stats[model_used]
            stats['total_searches'] += 1
            
            if session['success']:
                stats['successful_searches'] += 1
            
            # Zähle Felder (getrennt: alle vs. valide)
            total_fields = len(session['fields'])
            valid_fields = 0
            
            for field_data in session['fields'].values():
                if (field_data['normalized_value'] and 
                    not field_data['is_template_value'] and
                    field_data['validation_status'] != 'template'):
                    valid_fields += 1
                    if field_data['confidence_score']:
                        stats['confidence_scores'].append(field_data['confidence_score'])
                elif field_data['is_template_value']:
                    stats['template_values_count'] += 1
            
            stats['total_fields_found'] += valid_fields
            stats['fields_found_per_search'].append(total_fields)
            stats['valid_fields_per_search'].append(valid_fields)
            
            if session['search_duration_ms']:
                stats['total_duration_ms'] += session['search_duration_ms']
        
        # Berechne abgeleitete Metriken
        model_performance = {}
        for model, stats in model_stats.items():
            avg_duration = stats['total_duration_ms'] / stats['total_searches'] if stats['total_searches'] > 0 else 0
            success_rate = stats['successful_searches'] / stats['total_searches'] if stats['total_searches'] > 0 else 0
            avg_total_fields = statistics.mean(stats['fields_found_per_search']) if stats['fields_found_per_search'] else 0
            avg_valid_fields = statistics.mean(stats['valid_fields_per_search']) if stats['valid_fields_per_search'] else 0
            avg_confidence = statistics.mean(stats['confidence_scores']) if stats['confidence_scores'] else 0
            
            # Qualitäts-Rate (valide Felder / alle Felder)
            quality_rate = avg_valid_fields / avg_total_fields if avg_total_fields > 0 else 0
            
            # Performance Score (0-100) - ERWEITERT
            performance_score = (
                (success_rate * 25) +  # 25% Erfolgsquote
                (min(avg_valid_fields / 15, 1.0) * 25) +  # 25% Feldvollständigkeit
                (avg_confidence * 20) +  # 20% Durchschnittliches Vertrauen
                (quality_rate * 20) +  # 20% Qualitäts-Rate (keine Template-Werte)
                ((10000 - min(avg_duration, 10000)) / 10000 * 10)  # 10% Geschwindigkeit
            )
            
            model_performance[model] = {
                'total_searches': stats['total_searches'],
                'successful_searches': stats['successful_searches'],
                'success_rate': success_rate,
                'avg_duration_ms': avg_duration,
                'avg_total_fields': avg_total_fields,
                'avg_valid_fields': avg_valid_fields,
                'quality_rate': quality_rate,
                'template_values_count': stats['template_values_count'],
                'avg_confidence_score': avg_confidence,
                'performance_score': performance_score,
                'fields_distribution': dict(Counter(stats['valid_fields_per_search']))
            }
        
        return model_performance
    
    def analyze_mine_consistency(self, mine_name: str) -> Dict[str, Any]:
        """Vollständige Konsistenz-Analyse für eine Mine"""
        print(f"\n🔍 ANALYSIERE KONSISTENZ für: {mine_name}")
        
        # Hole Daten
        data = self.get_mine_search_data(mine_name)
        sessions = data['sessions']
        
        if not sessions:
            return {'error': f'Keine Daten für Mine {mine_name} gefunden'}
        
        print(f"📊 {len(sessions)} Suchsitzungen gefunden")
        
        # Sammle alle vorhandenen Feldnamen
        all_fields = set()
        for session in sessions:
            all_fields.update(session['fields'].keys())
        
        print(f"📋 {len(all_fields)} verschiedene Felder gefunden")
        
        # Analysiere Konsistenz pro Feld
        field_consistency = {}
        for field_name in all_fields:
            consistency = self.calculate_field_consistency(sessions, field_name)
            field_consistency[field_name] = consistency
        
        # Modell-Performance
        model_performance = self.calculate_model_performance(sessions)
        
        # Overall-Statistiken
        total_valid_values = sum(fc['total_values'] for fc in field_consistency.values())
        avg_consistency = statistics.mean([fc['consistency_score'] for fc in field_consistency.values() if fc['total_values'] > 0])
        
        # Kategorisiere Felder nach Konsistenz
        high_consistency_fields = [fc for fc in field_consistency.values() if fc['consistency_score'] >= 0.8 and fc['total_values'] >= 3]
        medium_consistency_fields = [fc for fc in field_consistency.values() if 0.5 <= fc['consistency_score'] < 0.8 and fc['total_values'] >= 3]
        low_consistency_fields = [fc for fc in field_consistency.values() if fc['consistency_score'] < 0.5 and fc['total_values'] >= 3]
        
        # Zusätzliche Bewertungsmetriken
        template_rate = sum(stats['template_values_count'] for stats in model_performance.values()) / sum(stats['total_searches'] for stats in model_performance.values()) if model_performance else 0
        
        return {
            'mine_name': mine_name,
            'analysis_timestamp': datetime.now().isoformat(),
            'sessions_analyzed': len(sessions),
            'total_fields': len(all_fields),
            'total_valid_values': total_valid_values,
            'avg_consistency_score': avg_consistency,
            'template_value_rate': template_rate,
            'field_consistency': field_consistency,
            'model_performance': model_performance,
            'consistency_categories': {
                'high_consistency': len(high_consistency_fields),
                'medium_consistency': len(medium_consistency_fields),
                'low_consistency': len(low_consistency_fields)
            },
            'high_consistency_fields': high_consistency_fields,
            'medium_consistency_fields': medium_consistency_fields,
            'low_consistency_fields': low_consistency_fields
        }
    
    def generate_comprehensive_report(self, mine_name: str) -> str:
        """Generiere umfassenden Bericht mit erweiterten Metriken"""
        analysis = self.analyze_mine_consistency(mine_name)
        
        if 'error' in analysis:
            return f"❌ {analysis['error']}"
        
        report = []
        report.append(f"🏭 COMPREHENSIVE MINE ANALYSIS: {analysis['mine_name']}")
        report.append("=" * 70)
        report.append(f"📊 Sessions analyzed: {analysis['sessions_analyzed']}")
        report.append(f"📋 Total fields: {analysis['total_fields']}")
        report.append(f"✅ Valid values: {analysis['total_valid_values']}")
        report.append(f"📈 Average consistency: {analysis['avg_consistency_score']:.1%}")
        report.append(f"🎭 Template value rate: {analysis['template_value_rate']:.1%}")
        
        report.append(f"\n🎯 CONSISTENCY DISTRIBUTION:")
        report.append(f"   🟢 High (≥80%): {analysis['consistency_categories']['high_consistency']} fields")
        report.append(f"   🟡 Medium (50-79%): {analysis['consistency_categories']['medium_consistency']} fields")
        report.append(f"   🔴 Low (<50%): {analysis['consistency_categories']['low_consistency']} fields")
        
        # TOP konsistente Felder mit erweiterten Metriken
        if analysis['high_consistency_fields']:
            report.append(f"\n🟢 TOP CONSISTENT FIELDS:")
            for field in sorted(analysis['high_consistency_fields'], key=lambda x: x['consistency_score'], reverse=True)[:5]:
                report.append(f"   📝 {field['field_name']}:")
                report.append(f"      🎯 Consistency: {field['consistency_score']:.1%} ({field['most_common_count']}/{field['total_values']})")
                report.append(f"      🏆 Most common: '{field['most_common_value']}'")
                report.append(f"      🤖 AI Confidence: {field['avg_confidence_score']:.2f}/1.0")
                report.append(f"      🤝 Models: {', '.join(field['models_contributing'][:3])}{'...' if len(field['models_contributing']) > 3 else ''}")
        
        # Problematische Felder
        if analysis['low_consistency_fields']:
            report.append(f"\n🔴 LOW CONSISTENCY FIELDS (need attention):")
            for field in sorted(analysis['low_consistency_fields'], key=lambda x: x['consistency_score'])[:5]:
                report.append(f"   📝 {field['field_name']}: {field['consistency_score']:.1%} ({field['unique_values']} different values)")
                top_values = sorted(field['value_counts'].items(), key=lambda x: x[1], reverse=True)[:3]
                top_values_str = ', '.join([f"'{v}' ({c}x)" for v, c in top_values])
                report.append(f"      📊 Top values: {top_values_str}")
        
        # ERWEITERTE Modell-Performance mit neuen Metriken
        report.append(f"\n🤖 MODEL PERFORMANCE RANKING:")
        sorted_models = sorted(analysis['model_performance'].items(), key=lambda x: x[1]['performance_score'], reverse=True)
        for i, (model, perf) in enumerate(sorted_models, 1):
            report.append(f"   {i}. {model}:")
            report.append(f"      🏆 Overall Score: {perf['performance_score']:.1f}/100")
            report.append(f"      ✅ Success Rate: {perf['success_rate']:.1%}")
            report.append(f"      📊 Avg Valid Fields: {perf['avg_valid_fields']:.1f} (Quality: {perf['quality_rate']:.1%})")
            report.append(f"      ⏱️ Avg Duration: {perf['avg_duration_ms']:.0f}ms")
            report.append(f"      🎯 Avg AI Confidence: {perf['avg_confidence_score']:.2f}")
            report.append(f"      🎭 Template Values: {perf['template_values_count']} total")
        
        # NEUE BEWERTUNGSMETRIKEN
        report.append(f"\n🎯 ADDITIONAL MODEL INSIGHTS:")
        
        # Kosten-Nutzen-Verhältnis (hypothetisch)
        report.append(f"   💰 Cost-Efficiency Ranking:")
        cost_efficiency = []
        for model, perf in analysis['model_performance'].items():
            # Vereinfachte Kostenberechnung (kostenlose Modelle = 0, andere geschätzt)
            estimated_cost = 0.0 if 'free' in model.lower() else 0.01  # $0.01 pro Suche geschätzt
            efficiency = perf['performance_score'] / max(estimated_cost * 100, 1)  # Performance per cost unit
            cost_efficiency.append((model, efficiency, estimated_cost))
        
        for model, efficiency, cost in sorted(cost_efficiency, key=lambda x: x[1], reverse=True):
            report.append(f"      💡 {model}: {efficiency:.1f} (Est. ${cost:.3f}/search)")
        
        # Spezialisierung (welches Modell für welche Felder am besten)
        field_specialists = defaultdict(list)
        for field_name, field_data in analysis['field_consistency'].items():
            if field_data['total_values'] >= 3:  # Nur Felder mit genug Daten
                best_models = field_data['models_contributing'][:2]  # Top 2 Modelle
                for model in best_models:
                    field_specialists[model].append(field_name)
        
        if field_specialists:
            report.append(f"\n🎯 FIELD SPECIALIZATION:")
            for model, fields in field_specialists.items():
                if len(fields) >= 3:  # Nur wenn Modell bei mehreren Feldern gut ist
                    report.append(f"   🏅 {model}: Best for {', '.join(fields[:3])}{'...' if len(fields) > 3 else ''}")
        
        return "\n".join(report)
    
    def save_analysis(self, mine_name: str, output_dir: str = "/app"):
        """Speichere erweiterte Analyse"""
        analysis = self.analyze_mine_consistency(mine_name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON mit erweiterten Daten speichern
        json_filename = f"{output_dir}/normalized_mine_analysis_{mine_name.replace(' ', '_')}_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        
        # Umfassenden Bericht speichern
        report = self.generate_comprehensive_report(mine_name)
        txt_filename = f"{output_dir}/normalized_mine_report_{mine_name.replace(' ', '_')}_{timestamp}.txt"
        with open(txt_filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"📄 NORMALISIERTE Analyse gespeichert:")
        print(f"   JSON: {json_filename}")
        print(f"   Bericht: {txt_filename}")
        
        return json_filename, txt_filename

def main():
    """Hauptfunktion"""
    evaluator = NormalizedModelEvaluationSystem()
    
    mine_name = "Sigma Mine"
    
    print("🚀 NORMALIZED MINE MODEL EVALUATION SYSTEM")
    print("=" * 60)
    print("🎯 Features: Consistency Analysis, Quality Metrics, Cost-Efficiency, Field Specialization")
    
    # Generiere und zeige Bericht
    report = evaluator.generate_comprehensive_report(mine_name)
    print(report)
    
    # Speichere detaillierte Analyse
    evaluator.save_analysis(mine_name)
    
    print(f"\n🏁 EVALUATION COMPLETED!")

if __name__ == "__main__":
    main()