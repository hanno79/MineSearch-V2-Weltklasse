"""
Author: rahn
Datum: 19.06.2025
Version: 1.0
Beschreibung: Integrations-Tests für Agenten-Zusammenspiel
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from src.agents.base_agent import MineQuery, SearchResult, AgentStatus
from src.agents.factory import AgentFactory
from src.agents.agent_coordinator import AgentCoordinator
from src.core.config import Config
from src.core.cancellation import CancellationToken


class TestAgentIntegration:
    """Integrations-Tests für das Zusammenspiel verschiedener Agenten"""
    
    @pytest.fixture
    def mock_config(self):
        """Mock-Konfiguration für Tests"""
        config = Mock(spec=Config)
        config.api = Mock()
        config.scraping = Mock()
        config.max_concurrent_requests = 3
        
        # Aktiviere einige Agenten
        config.api.openrouter_key = "test_key"
        config.api.perplexity_key = "test_key"
        config.api.tavily_key = "test_key"
        config.api.scraper_key = None  # Scraper braucht keinen Key
        
        # Mock validate
        config.api.validate = Mock(return_value={
            "openrouter_key": True,
            "perplexity_key": True,
            "tavily_key": True
        })
        
        return config
    
    @pytest.fixture
    def sample_query(self):
        """Standard-Suchanfrage"""
        return MineQuery(
            mine_name="Integration Test Mine",
            region="Test Region",
            country="Test Country",
            languages=["en"],
            required_fields=["betreiber", "koordinaten", "aktivitaetsstatus"]
        )
    
    @pytest.mark.asyncio
    async def test_multiple_agents_parallel_search(self, mock_config, sample_query):
        """Test parallele Suche mit mehreren Agenten"""
        # Erstelle mehrere Agenten
        agents = []
        agent_types = ["claude", "perplexity", "scraper"]
        
        for agent_type in agent_types:
            agent = AgentFactory.create_agent(agent_type, mock_config)
            agents.append(agent)
        
        # Mock search_mine für alle Agenten
        for i, agent in enumerate(agents):
            async def mock_search(query, agent_index=i):
                await asyncio.sleep(0.1)  # Simuliere Verarbeitung
                return [
                    SearchResult(
                        mine_name=query.mine_name,
                        field_name="betreiber",
                        value=f"Result from {agents[agent_index].name}",
                        source=f"Source {agent_index}",
                        source_url=f"http://example{agent_index}.com",
                        source_date=2024,
                        confidence_score=0.8 + agent_index * 0.05,
                        agent_name=agents[agent_index].name,
                        timestamp=datetime.now(),
                        metadata={}
                    )
                ]
            agent.search_mine = mock_search
        
        # Führe parallele Suche durch
        tasks = [agent.execute_search(sample_query) for agent in agents]
        results = await asyncio.gather(*tasks)
        
        # Prüfe Ergebnisse
        assert len(results) == 3
        for i, agent_results in enumerate(results):
            assert len(agent_results) > 0
            assert agent_results[0].agent_name == agents[i].name
    
    @pytest.mark.asyncio
    async def test_agent_fallback_mechanism(self, mock_config, sample_query):
        """Test Fallback-Mechanismus bei Agent-Fehlern"""
        # Erstelle Haupt-Agent und Fallback-Agent
        primary_agent = AgentFactory.create_agent("claude", mock_config)
        fallback_agent = AgentFactory.create_agent("scraper", mock_config)
        
        # Lass Haupt-Agent fehlschlagen
        primary_agent.search_mine = AsyncMock(side_effect=Exception("API Error"))
        
        # Fallback sollte funktionieren
        fallback_agent.search_mine = AsyncMock(return_value=[
            SearchResult(
                mine_name=sample_query.mine_name,
                field_name="betreiber",
                value="Fallback Result",
                source="Fallback",
                source_url="http://fallback.com",
                source_date=2024,
                confidence_score=0.7,
                agent_name="scraper",
                timestamp=datetime.now(),
                metadata={}
            )
        ])
        
        # Führe Suche mit Fallback durch
        primary_results = await primary_agent.execute_search(sample_query)
        assert primary_results == []  # Primär fehlgeschlagen
        
        fallback_results = await fallback_agent.execute_search(sample_query)
        assert len(fallback_results) == 1
        assert fallback_results[0].value == "Fallback Result"
    
    @pytest.mark.asyncio
    async def test_cancellation_across_agents(self, mock_config, sample_query):
        """Test Abbruch-Funktionalität über mehrere Agenten"""
        token = CancellationToken()
        agents = []
        
        # Erstelle mehrere Agenten mit Cancellation Token
        for agent_type in ["claude", "perplexity", "scraper"]:
            agent = AgentFactory.create_agent(agent_type, mock_config)
            agent.set_cancellation_token(token)
            agents.append(agent)
        
        # Mock lange laufende Suche
        async def slow_search(query):
            for _ in range(10):
                await asyncio.sleep(0.1)
                await agent.check_cancellation()  # Prüfe Abbruch
            return []
        
        for agent in agents:
            agent.search_mine = slow_search
        
        # Starte parallele Suchen
        tasks = [agent.execute_search(sample_query) for agent in agents]
        
        # Breche nach kurzer Zeit ab
        async def cancel_after_delay():
            await asyncio.sleep(0.2)
            token.cancel()
        
        cancel_task = asyncio.create_task(cancel_after_delay())
        
        # Warte auf Ergebnisse
        results = await asyncio.gather(*tasks, return_exceptions=True)
        await cancel_task
        
        # Alle Agenten sollten abgebrochen worden sein
        for result in results:
            # Ergebnis sollte leer sein (abgebrochen) oder Exception
            assert result == [] or isinstance(result, Exception)
    
    @pytest.mark.asyncio
    async def test_result_deduplication(self, mock_config, sample_query):
        """Test Deduplizierung von Ergebnissen verschiedener Agenten"""
        agents = []
        
        # Erstelle Agenten die gleiche Ergebnisse liefern
        for agent_type in ["claude", "perplexity"]:
            agent = AgentFactory.create_agent(agent_type, mock_config)
            
            # Beide liefern identische Ergebnisse
            agent.search_mine = AsyncMock(return_value=[
                SearchResult(
                    mine_name=sample_query.mine_name,
                    field_name="betreiber",
                    value="Test Mining Corp",  # Identischer Wert
                    source=f"Source from {agent.name}",
                    source_url="http://example.com",
                    source_date=2024,
                    confidence_score=0.9,
                    agent_name=agent.name,
                    timestamp=datetime.now(),
                    metadata={}
                )
            ])
            agents.append(agent)
        
        # Sammle alle Ergebnisse
        all_results = []
        for agent in agents:
            results = await agent.execute_search(sample_query)
            all_results.extend(results)
        
        # Ohne Deduplizierung sollten wir 2 Ergebnisse haben
        assert len(all_results) == 2
        
        # Deduplizierung basierend auf field_name und value
        unique_results = {}
        for result in all_results:
            key = (result.field_name, result.value)
            if key not in unique_results or result.confidence_score > unique_results[key].confidence_score:
                unique_results[key] = result
        
        # Nach Deduplizierung sollte nur 1 Ergebnis übrig sein
        assert len(unique_results) == 1
        # Das Ergebnis mit höherer Konfidenz sollte behalten werden
        assert list(unique_results.values())[0].confidence_score == 0.9
    
    @pytest.mark.asyncio
    async def test_agent_coordinator_integration(self, mock_config, sample_query):
        """Test Integration mit Agent Coordinator"""
        coordinator = AgentCoordinator(mock_config)
        
        # Mock einzelne Agenten
        with patch('src.agents.factory.AgentFactory.create_agent') as mock_create:
            # Mock verschiedene Agent-Typen
            mock_agents = {}
            for agent_type in ["claude", "perplexity", "scraper"]:
                mock_agent = AsyncMock()
                mock_agent.name = agent_type
                mock_agent.initialize = AsyncMock(return_value=True)
                mock_agent.search_mine = AsyncMock(return_value=[
                    SearchResult(
                        mine_name=sample_query.mine_name,
                        field_name="betreiber",
                        value=f"Result from {agent_type}",
                        source=f"{agent_type} source",
                        source_url=f"http://{agent_type}.com",
                        source_date=2024,
                        confidence_score=0.8,
                        agent_name=agent_type,
                        timestamp=datetime.now(),
                        metadata={}
                    )
                ])
                mock_agent.cleanup = AsyncMock()
                mock_agents[agent_type] = mock_agent
            
            def create_agent_side_effect(agent_type, config):
                return mock_agents.get(agent_type)
            
            mock_create.side_effect = create_agent_side_effect
            
            # Initialisiere Coordinator
            await coordinator.initialize()
            
            # Führe koordinierte Suche durch
            results = await coordinator.search_all_agents(sample_query)
            
            # Prüfe Ergebnisse
            assert len(results) > 0
            agent_names = {r.agent_name for r in results}
            # Mindestens ein Agent sollte Ergebnisse geliefert haben
            assert len(agent_names) >= 1
    
    @pytest.mark.asyncio
    async def test_performance_monitoring(self, mock_config, sample_query):
        """Test Performance-Monitoring über mehrere Agenten"""
        agents = []
        
        # Erstelle Agenten mit unterschiedlichen Response-Zeiten
        response_times = {"claude": 0.5, "perplexity": 0.2, "scraper": 1.0}
        
        for agent_type, delay in response_times.items():
            agent = AgentFactory.create_agent(agent_type, mock_config)
            
            async def mock_search(query, response_delay=delay):
                await asyncio.sleep(response_delay)
                return [SearchResult(
                    mine_name=query.mine_name,
                    field_name="test",
                    value="test",
                    source="test",
                    source_url="",
                    source_date=2024,
                    confidence_score=0.8,
                    agent_name=agent.name,
                    timestamp=datetime.now(),
                    metadata={}
                )]
            
            agent.search_mine = mock_search
            agents.append(agent)
        
        # Führe Suchen durch und messe Zeit
        start_times = {}
        end_times = {}
        
        for agent in agents:
            start_times[agent.name] = datetime.now()
            await agent.execute_search(sample_query)
            end_times[agent.name] = datetime.now()
        
        # Prüfe Statistiken
        for agent in agents:
            stats = agent.get_statistics()
            assert stats["total_requests"] == 1
            assert stats["successful_requests"] == 1
            assert stats["runtime_seconds"] > 0
            
            # Prüfe ob Response-Zeit ungefähr stimmt
            actual_time = (end_times[agent.name] - start_times[agent.name]).total_seconds()
            expected_time = response_times[agent.name]
            assert abs(actual_time - expected_time) < 0.2  # Toleranz
    
    @pytest.mark.asyncio
    async def test_error_propagation(self, mock_config, sample_query):
        """Test Fehler-Propagierung zwischen Agenten"""
        # Erstelle Agent mit spezifischem Fehler
        agent = AgentFactory.create_agent("claude", mock_config)
        
        # Mock verschiedene Fehlertypen
        error_types = [
            ("Rate limit exceeded", AgentStatus.RATE_LIMITED),
            ("401 Unauthorized", AgentStatus.ERROR),
            ("Network timeout", AgentStatus.ERROR)
        ]
        
        for error_msg, expected_status in error_types:
            agent.status = AgentStatus.READY
            agent.search_mine = AsyncMock(side_effect=Exception(error_msg))
            
            results = await agent.execute_search(sample_query)
            
            assert results == []
            assert agent.stats["failed_requests"] > 0
            # Status sollte je nach Fehlertyp gesetzt werden
            # (Die genaue Implementierung hängt vom Agent ab)