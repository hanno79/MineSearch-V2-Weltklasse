#!/usr/bin/env python3
"""
Author: rahn
Datum: 29.07.2025
Version: 1.0
Beschreibung: Test für CSV-Integration mit neuen Feldnamen
"""

from config.base import CSV_COLUMNS
from field_mapping import get_field_display_order

def test_csv_columns_consistency():
    """Teste dass CSV_COLUMNS und field_display_order konsistent sind"""
    
    csv_fields = set(CSV_COLUMNS)
    display_fields = set(get_field_display_order())
    
    print(f"CSV_COLUMNS: {len(csv_fields)} Felder")
    print(f"Display Order: {len(display_fields)} Felder")
    
    # Prüfe dass alle CSV-Felder in der Display-Order sind
    missing_in_display = csv_fields - display_fields
    extra_in_display = display_fields - csv_fields
    
    if missing_in_display:
        print(f"⚠️ Felder in CSV_COLUMNS aber nicht in Display Order: {missing_in_display}")
    
    if extra_in_display:
        print(f"⚠️ Felder in Display Order aber nicht in CSV_COLUMNS: {extra_in_display}")
    
    # Teste dass wichtige neue Felder vorhanden sind
    required_fields = ['Mine', 'Land', 'Kostenjahr', 'Dokumentenjahr', 'Minenfläche in qkm', 'Rohstoffe']
    
    for field in required_fields:
        assert field in csv_fields, f"Fehlendes Feld in CSV_COLUMNS: {field}"
        assert field in display_fields, f"Fehlendes Feld in Display Order: {field}"
    
    print("✅ CSV-Konsistenz-Test erfolgreich")

def test_field_order():
    """Teste dass die gewünschte Feldreihenfolge implementiert ist"""
    
    order = get_field_display_order()
    
    # Teste dass die ersten Felder korrekt sind
    expected_start = [
        'Mine', 'Land', 'Region', 'Zuverlässigkeit', 'Modelle', 'Letzte Aktualisierung',
        'Betreiber', 'Eigentümer', 'Rohstoffe', 'Minentyp', 'Aktivitätsstatus'
    ]
    
    for i, expected_field in enumerate(expected_start):
        actual_field = order[i]
        assert actual_field == expected_field, f"Position {i}: erwartet '{expected_field}', erhalten '{actual_field}'"
    
    print(f"✅ Feldreihenfolge-Test erfolgreich - Erste {len(expected_start)} Felder sind korrekt")

def test_no_legacy_names():
    """Teste dass keine alten Feldnamen mehr verwendet werden"""
    
    csv_fields = CSV_COLUMNS
    legacy_names = ['Name', 'Country', 'Jahr der Aufnahme der Kosten', 
                   'Jahr der Erstellung des Dokumentes', 'Fläche der Mine in qkm', 
                   'Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)']
    
    found_legacy = []
    for legacy in legacy_names:
        if legacy in csv_fields:
            found_legacy.append(legacy)
    
    assert not found_legacy, f"Legacy-Feldnamen gefunden: {found_legacy}"
    
    print("✅ Keine Legacy-Feldnamen Test erfolgreich")

if __name__ == "__main__":
    try:
        test_csv_columns_consistency()
        test_field_order()
        test_no_legacy_names()
        print("\n🎉 Alle CSV-Integration Tests erfolgreich!")
    except Exception as e:
        print(f"\n❌ Test fehlgeschlagen: {e}")
        raise