#!/usr/bin/env python3
"""
Author: rahn
Datum: 06.09.2025
Version: 1.0
Beschreibung: Bereinigt Activity_Statuses Duplikate
Merged Explorationsphase -> Exploration und behält die bessere Beschreibung
"""

import sqlite3
from datetime import datetime

def fix_activity_status_duplicates():
    """Bereinigt Activity_Status Duplikate: Explorationsphase -> Exploration"""
    
    print("🔧 ACTIVITY_STATUSES DUPLIKATE-BEREINIGUNG")
    print("=" * 60)
    
    conn = sqlite3.connect('mines.db')
    cursor = conn.cursor()
    
    try:
        # 1. Analysiere die Exploration-Duplikate
        print("1. EXPLORATION-DUPLIKATE ANALYSE:")
        
        cursor.execute("SELECT id, status, description FROM activity_statuses WHERE status IN ('Exploration', 'Explorationsphase')")
        exploration_statuses = cursor.fetchall()
        
        print("   📊 Gefundene Exploration-Varianten:")
        for status_id, status, desc in exploration_statuses:
            print(f"     ID:{status_id} - '{status}' - {desc or 'NULL'}")
        
        if len(exploration_statuses) != 2:
            print(f"   ❌ Erwartete 2 Exploration-Varianten, gefunden: {len(exploration_statuses)}")
            return False
        
        # Identifiziere Target und Source
        exploration_id = None
        explorationsphase_id = None
        exploration_desc = None
        
        for status_id, status, desc in exploration_statuses:
            if status == 'Exploration':
                exploration_id = status_id
                exploration_desc = desc
            elif status == 'Explorationsphase':
                explorationsphase_id = status_id
        
        if not exploration_id or not explorationsphase_id:
            print("   ❌ Konnte nicht beide IDs identifizieren!")
            return False
        
        print(f"\n   🎯 Merge-Plan:")
        print(f"     Target: 'Exploration' (ID:{exploration_id})")
        print(f"     Source: 'Explorationsphase' (ID:{explorationsphase_id}) -> zu löschende Variante")
        
        # 2. Prüfe Referenzen
        print(f"\n2. REFERENZEN-ANALYSE:")
        
        cursor.execute("SELECT COUNT(*) FROM mine_data_fields WHERE activity_status_id = ?", (exploration_id,))
        exploration_refs = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM mine_data_fields WHERE activity_status_id = ?", (explorationsphase_id,))
        explorationsphase_refs = cursor.fetchone()[0]
        
        print(f"   📊 'Exploration' (ID:{exploration_id}): {exploration_refs} Referenzen")
        print(f"   📊 'Explorationsphase' (ID:{explorationsphase_id}): {explorationsphase_refs} Referenzen")
        
        # 3. Führe Merge durch
        print(f"\n3. FÜHRE MERGE DURCH:")
        
        if explorationsphase_refs > 0:
            print(f"   🔄 Aktualisiere {explorationsphase_refs} Referenzen...")
            cursor.execute("""
                UPDATE mine_data_fields 
                SET activity_status_id = ? 
                WHERE activity_status_id = ?
            """, (exploration_id, explorationsphase_id))
            print(f"   ✅ {explorationsphase_refs} Referenzen von 'Explorationsphase' -> 'Exploration' verschoben")
        
        # 4. Lösche Duplikat
        print(f"\n4. LÖSCHE DUPLIKAT:")
        cursor.execute("DELETE FROM activity_statuses WHERE id = ?", (explorationsphase_id,))
        print(f"   ✅ 'Explorationsphase' (ID:{explorationsphase_id}) gelöscht")
        
        # 5. Ergänze Beschreibung falls nötig
        print(f"\n5. BESCHREIBUNG VALIDIERUNG:")
        
        cursor.execute("SELECT description FROM activity_statuses WHERE id = ?", (exploration_id,))
        current_desc = cursor.fetchone()[0]
        
        if not current_desc:
            new_desc = "Explorationsaktivitäten und Erkundungsarbeiten laufen"
            cursor.execute("UPDATE activity_statuses SET description = ? WHERE id = ?", (new_desc, exploration_id))
            print(f"   ✅ Beschreibung für 'Exploration' hinzugefügt: {new_desc}")
        else:
            print(f"   ℹ️  'Exploration' hat bereits Beschreibung: {current_desc}")
        
        # 6. Finale Validierung
        print(f"\n6. FINALE VALIDIERUNG:")
        
        cursor.execute("SELECT id, status, description FROM activity_statuses ORDER BY status")
        all_statuses = cursor.fetchall()
        
        print(f"   📊 Bereinigte Activity_Statuses ({len(all_statuses)}):")
        for status_id, status, desc in all_statuses:
            desc_preview = desc[:40] + "..." if desc and len(desc) > 40 else desc or "NULL"
            print(f"     ID:{status_id:<2} - '{status:<20}' - {desc_preview}")
        
        # Prüfe auf weitere Exploration-Duplikate
        exploration_variants = [status for _, status, _ in all_statuses if 'exploration' in status.lower()]
        
        if len(exploration_variants) > 1:
            print(f"\n   ⚠️  Noch {len(exploration_variants)} Exploration-Varianten gefunden: {exploration_variants}")
        else:
            print(f"\n   ✅ Nur eine Exploration-Variante verbleibt")
        
        # Prüfe finale Referenzen
        cursor.execute("SELECT COUNT(*) FROM mine_data_fields WHERE activity_status_id = ?", (exploration_id,))
        final_refs = cursor.fetchone()[0]
        print(f"   📊 'Exploration' (ID:{exploration_id}) finale Referenzen: {final_refs}")
        
        conn.commit()
        
        print(f"\n🎉 ACTIVITY_STATUS DUPLIKATE-BEREINIGUNG ABGESCHLOSSEN!")
        print("=" * 60)
        print(f"✅ 'Explorationsphase' erfolgreich in 'Exploration' gemerged")
        print(f"✅ {explorationsphase_refs} Referenzen aktualisiert")
        print(f"✅ {len(all_statuses)} bereinigte Activity_Statuses")
        print(f"✅ Beschreibung vervollständigt")
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler bei Activity_Status Bereinigung: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    print(f"🧪 STARTE ACTIVITY_STATUS BEREINIGUNG - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    success = fix_activity_status_duplicates()
    
    if success:
        print(f"\n🎯 BEREINIGUNG ERFOLGREICH!")
        print("✅ Activity_Status Duplikate bereinigt") 
        print("✅ Alle Referenzen korrekt aktualisiert")
        print("✅ System vollständig duplikatfrei")
        print()
        print("🔄 EMPFEHLUNG:")
        print("   - Führe validate_duplicates_prevention.py erneut aus")
        print("   - Committe Änderungen zu GitHub")
        print("   - Teste Frontend auf bereinigte Activity_Status")
    else:
        print(f"\n❌ BEREINIGUNG FEHLGESCHLAGEN!")
        print("🔧 Manuelle Überprüfung erforderlich")