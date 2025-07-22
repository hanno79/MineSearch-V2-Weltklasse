#!/usr/bin/env python3
"""
Analyse warum Éléonore Mine erfolgreiche Datenextraktion hat
"""
import sqlite3, json

def analyze_eleonore_success():
    conn = sqlite3.connect('/app/minesearch_v2/backend/mines.db')
    cursor = conn.cursor()
    
    print("🔬 ÉLÉONORE SUCCESS ANALYSE")
    print("=" * 60)
    
    # Hole Éléonore Daten
    cursor.execute('''
        SELECT mine_name, model_used, structured_data, sources, country, region, commodity, 
               search_timestamp, session_id, data_quality
        FROM search_results 
        WHERE mine_name = 'Éléonore'
    ''')
    
    eleonore_result = cursor.fetchone()
    
    if not eleonore_result:
        print("❌ Keine Éléonore Daten gefunden!")
        return
    
    mine_name, model_used, structured_data_json, sources_json, country, region, commodity, timestamp, session_id, data_quality = eleonore_result
    
    print(f"📊 ÉLÉONORE BASISDATEN:")
    print(f"   Mine: {mine_name}")
    print(f"   Model: {model_used}")
    print(f"   Land: {country}")
    print(f"   Region: {region}")
    print(f"   Rohstoff: {commodity}")
    print(f"   Session: {session_id}")
    print(f"   Timestamp: {timestamp}")
    
    # Analysiere strukturierte Daten
    if structured_data_json:
        structured_data = json.loads(structured_data_json)
        
        print(f"\n📋 STRUKTURIERTE DATEN ({len(structured_data)} Felder):")
        print("-" * 60)
        
        gefuellte_felder = []
        x_felder = []
        leere_felder = []
        
        for field, value in structured_data.items():
            if not value or not str(value).strip():
                leere_felder.append(field)
            elif str(value).strip() == 'X':
                x_felder.append(field)
            else:
                gefuellte_felder.append((field, value))
        
        print(f"✅ GEFÜLLTE FELDER ({len(gefuellte_felder)}):")
        for field, value in gefuellte_felder:
            print(f"   • {field}: '{value}'")
        
        print(f"\n❌ X-MARKIERTE FELDER ({len(x_felder)}):")
        for field in x_felder:
            print(f"   • {field}: X (gesucht aber nicht gefunden)")
        
        print(f"\n⚠️  LEERE FELDER ({len(leere_felder)}):")
        for field in leere_felder:
            print(f"   • {field}: (leer - Suchfehler)")
    
    # Analysiere Quellen
    if sources_json:
        try:
            sources = json.loads(sources_json)
            print(f"\n🔗 QUELLEN ({len(sources)} gefunden):")
            print("-" * 60)
            for i, source in enumerate(sources[:10], 1):  # Erste 10 Quellen
                if isinstance(source, dict):
                    url = source.get('url', 'Keine URL')
                    title = source.get('title', 'Kein Titel')
                    print(f"   {i}. {title[:50]}...")
                    print(f"      URL: {url}")
                else:
                    print(f"   {i}. {str(source)[:100]}...")
        except:
            print(f"\n🔗 QUELLEN: {sources_json[:200]}...")
    
    # Vergleiche mit anderen Minen
    print(f"\n📊 VERGLEICH MIT ANDEREN MINEN:")
    print("-" * 60)
    
    cursor.execute('''
        SELECT mine_name, model_used, structured_data
        FROM search_results 
        WHERE mine_name != 'Éléonore'
        ORDER BY mine_name
    ''')
    
    other_mines = cursor.fetchall()
    
    for other_mine_name, other_model, other_data_json in other_mines:
        if other_data_json:
            other_data = json.loads(other_data_json)
            other_filled = len([v for v in other_data.values() if v and str(v).strip() and str(v) != 'X'])
            other_x = len([v for v in other_data.values() if str(v).strip() == 'X'])
            print(f"   {other_mine_name}: {other_filled} gefüllt, {other_x} X-markiert (Model: {other_model})")
        else:
            print(f"   {other_mine_name}: Keine Daten (Model: {other_model})")
    
    conn.close()

if __name__ == "__main__":
    analyze_eleonore_success()