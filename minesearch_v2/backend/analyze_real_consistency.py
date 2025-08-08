#!/usr/bin/env python3
"""
Author: rahn
Datum: 02.08.2025
Version: 1.0
Beschreibung: Analysiert echte Feld-Konsistenz in der Datenbank
"""

import sqlite3
from collections import defaultdict
from typing import Dict, List, Tuple

def analyze_field_consistency():
    """Analysiert echte Feld-Konsistenz pro Modell"""
    
    conn = sqlite3.connect('mines.db')
    cursor = conn.cursor()
    
    print('🔍 ECHTE FELD-KONSISTENZ-ANALYSE')
    print('=' * 60)
    
    # Hole verfügbare Modelle
    cursor.execute('SELECT DISTINCT model_id FROM model_statistics LIMIT 5')
    models = [row[0] for row in cursor.fetchall()]
    
    print(f"📋 Analysiere {len(models)} Modelle:")
    for model in models:
        print(f"  • {model}")
    
    print('\n' + '=' * 60)
    
    # Analysiere jedes Modell
    for model_id in models:
        print(f'\n🤖 MODELL: {model_id}')
        print('-' * 50)
        
        # Hole alle Feld-Werte für dieses Modell
        cursor.execute('''
            SELECT field_name, field_value, COUNT(*) as frequency
            FROM model_statistics 
            WHERE model_id = ?
            GROUP BY field_name, field_value
            ORDER BY field_name, frequency DESC
        ''', (model_id,))
        
        results = cursor.fetchall()
        
        # Gruppiere nach Feldern
        fields_data = defaultdict(list)
        for field_name, field_value, frequency in results:
            fields_data[field_name].append((field_value, frequency))
        
        # Berechne Konsistenz pro Feld
        field_consistencies = {}
        
        for field_name, values in fields_data.items():
            if not values:
                continue
                
            total_entries = sum(frequency for _, frequency in values)
            most_frequent_count = values[0][1]  # Bereits sortiert nach frequency DESC
            most_frequent_value = values[0][0]
            
            # Echte Konsistenz = Häufigster Wert / Gesamt Einträge
            consistency_percent = (most_frequent_count / total_entries) * 100
            field_consistencies[field_name] = consistency_percent
            
            # Zeige Details nur für wichtige Felder
            important_fields = ['Country', 'Land', 'Region', 'Mine', 'Aktivitätsstatus', 'Rohstoffe']
            if field_name in important_fields:
                print(f'📊 {field_name}:')
                print(f'   Konsistenz: {consistency_percent:.1f}%')
                print(f'   Häufigster Wert: "{most_frequent_value}" ({most_frequent_count}/{total_entries})')
                
                # Zeige alle Varianten wenn < 100%
                if consistency_percent < 100 and len(values) > 1:
                    print(f'   Varianten:')
                    for value, freq in values[:3]:  # Top 3
                        percent = (freq / total_entries) * 100
                        print(f'     • "{value}": {freq}x ({percent:.1f}%)')
                print()
        
        # Berechne Overall-Konsistenz (Durchschnitt aller Felder)
        if field_consistencies:
            overall_consistency = sum(field_consistencies.values()) / len(field_consistencies)
            print(f'🎯 GESAMT-KONSISTENZ: {overall_consistency:.1f}%')
            print(f'   Basierend auf {len(field_consistencies)} Feldern')
            
            # Zeige problematische Felder (< 90% Konsistenz)
            problematic_fields = {k: v for k, v in field_consistencies.items() if v < 90}
            if problematic_fields:
                print(f'\n⚠️  PROBLEMATISCHE FELDER (< 90% Konsistenz):')
                for field, consistency in sorted(problematic_fields.items(), key=lambda x: x[1]):
                    print(f'     • {field}: {consistency:.1f}%')
        
        print('\n' + '=' * 60)
    
    conn.close()

def compare_current_vs_real_consistency():
    """Vergleicht aktuelle Konsistenz-Berechnung mit realer Konsistenz"""
    
    conn = sqlite3.connect('mines.db')
    cursor = conn.cursor()
    
    print('\n🔍 VERGLEICH: AKTUELLE vs. ECHTE KONSISTENZ')
    print('=' * 60)
    
    # Hole aktuelle Konsistenz aus model_summary
    cursor.execute('''
        SELECT model_id, overall_consistency
        FROM model_summary 
        WHERE overall_consistency IS NOT NULL
        LIMIT 5
    ''')
    
    current_consistencies = cursor.fetchall()
    
    for model_id, current_consistency in current_consistencies:
        print(f'\n📊 {model_id}:')
        print(f'  Aktuelle Konsistenz (model_summary): {current_consistency * 100:.1f}%')
        
        # Berechne echte Konsistenz
        cursor.execute('''
            SELECT field_name, field_value, COUNT(*) as frequency
            FROM model_statistics 
            WHERE model_id = ?
            GROUP BY field_name, field_value
            ORDER BY field_name, frequency DESC
        ''', (model_id,))
        
        results = cursor.fetchall()
        fields_data = defaultdict(list)
        for field_name, field_value, frequency in results:
            fields_data[field_name].append((field_value, frequency))
        
        field_consistencies = []
        for field_name, values in fields_data.items():
            if values:
                total_entries = sum(frequency for _, frequency in values)
                most_frequent_count = values[0][1]
                consistency_percent = (most_frequent_count / total_entries) * 100
                field_consistencies.append(consistency_percent)
        
        if field_consistencies:
            real_consistency = sum(field_consistencies) / len(field_consistencies)
            print(f'  Echte Konsistenz (berechnet):     {real_consistency:.1f}%')
            print(f'  Differenz:                        {abs(current_consistency * 100 - real_consistency):.1f}%')
            
            if abs(current_consistency * 100 - real_consistency) > 10:
                print(f'  ⚠️  GROSSE ABWEICHUNG!')
    
    conn.close()

if __name__ == "__main__":
    analyze_field_consistency()
    compare_current_vs_real_consistency()