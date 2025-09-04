#!/usr/bin/env python3
"""
Author: rahn
Datum: 04.09.2025
Version: 1.0
Beschreibung: Migriert bestehende Minen zu vollständigen Datensätzen mit Fremdschlüsseln
"""

import sys
sys.path.insert(0, 'backend')

from minesearch.database.normalized_manager import NormalizedDatabaseManager
import sqlite3

def migrate_existing_mines():
    """Migriere bestehende Minen mit Daten aus mine_data_fields"""
    
    print("🔧 [MIGRATION] Starte Migration bestehender Minen...")
    
    db_manager = NormalizedDatabaseManager()
    
    # Hole alle bestehenden Minen mit NULL-Fremdschlüsseln
    conn = sqlite3.connect(get_normalized_db_path())
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, name, latitude, longitude 
        FROM mines 
        WHERE country_id IS NULL OR region_id IS NULL
    """)
    
    mines_to_migrate = cursor.fetchall()
    print(f"📊 [MIGRATION] {len(mines_to_migrate)} Minen benötigen Migration")
    
    for mine_id, mine_name, current_lat, current_lon in mines_to_migrate:
        print(f"🔄 [MIGRATION] Bearbeite Mine: {mine_name} (ID: {mine_id})")
        
        # Sammle alle Daten für diese Mine aus mine_data_fields
        cursor.execute("""
            SELECT field_name, normalized_value 
            FROM mine_data_fields 
            WHERE mine_id = ?
            ORDER BY field_name
        """, (mine_id,))
        
        field_data = {}
        for field_name, normalized_value in cursor.fetchall():
            if normalized_value and normalized_value != 'Nicht gefunden':
                if field_name not in field_data:
                    field_data[field_name] = normalized_value
                # Bei Duplikaten: nehme den ersten gültigen Wert
        
        # Extrahiere die wichtigsten Werte
        country = field_data.get('Country') or 'Unknown'
        region = field_data.get('Region')
        activity_status = field_data.get('Aktivitätsstatus')
        mine_type = field_data.get('Minentyp (Untertage/ Open-Pit/ usw.)')
        owner = field_data.get('Eigentümer')
        operator = field_data.get('Betreiber')
        
        print(f"   Country: {country}")
        print(f"   Region: {region}")  
        print(f"   Status: {activity_status}")
        print(f"   Type: {mine_type}")
        print(f"   Owner: {owner}")
        print(f"   Operator: {operator}")
        
        # Erstelle oder finde Fremdschlüssel
        with db_manager.get_session() as session:
            country_id = db_manager.get_or_create_country(country, db_session=session)
            
            region_id = None
            if region:
                region_id = db_manager.get_or_create_region(region, country_id, db_session=session)
            
            activity_status_id = None
            if activity_status:
                # Normalisiere Status für DB
                status_normalized = activity_status.lower()
                if 'geschlossen' in status_normalized or 'closed' in status_normalized:
                    status_normalized = 'closed'
                elif 'aktiv' in status_normalized or 'exploitation' in status_normalized:
                    status_normalized = 'active'
                elif 'exploration' in status_normalized:
                    status_normalized = 'exploration'
                else:
                    status_normalized = activity_status
                    
                activity_status_id = db_manager.get_or_create_activity_status(status_normalized, db_session=session)
            
            mine_type_id = None
            if mine_type:
                # Normalisiere Mine Type für DB
                type_normalized = mine_type.lower()
                if 'untertage' in type_normalized or 'underground' in type_normalized:
                    type_normalized = 'underground'
                elif 'open' in type_normalized or 'pit' in type_normalized:
                    type_normalized = 'open_pit'
                else:
                    type_normalized = mine_type
                    
                mine_type_id = db_manager.get_or_create_mine_type(type_normalized, db_session=session)
            
            # Erstelle Companies für Owner/Operator
            if owner and owner not in ['Nicht gefunden', 'nichts gefunden']:
                owner_id = db_manager.get_or_create_company(owner, 'owner', db_session=session)
                print(f"   ✅ Owner Company ID: {owner_id}")
                
            if operator and operator not in ['Nicht gefunden', 'nichts gefunden']:
                operator_id = db_manager.get_or_create_company(operator, 'operator', db_session=session)
                print(f"   ✅ Operator Company ID: {operator_id}")
            
            # Update die Mine mit allen Fremdschlüsseln
            from sqlalchemy import text
# Import für Root-Level-Scripts
try:
    # Versuche Backend-Import  
    from minesearch.database.db_utils import get_normalized_db_path, get_sqlite_connection
except ImportError:
    # Fallback für Root-Level-Scripts
    from db_utils_root.db_utils import get_normalized_db_path, get_sqlite_connection
            session.execute(text("""
                UPDATE mines 
                SET country_id = :country_id,
                    region_id = :region_id,
                    mine_type_id = :mine_type_id,
                    activity_status_id = :activity_status_id,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :mine_id
            """), {
                'mine_id': mine_id,
                'country_id': country_id,
                'region_id': region_id,
                'mine_type_id': mine_type_id,
                'activity_status_id': activity_status_id
            })
            
            session.commit()
            
            print(f"   ✅ Mine {mine_name} aktualisiert:")
            print(f"      - Country ID: {country_id}")
            print(f"      - Region ID: {region_id}")
            print(f"      - Mine Type ID: {mine_type_id}")
            print(f"      - Activity Status ID: {activity_status_id}")
    
    conn.close()
    
    # Prüfe Ergebnis
    print("\n📊 [MIGRATION] Ergebnis-Prüfung:")
    conn = sqlite3.connect(get_normalized_db_path())
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT m.id, m.name, 
               c.name as country_name,
               r.name as region_name,
               mt.name as mine_type_name,
               ast.status as activity_status_name
        FROM mines m
        LEFT JOIN countries c ON m.country_id = c.id
        LEFT JOIN regions r ON m.region_id = r.id  
        LEFT JOIN mine_types mt ON m.mine_type_id = mt.id
        LEFT JOIN activity_statuses ast ON m.activity_status_id = ast.id
        WHERE m.id IN (12, 13, 14)
        ORDER BY m.id
    """)
    
    for row in cursor.fetchall():
        mine_id, name, country, region, mine_type, status = row
        print(f"✅ Mine {mine_id}: {name}")
        print(f"   Country: {country or 'NULL'}")
        print(f"   Region: {region or 'NULL'}")
        print(f"   Type: {mine_type or 'NULL'}")
        print(f"   Status: {status or 'NULL'}")
    
    conn.close()
    return True

if __name__ == "__main__":
    success = migrate_existing_mines()
    print(f"\n🎯 [MIGRATION] {'✅ ERFOLGREICH' if success else '❌ FEHLGESCHLAGEN'}")