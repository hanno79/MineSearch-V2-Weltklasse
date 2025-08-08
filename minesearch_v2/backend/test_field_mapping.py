#!/usr/bin/env python3
"""
Author: rahn
Datum: 29.07.2025
Version: 1.0
Beschreibung: Test für Feldmapping-Funktionalität
"""

import pytest
from field_mapping import convert_old_to_new, convert_new_to_old, FIELD_MAPPING, get_field_display_order

def test_field_mapping_consistency():
    """Teste dass alle alten Feldnamen korrekt gemappt werden"""
    
    # Teste bekannte Mappings
    test_data = {
        'Name': 'TestMine',
        'Country': 'Chile',
        'Jahr der Aufnahme der Kosten': '2023',
        'Jahr der Erstellung des Dokumentes': '2024',
        'Fläche der Mine in qkm': '15.5',
        'Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)': 'Gold, Kupfer'
    }
    
    converted = convert_old_to_new(test_data)
    
    # Prüfe dass alte Feldnamen korrekt konvertiert wurden
    assert converted['Mine'] == 'TestMine'
    assert converted['Land'] == 'Chile'
    assert converted['Kostenjahr'] == '2023'
    assert converted['Dokumentenjahr'] == '2024'
    assert converted['Minenfläche in qkm'] == '15.5'
    assert converted['Rohstoffe'] == 'Gold, Kupfer'
    
    print("✅ Feldmapping-Test erfolgreich")

def test_field_display_order():
    """Teste dass die Feldreihenfolge korrekt ist"""
    
    order = get_field_display_order()
    
    # Prüfe dass die gewünschte Reihenfolge eingehalten wird
    expected_start = ['Mine', 'Land', 'Region', 'Zuverlässigkeit', 'Modelle', 'Letzte Aktualisierung']
    
    for i, field in enumerate(expected_start):
        assert order[i] == field, f"Position {i}: erwartet '{field}', erhalten '{order[i]}'"
    
    # Prüfe dass alle wichtigen Felder enthalten sind
    assert 'Mine' in order
    assert 'Land' in order
    assert 'Kostenjahr' in order
    assert 'Dokumentenjahr' in order
    assert 'Minenfläche in qkm' in order
    assert 'Rohstoffe' in order
    
    print(f"✅ Feldreihenfolge-Test erfolgreich - {len(order)} Felder in korrekter Reihenfolge")

def test_reverse_mapping():
    """Teste dass Rückwärts-Mapping funktioniert"""
    
    new_data = {
        'Mine': 'TestMine',
        'Land': 'Chile',
        'Kostenjahr': '2023'
    }
    
    old_data = convert_new_to_old(new_data)
    
    assert old_data['Name'] == 'TestMine'
    assert old_data['Country'] == 'Chile'
    assert old_data['Jahr der Aufnahme der Kosten'] == '2023'
    
    print("✅ Rückwärts-Mapping-Test erfolgreich")

if __name__ == "__main__":
    try:
        test_field_mapping_consistency()
        test_field_display_order()
        test_reverse_mapping()
        print("\n🎉 Alle Field-Mapping Tests erfolgreich!")
    except Exception as e:
        print(f"\n❌ Test fehlgeschlagen: {e}")
        raise