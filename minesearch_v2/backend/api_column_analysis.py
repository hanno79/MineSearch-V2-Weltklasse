#!/usr/bin/env python3
"""
Author: rahn
Datum: 30.07.2025
Version: 1.0
Beschreibung: API-Datenanalyse - Spalten der konsolidierten Ergebnisse vs. Frontend-Konfiguration
"""

import requests
import json
from collections import Counter

def analyze_api_columns():
    """Analysiere die Spalten aus der API und vergleiche mit Frontend-Konfiguration"""
    
    print("🔍 FRONTEND DISPLAY SPECIALIST AGENT - API COLUMN ANALYSIS")
    print("=" * 70)
    
    try:
        # Hole konsolidierte Daten von API
        print("📡 Lade konsolidierte Daten von API...")
        response = requests.get('http://localhost:8000/api/results/consolidated')
        data = response.json()
        
        if not data.get('success'):
            print(f"❌ API-Fehler: {data.get('message', 'Unbekannter Fehler')}")
            return
        
        consolidated_results = data['data']['consolidated_results']
        print(f"✅ {len(consolidated_results)} konsolidierte Ergebnisse geladen")
        
        # Analysiere verfügbare Spalten
        if consolidated_results:
            first_result = consolidated_results[0]
            print(f"\n📊 STRUKTUR DES ERSTEN ERGEBNISSES:")
            print(f"Mine Name: {first_result.get('mine_name')}")
            print(f"Country: {first_result.get('country')}")
            print(f"Region: {first_result.get('region')}")
            
            # Analysiere best_values
            best_values = first_result.get('best_values', {})
            print(f"\n🎯 VERFÜGBARE BEST_VALUES SPALTEN ({len(best_values)}):")
            
            api_columns = []
            for i, (key, value) in enumerate(best_values.items(), 1):
                print(f"  {i:2d}. {key}: {str(value)[:50]}{'...' if len(str(value)) > 50 else ''}")
                api_columns.append(key)
            
            # Frontend-Konfiguration aus results-display.js
            frontend_columns = [
                'mine_name', 'country', 'region', 'overall_confidence', 'model_count', 'last_updated',
                'Betreiber', 'Eigentümer', 'Rohstoffe', 'Minentyp', 'Aktivitätsstatus',
                'Produktionsstart', 'Produktionsende', 'Fördermenge/Jahr', 'Minenfläche in qkm',
                'x-Koordinate', 'y-Koordinate', 'Restaurationskosten', 'Kostenjahr', 'Dokumentenjahr',
                'Quellenangaben', 'details'
            ]
            
            # Vergleiche Frontend-Konfiguration mit API-Daten
            print(f"\n🔍 FRONTEND-KONFIGURATION VS. API-DATEN:")
            print("-" * 70)
            
            print("\n✅ FRONTEND-SPALTEN DIE IN API VERFÜGBAR SIND:")
            available_in_api = []
            for col in frontend_columns:
                if col in ['mine_name', 'country', 'region', 'overall_confidence', 'model_count', 'last_updated', 'details']:
                    # Diese sind in der Hauptstruktur
                    available_in_api.append(col)
                    print(f"  ✅ {col} (Hauptstruktur)")
                elif col in api_columns:
                    # Diese sind in best_values
                    available_in_api.append(col)
                    print(f"  ✅ {col} (best_values)")
            
            print("\n❌ FRONTEND-SPALTEN DIE NICHT IN API VERFÜGBAR SIND:")
            missing_in_api = []
            for col in frontend_columns:
                if col not in ['mine_name', 'country', 'region', 'overall_confidence', 'model_count', 'last_updated', 'details'] and col not in api_columns:
                    missing_in_api.append(col)
                    print(f"  ❌ {col}")
            
            print("\n🆕 API-SPALTEN DIE NICHT IM FRONTEND KONFIGURIERT SIND:")
            extra_in_api = []
            for col in api_columns:
                if col not in frontend_columns:
                    extra_in_api.append(col)
                    print(f"  🆕 {col}")
            
            # Prüfe speziell die Problem-Spalten
            print(f"\n💰 SPEZIELLE ANALYSE - PROBLEM-SPALTEN:")
            problem_columns = ['Restaurationskosten', 'Kostenjahr', 'Dokumentenjahr']
            
            for prob_col in problem_columns:
                if prob_col in api_columns:
                    # Schaue dir die tatsächlichen Werte an
                    values_sample = []
                    for result in consolidated_results[:5]:  # Erste 5 Ergebnisse
                        value = result.get('best_values', {}).get(prob_col, 'N/A')
                        values_sample.append(str(value)[:30])
                    
                    print(f"  💰 {prob_col}:")
                    print(f"    ✅ In API verfügbar")
                    print(f"    📊 Sample Werte: {values_sample}")
                else:
                    print(f"  💰 {prob_col}: ❌ NICHT in API verfügbar")
            
            # Duplikat-Analyse der API-Spalten
            print(f"\n🔍 DUPLIKAT-ANALYSE IN API-SPALTEN:")
            column_counts = Counter(api_columns)
            duplicates = [col for col, count in column_counts.items() if count > 1]
            
            if duplicates:
                print(f"❌ DUPLIKATE GEFUNDEN: {duplicates}")
            else:
                print("✅ Keine Duplikate in API-Spalten")
            
            # Speichere Analyse
            analysis_result = {
                "timestamp": "2025-07-30T09:31:00Z",
                "total_results": len(consolidated_results),
                "api_columns": api_columns,
                "frontend_columns": frontend_columns,
                "available_in_api": available_in_api,
                "missing_in_api": missing_in_api,
                "extra_in_api": extra_in_api,
                "problem_columns_analysis": {
                    col: {
                        "available": col in api_columns,
                        "sample_values": [
                            str(result.get('best_values', {}).get(col, 'N/A'))[:30]
                            for result in consolidated_results[:3]
                        ] if col in api_columns else []
                    }
                    for col in problem_columns
                },
                "duplicates_in_api": duplicates
            }
            
            with open('/app/minesearch_v2/backend/column_analysis_report.json', 'w', encoding='utf-8') as f:
                json.dump(analysis_result, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 Detaillierte Analyse gespeichert: column_analysis_report.json")
            
            # FAZIT
            print(f"\n🎯 FAZIT:")
            print(f"  📊 API liefert {len(api_columns)} Spalten")
            print(f"  🖥️ Frontend konfiguriert für {len(frontend_columns)} Spalten")
            print(f"  ✅ {len(available_in_api)} Spalten verfügbar")
            print(f"  ❌ {len(missing_in_api)} Spalten fehlen in API")
            print(f"  🆕 {len(extra_in_api)} zusätzliche API-Spalten")
            
            if duplicates:
                print(f"  ⚠️ {len(duplicates)} Duplikate in API gefunden!")
            
            return analysis_result
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Netzwerk-Fehler: {str(e)}")
    except Exception as e:
        print(f"❌ Unerwarteter Fehler: {str(e)}")
    
    return None

if __name__ == "__main__":
    analyze_api_columns()