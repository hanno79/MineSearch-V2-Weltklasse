#!/usr/bin/env python3
"""
Author: rahn
Datum: 04.09.2025
Version: 1.0
Beschreibung: Korrigiert die Koordinaten-Zuordnung - x-Koordinate = Longitude, y-Koordinate = Latitude
"""

import sys
sys.path.insert(0, 'backend')

import sqlite3
from minesearch.database.db_utils import get_normalized_db_path, get_sqlite_connection

def fix_coordinate_assignment():
    """Korrigiert die Koordinaten-Zuordnung basierend auf geologischen Standards"""
    
    print("🔧 [KOORDINATEN-FIX] Starte Koordinaten-Zuordnung-Korrektur...")
    print("📍 [KOORDINATEN-FIX] Standard: x-Koordinate = Longitude (Ost-West), y-Koordinate = Latitude (Nord-Süd)")
    
    conn = sqlite3.connect(get_normalized_db_path())
    cursor = conn.cursor()
    
    # Hole alle Minen
    cursor.execute("SELECT id, name FROM mines ORDER BY id")
    mines = cursor.fetchall()
    
    print(f"📊 [KOORDINATEN-FIX] {len(mines)} Minen zu korrigieren")
    
    for mine_id, mine_name in mines:
        print(f"\n🔍 [KOORDINATEN-FIX] Mine: {mine_name} (ID: {mine_id})")
        
        # Hole beste x-Koordinate (= Longitude, Ost-West)
        cursor.execute("""
            SELECT normalized_value, confidence_score 
            FROM mine_data_fields 
            WHERE mine_id = ? 
              AND field_name = 'x-Koordinate' 
              AND normalized_value IS NOT NULL 
              AND normalized_value != 'Nicht gefunden'
              AND normalized_value != 'nichts gefunden'
            ORDER BY confidence_score DESC, id DESC
            LIMIT 1
        """, (mine_id,))
        
        x_result = cursor.fetchone()
        longitude = None
        if x_result:
            try:
                longitude = float(str(x_result[0]).replace(',', '.'))
                # Validate longitude range
                if not (-180 <= longitude <= 180):
                    longitude = None
                else:
                    print(f"   ✅ X-Koordinate (Longitude) gefunden: {longitude}")
            except (ValueError, TypeError):
                print(f"   ❌ Ungültige X-Koordinate: {x_result[0]}")
                
        # Hole beste y-Koordinate (= Latitude, Nord-Süd)
        cursor.execute("""
            SELECT normalized_value, confidence_score 
            FROM mine_data_fields 
            WHERE mine_id = ? 
              AND field_name = 'y-Koordinate' 
              AND normalized_value IS NOT NULL 
              AND normalized_value != 'Nicht gefunden'
              AND normalized_value != 'nichts gefunden'
            ORDER BY confidence_score DESC, id DESC
            LIMIT 1
        """, (mine_id,))
        
        y_result = cursor.fetchone()
        latitude = None
        if y_result:
            try:
                latitude = float(str(y_result[0]).replace(',', '.'))
                # Validate latitude range
                if not (-90 <= latitude <= 90):
                    latitude = None
                else:
                    print(f"   ✅ Y-Koordinate (Latitude) gefunden: {latitude}")
            except (ValueError, TypeError):
                print(f"   ❌ Ungültige Y-Koordinate: {y_result[0]}")
        
        # Aktualisiere die Mine mit korrekter Zuordnung
        if latitude is not None or longitude is not None:
            cursor.execute("""
                UPDATE mines 
                SET latitude = ?, longitude = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (latitude, longitude, mine_id))
            
            print(f"   🚀 Mine {mine_name} korrekt aktualisiert:")
            print(f"      - Latitude (y): {latitude}")  
            print(f"      - Longitude (x): {longitude}")
        else:
            print(f"   ⚠️  Keine gültigen Koordinaten für {mine_name} gefunden")
    
    conn.commit()
    conn.close()
    
    # Verifikation
    print("\n📊 [KOORDINATEN-FIX] Ergebnis-Prüfung:")
    conn = sqlite3.connect(get_normalized_db_path())
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT m.id, m.name, m.latitude, m.longitude
        FROM mines m
        ORDER BY m.id
    """)
    
    for row in cursor.fetchall():
        mine_id, name, latitude, longitude = row
        print(f"✅ Mine {mine_id}: {name}")
        print(f"   Latitude (Nord-Süd): {latitude or 'NULL'}")
        print(f"   Longitude (Ost-West): {longitude or 'NULL'}")
        
        # Geografische Plausibilität prüfen für Quebec, Canada
        if latitude and longitude:
            if 45 <= latitude <= 62 and -79 <= longitude <= -57:
                print(f"   ✅ Koordinaten sind plausibel für Quebec")
            else:
                print(f"   ⚠️  Koordinaten könnten außerhalb Quebec liegen")
    
    conn.close()
    return True

if __name__ == "__main__":
    success = fix_coordinate_assignment()
    print(f"\n🎯 [KOORDINATEN-FIX] {'✅ ERFOLGREICH' if success else '❌ FEHLGESCHLAGEN'}")