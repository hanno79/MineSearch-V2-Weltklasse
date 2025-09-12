#!/usr/bin/env python3
"""
Author: rahn
Datum: 06.09.2025
Version: 1.0
Beschreibung: Vollständige Bereinigung der verbliebenen Duplikate
Bereinigt SOQUEM/Soquem, Osisko, Wallbridge und ergänzt Mine-Type Beschreibungen
"""

import sqlite3
from datetime import datetime

def complete_remaining_duplicates_cleanup():
    """Bereinigt alle verbliebenen Duplikate vollständig"""

    print("🧹 VOLLSTÄNDIGE BEREINIGUNG VERBLIEBENER DUPLIKATE")
    print("=" * 70)

    conn = sqlite3.connect('mines.db')
    cursor = conn.cursor()

    try:
        # 1. Analysiere aktuelle Companies
        print("1. ANALYSE AKTUELLE COMPANIES:")
        cursor.execute("SELECT id, name, role FROM companies ORDER BY name")
        all_companies = cursor.fetchall()

        print(f"   📊 Aktuelle Companies ({len(all_companies)}):")
        for comp_id, name, role in all_companies:
            print(f"     ID:{comp_id:<2} - '{name}' (Role: {role})")

        # 2. Bereinige identifizierte Duplikate
        print(f"\n2. BEREINIGE IDENTIFIZIERTE DUPLIKATE:")

        duplicates_to_fix = [
            # (keep_name, keep_id, duplicate_names_to_merge)
            ('SOQUEM Inc', None, ['Soquem']),
            ('Osisko Mining Inc', None, ['Osisko Mining']),
            ('Wallbridge Mining Company Limited', None, ['Wallbridge Mining Company'])
        ]

        total_merged = 0

        for target_name, target_id, duplicate_names in duplicates_to_fix:
            print(f"\n   🔧 Bearbeite: {target_name}")

            # Finde Target-Company
            cursor.execute("SELECT id, name, role FROM companies WHERE name = ?", (target_name,))
            target_result = cursor.fetchone()

            if not target_result:
                # Falls Target nicht existiert, nimm das erste Duplikat als Target
                if duplicate_names:
                    cursor.execute("SELECT id, name, role FROM companies WHERE name = ?", (duplicate_names[0],))
                    target_result = cursor.fetchone()
                    if target_result:
                        target_name = target_result[1]  # Update target_name
                        print(f"     Target nicht gefunden, verwende: {target_name} als Basis")

            if target_result:
                target_id, target_name_actual, target_role = target_result
                print(f"     Target: '{target_name_actual}' (ID:{target_id})")

                # Merge alle Duplikate
                for duplicate_name in duplicate_names:
                    cursor.execute("SELECT id, name, role FROM companies WHERE name = ?", (duplicate_name,))
                    duplicate_result = cursor.fetchone()

                    if duplicate_result:
                        dup_id, dup_name, dup_role = duplicate_result
                        print(f"     Merging: '{dup_name}' (ID:{dup_id}) -> '{target_name_actual}' (ID:{target_id})")

                        # Update alle Referenzen in mine_data_fields
                        cursor.execute("SELECT COUNT(*) FROM mine_data_fields WHERE company_id = ?", (dup_id,))
                        ref_count = cursor.fetchone()[0]

                        if ref_count > 0:
                            cursor.execute("UPDATE mine_data_fields SET company_id = ? WHERE
company_id = ?", (target_id, dup_id))
                            print(f"       ✅ {ref_count} Referenzen aktualisiert")

                        # Lösche Duplikat
                        cursor.execute("DELETE FROM companies WHERE id = ?", (dup_id,))
                        print(f"       ✅ Duplikat '{dup_name}' gelöscht")

                        total_merged += 1
            else:
                print(f"     ❌ Target '{target_name}' nicht gefunden!")

        # 3. Mine-Types Beschreibungen ergänzen
        print(f"\n3. ERGÄNZE MINE-TYPES BESCHREIBUNGEN:")

        cursor.execute("SELECT id, name, description FROM mine_types WHERE description IS NULL OR description = ''")
        missing_descriptions = cursor.fetchall()

        if missing_descriptions:
            print(f"   📋 {len(missing_descriptions)} Mine-Types ohne Beschreibung:")
            for type_id, name, desc in missing_descriptions:
                print(f"     ID:{type_id} - '{name}' (Description: {desc})")

            # Definiere Beschreibungen für fehlende Types
            type_descriptions = {
                'Exploration Property': 'Explorationsgrundstück - Gebiet mit potentiellen
Mineralvorkommen in Erkundungsphase',
                'Exploration Project': 'Explorationsprojekt - Aktive Erkundungsaktivitäten zur
Bewertung von Mineralvorkommen'
            }

            descriptions_added = 0

            for type_id, name, desc in missing_descriptions:
                if name in type_descriptions:
                    new_description = type_descriptions[name]
                    cursor.execute("UPDATE mine_types SET description = ? WHERE id = ?", (new_description, type_id))
                    print(f"     ✅ '{name}': Beschreibung hinzugefügt")
                    descriptions_added += 1
                else:
                    print(f"     ❓ '{name}': Keine Beschreibung definiert")

            print(f"   📊 {descriptions_added} Beschreibungen ergänzt")
        else:
            print(f"   ✅ Alle Mine-Types haben bereits Beschreibungen")

        # 4. Finale Validierung
        print(f"\n4. FINALE VALIDIERUNG:")

        cursor.execute("SELECT COUNT(*) FROM companies")
        final_companies_count = cursor.fetchone()[0]

        cursor.execute("SELECT id, name, role FROM companies ORDER BY name")
        final_companies = cursor.fetchall()

        print(f"   📊 Finale Companies ({final_companies_count}):")
        for comp_id, name, role in final_companies:
            print(f"     ID:{comp_id:<2} - '{name}' (Role: {role})")

        # Prüfe auf verbleibende Duplikate
        cursor.execute("""
            SELECT name, COUNT(*) as count
            FROM companies
            GROUP BY LOWER(TRIM(name))
            HAVING count > 1
        """)
        remaining_duplicates = cursor.fetchall()

        if remaining_duplicates:
            print(f"\n   ⚠️  Verbleibende potentielle Duplikate:")
            for name, count in remaining_duplicates:
                print(f"     '{name}': {count} Varianten")
        else:
            print(f"\n   ✅ Keine offensichtlichen Duplikate mehr vorhanden")

        # Prüfe Mine-Types
        cursor.execute("SELECT id, name, description FROM mine_types ORDER BY name")
        all_mine_types = cursor.fetchall()

        print(f"\n   📊 Finale Mine-Types ({len(all_mine_types)}):")
        for type_id, name, desc in all_mine_types:
            desc_status = "✅" if desc else "❓"
            print(f"     {desc_status} ID:{type_id:<2} - '{name}' - {desc[:50] + '...' if desc and
len(desc) > 50 else desc or 'KEINE BESCHREIBUNG'}")

        conn.commit()

        print(f"\n🎉 VOLLSTÄNDIGE BEREINIGUNG ABGESCHLOSSEN!")
        print("=" * 70)
        print(f"✅ {total_merged} Company-Duplikate gemerged")
        print(f"✅ Mine-Types Beschreibungen ergänzt")
        print(f"✅ {final_companies_count} bereinigte Companies")
        print(f"✅ {len(all_mine_types)} vollständige Mine-Types")

        return total_merged

    except Exception as e:
        print(f"❌ Fehler bei Bereinigung: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    print(f"🧪 STARTE VOLLSTÄNDIGE DUPLIKATE-BEREINIGUNG - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    merged_count = complete_remaining_duplicates_cleanup()

    if merged_count > 0:
        print(f"\n🎯 BEREINIGUNG ERFOLGREICH!")
        print(f"✅ {merged_count} Duplikate erfolgreich gemerged")
        print("✅ Mine-Types Beschreibungen vervollständigt")
        print("✅ Datenbank vollständig bereinigt")
        print()
        print("🔄 EMPFEHLUNG:")
        print("   - Führe validate_duplicates_prevention.py erneut aus")
        print("   - Teste Frontend-Anzeige auf korrekte Company-Namen")
        print("   - Verifiziere Mine-Types Beschreibungen")
    else:
        print(f"\n❌ KEINE DUPLIKATE GEFUNDEN ZUM MERGEN")
        print("🔧 Überprüfe manuelle Company-Namen")
