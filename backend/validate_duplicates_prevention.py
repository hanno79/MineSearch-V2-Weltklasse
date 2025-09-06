#!/usr/bin/env python3
"""
Author: rahn
Datum: 06.09.2025
Version: 1.0
Beschreibung: Validierungsscript für zukünftige Duplikate-Erkennung
Führt comprehensive Duplikate-Checks für alle Lookup-Tabellen durch
"""

import sqlite3
from datetime import datetime
import logging

def validate_all_duplicates():
    """Führt umfassende Duplikate-Validierung durch"""
    
    print("🔍 COMPREHENSIVE DUPLIKATE-VALIDIERUNG")
    print("=" * 70)
    
    conn = sqlite3.connect('mines.db')
    cursor = conn.cursor()
    
    total_issues = 0
    
    try:
        # 1. Company-Duplikate prüfen
        print("1. COMPANY-DUPLIKATE PRÜFUNG:")
        
        company_issues = check_company_duplicates(cursor)
        total_issues += company_issues
        
        # 2. Region-Duplikate prüfen
        print("\n2. REGION-DUPLIKATE PRÜFUNG:")
        
        region_issues = check_region_duplicates(cursor)
        total_issues += region_issues
        
        # 3. Commodity-Duplikate prüfen
        print("\n3. COMMODITY-DUPLIKATE PRÜFUNG:")
        
        commodity_issues = check_commodity_duplicates(cursor)
        total_issues += commodity_issues
        
        # 4. Mine-Type-Duplikate prüfen
        print("\n4. MINE-TYPE-DUPLIKATE PRÜFUNG:")
        
        mine_type_issues = check_mine_type_duplicates(cursor)
        total_issues += mine_type_issues
        
        # 5. 3NF-Compliance prüfen
        print("\n5. 3NF-COMPLIANCE PRÜFUNG:")
        
        compliance_issues = check_3nf_compliance(cursor)
        total_issues += compliance_issues
        
        # 6. Referentielle Integrität prüfen
        print("\n6. REFERENTIELLE INTEGRITÄT:")
        
        integrity_issues = check_referential_integrity(cursor)
        total_issues += integrity_issues
        
        return total_issues
        
    except Exception as e:
        print(f"❌ Fehler bei Validierung: {e}")
        return -1
    finally:
        conn.close()

def check_company_duplicates(cursor):
    """Prüft Company-Duplikate mit intelligenter Mustererkennung"""
    
    cursor.execute("SELECT id, name FROM companies ORDER BY name")
    all_companies = cursor.fetchall()
    
    print(f"   📊 {len(all_companies)} Companies analysieren...")
    
    duplicates_found = 0
    
    # Bekannte Duplikate-Muster
    variant_patterns = [
        ['goldcorp', 'goldcorp inc', 'goldcorp corporation'],
        ['barrick', 'barrick gold', 'barrick gold corp'],
        ['newmont', 'newmont corp', 'newmont corporation'],
        ['rio tinto', 'rio tinto group', 'rio tinto plc'],
        ['vale', 'vale s.a.', 'vale sa'],
        ['bhp', 'bhp billiton', 'bhp group']
    ]
    
    # Prüfe bekannte Muster
    for pattern in variant_patterns:
        found_variants = []
        for company_id, name in all_companies:
            if name.lower().strip() in [p.lower() for p in pattern]:
                found_variants.append((company_id, name))
        
        if len(found_variants) > 1:
            print(f"   ⚠️  Company-Duplikat-Muster gefunden:")
            for comp_id, comp_name in found_variants:
                print(f"     ID:{comp_id} - '{comp_name}'")
            duplicates_found += len(found_variants) - 1
    
    # Fuzzy-Matching für ähnliche Namen
    similar_groups = find_similar_names([name for _, name in all_companies])
    
    for group in similar_groups:
        if len(group) > 1:
            print(f"   ⚠️  Ähnliche Company-Namen gefunden: {group}")
            duplicates_found += len(group) - 1
    
    if duplicates_found == 0:
        print("   ✅ Keine Company-Duplikate gefunden")
    else:
        print(f"   🔧 {duplicates_found} potentielle Company-Duplikate")
    
    return duplicates_found

