"""
Author: rahn
Datum: 23.06.2025
Version: 1.0
Beschreibung: Vereinfachte Pytest Configuration für Tests
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock
from pathlib import Path
import tempfile
import shutil


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir():
    """Create temporary directory for tests"""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def mock_config():
    """Mock configuration"""
    config = MagicMock()
    config.api_config = MagicMock()
    config.api_config.claude_key = "test_key"
    config.api_config.openai_key = "test_key"
    config.api_config.openrouter_key = "test_key"
    config.api_config.tavily_key = "test_key"
    config.api_config.perplexity_key = "test_key"
    return config


@pytest.fixture
def sample_mine_query():
    """Sample MineQuery for testing"""
    from src.agents.base_agent import MineQuery
    return MineQuery(
        mine_name="Test Mine",
        region="Test Region",
        country="Canada",
        languages=["en", "fr"],
        required_fields=["betreiber", "koordinaten", "produktion", "sanierungskosten"]
    )


@pytest.fixture
def sample_search_result():
    """Sample SearchResult for testing"""
    from src.agents.base_agent import SearchResult
    return SearchResult(
        field_name="betreiber",
        value="Test Mining Corp",
        source="Test Agent",
        confidence_score=0.95,
        metadata={"test": True}
    )