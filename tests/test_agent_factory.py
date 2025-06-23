"""
Author: rahn
Datum: 19.06.2025
Version: 1.0
Beschreibung: Unit-Tests für Agent Factory
"""

import pytest
from unittest.mock import Mock, patch

from src.agents.factory import AgentFactory
from src.agents.base_agent import BaseAgent
from src.core.config import Config


class TestAgentFactory:
    """Test-Klasse für Agent Factory"""
    
    @pytest.fixture
    def mock_config(self):
        """Mock-Konfiguration für Tests"""
        config = Mock(spec=Config)
        config.api = Mock()
        config.scraping = Mock()
        config.max_concurrent_requests = 5
        
        # Standard API-Keys
        config.api.openrouter_key = "test_openrouter_key"
        config.api.perplexity_key = "test_perplexity_key"
        config.api.tavily_key = "test_tavily_key"
        config.api.exa_key = "test_exa_key"
        config.api.apify_key = "test_apify_key"
        config.api.scrapingbee_key = "test_scrapingbee_key"
        config.api.firecrawl_key = "test_firecrawl_key"
        config.api.brightdata_key = "test_brightdata_key"
        
        return config
    
    def test_create_agent_success(self, mock_config):
        """Test erfolgreiche Agent-Erstellung"""
        # Test verschiedene Agent-Typen
        agent_types = ["claude", "gpt4", "perplexity", "scraper", "tavily"]
        
        for agent_type in agent_types:
            agent = AgentFactory.create_agent(agent_type, mock_config)
            assert agent is not None
            assert isinstance(agent, BaseAgent)
            assert agent.name == agent_type
    
    def test_create_agent_invalid_type(self, mock_config):
        """Test Fehler bei unbekanntem Agent-Typ"""
        with pytest.raises(ValueError, match="Unbekannter Agent-Typ"):
            AgentFactory.create_agent("invalid_agent", mock_config)
    
    def test_create_openrouter_agent(self, mock_config):
        """Test OpenRouter Agent Erstellung"""
        # Test mit model_id Parameter
        agent = AgentFactory.create_agent(
            "openrouter_claude",
            mock_config,
            model_id="anthropic/claude-3.5-sonnet"
        )
        assert agent is not None
        assert agent.name == "openrouter"
    
    def test_create_openrouter_agent_auto_model_detection(self, mock_config):
        """Test OpenRouter Agent mit automatischer Model-Erkennung"""
        # Test ohne explizite model_id
        with patch('src.agents.openrouter_agent.OpenRouterAgent') as mock_openrouter:
            mock_openrouter.FREE_MODELS = {
                "google/gemma-2-9b-it:free": {"name": "Gemma 2 9B"}
            }
            mock_openrouter.PREMIUM_MODELS = {
                "anthropic/claude-3.5-sonnet": {"name": "Claude 3.5"}
            }
            
            agent = AgentFactory.create_agent("openrouter_gemma-2-9b-it", mock_config)
            # Factory sollte versuchen, das Modell zu finden
    
    def test_create_deepseek_variants(self, mock_config):
        """Test DeepSeek Agent Varianten"""
        variants = ["deepseek", "deepseek_reasoner", "deepseek_coder"]
        
        for variant in variants:
            agent = AgentFactory.create_agent(variant, mock_config)
            assert agent is not None
            assert variant in agent.name
    
    def test_get_available_agents_with_all_keys(self, mock_config):
        """Test verfügbare Agenten mit allen API-Keys"""
        available = AgentFactory.get_available_agents(mock_config)
        
        # Mit allen Keys sollten viele Agenten verfügbar sein
        assert available["claude"] is True
        assert available["gpt4"] is True
        assert available["perplexity"] is True
        assert available["scraper"] is True  # Immer verfügbar
        assert available["tavily"] is True
        assert available["exa"] is True
        assert available["apify"] is True
        assert available["scrapingbee"] is True
        assert available["firecrawl"] is True
        assert available["brightdata"] is True
        assert available["deepseek"] is True
        assert available["deep_web_crawler"] is True
        assert available["perplexity_deep"] is True
        assert available["premium_mining"] is True
    
    def test_get_available_agents_without_keys(self, mock_config):
        """Test verfügbare Agenten ohne API-Keys"""
        # Entferne alle API-Keys
        mock_config.api.openrouter_key = None
        mock_config.api.perplexity_key = None
        mock_config.api.tavily_key = None
        mock_config.api.exa_key = None
        mock_config.api.apify_key = None
        mock_config.api.scrapingbee_key = None
        mock_config.api.firecrawl_key = None
        mock_config.api.brightdata_key = None
        
        available = AgentFactory.get_available_agents(mock_config)
        
        # Ohne Keys sollten nur wenige Agenten verfügbar sein
        assert available["claude"] is False
        assert available["gpt4"] is False
        assert available["perplexity"] is False
        assert available["scraper"] is True  # Immer verfügbar
        assert available["tavily"] is False
        assert available["exa"] is False
        assert available["apify"] is False
        assert available["scrapingbee"] is False
        assert available["firecrawl"] is False
        assert available["brightdata"] is False
        assert available["deepseek"] is False
        assert available["deep_web_crawler"] is True  # Immer verfügbar
        assert available["perplexity_deep"] is False
        assert available["premium_mining"] is False
    
    def test_get_available_agents_partial_keys(self, mock_config):
        """Test verfügbare Agenten mit teilweisen API-Keys"""
        # Nur einige Keys setzen
        mock_config.api.openrouter_key = "test_key"
        mock_config.api.perplexity_key = None
        mock_config.api.tavily_key = "test_key"
        mock_config.api.exa_key = None
        
        available = AgentFactory.get_available_agents(mock_config)
        
        # Prüfe selektive Verfügbarkeit
        assert available["claude"] is True  # Via OpenRouter
        assert available["gpt4"] is True    # Via OpenRouter
        assert available["perplexity"] is False
        assert available["tavily"] is True
        assert available["exa"] is False
    
    def test_get_agent_requirements(self):
        """Test Agent-Anforderungen"""
        # Test bekannte Agenten
        req = AgentFactory.get_agent_requirements("claude")
        assert req["api_key"] == "openrouter_key"
        assert "Claude" in req["description"]
        
        req = AgentFactory.get_agent_requirements("scraper")
        assert req["api_key"] is None
        assert "no API needed" in req["description"]
        
        req = AgentFactory.get_agent_requirements("perplexity")
        assert req["api_key"] == "perplexity_key"
        
        # Test OpenRouter Agenten
        req = AgentFactory.get_agent_requirements("openrouter_gemma")
        assert req["api_key"] == "openrouter_key"
        assert "OpenRouter Model" in req["description"]
        
        # Test unbekannter Agent
        req = AgentFactory.get_agent_requirements("unknown_agent")
        assert req["api_key"] == "unknown"
    
    def test_factory_agent_registration(self):
        """Test dass alle Agenten korrekt registriert sind"""
        expected_agents = [
            "claude", "gpt4", "perplexity", "scraper", "tavily",
            "exa", "apify", "scrapingbee", "firecrawl", "brightdata",
            "openrouter", "deepseek", "deepseek_reasoner", "deepseek_coder",
            "deep_web_crawler", "perplexity_deep", "premium_mining"
        ]
        
        for agent_type in expected_agents:
            assert agent_type in AgentFactory._agent_classes
    
    def test_create_agent_with_custom_config(self, mock_config):
        """Test Agent-Erstellung mit benutzerdefinierten Parametern"""
        # Ändere Config-Werte
        mock_config.max_concurrent_requests = 10
        
        agent = AgentFactory.create_agent("scraper", mock_config)
        
        # Prüfe ob Config korrekt übergeben wurde
        assert agent.config["max_concurrent"] == 10
        assert agent.config["api_config"] == mock_config.api
        assert agent.config["scraping_config"] == mock_config.scraping
    
    def test_openrouter_model_availability(self, mock_config):
        """Test OpenRouter Model-Verfügbarkeit"""
        with patch('src.agents.openrouter_agent.OpenRouterAgent') as mock_openrouter:
            # Mock Modelle
            mock_openrouter.FREE_MODELS = {
                "google/gemma-2-9b-it:free": {"name": "Gemma 2"},
                "meta-llama/llama-3.2-1b-instruct:free": {"name": "Llama 3.2"}
            }
            mock_openrouter.PREMIUM_MODELS = {
                "anthropic/claude-3.5-sonnet": {"name": "Claude 3.5"},
                "openai/gpt-4-turbo": {"name": "GPT-4 Turbo"}
            }
            
            available = AgentFactory.get_available_agents(mock_config)
            
            # Prüfe ob OpenRouter Modelle als verfügbar gelistet werden
            assert available.get("openrouter_gemma-2-9b-it") is True
            assert available.get("openrouter_llama-3.2-1b-instruct") is True
            assert available.get("openrouter_claude-3.5-sonnet") is True
            assert available.get("openrouter_gpt-4-turbo") is True