def check_region_duplicates(cursor):
    """Prüft Region-Duplikate (besonders Quebec-Varianten)"""
    
    cursor.execute("SELECT id, name, country_id FROM regions ORDER BY name")
    all_regions = cursor.fetchall()
    
    print(f"   📊 {len(all_regions)} Regions analysieren...")
    
    duplicates_found = 0
    
    # Quebec-spezifische Prüfung
    quebec_variants = []
    for region_id, name, country_id in all_regions:
        if any(q in name.lower() for q in ['quebec', 'québec']):
            quebec_variants.append((region_id, name, country_id))
    
    if len(quebec_variants) > 1:
        print(f"   ⚠️  Quebec-Varianten gefunden:")
        for reg_id, reg_name, country in quebec_variants:
            print(f"     ID:{reg_id} - '{reg_name}' (Country:{country})")
        duplicates_found += len(quebec_variants) - 1
    
    # Exakte Duplikate prüfen
    name_count = {}
    for region_id, name, country_id in all_regions:
        key = (name.lower().strip(), country_id)
        if key in name_count:
            name_count[key].append((region_id, name))
        else:
            name_count[key] = [(region_id, name)]
    
    for key, regions in name_count.items():
        if len(regions) > 1:
            print(f"   ⚠️  Exakte Region-Duplikate: {[r[1] for r in regions]}")
            duplicates_found += len(regions) - 1
    
    if duplicates_found == 0:
        print("   ✅ Keine Region-Duplikate gefunden")
    else:
        print(f"   🔧 {duplicates_found} potentielle Region-Duplikate")
    
    return duplicates_found

def check_commodity_duplicates(cursor):
    """Prüft Commodity-Duplikate (deutsch/englisch)"""
    
    cursor.execute("SELECT id, name, symbol FROM commodities ORDER BY name")
    all_commodities = cursor.fetchall()
    
    print(f"   📊 {len(all_commodities)} Commodities analysieren...")
    
    duplicates_found = 0
    
    # Deutsch-Englisch Translation-Paare
    translation_pairs = [
        ['gold', 'gold'],  # Beide gleich
        ['kupfer', 'copper'],
        ['silber', 'silver'],
        ['eisenerz', 'iron ore'],
        ['kohle', 'coal']
    ]
    
    for german, english in translation_pairs:
        found_variants = []
        for comm_id, name, symbol in all_commodities:
            if name.lower().strip() in [german, english]:
                found_variants.append((comm_id, name, symbol))
        
        if len(found_variants) > 1:
            print(f"   ⚠️  Commodity Translation-Duplikate:")
            for comm_id, comm_name, comm_symbol in found_variants:
                print(f"     ID:{comm_id} - '{comm_name}' ({comm_symbol})")
            duplicates_found += len(found_variants) - 1
    
    # Symbol-basierte Duplikate
    symbol_count = {}
    for comm_id, name, symbol in all_commodities:
        if symbol:
            if symbol in symbol_count:
                symbol_count[symbol].append((comm_id, name, symbol))
            else:
                symbol_count[symbol] = [(comm_id, name, symbol)]
    
    for symbol, commodities in symbol_count.items():
        if len(commodities) > 1:
            print(f"   ⚠️  Symbol-Duplikate ({symbol}): {[c[1] for c in commodities]}")
            duplicates_found += len(commodities) - 1
    
    if duplicates_found == 0:
        print("   ✅ Keine Commodity-Duplikate gefunden")
    else:
        print(f"   🔧 {duplicates_found} potentielle Commodity-Duplikate")
    
    return duplicates_found

