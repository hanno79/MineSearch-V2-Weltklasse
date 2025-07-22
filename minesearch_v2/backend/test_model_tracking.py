#!/usr/bin/env python3
"""
Test script to verify corrected model tracking
"""

import asyncio
from search_service import search_service
import logging
logging.basicConfig(level=logging.INFO)

async def test_model_tracking():
    """Test dass das korrekte Modell in der Datenbank gespeichert wird"""
    
    # Test 1: Ein spezifisches Modell anfordern
    print("\n=== TEST 1: Spezifisches Modell ===")
    result1 = await search_service.search_mine(
        mine_name='Test Mine Alpha',
        model='openrouter:anthropic/claude-3.5-sonnet',
        country='Canada'
    )
    
    if result1.get('success'):
        model_used = result1['data'].get('model_used', 'UNBEKANNT')
        print(f"✅ Test Mine Alpha - Model used: {model_used}")
    else:
        print(f"❌ Test Mine Alpha - Fehler: {result1.get('error')}")
    
    # Test 2: Fallback-Verhalten testen (ungültiges Modell)
    print("\n=== TEST 2: Ungültiges Modell (Fallback) ===")
    result2 = await search_service.search_mine(
        mine_name='Test Mine Beta',
        model='openrouter:invalid-model-name-xyz',
        country='Canada'
    )
    
    if result2.get('success'):
        model_used = result2['data'].get('model_used', 'UNBEKANNT')
        print(f"✅ Test Mine Beta - Model used: {model_used}")
    else:
        print(f"❌ Test Mine Beta - Fehler: {result2.get('error')}")
    
    # Test 3: Modell ohne Provider-Präfix
    print("\n=== TEST 3: Modell ohne Provider-Präfix ===")
    result3 = await search_service.search_mine(
        mine_name='Test Mine Gamma',
        model='kimi-k2',
        country='Canada'
    )
    
    if result3.get('success'):
        model_used = result3['data'].get('model_used', 'UNBEKANNT')
        print(f"✅ Test Mine Gamma - Model used: {model_used}")
    else:
        print(f"❌ Test Mine Gamma - Fehler: {result3.get('error')}")
    
    return [result1, result2, result3]

async def check_database_entries():
    """Prüfe die Database-Einträge direkt"""
    print("\n=== DATABASE VERIFICATION ===")
    
    from database.manager import DatabaseManager
    db_manager = DatabaseManager()
    
    with db_manager.get_session() as session:
        from database.models import SearchResult
        
        # Hole letzte 5 Einträge
        results = session.query(SearchResult).order_by(SearchResult.id.desc()).limit(5).all()
        
        print(f"Letzte {len(results)} Suchergebnisse:")
        for result in results:
            print(f"  ID {result.id}: {result.mine_name} -> {result.model_used}")

if __name__ == "__main__":
    print("🧪 Model Tracking Correction Test")
    print("=" * 50)
    
    test_results = asyncio.run(test_model_tracking())
    asyncio.run(check_database_entries())
    
    print("\n" + "=" * 50)
    print("✅ Model Tracking Test abgeschlossen!")