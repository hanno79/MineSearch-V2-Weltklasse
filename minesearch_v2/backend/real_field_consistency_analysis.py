#!/usr/bin/env python3
"""
Author: rahn
Datum: 02.08.2025
Version: 1.0
Beschreibung: Analysiert echte Feld-Konsistenz basierend auf structured_data
"""

import sqlite3
import json
from collections import defaultdict
from typing import Dict, List, Tuple

def analyze_real_field_consistency():
    """Analysiert echte Feld-Konsistenz aus structured_data"""
    
    conn = sqlite3.connect('mines.db')
    cursor = conn.cursor()
    
    print('🔍 ECHTE FELD-KONSISTENZ-ANALYSE (structured_data)')
    print('=' * 70)
    
    # Hole Test-Modell
    test_model = 'openrouter:deepseek-chimera-free'
    
    cursor.execute('''
        SELECT structured_data, mine_name
        FROM model_statistics 
        WHERE model_id = ? AND structured_data IS NOT NULL AND success = 1
        LIMIT 20
    ''', (test_model,))
    
    results = cursor.fetchall()
    
    if not results:
        print(f"❌ Keine structured_data für {test_model} gefunden")
        return
    
    print(f"📊 Analysiere {len(results)} erfolgreiche Suchen für: {test_model}")
    print()
    
    # Sammle alle Feld-Werte
    field_values = defaultdict(list)
    
    for structured_data_json, mine_name in results:
        try:
            if structured_data_json:
                structured_data = json.loads(structured_data_json)
                
                # Durchsuche alle Felder in structured_data
                for field_name, field_value in structured_data.items():
                    if field_value and field_value not in ['', 'N/A', 'X', 'noch aktiv']:
                        field_values[field_name].append(field_value)
                        
        except json.JSONDecodeError:
            continue
    
    # Berechne Konsistenz pro Feld
    print("📋 FELD-KONSISTENZ-ANALYSE:")
    print("-" * 50)
    
    total_consistency_scores = []
    
    for field_name in sorted(field_values.keys()):
        values = field_values[field_name]
        
        if not values:
            continue
            
        # Zähle Häufigkeiten
        value_counts = defaultdict(int)
        for value in values:
            value_counts[value] += 1
        
        # Finde häufigsten Wert
        most_common_value = max(value_counts.items(), key=lambda x: x[1])
        most_common_count = most_common_value[1]
        most_common_text = most_common_value[0]
        
        # Berechne Konsistenz
        total_entries = len(values)
        consistency_percent = (most_common_count / total_entries) * 100
        total_consistency_scores.append(consistency_percent)
        
        print(f"🔸 {field_name}:")
        print(f"   Konsistenz: {consistency_percent:.1f}%")
        print(f"   Häufigster Wert: '{most_common_text}' ({most_common_count}/{total_entries})")
        
        # Zeige Varianten wenn nicht 100% konsistent
        if consistency_percent < 100 and len(value_counts) > 1:
            print(f"   Alle Varianten:")
            for value, count in sorted(value_counts.items(), key=lambda x: x[1], reverse=True):
                percent = (count / total_entries) * 100
                print(f"     • '{value}': {count}x ({percent:.1f}%)")
        print()
    
    # Berechne Gesamt-Konsistenz
    if total_consistency_scores:
        overall_consistency = sum(total_consistency_scores) / len(total_consistency_scores)
        print(f"🎯 GESAMT-KONSISTENZ (Modell {test_model}): {overall_consistency:.1f}%")
        print(f"   Basierend auf {len(total_consistency_scores)} Feldern")
        
        # Identifiziere problematische Felder
        low_consistency_fields = []
        for field_name in sorted(field_values.keys()):
            values = field_values[field_name]
            if values:
                value_counts = defaultdict(int)
                for value in values:
                    value_counts[value] += 1
                most_common_count = max(value_counts.values())
                consistency = (most_common_count / len(values)) * 100
                
                if consistency < 90:
                    low_consistency_fields.append((field_name, consistency))
        
        if low_consistency_fields:
            print(f"\n⚠️  FELDER MIT NIEDRIGER KONSISTENZ (< 90%):")
            for field_name, consistency in sorted(low_consistency_fields, key=lambda x: x[1]):
                print(f"     • {field_name}: {consistency:.1f}%")
        else:
            print(f"\n✅ Alle Felder haben >= 90% Konsistenz")
    
    # Vergleiche mit aktueller model_summary
    cursor.execute('''
        SELECT overall_consistency 
        FROM model_summary 
        WHERE model_id = ?
    ''', (test_model,))
    
    current_result = cursor.fetchone()
    if current_result:
        current_consistency = current_result[0] * 100
        print(f"\n📊 VERGLEICH:")
        print(f"   Aktuelle model_summary Konsistenz: {current_consistency:.1f}%")
        print(f"   Echte berechnete Konsistenz:       {overall_consistency:.1f}%")
        print(f"   Abweichung:                        {abs(current_consistency - overall_consistency):.1f}%")
        
        if abs(current_consistency - overall_consistency) > 20:
            print(f"   ⚠️  GROSSE ABWEICHUNG - Konsistenz-Algorithmus fehlerhaft!")
        elif current_consistency == 100.0 and overall_consistency < 95:
            print(f"   ⚠️  100% Konsistenz unrealistisch - echte Konsistenz ist niedriger!")
    
    conn.close()

