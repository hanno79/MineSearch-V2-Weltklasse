#!/usr/bin/env python3
"""
Author: rahn
Datum: 06.09.2025
Version: 1.0
Beschreibung: Analysiere Duplikate in allen Datenbank-Tabellen
"""

import sqlite3
import pandas as pd
from collections import Counter
import difflib

def analyze_database_duplicates():
    """Analysiere alle Tabellen auf Duplikate"""
    
    conn = sqlite3.connect('mines.db')
    cursor = conn.cursor()
    
    print("🔍 DATENBANK DUPLIKATE ANALYSE")
    print("=" * 60)
    
    # Hole alle Tabellen
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    print(f"📋 Gefundene Tabellen: {len(tables)}")
    for table in tables:
        print(f"   - {table}")
    
    print("\n" + "=" * 60)
    
    total_duplicates = 0
    
    for table in tables:
        print(f"\n🔍 TABELLE: {table}")
        print("-" * 40)
        
        try:
            # Hole Schema
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [col[1] for col in cursor.fetchall()]
            print(f"   Spalten: {', '.join(columns)}")
            
            # Hole alle Daten
            df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
            total_rows = len(df)
            print(f"   Gesamt Einträge: {total_rows}")
            
            if total_rows == 0:
                print("   ⚠️  Tabelle ist leer")
                continue
            
            # Analysiere verschiedene Duplikat-Arten
            
            # 1. EXAKTE DUPLIKATE (alle Spalten identisch)
            exact_duplicates = df.duplicated().sum()
            if exact_duplicates > 0:
                print(f"   ❌ EXAKTE DUPLIKATE: {exact_duplicates}")
                total_duplicates += exact_duplicates
                
                # Zeige Beispiele
                duplicated_rows = df[df.duplicated(keep=False)]
                print(f"   📋 Beispiel Duplikate:")
                for i, row in duplicated_rows.head(4).iterrows():
                    print(f"      Row {i}: {dict(row)}")
            
            # 2. DUPLIKATE NACH HAUPTSCHLÜSSEL-SPALTEN
            if 'name' in columns or 'company_name' in columns:
                key_col = 'name' if 'name' in columns else 'company_name'
                
                # Exakte Name-Duplikate
                name_counts = df[key_col].value_counts()
                exact_name_dups = name_counts[name_counts > 1]
                
                if len(exact_name_dups) > 0:
                    print(f"   ❌ EXAKTE {key_col.upper()}-DUPLIKATE: {len(exact_name_dups)} Namen betroffen")
                    print(f"   📊 Top 5 Duplikate:")
                    for name, count in exact_name_dups.head(5).items():
                        print(f"      '{name}': {count} mal")
                
                # Ähnliche Name-Duplikate (Fuzzy Matching)
                unique_names = df[key_col].dropna().unique()
                similar_groups = find_similar_names(unique_names)
                
                if similar_groups:
                    print(f"   ⚠️  ÄHNLICHE {key_col.upper()}-DUPLIKATE: {len(similar_groups)} Gruppen")
                    for group in similar_groups[:3]:  # Top 3 zeigen
                        print(f"      Ähnlich: {group}")
            
            # 3. NORMALISIERTE DUPLIKATE (mit normalized_name Spalte)
            if 'normalized_name' in columns:
                norm_counts = df['normalized_name'].value_counts()
                norm_dups = norm_counts[norm_counts > 1]
                
                if len(norm_dups) > 0:
                    print(f"   ❌ NORMALISIERTE DUPLIKATE: {len(norm_dups)} normalisierte Namen betroffen")
                    print(f"   📊 Top 3 normalisierte Duplikate:")
                    for norm_name, count in norm_dups.head(3).items():
                        # Zeige originale Namen für diesen normalisierten Namen
                        original_names = df[df['normalized_name'] == norm_name]['name'].tolist() if 'name' in columns else ['N/A']
                        print(f"      '{norm_name}': {count} mal -> {original_names}")
            
            print(f"   ✅ Eindeutige Einträge: {total_rows - exact_duplicates}")
            
        except Exception as e:
            print(f"   ❌ Fehler bei Analyse: {e}")
    
    print("\n" + "=" * 60)
    print(f"🎯 ZUSAMMENFASSUNG:")
    print(f"   📊 Total Tabellen analysiert: {len(tables)}")
    print(f"   ❌ Total exakte Duplikate gefunden: {total_duplicates}")
    print(f"   ⚠️  Datenverschwendung durch Duplikate!")
    
    conn.close()

def find_similar_names(names, threshold=0.8):
    """Finde ähnliche Namen mit Fuzzy-Matching"""
    similar_groups = []
    processed = set()
    
    for i, name1 in enumerate(names):
        if name1 in processed:
            continue
            
        similar = [name1]
        processed.add(name1)
        
        for name2 in names[i+1:]:
            if name2 in processed:
                continue
                
            # Berechne Ähnlichkeit
            ratio = difflib.SequenceMatcher(None, name1.lower(), name2.lower()).ratio()
            
            if ratio >= threshold:
                similar.append(name2)
                processed.add(name2)
        
        if len(similar) > 1:
            similar_groups.append(similar)
    
    return similar_groups

if __name__ == "__main__":
    analyze_database_duplicates()