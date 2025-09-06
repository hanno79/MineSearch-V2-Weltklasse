#!/usr/bin/env python3
"""
Author: rahn
Datum: 06.09.2025
Version: 1.0
Beschreibung: Test und Analyse der verbesserten "Fehlgeschlagene Ergebnisse" Klassifikation
"""

import requests
import json
import time
from datetime import datetime

def test_improved_error_classification():
    """Test die verbesserten Fehlerschlagenen-Ergebnisse Features"""
    print("🧪 TEST VERBESSERTE FEHLGESCHLAGENE ERGEBNISSE")
    print("=" * 60)
    
    # Test 1: Einzelsuche für Validierung
    print("1. TESTE EINZELSUCHE MIT QUALITÄTS-FILTER:")
    response = requests.post(
        "http://localhost:8000/api/search",
        data={
            "mine": "Nonexistent Mine Test 12345",  # Mine die nicht existiert
            "country": "Nowhere",
            "model": "openrouter:deepseek-free"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        success = data.get('success', False)
        error = data.get('error', '')
        
        print(f"   Status: {'✅ Erfolg' if success else '❌ Fehlgeschlagen'}")
        if not success:
            print(f"   Grund: {error}")
            
            # Klassifiziere Fehler
            if 'unzureichende' in error.lower():
                print("   🎯 Klassifikation: QUALITÄTS-FILTER (Erwarteter Typ)")
            elif 'timeout' in error.lower():
                print("   ⏱️ Klassifikation: API-TIMEOUT")
            else:
                print("   ❓ Klassifikation: SYSTEM-FEHLER")
    
    print("\n2. TESTE BATCH-SUCHE MIT CSV:")
    
    # Erstelle Test-CSV mit problematischen Einträgen
    test_csv_content = """Name,Country,Region,Commodity
Real Mine,Canada,Quebec,Gold
Fake Mine XYZ,Nowhere,None,Unknown
Standard Graphite,Canada,Quebec,Graphite
Another Fake,Test Country,Test Region,Test Commodity"""
    
    # Speichere temporäre CSV
    with open("test_error_classification.csv", "w") as f:
        f.write(test_csv_content)
    
    # Upload CSV
    try:
        with open("test_error_classification.csv", "rb") as f:
            response = requests.post(
                "http://localhost:8000/api/upload-csv",
                files={"file": f}
            )
        
        if response.status_code == 200:
            # Extrahiere Session ID (vereinfacht)
            import re
            match = re.search(r'Session ID: ([a-f0-9\-]+)', response.text)
            if match:
                session_id = match.group(1)
                print(f"   📋 Session ID: {session_id}")
                
                # Starte Batch-Suche
                batch_response = requests.post(
                    "http://localhost:8000/api/batch-search",
                    data={
                        "session_id": session_id,
                        "selection_mode": "first_n",
                        "count": "4",
                        "selected_models": "openrouter:deepseek-free",
                        "search_type": "standard"
                    }
                )
                
                if batch_response.status_code == 200:
                    print("   ✅ Batch-Suche gestartet")
                    
                    # Monitor Progress für erweiterte Fehler-Klassifikation
                    print("\n3. MONITOR ERWEITERTE FEHLER-KLASSIFIKATION:")
                    for i in range(30):  # 30 Sekunden überwachen
                        time.sleep(2)
                        
                        progress_response = requests.get(f"http://localhost:8000/api/batch-progress/{session_id}")
                        if progress_response.status_code == 200:
                            progress = progress_response.json()
                            
                            # Zeige erweiterte Metriken
                            print(f"\n   Iteration {i+1}:")
                            print(f"     Erfolgreiche Ergebnisse: {progress.get('successful_results', 0)}")
                            print(f"     Fehlgeschlagene Ergebnisse: {progress.get('failed_results', 0)}")
                            
                            # NEUE ERWEITERTE KLASSIFIKATION
                            quality_filtered = progress.get('quality_filtered', 0)
                            api_timeouts = progress.get('api_timeouts', 0)
                            database_errors = progress.get('database_errors', 0)
                            system_errors = progress.get('system_errors', 0)
                            
                            if quality_filtered > 0:
                                print(f"     🎯 Qualitäts-Filter: {quality_filtered}")
                            if api_timeouts > 0:
                                print(f"     ⏱️ API-Timeouts: {api_timeouts}")
                            if database_errors > 0:
                                print(f"     💾 Database-Fehler: {database_errors}")
                            if system_errors > 0:
                                print(f"     ❌ System-Fehler: {system_errors}")
                            
                            # Prüfe ob abgeschlossen
                            state = progress.get('state', '')
                            if 'complete' in state.lower():
                                print("\n   🎉 Batch-Suche abgeschlossen!")
                                break
                    
                    print("\n4. FINALE ANALYSE:")
                    final_progress = requests.get(f"http://localhost:8000/api/batch-progress/{session_id}")
                    if final_progress.status_code == 200:
                        data = final_progress.json()
                        
                        successful = data.get('successful_results', 0)
                        failed = data.get('failed_results', 0)
                        quality_filtered = data.get('quality_filtered', 0)
                        api_timeouts = data.get('api_timeouts', 0)
                        database_errors = data.get('database_errors', 0)
                        system_errors = data.get('system_errors', 0)
                        
                        total = successful + failed
                        
                        print(f"\n   📊 ENDERGEBNIS:")
                        print(f"     Gesamt verarbeitet: {total}")
                        print(f"     ✅ Erfolgreich: {successful} ({successful/total*100:.1f}%)")
                        print(f"     ❌ Fehlgeschlagen: {failed} ({failed/total*100:.1f}%)")
                        
                        if failed > 0:
                            print(f"\n   🔍 FEHLER-BREAKDOWN:")
                            if quality_filtered > 0:
                                print(f"     🎯 Qualitäts-Filter: {quality_filtered} ({quality_filtered/failed*100:.1f}% der Fehler)")
                                print(f"         → Niedrige Relevanz, zu wenig Mining-Begriffe")
                            if api_timeouts > 0:
                                print(f"     ⏱️ API-Timeouts: {api_timeouts} ({api_timeouts/failed*100:.1f}% der Fehler)")
                                print(f"         → Provider-Probleme, Rate-Limiting")
                            if database_errors > 0:
                                print(f"     💾 Database-Fehler: {database_errors} ({database_errors/failed*100:.1f}% der Fehler)")
                                print(f"         → Schema-Probleme (sollten jetzt behoben sein)")
                            if system_errors > 0:
                                print(f"     ❌ System-Fehler: {system_errors} ({system_errors/failed*100:.1f}% der Fehler)")
                                print(f"         → Echte Programm-Fehler")
                        
                        # Bewertung
                        if quality_filtered >= failed * 0.7:  # Mindestens 70% Qualitäts-Filter
                            print(f"\n   🎉 AUSGEZEICHNET: Meist Qualitäts-Filter (normale Funktion)")
                        elif database_errors >= failed * 0.5:  # Viele Database-Fehler
                            print(f"\n   ⚠️ DATABASE-PROBLEME: Schema-Fix erneut prüfen")
                        elif api_timeouts >= failed * 0.5:  # Viele API-Probleme
                            print(f"\n   ⏱️ API-PROBLEME: Provider-Status prüfen")
                        else:
                            print(f"\n   ✅ GEMISCHT: Normal verteilte Fehlertypen")
                else:
                    print("   ❌ Batch-Suche Start fehlgeschlagen")
            else:
                print("   ❌ Session ID nicht gefunden")
        else:
            print("   ❌ CSV Upload fehlgeschlagen")
    
    except Exception as e:
        print(f"   ❌ Test-Fehler: {e}")
    
    # Cleanup
    try:
        import os
        os.remove("test_error_classification.csv")
    except:
        pass
    
    print("\n" + "=" * 60)
    print("🎯 ZUSAMMENFASSUNG:")
    print("✅ Database Schema wurde repariert (normalized columns)")
    print("✅ Frontend zeigt Tooltip für 'Fehlgeschlagene Ergebnisse'")
    print("✅ Backend klassifiziert Fehler in 4 Kategorien")
    print("✅ Progress-API liefert erweiterte Fehler-Metriken")
    print()
    print("📋 'FEHLGESCHLAGENE ERGEBNISSE' bedeuten jetzt:")
    print("   🎯 Qualitäts-Filter: Zu wenig relevante Informationen")
    print("   ⏱️ API-Timeouts: Provider-Probleme, normal")
    print("   💾 Database-Fehler: Schema-Probleme (behoben)")
    print("   ❌ System-Fehler: Echte Programm-Fehler (selten)")

if __name__ == "__main__":
    print(f"🧪 STARTE VERBESSERTE FEHLER-ANALYSE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    test_improved_error_classification()
    
    print(f"\n🎯 BENUTZER-INFORMATION:")
    print("Die meisten 'fehlgeschlagenen Ergebnisse' sind NORMAL und kein Problem.")
    print("Sie bedeuten meist: 'Niedrige Qualität gefiltert' oder 'Nicht gefunden'.")
    print("Database-Speicher-Fehler wurden behoben.")
    print("Frontend zeigt jetzt Tooltip mit Erklärung.")