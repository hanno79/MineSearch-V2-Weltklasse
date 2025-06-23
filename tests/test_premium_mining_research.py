"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Tests für Premium Mining Research Module
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime

from src.agents.premium_mining_research import (
    PremiumMiningResearch, ResearchPhase, ResearchMetadata,
    QualityIndicators, ResearchPhaseManager, QueryOptimizer
)
from src.agents.base_agent import MineQuery, SearchResult


class TestPremiumMiningResearch:
    """Tests für PremiumMiningResearch Hauptklasse"""
    
    @pytest.fixture
    def mock_agents(self):
        """Mock Agenten für Tests"""
        return {
            "tavily": AsyncMock(),
            "perplexity": AsyncMock(),
            "claude": AsyncMock(),
            "scraper": AsyncMock(),
            "brightdata": AsyncMock()
        }
    
    @pytest.fixture
    def premium_research(self, mock_config, mock_agents):
        """PremiumMiningResearch Instanz"""
        return PremiumMiningResearch("premium", mock_config, mock_agents)
    
    def test_initialization(self, premium_research, mock_agents):
        """Test Initialisierung"""
        assert premium_research.name == "premium"
        assert premium_research.agents == mock_agents
        assert premium_research.phase_manager is not None
        assert premium_research.query_optimizer is not None
    
    @pytest.mark.asyncio
    async def test_search(self, premium_research, sample_mine_query):
        """Test search Methode"""
        # Mock research_mine
        premium_research.research_mine = AsyncMock(return_value={
            "mine_data": {
                "betreiber": {
                    "value": "Test Corp",
                    "source": "Test",
                    "confidence": 0.9
                }
            }
        })
        
        results = await premium_research.search(sample_mine_query)
        
        assert isinstance(results, list)
        assert len(results) > 0
        assert results[0].field_name == "betreiber"
        assert results[0].value == "Test Corp"
    
    @pytest.mark.asyncio
    async def test_research_mine_success(self, premium_research, sample_mine_query):
        """Test erfolgreiche Mine-Recherche"""
        # Mock Phase Manager Methoden
        mock_sources = [MagicMock(url="http://test.com", source_type=MagicMock(value="government"))]
        premium_research.phase_manager.execute_discovery_phase = AsyncMock(
            return_value=mock_sources
        )
        
        mock_keywords = {"en": ["test", "mine"], "fr": ["test", "mine"]}
        premium_research.phase_manager.execute_keyword_generation = AsyncMock(
            return_value=mock_keywords
        )
        
        mock_crawl_results = [MagicMock()]
        premium_research.phase_manager.execute_deep_dive = AsyncMock(
            return_value=mock_crawl_results
        )
        
        mock_search_results = [
            SearchResult(
                field_name="betreiber",
                value="Test Corp",
                source="tavily",
                confidence_score=0.9,
                metadata={}
            )
        ]
        premium_research.phase_manager.execute_intelligent_search = AsyncMock(
            return_value=mock_search_results
        )
        
        premium_research.phase_manager.execute_analysis_phase = AsyncMock(
            return_value=[]
        )
        
        premium_research.phase_manager.execute_verification_phase = AsyncMock(
            return_value=mock_search_results
        )
        
        result = await premium_research.research_mine(sample_mine_query)
        
        assert "mine_data" in result
        assert "research_metadata" in result
        assert "discovered_sources" in result
        assert "quality_indicators" in result
        
        # Prüfe Metadaten
        metadata = result["research_metadata"]
        assert "start_time" in metadata
        assert "end_time" in metadata
        assert "phases_completed" in metadata
        assert len(metadata["phases_completed"]) == 6
    
    @pytest.mark.asyncio
    async def test_research_mine_error_handling(self, premium_research, sample_mine_query):
        """Test Fehlerbehandlung"""
        # Mock Phase Manager mit Fehler
        premium_research.phase_manager.execute_discovery_phase = AsyncMock(
            side_effect=Exception("Test error")
        )
        
        result = await premium_research.research_mine(sample_mine_query)
        
        assert "error" in result
        assert result["error"] == "Test error"
        assert len(result["mine_data"]) == 0
    
    def test_aggregate_premium_results_single_value(self, premium_research):
        """Test Aggregation mit Einzelwerten"""
        results = [
            SearchResult(
                field_name="betreiber",
                value="Test Corp",
                source="tavily",
                confidence_score=0.9,
                metadata={"lang": "en"}
            )
        ]
        
        aggregated = premium_research._aggregate_premium_results(results)
        
        assert "betreiber" in aggregated
        assert aggregated["betreiber"]["value"] == "Test Corp"
        assert aggregated["betreiber"]["confidence"] == 0.9
    
    def test_aggregate_premium_results_multiple_values(self, premium_research):
        """Test Aggregation mit Mehrfachwerten"""
        results = [
            SearchResult(
                field_name="sanierungskosten",
                value="50 million USD",
                source="source1",
                confidence_score=0.8,
                metadata={}
            ),
            SearchResult(
                field_name="sanierungskosten",
                value="45 million USD",
                source="source2",
                confidence_score=0.7,
                metadata={}
            )
        ]
        
        aggregated = premium_research._aggregate_premium_results(results)
        
        assert "sanierungskosten" in aggregated
        assert isinstance(aggregated["sanierungskosten"], list)
        assert len(aggregated["sanierungskosten"]) == 2
        # Sollte nach Konfidenz sortiert sein
        assert aggregated["sanierungskosten"][0]["confidence"] == 0.8
    
    def test_calculate_quality_indicators(self, premium_research):
        """Test Qualitätsindikator-Berechnung"""
        results = {
            "betreiber": {"value": "Test", "confidence": 0.9},
            "koordinaten": {"value": "45N 73W", "confidence": 0.85},
            "produktion": [
                {"value": "100k", "confidence": 0.7},
                {"value": "120k", "confidence": 0.6}
            ]
        }
        
        indicators = premium_research._calculate_quality_indicators(results)
        
        assert isinstance(indicators, QualityIndicators)
        assert 0 <= indicators.completeness_score <= 1
        assert 0 <= indicators.source_diversity <= 1
        assert 0 <= indicators.confidence_average <= 1
        assert 0 <= indicators.overall_quality <= 1


