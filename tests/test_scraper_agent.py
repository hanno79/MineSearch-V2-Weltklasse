"""
Author: rahn
Datum: 19.06.2025
Version: 1.0
Beschreibung: Unit-Tests für Scraper Agent
"""

import pytest
from unittest.mock import patch, AsyncMock, Mock

from src.agents.scraper_agent import ScraperAgent
from tests.test_agents_base import BaseAgentTest


class TestScraperAgent(BaseAgentTest):
    """Test-Klasse für Scraper Agent"""
    
    agent_class = ScraperAgent
    agent_name = "scraper"
    required_api_key = None  # Scraper benötigt keinen API-Key
    
    @pytest.mark.asyncio
    async def test_scraper_no_api_key_required(self, mock_config):
        """Test dass Scraper ohne API-Key funktioniert"""
        # Entferne alle API-Keys
        mock_config.api.openrouter_key = None
        mock_config.api.perplexity_key = None
        
        agent = self.create_agent(mock_config)
        result = await agent.validate_credentials()
        
        # Scraper sollte immer True zurückgeben
        assert result is True
    
    @pytest.mark.asyncio
    async def test_scraper_google_search(self, mock_config, sample_query):
        """Test Google-Such-Funktionalität"""
        agent = self.create_agent(mock_config)
        
        # Mock Google Search Response
        mock_html = """
        <html>
        <body>
            <div class="g">
                <h3>Test Mine - Official Website</h3>
                <a href="https://test-mine.com">test-mine.com</a>
                <span>Test Mine operated by Test Mining Corp. Located in Ontario.</span>
            </div>
            <div class="g">
                <h3>Mining Registry - Test Mine</h3>
                <a href="https://mining-registry.ca/test-mine">mining-registry.ca</a>
                <span>Coordinates: 45.123, -75.456. Status: Active. Gold mine.</span>
            </div>
        </body>
        </html>
        """
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session
            
            # Mock Google search response
            mock_search_response = AsyncMock()
            mock_search_response.status = 200
            mock_search_response.text = AsyncMock(return_value=mock_html)
            
            # Mock page scraping responses
            mock_page_response = AsyncMock()
            mock_page_response.status = 200
            mock_page_response.text = AsyncMock(return_value="""
                <html><body>
                <h1>Test Mine</h1>
                <p>Operator: Test Mining Corporation</p>
                <p>Location: 45.123°N, 75.456°W</p>
                <p>Status: Active mining operation</p>
                <p>Commodity: Gold, Silver</p>
                </body></html>
            """)
            
            # Setup response routing
            async def mock_get(url, *args, **kwargs):
                if "google.com/search" in url:
                    return mock_search_response
                else:
                    return mock_page_response
            
            mock_session.get = mock_get
            
            results = await agent.search_mine(sample_query)
            
            # Prüfe ob Ergebnisse gefunden wurden
            assert len(results) > 0
            field_names = [r.field_name for r in results]
            
            # Scraper sollte mindestens einige Felder finden
            assert any(field in field_names for field in ["betreiber", "koordinaten", "aktivitaetsstatus"])
    
    @pytest.mark.asyncio
    async def test_scraper_url_extraction(self, mock_config):
        """Test URL-Extraktion aus Google-Ergebnissen"""
        agent = self.create_agent(mock_config)
        
        # Test HTML mit verschiedenen URL-Formaten
        test_html = """
        <div class="g">
            <a href="/url?q=https://example.com&amp;sa=U&amp;ved=123">Link 1</a>
        </div>
        <div class="g">
            <a href="https://direct-link.com">Link 2</a>
        </div>
        <div class="g">
            <a href="/url?q=https://another-example.com">Link 3</a>
        </div>
        """
        
        # Simuliere interne Methode falls zugänglich
        # Ansonsten testen wir durch die öffentliche API
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session
            
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value=test_html)
            mock_session.get.return_value.__aenter__.return_value = mock_response
            
            # Führe Suche durch
            sample_query = self.sample_query()
            await agent.search_mine(sample_query)
            
            # Prüfe ob URLs korrekt extrahiert wurden
            # Dies testet indirekt die URL-Extraktion
            assert mock_session.get.call_count > 1  # Sollte mehrere URLs besuchen
    
    @pytest.mark.asyncio
    async def test_scraper_error_handling(self, mock_config, sample_query):
        """Test Fehlerbehandlung beim Scraping"""
        agent = self.create_agent(mock_config)
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session
            
            # Simuliere Netzwerkfehler
            mock_session.get.side_effect = Exception("Network error")
            
            results = await agent.search_mine(sample_query)
            
            # Sollte leere Liste zurückgeben, nicht crashen
            assert results == []
            assert agent.stats["failed_requests"] > 0
    
    @pytest.mark.asyncio
    async def test_scraper_text_extraction(self, mock_config):
        """Test Text-Extraktion aus HTML"""
        agent = self.create_agent(mock_config)
        
        # Test verschiedene HTML-Strukturen
        test_cases = [
            # Einfacher Text
            ("<p>Test Mining Corp operates the mine</p>", "Test Mining Corp"),
            # Text mit Tags
            ("<p>Located at <strong>45.123, -75.456</strong></p>", "45.123, -75.456"),
            # Tabellen
            ("<table><tr><td>Status:</td><td>Active</td></tr></table>", "Active"),
            # Listen
            ("<ul><li>Commodity: Gold</li><li>Production: 100k oz</li></ul>", "Gold"),
        ]
        
        for html, expected_text in test_cases:
            with patch('aiohttp.ClientSession') as mock_session_class:
                mock_session = AsyncMock()
                mock_session_class.return_value.__aenter__.return_value = mock_session
                
                # Mock search results
                search_html = f'<div class="g"><a href="http://test.com">Test</a></div>'
                mock_search = AsyncMock()
                mock_search.status = 200
                mock_search.text = AsyncMock(return_value=search_html)
                
                # Mock page content
                mock_page = AsyncMock()
                mock_page.status = 200
                mock_page.text = AsyncMock(return_value=f"<html><body>{html}</body></html>")
                
                async def mock_get(url, *args, **kwargs):
                    if "google.com/search" in url:
                        return mock_search
                    else:
                        return mock_page
                
                mock_session.get = mock_get
                
                sample_query = self.sample_query()
                results = await agent.search_mine(sample_query)
                
                # Prüfe ob erwarteter Text extrahiert wurde
                all_values = [r.value for r in results]
                assert any(expected_text in str(v) for v in all_values)
    
    @pytest.mark.asyncio
    async def test_scraper_multi_language_search(self, mock_config):
        """Test Mehrsprachige Suche"""
        agent = self.create_agent(mock_config)
        
        # Query mit mehreren Sprachen
        query = self.sample_query()
        query.languages = ["en", "fr", "es"]
        
        call_count = 0
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session
            
            async def mock_get(url, *args, **kwargs):
                nonlocal call_count
                call_count += 1
                
                mock_response = AsyncMock()
                mock_response.status = 200
                
                # Unterschiedliche Responses für verschiedene Sprachen
                if "hl=en" in url:
                    mock_response.text = AsyncMock(return_value="<div>English results</div>")
                elif "hl=fr" in url:
                    mock_response.text = AsyncMock(return_value="<div>Résultats français</div>")
                elif "hl=es" in url:
                    mock_response.text = AsyncMock(return_value="<div>Resultados españoles</div>")
                else:
                    mock_response.text = AsyncMock(return_value="<div>Default results</div>")
                
                return mock_response
            
            mock_session.get = mock_get
            
            await agent.search_mine(query)
            
            # Prüfe ob für jede Sprache gesucht wurde
            assert call_count >= len(query.languages)