#!/usr/bin/env python3
"""
Direct API Debug für Batch-Suche
Prüfe direkt die API-Responses ohne Browser
"""

import requests
import json
import time

def debug_batch_api():
    print("🔍 STARTE DIREKTE API-ANALYSE")
    
    # 1. Upload CSV
    print("\n📤 UPLOADE TEST-CSV...")
    csv_content = "Name,Country,Region\nÉléonore,Canada,Quebec\nLac Expanse,Canada,Quebec\nAubelle,Canada,Quebec"
    
    with open('/tmp/debug_test.csv', 'w', encoding='utf-8', newline='') as f:
        f.write(csv_content)
    
    with open('/tmp/debug_test.csv', 'rb') as f:
        files = {'csv_file': f}
        upload_response = requests.post('http://localhost:8000/api/upload-csv', files=files)
    
    print(f"Upload Status: {upload_response.status_code}")
    
    # Extrahiere Session ID aus HTML Response
    html = upload_response.text
    import re
    session_match = re.search(r'session_id.*?value="([^"]+)"', html)
    
    if not session_match:
        print("❌ Session ID nicht gefunden in Upload Response")
        print("HTML Preview:", html[:500])
        return
    
    session_id = session_match.group(1)
    print(f"✅ Session ID: {session_id}")
    
    # 2. Starte Batch-Suche
    print("\n🚀 STARTE BATCH-SUCHE...")
    batch_data = {
        'session_id': session_id,
        'selected_models': 'openrouter:deepseek-free',
        'search_type': 'standard',
        'count': '3',
        'search_all': 'true'
    }
    
    batch_response = requests.post('http://localhost:8000/api/batch-search', data=batch_data, timeout=120)
    print(f"Batch Status: {batch_response.status_code}")
    
    batch_html = batch_response.text
    
    # 3. Analysiere die Response
    print(f"\n🔍 ANALYSIERE BATCH-RESPONSE ({len(batch_html)} chars):")
    
    # Zähle "nichts gefunden"
    nichts_gefunden_count = batch_html.count('nichts gefunden')
    print(f"❌ 'nichts gefunden' Anzahl: {nichts_gefunden_count}")
    
    # Suche nach echten Daten-Indikatoren
    real_data_indicators = ['Newmont', 'Underground', 'Gold', '52.', '76.', '2014', 'aktiv', 'Untertage']
    real_data_found = []
    for indicator in real_data_indicators:
        if indicator in batch_html:
            real_data_found.append(indicator)
    
    print(f"✅ Echte Daten gefunden: {real_data_found}")
    
    # Suche nach Éléonore-Tabellenzeile
    eleonore_match = re.search(r'<tr[^>]*>.*?Éléonore.*?</tr>', batch_html, re.DOTALL)
    if eleonore_match:
        eleonore_row = eleonore_match.group(0)
        print(f"\n📋 ÉLÉONORE-ZEILE GEFUNDEN ({len(eleonore_row)} chars):")
        
        # Extrahiere alle Zellenwerte aus der Éléonore-Zeile
        cell_matches = re.findall(r'<td[^>]*.*?title="([^"]*)"', eleonore_row)
        
        field_names = [
            'Status', 'Name', 'Country', 'Region', 'Eigentümer', 'Betreiber', 
            'x-Koordinate', 'y-Koordinate', 'Aktivitätsstatus', 'Restaurationskosten',
            'Jahr der Aufnahme der Kosten', 'Jahr der Erstellung des Dokumentes',
            'Rohstoffabbau', 'Minentyp', 'Produktionsstart', 'Produktionsende',
            'Fördermenge/Jahr', 'Fläche der Mine in qkm', 'Quellenangaben'
        ]
        
        print("   FELD-ANALYSE:")
        filled_count = 0
        for i, value in enumerate(cell_matches):
            if i < len(field_names):
                field = field_names[i]
                if value and value.strip() and 'nichts gefunden' not in value and value != '✅':
                    filled_count += 1
                    status = '✅'
                else:
                    status = '❌'
                print(f"   {status} {field}: {repr(value)}")
        
        success_rate = filled_count / (len(cell_matches) - 1) * 100 if len(cell_matches) > 1 else 0
        print(f"\n   📊 ÉLÉONORE SUCCESS RATE: {filled_count}/{len(cell_matches)-1} = {success_rate:.1f}%")
        
    else:
        print("❌ Éléonore-Zeile nicht gefunden")
        # Zeige ersten Teil der Response
        print("Response Preview:", batch_html[:1000])
    
    # 4. Prüfe auch die Datenbank direkt
    print(f"\n🗄️ VERGLEICHE MIT DATENBANK:")
    try:
        import sys
        sys.path.append('/app/backend')
        from minesearch.database import db_manager
        from sqlalchemy import text
        
        with db_manager.get_session() as session:
            result = session.execute(text('''
                SELECT mine_name, structured_data, created_at 
                FROM search_results 
                WHERE mine_name = 'Éléonore' 
                ORDER BY created_at DESC 
                LIMIT 1
            '''))
            
            row = result.fetchone()
            if row and row[1]:
                db_data = json.loads(row[1])
                db_filled = sum(1 for v in db_data.values() 
                               if v and str(v).strip() and str(v).strip() not in ['', 'X'])
                print(f"   📊 DATABASE: {db_filled}/{len(db_data)} Felder gefüllt")
                print(f"   🕒 Letzte Aktualisierung: {row[2]}")
                
                # Zeige erste gefüllte Felder aus DB
                sample_fields = [(k, v) for k, v in db_data.items() 
                                if v and str(v).strip() and str(v).strip() not in ['', 'X']][:3]
                for field, value in sample_fields:
                    print(f"   📋 DB-Beispiel {field}: {repr(str(value)[:40])}")
            else:
                print("   ❌ Keine DB-Daten für Éléonore gefunden")
                
    except Exception as e:
        print(f"   ❌ DB-Check Fehler: {e}")
    
    # 5. Endergebnis
    print(f"\n🎯 ENDERGEBNIS:")
    if len(real_data_found) >= 2 and nichts_gefunden_count < 20:
        print("   ✅ SUCCESS: Echte Daten erreichen Frontend!")
    else:
        print("   ❌ FAILED: 'nichts gefunden' dominiert weiterhin")
        print("   🔧 NÄCHSTE SCHRITTE: API-Chain genauer prüfen")

if __name__ == "__main__":
    debug_batch_api()