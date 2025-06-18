#!/usr/bin/env python3
"""Debug why agents are not connecting"""
import asyncio
from src.core.config import Config
from src.core.orchestrator import MineSearchOrchestrator
from src.agents.factory import AgentFactory

async def debug_agents():
    print("=== DEBUGGING AGENT CONNECTION ===\n")
    
    # Load config
    config = Config()
    print(f"1. Config loaded")
    print(f"   - OpenRouter Key: {'SET' if config.api.openrouter_key else 'NOT SET'}")
    print(f"   - Perplexity Key: {'SET' if config.api.perplexity_key else 'NOT SET'}")
    print(f"   - Tavily Key: {'SET' if config.api.tavily_key else 'NOT SET'}")
    
    # Check available agents
    print(f"\n2. Available agents from factory:")
    available = AgentFactory.get_available_agents(config)
    for agent, is_available in available.items():
        print(f"   - {agent}: {'✓ Available' if is_available else '✗ Not Available'}")
    
    # Test orchestrator initialization
    print(f"\n3. Testing orchestrator initialization...")
    orchestrator = MineSearchOrchestrator(config)
    
    # Set some test agents
    test_agents = ['scraper', 'tavily', 'openrouter_deepseek-chat']
    orchestrator.active_agents = test_agents
    print(f"   - Set active_agents to: {test_agents}")
    
    # Initialize
    await orchestrator.initialize()
    
    print(f"\n4. After initialization:")
    print(f"   - Orchestrator agents dict: {list(orchestrator.agents.keys())}")
    print(f"   - Orchestrator active_agents: {orchestrator.active_agents}")
    print(f"   - Number of active agents: {len(orchestrator.active_agents)}")
    
    # Test agent creation directly
    print(f"\n5. Testing direct agent creation:")
    try:
        scraper = AgentFactory.create_agent('scraper', config)
        print(f"   - Scraper agent created: {scraper is not None}")
    except Exception as e:
        print(f"   - Scraper agent ERROR: {e}")
    
    try:
        tavily = AgentFactory.create_agent('tavily', config)
        print(f"   - Tavily agent created: {tavily is not None}")
    except Exception as e:
        print(f"   - Tavily agent ERROR: {e}")
    
    try:
        openrouter = AgentFactory.create_agent('openrouter_deepseek-chat', config, model_id='deepseek/deepseek-chat')
        print(f"   - OpenRouter agent created: {openrouter is not None}")
    except Exception as e:
        print(f"   - OpenRouter agent ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(debug_agents())