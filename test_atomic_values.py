#!/usr/bin/env python3
"""
SCHEMA-NORMALISIERUNG 28.08.2025: Test für atomische Feldwerte
Testet die neue normalisierte Datenbankstruktur
"""

import os
import sys
import asyncio
import logging

# Add backend to path
sys.path.insert(0, '/app/backend')

from minesearch.search_service import MineSearchService
from minesearch.database import db_manager
from minesearch.field_value_parser import extract_atomic_value_and_sources, normalize_atomic_value
from minesearch.atomic_value_service import calculate_best_atomic_value

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_atomic_values():
    """Test atomische Feldwerte System"""
    
    print("=== ATOMIC VALUES SYSTEM TEST ===")
    print()
    
    # 1. Test Field Value Parser
    print("1. Testing Field Value Parser...")
    test_values = [
        "Kanada [1,2,3,4,5]",
        "Gold Mine [1,2,3]", 
        "Barrick Gold Corporation [10,11,12,13,14]",
        "Kanada",
        "X [1,2,3]",
        ""
    ]
    
    for test_value in test_values:
        atomic, sources = extract_atomic_value_and_sources(test_value)
        normalized = normalize_atomic_value(atomic)
        print(f"  Input: '{test_value}' → Atomic: '{atomic}' | Sources: {sources} | Normalized: {normalized}")
    
    print()
    
    # 2. Test Database Tables
    print("2. Testing Database Tables...")
    with db_manager.get_session() as session:
        # Check if new tables exist
        try:
            from minesearch.database.models import FieldValue, FieldValueSource
            field_count = session.query(FieldValue).count()
            source_count = session.query(FieldValueSource).count()
            print(f"  ✅ FieldValue table: {field_count} entries")
            print(f"  ✅ FieldValueSource table: {source_count} entries")
        except Exception as e:
            print(f"  ❌ Database table error: {e}")
    
    print()
    
    # 3. Test Search with atomic values
    print("3. Testing Search with Atomic Value Storage...")
    search_service = MineSearchService()
    
    try:
        # Führe eine kleine Test-Suche durch
        print("  🚀 Starting test search for 'Eleonore Mine'...")
        result = await search_service.search_mine(
            mine_name="Eleonore Mine",
            model="openrouter:deepseek-free",
            country="Kanada"
        )
        
        if result.get('success'):
            print(f"  ✅ Search successful!")
            structured_data = result['data'].get('structured_data', {})
            print(f"  📊 Found {len(structured_data)} fields")
            
            # Zeige einige Beispielfelder
            for i, (field, value) in enumerate(structured_data.items()):
                if i < 3:  # Nur erste 3 Felder
                    print(f"    {field}: {value}")
            
        else:
            print(f"  ❌ Search failed: {result.get('error')}")
            
    except Exception as e:
        print(f"  ❌ Search error: {e}")
        
    print()
    
    # 4. Test Atomic Value Service
    print("4. Testing Atomic Value Service...")
    try:
        with db_manager.get_session() as session:
            # Test für Eleonore Mine, Land Feld
            best_value = calculate_best_atomic_value(
                session, "Eleonore Mine", "Land", fallback_to_json=True
            )
            
            print(f"  🎯 Best value for 'Eleonore Mine.Land':")
            print(f"    Method: {best_value['method']}")
            print(f"    Value: {best_value['display_value']}")
            print(f"    Confidence: {best_value['confidence_score']}")
            print(f"    Frequency: {best_value['frequency']}")
            
    except Exception as e:
        print(f"  ❌ Atomic value service error: {e}")
        
    print()
    
    # 5. Test Database Content
    print("5. Checking Database Content...")
    with db_manager.get_session() as session:
        try:
            from minesearch.database.models import SearchResult, FieldValue
            
            # Anzahl SearchResults
            search_results = session.query(SearchResult).count()
            print(f"  📊 Total SearchResults: {search_results}")
            
            # Anzahl FieldValues
            field_values = session.query(FieldValue).count()
            print(f"  📊 Total FieldValues: {field_values}")
            
            # Beispiele von FieldValues
            if field_values > 0:
                examples = session.query(FieldValue).limit(5).all()
                print(f"  🔍 Example FieldValues:")
                for fv in examples:
                    print(f"    {fv.field_name}: '{fv.atomic_value}' (confidence: {fv.confidence_score})")
                    
        except Exception as e:
            print(f"  ❌ Database content check error: {e}")
            
    print()
    print("=== TEST COMPLETED ===")

if __name__ == "__main__":
    asyncio.run(test_atomic_values())