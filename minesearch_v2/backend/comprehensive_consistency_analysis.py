#!/usr/bin/env python3
"""
Author: rahn
Datum: 02.08.2025
Version: 1.0
Beschreibung: Umfassende Analyse der echten Feld-Konsistenz aus search_results
"""

import sqlite3
import json
from collections import defaultdict, Counter
from typing import Dict, List, Tuple

def analyze_real_field_consistency():
    """Analysiert echte Feld-Konsistenz aus search_results structured_data"""
    
    conn = sqlite3.connect('mines.db')
    cursor = conn.cursor()
    
    print('🔍 COMPREHENSIVE FELD-KONSISTENZ-ANALYSE')
    print('=' * 70)
    
    # Sammle alle Daten pro Modell
    cursor.execute('''
        SELECT model_used, mine_name, structured_data
        FROM search_results 
        WHERE structured_data IS NOT NULL AND success = 1
        ORDER BY model_used, mine_name
    ''')
    
    all_results = cursor.fetchall()
    print(f"📊 Analysiere {len(all_results)} erfolgreiche Suchen")
    
    # Gruppiere nach Modell
    model_data = defaultdict(lambda: defaultdict(list))
    
    for model_used, mine_name, structured_data_json in all_results:
        try:
            structured_data = json.loads(structured_data_json)
            
            for field_name, field_value in structured_data.items():
                # Filtere leere/unwichtige Werte
                if field_value and field_value not in ['', 'N/A', 'X', 'null', 'noch aktiv']:
                    model_data[model_used][field_name].append(field_value)
                    
        except json.JSONDecodeError:
            continue
    
    print(f"\n📋 Gefunden: {len(model_data)} Modelle mit verwertbaren Daten")
    
    # Analysiere jedes Modell
    model_consistency_results = {}
    
    for model_id in sorted(model_data.keys())[:5]:  # Top 5 Modelle
        fields = model_data[model_id]
        
        print(f"\n🤖 MODELL: {model_id}")
        print("-" * 50)
        
        field_consistency_scores = []
        field_details = {}
        
        for field_name in sorted(fields.keys()):
            values = fields[field_name]
            
            if len(values) < 2:  # Mindestens 2 Werte für Konsistenz-Berechnung
                continue
            
            # Zähle Häufigkeiten
            value_counts = Counter(values)
            total_values = len(values)
            most_common_value, most_common_count = value_counts.most_common(1)[0]
            
            # Berechne echte Konsistenz
            consistency_percent = (most_common_count / total_values) * 100
            field_consistency_scores.append(consistency_percent)
            
            field_details[field_name] = {
                'consistency': consistency_percent,
                'most_common': most_common_value,
                'total_values': total_values,
                'unique_values': len(value_counts),
                'variants': dict(value_counts.most_common(3))
            }
            
            # Zeige Details für wichtige Felder
            important_fields = ['Country', 'Land', 'Region', 'Mine', 'Aktivitätsstatus', 'Rohstoffe', 'Betreiber']
            if field_name in important_fields:
                print(f"📊 {field_name}:")
                print(f"   Konsistenz: {consistency_percent:.1f}%")
                print(f"   Häufigster Wert: '{most_common_value}' ({most_common_count}/{total_values})")
                
                if consistency_percent < 100:
                    print(f"   Varianten:")
                    for value, count in value_counts.most_common(3):
                        percent = (count / total_values) * 100
                        print(f"     • '{value}': {count}x ({percent:.1f}%)")
                print()
        
        # Berechne Gesamt-Konsistenz für dieses Modell
        if field_consistency_scores:
            overall_consistency = sum(field_consistency_scores) / len(field_consistency_scores)
            model_consistency_results[model_id] = {
                'overall_consistency': overall_consistency,
                'field_details': field_details,
                'analyzed_fields': len(field_consistency_scores)
            }
            
            print(f"🎯 GESAMT-KONSISTENZ: {overall_consistency:.1f}%")
            print(f"   Basierend auf {len(field_consistency_scores)} Feldern")
            
            # Identifiziere problematische Felder
            low_consistency_fields = [(name, details['consistency']) 
                                    for name, details in field_details.items() 
                                    if details['consistency'] < 90]
            
            if low_consistency_fields:
                print(f"\n⚠️  PROBLEMATISCHE FELDER (< 90% Konsistenz):")
                for field_name, consistency in sorted(low_consistency_fields, key=lambda x: x[1]):
                    print(f"     • {field_name}: {consistency:.1f}%")
            else:
                print(f"\n✅ Alle analysierten Felder haben >= 90% Konsistenz")
        
        print("\n" + "=" * 70)
    
    # Vergleiche mit aktueller model_summary
    print("\n🔍 VERGLEICH MIT AKTUELLER MODEL_SUMMARY:")
    print("=" * 50)
    
    for model_id, results in model_consistency_results.items():
        cursor.execute('''
            SELECT overall_consistency 
            FROM model_summary 
            WHERE model_id = ?
        ''', (model_id,))
        
        current_result = cursor.fetchone()
        if current_result:
            current_consistency = current_result[0] * 100
            real_consistency = results['overall_consistency']
            
            print(f"\n📊 {model_id}:")
            print(f"   model_summary Konsistenz: {current_consistency:.1f}%")
            print(f"   Echte Konsistenz:         {real_consistency:.1f}%")
            print(f"   Abweichung:               {abs(current_consistency - real_consistency):.1f}%")
            
            if current_consistency == 100.0 and real_consistency < 95:
                print(f"   ⚠️  100% UNREALISTISCH - echte Konsistenz ist {real_consistency:.1f}%!")
            elif abs(current_consistency - real_consistency) > 20:
                print(f"   ⚠️  GROSSE ABWEICHUNG - Algorithmus fehlerhaft!")
            else:
                print(f"   ✅ Konsistenz-Berechnung akzeptabel")
    
    conn.close()
    return model_consistency_results

