#!/usr/bin/env python3
"""
Author: rahn
Datum: 25.08.2025
Version: 1.0
Beschreibung: Automatische NULL-Normalisierung (ohne Benutzerinteraktion)

AUTOMATED NULL-NORMALIZATION 25.08.2025: Führt NULL-Normalisierung automatisch durch
"""

import sys
sys.path.insert(0, '.')

from minesearch.null_normalizer import NullNormalizer
import logging

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def run_automatic_null_normalization():
    """
    AUTOMATISCHE NULL-NORMALISIERUNG 25.08.2025
    Führt NULL-Normalisierung ohne Benutzerinteraktion durch
    """
    print("🔄 AUTOMATISCHE NULL-NORMALISIERUNG")
    print("=" * 50)
    
    normalizer = NullNormalizer()
    
    # Analysiere aktuelle NULL-Situation
    print("📊 Analysiere aktuelle NULL-Werte...")
    stats = normalizer.get_null_statistics()
    
    if 'error' in stats:
        print(f"❌ Fehler bei Analyse: {stats['error']}")
        return False
    
    print(f"📈 {stats['total_entries']} Einträge analysiert")
    print(f"🔄 {stats['total_null_normalizable']} normalisierbare NULL-Werte gefunden")
    
    if stats['null_normalizable_fields']:
        print("\n🔍 Top 10 normalisierbare Felder:")
        sorted_fields = sorted(stats['null_normalizable_fields'].items(), key=lambda x: x[1], reverse=True)
        for field, count in sorted_fields[:10]:
            print(f"   - {field}: {count} Werte")
        
        if len(sorted_fields) > 10:
            remaining = sum(count for _, count in sorted_fields[10:])
            print(f"   - ... und {len(sorted_fields)-10} weitere Felder mit {remaining} Werten")
    
    if stats['total_null_normalizable'] == 0:
        print("✅ Keine NULL-Normalisierung nötig - alle Werte bereits korrekt!")
        return True
    
    # Automatische Normalisierung ohne Benutzerinteraktion
    print(f"\n🚀 Starte automatische NULL-Normalisierung für {stats['total_null_normalizable']} Werte...")
    print("⚠️  WARNUNG: Dieser Vorgang verändert die Datenbank irreversibel!")
    
    # Führe Normalisierung durch
    result_stats = normalizer.normalize_database(batch_size=200)  # Größere Batches für Performance
    
    if 'error' in result_stats:
        print(f"❌ Fehler bei Normalisierung: {result_stats['error']}")
        return False
    
    print(f"\n✅ NULL-NORMALISIERUNG ERFOLGREICH ABGESCHLOSSEN!")
    print(f"   📊 {result_stats['processed_entries']} Einträge verarbeitet")
    print(f"   ✅ {result_stats['normalized_entries']} Einträge normalisiert")
    print(f"   ⏭️ {result_stats['skipped_entries']} Einträge übersprungen")
    print(f"   ❌ {result_stats['error_entries']} Fehler")
    
    # Erfolgsrate berechnen
    if result_stats['processed_entries'] > 0:
        success_rate = (result_stats['normalized_entries'] / result_stats['processed_entries']) * 100
        print(f"   📈 Erfolgsrate: {success_rate:.1f}%")
    
    # Finale Validierung
    print(f"\n🔍 Führe finale Validierung durch...")
    final_stats = normalizer.get_null_statistics()
    
    if 'error' not in final_stats:
        remaining_nulls = final_stats['total_null_normalizable']
        print(f"   📊 {remaining_nulls} normalisierbare NULL-Werte verbleibend")
        
        if remaining_nulls == 0:
            print("   🎉 PERFEKT: Alle NULL-Werte erfolgreich normalisiert!")
        elif remaining_nulls < stats['total_null_normalizable']:
            improvement = stats['total_null_normalizable'] - remaining_nulls
            print(f"   📈 VERBESSERUNG: {improvement} NULL-Werte erfolgreich normalisiert")
        else:
            print("   ⚠️ WARNUNG: Keine Verbesserung erkannt - möglicherweise Problem")
    
    return True

if __name__ == "__main__":
    success = run_automatic_null_normalization()
    exit(0 if success else 1)