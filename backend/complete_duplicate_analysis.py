#!/usr/bin/env python3
"""
Author: rahn
Datum: 06.09.2025
Version: 1.0
Beschreibung: STUFE 1 - Vollständige Duplikat-Analyse aller Tabellen
"""

import sqlite3
import pandas as pd
from collections import Counter
import difflib
import json
from datetime import datetime
import re

def analyze_all_duplicates():
    """Vollständige Duplikat-Analyse - STUFE 1"""
    print("🔍 STUFE 1: VOLLSTÄNDIGE DUPLIKAT-ANALYSE")
    print("=" * 60)
    
    conn = sqlite3.connect('mines.db')
    
    try:
        # Hole alle Tabellen
        tables = get_all_tables(conn)
        
        print(f"📋 Gefundene Tabellen: {len(tables)}")
        for table in tables:
            print(f"   - {table}")
        
        print("\n" + "=" * 60)
        
        total_duplicates = 0
        analysis_results = {}
        
        for table in tables:
            print(f"\n🔍 ANALYSIERE TABELLE: {table}")
            print("-" * 40)
            
            try:
                # Hole Schema-Informationen
                cursor = conn.cursor()
                cursor.execute(f"PRAGMA table_info({table})")
                columns_info = cursor.fetchall()
                columns = [col[1] for col in columns_info]
                print(f"   📊 Spalten ({len(columns)}): {', '.join(columns[:5])}{'...' if len(columns) > 5 else ''}")
                
                # Hole alle Daten
                df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
                total_rows = len(df)
                print(f"   📈 Gesamt Einträge: {total_rows:,}")
                
                if total_rows == 0:
                    print("   ⚠️  Tabelle ist leer")
                    analysis_results[table] = {'status': 'empty'}
                    continue
                
                # Analysiere verschiedene Duplikat-Arten
                table_analysis = analyze_table_duplicates(df, table, columns)
                analysis_results[table] = table_analysis
                
                # Zeige Ergebnisse
                if table_analysis['exact_duplicates'] > 0:
                    print(f"   ❌ EXAKTE DUPLIKATE: {table_analysis['exact_duplicates']:,}")
                    total_duplicates += table_analysis['exact_duplicates']
                    
                    # Zeige Beispiele
                    duplicated_rows = df[df.duplicated(keep=False)]
                    if not duplicated_rows.empty:
                        print(f"   📋 Beispiel Duplikate (erste 3):")
                        sample_columns = [col for col in ['id', 'name', 'company_name', 'mine_name', 'url'] if col in df.columns][:3]
                        for i, (_, row) in enumerate(duplicated_rows.head(6).iterrows()):
                            if i % 2 == 0:  # Zeige nur jeden zweiten (Duplikate sind immer paarweise)
                                sample_data = {col: row[col] for col in sample_columns}
                                print(f"      {sample_data}")
                            if i >= 5:
                                break
                
                # Analysiere Key-Column Duplikate
                key_columns = identify_key_columns(df, table)
                key_duplicates_found = False
                
                for col in key_columns:
                    if col in df.columns and not df[col].isna().all():
                        col_counts = df[col].value_counts()
                        col_duplicates = col_counts[col_counts > 1]
                        
                        if len(col_duplicates) > 0:
                            key_duplicates_found = True
                            print(f"   ⚠️  {col.upper()}-DUPLIKATE: {len(col_duplicates)} verschiedene Werte, {col_duplicates.sum()} Einträge betroffen")
                            
                            # Top 3 zeigen
                            print(f"   🔥 Top 3 doppelte {col}-Werte:")
                            for value, count in col_duplicates.head(3).items():
                                print(f"      '{value}': {count} mal")
                
                # Fuzzy-Duplikate analysieren (nur für Name-Spalten)
                fuzzy_groups = []
                name_columns = [col for col in df.columns if 'name' in col.lower() and col in df.columns]
                
                for col in name_columns:
                    if not df[col].isna().all():
                        unique_values = df[col].dropna().unique()
                        if len(unique_values) > 1 and len(unique_values) < 1000:  # Limit für Performance
                            similar_groups = find_similar_values(unique_values)
                            if similar_groups:
                                fuzzy_groups.extend(similar_groups)
                                print(f"   🔍 FUZZY-DUPLIKATE in {col}: {len(similar_groups)} ähnliche Gruppen")
                                for group in similar_groups[:2]:  # Top 2 zeigen
                                    print(f"      Ähnlich: {group}")
                
                # Eindeutige Einträge
                unique_count = total_rows - table_analysis['exact_duplicates']
                print(f"   ✅ Eindeutige Einträge: {unique_count:,}")
                
                # Empfehlungen
                recommendations = generate_recommendations(table_analysis, table, total_rows)
                if recommendations:
                    print(f"   🎯 EMPFEHLUNGEN:")
                    for rec in recommendations:
                        print(f"      {rec}")
                
            except Exception as e:
                print(f"   ❌ Fehler bei Analyse von {table}: {e}")
                analysis_results[table] = {'error': str(e)}
        
        # Gesamtzusammenfassung
        print("\n" + "=" * 60)
        print(f"🎯 GESAMTANALYSE ZUSAMMENFASSUNG:")
        print(f"   📊 Tabellen analysiert: {len(tables)}")
        print(f"   ❌ Total exakte Duplikate: {total_duplicates:,}")
        
        if total_duplicates > 0:
            print(f"   🚨 KRITISCH: Massive Duplikat-Probleme gefunden!")
        else:
            print(f"   ✅ Keine exakten Duplikate gefunden")
        
        # Speichere detaillierten Report
        save_analysis_report(analysis_results, tables, total_duplicates)
        
    except Exception as e:
        print(f"❌ KRITISCHER FEHLER: {e}")
    
    finally:
        conn.close()