def check_mine_type_duplicates(cursor):
    """Prüft Mine-Type-Duplikate (deutsch/englisch)"""
    
    cursor.execute("SELECT id, name FROM mine_types ORDER BY name")
    all_types = cursor.fetchall()
    
    print(f"   📊 {len(all_types)} Mine-Types analysieren...")
    
    duplicates_found = 0
    
    # Deutsch-Englisch Mine-Type-Paare
    translation_pairs = [
        ['open-pit', 'tagebau'],
        ['surface', 'tagebau'],
        ['underground', 'untertage'],
        ['quarry', 'steinbruch'],
        ['dredging', 'schwimmbagger'],
        ['in-situ-leaching', 'lösungsbergbau'],
        ['placer', 'seifenlagerstätte']
    ]
    
    for english, german in translation_pairs:
        found_variants = []
        for type_id, name in all_types:
            clean_name = name.lower().strip().replace('-', ' ')
            if clean_name in [english.replace('-', ' '), german]:
                found_variants.append((type_id, name))
        
        if len(found_variants) > 1:
            print(f"   ⚠️  Mine-Type Translation-Duplikate:")
            for type_id, type_name in found_variants:
                print(f"     ID:{type_id} - '{type_name}'")
            duplicates_found += len(found_variants) - 1
    
    if duplicates_found == 0:
        print("   ✅ Keine Mine-Type-Duplikate gefunden")
    else:
        print(f"   🔧 {duplicates_found} potentielle Mine-Type-Duplikate")
    
    return duplicates_found

def check_3nf_compliance(cursor):
    """Prüft 3NF-Compliance in mine_data_fields"""
    
    print(f"   📊 3NF-Compliance prüfen...")
    
    issues_found = 0
    
    # Test 1: Normalized fields mit primitive_value (VERBOTEN)
    cursor.execute("""
        SELECT COUNT(*) FROM mine_data_fields 
        WHERE field_type = 'normalized' AND primitive_value IS NOT NULL
    """)
    normalized_with_primitive = cursor.fetchone()[0]
    
    if normalized_with_primitive > 0:
        print(f"   ❌ {normalized_with_primitive} normalized fields haben primitive_value!")
        issues_found += normalized_with_primitive
    else:
        print(f"   ✅ Normalized fields haben kein primitive_value")
    
    # Test 2: Primitive fields mit FK-IDs (VERBOTEN) 
    cursor.execute("""
        SELECT COUNT(*) FROM mine_data_fields 
        WHERE field_type = 'primitive' AND (
            commodity_id IS NOT NULL OR company_id IS NOT NULL OR 
            activity_status_id IS NOT NULL OR mine_type_id IS NOT NULL OR
            country_id IS NOT NULL OR region_id IS NOT NULL
        )
    """)
    primitive_with_fk = cursor.fetchone()[0]
    
    if primitive_with_fk > 0:
        print(f"   ❌ {primitive_with_fk} primitive fields haben FK-IDs!")
        issues_found += primitive_with_fk
    else:
        print(f"   ✅ Primitive fields haben keine FK-IDs")
    
    # Test 3: Normalized fields ohne FK-IDs (VERBOTEN)
    cursor.execute("""
        SELECT COUNT(*) FROM mine_data_fields 
        WHERE field_type = 'normalized' AND (
            commodity_id IS NULL AND company_id IS NULL AND 
            activity_status_id IS NULL AND mine_type_id IS NULL AND
            country_id IS NULL AND region_id IS NULL
        )
    """)
    normalized_without_fk = cursor.fetchone()[0]
    
    if normalized_without_fk > 0:
        print(f"   ❌ {normalized_without_fk} normalized fields haben keine FK-IDs!")
        issues_found += normalized_without_fk
    else:
        print(f"   ✅ Alle normalized fields haben FK-IDs")
    
    return issues_found

