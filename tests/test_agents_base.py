"""
Author: rahn
Datum: 19.06.2025
Version: 1.0
Beschreibung: Basis-Test-Klasse für alle Agent-Tests

Dieses Modul stellt eine wiederverwendbare Test-Basis für alle
Agent-Implementierungen zur Verfügung.
"""

import pytest
import asyncio
from typing import List, Optional, Dict, Any, Type
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
import aiohttp

from src.agents.base_agent import BaseAgent, MineQuery, SearchResult, AgentStatus
from src.core.cancellation import CancellationToken, CancellationException
from src.core.config import Config


class BaseAgentTest:
    """
    Basis-Klasse für Agent-Tests
    
    Stellt gemeinsame Test-Funktionalität für alle Agent-Tests zur Verfügung.
    Jeder spezifische Agent-Test sollte von dieser Klasse erben.
    """
    
    # Muss von Unterklassen überschrieben werden
    agent_class: Type[BaseAgent] = None
    agent_name: str = None
    required_api_key: Optional[str] = None
    
    @pytest.fixture
    def mock_config(self):
        """Mock-Konfiguration für Tests"""
        config = Mock(spec=Config)
        config.api = Mock()
        config.scraping = Mock()
        config.max_concurrent_requests = 5
        
        # Standard API-Keys (können in Unterklassen überschrieben werden)
        config.api.openrouter_key = "test_openrouter_key"
        config.api.perplexity_key = "test_perplexity_key"
        config.api.tavily_key = "test_tavily_key"
        config.api.exa_key = "test_exa_key"
        config.api.apify_key = "test_apify_key"
        config.api.scrapingbee_key = "test_scrapingbee_key"
        config.api.firecrawl_key = "test_firecrawl_key"
        config.api.brightdata_key = "test_brightdata_key"
        
        return config
    
    @pytest.fixture
    def sample_query(self):
        """Standard-Suchanfrage für Tests"""
        return MineQuery(
            mine_name="Test Mine",
            region="Ontario",
            country="Canada",
            languages=["en", "fr"],
            required_fields=["betreiber", "koordinaten", "aktivitaetsstatus", "rohstofftyp"]
        )
    
    @pytest.fixture
    def mock_response(self):
        """Mock HTTP-Response"""
        response = Mock()
        response.status = 200
        response.json = AsyncMock(return_value={
            "choices": [{
                "message": {
                    "content": "Test Mining Corp operates the Test Mine at coordinates 45.123, -75.456"
                }
            }]
        })
        response.text = AsyncMock(return_value="Mock response text")
        return response
    
    def create_agent(self, config: Config) -> BaseAgent:
        """
        Erstellt Agent-Instanz für Tests
        
        Kann von Unterklassen überschrieben werden für spezielle Initialisierung
        """
        if self.agent_class is None:
            raise NotImplementedError("agent_class muss in Unterklasse definiert werden")
        
        return self.agent_class(name=self.agent_name, config={
            "api_config": config.api,
            "scraping_config": config.scraping,
            "max_concurrent": config.max_concurrent_requests
        })
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self, mock_config):
        """Test Agent-Initialisierung"""
        agent = self.create_agent(mock_config)
        
        assert agent.name == self.agent_name
        assert agent.status == AgentStatus.READY
        assert agent.stats["total_requests"] == 0
        assert agent._cancellation_token is None
    
    @pytest.mark.asyncio
    async def test_agent_validate_credentials_success(self, mock_config, mock_response):
        """Test erfolgreiche Credential-Validierung"""
        agent = self.create_agent(mock_config)
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session
            mock_session.post.return_value.__aenter__.return_value = mock_response
            mock_session.get.return_value.__aenter__.return_value = mock_response
            
            result = await agent.validate_credentials()
            # Basis-Implementation testet nur ob keine Exception geworfen wird
            # Spezifische Tests können genauere Assertions hinzufügen
    
    @pytest.mark.asyncio
    async def test_agent_validate_credentials_failure(self, mock_config):
        """Test fehlgeschlagene Credential-Validierung"""
        agent = self.create_agent(mock_config)
        
        # Setze API-Key auf None
        if self.required_api_key:
            setattr(mock_config.api, self.required_api_key, None)
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session
            mock_session.post.side_effect = Exception("API key invalid")
            
            result = await agent.validate_credentials()
            # Manche Agenten geben False zurück, andere werfen Exception
            # Dies hängt von der spezifischen Implementierung ab
    
    @pytest.mark.asyncio
    async def test_search_mine_success(self, mock_config, sample_query, mock_response):
        """Test erfolgreiche Suche"""
        agent = self.create_agent(mock_config)
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session
            mock_session.post.return_value.__aenter__.return_value = mock_response
            mock_session.get.return_value.__aenter__.return_value = mock_response
            
            # Initialize agent first
            await agent.initialize()
            
            # Execute search
            results = await agent.execute_search(sample_query)
            
            # Basis-Assertions
            assert isinstance(results, list)
            assert agent.stats["successful_requests"] == 1
            assert agent.stats["failed_requests"] == 0
    
    @pytest.mark.asyncio
    async def test_search_mine_error_handling(self, mock_config, sample_query):
        """Test Fehlerbehandlung bei Suche"""
        agent = self.create_agent(mock_config)
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session
            mock_session.post.side_effect = aiohttp.ClientError("Network error")
            
            results = await agent.execute_search(sample_query)
            
            assert results == []
            assert agent.stats["failed_requests"] == 1
            assert agent.status == AgentStatus.ERROR
    
    @pytest.mark.asyncio
    async def test_cancellation_token(self, mock_config, sample_query):
        """Test Cancellation Token Funktionalität"""
        agent = self.create_agent(mock_config)
        token = CancellationToken()
        
        # Setze Cancellation Token
        agent.set_cancellation_token(token)
        assert agent._cancellation_token == token
        
        # Teste check_cancellation wenn nicht abgebrochen
        await agent.check_cancellation()  # Sollte keine Exception werfen
        
        # Teste check_cancellation wenn abgebrochen
        token.cancel()
        with pytest.raises(CancellationException):
            await agent.check_cancellation()
    
    @pytest.mark.asyncio
    async def test_cleanup(self, mock_config):
        """Test Ressourcen-Cleanup"""
        agent = self.create_agent(mock_config)
        
        # Erstelle Mock Session
        agent._session = AsyncMock()
        agent._session.close = AsyncMock()
        
        await agent.cleanup()
        
        agent._session.close.assert_called_once()
        assert agent._session is None
    
    @pytest.mark.asyncio
    async def test_statistics(self, mock_config, sample_query, mock_response):
        """Test Statistik-Erfassung"""
        agent = self.create_agent(mock_config)
        
        # Führe einige Operationen durch
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session
            mock_session.post.return_value.__aenter__.return_value = mock_response
            
            await agent.execute_search(sample_query)
        
        stats = agent.get_statistics()
        
        assert stats["name"] == self.agent_name
        assert stats["total_requests"] == 1
        assert stats["successful_requests"] == 1
        assert stats["failed_requests"] == 0
        assert "success_rate" in stats
        assert "runtime_seconds" in stats
        assert "requests_per_minute" in stats
    
    @pytest.mark.asyncio
    async def test_field_extraction(self, mock_config):
        """Test Feld-Extraktion aus Text"""
        agent = self.create_agent(mock_config)
        
        test_text = """
        The Test Mine is operated by Mining Corp International.
        Located at coordinates 45.123, -75.456.
        Current status: Active
        Primary commodity: Gold
        Annual production: 100,000 oz
        Remediation costs estimated at $45 million CAD
        """
        
        # Teste verschiedene Extraktionen
        results = agent._extract_with_context(test_text, "betreiber")
        assert len(results) > 0
        
        results = agent._extract_with_context(test_text, "koordinaten")
        assert len(results) > 0
        
        results = agent._extract_with_context(test_text, "aktivitaetsstatus")
        assert len(results) > 0
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, mock_config, sample_query):
        """Test Rate-Limiting Funktionalität"""
        agent = self.create_agent(mock_config)
        
        # Mock Rate Limiter
        mock_rate_limiter = AsyncMock()
        agent._rate_limiter = mock_rate_limiter
        
        with patch('aiohttp.ClientSession'):
            await agent.execute_search(sample_query)
        
        mock_rate_limiter.acquire.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_status_updates(self, mock_config):
        """Test Status-Update Callbacks"""
        agent = self.create_agent(mock_config)
        
        # Mock Status Callback
        status_messages = []
        async def mock_callback(message):
            status_messages.append(message)
        
        agent.status_callback = mock_callback
        
        # Sende Status
        await agent._send_status("Test status message")
        
        assert len(status_messages) == 1
        assert "Test status message" in status_messages[0]
    
    @pytest.mark.asyncio
    async def test_disabled_agent(self, mock_config, sample_query):
        """Test Verhalten bei deaktiviertem Agent"""
        agent = self.create_agent(mock_config)
        agent.status = AgentStatus.DISABLED
        
        results = await agent.execute_search(sample_query)
        
        assert results == []
        assert agent.stats["total_requests"] == 1
        assert agent.stats["successful_requests"] == 0
    
    @pytest.mark.asyncio
    async def test_field_normalization(self, mock_config):
        """Test Feldnamen-Normalisierung"""
        agent = self.create_agent(mock_config)
        
        # Teste verschiedene Feldnamen-Varianten
        assert agent._normalize_field_name("operator") == "betreiber"
        assert agent._normalize_field_name("OWNER") == "betreiber"
        assert agent._normalize_field_name("coordinates") == "koordinaten"
        assert agent._normalize_field_name("GPS Location") == "koordinaten"
        assert agent._normalize_field_name("commodity") == "rohstofftyp"
        assert agent._normalize_field_name("operational_status") == "aktivitaetsstatus"
    
    @pytest.mark.asyncio
    async def test_currency_normalization(self, mock_config):
        """Test Währungs-Normalisierung"""
        agent = self.create_agent(mock_config)
        
        # Teste verschiedene Währungsformate
        result = agent._normalize_currency("$100,000", "USD", "CAD")
        assert result is not None
        assert result > 100000  # USD zu CAD sollte höher sein
        
        result = agent._normalize_currency("€50.000", "EUR", "CAD")
        assert result is not None
        
        result = agent._normalize_currency("123456.78", "CAD", "CAD")
        assert result == 123456.78
    
    @pytest.mark.asyncio
    async def test_year_extraction(self, mock_config):
        """Test Jahr-Extraktion aus Text"""
        agent = self.create_agent(mock_config)
        
        # Teste verschiedene Text-Formate
        year = agent._extract_year_from_text("The mine was opened in 2020")
        assert year == 2020
        
        year = agent._extract_year_from_text("Data from 2019 and updated in 2023")
        assert year == 2023  # Sollte neuestes Jahr zurückgeben
        
        year = agent._extract_year_from_text("No year information")
        assert year is None
    
    @pytest.mark.asyncio
    async def test_json_extraction(self, mock_config):
        """Test JSON-Extraktion aus Text"""
        agent = self.create_agent(mock_config)
        
        # Test mit validem JSON
        text = 'Some text {"field": "value", "number": 123} more text'
        result = agent._safe_extract_json(text)
        assert result is not None
        assert result["field"] == "value"
        assert result["number"] == 123
        
        # Test mit invalidem JSON
        text = "No JSON here"
        result = agent._safe_extract_json(text)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_api_error_handling(self, mock_config):
        """Test spezifische API-Fehlerbehandlung"""
        agent = self.create_agent(mock_config)
        
        # Mock Status Callback
        status_messages = []
        async def mock_callback(message):
            status_messages.append(message)
        agent.status_callback = mock_callback
        
        # Test Rate Limit Error
        error = Exception("Rate limit exceeded")
        await agent._handle_api_error(error, "test context")
        assert any("Rate limit" in msg for msg in status_messages)
        
        # Test Unauthorized Error
        agent.status = AgentStatus.READY
        error = Exception("401 Unauthorized")
        await agent._handle_api_error(error)
        assert agent.status == AgentStatus.ERROR
        
        # Test Timeout Error
        error = Exception("Request timeout")
        await agent._handle_api_error(error)
        assert agent.stats["failed_requests"] > 0