#!/usr/bin/env python3
"""
Author: rahn
Datum: 02.08.2025
Version: 1.0
Beschreibung: Korrekte Konsistenz-Berechnung basierend auf echten Feld-Werten
"""

import sqlite3
import json
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Optional
from datetime import datetime

class FixedConsistencyCalculator:
    """Berechnet realistische Feld-Konsistenz basierend auf echten Werten"""
    
    def __init__(self, db_path: str = 'mines.db'):
        self.db_path = db_path
    
    def calculate_field_consistency(self, model_id: str) -> Dict[str, float]:
        """
        Berechnet echte Feld-Konsistenz für ein Modell
        
        Returns:
            Dict mit field_name -> consistency_percentage
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Hole alle structured_data für dieses Modell
        cursor.execute('''
            SELECT structured_data
            FROM search_results 
            WHERE model_used = ? AND structured_data IS NOT NULL AND success = 1
        ''', (model_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        if not results:
            return {}
        
        # Sammle alle Feld-Werte
        field_values = defaultdict(list)
        
        for (structured_data_json,) in results:
            try:
                structured_data = json.loads(structured_data_json)
                
                for field_name, field_value in structured_data.items():
                    # Filtere nur sinnvolle Werte
                    if (field_value and 
                        isinstance(field_value, str) and 
                        field_value not in ['', 'N/A', 'X', 'null', 'noch aktiv']):
                        field_values[field_name].append(field_value.strip())
                        
            except (json.JSONDecodeError, TypeError):
                continue
        
        # Berechne Konsistenz pro Feld
        field_consistencies = {}
        
        for field_name, values in field_values.items():
            if len(values) < 2:  # Mindestens 2 Werte für Konsistenz-Berechnung
                continue
            
            # Zähle Häufigkeiten
            value_counts = Counter(values)
            total_values = len(values)
            most_common_count = value_counts.most_common(1)[0][1]
            
            # Echte Konsistenz = Häufigster Wert / Gesamt Werte
            consistency_percent = (most_common_count / total_values) * 100
            field_consistencies[field_name] = consistency_percent
        
        return field_consistencies
    
    def calculate_overall_consistency(self, field_consistencies: Dict[str, float]) -> float:
        """
        Berechnet Gesamt-Konsistenz als gewichteten Durchschnitt
        
        Wichtige Felder bekommen höhere Gewichtung
        """
        if not field_consistencies:
            return 0.0
        
        # Feld-Gewichtungen (wichtige Felder höher gewichtet)
        field_weights = {
            'Mine': 1.0,
            'Land': 0.9,
            'Country': 0.9,
            'Region': 0.8,
            'Aktivitätsstatus': 0.7,
            'Rohstoffe': 0.6,
            'Betreiber': 0.5,
            'Eigentümer': 0.4,
            # Alle anderen Felder: 0.3
        }
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        for field_name, consistency in field_consistencies.items():
            weight = field_weights.get(field_name, 0.3)  # Default-Gewichtung
            weighted_sum += consistency * weight
            total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    def update_model_summary_consistency(self, model_id: str) -> Dict[str, any]:
        """
        Aktualisiert model_summary mit korrekter Konsistenz-Berechnung
        """
        # Berechne echte Konsistenz
        field_consistencies = self.calculate_field_consistency(model_id)
        overall_consistency = self.calculate_overall_consistency(field_consistencies)
        
        # Aktualisiere Datenbank
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Erstelle detaillierte Feld-Informationen
        field_details = {
            "field_consistency_details": field_consistencies,
            "calculation_method": "real_field_value_analysis",
            "calculation_timestamp": datetime.now().isoformat(),
            "analyzed_fields": len(field_consistencies)
        }
        
        # Update model_summary
        cursor.execute('''
            UPDATE model_summary 
            SET overall_consistency = ?,
                critical_fields_consistency = ?
            WHERE model_id = ?
        ''', (overall_consistency / 100, json.dumps(field_details), model_id))
        
        conn.commit()
        conn.close()
        
        return {
            'model_id': model_id,
            'overall_consistency': overall_consistency,
            'field_consistencies': field_consistencies,
            'field_details': field_details
        }
    
    def update_all_models(self) -> List[Dict[str, any]]:
        """
        Aktualisiert Konsistenz für alle Modelle
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Hole alle Modelle mit Daten
        cursor.execute('''
            SELECT DISTINCT model_used, COUNT(*) as count
            FROM search_results 
            WHERE structured_data IS NOT NULL AND success = 1
            GROUP BY model_used
            ORDER BY count DESC
        ''')
        
        models = cursor.fetchall()
        conn.close()
        
        results = []
        
        for model_id, count in models:
            print(f"🔄 Aktualisiere Konsistenz für {model_id} ({count} Suchen)...")
            
            result = self.update_model_summary_consistency(model_id)
            results.append(result)
            
            print(f"   ✅ Neue Konsistenz: {result['overall_consistency']:.1f}%")
            
            # Zeige problematische Felder
            low_consistency_fields = [
                (field, consistency) for field, consistency in result['field_consistencies'].items()
                if consistency < 90
            ]
            
            if low_consistency_fields:
                print(f"   ⚠️  Problematische Felder:")
                for field, consistency in sorted(low_consistency_fields, key=lambda x: x[1]):
                    print(f"      • {field}: {consistency:.1f}%")
        
        return results

def main():
    """Hauptfunktion für Konsistenz-Korrektur"""
    
    print('🔧 KONSISTENZ-KORREKTUR GESTARTET')
    print('=' * 50)
    print('Author: rahn | Datum: 02.08.2025 | Version: 1.0')
    print('Zweck: Korrekte Berechnung der Feld-Konsistenz')
    print('=' * 50)
    
    calculator = FixedConsistencyCalculator()
    
    # Aktualisiere alle Modelle
    results = calculator.update_all_models()
    
    print(f'\n📊 ZUSAMMENFASSUNG:')
    print(f'   Aktualisierte Modelle: {len(results)}')
    
    # Zeige Statistiken
    consistencies = [r['overall_consistency'] for r in results]
    if consistencies:
        avg_consistency = sum(consistencies) / len(consistencies)
        min_consistency = min(consistencies)
        max_consistency = max(consistencies)
        
        print(f'   Durchschnittliche Konsistenz: {avg_consistency:.1f}%')
        print(f'   Niedrigste Konsistenz: {min_consistency:.1f}%')
        print(f'   Höchste Konsistenz: {max_consistency:.1f}%')
        
        # Modelle mit unrealistisch hoher Konsistenz
        high_consistency_models = [r for r in results if r['overall_consistency'] > 95]
        if high_consistency_models:
            print(f'\n⚠️  Modelle mit möglicherweise zu hoher Konsistenz (> 95%):')
            for model in high_consistency_models:
                print(f'      • {model["model_id"]}: {model["overall_consistency"]:.1f}%')
        
        # Modelle mit realistischer Konsistenz
        realistic_models = [r for r in results if 60 <= r['overall_consistency'] <= 95]
        print(f'\n✅ Modelle mit realistischer Konsistenz (60-95%): {len(realistic_models)}')
    
    print('\n🎉 KONSISTENZ-KORREKTUR ABGESCHLOSSEN!')

if __name__ == "__main__":
    main()