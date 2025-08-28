#!/usr/bin/env python3
"""
Author: rahn
Datum: 22.08.2025
Version: 2.0
Beschreibung: Umfassender End-to-End Debug-Test mit vollständigem Trail
"""

import requests
import json
import time
import sys
import os

def test_single_search():
    """Teste eine Einzelsuche für Éléonore"""
    print('🔍 TESTE EINZELSUCHE FÜR ÉLÉONORE...')
    
    payload = {
        "mine_name": "Éléonore",
        "country": "Canada", 
        "region": "Quebec",
        "model": "openrouter:deepseek-free",
        "comprehensive_search": False
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/api/search",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                structured = data.get('data', {}).get('structured_data', {})
                mine_name = data.get('data', {}).get('mine_name', 'Unknown')
                
                print(f'   ✅ Mine: {mine_name}')
                
                # Teste kritische Felder
                fields = ['Country', 'Region', 'Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)', 'Restaurationskosten', 'Eigentümer']
                filled_count = 0
                
                for field in fields:
                    value = structured.get(field, 'NICHT_VORHANDEN')
                    if value and str(value).strip() and value != 'NICHT_VORHANDEN':
                        filled_count += 1
                        status = '✅'
                    else:
                        status = '❌'
                    print(f'   {status} {field}: "{value}"')
                
                print(f'   📊 {filled_count}/{len(fields)} Felder haben Daten')
                print(f'   📋 Insgesamt {len(structured)} Felder in structured_data')
                
                return True
            else:
                print(f'   ❌ Search fehlgeschlagen: {data.get("error", "Unknown")}')
                return False
        else:
            print(f'   ❌ HTTP Error: {response.status_code}')
            return False
            
    except Exception as e:
        print(f'   ❌ Fehler: {str(e)}')
        return False

def test_batch_html_generation():
    """Teste die HTML-Generierung mit echten Daten"""
    print('\n🔧 TESTE BATCH-HTML-GENERIERUNG...')
    
    # Simuliere Batch-Daten mit echten und leeren Werten
    test_results = [
        {
            'mine_name': 'Éléonore',
            'success': True,
            'country': 'Canada',
            'region': 'Quebec',
            'data': {
                'structured_data': {
                    'Name': 'Éléonore',
                    'Country': 'Canada',
                    'Region': 'Quebec',
                    'Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)': 'Gold',
                    'Restaurationskosten': '',  # LEER - sollte "nichts gefunden" werden
                    'Eigentümer': '',  # LEER - sollte "nichts gefunden" werden
                    'Betreiber': 'Newmont Corporation'  # ECHTE DATEN - sollten erhalten bleiben
                }
            }
        },
        {
            'mine_name': 'Aubelle',
            'success': True,
            'country': 'Canada', 
            'region': 'Quebec',
            'data': {
                'structured_data': {
                    'Name': 'Aubelle',
                    'Country': 'Canada',
                    'Region': 'Quebec',
                    # Alle anderen Felder fehlen - sollten "nichts gefunden" werden
                }
            }
        }
    ]
    
    try:
        # Importiere und teste die HTML-Generierung
        import sys
        sys.path.append('/app/backend')
        
        from minesearch.html_utils import create_batch_results_table
        
        html = create_batch_results_table(test_results)
        
        print('   ✅ HTML erfolgreich generiert')
        
        # Analysiere das HTML für "nichts gefunden" vs echte Daten
        nichts_gefunden_count = html.count('nichts gefunden')
        newmont_found = 'Newmont Corporation' in html
        gold_found = 'Gold' in html
        
        print(f'   📊 "nichts gefunden" im HTML: {nichts_gefunden_count} mal')
        print(f'   ✅ Echte Daten erhalten - Newmont: {newmont_found}')
        print(f'   ✅ Echte Daten erhalten - Gold: {gold_found}')
        
        if newmont_found and gold_found:
            print('   🎉 FIX ERFOLGREICH: Echte Daten bleiben erhalten!')
            return True
        else:
            print('   ❌ FIX FEHLGESCHLAGEN: Echte Daten gehen verloren')
            return False
            
    except Exception as e:
        print(f'   ❌ Fehler beim HTML-Test: {str(e)}')
        return False

def test_batch_csv_upload():
    """Teste komplette Batch CSV Upload Pipeline"""
    print('\n🔧 TESTE BATCH CSV UPLOAD PIPELINE...')
    
    try:
        # Erstelle Test-CSV Datei
        csv_content = "mine_name,country,region,commodity\nÉléonore,Canada,Quebec,Gold\nAubelle,Canada,Quebec,\n"
        csv_file = "/tmp/test_batch_debug.csv"
        
        with open(csv_file, 'w') as f:
            f.write(csv_content)
        
        print('   ✅ Test-CSV erstellt')
        
        # Upload CSV
        with open(csv_file, 'rb') as f:
            files = {'file': ('test_batch_debug.csv', f, 'text/csv')}
            data = {
                'models': 'openrouter:deepseek-free',
                'search_type': 'standard',
                'count': '1'
            }
            
            response = requests.post(
                "http://localhost:8000/api/batch/upload",
                files=files,
                data=data,
                timeout=60
            )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                batch_id = data.get('batch_id')
                print(f'   ✅ CSV Upload erfolgreich - Batch ID: {batch_id}')
                
                # Überwache Batch-Fortschritt 
                print('   🔍 Überwache Batch-Fortschritt...')
                for i in range(10):  # Max 10 Checks
                    time.sleep(5)
                    
                    progress_response = requests.get(f"http://localhost:8000/api/batch/progress/{batch_id}")
                    if progress_response.status_code == 200:
                        progress_data = progress_response.json()
                        status = progress_data.get('status', 'unknown')
                        completed = progress_data.get('completed', 0)
                        total = progress_data.get('total', 0)
                        
                        print(f'   📊 Status: {status} - {completed}/{total} abgeschlossen')
                        
                        if status == 'completed':
                            print('   🎉 Batch-Processing abgeschlossen!')
                            return True, batch_id
                        elif status == 'failed':
                            print('   ❌ Batch-Processing fehlgeschlagen!')
                            return False, batch_id
                    else:
                        print(f'   ⚠️ Progress-Check fehlgeschlagen: {progress_response.status_code}')
                
                print('   ⏰ Timeout beim Batch-Processing')
                return False, batch_id
            else:
                print(f'   ❌ CSV Upload fehlgeschlagen: {data.get("error")}')
                return False, None
        else:
            print(f'   ❌ HTTP Error bei CSV Upload: {response.status_code}')
            return False, None
            
    except Exception as e:
        print(f'   ❌ Fehler beim Batch-Test: {str(e)}')
        return False, None

def test_debug_logging_analysis():
    """Analysiere Server-Logs für Debug-Informationen"""
    print('\n📋 ANALYSIERE DEBUG-LOGS...')
    
    try:
        # Versuche Server-Logs zu lesen (wenn verfügbar)
        log_files = [
            '/app/backend/server.log',
            '/tmp/minesearch.log',
            '/var/log/minesearch.log'
        ]
        
        for log_file in log_files:
            if os.path.exists(log_file):
                print(f'   📄 Analysiere {log_file}...')
                
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                
                # Suche nach Debug-Patterns
                orchestrator_logs = [line for line in lines if '[ORCHESTRATOR' in line]
                validation_logs = [line for line in lines if '[VALIDATION' in line]
                db_logs = [line for line in lines if '[DB-CONSISTENCY' in line]
                
                print(f'   🔍 Orchestrator-Logs: {len(orchestrator_logs)}')
                print(f'   🔍 Validation-Logs: {len(validation_logs)}')
                print(f'   🔍 DB-Consistency-Logs: {len(db_logs)}')
                
                if orchestrator_logs:
                    print('   📝 Letzte 3 Orchestrator-Logs:')
                    for log in orchestrator_logs[-3:]:
                        print(f'      {log.strip()}')
                
                return True
        
        print('   ⚠️ Keine Log-Dateien gefunden')
        return False
        
    except Exception as e:
        print(f'   ❌ Fehler bei Log-Analyse: {str(e)}')
        return False

def test_database_consistency():
    """Teste Database-Konsistenz direkt"""
    print('\n🗄️ TESTE DATABASE-KONSISTENZ...')
    
    try:
        # Direkte Database-Abfrage
        sys.path.append('/app/backend')
        from minesearch.database import db_manager
        from minesearch.database.models import SearchResult
        
        with db_manager.get_session() as session:
            # Suche nach Éléonore Einträgen
            results = session.query(SearchResult).filter(SearchResult.mine_name == 'Éléonore').all()
            
            print(f'   📊 Database-Einträge für Éléonore: {len(results)}')
            
            data_count = 0
            empty_count = 0
            
            for result in results:
                structured_data = result.structured_data or {}
                if structured_data:
                    filled_fields = len([v for v in structured_data.values() if v and str(v).strip() and str(v).strip() != 'nichts gefunden'])
                    if filled_fields > 0:
                        data_count += 1
                        print(f'   ✅ {result.model_used}: {filled_fields} Felder mit Daten')
                    else:
                        empty_count += 1
                        print(f'   ❌ {result.model_used}: Keine Daten')
                else:
                    empty_count += 1
                    print(f'   ❌ {result.model_used}: NULL structured_data')
            
            print(f'   📈 Zusammenfassung: {data_count} mit Daten, {empty_count} leer')
            return data_count > 0
            
    except Exception as e:
        print(f'   ❌ Fehler bei Database-Test: {str(e)}')
        return False

if __name__ == "__main__":
    print('🚀 UMFASSENDER END-TO-END DEBUG-TEST')
    print('='*60)
    
    # Phase 1: Basis-Tests
    print('\n🔹 PHASE 1: BASIS-TESTS')
    test1_ok = test_single_search()
    test2_ok = test_batch_html_generation()
    
    # Phase 2: Pipeline-Tests  
    print('\n🔹 PHASE 2: PIPELINE-TESTS')
    try:
        result = test_batch_csv_upload()
        if isinstance(result, tuple) and len(result) == 2:
            test3_ok, batch_id = result
        else:
            print(f'   ❌ test_batch_csv_upload gab unerwartetes Ergebnis zurück: {result}')
            test3_ok, batch_id = False, None
    except (ValueError, TypeError) as e:
        print(f'   ❌ Fehler beim Unpacking von test_batch_csv_upload: {e}')
        test3_ok, batch_id = False, None
    
    # Phase 3: Debug-Analyse
    print('\n🔹 PHASE 3: DEBUG-ANALYSE')
    test4_ok = test_debug_logging_analysis()
    test5_ok = test_database_consistency()
    
    # Zusammenfassung
    print('\n📊 VOLLSTÄNDIGE TEST-ZUSAMMENFASSUNG:')
    print('='*60)
    print(f'   Einzelsuche: {"✅" if test1_ok else "❌"}')
    print(f'   Batch-HTML: {"✅" if test2_ok else "❌"}')
    print(f'   CSV-Pipeline: {"✅" if test3_ok else "❌"}')
    print(f'   Log-Analyse: {"✅" if test4_ok else "❌"}')
    print(f'   DB-Konsistenz: {"✅" if test5_ok else "❌"}')
    
    all_passed = all([test1_ok, test2_ok, test3_ok, test4_ok, test5_ok])
    
    if all_passed:
        print('\n🎉 ALLE TESTS ERFOLGREICH - SYSTEM FUNKTIONIERT VOLLSTÄNDIG!')
    else:
        print('\n❌ EINIGE TESTS FEHLGESCHLAGEN - WEITERE DEBUGGING ERFORDERLICH')
        if batch_id:
            print(f'\n🔍 Für weitere Analyse verwende Batch-ID: {batch_id}')
    
    print('\n📋 NEXT STEPS:')
    print('   1. Server-Logs prüfen für detaillierte Debug-Informationen')
    print('   2. Mit Batch-ID die spezifischen Logs durchsuchen')
    print('   3. Provider-Response-Validation-Logs analysieren')
    print('   4. Database-Consistency-Reports auswerten')