def analyze_field_level_consistency():
    """Analysiert Feld-spezifische Konsistenz für Detail-Modals"""
    
    conn = sqlite3.connect('mines.db')
    cursor = conn.cursor()
    
    print('\n🔍 FELD-SPEZIFISCHE KONSISTENZ-ANALYSE')
    print('=' * 50)
    
    # Analysiere häufige Felder
    cursor.execute('''
        SELECT model_used, structured_data
        FROM search_results 
        WHERE structured_data IS NOT NULL AND success = 1
        AND model_used = 'openrouter:deepseek-free'
        LIMIT 20
    ''')
    
    results = cursor.fetchall()
    
    if not results:
        print("❌ Keine Daten für Detail-Analyse gefunden")
        return
    
    # Sammle alle Feld-Werte
    all_fields = defaultdict(list)
    
    for model_used, structured_data_json in results:
        try:
            structured_data = json.loads(structured_data_json)
            for field_name, field_value in structured_data.items():
                if field_value and field_value not in ['', 'N/A', 'X', 'null']:
                    all_fields[field_name].append(field_value)
        except:
            continue
    
    print(f"📊 Analyse für openrouter:deepseek-free ({len(results)} Suchen):")
    print("\n📋 FELD-SPEZIFISCHE KONSISTENZ für Detail-Modal:")
    
    field_consistency_data = {}
    
    for field_name in sorted(all_fields.keys()):
        values = all_fields[field_name]
        
        if len(values) < 2:
            continue
            
        value_counts = Counter(values)
        total_values = len(values)
        most_common_value, most_common_count = value_counts.most_common(1)[0]
        consistency_percent = (most_common_count / total_values) * 100
        
        field_consistency_data[field_name] = {
            'consistency_percent': consistency_percent,
            'most_common_value': most_common_value,
            'most_common_count': most_common_count,
            'total_values': total_values,
            'unique_values': len(value_counts),
            'value_distribution': dict(value_counts)
        }
        
        print(f"\n🔸 {field_name}:")
        print(f"   Konsistenz: {consistency_percent:.1f}%")
        print(f"   Häufigster Wert: '{most_common_value}' ({most_common_count}/{total_values})")
        
        if consistency_percent < 100:
            print(f"   Alle Varianten:")
            for value, count in value_counts.most_common():
                percent = (count / total_values) * 100
                print(f"     • '{value}': {count}x ({percent:.1f}%)")
    
    # Generiere JSON für Frontend
    with open('/app/minesearch_v2/frontend/field_consistency_data.json', 'w') as f:
        json.dump(field_consistency_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Feld-Konsistenz-Daten gespeichert: field_consistency_data.json")
    
    conn.close()
    return field_consistency_data

if __name__ == "__main__":
    model_results = analyze_real_field_consistency()
    field_results = analyze_field_level_consistency()