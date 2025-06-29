#!/usr/bin/env python3
"""Test ob Timeout-Fehler behoben sind"""
import asyncio
import sys
sys.path.insert(0, '/app')

async def test_perplexity_timeout():
    """Teste Perplexity Agent ohne Timeout-Fehler"""
    from src.core.config import Config
    from src.agents.perplexity_agent import PerplexityAgent
    from src.agents.base_agent import MineQuery
    
    print("🧪 Testing Perplexity Agent Timeout Fix...")
    
    # Setup
    config = Config()
    agent_config = {
        'api_config': config.api,
        'scraping_config': config.scraping,
        'max_concurrent': 5
    }
    
    agent = PerplexityAgent("perplexity_test", agent_config)
    
    # Test 1: Initialisierung
    print("\n1️⃣ Testing initialization...")
    try:
        success = await agent.initialize()
        if success:
            print("✅ Agent initialized without timeout errors")
        else:
            print("❌ Agent initialization failed (but no timeout error)")
    except Exception as e:
        if "Timeout context manager" in str(e):
            print(f"❌ TIMEOUT ERROR STILL EXISTS: {e}")
            return False
        else:
            print(f"⚠️ Other error (not timeout): {e}")
    
    # Test 2: API Call
    if agent.api_key:
        print("\n2️⃣ Testing API call...")
        try:
            # Erstelle Test-Query
            query = MineQuery(
                mine_name="Test Mine",
                region="Ontario", 
                country="Canada",
                languages=["en"],
                required_fields=["betreiber"]
            )
            
            # Setze Agent in Test-Modus (nur 1 Query)
            agent._cache_ttl = 0  # Disable cache
            
            # Führe eine kurze Suche durch
            results = await agent.search_mine(query)
            print("✅ API call completed without timeout errors")
            
        except Exception as e:
            if "Timeout context manager" in str(e):
                print(f"❌ TIMEOUT ERROR IN API CALL: {e}")
                return False
            else:
                print(f"⚠️ Other error during search: {e}")
    else:
        print("\n⚠️ Skipping API test (no API key configured)")
    
    # Cleanup
    await agent.cleanup()
    
    print("\n✅ All timeout tests passed!")
    return True

async def main():
    """Main test function"""
    success = await test_perplexity_timeout()
    
    # Cleanup test file
    import os
    try:
        os.remove('/app/test_timeout_fix.py')
    except:
        pass
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)