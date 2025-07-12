#!/usr/bin/env python3
"""
Author: rahn
Datum: 11.07.2025
Version: 1.0
Beschreibung: Vollständige Datenbank-Validierung für anthropic:claude-3.7-sonnet Tests
"""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path

def format_datetime(dt_str):
    """Formatiere Datetime-String für Anzeige"""
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return dt_str

def validate_database():
    """Führe vollständige Datenbankvalidierung durch"""
    db_path = Path("mines.db")
    if not db_path.exists():
        print("❌ FEHLER: Datenbank mines.db nicht gefunden!")
        return False
    
    print("🔍 VOLLSTÄNDIGE DATENBANK-VALIDIERUNG")
    print("=" * 60)
    print(f"Datenbank: {db_path.absolute()}")
    print(f"Validierung am: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # 1. SearchResults Tabelle prüfen
    print("\n📊 1. SEARCHRESULTS TABELLE - anthropic:claude-3.7-sonnet")
    print("-" * 50)
    
    # Gesamtanzahl und Zeitspanne
    cursor.execute("""
        SELECT COUNT(*) as total, MIN(created_at) as first, MAX(created_at) as last 
        FROM search_results 
        WHERE model = 'anthropic:claude-3.7-sonnet'
    """)
    result = cursor.fetchone()
    total_searches, first_entry, last_entry = result
    
    print(f"✅ Gesamtanzahl Einträge: {total_searches}")
    if first_entry and last_entry:
        print(f"✅ Erster Eintrag: {format_datetime(first_entry)}")
        print(f"✅ Letzter Eintrag: {format_datetime(last_entry)}")
        
        # Zeitspanne berechnen
        try:
            first_dt = datetime.fromisoformat(first_entry.replace('Z', '+00:00'))
            last_dt = datetime.fromisoformat(last_entry.replace('Z', '+00:00'))
            duration = last_dt - first_dt
            print(f"✅ Zeitspanne: {duration}")
        except:
            pass
    
    # Detailanalyse der letzten 15 Suchen
    cursor.execute("""
        SELECT mine_name, created_at, 
               CASE WHEN structured_data IS NOT NULL THEN 'Ja' ELSE 'Nein' END as has_data,
               CASE WHEN sources IS NOT NULL THEN json_array_length(sources) ELSE 0 END as source_count
        FROM search_results 
        WHERE model = 'anthropic:claude-3.7-sonnet'
        ORDER BY created_at DESC
        LIMIT 15
    """)
    
    recent_searches = cursor.fetchall()
    print(f"\n📋 Letzte {len(recent_searches)} Suchen:")
    for i, (mine_name, timestamp, has_data, source_count) in enumerate(recent_searches, 1):
        print(f"  {i:2d}. {mine_name[:30]:30s} | {format_datetime(timestamp)} | Daten: {has_data} | Quellen: {source_count}")
    
    # Kritische Felder prüfen
    print(f"\n🔍 Kritische Felder-Analyse:")
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN json_extract(structured_data, '$.owner') IS NOT NULL THEN 1 ELSE 0 END) as has_owner,
            SUM(CASE WHEN json_extract(structured_data, '$.operator') IS NOT NULL THEN 1 ELSE 0 END) as has_operator,
            SUM(CASE WHEN json_extract(structured_data, '$.restoration_costs') IS NOT NULL THEN 1 ELSE 0 END) as has_restoration,
            SUM(CASE WHEN json_extract(structured_data, '$.coordinates') IS NOT NULL THEN 1 ELSE 0 END) as has_coordinates
        FROM search_results 
        WHERE model = 'anthropic:claude-3.7-sonnet'
    """)
    
    field_stats = cursor.fetchone()
    total, has_owner, has_operator, has_restoration, has_coordinates = field_stats
    if total > 0:
        print(f"  Owner-Feld:        {has_owner:2d}/{total} ({has_owner/total*100:.1f}%)")
        print(f"  Operator-Feld:     {has_operator:2d}/{total} ({has_operator/total*100:.1f}%)")
        print(f"  Restoration-Feld:  {has_restoration:2d}/{total} ({has_restoration/total*100:.1f}%)")
        print(f"  Coordinates-Feld:  {has_coordinates:2d}/{total} ({has_coordinates/total*100:.1f}%)")
    
    # 2. ModelStatistics Tabelle prüfen
    print("\n📈 2. MODELSTATISTICS TABELLE")
    print("-" * 50)
    
    cursor.execute("""
        SELECT model_name, total_searches, successful_searches, avg_response_time,
               avg_data_quality_score, last_updated
        FROM model_statistics 
        WHERE model_name = 'anthropic:claude-3.7-sonnet'
    """)
    
    model_stats = cursor.fetchone()
    if model_stats:
        model_name, total, successful, avg_time, avg_quality, last_updated = model_stats
        success_rate = (successful / total * 100) if total > 0 else 0
        
        print(f"✅ Modell: {model_name}")
        print(f"✅ Gesamte Suchen: {total}")
        print(f"✅ Erfolgreiche Suchen: {successful}")
        print(f"✅ Erfolgsrate: {success_rate:.1f}%")
        print(f"✅ Durchschnittliche Response-Zeit: {avg_time:.2f}s")
        print(f"✅ Durchschnittlicher Qualitätsscore: {avg_quality:.1f}%")
        print(f"✅ Letztes Update: {format_datetime(last_updated)}")
        
        # Plausibilitätsprüfung
        issues = []
        if success_rate <= 0:
            issues.append("❌ Erfolgsrate = 0% (unrealistisch)")
        if avg_time <= 0:
            issues.append("❌ Response-Zeit = 0s (unrealistisch)")
        if avg_quality <= 0:
            issues.append("❌ Qualitätsscore = 0% (unrealistisch)")
        
        if issues:
            print("\n⚠️  PLAUSIBILITÄTSPROBLEME:")
            for issue in issues:
                print(f"   {issue}")
        else:
            print("✅ Alle Werte plausibel")
    else:
        print("❌ FEHLER: Keine ModelStatistics für anthropic:claude-3.7-sonnet gefunden!")
    
    # 3. FieldConsistency Tabelle prüfen
    print("\n📊 3. FIELDCONSISTENCY TABELLE")
    print("-" * 50)
    
    cursor.execute("""
        SELECT field_name, success_rate, total_searches, last_updated
        FROM field_consistency
        ORDER BY field_name
    """)
    
    field_consistency = cursor.fetchall()
    if field_consistency:
        print(f"✅ Gefundene Felder: {len(field_consistency)}")
        for field_name, success_rate, total_searches, last_updated in field_consistency:
            print(f"  {field_name:20s}: {success_rate:5.1f}% ({total_searches:2d} Suchen) | Update: {format_datetime(last_updated)}")
        
        # Kritische Felder prüfen
        critical_fields = ['owner', 'operator', 'restoration_costs', 'coordinates']
        missing_critical = []
        for field in critical_fields:
            found = any(row[0] == field for row in field_consistency)
            if not found:
                missing_critical.append(field)
        
        if missing_critical:
            print(f"\n❌ FEHLENDE kritische Felder: {', '.join(missing_critical)}")
        else:
            print("✅ Alle kritischen Felder vorhanden")
    else:
        print("❌ FEHLER: Keine FieldConsistency-Daten gefunden!")
    
    # 4. Sources Tabelle prüfen
    print("\n🌐 4. SOURCES TABELLE")
    print("-" * 50)
    
    # Gesamtstatistiken
    cursor.execute("SELECT COUNT(*) FROM sources")
    total_sources = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM sources WHERE last_accessed IS NOT NULL")
    accessed_sources = cursor.fetchone()[0]
    
    cursor.execute("SELECT AVG(reliability_score) FROM sources WHERE reliability_score > 0")
    avg_reliability = cursor.fetchone()[0] or 0
    
    print(f"✅ Gesamte Quellen: {total_sources}")
    print(f"✅ Genutzte Quellen: {accessed_sources}")
    print(f"✅ Nutzungsrate: {accessed_sources/total_sources*100:.1f}%")
    print(f"✅ Durchschnittliche Zuverlässigkeit: {avg_reliability:.1f}")
    
    # Kanadische/Quebec-Quellen
    cursor.execute("""
        SELECT COUNT(*) FROM sources 
        WHERE country = 'Canada' OR region = 'Quebec' OR domain LIKE '%canada%' OR domain LIKE '%quebec%'
    """)
    canadian_sources = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT COUNT(*) FROM sources 
        WHERE (country = 'Canada' OR region = 'Quebec' OR domain LIKE '%canada%' OR domain LIKE '%quebec%')
        AND last_accessed IS NOT NULL
    """)
    canadian_accessed = cursor.fetchone()[0]
    
    print(f"✅ Kanadische/Quebec-Quellen: {canadian_sources}")
    print(f"✅ Davon genutzt: {canadian_accessed}")
    
    # Quellentyp-Verteilung
    cursor.execute("""
        SELECT source_type, COUNT(*) 
        FROM sources 
        GROUP BY source_type 
        ORDER BY COUNT(*) DESC
    """)
    source_types = cursor.fetchall()
    print(f"\n📊 Quellentyp-Verteilung:")
    for source_type, count in source_types:
        print(f"  {source_type:15s}: {count:3d} Quellen")
    
    # 5. Allgemeine Datenbankintegrität
    print("\n🔧 5. DATENBANKINTEGRITÄT")
    print("-" * 50)
    
    # Timestamp-Prüfung (letzte 2 Stunden)
    now = datetime.now()
    two_hours_ago = now - timedelta(hours=2)
    
    cursor.execute("""
        SELECT COUNT(*) FROM search_results 
        WHERE model = 'anthropic:claude-3.7-sonnet'
        AND datetime(created_at) > datetime(?)
    """, (two_hours_ago.isoformat(),))
    recent_count = cursor.fetchone()[0]
    
    print(f"✅ Suchen der letzten 2 Stunden: {recent_count}")
    
    # Null-Werte in kritischen Feldern
    cursor.execute("""
        SELECT COUNT(*) FROM search_results 
        WHERE model = 'anthropic:claude-3.7-sonnet'
        AND (mine_name IS NULL OR model IS NULL OR created_at IS NULL)
    """)
    null_critical = cursor.fetchone()[0]
    
    if null_critical > 0:
        print(f"❌ Einträge mit Null-Werten in kritischen Feldern: {null_critical}")
    else:
        print("✅ Keine Null-Werte in kritischen Feldern")
    
    # Foreign Key Konsistenz (falls vorhanden)
    cursor.execute("PRAGMA foreign_key_check")
    fk_errors = cursor.fetchall()
    
    if fk_errors:
        print(f"❌ Foreign Key Fehler: {len(fk_errors)}")
        for error in fk_errors[:5]:  # Zeige nur erste 5
            print(f"   {error}")
    else:
        print("✅ Foreign Key Konsistenz OK")
    
    conn.close()
    
    # 6. Validierungsresultat
    print("\n🏁 VALIDIERUNGSRESULTAT")
    print("=" * 60)
    
    validation_passed = True
    critical_issues = []
    
    # Kritische Validierungspunkte
    if total_searches < 15:
        critical_issues.append(f"❌ Nur {total_searches}/15 Suchergebnisse gefunden")
        validation_passed = False
    else:
        print("✅ Alle 15 Suchergebnisse in SearchResults vorhanden")
    
    if not model_stats:
        critical_issues.append("❌ ModelStatistics fehlen")
        validation_passed = False
    elif success_rate <= 0 or avg_time <= 0:
        critical_issues.append("❌ ModelStatistics zeigt unrealistische Werte")
        validation_passed = False
    else:
        print("✅ ModelStatistics zeigt realistische Werte")
    
    if not field_consistency:
        critical_issues.append("❌ FieldConsistency-Daten fehlen")
        validation_passed = False
    else:
        print("✅ FieldConsistency wurde aktualisiert")
    
    if accessed_sources < total_sources * 0.5:  # Mindestens 50% der Quellen sollten genutzt werden
        critical_issues.append(f"❌ Nur {accessed_sources}/{total_sources} Quellen genutzt")
        validation_passed = False
    else:
        print("✅ Sources zeigt umfassende Nutzung")
    
    if recent_count < 10:  # Mindestens 10 der letzten 15 Suchen sollten in den letzten 2 Stunden sein
        critical_issues.append(f"❌ Nur {recent_count} Suchen in letzten 2 Stunden")
        validation_passed = False
    else:
        print("✅ Timestamps plausibel (letzte 2 Stunden)")
    
    if null_critical > 0:
        critical_issues.append(f"❌ {null_critical} Einträge mit Null-Werten")
        validation_passed = False
    else:
        print("✅ Keine Null-Werte in kritischen Feldern")
    
    print()
    if validation_passed:
        print("🎉 VALIDIERUNG ERFOLGREICH! Datenbank ist bereit für nächsten Provider-Test.")
        print("   Alle kritischen Validierungspunkte bestanden.")
    else:
        print("❌ VALIDIERUNG FEHLGESCHLAGEN!")
        print("   Kritische Probleme gefunden:")
        for issue in critical_issues:
            print(f"   {issue}")
        print("   Bitte Probleme beheben vor nächstem Provider-Test.")
    
    return validation_passed

if __name__ == "__main__":
    validate_database()