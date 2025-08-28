#!/usr/bin/env python3
"""
Test für konsolidierte Quellenreferenzen
"""
import requests
import json

def test_consolidated_sources():
    print("🧪 KONSOLIDIERTE QUELLENREFERENZEN TEST")
    print("=" * 50)
    
    # Test API - nutze korrekte Results-API (nicht consolidated)
    response = requests.get("http://localhost:8000/api/results")
    
    if response.status_code != 200:
        print(f"❌ API-Fehler: {response.status_code}")
        return
    
    try:
        data = response.json()
        if not data['success']:
            print(f"❌ API-Antwort-Fehler: {data}")
            return
        
        # Guard: Check data structure exists before accessing
        if 'data' not in data or not data['data']:
            raise AssertionError("Test failed: API response missing or empty 'data' field")
        
        if 'results' not in data['data']:
            raise AssertionError("Test failed: API response missing 'results' field in data")
        
        if not isinstance(data['data']['results'], list):
            raise AssertionError("Test failed: 'results' field is not a list")
        
        results = data['data']['results']
        if len(results) == 0:
            print("⚠️ Test skipped: No results available in API response")
            print("   This could indicate:")
            print("   - Empty database")
            print("   - API filtering returning no results")
            print("   - Database connection issues")
            return
        
        first_mine = results[0]
        
        # Quellenanzahl aus strukturierten Daten bestimmen
        source_mapping = first_mine.get('_source_mapping', {})
        sources_dict = source_mapping.get('sources', {})
        unique_sources_count = len(sources_dict)
        
        print(f"✅ QUELLENANZAHL-TEST:")
        print(f"   Mine: {first_mine['mine_name']}")
        print(f"   Unique Sources: {unique_sources_count}")
        print(f"   Status: {'KORREKT' if unique_sources_count <= 15 else 'INKORREKT (zu viele)'}")
        
        # Test CSV export sample - nutze strukturierte Daten
        structured_data = first_mine.get('structured_data', {})
        fields_with_sources = 0
        total_fields = 0
        
        for field, value in structured_data.items():
            if field not in ['Quellenangaben', '_source_mapping'] and value and value.strip():
                total_fields += 1
                if '[' in value and ']' in value:
                    fields_with_sources += 1
                    print(f"     ✓ {field}: {value[:50]}...")
                else:
                    print(f"     ❌ {field}: {value[:50]}... (KEINE QUELLEN)")
        
        print(f"\n✅ CSV-QUELLEN-TEST:")
        print(f"   Felder mit Werten: {total_fields}")
        print(f"   Felder mit Quellen: {fields_with_sources}")
        if total_fields > 0:
            success_rate = fields_with_sources/total_fields*100
            print(f"   Erfolgsrate: {success_rate:.1f}%")
            print(f"   Status: {'PERFEKT' if fields_with_sources == total_fields else 'VERBESSERUNG NÖTIG'}")
        else:
            print("   Status: KEINE FELDER ZUM TESTEN")
        
        # Test field_sources in _source_mapping
        print(f"\n🎯 FIELD_SOURCES TEST:")
        field_sources = source_mapping.get('field_sources', {})
        fields_with_field_sources = len(field_sources)
        
        print(f"   Felder mit field_sources: {fields_with_field_sources}")
        for field, source_ids in field_sources.items():
            print(f"     ✓ {field}: {source_ids}")
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
        print(f"Raw Response: {response.text[:500]}")

if __name__ == "__main__":
    test_consolidated_sources()