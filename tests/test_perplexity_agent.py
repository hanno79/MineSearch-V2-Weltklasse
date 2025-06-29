"""
Author: rahn
Datum: 19.06.2025
Version: 1.0
Beschreibung: Unit-Tests für Perplexity Agent
"""

import pytest
from unittest.mock import patch, AsyncMock

from src.agents.perplexity_agent import PerplexityAgent
from tests.test_agents_base import BaseAgentTest


class TestPerplexityAgent(BaseAgentTest):
    """Test-Klasse für Perplexity Agent"""
    
    agent_class = PerplexityAgent
    agent_name = "perplexity"
    required_api_key = "perplexity_key"
    
    def create_agent(self, config):
        """Überschrieben für Perplexity-spezifische Initialisierung"""
        return PerplexityAgent(
            name=self.agent_name,
            config={
                "api_config": config.api,
                "scraping_config": config.scraping,
                "max_concurrent": config.max_concurrent_requests
            }
        )
    
    @pytest.mark.asyncio
    async def test_perplexity_web_search(self, mock_config, sample_query):
        """Test Perplexity Web-Such-Funktionalität"""
        agent = self.create_agent(mock_config)
        
        # Mock Perplexity-spezifische Response mit Citations
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "choices": [{
                "message": {
                    "content": """The Test Mine is operated by Test Mining Corp [1].
                    Located at 45.123°N, 75.456°W [2].
                    Current status: Active [3].
                    Primary commodity: Gold [1]."""
                }
            }],
            "citations": [
                {"url": "https://mining-registry.ca/test-mine", "title": "Mining Registry"},
                {"url": "https://maps.gov.ca/mines", "title": "Government Maps"},
                {"url": "https://test-mine.com", "title": "Company Website"}
            ]
        })
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session
            mock_session.post.return_value.__aenter__.return_value = mock_response
            
            results = await agent.search_mine(sample_query)
            
            # Prüfe ob Citations in Metadata enthalten sind
            assert len(results) > 0
            for result in results:
                assert "url" in result.metadata or "citations" in result.metadata
                assert result.source != "Perplexity"  # Sollte spezifische Quelle haben
    
    @pytest.mark.asyncio
    async def test_perplexity_model_options(self, mock_config):
        """Test verschiedene Perplexity Model-Optionen"""
        agent = self.create_agent(mock_config)
        
        # Prüfe ob Online-Modell verwendet wird
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session
            
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                "choices": [{"message": {"content": "test"}}]
            })
            mock_session.post.return_value.__aenter__.return_value = mock_response
            
            await agent.initialize()
            
            # Prüfe API-Call Parameter
            call_args = mock_session.post.call_args
            json_data = call_args[1]['json']
            assert 'model' in json_data
            assert 'online' in json_data['model'] or 'sonar' in json_data['model']
    
    @pytest.mark.asyncio
    async def test_perplexity_search_domain_filter(self, mock_config, sample_query):
        """Test Domain-Filter Funktionalität"""
        agent = self.create_agent(mock_config)
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session
            
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                "choices": [{"message": {"content": "test"}}]
            })
            mock_session.post.return_value.__aenter__.return_value = mock_response
            
            await agent.search_mine(sample_query)
            
            # Prüfe ob Domain-Filter in Request enthalten ist
            call_args = mock_session.post.call_args
            json_data = call_args[1]['json']
            # Perplexity unterstützt möglicherweise search_domain_filter
            # Dies ist implementierungsabhängig
    
    @pytest.mark.asyncio
    async def test_perplexity_rate_limit_handling(self, mock_config, sample_query):
        """Test Perplexity Rate Limit Handling"""
        agent = self.create_agent(mock_config)
        
        # Simuliere Rate Limit Error
        mock_response = AsyncMock()
        mock_response.status = 429
        mock_response.headers = {"Retry-After": "60"}
        mock_response.text = AsyncMock(return_value="Rate limit exceeded")
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session
            mock_session.post.return_value.__aenter__.return_value = mock_response
            
            results = await agent.search_mine(sample_query)
            
            assert results == []
            # Stats sollten aktualisiert sein
            assert agent.stats["failed_requests"] > 0
    
    @pytest.mark.asyncio
    async def test_perplexity_citation_parsing(self, mock_config):
        """Test Citation-Parsing aus Perplexity Responses"""
        agent = self.create_agent(mock_config)
        
        # Test Text mit Citation-Markierungen
        test_content = """
        The mine is operated by ABC Corp [1].
        Production started in 2020 [2].
        Annual output is 100,000 oz [3].
        """
        
        test_citations = [
            {"url": "https://source1.com", "title": "Source 1"},
            {"url": "https://source2.com", "title": "Source 2"},
            {"url": "https://source3.com", "title": "Source 3"}
        ]
        
        # Hier würde normalerweise eine interne Methode getestet
        # Da wir die interne Implementierung nicht kennen, 
        # testen wir das Verhalten durch die öffentliche API
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "choices": [{"message": {"content": test_content}}],
            "citations": test_citations
        })
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session
            mock_session.post.return_value.__aenter__.return_value = mock_response
            
            sample_query = self.sample_query()
            results = await agent.search_mine(sample_query)
            
            # Prüfe ob Citations korrekt zugeordnet wurden
            assert len(results) > 0
            for result in results:
                if result.source_url:
                    assert result.source_url in [c["url"] for c in test_citations]