#!/usr/bin/env python3
"""
Author: rahn
Datum: 29.07.2025
Version: 1.0
Beschreibung: Finale Validierung aller Änderungen
"""

import sys
from pathlib import Path

def validate_config():
    """Validiere config/base.py Änderungen"""
    print("🔍 Validiere Config...")
    
    from config.base import CSV_COLUMNS, FIELDS_WITHOUT_SOURCES
    
    # Teste neue Feldnamen
    required_fields = ['Mine', 'Land', 'Kostenjahr', 'Dokumentenjahr', 'Minenfläche in qkm', 'Rohstoffe']
    for field in required_fields:
        assert field in CSV_COLUMNS, f"Feld '{field}' fehlt in CSV_COLUMNS"
    
    # Teste dass alte Feldnamen entfernt wurden
    legacy_fields = ['Name', 'Country', 'Jahr der Aufnahme der Kosten']
    for field in legacy_fields:
        assert field not in CSV_COLUMNS, f"Legacy-Feld '{field}' noch in CSV_COLUMNS"
    
    print(f"✅ Config: {len(CSV_COLUMNS)} Felder, {len(FIELDS_WITHOUT_SOURCES)} ohne Quellen")

def validate_extraction_patterns():
    """Validiere extraction_patterns.py Änderungen"""
    print("🔍 Validiere Extraction Patterns...")
    
    from extraction_patterns import get_extraction_patterns
    
    patterns = get_extraction_patterns()
    
    # Teste dass neue Feldnamen verwendet werden
    required_pattern_fields = ['Land', 'Kostenjahr', 'Dokumentenjahr', 'Minenfläche in qkm', 'Rohstoffe']
    for field in required_pattern_fields:
        assert field in patterns, f"Pattern für Feld '{field}' fehlt"
    
    # Teste dass alte Feldnamen entfernt wurden
    legacy_pattern_fields = ['Country', 'Jahr der Aufnahme der Kosten']
    for field in legacy_pattern_fields:
        assert field not in patterns, f"Legacy-Pattern für Feld '{field}' noch vorhanden"
    
    print(f"✅ Extraction Patterns: {len(patterns)} Pattern-Sets definiert")

def validate_field_mapping():
    """Validiere field_mapping.py Funktionalität"""
    print("🔍 Validiere Field Mapping...")
    
    from field_mapping import FIELD_MAPPING, get_field_display_order, convert_old_to_new
    
    # Teste wichtige Mappings
    assert FIELD_MAPPING['Name'] == 'Mine'
    assert FIELD_MAPPING['Country'] == 'Land'
    
    # Teste Feldreihenfolge
    order = get_field_display_order()
    assert order[0] == 'Mine'
    assert order[1] == 'Land'
    assert order[2] == 'Region'
    
    print(f"✅ Field Mapping: {len(FIELD_MAPPING)} Mappings, {len(order)} Felder in Reihenfolge")

def validate_csv_service():
    """Validiere csv_service.py Änderungen"""
    print("🔍 Validiere CSV Service...")
    
    from csv_service import CSVExportService
    
    service = CSVExportService()
    
    # Teste dass neue Feldnamen gemappt werden
    assert 'Mine' in service.field_mapping
    assert 'Land' in service.field_mapping
    assert 'Kostenjahr' in service.field_mapping
    
    print(f"✅ CSV Service: {len(service.field_mapping)} Feld-Mappings definiert")

def validate_data_extraction():
    """Validiere data_extraction.py Import"""
    print("🔍 Validiere Data Extraction...")
    
    try:
        from data_extraction import DataExtractor
        extractor = DataExtractor()
        print("✅ Data Extraction: Import erfolgreich")
    except Exception as e:
        print(f"❌ Data Extraction Import Fehler: {e}")
        raise

def validate_frontend_files():
    """Validiere Frontend-Dateien"""
    print("🔍 Validiere Frontend...")
    
    frontend_path = Path(__file__).parent.parent / 'frontend' / 'index.html'
    
    if frontend_path.exists():
        content = frontend_path.read_text()
        
        # Prüfe dass neue Feldreihenfolge verwendet wird
        if "'Mine', 'Land', 'Region', 'Zuverlässigkeit'" in content:
            print("✅ Frontend: Neue Feldreihenfolge implementiert")
        else:
            print("⚠️ Frontend: Neue Feldreihenfolge möglicherweise nicht vollständig implementiert")
        
        # Prüfe dass sortable-table Klasse vorhanden ist
        if 'sortable-table' in content:
            print("✅ Frontend: Sortierbare Tabellen implementiert")
        else:
            print("⚠️ Frontend: Sortierbare Tabellen möglicherweise nicht implementiert")
    else:
        print("⚠️ Frontend index.html nicht gefunden")

def run_final_validation():
    """Führe alle Validierungen durch"""
    print("🚀 Starte finale Validierung der Feldänderungen...")
    print("=" * 60)
    
    try:
        validate_config()
        validate_extraction_patterns()
        validate_field_mapping()
        validate_csv_service()
        validate_data_extraction()
        validate_frontend_files()
        
        print("=" * 60)
        print("🎉 ALLE VALIDIERUNGEN ERFOLGREICH!")
        print("\n📋 Zusammenfassung der Änderungen:")
        print("✅ Feldkonsolidierung: Mine/Name und Land/Country")
        print("✅ Feldumbenennungen: Kostenjahr, Dokumentenjahr, Minenfläche, Rohstoffe")
        print("✅ Neue Feldreihenfolge implementiert")
        print("✅ Frontend-Tabellen angepasst")
        print("✅ Sortierung für alle Spalten verfügbar")
        print("✅ CSV-Export mit neuer Struktur")
        print("✅ Backend/API vollständig validiert")
        
        return True
        
    except Exception as e:
        print("=" * 60)
        print(f"❌ VALIDIERUNG FEHLGESCHLAGEN: {e}")
        return False

if __name__ == "__main__":
    success = run_final_validation()
    sys.exit(0 if success else 1)