class TestResearchPhaseManager:
    """Tests für ResearchPhaseManager"""
    
    @pytest.fixture
    def phase_manager(self, mock_agents, mock_config):
        """ResearchPhaseManager Instanz"""
        return ResearchPhaseManager(mock_agents, mock_config)
    
    def test_get_research_phases(self, phase_manager):
        """Test Research-Phasen Definition"""
        phases = phase_manager.get_research_phases()
        
        assert len(phases) == 4
        assert phases[0].name == "Discovery"
        assert phases[1].name == "Deep_Dive"
        assert phases[2].name == "Analysis"
        assert phases[3].name == "Verification"
        
        for phase in phases:
            assert isinstance(phase, ResearchPhase)
            assert phase.max_duration > 0
            assert len(phase.required_agents) > 0
    
    @pytest.mark.asyncio
    async def test_execute_discovery_phase(self, phase_manager, sample_mine_query):
        """Test Discovery-Phase"""
        # Mock source discovery
        mock_sources = [MagicMock(url="http://test.com")]
        phase_manager.source_discovery.discover_sources_for_country = AsyncMock(
            return_value=mock_sources
        )
        
        sources = await phase_manager.execute_discovery_phase(sample_mine_query)
        
        assert sources == mock_sources
        
        # Test Cache
        cached_sources = await phase_manager.execute_discovery_phase(sample_mine_query)
        assert cached_sources == mock_sources
        # Sollte nur einmal aufgerufen werden (wegen Cache)
        phase_manager.source_discovery.discover_sources_for_country.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_keyword_generation(self, phase_manager, sample_mine_query):
        """Test Keyword-Generierung"""
        mock_sources = [
            MagicMock(
                url="http://gov.ca",
                source_type=MagicMock(name="GOVERNMENT")
            )
        ]
        
        phase_manager.keyword_generator.generate_keywords_for_search = AsyncMock(
            return_value={"en": ["test", "mine"]}
        )
        
        keywords = await phase_manager.execute_keyword_generation(sample_mine_query, mock_sources)
        
        assert isinstance(keywords, dict)
        assert "en" in keywords
        assert "official_sources" in keywords  # Sollte gov.ca Domain hinzufügen
    
    @pytest.mark.asyncio
    async def test_execute_intelligent_search(self, phase_manager, sample_mine_query):
        """Test intelligente Suche"""
        mock_keywords = {"en": ["test"]}
        mock_sources = []
        
        # Mock query optimizer
        mock_query_optimizer = MagicMock()
        mock_search_queries = [MagicMock(language="en", target_field="betreiber")]
        mock_query_optimizer.build_intelligent_queries.return_value = mock_search_queries
        mock_query_optimizer.assign_queries_to_agents.return_value = {
            "tavily": mock_search_queries
        }
        
        # Mock agent search
        phase_manager.agents["tavily"].search = AsyncMock(return_value=[
            SearchResult(
                field_name="betreiber",
                value="Test Corp",
                source="tavily",
                confidence_score=0.9,
                metadata={}
            )
        ])
        
        results = await phase_manager.execute_intelligent_search(
            sample_mine_query, mock_keywords, mock_sources, mock_query_optimizer
        )
        
        assert len(results) > 0
        assert results[0].field_name == "betreiber"


