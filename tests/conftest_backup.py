"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Pytest Configuration und gemeinsame Fixtures
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock
from pathlib import Path
import tempfile
import shutil

from src.core.config import Config, APIConfig, DatabaseConfig
# from src.core.database import Database  # TODO: Update when Database class is refactored
from src.data.models import MineStatus


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
def mock_api_config():
    """Mock API configuration"""
    return APIConfig(
        claude_key="test_claude_key",
        openai_key="test_openai_key",
        openrouter_key="test_openrouter_key",
        tavily_key="test_tavily_key",
        perplexity_key="test_perplexity_key",
        brightdata_key="test_brightdata_key",
        scrapingbee_key="test_scrapingbee_key",
        apify_key="test_apify_key",
        firecrawl_key="test_firecrawl_key",
        google_cx="test_google_cx",
        google_key="test_google_key"
    )


@pytest.fixture
def mock_config(mock_api_config, temp_dir):
    """Mock configuration"""
    return Config(
        api_config=mock_api_config,
        database_config=DatabaseConfig(
            path=str(temp_dir / "test.db"),
            echo=False,
            pool_size=5
        ),
        agent_config={
            "timeout": 30,
            "max_retries": 3,
            "batch_size": 5
        }
    )


@pytest.fixture
async def mock_database(mock_config):
    """Mock database"""
    # Mock database until Database class is available
    from unittest.mock import AsyncMock, MagicMock
    db = AsyncMock()
    db.get_mine_by_name = AsyncMock(return_value=None)
    db.create_mine = AsyncMock(return_value=MagicMock(id=1))
    db.add_search_result = AsyncMock()
    yield db


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


@pytest.fixture
def mock_http_response():
    """Mock HTTP response"""
    response = AsyncMock()
    response.status = 200
    response.json = AsyncMock(return_value={"success": True})
    response.text = AsyncMock(return_value="Success")
    return response


@pytest.fixture
def mock_session(mock_http_response):
    """Mock aiohttp session"""
    session = AsyncMock()
    session.post.return_value.__aenter__.return_value = mock_http_response
    session.get.return_value.__aenter__.return_value = mock_http_response
    return session


@pytest.fixture
def mock_session_class(mock_session):
    """Mock aiohttp ClientSession class"""
    with pytest.mock.patch('aiohttp.ClientSession') as mock_class:
        mock_class.return_value.__aenter__.return_value = mock_session
        yield mock_class


# Test Data Fixtures
@pytest.fixture
def sample_mine_data():
    """Sample mine data for testing"""
    return {
        "name": "Test Mine",
        "region": "Test Region",
        "country": "Canada",
        "betreiber": "Test Mining Corp",
        "koordinaten": "45.5017° N, 73.5673° W",
        "rohstofftyp": "Gold, Silver",
        "produktion": "100,000 tons/year",
        "aktivitaetsstatus": MineStatus.PRODUCING,
        "sanierungskosten": "50 million USD"
    }


@pytest.fixture
def sample_html_content():
    """Sample HTML content for scraper tests"""
    return """
    <html>
    <body>
        <h1>Test Mine Information</h1>
        <table>
            <tr>
                <td>Operator:</td>
                <td>Test Mining Corp</td>
            </tr>
            <tr>
                <td>Location:</td>
                <td>45.5017° N, 73.5673° W</td>
            </tr>
            <tr>
                <td>Production:</td>
                <td>100,000 tons/year</td>
            </tr>
        </table>
    </body>
    </html>
    """


# Markers for test categorization
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.slow = pytest.mark.slow
pytest.mark.asyncio = pytest.mark.asyncio