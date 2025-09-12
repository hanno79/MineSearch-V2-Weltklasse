#!/usr/bin/env python3
"""
Author: rahn
Datum: 04.09.2025
Version: 1.0
Beschreibung: Aktualisiert die mines-Tabelle mit den besten verfügbaren Koordinaten aus mine_data_fields
"""

import sys
sys.path.insert(0, 'backend')

from minesearch.database.normalized_manager import NormalizedDatabaseManager
import sqlite3
# Import für Root-Level-Scripts
try:
    # Versuche Backend-Import
    from minesearch.database.db_utils import get_normalized_db_path, get_sqlite_connection
except ImportError:
    # Fallback für Root-Level-Scripts
    from db_utils_root.db_utils import get_normalized_db_path, get_sqlite_connection

def update_mine_coordinates():
    """Aktualisiert alle Minen mit den besten verfügbaren Koordinaten"""

    print("🔧 [KOORDINATEN-UPDATE] Starte Koordinaten-Aktualisierung...")

    db_manager = NormalizedDatabaseManager()
    conn = sqlite3.connect(get_normalized_db_path())
    cursor = conn.cursor()

    # Hole alle Minen
    cursor.execute("SELECT id, name FROM mines ORDER BY id")
    mines = cursor.fetchall()

    print(f"📊 [KOORDINATEN-UPDATE] {len(mines)} Minen zu prüfen")

    for mine_id, mine_name in mines:
        print(f"\n🔍 [KOORDINATEN-UPDATE] Mine: {mine_name} (ID: {mine_id})")

        # Hole die besten verfügbaren x-Koordinaten (y-Koordinate = Latitude)
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

        lat_result = cursor.fetchone()
        latitude = None
        if lat_result:
            try:
                latitude = float(str(lat_result[0]).replace(',', '.'))
                # Validate latitude range
                if not (-90 <= latitude <= 90):
                    latitude = None
                else:
                    print(f"   ✅ Latitude gefunden: {latitude} (confidence: {lat_result[1]})")
            except (ValueError, TypeError):
                print(f"   ❌ Ungültige Latitude: {lat_result[0]}")

        # Hole die besten verfügbaren y-Koordinaten (x-Koordinate = Longitude)
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

        lon_result = cursor.fetchone()
        longitude = None
        if lon_result:
            try:
                longitude = float(str(lon_result[0]).replace(',', '.'))
                # Validate longitude range
                if not (-180 <= longitude <= 180):
                    longitude = None
                else:
                    print(f"   ✅ Longitude gefunden: {longitude} (confidence: {lon_result[1]})")
            except (ValueError, TypeError):
                print(f"   ❌ Ungültige Longitude: {lon_result[0]}")

        # Aktualisiere die Mine nur wenn wir Koordinaten haben
        if latitude is not None or longitude is not None:
            cursor.execute("""
                UPDATE mines
                SET latitude = ?, longitude = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (latitude, longitude, mine_id))

            print(f"   🚀 Mine {mine_name} aktualisiert:")
            print(f"      - Latitude: {latitude}")
            print(f"      - Longitude: {longitude}")
        else:
            print(f"   ⚠️  Keine gültigen Koordinaten für {mine_name} gefunden")

    conn.commit()
    conn.close()

    # Verifikation
    print("\n📊 [KOORDINATEN-UPDATE] Ergebnis-Prüfung:")
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
        print(f"   Latitude: {latitude or 'NULL'}")
        print(f"   Longitude: {longitude or 'NULL'}")

    conn.close()
    return True

if __name__ == "__main__":
    success = update_mine_coordinates()
    print(f"\n🎯 [KOORDINATEN-UPDATE] {'✅ ERFOLGREICH' if success else '❌ FEHLGESCHLAGEN'}")
