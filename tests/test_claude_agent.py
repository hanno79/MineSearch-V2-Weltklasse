"""
Author: rahn
Datum: 19.06.2025
Version: 1.0
Beschreibung: Unit-Tests für Claude Agent
"""

import pytest
from unittest.mock import patch, AsyncMock

from src.agents.claude_agent import ClaudeAgent
from tests.test_agents_base import BaseAgentTest


class TestClaudeAgent(BaseAgentTest):
    """Test-Klasse für Claude Agent"""
    
    agent_class = ClaudeAgent
    agent_name = "claude"
    required_api_key = "openrouter_key"
    
    @pytest.mark.asyncio
    async def test_claude_specific_search(self, mock_config, sample_query):
        """Test Claude-spezifische Such-Funktionalität"""
        agent = self.create_agent(mock_config)
        
        # Mock spezifische Claude Response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "choices": [{
                "message": {
                    "content": """Based on my research:
                    - Operator: Test Mining Corporation
                    - Coordinates: 45.123°N, 75.456°W
                    - Status: Active mining operation
                    - Commodity: Gold, Silver
                    - Annual Production: 150,000 oz gold
                    - Closure costs: $75 million CAD"""
                }
            }]
        })
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session
            mock_session.post.return_value.__aenter__.return_value = mock_response
            
            results = await agent.search_mine(sample_query)
            
            # Prüfe ob alle Felder extrahiert wurden
            field_names = [r.field_name for r in results]
            assert "betreiber" in field_names
            assert "koordinaten" in field_names
            assert "aktivitaetsstatus" in field_names
            assert "rohstofftyp" in field_names
            
            # Prüfe spezifische Werte
            betreiber_result = next(r for r in results if r.field_name == "betreiber")
            assert "Test Mining Corporation" in betreiber_result.value
            assert betreiber_result.agent_name == "claude"
            assert betreiber_result.confidence_score >= 0.8
    
    @pytest.mark.asyncio
    async def test_claude_multi_language_support(self, mock_config):
        """Test Mehrsprachunterstützung"""
        agent = self.create_agent(mock_config)
        
        # Query mit französischer Sprache
        query = sample_query = self.sample_query()
        query.languages = ["fr", "en"]
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "choices": [{
                "message": {
                    "content": """D'après mes recherches:
                    - Exploitant: Société Minière Test
                    - Coordonnées: 45.123°N, 75.456°O
                    - Statut: Mine active"""
                }
            }]
        })
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session
            mock_session.post.return_value.__aenter__.return_value = mock_response
            
            results = await agent.search_mine(query)
            
            # Sollte trotz französischer Antwort korrekt extrahieren
            assert len(results) > 0
            field_names = [r.field_name for r in results]
            assert "betreiber" in field_names or "koordinaten" in field_names
    
    @pytest.mark.asyncio
    async def test_claude_error_handling(self, mock_config, sample_query):
        """Test Claude-spezifische Fehlerbehandlung"""
        agent = self.create_agent(mock_config)
        
        # Test mit 429 Rate Limit Error
        mock_response = AsyncMock()
        mock_response.status = 429
        mock_response.text = AsyncMock(return_value="Rate limit exceeded")
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session
            mock_session.post.return_value.__aenter__.return_value = mock_response
            
            results = await agent.search_mine(sample_query)
            
            assert results == []
            # Agent sollte nicht permanent auf ERROR gesetzt werden bei Rate Limit
            assert agent.status != AgentStatus.ERROR
    
    @pytest.mark.asyncio
    async def test_claude_model_selection(self, mock_config):
        """Test Model-Auswahl für Claude"""
        agent = self.create_agent(mock_config)
        
        # Prüfe ob korrektes Modell verwendet wird
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session
            
            # Mock response
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"choices": [{"message": {"content": "test"}}]})
            mock_session.post.return_value.__aenter__.return_value = mock_response
            
            await agent.initialize()
            
            # Prüfe ob API-Call mit korrektem Model gemacht wurde
            call_args = mock_session.post.call_args
            assert call_args is not None
            json_data = call_args[1]['json']
            assert 'model' in json_data
            assert 'claude' in json_data['model'].lower() or 'anthropic' in json_data['model'].lower()