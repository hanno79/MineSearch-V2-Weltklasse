#!/usr/bin/env python3
"""
Author: rahn
Datum: 02.08.2025
Version: 1.0
Beschreibung: Erfolgsraten-Korrektur basierend auf echten structured_data
"""

import sqlite3
import json
from collections import defaultdict
from datetime import datetime

class SuccessRateCalculator:
    """Berechnet realistische Erfolgsraten basierend auf structured_data"""
    
    def __init__(self, db_path: str = 'mines.db'):
        self.db_path = db_path
    
    def calculate_real_success_rate(self, model_id: str) -> dict:
        """
        Berechnet echte Erfolgsrate basierend auf structured_data Verfügbarkeit
        
        Returns:
            Dict mit success_rate und data_success_rate
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Hole alle Suchergebnisse für dieses Modell
        cursor.execute('''
            SELECT success, structured_data, sources
            FROM search_results 
            WHERE model_used = ?
        ''', (model_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        if not results:
            return {'success_rate': 0.0, 'data_success_rate': 0.0, 'total_searches': 0}
        
        total_searches = len(results)
        basic_success_count = 0
        data_success_count = 0
        
        for success, structured_data, sources in results:
            # Basic Success: success=1 in DB
            if success == 1:
                basic_success_count += 1
            
            # Data Success: success=1 AND structured_data vorhanden und verwertbar
            if success == 1 and structured_data:
                try:
                    parsed_data = json.loads(structured_data)
                    # Prüfe ob verwertbare Daten vorhanden (mindestens 2 Felder mit Inhalt)
                    useful_fields = 0
                    for field_name, field_value in parsed_data.items():
                        if (field_value and 
                            isinstance(field_value, str) and 
                            field_value not in ['', 'N/A', 'X', 'null', 'noch aktiv']):
                            useful_fields += 1
                    
                    if useful_fields >= 2:  # Mindestens 2 verwertbare Felder
                        data_success_count += 1
                        
                except (json.JSONDecodeError, TypeError):
                    # Structured data nicht parsebar -> kein Data Success
                    pass
        
        basic_success_rate = basic_success_count / total_searches
        data_success_rate = data_success_count / total_searches
        
        return {
            'success_rate': basic_success_rate,
            'data_success_rate': data_success_rate,
            'total_searches': total_searches,
            'basic_successes': basic_success_count,
            'data_successes': data_success_count
        }
    
    def update_model_summary_success_rates(self, model_id: str) -> dict:
        """
        Aktualisiert model_summary mit korrekten Erfolgsraten
        """
        rates = self.calculate_real_success_rate(model_id)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Update model_summary mit echten Erfolgsraten
        cursor.execute('''
            UPDATE model_summary 
            SET success_rate = ?,
                data_success_rate = ?
            WHERE model_id = ?
        ''', (rates['success_rate'], rates['data_success_rate'], model_id))
        
        conn.commit()
        conn.close()
        
        return rates
    
    def update_all_success_rates(self) -> list:
        """
        Aktualisiert Erfolgsraten für alle Modelle
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Hole alle Modelle mit Daten
        cursor.execute('''
            SELECT DISTINCT model_used, COUNT(*) as search_count
            FROM search_results 
            WHERE model_used IS NOT NULL
            GROUP BY model_used
            ORDER BY search_count DESC
        ''')
        
        models = cursor.fetchall()
        conn.close()
        
        results = []
        
        for model_id, search_count in models:
            print(f"🔄 Aktualisiere Erfolgsraten für {model_id} ({search_count} Suchen)...")
            
            rates = self.update_model_summary_success_rates(model_id)
            
            basic_pct = rates['success_rate'] * 100
            data_pct = rates['data_success_rate'] * 100
            
            print(f"   ✅ Basic Success: {basic_pct:.1f}% ({rates['basic_successes']}/{rates['total_searches']})")
            print(f"   ✅ Data Success: {data_pct:.1f}% ({rates['data_successes']}/{rates['total_searches']})")
            
            if rates['success_rate'] == 0.0:
                print(f"   ⚠️  PROBLEM: Keine erfolgreichen Suchen!")
            elif rates['data_success_rate'] == 0.0:
                print(f"   ⚠️  PROBLEM: Keine verwertbaren Daten!")
            elif rates['data_success_rate'] < rates['success_rate'] * 0.5:
                print(f"   ⚠️  WARNUNG: Niedrige Datenqualität!")
            
            results.append({
                'model_id': model_id,
                **rates
            })
        
        return results

def main():
    """Hauptfunktion für Erfolgsraten-Korrektur"""
    
    print('🔧 ERFOLGSRATEN-KORREKTUR GESTARTET')
    print('=' * 50)
    print('Author: rahn | Datum: 02.08.2025 | Version: 1.0')
    print('Zweck: Korrekte Berechnung der Erfolgsraten')
    print('=' * 50)
    
    calculator = SuccessRateCalculator()
    
    # Aktualisiere alle Modelle
    results = calculator.update_all_success_rates()
    
    print(f'\n📊 ZUSAMMENFASSUNG:')
    print(f'   Aktualisierte Modelle: {len(results)}')
    
    # Zeige Statistiken
    if results:
        basic_rates = [r['success_rate'] for r in results]
        data_rates = [r['data_success_rate'] for r in results]
        
        avg_basic = sum(basic_rates) / len(basic_rates) * 100
        avg_data = sum(data_rates) / len(data_rates) * 100
        
        print(f'   Durchschnittliche Basic Success Rate: {avg_basic:.1f}%')
        print(f'   Durchschnittliche Data Success Rate: {avg_data:.1f}%')
        
        # Modelle ohne Erfolg
        failed_models = [r for r in results if r['success_rate'] == 0.0]
        if failed_models:
            print(f'\n❌ Modelle ohne Erfolg ({len(failed_models)}):')
            for model in failed_models[:5]:  # Zeige erste 5
                print(f'      • {model["model_id"]}')
        
        # Modelle mit hoher Erfolgsrate
        successful_models = [r for r in results if r['data_success_rate'] >= 0.8]
        print(f'\n✅ Modelle mit hoher Daten-Erfolgsrate (≥80%): {len(successful_models)}')
        
        if successful_models:
            print(f'   Top Performer:')
            for model in sorted(successful_models, key=lambda x: x['data_success_rate'], reverse=True)[:5]:
                data_pct = model['data_success_rate'] * 100
                print(f'      • {model["model_id"]}: {data_pct:.1f}%')
    
    print('\n🎉 ERFOLGSRATEN-KORREKTUR ABGESCHLOSSEN!')

if __name__ == "__main__":
    main()