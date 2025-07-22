#!/usr/bin/env python3
"""
Author: rahn
Datum: 19.07.2025
Version: 1.0
Beschreibung: Debug Search Service für Error-Diagnose
"""

import sys
import os
sys.path.append('/app/minesearch_v2/backend')

import logging
logging.basicConfig(level=logging.DEBUG)

def test_search_service():
    """Test MineSearchService direkt"""
    print("🔧 Debug MineSearchService...")
    
    try:
        print("1. Import MineSearchService...")
        from search_service import MineSearchService
        print("✅ Import erfolgreich")
        
        print("2. Instanziierung...")
        service = MineSearchService()
        print("✅ Instanziierung erfolgreich")
        
        print("3. Test einfache Suche...")
        result = service.search(
            mine_name="Test Mine Debug",
            country="Canada",
            provider="perplexity",
            model="perplexity:sonar"
        )
        print(f"✅ Suche erfolgreich: {result.get('success', False)}")
        print(f"   Structured Data: {'structured_data' in result}")
        
        if 'error' in result:
            print(f"❌ Fehler in Ergebnis: {result['error']}")
            
        return True
        
    except Exception as e:
        print(f"❌ Fehler bei Search Service Test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_data_extractor():
    """Test DataExtractor direkt"""
    print("\n🔧 Debug DataExtractor...")
    
    try:
        print("1. Import DataExtractor...")
        from data_extraction import DataExtractor
        print("✅ Import erfolgreich")
        
        print("2. Instanziierung...")
        extractor = DataExtractor()
        print("✅ Instanziierung erfolgreich")
        
        print("3. Test Extraktion mit Mock-Response...")
        mock_response = """
        Mining Information for Test Mine:
        - Eigentümer: Test Company
        - Minentyp: Open-Pit
        - Aktivitätsstatus: Aktiv
        
        Sources:
        [1] https://test-source.com
        """
        
        result = extractor.extract_structured_data(mock_response, "Test Mine", "Canada")
        print(f"✅ Extraktion erfolgreich")
        print(f"   Felder extrahiert: {len([k for k, v in result.items() if v and v != 'X'])}")
        print(f"   Source Mapping: {'_source_mapping' in result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler bei DataExtractor Test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🧪 Debug Search Service und DataExtractor")
    print("=" * 60)
    
    data_extractor_ok = test_data_extractor()
    search_service_ok = test_search_service()
    
    print(f"\n{'='*60}")
    print(f"📊 DEBUG ERGEBNIS")
    print(f"DataExtractor: {'✅ OK' if data_extractor_ok else '❌ FEHLER'}")
    print(f"SearchService: {'✅ OK' if search_service_ok else '❌ FEHLER'}")
    
    if data_extractor_ok and search_service_ok:
        print(f"🎯 Beide Komponenten funktionieren - API-Problem ist woanders")
    else:
        print(f"🚨 Grundlegende Komponenten defekt - muss repariert werden")

if __name__ == "__main__":
    main()