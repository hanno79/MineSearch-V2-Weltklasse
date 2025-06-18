#!/usr/bin/env python
"""
Test script for MineSearch system
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.config import Config
from src.core.orchestrator import MineSearchOrchestrator
from src.agents.base_agent import MineQuery


async def test_search():
    """Test basic search functionality"""
    print("=== MineSearch System Test ===\n")
    
    # Create config
    config = Config()
    print("✓ Configuration loaded")
    
    # Create orchestrator
    orchestrator = MineSearchOrchestrator(config)
    print("✓ Orchestrator created")
    
    # Initialize
    await orchestrator.initialize()
    print(f"✓ Initialized with {len(orchestrator.active_agents)} active agents: {orchestrator.active_agents}")
    
    # Create test query
    query = MineQuery(
        mine_name="Test Mine",
        region="Quebec",
        country="Canada",
        languages=["en", "fr"],
        required_fields=["betreiber", "koordinaten", "rohstofftyp"]
    )
    print(f"\n✓ Created query for: {query.mine_name}")
    
    # Run search with scraper agent only (doesn't need API keys)
    orchestrator.active_agents = ['scraper'] if 'scraper' in orchestrator.active_agents else []
    
    if orchestrator.active_agents:
        print(f"✓ Running search with agents: {orchestrator.active_agents}")
        results = await orchestrator.search_mine(query)
        
        print(f"\n✓ Search completed! Found {len(results)} results")
        
        # Display results
        if results:
            print("\nSample results:")
            for i, result in enumerate(results[:3]):
                print(f"\n{i+1}. {result.field_name}: {result.value}")
                print(f"   Source: {result.source}")
                print(f"   Confidence: {result.confidence_score}")
    else:
        print("\n⚠ No agents available for testing (all require API keys)")
    
    # Cleanup
    await orchestrator.cleanup()
    print("\n✓ Cleanup completed")
    
    # Show statistics
    stats = orchestrator.get_agent_statistics()
    print("\nAgent Statistics:")
    for agent, stat in stats.items():
        print(f"- {agent}: {stat['status']}")


if __name__ == "__main__":
    print("Starting MineSearch system test...\n")
    asyncio.run(test_search())
    print("\n✓ Test completed successfully!")