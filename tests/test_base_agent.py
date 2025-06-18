import pytest
import asyncio
from datetime import datetime
from typing import List
from src.agents.base_agent import BaseAgent, MineQuery, SearchResult, AgentStatus


class MockAgent(BaseAgent):
    """Mock-Implementation für Tests"""
    
    async def initialize(self) -> bool:
        return True
    
    async def search_mine(self, query: MineQuery) -> List[SearchResult]:
        # Simuliere erfolgreiche Suche
        return [
            SearchResult(
                mine_name=query.mine_name,
                field_name="betreiber",
                value="Test Mining Corp",
                source="Mock Source",
                source_url="http://example.com",
                source_date=2024,
                confidence_score=0.95,
                agent_name=self.name,
                timestamp=datetime.now(),
                metadata={}
            )
        ]
    
    async def validate_credentials(self) -> bool:
        return True


@pytest.mark.asyncio
async def test_agent_execution():
    """Test Agent-Ausführung"""
    agent = MockAgent("test_agent", {})
    
    query = MineQuery(
        mine_name="Test Mine",
        region="Quebec",
        country="Canada",
        languages=["en", "fr"],
        required_fields=["betreiber", "standort"]
    )
    
    results = await agent.execute_search(query)
    
    assert len(results) == 1
    assert results[0].mine_name == "Test Mine"
    assert agent.stats["successful_requests"] == 1


@pytest.mark.asyncio
async def test_agent_statistics():
    """Test Statistik-Erfassung"""
    agent = MockAgent("test_agent", {})
    
    stats = agent.get_statistics()
    
    assert stats["name"] == "test_agent"
    assert stats["status"] == "ready"
    assert stats["total_requests"] == 0