def analyze_table_duplicates(df, table_name, columns):
    """Analysiert eine einzelne Tabelle detailliert"""
    analysis = {
        'total_rows': len(df),
        'exact_duplicates': df.duplicated().sum(),
        'unique_rows': len(df) - df.duplicated().sum(),
        'duplicate_percentage': 0,
        'key_column_analysis': {},
        'fuzzy_groups': [],
        'recommendations': []
    }
    
    # Berechne Duplikat-Prozentsatz
    if analysis['total_rows'] > 0:
        analysis['duplicate_percentage'] = round((analysis['exact_duplicates'] / analysis['total_rows']) * 100, 2)
    
    # Analysiere Key-Columns
    key_columns = identify_key_columns(df, table_name)
    for col in key_columns:
        if col in df.columns:
            col_counts = df[col].value_counts()
            col_duplicates = col_counts[col_counts > 1]
            
            analysis['key_column_analysis'][col] = {
                'unique_values': len(col_counts),
                'duplicate_values': len(col_duplicates),
                'total_duplicate_rows': col_duplicates.sum() if len(col_duplicates) > 0 else 0
            }
    
    return analysis

def get_all_tables(conn):
    """Hole alle relevanten Tabellennamen"""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    return [row[0] for row in cursor.fetchall()]

def identify_key_columns(df, table_name):
    """Identifiziere wichtige Spalten für Duplikat-Prüfung"""
    key_columns = []
    
    # Standard-Schlüssel-Spalten
    standard_keys = ['name', 'company_name', 'mine_name', 'url', 'atomic_value', 'normalized_name']
    
    for col in df.columns:
        if col.lower() in [k.lower() for k in standard_keys]:
            key_columns.append(col)
    
    # Tabellen-spezifische Spalten
    if table_name == 'companies' and 'country' in df.columns:
        key_columns.append('country')
    elif table_name == 'mines' and 'country' in df.columns:
        key_columns.append('country')
    elif table_name == 'field_values' and 'field_name' in df.columns:
        key_columns.append('field_name')
    
    return list(set(key_columns))

def find_similar_values(values, threshold=0.85):
    """Findet ähnliche Werte mit Fuzzy-Matching"""
    if len(values) < 2:
        return []
    
    similar_groups = []
    processed = set()
    
    values_list = list(values)
    
    for i, value1 in enumerate(values_list):
        if value1 in processed or pd.isna(value1):
            continue
            
        group = [value1]
        processed.add(value1)
        
        for value2 in values_list[i+1:]:
            if value2 in processed or pd.isna(value2):
                continue
                
            similarity = calculate_similarity(value1, value2)
            if similarity >= threshold:
                group.append(value2)
                processed.add(value2)
        
        if len(group) > 1:
            similar_groups.append(group)
    
    return similar_groups

