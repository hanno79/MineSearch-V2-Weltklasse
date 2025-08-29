#!/usr/bin/env python3
"""
Test: Überprüft dass das System keine Dummy-Daten mehr erzeugt (Regel 10)
"""
import requests
import time
import re

def test_no_dummy_data():
    print("🧪 TEST: REGEL 10 - KEINE DUMMY-DATEN")
    print("=" * 60)
    
    # CSV mit einer Test-Mine
    test_csv = """Name,Country,Region,Aktivitätsstatus
Test Mine ABC,Canada,Quebec,Aktiv"""
    
    # Upload CSV
    files = {'csv_file': ('test.csv', test_csv, 'text/csv')}
    
    try:
        upload_response = requests.post(
            "http://localhost:8000/api/upload-csv", 
            files=files, 
            timeout=10
        )
        
        if upload_response.status_code != 200:
            print(f"❌ Upload fehlgeschlagen: {upload_response.status_code}")
            return
        
        # Session ID extrahieren
        upload_html = upload_response.text
        # Robustes HTML-Parsing mit BeautifulSoup
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(upload_html, 'html.parser')

        session_id = None

        # 1) Versuche Hidden-Input (z. B. <input name="session_id" value="...">)
        input_tag = soup.find('input', attrs={'name': 'session_id'}) or soup.find('input', attrs={'id': 'session_id'})
        if input_tag and input_tag.get('value'):
            session_id = input_tag.get('value').strip()

        # 2) Versuche bekannte Container (id/class oder data-Attribut)
        if not session_id:
            explicit = soup.select_one('#session-id, .session-id, #session_id, .session_id, [data-session-id]')
            if explicit:
                if explicit.has_attr('data-session-id'):
                    session_id = explicit['data-session-id'].strip()
                else:
                    text_content = explicit.get_text(" ", strip=True)
                    m = re.search(r'([a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12})', text_content)
                    if m:
                        session_id = m.group(1)

        # 3) Suche nach Text "Session ID" in semantischen Tags
        if not session_id:
            label_candidate = soup.find(lambda tag: tag.name in ['em', 'p', 'span', 'div', 'label'] and tag.get_text() and 'Session ID' in tag.get_text())
            if label_candidate:
                text_content = label_candidate.get_text(" ", strip=True)
                m = re.search(r'([a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12})', text_content)
                if m:
                    session_id = m.group(1)

        # 4) Striktes Regex-Fallback gegen kompletten HTML-Text
        if not session_id:
            m = re.search(r'name=["\']session_id["\']\s+value=["\']([^"\']+)["\']', upload_html, flags=re.IGNORECASE)
            if m:
                session_id = m.group(1).strip()

        if not session_id:
            m = re.search(r'Session\s*ID[:\s]*([a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12})', upload_html, flags=re.IGNORECASE)
            if m:
                session_id = m.group(1).strip()

        if not session_id:
            raise ValueError("Session ID nicht gefunden in Upload-Response")

        print(f"📋 Session ID: {session_id}")
        
        # Teste Batch-Search mit einem verfügbaren Modell
        batch_data = {
            'session_id': session_id,
            'search_all': 'false',
            'count': '1',
            'selected_models': 'openrouter:deepseek-free',  # Verfügbares Modell
            'search_type': 'standard'
        }
        
        print("\n🔍 Führe Batch-Suche durch...")
        batch_response = requests.post(
            "http://localhost:8000/api/batch-search",
            data=batch_data,
            timeout=60
        )
        
        if batch_response.status_code != 200:
            print(f"❌ Batch-Search fehlgeschlagen: {batch_response.status_code}")
            return
        
        print("✅ Batch-Search erfolgreich")
        
        # Warte und hole konsolidierte Ergebnisse
        time.sleep(5)
        
        consolidated_response = requests.get(
            "http://localhost:8000/api/consolidated/results?exclude_exa=true&days_back=1&sort_by=mine_name",
            timeout=30
        )
        
        if consolidated_response.status_code != 200:
            print(f"❌ Konsolidierte Ergebnisse fehlgeschlagen: {consolidated_response.status_code}")
            return
        
        data = consolidated_response.json()
        
        if not data.get('success'):
            print("❌ Keine erfolgreichen Ergebnisse")
            return
        
        # Analysiere Ergebnisse auf Dummy-Daten
        print("\n📊 ANALYSIERE ERGEBNISSE AUF DUMMY-DATEN...")
        
        results = data.get('data', [])
        if not results:
            print("📋 Keine Ergebnisse zur Analyse")
            return
        
        dummy_indicators_found = 0
        total_fields_analyzed = 0
        
        for result in results:
            mine_name = result.get('mine_name', 'Unknown')
            print(f"\n🔍 Analysiere Mine: {mine_name}")
            
            # Prüfe best_values
            best_values = result.get('best_values', {})
            
            for field, value in best_values.items():
                total_fields_analyzed += 1
                value_str = str(value) if value is not None else ""
                
                # Prüfe auf typische Dummy-Indikatoren
                # Hinweis: 'X' gilt nur als Dummy, wenn das gesamte Feld genau 'X' ist
                dummy_patterns = [
                    'dummy', 'DUMMY',
                    'placeholder', 'PLACEHOLDER',
                    'template', 'TEMPLATE',
                    'sample', 'SAMPLE',
                    'example', 'EXAMPLE',
                    'test', 'TEST'
                ]

                # Strenger 'X'-Check: nur vollständiger Feldwert 'X' (keine Teilwörter wie "Mine X")
                if re.fullmatch(r'\s*X\s*', value_str):
                    dummy_indicators_found += 1
                    print(f"❌ DUMMY-INDIKATOR GEFUNDEN: {field} = '{value_str}'")
                else:
                    for pattern in dummy_patterns:
                        if pattern in value_str:
                            dummy_indicators_found += 1
                            print(f"❌ DUMMY-INDIKATOR GEFUNDEN: {field} = '{value_str}'")
                            break
                    else:
                        if value_str.strip():
                            print(f"✅ {field}: '{value_str[:50]}{'...' if len(value_str) > 50 else ''}'")
        
        print(f"\n📈 ANALYSE-ERGEBNIS:")
        print(f"   📊 Analysierte Felder: {total_fields_analyzed}")
        print(f"   ❌ Dummy-Indikatoren gefunden: {dummy_indicators_found}")
        
        if dummy_indicators_found == 0:
            print(f"\n🎉 REGEL 10 ERFOLGREICH: Keine Dummy-Daten gefunden!")
        else:
            print(f"\n⚠️ REGEL 10 VERLETZT: {dummy_indicators_found} Dummy-Indikatoren gefunden!")
        
        # Zusätzlich: Prüfe auf leere Felder (das ist OK)
        empty_fields = sum(1 for result in results 
                          for field, value in result.get('best_values', {}).items() 
                          if not value or str(value).strip() == '')
        
        print(f"   📝 Leere Felder: {empty_fields} (✅ OK - echte 'nicht gefunden')")
        
        return dummy_indicators_found == 0
        
    except Exception as e:
        print(f"❌ Test fehlgeschlagen: {e}")
        return False

if __name__ == "__main__":
    success = test_no_dummy_data()
    exit(0 if success else 1)