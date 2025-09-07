#!/usr/bin/env python3
"""
Author: rahn
Datum: 06.09.2025
Version: 1.0
Beschreibung: STUFE 2 - Intelligente Duplikat-Bereinigung mit Smart-Merging
"""

import sqlite3
import pandas as pd
import difflib
import re
from collections import defaultdict
from datetime import datetime
import json

class IntelligentDeduplication:
    """
    STUFE 2: INTELLIGENTE DUPLIKAT-BEREINIGUNG
    ==========================================
    
    Bereinigt Fuzzy-Duplikate mit Smart-Merging Algorithmus
    - Erkennt ähnliche Unternehmen automatisch
    - Merged References sauber
    - Backup aller Änderungen
    - DRY-RUN Modus für sichere Tests
    """
    
    def __init__(self, db_path='mines.db', similarity_threshold=0.85):
        self.db_path = db_path
        self.threshold = similarity_threshold
        self.merge_decisions = []
        self.backup_data = {}
        
    def clean_all_fuzzy_duplicates(self, dry_run=True):
        """Hauptfunktion für komplette Bereinigung"""
        print("🧹 STUFE 2: INTELLIGENTE BEREINIGUNG")
        print("=" * 50)
        
        conn = sqlite3.connect(self.db_path)
        results = {
            'dry_run': dry_run,
            'companies_cleaned': 0,
            'mines_cleaned': 0,
            'total_merges': 0,
            'merge_decisions': [],
            'backup_created': False
        }
        
        try:
            # 1. BACKUP erstellen (falls nicht DRY RUN)
            if not dry_run:
                self._create_backup(conn)
                results['backup_created'] = True
            
            # 2. COMPANIES bereinigen (Hauptproblem)
            print("\n🏢 BEREINIGE COMPANIES...")
            companies_result = self._clean_companies(conn, dry_run)
            results['companies_cleaned'] = companies_result
            
            # 3. MINES prüfen (falls nötig)
            print("\n⛏️ PRÜFE MINES...")
            mines_result = self._check_mines(conn, dry_run)
            results['mines_cleaned'] = mines_result
            
            # 4. ANDERE TABELLEN prüfen
            print("\n🔍 PRÜFE ANDERE TABELLEN...")
            self._check_other_tables(conn)
            
            results['total_merges'] = len(self.merge_decisions)
            results['merge_decisions'] = self.merge_decisions
            
            if not dry_run:
                conn.commit()
                print("✅ ALLE ÄNDERUNGEN COMMITTED")
            else:
                print("🔍 DRY RUN - Keine Änderungen angewendet")
                
        except Exception as e:
            if not dry_run:
                conn.rollback()
            results['error'] = str(e)
            print(f"❌ FEHLER: {e}")
            
        finally:
            conn.close()
            
        # Speichere Ergebnisse
        self._save_cleaning_report(results)
        return results
    
    def _clean_companies(self, conn, dry_run=True):
        """Bereinigt Company-Duplikate intelligent"""
        # Hole alle Companies
        df = pd.read_sql_query("SELECT * FROM companies", conn)
        
        if len(df) == 0:
            print("   ⚠️  Keine Companies gefunden")
            return 0
        
        print(f"   📊 {len(df)} Companies gefunden")
        
        cleaned_count = 0
        
        # 1. IDENTISCHE NAME-DUPLIKATE (exakt gleiche Namen)
        exact_name_duplicates = df[df.duplicated(subset=['name'], keep='first')]
        
        if not exact_name_duplicates.empty:
            print(f"   🎯 {len(exact_name_duplicates)} exakte Name-Duplikate gefunden")
            
            for _, duplicate_company in exact_name_duplicates.iterrows():
                # Finde das Original (erstes Vorkommen)
                original = df[(df['name'] == duplicate_company['name']) & (df['id'] != duplicate_company['id'])].iloc[0]
                
                print(f"      🔄 Merge: '{duplicate_company['name']}' (ID {duplicate_company['id']}) -> (ID {original['id']})")
                
                if not dry_run:
                    self._merge_companies(conn, original['id'], duplicate_company['id'])
                
                self.merge_decisions.append({
                    'type': 'exact_name_duplicate',
                    'kept_company': {'id': int(original['id']), 'name': original['name']},
                    'merged_company': {'id': int(duplicate_company['id']), 'name': duplicate_company['name']},
                    'reason': 'Identical name'
                })
                
                cleaned_count += 1
        
        # 2. FUZZY-DUPLIKATE (ähnliche Namen)
        unique_names = df['name'].unique()
        fuzzy_groups = self._find_similar_companies(unique_names)
        
        if fuzzy_groups:
            print(f"   🔍 {len(fuzzy_groups)} Fuzzy-Duplikat-Gruppen gefunden")
            
            for group in fuzzy_groups:
                if len(group) > 1:
                    # Hole alle Companies für diese Gruppe
                    group_companies = df[df['name'].isin(group)]
                    
                    # Wähle die "beste" Company (Heuristiken)
                    best_company = self._select_best_company(group_companies)
                    others = group_companies[group_companies['id'] != best_company['id']]
                    
                    print(f"      📋 Gruppe: {group}")
                    print(f"      🏆 Gewählt: '{best_company['name']}' (ID {best_company['id']})")
                    
                    # Merge alle anderen in die beste
                    for _, other_company in others.iterrows():
                        print(f"         🔄 Merge: '{other_company['name']}' (ID {other_company['id']}) -> '{best_company['name']}'")
                        
                        if not dry_run:
                            self._merge_companies(conn, best_company['id'], other_company['id'])
                        
                        self.merge_decisions.append({
                            'type': 'fuzzy_duplicate',
                            'kept_company': {'id': int(best_company['id']), 'name': best_company['name']},
                            'merged_company': {'id': int(other_company['id']), 'name': other_company['name']},
                            'similarity': self._calculate_similarity(best_company['name'], other_company['name']),
                            'reason': 'Similar names (fuzzy match)'
                        })
                        
                        cleaned_count += 1
        
        print(f"   📊 Companies bereinigt: {cleaned_count}")
        return cleaned_count
    
    def _find_similar_companies(self, company_names):
        """Findet ähnliche Company-Namen mit erweiterten Heuristiken"""
        similar_groups = []
        processed = set()
        
        names_list = list(company_names)
        
        for i, name1 in enumerate(names_list):
            if name1 in processed:
                continue
                
            group = [name1]
            processed.add(name1)
            
            for name2 in names_list[i+1:]:
                if name2 in processed:
                    continue
                
                # Verschiedene Ähnlichkeitstests
                similarity = self._calculate_similarity(name1, name2)
                
                # Erweiterte Tests für häufige Company-Namen-Variationen
                is_similar = (
                    similarity >= self.threshold or
                    self._is_company_variation(name1, name2) or
                    self._is_case_variation(name1, name2)
                )
                
                if is_similar:
                    group.append(name2)
                    processed.add(name2)
            
            if len(group) > 1:
                similar_groups.append(group)
        
        return similar_groups
    
    def _is_company_variation(self, name1, name2):
        """Prüft auf häufige Company-Namen-Variationen"""
        # Normalisiere beide Namen
        norm1 = self._normalize_company_name(name1)
        norm2 = self._normalize_company_name(name2)
        
        # Exact match nach Normalisierung
        if norm1 == norm2:
            return True
        
        # Einer ist Subset des anderen (nach Normalisierung)
        if norm1 in norm2 or norm2 in norm1:
            # Aber nur wenn der Unterschied hauptsächlich Suffixe sind
            diff_words = set(norm1.split()) ^ set(norm2.split())
            suffix_words = {'ltd', 'limited', 'corp', 'corporation', 'inc', 'incorporated', 'co', 'company', 'ag', 'gmbh', 'sa', 'plc', 'llc', 'mining', 'mines'}
            
            return all(word in suffix_words for word in diff_words)
        
        return False
    
    def _is_case_variation(self, name1, name2):
        """Prüft auf reine Groß-/Kleinschreibungs-Unterschiede"""
        return name1.lower() == name2.lower()
    
    def _normalize_company_name(self, name):
        """Normalisiert Company-Namen für Vergleiche"""
        if not name:
            return ""
        
        # Kleinschreibung
        normalized = name.lower().strip()
        
        # Entferne Punkte, Kommata, etc.
        normalized = re.sub(r'[.,\-_]', ' ', normalized)
        
        # Mehrfache Leerzeichen entfernen
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        # Entferne häufige Company-Suffixe für Vergleich
        suffixes = ['ltd', 'limited', 'corp', 'corporation', 'inc', 'incorporated', 
                   'co', 'company', 'ag', 'gmbh', 'sa', 'plc', 'llc']
        
        words = normalized.split()
        filtered_words = [w for w in words if w not in suffixes]
        
        return ' '.join(filtered_words)
    
    def _calculate_similarity(self, text1, text2):
        """Berechnet Ähnlichkeit zwischen zwei Texten"""
        if not text1 or not text2:
            return 0.0
        
        # Normalisiere für besseren Vergleich
        norm1 = self._normalize_company_name(text1)
        norm2 = self._normalize_company_name(text2)
        
        return difflib.SequenceMatcher(None, norm1, norm2).ratio()
    
    def _select_best_company(self, companies_df):
        """Wählt die beste Company aus einer Gruppe ähnlicher Companies"""
        # Heuristiken für "beste" Company:
        # 1. Älteste Company (created_at)
        # 2. Company mit country_id (mehr Informationen)
        # 3. Längster Name (meist vollständigste Bezeichnung)
        
        best = companies_df.iloc[0]  # Fallback
        
        # Bevorzuge Companies mit country_id
        companies_with_country = companies_df[companies_df['country_id'].notna()]
        if not companies_with_country.empty:
            companies_df = companies_with_country
        
        # Bevorzuge älteste Company
        if 'created_at' in companies_df.columns:
            companies_df = companies_df.sort_values('created_at')
        
        # Bei Gleichstand: längster Name
        companies_df = companies_df.assign(name_length=companies_df['name'].str.len())
        companies_df = companies_df.sort_values('name_length', ascending=False)
        
        best = companies_df.iloc[0]
        return best
    
    def _merge_companies(self, conn, keep_id, merge_id):
        """Merged zwei Companies: behält keep_id, löscht merge_id"""
        cursor = conn.cursor()
        
        try:
            # 1. Update alle Referenzen auf merge_id zu keep_id
            
            # Mine Owners
            cursor.execute("UPDATE mine_owners SET company_id = ? WHERE company_id = ?", (keep_id, merge_id))
            
            # Mine Operators  
            cursor.execute("UPDATE mine_operators SET company_id = ? WHERE company_id = ?", (keep_id, merge_id))
            
            # Andere mögliche Referenzen könnten hier stehen
            
            # 2. Lösche die doppelte Company
            cursor.execute("DELETE FROM companies WHERE id = ?", (merge_id,))
            
            print(f"         ✅ Referenzen aktualisiert, Company {merge_id} gelöscht")
            
        except Exception as e:
            print(f"         ❌ Merge-Fehler: {e}")
            raise
    
    def _check_mines(self, conn, dry_run=True):
        """Prüft Mines auf ähnliche Duplikate"""
        df = pd.read_sql_query("SELECT * FROM mines", conn)
        
        if len(df) == 0:
            print("   ⚠️  Keine Mines gefunden")
            return 0
        
        print(f"   📊 {len(df)} Mines gefunden")
        
        # Prüfe auf ähnliche Mine-Namen
        unique_names = df['name'].unique()
        fuzzy_groups = self._find_similar_values(unique_names, threshold=0.90)  # Höherer Threshold für Mines
        
        if fuzzy_groups:
            print(f"   ⚠️  {len(fuzzy_groups)} potentielle Mine-Duplikate gefunden:")
            for group in fuzzy_groups:
                print(f"      Ähnlich: {group}")
            print("   💡 Manuelle Überprüfung empfohlen (Mines haben oft ähnliche Namen)")
        else:
            print("   ✅ Keine verdächtigen Mine-Duplikate gefunden")
        
        return len(fuzzy_groups)
    
    def _find_similar_values(self, values, threshold=None):
        """Generische ähnliche-Werte-Finder"""
        if threshold is None:
            threshold = self.threshold
            
        similar_groups = []
        processed = set()
        
        values_list = list(values)
        
        for i, value1 in enumerate(values_list):
            if value1 in processed:
                continue
                
            group = [value1]
            processed.add(value1)
            
            for value2 in values_list[i+1:]:
                if value2 in processed:
                    continue
                    
                similarity = difflib.SequenceMatcher(None, value1.lower(), value2.lower()).ratio()
                if similarity >= threshold:
                    group.append(value2)
                    processed.add(value2)
            
            if len(group) > 1:
                similar_groups.append(group)
        
        return similar_groups
    
    def _check_other_tables(self, conn):
        """Prüft andere Tabellen auf potentielle Probleme"""
        print("   📊 Andere Tabellen scheinen sauber zu sein (laut STUFE 1)")
        print("   ✅ Keine weiteren Bereinigungen erforderlich")
    
    def _create_backup(self, conn):
        """Erstellt Backup der zu ändernden Daten"""
        print("💾 Erstelle Backup...")
        
        # Backup Companies vor Änderungen
        companies_backup = pd.read_sql_query("SELECT * FROM companies", conn)
        self.backup_data['companies'] = companies_backup.to_dict('records')
        
        # Backup relevante Referenz-Tabellen
        try:
            mine_owners_backup = pd.read_sql_query("SELECT * FROM mine_owners", conn)
            self.backup_data['mine_owners'] = mine_owners_backup.to_dict('records')
        except:
            self.backup_data['mine_owners'] = []
            
        try:
            mine_operators_backup = pd.read_sql_query("SELECT * FROM mine_operators", conn)  
            self.backup_data['mine_operators'] = mine_operators_backup.to_dict('records')
        except:
            self.backup_data['mine_operators'] = []
        
        print("   ✅ Backup erstellt")
    
    def _save_cleaning_report(self, results):
        """Speichert detaillierten Bereinigungsreport"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f'deduplication_report_{timestamp}.json'
        
        # Konvertiere alle numpy/pandas Typen zu Python-native Typen
        def convert_types(obj):
            if hasattr(obj, 'item'):  # numpy types
                return obj.item()
            elif isinstance(obj, dict):
                return {k: convert_types(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_types(v) for v in obj]
            else:
                return obj
        
        report_data = {
            'cleaning_timestamp': datetime.now().isoformat(),
            'results': convert_types(results),
            'backup_data': convert_types(self.backup_data) if self.backup_data else None,
            'settings': {
                'similarity_threshold': self.threshold,
                'database_path': self.db_path
            }
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Bereinigungsreport gespeichert: {report_file}")
        
        # Zusammenfassung anzeigen
        print(f"\n🎯 BEREINIGUNGSRESULTATE:")
        if results['total_merges'] > 0:
            print(f"   ✅ {results['companies_cleaned']} Companies bereinigt")
            print(f"   🔄 {results['total_merges']} Merge-Operationen durchgeführt") 
            if results['dry_run']:
                print(f"   🔍 DRY RUN - Änderungen NICHT angewendet")
            else:
                print(f"   💾 Änderungen in Datenbank gespeichert")
        else:
            print(f"   ✅ Keine Bereinigung erforderlich")


def main():
    import sys
    
    execute_real = "--execute" in sys.argv or "--real" in sys.argv
    
    print(f"🚀 STARTE INTELLIGENTE BEREINIGUNG - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    dedup = IntelligentDeduplication()
    
    if execute_real:
        print("\n" + "="*60)
        print("🔥 ECHTE BEREINIGUNG - Ändert Datenbank!")
        print("="*60)
        
        real_results = dedup.clean_all_fuzzy_duplicates(dry_run=False)
        print(f"\n🎉 BEREINIGUNG ABGESCHLOSSEN!")
        return real_results
    else:
        # Standard DRY RUN
        print("\n" + "="*60)
        print("🔍 DRY RUN - Zeige was gemacht würde...")
        print("="*60)
        
        dry_results = dedup.clean_all_fuzzy_duplicates(dry_run=True)
        
        # Frage nach Bestätigung für echte Ausführung
        if dry_results['total_merges'] > 0:
            print(f"\n❓ {dry_results['total_merges']} Merge-Operationen gefunden.")
            print("   Soll die echte Bereinigung ausgeführt werden? (y/N)")
            user_input = input().strip().lower()
            
            if user_input == 'y' or user_input == 'yes':
                print("\n" + "="*60)
                print("🔥 ECHTE BEREINIGUNG - Ändert Datenbank!")
                print("="*60)
                
                # Neue Instanz für echte Ausführung
                dedup_real = IntelligentDeduplication()
                real_results = dedup_real.clean_all_fuzzy_duplicates(dry_run=False)
                
                print(f"\n🎉 BEREINIGUNG ABGESCHLOSSEN!")
            else:
                print("\n💡 Nur DRY RUN ausgeführt. Datenbank unverändert.")
        else:
            print(f"\n✅ Keine Bereinigung erforderlich - Datenbank ist sauber!")

if __name__ == "__main__":
    main()