"""
Author: rahn
Datum: 18.06.2025
Version: 1.0
Beschreibung: Test-Skript für die neuen Research-API Integrationen
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.base_agent import MineQuery
from src.agents.deepseek_research_agent import DeepSeekResearchAgent
from src.agents.perplexity_deep_agent import PerplexityDeepAgent
from src.agents.research_orchestrator import ResearchOrchestrator
from src.agents.research_integration import (
    ResearchAgentFactory,
    ResearchModeSelector,
    integrate_research_orchestrator
)
from src.core.logger import setup_logging

# Load environment variables
load_dotenv()

# Setup logging
setup_logging()


async def test_deepseek_research():
    """Test DeepSeek Research Agent"""
    print("\n" + "="*60)
    print("Testing DeepSeek Research Agent")
    print("="*60)
    
    # Check for API key
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("❌ No DEEPSEEK_API_KEY found in .env")
        print("💡 DeepSeek is available for free via OpenRouter!")
        return
    
    try:
        # Create agent
        agent = DeepSeekResearchAgent(api_key=api_key, model="chat")
        
        # Test validation
        is_valid = await agent.validate()
        print(f"✓ API Key validation: {'Success' if is_valid else 'Failed'}")
        
        if not is_valid:
            return
        
        # Test search
        query = MineQuery(
            mine_name="Malartic",
            region="Quebec",
            country="Canada",
            languages=["en", "fr"],
            required_fields=["betreiber", "koordinaten", "sanierungskosten"]
        )
        
        print(f"\nSearching for: {query.mine_name} mine")
        results = await agent.search(query)
        
        print(f"\n✓ Found {len(results)} results:")
        for result in results[:5]:  # Show first 5
            print(f"  - {result.field_name}: {result.value} (confidence: {result.confidence_score:.2f})")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")


async def test_perplexity_deep():
    """Test Perplexity Deep Research"""
    print("\n" + "="*60)
    print("Testing Perplexity Deep Research Agent")
    print("="*60)
    
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        print("❌ No PERPLEXITY_API_KEY found in .env")
        return
    
    try:
        # Test both modes
        for use_deep in [False, True]:
            mode = "Deep Research" if use_deep else "Standard"
            print(f"\nTesting {mode} mode...")
            
            agent = PerplexityDeepAgent(api_key=api_key, use_deep_research=use_deep)
            
            # Test validation
            is_valid = await agent.validate()
            if not is_valid:
                print(f"❌ Validation failed for {mode} mode")
                continue
            
            # Simple test query
            query = MineQuery(
                mine_name="Olympic Dam",
                region="South Australia",
                country="Australia",
                languages=["en"],
                required_fields=["betreiber", "rohstofftyp", "jahresproduktion"]
            )
            
            results = await agent.search(query)
            print(f"✓ {mode} mode found {len(results)} results")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")


async def test_research_orchestrator():
    """Test Research Orchestrator"""
    print("\n" + "="*60)
    print("Testing Research Orchestrator")
    print("="*60)
    
    # Create mock agents for testing
    mock_agents = {}
    
    # Add real agents if available
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if openrouter_key:
        from src.agents.openrouter_agent import OpenRouterAgent
        
        # Add DeepSeek via OpenRouter
        deepseek_agent = OpenRouterAgent(
            api_key=openrouter_key,
            model_id="deepseek/deepseek-chat"
        )
        mock_agents["deepseek_research"] = deepseek_agent
        print("✓ Added DeepSeek via OpenRouter")
    
    perplexity_key = os.getenv("PERPLEXITY_API_KEY")
    if perplexity_key:
        from src.agents.perplexity_agent import PerplexityAgent
        perplexity_agent = PerplexityAgent(
            name="perplexity",
            config={"api_config": type('obj', (object,), {'perplexity_key': perplexity_key})}
        )
        mock_agents["perplexity"] = perplexity_agent
        print("✓ Added Perplexity agent")
    
    if not mock_agents:
        print("❌ No agents available for orchestration test")
        return
    
    try:
        # Create orchestrator
        orchestrator = ResearchOrchestrator(mock_agents)
        print(f"\n✓ Orchestrator initialized with {len(orchestrator.research_agents)} agents")
        
        # Test research
        query = MineQuery(
            mine_name="Super Pit",
            region="Western Australia",
            country="Australia",
            languages=["en"],
            required_fields=["betreiber", "koordinaten", "aktivitaetsstatus", "sanierungskosten"]
        )
        
        print(f"\nOrchestrating research for: {query.mine_name}")
        result = await orchestrator.orchestrate_research(query)
        
        print(f"\n✓ Research completed:")
        print(f"  - Results found: {len(result['results'])}")
        print(f"  - Tasks completed: {result['task_summary']['completed_tasks']}")
        print(f"  - Quality metrics:")
        for metric, value in result['quality_metrics'].items():
            print(f"    - {metric}: {value}%")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")


async def test_research_integration():
    """Test complete research integration"""
    print("\n" + "="*60)
    print("Testing Research Integration")
    print("="*60)
    
    # Create base agents
    base_agents = {}
    
    # Add any available agents
    if os.getenv("OPENROUTER_API_KEY"):
        from src.agents.openrouter_agent import OpenRouterAgent
        base_agents["openrouter"] = OpenRouterAgent(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            model_id="deepseek/deepseek-chat"
        )
    
    # Enhance with research agents
    all_agents = ResearchAgentFactory.create_research_agents(base_agents)
    print(f"✓ Total agents available: {len(all_agents)}")
    
    # Test mode selection
    mode_selector = ResearchModeSelector(all_agents)
    
    test_cases = [
        {
            "mine": "Grasberg",
            "country": "Indonesia",
            "fields": ["betreiber", "koordinaten"],
            "expected_mode": "standard"
        },
        {
            "mine": "Unknown Mine",
            "country": "Mongolia",
            "fields": ["betreiber", "koordinaten", "sanierungskosten", "jahresproduktion"],
            "expected_mode": "discovery"
        },
        {
            "mine": "Complex Mine",
            "country": "Chile",
            "fields": ["betreiber", "koordinaten", "sanierungskosten", "jahresproduktion",
                      "rohstofftyp", "mitarbeiter", "flaeche", "aktivitaetsstatus",
                      "umweltauflagen", "wasserverbrauch", "energieverbrauch"],
            "expected_mode": "deep_research"
        }
    ]
    
    print("\nTesting Research Mode Selection:")
    for test in test_cases:
        mode = mode_selector.select_research_mode(
            test["mine"],
            test["country"],
            test["fields"]
        )
        print(f"  - {test['mine']} ({len(test['fields'])} fields) → {mode} mode")
        
        agents_for_mode = mode_selector.get_agents_for_mode(mode)
        print(f"    Agents: {', '.join(agents_for_mode)}")


async def main():
    """Run all tests"""
    print("\n🚀 Testing Research API Integrations\n")
    
    # Run individual tests
    await test_deepseek_research()
    await test_perplexity_deep()
    await test_research_orchestrator()
    await test_research_integration()
    
    print("\n✅ All tests completed!")
    print("\n💡 Tips:")
    print("1. DeepSeek is available for FREE via OpenRouter")
    print("2. Set DEEPSEEK_API_KEY for direct API access with advanced features")
    print("3. Perplexity Deep Research requires Pro subscription")
    print("4. Research Orchestrator works best with multiple agents")


if __name__ == "__main__":
    asyncio.run(main())