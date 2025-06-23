"""
Author: rahn
Datum: 23.06.2025
Version: 1.0
Beschreibung: Tests für Orchestrator Module
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import asyncio
from datetime import datetime

from src.core.orchestrator import MineSearchOrchestratorV2
from src.agents.base_agent import MineQuery, SearchResult, AgentStatus
from src.core.cancellation import CancellationToken
from enum import Enum

class SearchMode(Enum):
    """Such-Modi für Tests"""
    FAST = "fast"
    STANDARD = "standard"
    DEEP = "deep"

class MineStatus(Enum):
    """Mine Status für Tests"""
    ACTIVE = "active"
    INACTIVE = "inactive"


class TestOrchestrator:
    """Tests für Orchestrator Hauptklasse"""
    
    @pytest.fixture
    def mock_agents(self):
        """Mock Agenten für Tests"""
        agents = {}
        for name in ["tavily", "perplexity", "claude", "scraper"]:
            agent = AsyncMock()
            agent.name = name
            agent.status = AgentStatus.ACTIVE
            agent.initialize = AsyncMock(return_value=True)
            agent.search = AsyncMock(return_value=[
                SearchResult(
                    field_name="betreiber",
                    value=f"Test Corp from {name}",
                    source=name,
                    confidence_score=0.8,
                    metadata={}
                )
            ])
            agents[name] = agent
        return agents
    
    @pytest.fixture
    async def orchestrator(self, mock_config, mock_database, mock_agents):
        """Orchestrator Instanz"""
        orchestrator = MineSearchOrchestratorV2(mock_config, self.status_callback)
        
        # Mock Agent Factory
        with patch('src.core.orchestrator.AgentFactory') as mock_factory:
            mock_factory.return_value.get_available_agents.return_value = mock_agents
            mock_factory.return_value.create_agent.side_effect = lambda name, config: mock_agents.get(name)
            
            await orchestrator.initialize()
            
        return orchestrator
    
    @pytest.mark.asyncio
    async def test_initialization(self, orchestrator):
        """Test Orchestrator Initialisierung"""
        assert orchestrator.is_initialized
        assert len(orchestrator.agents) > 0
        assert orchestrator.coordinator is not None
    
    @pytest.mark.asyncio
    async def test_search_mine_basic(self, orchestrator, sample_mine_query):
        """Test basis Mine-Suche"""
        results = await orchestrator.search_mine(
            mine_name=sample_mine_query.mine_name,
            region=sample_mine_query.region,
            country=sample_mine_query.country
        )
        
        assert "found_fields" in results
        assert "missing_fields" in results
        assert "search_metadata" in results
        assert results["search_metadata"]["total_agents_used"] > 0
    
    @pytest.mark.asyncio
    async def test_search_mine_with_mode(self, orchestrator, sample_mine_query):
        """Test Mine-Suche mit verschiedenen Modi"""
        # Fast mode
        results = await orchestrator.search_mine(
            mine_name=sample_mine_query.mine_name,
            region=sample_mine_query.region,
            country=sample_mine_query.country,
            mode=SearchMode.FAST
        )
        
        assert results["search_metadata"]["mode"] == "fast"
        
        # Deep mode
        results = await orchestrator.search_mine(
            mine_name=sample_mine_query.mine_name,
            region=sample_mine_query.region,
            country=sample_mine_query.country,
            mode=SearchMode.DEEP
        )
        
        assert results["search_metadata"]["mode"] == "deep"
    
    @pytest.mark.asyncio
    async def test_search_mine_with_cancellation(self, orchestrator, sample_mine_query):
        """Test Mine-Suche mit Abbruch"""
        # Erstelle Cancellation Token
        token = CancellationToken()
        
        # Starte Suche
        search_task = asyncio.create_task(
            orchestrator.search_mine(
                mine_name=sample_mine_query.mine_name,
                region=sample_mine_query.region,
                country=sample_mine_query.country,
                cancellation_token=token
            )
        )
        
        # Abbrechen nach kurzer Zeit
        await asyncio.sleep(0.1)
        token.cancel()
        
        # Warte auf Ergebnis
        results = await search_task
        
        assert results["search_metadata"].get("cancelled", False) is True
    
    @pytest.mark.asyncio
    async def test_search_with_languages(self, orchestrator):
        """Test Suche mit mehreren Sprachen"""
        results = await orchestrator.search_mine(
            mine_name="Test Mine",
            region="Quebec",
            country="Canada",
            languages=["en", "fr"]
        )
        
        assert "found_fields" in results
        # Sprachen sollten an Query weitergegeben werden
        for agent in orchestrator.agents.values():
            if agent.search.called:
                call_args = agent.search.call_args[0][0]
                assert call_args.languages == ["en", "fr"]
    
    @pytest.mark.asyncio
    async def test_search_with_discovered_sources(self, orchestrator, sample_mine_query):
        """Test Suche mit entdeckten Quellen"""
        # Mock source discovery
        mock_sources = [
            MagicMock(url="http://gov.ca/mines", source_type="government")
        ]
        
        with patch.object(orchestrator, '_discover_sources', return_value=mock_sources):
            results = await orchestrator.search_mine(
                mine_name=sample_mine_query.mine_name,
                region=sample_mine_query.region,
                country=sample_mine_query.country,
                discover_sources=True
            )
            
            assert "discovered_sources" in results
            assert len(results["discovered_sources"]) > 0
    
    @pytest.mark.asyncio
    async def test_get_agent_statuses(self, orchestrator):
        """Test Agent-Status Abfrage"""
        statuses = await orchestrator.get_agent_statuses()
        
        assert isinstance(statuses, dict)
        assert len(statuses) == len(orchestrator.agents)
        
        for name, status in statuses.items():
            assert "status" in status
            assert "stats" in status
            assert status["status"] == "active"
    
    @pytest.mark.asyncio
    async def test_get_search_statistics(self, orchestrator, sample_mine_query):
        """Test Such-Statistiken"""
        # Führe eine Suche durch
        await orchestrator.search_mine(
            mine_name=sample_mine_query.mine_name,
            region=sample_mine_query.region,
            country=sample_mine_query.country
        )
        
        stats = await orchestrator.get_search_statistics()
        
        assert "total_searches" in stats
        assert "total_agents_used" in stats
        assert "average_search_time" in stats
        assert "success_rate" in stats
        assert stats["total_searches"] > 0
    
    @pytest.mark.asyncio
    async def test_export_results(self, orchestrator, sample_mine_query, temp_dir):
        """Test Ergebnis-Export"""
        # Führe Suche durch
        search_results = await orchestrator.search_mine(
            mine_name=sample_mine_query.mine_name,
            region=sample_mine_query.region,
            country=sample_mine_query.country
        )
        
        # Exportiere als CSV
        csv_path = temp_dir / "test_export.csv"
        export_result = await orchestrator.export_results(
            mine_name=sample_mine_query.mine_name,
            format="csv",
            filename=str(csv_path)
        )
        
        assert export_result["success"] is True
        assert csv_path.exists()
    
    @pytest.mark.asyncio
    async def test_bulk_search(self, orchestrator):
        """Test Bulk-Suche für mehrere Minen"""
        mines = [
            {"name": "Mine 1", "region": "Region 1", "country": "Canada"},
            {"name": "Mine 2", "region": "Region 2", "country": "Australia"}
        ]
        
        results = await orchestrator.bulk_search(mines, max_concurrent=2)
        
        assert len(results) == 2
        assert all("found_fields" in r for r in results.values())
    
    @pytest.mark.asyncio
    async def test_search_with_premium_mode(self, orchestrator, sample_mine_query):
        """Test Premium-Suche"""
        # Mock premium agent
        premium_agent = AsyncMock()
        premium_agent.name = "premium"
        premium_agent.search = AsyncMock(return_value=[
            SearchResult(
                field_name="sanierungskosten",
                value="50 million USD",
                source="premium",
                confidence_score=0.95,
                metadata={"premium": True}
            )
        ])
        
        orchestrator.agents["premium"] = premium_agent
        
        results = await orchestrator.search_mine(
            mine_name=sample_mine_query.mine_name,
            region=sample_mine_query.region,
            country=sample_mine_query.country,
            mode=SearchMode.PREMIUM
        )
        
        assert results["search_metadata"]["mode"] == "premium"
        premium_agent.search.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_error_handling(self, orchestrator, sample_mine_query):
        """Test Fehlerbehandlung"""
        # Lass einen Agent fehlschlagen
        orchestrator.agents["tavily"].search.side_effect = Exception("Test error")
        
        results = await orchestrator.search_mine(
            mine_name=sample_mine_query.mine_name,
            region=sample_mine_query.region,
            country=sample_mine_query.country
        )
        
        # Sollte trotzdem Ergebnisse von anderen Agents haben
        assert "found_fields" in results
        assert results["search_metadata"]["errors"] > 0
    
    @pytest.mark.asyncio
    async def test_save_to_database(self, orchestrator, sample_mine_query, mock_database):
        """Test Speichern in Datenbank"""
        # Mock database methods
        mock_database.get_mine_by_name = AsyncMock(return_value=None)
        mock_database.create_mine = AsyncMock(return_value=MagicMock(id=1))
        mock_database.add_search_result = AsyncMock()
        
        results = await orchestrator.search_mine(
            mine_name=sample_mine_query.mine_name,
            region=sample_mine_query.region,
            country=sample_mine_query.country,
            save_to_db=True
        )
        
        assert results["search_metadata"]["saved_to_db"] is True
        mock_database.create_mine.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cleanup(self, orchestrator):
        """Test Cleanup"""
        await orchestrator.cleanup()
        
        for agent in orchestrator.agents.values():
            if hasattr(agent, 'cleanup'):
                agent.cleanup.assert_called_once()


class TestSearchMode:
    """Tests für SearchMode Enum"""
    
    def test_search_modes(self):
        """Test verfügbare Such-Modi"""
        assert SearchMode.FAST.value == "fast"
        assert SearchMode.STANDARD.value == "standard"
        assert SearchMode.DEEP.value == "deep"
        assert SearchMode.PREMIUM.value == "premium"


# Integration Tests
@pytest.mark.integration
class TestOrchestratorIntegration:
    """Integrationstests für Orchestrator"""
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_full_search_workflow(self, mock_config, mock_database):
        """Test kompletter Such-Workflow"""
        # Setup Orchestrator mit echten Mock-Agents
        orchestrator = MineSearchOrchestratorV2(mock_config, self.status_callback)
        
        # Mock agents mit realistischen Antworten
        mock_agents = {}
        
        # Tavily - schnelle Web-Suche
        tavily = AsyncMock()
        tavily.name = "tavily"
        tavily.status = AgentStatus.ACTIVE
        tavily.initialize = AsyncMock(return_value=True)
        tavily.search = AsyncMock(return_value=[
            SearchResult(
                field_name="betreiber",
                value="ABC Mining Corp",
                source="tavily",
                confidence_score=0.85,
                metadata={"url": "http://example.com"}
            ),
            SearchResult(
                field_name="koordinaten",
                value="45.5° N, 73.6° W",
                source="tavily",
                confidence_score=0.9,
                metadata={"url": "http://example.com"}
            )
        ])
        mock_agents["tavily"] = tavily
        
        # Claude - Deep Analysis
        claude = AsyncMock()
        claude.name = "claude"
        claude.status = AgentStatus.ACTIVE
        claude.initialize = AsyncMock(return_value=True)
        claude.search = AsyncMock(return_value=[
            SearchResult(
                field_name="sanierungskosten",
                value="75 million CAD",
                source="claude",
                confidence_score=0.92,
                metadata={"analysis": "deep"}
            )
        ])
        mock_agents["claude"] = claude
        
        # Scraper - Direct extraction
        scraper = AsyncMock()
        scraper.name = "scraper"
        scraper.status = AgentStatus.ACTIVE
        scraper.initialize = AsyncMock(return_value=True)
        scraper.search = AsyncMock(return_value=[
            SearchResult(
                field_name="produktion",
                value="250,000 tons/year",
                source="scraper",
                confidence_score=0.88,
                metadata={"method": "table_extraction"}
            )
        ])
        mock_agents["scraper"] = scraper
        
        # Mock Factory
        with patch('src.core.orchestrator.AgentFactory') as mock_factory:
            mock_factory.return_value.get_available_agents.return_value = mock_agents
            mock_factory.return_value.create_agent.side_effect = lambda name, config: mock_agents.get(name)
            
            await orchestrator.initialize()
        
        # Führe Suche durch
        query = MineQuery(
            mine_name="Integration Test Mine",
            region="Ontario",
            country="Canada",
            languages=["en", "fr"],
            required_fields=["betreiber", "koordinaten", "produktion", "sanierungskosten", "status"]
        )
        
        results = await orchestrator.search_mine(
            mine_name=query.mine_name,
            region=query.region,
            country=query.country,
            mode=SearchMode.DEEP,
            languages=query.languages,
            required_fields=query.required_fields
        )
        
        # Validiere Ergebnisse
        assert results["found_fields"]["betreiber"] == "ABC Mining Corp"
        assert results["found_fields"]["koordinaten"] == "45.5° N, 73.6° W"
        assert results["found_fields"]["produktion"] == "250,000 tons/year"
        assert results["found_fields"]["sanierungskosten"] == "75 million CAD"
        
        assert "status" in results["missing_fields"]
        
        metadata = results["search_metadata"]
        assert metadata["total_agents_used"] == 3
        assert metadata["total_results"] == 4
        assert metadata["mode"] == "deep"
        
        # Cleanup
        await orchestrator.cleanup()
    
    @pytest.mark.asyncio
    async def test_concurrent_searches(self, mock_config, mock_database):
        """Test gleichzeitige Suchen"""
        orchestrator = MineSearchOrchestratorV2(mock_config, self.status_callback)
        
        # Simple mock agents
        mock_agent = AsyncMock()
        mock_agent.name = "test"
        mock_agent.status = AgentStatus.ACTIVE
        mock_agent.initialize = AsyncMock(return_value=True)
        mock_agent.search = AsyncMock(return_value=[])
        
        with patch('src.core.orchestrator.AgentFactory') as mock_factory:
            mock_factory.return_value.get_available_agents.return_value = {"test": mock_agent}
            mock_factory.return_value.create_agent.return_value = mock_agent
            
            await orchestrator.initialize()
        
        # Starte mehrere Suchen gleichzeitig
        searches = []
        for i in range(5):
            search = orchestrator.search_mine(
                mine_name=f"Mine {i}",
                region="Region",
                country="Country"
            )
            searches.append(search)
        
        # Warte auf alle
        results = await asyncio.gather(*searches)
        
        assert len(results) == 5
        assert all("found_fields" in r for r in results)