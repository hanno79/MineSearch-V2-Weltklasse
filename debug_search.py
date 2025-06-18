#!/usr/bin/env python3
"""Debug why only Exa returns results"""
import asyncio
from src.core.config import Config
from src.core.orchestrator import MineSearchOrchestrator
from src.agents.base_agent import MineQuery

async def debug_search():
    print("=== DEBUGGING SEARCH RESULTS ===\n")
    
    # Setup
    config = Config()
    orchestrator = MineSearchOrchestrator(config)
    
    # Test agents
    test_agents = ['scraper', 'tavily', 'perplexity', 'exa']
    orchestrator.active_agents = test_agents
    
    await orchestrator.initialize()
    
    print(f"Active agents after init: {orchestrator.active_agents}\n")
    
    # Create test query
    query = MineQuery(
        mine_name="Éléonore",
        region="Quebec", 
        country="Canada",
        languages=["en", "fr"],
        required_fields=["operator", "coordinates", "commodity", "status"]
    )
    
    # Test each agent individually
    for agent_name in orchestrator.active_agents:
        if agent_name in orchestrator.agents:
            agent = orchestrator.agents[agent_name]
            print(f"\nTesting {agent_name}...")
            try:
                results = await agent.search_mine(query)
                print(f"  Results: {len(results)}")
                if results:
                    for r in results[:2]:  # Show first 2 results
                        print(f"    - {r.field_name}: {r.value[:50]}...")
                else:
                    print("  No results returned")
            except Exception as e:
                print(f"  ERROR: {e}")
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_search())