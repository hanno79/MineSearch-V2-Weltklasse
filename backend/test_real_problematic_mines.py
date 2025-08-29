#!/usr/bin/env python3
"""
Author: rahn
Datum: 25.08.2025
Version: 1.0
Beschreibung: Live-Test mit echten problematischen Minen

LIVE-TEST 25.08.2025: Testet Schutzmaßnahmen mit echten Minen die früher Probleme verursacht haben
"""

import sys
sys.path.insert(0, '.')

import logging
from pathlib import Path

from minesearch.search_service import MineSearchService
from minesearch.field_name_blacklist import is_field_name_value

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_problematic_mines():
    """
    LIVE-TEST 25.08.2025: Testet echte Minen die früher Feldkontamination verursacht haben
    """
    
    print("🔥 LIVE-TEST MIT PROBLEMATISCHEN MINEN")
    print("=" * 50)
    
    # Diese Minen haben früher Feldkontamination verursacht
    problematic_mines = [
        "Eleonore Mine",      # Verursachte x-Koordinate im Betreiber-Feld
        "Canadian Malartic",  # Verursachte Region im Country-Feld  
        "Detour Lake",        # Verursachte y-Koordinate in verschiedenen Feldern
        "Agnico Eagle",       # Allgemeine Feldkontamination
        "Goldcorp Mine"       # Template-Response Probleme
    ]
    
    search_service = MineSearchService()
    
    test_results = {
        'total_tests': 0,
        'successful_extractions': 0,
        'blocked_contaminations': 0,
        'null_normalizations': 0,
        'clean_results': 0
    }
    
    for mine_name in problematic_mines:
        print(f"\n🔍 TESTE: {mine_name}")
        print("-" * 30)
        
        try:
            test_results['total_tests'] += 1
            
            # Führe echte Suche durch
            logger.info(f"[LIVE TEST] Starte Suche für {mine_name}...")
            
            # Simuliere Suche mit einem sicheren Provider
            import asyncio
            results = asyncio.run(search_service.search_mine(
                mine_name=mine_name,
                model="openrouter:deepseek-free",  # Schneller Provider für Test
                country=None
            ))
            
            if results and results.get('success'):
                test_results['successful_extractions'] += 1
                print(f"✅ Suche erfolgreich für {mine_name}")
                
                # Analysiere Ergebnis auf Kontamination
                if 'structured_data' in results:
                    structured_data = results.get('structured_data', {})
                    
                    print(f"📊 Analyse von {mine_name}:")
                    
                    contamination_found = False
                    null_values = 0
                    clean_fields = 0
                    
                    for field, value in structured_data.items():
                        if field.startswith('_'):
                            continue
                            
                        if value is None:
                            null_values += 1
                            print(f"   🔄 {field}: NULL (normalisiert)")
                        elif value and str(value).strip():
                            # Prüfe auf Feldkontamination
                            if is_field_name_value(str(value), field):
                                contamination_found = True
                                print(f"   🚨 {field}: '{value}' (KONTAMINATION GEFUNDEN!)")
                            else:
                                clean_fields += 1
                                value_display = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
                                print(f"   ✅ {field}: '{value_display}' (sauber)")
                        else:
                            null_values += 1
                            print(f"   🔄 {field}: leer → NULL")
                    
                    if not contamination_found:
                        test_results['clean_results'] += 1
                        print(f"   🎉 ERGEBNIS: Keine Kontamination gefunden!")
                    else:
                        print(f"   ❌ ERGEBNIS: Kontamination erkannt - Schutz fehlgeschlagen!")
                    
                    if null_values > 0:
                        test_results['null_normalizations'] += null_values
                        print(f"   📈 {null_values} NULL-Normalisierungen")
                    
                    print(f"   📊 {clean_fields} saubere Felder")
                else:
                    print(f"   ⚠️ Keine structured_data gefunden")
                
            else:
                print(f"❌ Suche fehlgeschlagen: {results.get('error', 'Unbekannter Fehler') if results else 'Keine Ergebnisse'}")
        
        except Exception as e:
            print(f"❌ Test-Fehler für {mine_name}: {e}")
            logger.error(f"[LIVE TEST] Fehler bei {mine_name}: {e}")
    
    # Gesamtergebnis
    print(f"\n📊 LIVE-TEST GESAMTERGEBNIS")
    print("=" * 40)
    print(f"📋 Getestete Minen: {test_results['total_tests']}")
    print(f"✅ Erfolgreiche Extraktionen: {test_results['successful_extractions']}")
    print(f"🎯 Saubere Ergebnisse (keine Kontamination): {test_results['clean_results']}")
    print(f"🔄 NULL-Normalisierungen: {test_results['null_normalizations']}")
    
    if test_results['successful_extractions'] > 0:
        success_rate = (test_results['clean_results'] / test_results['successful_extractions']) * 100
        print(f"📈 Schutz-Erfolgsrate: {success_rate:.1f}%")
        
        if success_rate == 100:
            print("🎉 PERFEKT: Alle Schutzmaßnahmen funktionieren!")
        elif success_rate >= 80:
            print("✅ GUT: Schutzmaßnahmen weitgehend wirksam")
        else:
            print("⚠️ PROBLEM: Schutzmaßnahmen benötigen Nachbesserung")
    
    return test_results

def main():
    """Hauptfunktion"""
    test_results = test_problematic_mines()
    
    # Return code für Automatisierung
    if test_results['successful_extractions'] == 0:
        exit(1)  # Keine erfolgreichen Tests
    
    success_rate = (test_results['clean_results'] / test_results['successful_extractions']) * 100
    exit(0 if success_rate >= 80 else 1)

if __name__ == "__main__":
    main()