"""
Author: rahn
Datum: 24.08.2025
Version: 1.0
Beschreibung: Bereinigung von Akzent-Duplikaten in der Datenbank
"""

import sys
import os
from pathlib import Path

# Backend-Pfad dynamisch ermitteln (Env BACKEND_PATH oder relativ zu dieser Datei)
_backend_env = os.getenv("BACKEND_PATH")
if _backend_env and os.path.isdir(_backend_env):
    _backend_path = os.path.abspath(_backend_env)
else:
    _backend_path = str(Path(__file__).resolve().parent)

if _backend_path not in sys.path:
    sys.path.append(_backend_path)

from minesearch.database import db_manager
from minesearch.utils import normalize_accents, generate_name_variants
from sqlalchemy import text
from collections import defaultdict

def cleanup_accent_duplicates():
    """
    Bereinige Duplikate mit Akzent-Variationen in der Datenbank
    """
    print("🧹 STARTE AKZENT-DUPLIKAT BEREINIGUNG")
    print("=" * 50)
    
    with db_manager.get_session() as session:
        # 1. Finde alle Minen mit ihren normalisierten Namen
        result = session.execute(text("""
            SELECT DISTINCT mine_name 
            FROM search_results 
            ORDER BY mine_name
        """))
        all_mines = [row[0] for row in result.fetchall()]
        
        print(f"📊 Gefunden: {len(all_mines)} einzigartige Minennamen")
        
        # 2. Intelligente Gruppierung - berücksichtigt Akzente UND Präfixe wie "Mine"
        normalized_groups = defaultdict(list)
        
        def create_normalization_key(name):
            """Erstelle Normalisierungs-Schlüssel der sowohl Akzente als auch Präfixe behandelt"""
            # Normalisiere Akzente
            normalized = normalize_accents(name.lower())
            
            # Entferne häufige Mining-Präfixe/-Suffixe für Vergleich
            prefixes = ['mine', 'project', 'property', 'deposit', 'operation', 'site']
            words = normalized.split()
            
            # Entferne Präfixe/Suffixe
            filtered_words = []
            for word in words:
                if word not in prefixes:
                    filtered_words.append(word)
            
            # Fallback: wenn alle Wörter Präfixe waren, behalte Original
            if not filtered_words:
                filtered_words = words
            
            return ' '.join(sorted(filtered_words))  # Sortiert für besseren Vergleich
        
        for mine_name in all_mines:
            key = create_normalization_key(mine_name)
            normalized_groups[key].append(mine_name)
            print(f"   DEBUG: '{mine_name}' → Schlüssel: '{key}'")
        
        # 3. Finde Duplikate (Gruppen mit mehr als einem Namen)
        duplicates_found = 0
        total_entries_updated = 0
        
        for normalized_name, original_names in normalized_groups.items():
            if len(original_names) > 1:
                duplicates_found += 1
                print(f"\n🔍 DUPLIKAT GEFUNDEN: '{normalized_name}'")
                print(f"   Varianten: {original_names}")
                
                # Zähle Einträge pro Variante
                variant_counts = {}
                for original_name in original_names:
                    result = session.execute(text("""
                        SELECT COUNT(*) 
                        FROM search_results 
                        WHERE mine_name = :name
                    """), {'name': original_name})
                    count = result.fetchone()[0]
                    variant_counts[original_name] = count
                    print(f"     - '{original_name}': {count} Einträge")
                
                # Wähle häufigste Variante als Zielname
                target_name = max(variant_counts.keys(), key=variant_counts.get)
                print(f"   ✅ Zielname: '{target_name}' (häufigste Variante)")
                
                # Aktualisiere alle anderen Varianten auf den Zielnamen
                for original_name in original_names:
                    if original_name != target_name:
                        print(f"   🔄 Aktualisiere '{original_name}' → '{target_name}'")
                        
                        # Update alle Einträge
                        result = session.execute(text("""
                            UPDATE search_results 
                            SET mine_name = :target_name 
                            WHERE mine_name = :original_name
                        """), {
                            'target_name': target_name,
                            'original_name': original_name
                        })
                        
                        updated_count = result.rowcount
                        total_entries_updated += updated_count
                        print(f"     ✅ {updated_count} Einträge aktualisiert")
        
        # 4. Entferne Test Mine
        print(f"\n🗑️ ENTFERNE TEST-DATEN")
        result = session.execute(text("""
            DELETE FROM search_results 
            WHERE LOWER(mine_name) LIKE '%test%'
        """))
        
        test_entries_deleted = result.rowcount
        print(f"   ✅ {test_entries_deleted} Test-Einträge gelöscht")
        
        # Commit alle Änderungen
        session.commit()
        
        print(f"\n🎉 BEREINIGUNG ABGESCHLOSSEN!")
        print(f"=" * 50)
        print(f"📊 ZUSAMMENFASSUNG:")
        print(f"   • Duplikat-Gruppen gefunden: {duplicates_found}")
        print(f"   • Einträge aktualisiert: {total_entries_updated}")
        print(f"   • Test-Einträge gelöscht: {test_entries_deleted}")
        print(f"   • Gesamte Änderungen: {total_entries_updated + test_entries_deleted}")
        
        # 5. Validierung: Prüfe Eleonore-Duplikat
        print(f"\n🔍 VALIDIERUNG:")
        result = session.execute(text("""
            SELECT DISTINCT mine_name 
            FROM search_results 
            WHERE mine_name LIKE '%leonore%' OR mine_name LIKE '%léonore%'
            ORDER BY mine_name
        """))
        eleonore_variants = [row[0] for row in result.fetchall()]
        
        if len(eleonore_variants) <= 1:
            print(f"   ✅ Eleonore-Duplikat behoben: {eleonore_variants}")
        else:
            print(f"   ⚠️  Eleonore-Duplikat noch vorhanden: {eleonore_variants}")
        
        # Prüfe Test-Minen
        result = session.execute(text("""
            SELECT COUNT(*) 
            FROM search_results 
            WHERE LOWER(mine_name) LIKE '%test%'
        """))
        remaining_test_entries = result.fetchone()[0]
        
        if remaining_test_entries == 0:
            print(f"   ✅ Alle Test-Minen entfernt")
        else:
            print(f"   ⚠️  Noch {remaining_test_entries} Test-Einträge vorhanden")

if __name__ == "__main__":
    print("AKZENT-DUPLIKAT BEREINIGUNGSSCRIPT")
    print("Bereinigt Minen mit verschiedenen Akzent-Schreibweisen")
    print()
    
    # Bestätigung einholen
    response = input("Möchten Sie die Bereinigung durchführen? (ja/nein): ").lower()
    
    if response in ['ja', 'j', 'yes', 'y']:
        cleanup_accent_duplicates()
        print("\n✅ Bereinigung erfolgreich!")
    else:
        print("❌ Bereinigung abgebrochen.")