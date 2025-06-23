"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Tests für Search Strategies Module
"""

import pytest
from unittest.mock import MagicMock, AsyncMock

from src.agents.search_strategies_module import (
    SearchStrategies, SearchStrategy, SearchScope, SearchDepth,
    StrategyBuilder, AdaptiveSearchManager, SearchProgress
)


class TestSearchStrategies:
    """Tests für SearchStrategies Hauptklasse"""
    
    @pytest.fixture
    def search_strategies(self):
        """SearchStrategies Instanz"""
        return SearchStrategies()
    
    def test_initialization(self, search_strategies):
        """Test Initialisierung"""
        assert search_strategies.builder is not None
        assert search_strategies.adaptive_manager is not None
        assert len(search_strategies.strategies) > 0
        assert search_strategies.active_strategy is None
    
    def test_select_strategy_basic(self, search_strategies, sample_mine_query):
        """Test Basis-Strategie-Auswahl"""
        available_agents = ["tavily", "perplexity", "claude"]
        
        strategy = search_strategies.select_strategy(
            mine_name=sample_mine_query.mine_name,
            country=sample_mine_query.country,
            region=sample_mine_query.region,
            required_fields=sample_mine_query.required_fields,
            available_agents=available_agents
        )
        
        assert isinstance(strategy, SearchStrategy)
        assert strategy.name is not None
        assert search_strategies.active_strategy == strategy
    
    def test_select_strategy_with_time_constraint(self, search_strategies, sample_mine_query):
        """Test Strategie-Auswahl mit Zeitbeschränkung"""
        available_agents = ["tavily", "perplexity"]
        time_constraint = 120  # 2 Minuten
        
        strategy = search_strategies.select_strategy(
            mine_name=sample_mine_query.mine_name,
            country=sample_mine_query.country,
            region=sample_mine_query.region,
            required_fields=sample_mine_query.required_fields,
            available_agents=available_agents,
            time_constraint=time_constraint
        )
        
        assert strategy.time_budget <= time_constraint
    
    def test_get_site_recommendations(self, search_strategies):
        """Test Website-Empfehlungen"""
        # Test verschiedene Feldtypen
        test_cases = [
            ("betreiber", ["sedar.com", "sec.gov"]),
            ("koordinaten", ["nrcan.gc.ca", "usgs.gov"]),
            ("sanierungskosten", ["epa.gov", "environment.gov.au"]),
            ("unknown_field", ["mining.com"])  # Default
        ]
        
        for field, expected_domains in test_cases:
            recommendations = search_strategies.get_site_recommendations(field)
            assert isinstance(recommendations, list)
            assert len(recommendations) > 0
            assert any(domain in recommendations for domain in expected_domains)
    
    def test_get_keyword_strategy_params(self, search_strategies):
        """Test Keyword-Strategie-Parameter"""
        strategies = ["broad", "balanced", "focused", "comprehensive"]
        
        for strategy_type in strategies:
            params = search_strategies.get_keyword_strategy_params(strategy_type)
            assert isinstance(params, dict)
            assert "max_keywords" in params
            assert "include_variations" in params
            assert "include_translations" in params
            assert "specificity" in params
    
    @pytest.mark.asyncio
    async def test_adapt_strategy(self, search_strategies):
        """Test Strategie-Anpassung"""
        # Setze aktive Strategie
        search_strategies.active_strategy = SearchStrategy(
            name="Test Strategy",
            scope=SearchScope.GLOBAL,
            depth=SearchDepth.STANDARD,
            time_budget=300,
            agent_preferences=["tavily"],
            keyword_strategy="balanced",
            parallel_searches=10,
            retry_strategy={"max_retries": 2, "backoff": 2}
        )
        
        # Mock Ergebnisse
        mock_results = [MagicMock(confidence_score=0.2) for _ in range(5)]
        
        adapted = await search_strategies.adapt_strategy(mock_results, 60)
        
        # Bei schlechten Ergebnissen sollte intensiviert werden
        if adapted:
            assert adapted.depth in [SearchDepth.DEEP, SearchDepth.EXHAUSTIVE]


class TestStrategyBuilder:
    """Tests für StrategyBuilder"""
    
    @pytest.fixture
    def builder(self):
        """StrategyBuilder Instanz"""
        agents = {"tavily": MagicMock(), "claude": MagicMock()}
        return StrategyBuilder(agents)
    
    def test_build_default_strategies(self, builder):
        """Test Standard-Strategien"""
        strategies = builder.build_default_strategies()
        
        assert isinstance(strategies, dict)
        assert "quick_scan" in strategies
        assert "standard_search" in strategies
        assert "deep_research" in strategies
        assert "government_focus" in strategies
        
        # Prüfe Strategie-Eigenschaften
        quick_scan = strategies["quick_scan"]
        assert quick_scan.time_budget == 60
        assert quick_scan.depth == SearchDepth.SHALLOW
    
    def test_analyze_requirements(self, builder, sample_mine_query):
        """Test Anforderungsanalyse"""
        analysis = builder.analyze_requirements(
            mine_name=sample_mine_query.mine_name,
            country=sample_mine_query.country,
            region=sample_mine_query.region,
            required_fields=sample_mine_query.required_fields
        )
        
        assert "complexity" in analysis
        assert "geographic_scope" in analysis
        assert "field_types" in analysis
        assert "language_needs" in analysis
        assert "source_preferences" in analysis
    
    def test_score_strategy(self, builder):
        """Test Strategie-Bewertung"""
        strategy = SearchStrategy(
            name="Test",
            scope=SearchScope.GLOBAL,
            depth=SearchDepth.STANDARD,
            time_budget=300,
            agent_preferences=["tavily"],
            keyword_strategy="balanced",
            parallel_searches=10,
            retry_strategy={"max_retries": 2, "backoff": 2}
        )
        
        analysis = {
            "complexity": "medium",
            "source_preferences": ["global"]
        }
        
        available_agents = ["tavily", "claude"]
        
        score = builder.score_strategy(strategy, analysis, available_agents)
        
        assert isinstance(score, float)
        assert 0 <= score <= 1
    
    def test_create_specialized_queries(self, builder, sample_mine_query):
        """Test spezialisierte Query-Erstellung"""
        queries = builder.create_specialized_queries(
            mine_name=sample_mine_query.mine_name,
            fields=sample_mine_query.required_fields,
            region=sample_mine_query.region,
            country=sample_mine_query.country,
            languages=sample_mine_query.languages
        )
        
        assert isinstance(queries, list)
        assert len(queries) > 0
        
        for query in queries:
            assert "query" in query
            assert "field" in query
            assert "priority" in query
            assert sample_mine_query.mine_name in query["query"]


class TestAdaptiveSearchManager:
    """Tests für AdaptiveSearchManager"""
    
    @pytest.fixture
    def manager(self):
        """AdaptiveSearchManager Instanz"""
        return AdaptiveSearchManager()
    
    def test_assess_result_quality(self, manager):
        """Test Ergebnis-Qualitätsbewertung"""
        # Test mit leeren Ergebnissen
        quality = manager.assess_result_quality([])
        assert quality == 0.0
        
        # Test mit guten Ergebnissen
        mock_results = [
            MagicMock(confidence_score=0.9, source="source1"),
            MagicMock(confidence_score=0.85, source="source2"),
            MagicMock(confidence_score=0.8, source="source3")
        ]
        
        quality = manager.assess_result_quality(mock_results)
        assert quality > 0.5
    
    def test_calculate_progress(self, manager):
        """Test Fortschrittsberechnung"""
        strategy = SearchStrategy(
            name="Test",
            scope=SearchScope.GLOBAL,
            depth=SearchDepth.STANDARD,
            time_budget=300,
            agent_preferences=["tavily", "perplexity", "claude"],
            keyword_strategy="balanced",
            parallel_searches=10,
            retry_strategy={"max_retries": 2, "backoff": 2}
        )
        
        progress = manager.calculate_progress(strategy, 10, 150)
        
        assert isinstance(progress, SearchProgress)
        assert progress.total_agents == 3
        assert progress.completed_agents > 0
        assert progress.total_results == 10
        assert progress.elapsed_time == 150
        assert progress.current_phase in ["early_search", "main_search", "deep_search"]
    
    def test_suggest_next_action(self, manager):
        """Test Aktionsvorschläge"""
        progress = SearchProgress(
            total_agents=5,
            completed_agents=2,
            total_results=5,
            elapsed_time=60,
            estimated_time_remaining=120,
            current_phase="early_search"
        )
        
        # Test mit schlechter Qualität
        action = manager.suggest_next_action(progress, 0.2)
        assert action in ["expand_search_scope", "try_alternative_sources"]
        
        # Test mit guter Qualität
        action = manager.suggest_next_action(progress, 0.8)
        assert action in ["continue_current_strategy", "refine_results", "finalize_search"]
    
    def test_optimize_parallel_searches(self, manager):
        """Test Parallelsuche-Optimierung"""
        # Test mit vielen Ressourcen
        optimized = manager.optimize_parallel_searches(10, 25)
        assert optimized == 20
        
        # Test mit wenigen Ressourcen
        optimized = manager.optimize_parallel_searches(10, 5)
        assert optimized < 10
    
    def test_get_retry_recommendations(self, manager):
        """Test Wiederholungsempfehlungen"""
        # Test ohne Fehler
        recommendations = manager.get_retry_recommendations([])
        assert recommendations["retry"] is False
        
        # Test mit Timeout-Fehlern
        failed_attempts = [
            {"error_type": "timeout"},
            {"error_type": "timeout"},
            {"error_type": "timeout"}
        ]
        
        recommendations = manager.get_retry_recommendations(failed_attempts)
        assert recommendations["retry"] is True
        assert recommendations["strategy"] == "increase_timeout"
        
        # Test mit Rate-Limit-Fehlern
        failed_attempts = [{"error_type": "rate_limit"}]
        
        recommendations = manager.get_retry_recommendations(failed_attempts)
        assert recommendations["retry"] is True
        assert recommendations["strategy"] == "exponential_backoff"


# Integration Tests
@pytest.mark.integration
class TestSearchStrategiesIntegration:
    """Integrationstests für Search Strategies"""
    
    @pytest.mark.asyncio
    async def test_full_strategy_workflow(self, sample_mine_query):
        """Test kompletter Strategie-Workflow"""
        # Setup
        search_strategies = SearchStrategies()
        available_agents = ["tavily", "perplexity", "claude", "gpt4"]
        
        # Phase 1: Strategie auswählen
        strategy = search_strategies.select_strategy(
            mine_name=sample_mine_query.mine_name,
            country=sample_mine_query.country,
            region=sample_mine_query.region,
            required_fields=sample_mine_query.required_fields,
            available_agents=available_agents
        )
        
        assert strategy is not None
        
        # Phase 2: Keywords und Queries generieren
        keyword_params = search_strategies.get_keyword_strategy_params(
            strategy.keyword_strategy
        )
        assert keyword_params["max_keywords"] > 0
        
        # Phase 3: Spezialisierte Queries erstellen
        queries = search_strategies.get_specialized_queries(
            mine_name=sample_mine_query.mine_name,
            fields=sample_mine_query.required_fields,
            region=sample_mine_query.region,
            country=sample_mine_query.country,
            languages=sample_mine_query.languages
        )
        
        assert len(queries) > 0
        
        # Phase 4: Fortschritt verfolgen
        progress = search_strategies.get_progress(10, 60)
        assert progress.total_results == 10
        
        # Phase 5: Performance loggen
        search_strategies.log_strategy_performance(
            strategy=strategy,
            results_count=10,
            time_taken=60,
            quality_score=0.8
        )
        
        assert len(search_strategies.search_history) == 1