def calculate_similarity(text1, text2):
    """Berechnet Ähnlichkeit zwischen zwei Texten"""
    if not text1 or not text2:
        return 0.0
    
    # Normalisiere für besseren Vergleich
    text1_norm = normalize_text(str(text1))
    text2_norm = normalize_text(str(text2))
    
    return difflib.SequenceMatcher(None, text1_norm, text2_norm).ratio()

def normalize_text(text):
    """Normalisiert Text für Vergleiche"""
    if not text:
        return ""
    
    # Kleinschreibung, entferne Sonderzeichen
    normalized = re.sub(r'[^\w\s]', '', text.lower())
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    # Entferne häufige Firmensuffixe
    suffixes = ['ltd', 'limited', 'corp', 'corporation', 'inc', 'incorporated', 
                'co', 'company', 'ag', 'gmbh', 'sa', 'plc', 'llc']
    words = normalized.split()
    filtered_words = [w for w in words if w not in suffixes]
    
    return ' '.join(filtered_words)

def generate_recommendations(analysis, table_name, total_rows):
    """Generiert Empfehlungen basierend auf Analyse"""
    recommendations = []
    
    # Exakte Duplikate
    if analysis['exact_duplicates'] > 0:
        if analysis['exact_duplicates'] > total_rows * 0.1:  # Mehr als 10%
            recommendations.append("🚨 KRITISCH: Sofortige Bereinigung exakter Duplikate erforderlich!")
        else:
            recommendations.append("⚠️ Exakte Duplikate gefunden - Bereinigung empfohlen")
    
    # Key-Column Probleme
    for col, col_analysis in analysis.get('key_column_analysis', {}).items():
        if col_analysis['duplicate_values'] > 0:
            if col in ['name', 'company_name', 'mine_name']:
                recommendations.append(f"🔑 UNIQUE-Constraint für '{col}' implementieren")
    
    # Tabellen-spezifische Empfehlungen
    if table_name in ['companies', 'mines'] and analysis['exact_duplicates'] == 0:
        recommendations.append("🛡️ UNIQUE-Constraints zur Prävention hinzufügen")
    
    return recommendations

def save_analysis_report(analysis_results, tables, total_duplicates):
    """Speichert detaillierten Analyse-Report"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f'duplicate_analysis_report_{timestamp}.json'
    
    report_data = {
        'analysis_timestamp': datetime.now().isoformat(),
        'total_tables_analyzed': len(tables),
        'total_exact_duplicates_found': total_duplicates,
        'critical_severity': total_duplicates > 100,
        'table_details': analysis_results,
        'summary': {
            'tables_with_duplicates': len([t for t, a in analysis_results.items() if a.get('exact_duplicates', 0) > 0]),
            'tables_clean': len([t for t, a in analysis_results.items() if a.get('exact_duplicates', 0) == 0]),
            'most_problematic_tables': []
        }
    }
    
    # Finde problematischste Tabellen
    problematic = [(table, analysis.get('exact_duplicates', 0)) 
                   for table, analysis in analysis_results.items()]
    problematic.sort(key=lambda x: x[1], reverse=True)
    report_data['summary']['most_problematic_tables'] = problematic[:5]
    
    # Speichere Report
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Detaillierter Report gespeichert: {report_file}")
    
    # Zeige Kritische Zusammenfassung
    print(f"\n🎯 KRITISCHE ERKENNTNISSE:")
    if total_duplicates > 0:
        print(f"   🚨 {total_duplicates:,} exakte Duplikate gefunden!")
        print(f"   📊 Problematischste Tabellen:")
        for table, dup_count in problematic[:3]:
            if dup_count > 0:
                print(f"      - {table}: {dup_count:,} Duplikate")
    else:
        print(f"   ✅ Keine exakten Duplikate gefunden")
    
    return report_file

if __name__ == "__main__":
    print(f"🚀 STARTE DUPLIKAT-ANALYSE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    analyze_all_duplicates()
    print(f"\n🎉 ANALYSE ABGESCHLOSSEN - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")