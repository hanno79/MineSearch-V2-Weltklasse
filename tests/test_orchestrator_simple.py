"""
Author: rahn
Datum: 23.06.2025
Version: 1.0
Beschreibung: Vereinfachte Tests für Orchestrator Module
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import asyncio

from src.core.orchestrator import MineSearchOrchestratorV2
from src.agents.base_agent import MineQuery, SearchResult


class TestOrchestratorSimple:
    """Vereinfachte Tests für Orchestrator"""
    
    @pytest.fixture
    def mock_config(self):
        """Mock Configuration"""
        config = MagicMock()
        config.orchestrator = MagicMock()
        config.orchestrator.max_concurrent_agents = 5
        config.orchestrator.timeout = 300
        return config
    
    @pytest.fixture
    def status_callback(self):
        """Status Callback Mock"""
        return MagicMock()
    
    @pytest.fixture
    def orchestrator(self, mock_config, status_callback):
        """Orchestrator Instanz"""
        return MineSearchOrchestratorV2(mock_config, status_callback)
    
    def test_initialization(self, orchestrator):
        """Test Orchestrator Initialisierung"""
        assert orchestrator.config is not None
        assert orchestrator.logger is not None
        assert orchestrator.status_callback is not None
    
    @pytest.mark.asyncio
    async def test_search_mine_mock(self, orchestrator):
        """Test Mine-Suche mit Mock"""
        # Mock die internen Komponenten
        orchestrator.search_executor = AsyncMock()
        orchestrator.search_executor.execute_search = AsyncMock(return_value=[
            SearchResult(
                field_name="betreiber",
                value="Test Mining Corp",
                source="test_agent",
                confidence_score=0.9,
                metadata={}
            )
        ])
        
        # Führe Suche aus
        query = MineQuery(
            mine_name="Test Mine",
            region="Test Region",
            country="Canada",
            languages=["en"],
            required_fields=["betreiber"]
        )
        
        results = await orchestrator.search_mine(
            mine_name=query.mine_name,
            region=query.region,
            country=query.country,
            required_fields=query.required_fields
        )
        
        # Verifiziere
        assert len(results) > 0
        assert results[0].field_name == "betreiber"