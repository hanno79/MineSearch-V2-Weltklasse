"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Test-Skript für refactorierte Agenten
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.agents.base_agent import MineQuery
from src.core.config import Config
from src.core.logger import get_logger

logger = get_logger("test_refactored")


async def test_base_modules():
    """Testet die Base-Module"""
    print("\n=== Test Base-Module ===")
    
    try:
        # Test HTTP Client
        from src.agents.base import BaseHTTPClient
        
        async with BaseHTTPClient(timeout=10) as client:
            print("✓ BaseHTTPClient initialisiert")
        
        # Test Result Processor
        from src.agents.base import ResultProcessor
        processor = ResultProcessor("TestAgent")
        print("✓ ResultProcessor initialisiert")
        
        # Test Query Builder
        from src.agents.base import QueryBuilder
        builder = QueryBuilder()
        test_query = MineQuery(
            mine_name="Test Mine",
            region="Ontario",
            country="Canada",
            languages=["English"],
            required_fields=["location", "production"]
        )
        search_query = builder.build_search_query(test_query)
        print(f"✓ QueryBuilder generiert: {search_query}")
        
        # Test Cache Manager
        from src.agents.base import CacheManager
        cache = CacheManager(cache_dir="test_cache")
        await cache.set("test", "key", {"data": "test"})
        cached = await cache.get("test", "key")
        print(f"✓ CacheManager funktioniert: {cached}")
        
        return True
        
    except Exception as e:
        print(f"✗ Base-Module Test fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_search_strategies():
    """Testet refactorierte Search Strategies"""
    print("\n=== Test Search Strategies ===")
    
    try:
        from src.agents.search_strategies_refactored import SearchStrategies
        
        strategies = SearchStrategies()
        
        # Test Strategie-Auswahl
        strategy = strategies.select_strategy(
            mine_name="Test Mine",
            country="Canada",
            region="Ontario",
            required_fields=["location", "production"],
            available_agents=["tavily", "perplexity", "claude"],
            time_constraint=300
        )
        
        print(f"✓ Strategie ausgewählt: {strategy.name}")
        print(f"  - Scope: {strategy.scope.value}")
        print(f"  - Depth: {strategy.depth.value}")
        print(f"  - Time Budget: {strategy.time_budget}s")
        
        # Test Empfehlung
        recommendation = strategies.get_recommendation(
            mine_name="Test Mine",
            country="Canada", 
            region="Ontario",
            required_fields=["location", "production"],
            available_agents=["tavily", "perplexity"],
            time_constraint=300
        )
        
        print(f"✓ Empfehlung erhalten: {recommendation['selected_strategy'].name}")
        print(f"  - Reasoning: {recommendation['reasoning']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Search Strategies Test fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_brightdata_agent():
    """Testet refactorierten BrightData Agent"""
    print("\n=== Test BrightData Agent ===")
    
    try:
        from src.agents.brightdata_agent_refactored import BrightDataAgent
        
        config = {
            'api_config': type('obj', (object,), {'brightdata_key': 'test_key'})()
        }
        
        agent = BrightDataAgent('brightdata_test', config)
        print("✓ BrightDataAgent erstellt")
        
        # Test Komponenten
        print(f"✓ HTTP Client: {agent.http_client}")
        print(f"✓ Result Processor: {agent.result_processor}")
        print(f"✓ Query Builder: {agent.query_builder}")
        print(f"✓ Cache Manager: {agent.cache_manager}")
        
        # Test Query Building
        test_query = MineQuery(
            mine_name="Goldcorp Red Lake",
            region="Ontario",
            country="Canada",
            languages=["English"],
            required_fields=["location", "production"]
        )
        
        query_string = agent.query_builder.build_search_query(test_query)
        print(f"✓ Query generiert: {query_string[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"✗ BrightData Agent Test fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_premium_mining_research():
    """Testet refactorierten Premium Mining Research"""
    print("\n=== Test Premium Mining Research ===")
    
    try:
        from src.agents.premium_mining_research_refactored import PremiumMiningResearch
        
        config = {'api_config': type('obj', (object,), {})()}
        agent = PremiumMiningResearch('premium_test', config)
        print("✓ PremiumMiningResearch erstellt")
        
        # Test Komponenten
        print(f"✓ Phase Manager: {agent.phase_manager}")
        print(f"✓ Phase Executor: {agent.phase_executor}")
        print(f"✓ Result Aggregator: {agent.result_aggregator}")
        
        # Test Phase Selection
        test_query = MineQuery(
            mine_name="Test Mine",
            region="Ontario",
            country="Canada",
            languages=["English", "French"],
            required_fields=["location", "production", "revenue"]
        )
        
        phases = agent.phase_manager.get_phases_for_query(test_query)
        print(f"✓ {len(phases)} Phasen ausgewählt:")
        for phase in phases:
            print(f"  - {phase.name}: {phase.description}")
        
        # Test Result Conversion
        mock_result = {
            'mine_data': {
                'location': 'Ontario, Canada',
                'production': '100,000 oz/year'
            },
            'sources': {},
            'metadata': {'research_id': 'test_123'}
        }
        
        search_results = agent._convert_to_search_results(mock_result, test_query)
        print(f"✓ {len(search_results)} SearchResults konvertiert")
        
        return True
        
    except Exception as e:
        print(f"✗ Premium Mining Research Test fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_imports_compatibility():
    """Testet Import-Kompatibilität"""
    print("\n=== Test Import-Kompatibilität ===")
    
    try:
        # Teste ob alte Imports noch funktionieren
        from src.agents import search_strategies
        print("✓ Original search_strategies importierbar")
        
        from src.agents import brightdata_agent
        print("✓ Original brightdata_agent importierbar")
        
        from src.agents import premium_mining_research
        print("✓ Original premium_mining_research importierbar")
        
        return True
        
    except Exception as e:
        print(f"✗ Import-Kompatibilität fehlgeschlagen: {e}")
        return False


async def main():
    """Führt alle Tests aus"""
    print("🧪 Starte Tests für refactorierte Agenten...")
    
    results = {
        "Base Module": await test_base_modules(),
        "Search Strategies": await test_search_strategies(),
        "BrightData Agent": await test_brightdata_agent(),
        "Premium Mining Research": await test_premium_mining_research(),
        "Import Compatibility": await test_imports_compatibility()
    }
    
    # Zusammenfassung
    print("\n=== Test-Zusammenfassung ===")
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nGesamt: {passed}/{total} Tests bestanden")
    
    if passed == total:
        print("\n✅ Alle Tests erfolgreich!")
        return 0
    else:
        print(f"\n❌ {total - passed} Tests fehlgeschlagen")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)