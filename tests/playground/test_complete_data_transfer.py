#!/usr/bin/env python3
"""
Author: rahn
Datum: 04.09.2025
Version: 1.0
Beschreibung: Testet die vollständige Datenübertragung von mine_data_fields zu mines-Tabelle
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

def test_complete_data_transfer():
    """Testet die erweiterte Datenübertragung"""

    print("🔧 [VOLLSTÄNDIGER DATENTEST] Teste erweiterte Datenübertragung...")

    db_manager = NormalizedDatabaseManager()

    # Teste für alle 3 Minen
    for mine_id in [12, 13, 14]:
        print(f"\n🔍 [TEST] Mine ID {mine_id} - vor Update:")

        # Zeige aktuellen Status
        conn = sqlite3.connect(get_normalized_db_path())
        cursor = conn.cursor()

        cursor.execute("""
            SELECT name, latitude, longitude, area_sqkm
            FROM mines WHERE id = ?
        """, (mine_id,))
        current = cursor.fetchone()
        print(f"   Aktuell: {current[0]} - Lat: {current[1]}, Lon: {current[2]}, Area: {current[3]}")

        conn.close()

        # Wende die erweiterte Update-Funktion an
        print(f"🚀 [TEST] Führe erweiterten Update für Mine {mine_id} aus...")
        db_manager._update_mine_coordinates_from_fields(mine_id)

        # Prüfe Ergebnis
        conn = sqlite3.connect(get_normalized_db_path())
        cursor = conn.cursor()

        cursor.execute("""
            SELECT name, latitude, longitude, area_sqkm
            FROM mines WHERE id = ?
        """, (mine_id,))
        updated = cursor.fetchone()
        print(f"   Nach Update: {updated[0]} - Lat: {updated[1]}, Lon: {updated[2]}, Area: {updated[3]}")

        # Vergleiche verfügbare Daten
        cursor.execute("""
            SELECT normalized_value
            FROM mine_data_fields
            WHERE mine_id = ? AND field_name = 'Fläche der Mine in qkm'
              AND normalized_value != 'Nicht gefunden'
            LIMIT 1
        """, (mine_id,))
        available_area = cursor.fetchone()
        if available_area:
            print(f"   📊 Verfügbare Fläche in mine_data_fields: {available_area[0]}")
        else:
            print(f"   📊 Keine Fläche in mine_data_fields gefunden")

        conn.close()

    print("\n📊 [VOLLSTÄNDIGER TEST] Finale Ergebnisse:")
    print("=" * 60)

    conn = sqlite3.connect(get_normalized_db_path())
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, latitude, longitude, area_sqkm
        FROM mines
        ORDER BY id
    """)

    for row in cursor.fetchall():
        mine_id, name, lat, lon, area = row
        print(f"✅ Mine {mine_id}: {name}")
        print(f"   Koordinaten: Lat={lat}, Lon={lon}")
        print(f"   Fläche: {area or 'NULL'} km²")

        # Verfügbare vs. übertragene Daten prüfen
        if area is None:
            cursor.execute("""
                SELECT normalized_value
                FROM mine_data_fields
                WHERE mine_id = ? AND field_name = 'Fläche der Mine in qkm'
                  AND normalized_value != 'Nicht gefunden'
                LIMIT 1
            """, (mine_id,))
            available = cursor.fetchone()
            if available:
                print(f"   ❌ PROBLEM: Verfügbare Fläche ({available[0]}) nicht übertragen!")
            else:
                print(f"   ✅ OK: Keine Flächendaten verfügbar")
        else:
            print(f"   ✅ OK: Fläche korrekt übertragen")
        print()

    conn.close()
    return True

if __name__ == "__main__":
    success = test_complete_data_transfer()
    print(f"🎯 [VOLLSTÄNDIGER TEST] {'✅ ERFOLGREICH' if success else '❌ FEHLGESCHLAGEN'}")
