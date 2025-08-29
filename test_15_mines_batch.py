#!/usr/bin/env python3
"""
Test für 15-Minen Batch-Suche nach den Fixes
"""
import requests
import time
import json

def test_15_mines_batch():
    print("🧪 TEST: 15-Minen Batch-Suche nach Fixes")
    print("=" * 60)
    
    # Teste zuerst ob Server läuft
    try:
        response = requests.get("http://localhost:8000/api/results/stats", timeout=5)
        response.raise_for_status()
        try:
            stats_data = response.json()
        except ValueError as je:
            print(f"❌ Server antwortete nicht mit gültigem JSON: {je}")
            print(f"Antwort (gekürzt): {response.text[:200]}...")
            return
        if not isinstance(stats_data, dict):
            print(f"❌ Unerwartetes Schema: JSON-Objekt erwartet, erhalten: {type(stats_data).__name__}")
            print(f"Antwort (gekürzt): {str(stats_data)[:200]}...")
            return
        if 'status' not in stats_data and 'data' not in stats_data:
            print(f"❌ Unerwartetes Schema: Schlüssel 'status' oder 'data' fehlt")
            print(f"Antwort-Schlüssel: {list(stats_data.keys())}")
            return
        fields = [k for k in ('status', 'data') if k in stats_data]
        fields_str = ", ".join(fields) if fields else "keine"
        print(f"✅ Server OK: {response.status_code} | Felder: {fields_str}")
    except requests.exceptions.HTTPError as he:
        print(f"❌ Server HTTP-Fehler: {he} | Body: {response.text[:200]}...")
        return
    except requests.exceptions.RequestException as e:
        print(f"❌ Server nicht erreichbar: {e}")
        return
    
    # Erstelle Test-CSV mit 15 Minen
    test_csv_content = """Name,Country,Region,Aktivitätsstatus
Mine A,Canada,Quebec,Aktiv
Mine B,Canada,Quebec,Exploration
Mine C,Canada,Ontario,Aktiv
Mine D,USA,Nevada,Aktiv
Mine E,Australia,Western Australia,Exploration
Mine F,Canada,British Columbia,Aktiv
Mine G,USA,Alaska,Geschlossen
Mine H,Chile,Atacama,Aktiv
Mine I,Canada,Quebec,Exploration
Mine J,Peru,Lima,Aktiv
Mine K,Australia,Queensland,Aktiv
Mine L,Canada,Ontario,Exploration
Mine M,South Africa,Gauteng,Aktiv
Mine N,USA,Colorado,Geschlossen
Mine O,Brazil,Minas Gerais,Aktiv"""
    
    print(f"📄 Test-CSV erstellt mit 15 Minen")
    
    # Upload CSV
    files = {
        'csv_file': ('test_15_mines.csv', test_csv_content, 'text/csv')
    }
    
    try:
        upload_response = requests.post(
            "http://localhost:8000/api/upload-csv",
            files=files,
            timeout=10
        )
        
        if upload_response.status_code != 200:
            print(f"❌ CSV Upload fehlgeschlagen: {upload_response.status_code}")
            print(f"Response: {upload_response.text}")
            return
            
        print(f"📨 Upload Response Status: {upload_response.status_code}")
        print(f"📨 Upload Response Text: {upload_response.text[:200]}...")
        
        upload_data = upload_response.json()
        session_id = upload_data['session_id']
        print(f"✅ CSV Upload erfolgreich")
        print(f"📋 Session ID: {session_id}")
        print(f"📊 Erkannte Minen: {upload_data['mine_count']}")
        
    except Exception as e:
        print(f"❌ CSV Upload Fehler: {e}")
        return
    
    # Test Batch-Search mit verfügbaren Modellen
    print(f"\n🔍 Starte Batch-Suche...")
    
    # Verwende nur bekannte, funktionierende Modelle
    test_models = [
        'openrouter:deepseek-free',
        'openrouter:glm-4.5-air-free', 
        'gemini:gemini-1.5-flash',
        'gemini:gemini-2.5-flash-lite'
    ]
    
    batch_data = {
        'session_id': session_id,
        'search_all': 'true',  # ALLE MINEN
        'count': '15',         # Zur Sicherheit
        'selected_models': ','.join(test_models),
        'search_type': 'standard'
    }
    
    try:
        batch_response = requests.post(
            "http://localhost:8000/api/batch-search",
            data=batch_data,
            timeout=120  # 2 Minuten Timeout
        )
        
        print(f"📨 Batch Request gesendet")
        print(f"📊 Angefordert: search_all=true, 15 Minen, {len(test_models)} Modelle")
        print(f"🤖 Modelle: {test_models}")
        
        if batch_response.status_code == 200:
            result = batch_response.json()
            print(f"✅ Batch-Suche erfolgreich")
            print(f"📈 Ergebnisse erhalten: {len(result.get('results', []))}")
            
            # Analysiere Ergebnisse
            if 'results' in result:
                successful = len([r for r in result['results'] if r.get('success')])
                failed = len(result['results']) - successful
                print(f"✅ Erfolgreiche Suchen: {successful}")
                print(f"❌ Fehlgeschlagene Suchen: {failed}")
                
        else:
            print(f"❌ Batch-Suche fehlgeschlagen: {batch_response.status_code}")
            print(f"Response: {batch_response.text[:500]}...")
            
    except Exception as e:
        print(f"❌ Batch-Suche Fehler: {e}")
        return
    
    # Prüfe konsolidierte Ergebnisse
    print(f"\n📊 Prüfe konsolidierte Ergebnisse...")
    
    try:
        consolidated_response = requests.get(
            "http://localhost:8000/api/consolidated/results?exclude_exa=true&days_back=1&sort_by=mine_name",
            timeout=30
        )
        
        if consolidated_response.status_code == 200:
            consolidated_data = consolidated_response.json()
            
            if consolidated_data.get('success') and 'data' in consolidated_data:
                mines_found = len(consolidated_data['data'])
                print(f"✅ Konsolidierte Ergebnisse: {mines_found} Minen gefunden")
                
                # Zeige erste 5 Minen
                for i, mine in enumerate(consolidated_data['data'][:5]):
                    mine_name = mine.get('mine_name', 'Unknown')
                    model_count = mine.get('model_count', 0)
                    print(f"  {i+1}. {mine_name}: {model_count} Modell-Ergebnisse")
                
                if mines_found > 5:
                    print(f"  ... und {mines_found - 5} weitere Minen")
                    
                # Erfolgsstatistik
                expected_mines = 15
                found_percentage = (mines_found / expected_mines) * 100
                
                print(f"\n🎯 FINALE BEWERTUNG:")
                print(f"   📋 Erwartete Minen: {expected_mines}")
                print(f"   ✅ Gefundene Minen: {mines_found}")
                print(f"   📊 Erfolgsrate: {found_percentage:.1f}%")
                
                if found_percentage >= 80:
                    print(f"   🎉 TEST ERFOLGREICH!")
                elif found_percentage >= 50:
                    print(f"   ⚠️  TEST TEILWEISE ERFOLGREICH")
                else:
                    print(f"   ❌ TEST FEHLGESCHLAGEN")
                    
            else:
                print(f"❌ Konsolidierte Ergebnisse: Keine Daten")
                print(f"Response: {consolidated_data}")
                
        else:
            print(f"❌ Konsolidierte Ergebnisse fehlgeschlagen: {consolidated_response.status_code}")
            
    except Exception as e:
        print(f"❌ Konsolidierte Ergebnisse Fehler: {e}")

if __name__ == "__main__":
    test_15_mines_batch()