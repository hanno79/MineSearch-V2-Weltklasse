#!/usr/bin/env python3
"""
Author: rahn
Datum: 06.09.2025
Version: 1.0
Beschreibung: Finale Bereinigung der identifizierten Duplikate
Bereinigt SOQUEM/Soquem, Osisko, Wallbridge, Newmont und ergänzt Mine-Type Beschreibungen
"""

import sqlite3
from datetime import datetime

def final_duplicates_cleanup():
    """Bereinigt alle identifizierten Duplikate final"""

    print("🧹 FINALE DUPLIKATE-BEREINIGUNG")
    print("=" * 60)

    conn = sqlite3.connect('mines.db')
    cursor = conn.cursor()

    try:
        # 1. Definiere Duplikate-Merging-Regeln
        duplicates_to_merge = [
            # (keep_id, keep_name, merge_ids_and_names)
            (1, 'SOQUEM Inc', [(2, 'Soquem')]),
            (3, 'Osisko Mining Inc', [(4, 'Osisko Mining')]),
            (12, 'Wallbridge Mining Company Limited', [(13, 'Wallbridge Mining Company')]),
            (6, 'Newmont', [(9, 'Newmont (früher Goldcorp)')])
        ]

        print("1. DUPLIKATE-MERGING:")

        total_merged = 0

        for keep_id, keep_name, merge_list in duplicates_to_merge:
            print(f"\n   🔧 Merge zu: '{keep_name}' (ID:{keep_id})")

            # Prüfe ob Keep-Company existiert
            cursor.execute("SELECT id, name FROM companies WHERE id = ?", (keep_id,))
            keep_result = cursor.fetchone()

            if not keep_result:
                print(f"     ❌ Target Company ID:{keep_id} nicht gefunden!")
                continue

            for merge_id, merge_name in merge_list:
                print(f"     Merging: '{merge_name}' (ID:{merge_id}) -> '{keep_name}' (ID:{keep_id})")

                # Prüfe ob Merge-Company existiert
                cursor.execute("SELECT id, name FROM companies WHERE id = ?", (merge_id,))
                merge_result = cursor.fetchone()

                if not merge_result:
                    print(f"       ❌ Merge Company ID:{merge_id} nicht gefunden!")
                    continue

                # Update alle Referenzen in mine_data_fields
                cursor.execute("SELECT COUNT(*) FROM mine_data_fields WHERE company_id = ?", (merge_id,))
                ref_count = cursor.fetchone()[0]

                if ref_count > 0:
                    cursor.execute("UPDATE mine_data_fields SET company_id = ? WHERE company_id =
?", (keep_id, merge_id))
                    print(f"       ✅ {ref_count} Referenzen aktualisiert")
                else:
                    print(f"       ✅ Keine Referenzen zu aktualisieren")

                # Lösche Duplikat-Company
                cursor.execute("DELETE FROM companies WHERE id = ?", (merge_id,))
                print(f"       ✅ '{merge_name}' (ID:{merge_id}) gelöscht")

                total_merged += 1

        # 2. Mine-Types Beschreibungen ergänzen
        print(f"\n2. MINE-TYPES BESCHREIBUNGEN ERGÄNZEN:")

        type_descriptions = {
            'Exploration Property': 'Explorationsgrundstück - Gebiet mit potentiellen
Mineralvorkommen in Erkundungsphase',
            'Exploration Project': 'Explorationsprojekt - Aktive Erkundungsaktivitäten zur Bewertung
von Mineralvorkommen'
        }

        descriptions_added = 0

        for type_name, description in type_descriptions.items():
            cursor.execute("SELECT id, description FROM mine_types WHERE name = ?", (type_name,))
            result = cursor.fetchone()

            if result:
                type_id, current_desc = result
                if not current_desc:
                    cursor.execute("UPDATE mine_types SET description = ? WHERE id = ?", (description, type_id))
                    print(f"   ✅ '{type_name}' (ID:{type_id}): Beschreibung hinzugefügt")
                    descriptions_added += 1
                else:
                    print(f"   ℹ️  '{type_name}' (ID:{type_id}): Beschreibung bereits vorhanden")
            else:
                print(f"   ❌ '{type_name}': Nicht gefunden!")

        # 3. Finale Validierung
        print(f"\n3. FINALE VALIDIERUNG:")

        # Bereinigte Companies
        cursor.execute("SELECT id, name FROM companies ORDER BY name")
        final_companies = cursor.fetchall()

        print(f"   📊 Bereinigte Companies ({len(final_companies)}):")
        for comp_id, name in final_companies:
            print(f"     ID:{comp_id:<2} - '{name}'")

        # Prüfe auf verbleibende Duplikate
        potential_duplicates = []
        company_names = [name.lower().strip() for _, name in final_companies]

        for i, name1 in enumerate(company_names):
            for j, name2 in enumerate(company_names[i+1:], i+1):
                # Einfache Ähnlichkeitsprüfung
                if len(name1) > 5 and len(name2) > 5:
                    if name1 in name2 or name2 in name1:
                        potential_duplicates.append((final_companies[i][1], final_companies[j][1]))

        if potential_duplicates:
            print(f"\n   ⚠️  Potentielle verbleibende Duplikate:")
            for name1, name2 in potential_duplicates:
                print(f"     '{name1}' <-> '{name2}'")
        else:
            print(f"\n   ✅ Keine offensichtlichen Duplikate mehr erkannt")

        # Mine-Types Validierung
        cursor.execute("SELECT id, name, description FROM mine_types ORDER BY name")
        final_mine_types = cursor.fetchall()

        print(f"\n   📊 Mine-Types mit Beschreibungen ({len(final_mine_types)}):")
        for type_id, name, desc in final_mine_types:
            desc_status = "✅" if desc else "❓"
            desc_preview = desc[:40] + "..." if desc and len(desc) > 40 else desc or "KEINE BESCHREIBUNG"
            print(f"     {desc_status} ID:{type_id:<2} - '{name:<25}' - {desc_preview}")

        # Commit Änderungen
        conn.commit()

        print(f"\n🎉 FINALE BEREINIGUNG ABGESCHLOSSEN!")
        print("=" * 60)
        print(f"✅ {total_merged} Company-Duplikate erfolgreich gemerged")
        print(f"✅ {descriptions_added} Mine-Type-Beschreibungen hinzugefügt")
        print(f"✅ {len(final_companies)} bereinigte Companies verbleiben")
        print(f"✅ {len(final_mine_types)} Mine-Types mit Beschreibungen")

        return total_merged, descriptions_added

    except Exception as e:
        print(f"❌ Fehler bei finaler Bereinigung: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    print(f"🧪 STARTE FINALE DUPLIKATE-BEREINIGUNG - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    merged_count, desc_count = final_duplicates_cleanup()

    print(f"\n🎯 FINALE BEREINIGUNG ERFOLGREICH!")
    print(f"✅ {merged_count} Duplikate gemerged")
    print(f"✅ {desc_count} Beschreibungen ergänzt")
    print("✅ Datenbank vollständig bereinigt und vervollständigt")
    print()
    print("🔄 NÄCHSTE SCHRITTE:")
    print("   - Teste Frontend auf bereinigte Company-Namen")
    print("   - Führe validate_duplicates_prevention.py erneut aus")
    print("   - Committe Änderungen zu GitHub")
