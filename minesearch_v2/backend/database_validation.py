"""
Author: rahn
Datum: 18.07.2025
Version: 1.0
Beschreibung: Validierung der Datenbank-Einträge nach Provider-Tests
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Any

def validate_database_entries():
    """Validiere alle Datenbank-Einträge nach den Provider-Tests"""
    
    print("🔍 DATENBANK-VALIDIERUNG GESTARTET")
    print("="*80)
    
    # Verbindung zur Datenbank
    conn = sqlite3.connect('/app/minesearch_v2/backend/mines.db')
    cursor = conn.cursor()
    
    # 1. Validiere ModelStatistics
    print("\n📊 VALIDIERUNG: ModelStatistics")
    cursor.execute("SELECT COUNT(*) FROM ModelStatistics")
    model_stats_count = cursor.fetchone()[0]
    print(f"  ✅ ModelStatistics Einträge: {model_stats_count}")
    
    if model_stats_count > 0:
        cursor.execute("""
            SELECT model_id, total_searches, successful_searches, 
                   avg_response_time, avg_relevance_score, created_at
            FROM ModelStatistics 
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        recent_stats = cursor.fetchall()
        print("  📋 Neueste ModelStatistics:")
        for stat in recent_stats:
            print(f"    {stat[0]}: {stat[1]} Suchen, {stat[2]} erfolgreich, {stat[3]:.2f}s avg")
    
    # 2. Validiere FieldStatistics
    print("\n📊 VALIDIERUNG: FieldStatistics")
    cursor.execute("SELECT COUNT(*) FROM FieldStatistics")
    field_stats_count = cursor.fetchone()[0]
    print(f"  ✅ FieldStatistics Einträge: {field_stats_count}")
    
    if field_stats_count > 0:
        cursor.execute("""
            SELECT field_name, COUNT(*) as count, AVG(completion_rate) as avg_completion
            FROM FieldStatistics 
            GROUP BY field_name
            ORDER BY avg_completion DESC
            LIMIT 10
        """)
        field_stats = cursor.fetchall()
        print("  📋 Top Field Completion Rates:")
        for stat in field_stats:
            print(f"    {stat[0]}: {stat[1]} Einträge, {stat[2]:.2f}% avg completion")
    
    # 3. Validiere FieldConsistency
    print("\n📊 VALIDIERUNG: FieldConsistency")
    cursor.execute("SELECT COUNT(*) FROM FieldConsistency")
    consistency_count = cursor.fetchone()[0]
    print(f"  ✅ FieldConsistency Einträge: {consistency_count}")
    
    if consistency_count > 0:
        cursor.execute("""
            SELECT field_name, COUNT(*) as count, AVG(consistency_score) as avg_consistency
            FROM FieldConsistency 
            GROUP BY field_name
            ORDER BY avg_consistency DESC
            LIMIT 10
        """)
        consistency_stats = cursor.fetchall()
        print("  📋 Top Field Consistency Scores:")
        for stat in consistency_stats:
            print(f"    {stat[0]}: {stat[1]} Einträge, {stat[2]:.2f} avg consistency")
    
    # 4. Validiere Sources
    print("\n📊 VALIDIERUNG: Sources")
    cursor.execute("SELECT COUNT(*) FROM Sources")
    sources_count = cursor.fetchone()[0]
    print(f"  ✅ Sources Einträge: {sources_count}")
    
    if sources_count > 0:
        cursor.execute("""
            SELECT domain, COUNT(*) as count, AVG(relevance_score) as avg_relevance
            FROM Sources 
            GROUP BY domain
            ORDER BY count DESC
            LIMIT 10
        """)
        sources_stats = cursor.fetchall()
        print("  📋 Top Source Domains:")
        for stat in sources_stats:
            print(f"    {stat[0]}: {stat[1]} Einträge, {stat[2]:.2f} avg relevance")
    
    # 5. Validiere SearchResults
    print("\n📊 VALIDIERUNG: SearchResults")
    cursor.execute("SELECT COUNT(*) FROM SearchResults")
    results_count = cursor.fetchone()[0]
    print(f"  ✅ SearchResults Einträge: {results_count}")
    
    if results_count > 0:
        cursor.execute("""
            SELECT COUNT(*) as count, AVG(relevance_score) as avg_relevance
            FROM SearchResults 
            WHERE created_at >= date('now', '-1 day')
        """)
        recent_results = cursor.fetchone()
        print(f"  📋 Letzte 24h: {recent_results[0]} Einträge, {recent_results[1]:.2f} avg relevance")
    
    # 6. Prüfe auf Dummy-Werte
    print("\n🔍 DUMMY-WERTE VALIDIERUNG")
    dummy_indicators = ['dummy', 'test', 'example', 'placeholder', 'unknown', 'n/a']
    
    # Prüfe in SearchResults
    dummy_count = 0
    for indicator in dummy_indicators:
        cursor.execute("""
            SELECT COUNT(*) FROM SearchResults 
            WHERE LOWER(extracted_data) LIKE ? OR LOWER(raw_content) LIKE ?
        """, (f'%{indicator}%', f'%{indicator}%'))
        count = cursor.fetchone()[0]
        if count > 0:
            print(f"  ⚠️  '{indicator}' in SearchResults: {count} Einträge")
            dummy_count += count
    
    if dummy_count == 0:
        print("  ✅ Keine Dummy-Werte in SearchResults gefunden")
    else:
        print(f"  ❌ {dummy_count} potenzielle Dummy-Werte gefunden")
    
    # 7. Plausibilitäts-Checks
    print("\n🎯 PLAUSIBILITÄTS-CHECKS")
    
    # Check 1: Negative Werte
    cursor.execute("""
        SELECT COUNT(*) FROM ModelStatistics 
        WHERE total_searches < 0 OR successful_searches < 0 OR avg_response_time < 0
    """)
    negative_count = cursor.fetchone()[0]
    if negative_count == 0:
        print("  ✅ Keine negativen Werte in ModelStatistics")
    else:
        print(f"  ❌ {negative_count} negative Werte in ModelStatistics")
    
    # Check 2: Erfolgsrate > 100%
    cursor.execute("""
        SELECT COUNT(*) FROM ModelStatistics 
        WHERE successful_searches > total_searches
    """)
    invalid_success = cursor.fetchone()[0]
    if invalid_success == 0:
        print("  ✅ Erfolgsraten sind plausibel")
    else:
        print(f"  ❌ {invalid_success} implausible Erfolgsraten")
    
    # Check 3: Completion Rate > 100%
    cursor.execute("""
        SELECT COUNT(*) FROM FieldStatistics 
        WHERE completion_rate > 100
    """)
    invalid_completion = cursor.fetchone()[0]
    if invalid_completion == 0:
        print("  ✅ Completion Rates sind plausibel")
    else:
        print(f"  ❌ {invalid_completion} implausible Completion Rates")
    
    # 8. Konsistenz-Checks
    print("\n🔄 KONSISTENZ-CHECKS")
    
    # Check Mining-relevante Inhalte
    cursor.execute("""
        SELECT COUNT(*) FROM SearchResults 
        WHERE LOWER(extracted_data) LIKE '%mine%' 
           OR LOWER(extracted_data) LIKE '%mining%'
           OR LOWER(extracted_data) LIKE '%gold%'
           OR LOWER(extracted_data) LIKE '%copper%'
    """)
    mining_relevant = cursor.fetchone()[0]
    print(f"  ✅ Mining-relevante Inhalte: {mining_relevant} Einträge")
    
    # Check Quebec-Referenzen
    cursor.execute("""
        SELECT COUNT(*) FROM SearchResults 
        WHERE LOWER(extracted_data) LIKE '%quebec%' 
           OR LOWER(raw_content) LIKE '%quebec%'
    """)
    quebec_refs = cursor.fetchone()[0]
    print(f"  ✅ Quebec-Referenzen: {quebec_refs} Einträge")
    
    # 9. Datenbank-Zusammenfassung
    print("\n📈 DATENBANK-ZUSAMMENFASSUNG")
    print(f"  ModelStatistics: {model_stats_count}")
    print(f"  FieldStatistics: {field_stats_count}")
    print(f"  FieldConsistency: {consistency_count}")
    print(f"  Sources: {sources_count}")
    print(f"  SearchResults: {results_count}")
    print(f"  Dummy-Werte: {dummy_count}")
    print(f"  Mining-relevant: {mining_relevant}")
    print(f"  Quebec-Referenzen: {quebec_refs}")
    
    # 10. Qualitätsbewertung
    print("\n⭐ QUALITÄTSBEWERTUNG")
    
    quality_score = 0
    max_score = 10
    
    # Bewertungskriterien
    if model_stats_count > 0:
        quality_score += 2
        print("  ✅ ModelStatistics vorhanden (+2)")
    
    if field_stats_count > 0:
        quality_score += 2
        print("  ✅ FieldStatistics vorhanden (+2)")
    
    if sources_count > 0:
        quality_score += 2
        print("  ✅ Sources vorhanden (+2)")
    
    if dummy_count == 0:
        quality_score += 2
        print("  ✅ Keine Dummy-Werte (+2)")
    
    if mining_relevant > 0:
        quality_score += 1
        print("  ✅ Mining-relevante Inhalte (+1)")
    
    if quebec_refs > 0:
        quality_score += 1
        print("  ✅ Quebec-Referenzen (+1)")
    
    quality_percentage = (quality_score / max_score) * 100
    print(f"\n🎯 GESAMTBEWERTUNG: {quality_score}/{max_score} ({quality_percentage:.1f}%)")
    
    if quality_percentage >= 80:
        print("  ✅ AUSGEZEICHNET - Datenbank ist hochqualitativ")
    elif quality_percentage >= 60:
        print("  ✅ GUT - Datenbank ist akzeptabel")
    elif quality_percentage >= 40:
        print("  ⚠️  BEFRIEDIGEND - Verbesserungen empfohlen")
    else:
        print("  ❌ UNGENÜGEND - Datenbank benötigt Überarbeitung")
    
    conn.close()
    
    print("\n" + "="*80)
    print("🏁 DATENBANK-VALIDIERUNG ABGESCHLOSSEN")
    
    return {
        'model_stats_count': model_stats_count,
        'field_stats_count': field_stats_count,
        'consistency_count': consistency_count,
        'sources_count': sources_count,
        'results_count': results_count,
        'dummy_count': dummy_count,
        'mining_relevant': mining_relevant,
        'quebec_refs': quebec_refs,
        'quality_score': quality_score,
        'quality_percentage': quality_percentage
    }

if __name__ == "__main__":
    validate_database_entries()