def check_referential_integrity(cursor):
    """Prüft referentielle Integrität zwischen Tabellen"""
    
    print(f"   📊 Referentielle Integrität prüfen...")
    
    issues_found = 0
    
    # Prüfe FK-Referenzen in mine_data_fields
    fk_checks = [
        ('commodity_id', 'commodities', 'id'),
        ('company_id', 'companies', 'id'),
        ('activity_status_id', 'activity_statuses', 'id'),
        ('mine_type_id', 'mine_types', 'id'),
        ('country_id', 'countries', 'id'),
        ('region_id', 'regions', 'id')
    ]
    
    for fk_column, target_table, target_column in fk_checks:
        cursor.execute(f"""
            SELECT COUNT(*) FROM mine_data_fields mdf
            LEFT JOIN {target_table} t ON mdf.{fk_column} = t.{target_column}
            WHERE mdf.{fk_column} IS NOT NULL AND t.{target_column} IS NULL
        """)
        orphaned_refs = cursor.fetchone()[0]
        
        if orphaned_refs > 0:
            print(f"   ❌ {orphaned_refs} verwaiste {fk_column} Referenzen!")
            issues_found += orphaned_refs
        else:
            print(f"   ✅ Alle {fk_column} Referenzen sind gültig")
    
    return issues_found

def find_similar_names(names):
    """Findet ähnliche Namen durch Wort-basierte Analyse"""
    
    similar_groups = []
    
    # Gruppiere Namen nach ersten Wörtern
    word_groups = {}
    for name in names:
        if not name:
            continue
        first_word = name.lower().strip().split()[0] if name.strip() else ""
        if len(first_word) >= 3:  # Mindestens 3 Zeichen
            if first_word not in word_groups:
                word_groups[first_word] = []
            word_groups[first_word].append(name)
    
    # Finde Gruppen mit mehreren Namen
    for word, group_names in word_groups.items():
        if len(group_names) > 1:
            # Prüfe ob Namen wirklich ähnlich sind (nicht nur gleicher erster Buchstabe)
            if len(set(name.lower()[:5] for name in group_names)) < len(group_names):
                similar_groups.append(group_names)
    
    return similar_groups

if __name__ == "__main__":
    print(f"🧪 STARTE DUPLIKATE-VALIDIERUNG - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    total_issues = validate_all_duplicates()
    
    print(f"\n🎯 VALIDIERUNGS-ERGEBNIS:")
    print("=" * 70)
    
    if total_issues == 0:
        print("🎉 KEINE DUPLIKATE ODER 3NF-VERLETZUNGEN GEFUNDEN!")
        print("✅ Database ist vollständig normalisiert")
        print("✅ Duplikate-Prävention funktioniert")
        print("✅ 3NF-Compliance erfüllt")
        print("✅ Referentielle Integrität gegeben")
        
        # Erstelle Success-Report
        with open('duplicate_validation_success.log', 'w') as f:
            f.write(f"DUPLIKATE-VALIDIERUNG ERFOLGREICH - {datetime.now()}\n")
            f.write("Keine Duplikate oder 3NF-Verletzungen gefunden.\n")
            f.write("Database vollständig normalisiert.\n")
        
        print(f"\n📝 Success-Report: duplicate_validation_success.log")
        
    elif total_issues > 0:
        print(f"⚠️  {total_issues} POTENTIELLE PROBLEME GEFUNDEN!")
        print("🔧 Überprüfung und mögliche Korrekturen erforderlich")
        print("📋 Siehe Details oben für spezifische Problembereiche")
        
        # Erstelle Issue-Report
        with open('duplicate_validation_issues.log', 'w') as f:
            f.write(f"DUPLIKATE-VALIDIERUNG - PROBLEME GEFUNDEN - {datetime.now()}\n")
            f.write(f"Anzahl Probleme: {total_issues}\n")
            f.write("Siehe Console-Output für Details.\n")
        
        print(f"\n📝 Issue-Report: duplicate_validation_issues.log")
        
    else:
        print("❌ VALIDIERUNG FEHLGESCHLAGEN!")
        print("🔧 Technische Probleme bei der Validierung")
        
    print(f"\n🔄 EMPFEHLUNG:")
    print("   - Führe diese Validierung regelmäßig nach Datenimporten durch")
    print("   - Bei Problemen: Verwende repair_duplicates_phase1.py")
    print("   - Nutze duplicate_prevention_enhancement.py für zukünftige Prävention")