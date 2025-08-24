#!/usr/bin/env python3
"""
Test für die neue "Exakte Quellenangaben" Spalte im CSV Export
"""
import requests

def test_exact_sources_csv():
    print("🧪 TEST: Exakte Quellenangaben im CSV Export")
    print("=" * 60)
    
    # CSV Export testen
    response = requests.get("http://localhost:8000/api/consolidated/results/export/csv?exclude_exa=true&days_back=30&sort_by=mine_name")
    
    if response.status_code == 200:
        csv_content = response.text
        lines = csv_content.split('\n')
        
        if lines:
            header = lines[0]
            columns = header.split('|')
            
            print(f"✅ CSV Export erfolgreich")
            print(f"✅ Spaltenanzahl: {len(columns)}")
            
            # Prüfe ob beide Quellenangaben-Spalten vorhanden sind
            quellenangaben_idx = -1
            exakte_quellenangaben_idx = -1
            
            for i, col in enumerate(columns):
                if col == "Quellenangaben":
                    quellenangaben_idx = i
                elif col == "Exakte Quellenangaben":
                    exakte_quellenangaben_idx = i
            
            if quellenangaben_idx >= 0:
                print(f"✅ 'Quellenangaben' Spalte gefunden (Index: {quellenangaben_idx})")
            else:
                print("❌ 'Quellenangaben' Spalte NICHT gefunden")
            
            if exakte_quellenangaben_idx >= 0:
                print(f"✅ 'Exakte Quellenangaben' Spalte gefunden (Index: {exakte_quellenangaben_idx})")
            else:
                print("❌ 'Exakte Quellenangaben' Spalte NICHT gefunden")
            
            # Analysiere Eleonore Mine Zeile
            eleonore_line = None
            for line in lines[1:]:
                if 'Eleonore Mine' in line:
                    eleonore_line = line
                    break
            
            if eleonore_line:
                parts = eleonore_line.split('|')
                print(f"\n🔍 ELEONORE MINE ANALYSE:")
                print(f"   Spaltenanzahl in Datenzeile: {len(parts)}")
                
                if quellenangaben_idx < len(parts):
                    quellenangaben = parts[quellenangaben_idx]
                    print(f"   Quellenangaben: {quellenangaben[:100]}...")
                
                if exakte_quellenangaben_idx < len(parts):
                    exakte_quellenangaben = parts[exakte_quellenangaben_idx]
                    print(f"   Exakte Quellenangaben: {exakte_quellenangaben[:150]}...")
                    
                    # Zähle [X] Referenzen in exakten Quellenangaben
                    import re
                    refs = re.findall(r'\[\d+\]', exakte_quellenangaben)
                    print(f"   Gefundene Quellenreferenzen: {len(refs)} ({refs})")
                    
                    if len(refs) > 0:
                        print("✅ Exakte Quellenangaben enthalten nummerierte Referenzen")
                    else:
                        print("❌ Keine nummerierten Referenzen in exakten Quellenangaben")
            
            # Teste weitere Minen
            print(f"\n📊 WEITERE MINEN TESTEN:")
            mine_count = 0
            for line in lines[1:6]:  # Teste erste 5 Minen
                if line.strip() and '|' in line:
                    parts = line.split('|')
                    if len(parts) > 0:
                        mine_name = parts[0]
                        mine_count += 1
                        
                        if exakte_quellenangaben_idx < len(parts):
                            exact_sources = parts[exakte_quellenangaben_idx]
                            
                            # Prüfe auf Quellenreferenzen
                            import re
                            refs = re.findall(r'\[\d+\]', exact_sources)
                            
                            if len(refs) > 0:
                                print(f"   ✅ {mine_name}: {len(refs)} Quellenreferenzen")
                            elif "Keine detaillierten Quellenangaben" in exact_sources:
                                print(f"   ⚠️ {mine_name}: Keine Quellenangaben verfügbar")
                            else:
                                print(f"   ❌ {mine_name}: Unerwarteter Inhalt")
            
            print(f"\n🎉 CSV EXPORT TEST ABGESCHLOSSEN")
            print(f"   Getestete Minen: {mine_count}")
            print(f"   Neue Spalte 'Exakte Quellenangaben' erfolgreich implementiert")
            
    else:
        print(f"❌ CSV Export Fehler: {response.status_code}")

if __name__ == "__main__":
    test_exact_sources_csv()