class TestQueryOptimizer:
    """Tests für QueryOptimizer"""
    
    @pytest.fixture
    def query_optimizer(self, mock_agents):
        """QueryOptimizer Instanz"""
        return QueryOptimizer(mock_agents)
    
    def test_analyze_agent_capabilities(self, query_optimizer):
        """Test Agent-Fähigkeiten-Analyse"""
        capabilities = query_optimizer.agent_capabilities
        
        assert isinstance(capabilities, dict)
        for agent in ["tavily", "perplexity", "claude"]:
            if agent in capabilities:
                assert "speed" in capabilities[agent]
                assert "depth" in capabilities[agent]
                assert "languages" in capabilities[agent]
                assert "rate_limit" in capabilities[agent]
    
    def test_build_intelligent_queries(self, query_optimizer, sample_mine_query):
        """Test intelligente Query-Erstellung"""
        keywords = {"en": ["test", "mine"], "fr": ["test", "mine"]}
        sources = []
        
        queries = query_optimizer.build_intelligent_queries(
            sample_mine_query, keywords, sources
        )
        
        assert isinstance(queries, list)
        assert len(queries) > 0
        
        for query in queries:
            assert hasattr(query, "query_text")
            assert hasattr(query, "target_field")
            assert hasattr(query, "priority")
            assert hasattr(query, "language")
            assert sample_mine_query.mine_name in query.query_text
    
    def test_assign_queries_to_agents(self, query_optimizer):
        """Test Query-Zuweisung an Agenten"""
        from src.agents.premium_mining_research.models import SearchQuery
        
        queries = [
            SearchQuery(
                query_text="test query",
                target_field="betreiber",
                priority="high",
                language="en",
                agent_preferences=["tavily", "perplexity"]
            )
        ]
        
        assignments = query_optimizer.assign_queries_to_agents(queries)
        
        assert isinstance(assignments, dict)
        assert len(assignments) > 0
        assert any(len(queries) > 0 for queries in assignments.values())
    
    def test_optimize_for_parallel_execution(self, query_optimizer):
        """Test Parallel-Ausführungs-Optimierung"""
        from src.agents.premium_mining_research.models import SearchQuery
        
        queries = [
            SearchQuery(
                query_text=f"query {i}",
                target_field="field",
                priority="medium",
                language="en",
                agent_preferences=["tavily"]
            )
            for i in range(25)
        ]
        
        batches = query_optimizer.optimize_for_parallel_execution(queries, max_parallel=10)
        
        assert isinstance(batches, list)
        assert all(len(batch) <= 10 for batch in batches)
        # Alle Queries sollten in Batches sein
        total_queries = sum(len(batch) for batch in batches)
        assert total_queries == len(queries)


class TestModels:
    """Tests für Datenmodelle"""
    
    def test_research_metadata(self):
        """Test ResearchMetadata"""
        metadata = ResearchMetadata(start_time=datetime.now())
        
        assert metadata.sources_discovered == 0
        assert metadata.documents_analyzed == 0
        assert metadata.keywords_used == 0
        assert isinstance(metadata.phases_completed, list)
        assert isinstance(metadata.errors, list)
    
    def test_quality_indicators(self):
        """Test QualityIndicators"""
        indicators = QualityIndicators(
            completeness_score=0.8,
            source_diversity=0.7,
            confidence_average=0.85,
            verification_ratio=0.9,
            language_coverage=0.6
        )
        
        overall = indicators.overall_quality
        assert 0 <= overall <= 1
        # Gewichtete Summe sollte korrekt sein
        expected = (0.8 * 0.3 + 0.7 * 0.2 + 0.85 * 0.2 + 0.9 * 0.2 + 0.6 * 0.1)
        assert abs(overall - expected) < 0.001


# Integration Tests
@pytest.mark.integration
class TestPremiumMiningResearchIntegration:
    """Integrationstests für Premium Mining Research"""
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_full_research_workflow(self, mock_config, sample_mine_query):
        """Test kompletter Research-Workflow"""
        # Setup mit echten Mock-Agenten
        mock_agents = {
            "tavily": AsyncMock(),
            "perplexity": AsyncMock(),
            "claude": AsyncMock(),
            "scraper": AsyncMock()
        }
        
        # Konfiguriere Mock-Antworten
        for agent in mock_agents.values():
            agent.search = AsyncMock(return_value=[
                SearchResult(
                    field_name="betreiber",
                    value="Integration Test Corp",
                    source="mock_agent",
                    confidence_score=0.85,
                    metadata={}
                )
            ])
        
        premium = PremiumMiningResearch("premium", mock_config, mock_agents)
        
        # Mock externe Abhängigkeiten
        premium.phase_manager.source_discovery.discover_sources_for_country = AsyncMock(
            return_value=[MagicMock(url="http://test.com", source_type=MagicMock(value="test"))]
        )
        
        premium.phase_manager.keyword_generator.generate_keywords_for_search = AsyncMock(
            return_value={"en": ["test", "keywords"]}
        )
        
        premium.phase_manager.web_crawler.deep_crawl = AsyncMock(
            return_value=[]
        )
        
        # Führe Research aus
        result = await premium.research_mine(sample_mine_query)
        
        # Validiere Ergebnis
        assert "mine_data" in result
        assert "research_metadata" in result
        assert not result.get("error")
        
        # Prüfe ob alle Phasen durchlaufen wurden
        metadata = result["research_metadata"]
        assert "Discovery" in metadata["phases_completed"]
        assert "Keyword_Generation" in metadata["phases_completed"]
        assert metadata["total_duration"] > 0