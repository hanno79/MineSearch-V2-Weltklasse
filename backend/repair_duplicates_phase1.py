#!/usr/bin/env python3
"""
Author: rahn
Datum: 06.09.2025
Version: 1.0
Beschreibung: Phase 1 - Duplikate-Bereinigung in Lookup-Tabellen
Behebt die identifizierten Duplikate in mine_types, regions und companies
"""

import sqlite3
from datetime import datetime

def repair_mine_types_duplicates():
    """Bereinigt Duplikate in mine_types Tabelle"""
    
    conn = sqlite3.connect('mines.db')
    cursor = conn.cursor()
    
    print("🔧 PHASE 1.1: MINE_TYPES DUPLIKATE-BEREINIGUNG")
    print("=" * 60)
    
    try:
        # 1. Analysiere aktuelle Duplikate
        print("1.1 Analysiere bestehende mine_types...")
        cursor.execute("SELECT id, name, description FROM mine_types ORDER BY name")
        all_types = cursor.fetchall()
        
        print(f"   📊 Gefunden: {len(all_types)} Einträge")
        for type_id, name, desc in all_types:
            print(f"     {type_id}: {name}")
        
        # 2. Definiere Bereinigungsregeln (behalte nur deutsche Begriffe)
        print("\n1.2 Definiere Bereinigungsregeln...")
        
        # Mapping: Englische/Doppelte -> Deutsche Hauptbegriffe
        consolidation_map = {
            # Englisch -> Deutsch
            'Open-Pit': 'Tagebau',
            'Underground': 'Untertage', 
            'Surface': 'Tagebau',  # Surface = Tagebau
            'Quarry': 'Steinbruch',
            'Dredging': 'Schwimmbagger',
            'In-Situ-Leaching': 'Lösungsbergbau',
            'Placer': 'Seifenlagerstätte'
        }
        
        print("   📋 Konsolidierungs-Regeln:")
        for old_name, new_name in consolidation_map.items():
            print(f"     {old_name} -> {new_name}")
        
        # 3. Finde IDs für Konsolidierung
        print("\n1.3 Bestimme zu konsolidierende IDs...")
        
        consolidations = []
        for old_name, target_name in consolidation_map.items():
            # Finde alte ID
            cursor.execute("SELECT id FROM mine_types WHERE name = ?", (old_name,))
            old_result = cursor.fetchone()
            
            # Finde Ziel-ID (oder erstelle sie)
            cursor.execute("SELECT id FROM mine_types WHERE name = ?", (target_name,))
            target_result = cursor.fetchone()
            
            if old_result:
                old_id = old_result[0]
                
                if target_result:
                    target_id = target_result[0]
                    print(f"     Konsolidiere: {old_name} (ID:{old_id}) -> {target_name} (ID:{target_id})")
                    consolidations.append((old_id, target_id, old_name, target_name))
                else:
                    # Ziel existiert nicht - rename old to target
                    print(f"     Umbenenne: {old_name} (ID:{old_id}) -> {target_name}")
                    cursor.execute("UPDATE mine_types SET name = ? WHERE id = ?", (target_name, old_id))
        
        # 4. Aktualisiere Referenzen in mine_data_fields
        print("\n1.4 Aktualisiere Referenzen in mine_data_fields...")
        
        for old_id, target_id, old_name, target_name in consolidations:
            # Prüfe bestehende Referenzen
            cursor.execute("SELECT COUNT(*) FROM mine_data_fields WHERE mine_type_id = ?", (old_id,))
            ref_count = cursor.fetchone()[0]
            
            if ref_count > 0:
                print(f"     Aktualisiere {ref_count} Referenzen: {old_name} -> {target_name}")
                cursor.execute("""
                UPDATE mine_data_fields 
                SET mine_type_id = ? 
                WHERE mine_type_id = ?
                """, (target_id, old_id))
        
        # 5. Lösche obsolete Duplikate
        print("\n1.5 Lösche obsolete Duplikate...")
        
        for old_id, target_id, old_name, target_name in consolidations:
            cursor.execute("DELETE FROM mine_types WHERE id = ?", (old_id,))
            print(f"     ✅ Gelöscht: {old_name} (ID:{old_id})")
        
        # 6. Validierung
        print("\n1.6 Validierung nach Bereinigung...")
        
        cursor.execute("SELECT id, name FROM mine_types ORDER BY name")
        clean_types = cursor.fetchall()
        
        print(f"   📊 Finale mine_types ({len(clean_types)} Einträge):")
        for type_id, name in clean_types:
            print(f"     {type_id}: {name}")
        
        conn.commit()
        print("\n✅ MINE_TYPES BEREINIGUNG ABGESCHLOSSEN!")
        
        return len(consolidations)
        
    except Exception as e:
        print(f"❌ Fehler bei mine_types Bereinigung: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def repair_regions_duplicates():
    """Bereinigt Duplikate in regions Tabelle"""
    
    conn = sqlite3.connect('mines.db')
    cursor = conn.cursor()
    
    print("\n🔧 PHASE 1.2: REGIONS DUPLIKATE-BEREINIGUNG")
    print("=" * 60)
    
    try:
        # 1. Analysiere Quebec-Varianten
        print("1.1 Analysiere Quebec-Duplikate...")
        
        cursor.execute("SELECT id, name FROM regions WHERE name LIKE '%Quebec%' OR name LIKE '%Québec%' ORDER BY name")
        quebec_variants = cursor.fetchall()
        
        print(f"   📊 Quebec-Varianten gefunden: {len(quebec_variants)}")
        for region_id, name in quebec_variants:
            print(f"     {region_id}: {name}")
        
        if len(quebec_variants) <= 1:
            print("   ✅ Keine Quebec-Duplikate gefunden")
            return 0
        
        # 2. Bestimme Hauptvariante (erste/einfachste)
        main_quebec = quebec_variants[0]  # Nehme erste Variante
        main_id, main_name = main_quebec
        
        print(f"\n1.2 Konsolidiere zu Hauptvariante: '{main_name}' (ID:{main_id})")
        
        # 3. Konsolidiere andere Varianten
        consolidation_count = 0
        
        for region_id, name in quebec_variants[1:]:  # Alle außer der ersten
            print(f"     Konsolidiere: '{name}' (ID:{region_id}) -> '{main_name}' (ID:{main_id})")
            
            # Aktualisiere Referenzen
            cursor.execute("SELECT COUNT(*) FROM mine_data_fields WHERE region_id = ?", (region_id,))
            ref_count = cursor.fetchone()[0]
            
            if ref_count > 0:
                print(f"       Aktualisiere {ref_count} Referenzen in mine_data_fields")
                cursor.execute("UPDATE mine_data_fields SET region_id = ? WHERE region_id = ?", (main_id, region_id))
            
            cursor.execute("SELECT COUNT(*) FROM mines WHERE region_id = ?", (region_id,))
            mine_refs = cursor.fetchone()[0]
            
            if mine_refs > 0:
                print(f"       Aktualisiere {mine_refs} Referenzen in mines")
                cursor.execute("UPDATE mines SET region_id = ? WHERE region_id = ?", (main_id, region_id))
            
            # Lösche Duplikat
            cursor.execute("DELETE FROM regions WHERE id = ?", (region_id,))
            print(f"       ✅ Gelöscht: '{name}' (ID:{region_id})")
            
            consolidation_count += 1
        
        conn.commit()
        print(f"\n✅ REGIONS BEREINIGUNG ABGESCHLOSSEN! ({consolidation_count} Duplikate entfernt)")
        
        return consolidation_count
        
    except Exception as e:
        print(f"❌ Fehler bei regions Bereinigung: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def repair_companies_duplicates():
    """Bereinigt Duplikate in companies Tabelle"""
    
    conn = sqlite3.connect('mines.db')
    cursor = conn.cursor()
    
    print("\n🔧 PHASE 1.3: COMPANIES DUPLIKATE-BEREINIGUNG")
    print("=" * 60)
    
    try:
        # 1. Finde potentielle Duplikate durch ähnliche Namen
        print("1.1 Analysiere potentielle Company-Duplikate...")
        
        cursor.execute("SELECT id, name FROM companies ORDER BY name")
        all_companies = cursor.fetchall()
        
        print(f"   📊 Alle Companies: {len(all_companies)}")
        
        # 2. Definiere manuelle Duplikate-Regeln basierend auf bekannten Mustern
        duplicate_patterns = [
            # Varianten mit/ohne Inc/Corp/Ltd
            ('Goldcorp', ['Goldcorp Inc', 'Goldcorp Inc.', 'Goldcorp Corporation']),
            ('Barrick', ['Barrick Gold', 'Barrick Gold Corporation', 'Barrick Gold Corp']),
            ('Newmont', ['Newmont Corporation', 'Newmont Corp', 'Newmont Mining']),
            ('Rio Tinto', ['Rio Tinto Group', 'Rio Tinto plc']),
            ('Vale', ['Vale S.A.', 'Vale SA']),
            ('BHP', ['BHP Billiton', 'BHP Group'])
        ]
        
        consolidations = []
        
        for base_name, variations in duplicate_patterns:
            # Finde Basis-Company
            cursor.execute("SELECT id FROM companies WHERE name = ?", (base_name,))
            base_result = cursor.fetchone()
            
            base_id = None
            if base_result:
                base_id = base_result[0]
            else:
                # Suche nach einer der Varianten als Basis
                for variation in variations:
                    cursor.execute("SELECT id FROM companies WHERE name = ?", (variation,))
                    var_result = cursor.fetchone()
                    if var_result:
                        base_id = var_result[0]
                        base_name = variation  # Nutze gefundene Variante als Basis
                        break
            
            if not base_id:
                continue  # Keine der Varianten gefunden
            
            print(f"\n   Basis-Company: '{base_name}' (ID:{base_id})")
            
            # Finde zu konsolidierende Varianten
            for variation in variations:
                if variation == base_name:
                    continue
                    
                cursor.execute("SELECT id FROM companies WHERE name = ?", (variation,))
                var_result = cursor.fetchone()
                
                if var_result:
                    var_id = var_result[0]
                    print(f"     Konsolidiere: '{variation}' (ID:{var_id}) -> '{base_name}' (ID:{base_id})")
                    consolidations.append((var_id, base_id, variation, base_name))
        
        # 3. Führe Konsolidierungen durch
        print(f"\n1.2 Führe {len(consolidations)} Konsolidierungen durch...")
        
        for old_id, target_id, old_name, target_name in consolidations:
            # Aktualisiere Referenzen in mine_data_fields
            cursor.execute("SELECT COUNT(*) FROM mine_data_fields WHERE company_id = ?", (old_id,))
            ref_count = cursor.fetchone()[0]
            
            if ref_count > 0:
                print(f"     Aktualisiere {ref_count} Referenzen: '{old_name}' -> '{target_name}'")
                cursor.execute("UPDATE mine_data_fields SET company_id = ? WHERE company_id = ?", (target_id, old_id))
            
            # Lösche Duplikat
            cursor.execute("DELETE FROM companies WHERE id = ?", (old_id,))
            print(f"     ✅ Gelöscht: '{old_name}' (ID:{old_id})")
        
        # 4. Validierung
        cursor.execute("SELECT COUNT(*) FROM companies")
        final_count = cursor.fetchone()[0]
        
        print(f"\n1.3 Finale Validierung: {final_count} Companies verbleiben")
        
        conn.commit()
        print(f"\n✅ COMPANIES BEREINIGUNG ABGESCHLOSSEN! ({len(consolidations)} Duplikate entfernt)")
        
        return len(consolidations)
        
    except Exception as e:
        print(f"❌ Fehler bei companies Bereinigung: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    print("🧹 STARTE PHASE 1: DUPLIKATE-BEREINIGUNG")
    print("=" * 80)
    
    total_fixed = 0
    
    # Phase 1.1: mine_types
    fixed_types = repair_mine_types_duplicates()
    total_fixed += fixed_types
    
    # Phase 1.2: regions  
    fixed_regions = repair_regions_duplicates()
    total_fixed += fixed_regions
    
    # Phase 1.3: companies
    fixed_companies = repair_companies_duplicates()
    total_fixed += fixed_companies
    
    print(f"\n🎉 PHASE 1 ABGESCHLOSSEN!")
    print("=" * 80)
    print(f"✅ mine_types: {fixed_types} Duplikate bereinigt")
    print(f"✅ regions: {fixed_regions} Duplikate bereinigt") 
    print(f"✅ companies: {fixed_companies} Duplikate bereinigt")
    print(f"🎯 GESAMT: {total_fixed} Duplikate beseitigt")
    print()
    print("🔄 Bereit für Phase 2: Frontend Count-Fix")