def test_multiple_models():
    """Teste mehrere Modelle auf realistische Konsistenz"""
    
    conn = sqlite3.connect('mines.db')
    cursor = conn.cursor()
    
    print('\n🔍 MULTI-MODELL KONSISTENZ-TEST')
    print('=' * 50)
    
    # Hole Top 5 Modelle mit Daten
    cursor.execute('''
        SELECT model_id, COUNT(*) as count
        FROM model_statistics 
        WHERE structured_data IS NOT NULL AND success = 1
        GROUP BY model_id
        ORDER BY count DESC
        LIMIT 5
    ''')
    
    models = cursor.fetchall()
    
    for model_id, count in models:
        print(f"\n📊 {model_id} ({count} erfolgreiche Suchen):")
        
        # Berechne echte Konsistenz für dieses Modell
        cursor.execute('''
            SELECT structured_data
            FROM model_statistics 
            WHERE model_id = ? AND structured_data IS NOT NULL AND success = 1
            LIMIT 15
        ''', (model_id,))
        
        results = cursor.fetchall()
        field_values = defaultdict(list)
        
        for (structured_data_json,) in results:
            try:
                if structured_data_json:
                    structured_data = json.loads(structured_data_json)
                    for field_name, field_value in structured_data.items():
                        if field_value and field_value not in ['', 'N/A', 'X']:
                            field_values[field_name].append(field_value)
            except:
                continue
        
        if field_values:
            consistency_scores = []
            for field_name, values in field_values.items():
                if values:
                    value_counts = defaultdict(int)
                    for value in values:
                        value_counts[value] += 1
                    most_common_count = max(value_counts.values())
                    consistency = (most_common_count / len(values)) * 100
                    consistency_scores.append(consistency)
            
            if consistency_scores:
                avg_consistency = sum(consistency_scores) / len(consistency_scores)
                print(f"   Echte Konsistenz: {avg_consistency:.1f}%")
                
                # Hole aktuelle model_summary Konsistenz
                cursor.execute('SELECT overall_consistency FROM model_summary WHERE model_id = ?', (model_id,))
                current = cursor.fetchone()
                if current:
                    current_consistency = current[0] * 100
                    print(f"   model_summary:    {current_consistency:.1f}%")
                    if current_consistency == 100.0 and avg_consistency < 95:
                        print(f"   ⚠️  UNREALISTISCH - sollte {avg_consistency:.1f}% sein")
    
    conn.close()

if __name__ == "__main__":
    analyze_real_field_consistency()
    test_multiple_models()