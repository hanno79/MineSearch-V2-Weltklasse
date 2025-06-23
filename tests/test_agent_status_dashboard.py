"""
Author: rahn
Datum: 19.06.2025
Version: 1.0
Beschreibung: Unit-Tests für Agent Status Dashboard
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from src.agents.agent_status import (
    AgentStatusDashboard, 
    AgentInfo, 
    AgentCapability,
    AgentStatus
)
from src.core.config import Config


class TestAgentStatusDashboard:
    """Test-Klasse für Agent Status Dashboard"""
    
    @pytest.fixture
    def mock_config(self):
        """Mock-Konfiguration für Tests"""
        config = Mock(spec=Config)
        config.api = Mock()
        config.scraping = Mock()
        config.max_concurrent_requests = 5
        
        # Setze einige API-Keys
        config.api.openrouter_key = "test_openrouter_key"
        config.api.perplexity_key = "test_perplexity_key"
        config.api.tavily_key = None  # Simuliere fehlenden Key
        config.api.exa_key = "test_exa_key"
        config.api.apify_key = None
        config.api.scrapingbee_key = "test_scrapingbee_key"
        config.api.firecrawl_key = None
        config.api.brightdata_key = None
        
        # Mock validate method
        config.api.validate = Mock(return_value={
            "openrouter_key": True,
            "perplexity_key": True,
            "tavily_key": False,
            "exa_key": True,
            "apify_key": False,
            "scrapingbee_key": True,
            "firecrawl_key": False,
            "brightdata_key": False
        })
        
        return config
    
    @pytest.fixture
    def dashboard(self, mock_config):
        """Dashboard-Instanz für Tests"""
        return AgentStatusDashboard(mock_config)
    
    @pytest.mark.asyncio
    async def test_dashboard_initialization(self, dashboard):
        """Test Dashboard-Initialisierung"""
        await dashboard.initialize()
        
        # Prüfe ob Agenten korrekt kategorisiert wurden
        assert "claude" in dashboard.agent_info
        assert "perplexity" in dashboard.agent_info
        assert "scraper" in dashboard.agent_info
        
        # Prüfe Status basierend auf API-Keys
        assert dashboard.agent_info["claude"].status == AgentStatus.READY
        assert dashboard.agent_info["perplexity"].status == AgentStatus.READY
        assert dashboard.agent_info["tavily"].status == AgentStatus.DISABLED
        assert dashboard.agent_info["scraper"].status == AgentStatus.READY  # Immer ready
    
    def test_format_status_table(self, dashboard):
        """Test Status-Tabellen-Formatierung"""
        # Füge Test-Daten hinzu
        dashboard.agent_info["test_agent"] = AgentInfo(
            name="test_agent",
            type="TEST",
            status=AgentStatus.READY,
            api_key_required=True,
            api_key_present=True,
            capabilities=[AgentCapability.WEB_SEARCH],
            error_count=0,
            success_count=10,
            last_used=datetime.now(),
            avg_response_time=1.5,
            cost_per_request=0.001
        )
        
        table = dashboard.format_status_table()
        
        # Prüfe ob Tabelle korrekt formatiert ist
        assert "Agent Status Dashboard" in table
        assert "test_agent" in table
        assert "READY" in table
        assert "✅" in table  # Status-Symbol
        assert "$0.0010" in table  # Kosten-Format
    
    def test_get_agents_by_capability(self, dashboard):
        """Test Agenten-Filterung nach Capability"""
        # Initialisiere mit Test-Daten
        dashboard.agent_info = {
            "agent1": AgentInfo(
                name="agent1", type="AI", status=AgentStatus.READY,
                capabilities=[AgentCapability.AI_ANALYSIS, AgentCapability.MULTI_LANGUAGE]
            ),
            "agent2": AgentInfo(
                name="agent2", type="SEARCH", status=AgentStatus.READY,
                capabilities=[AgentCapability.WEB_SEARCH]
            ),
            "agent3": AgentInfo(
                name="agent3", type="SCRAPING", status=AgentStatus.DISABLED,
                capabilities=[AgentCapability.WEB_SCRAPING]
            )
        }
        
        # Test verschiedene Capabilities
        ai_agents = dashboard.get_agents_by_capability(AgentCapability.AI_ANALYSIS)
        assert ai_agents == ["agent1"]
        
        search_agents = dashboard.get_agents_by_capability(AgentCapability.WEB_SEARCH)
        assert search_agents == ["agent2"]
        
        # Disabled Agenten sollten nicht enthalten sein
        scraping_agents = dashboard.get_agents_by_capability(AgentCapability.WEB_SCRAPING)
        assert scraping_agents == []
    
    def test_get_fallback_agents(self, dashboard):
        """Test Fallback-Agent-Empfehlungen"""
        # Setup Test-Agenten
        dashboard.agent_info = {
            "claude": AgentInfo(
                name="claude", type="AI", status=AgentStatus.ERROR,
                capabilities=[AgentCapability.AI_ANALYSIS]
            ),
            "gpt4": AgentInfo(
                name="gpt4", type="AI", status=AgentStatus.READY,
                capabilities=[AgentCapability.AI_ANALYSIS]
            ),
            "deepseek": AgentInfo(
                name="deepseek", type="AI", status=AgentStatus.READY,
                capabilities=[AgentCapability.AI_ANALYSIS, AgentCapability.DEEP_RESEARCH]
            )
        }
        
        # Test Fallback für fehlgeschlagenen AI-Agent
        fallbacks = dashboard.get_fallback_agents("claude")
        assert "gpt4" in fallbacks
        assert "deepseek" in fallbacks
        assert "claude" not in fallbacks  # Sollte sich selbst nicht empfehlen
    
    def test_get_status_summary(self, dashboard):
        """Test Status-Zusammenfassung"""
        # Setup Test-Daten
        dashboard.agent_info = {
            "ai1": AgentInfo(name="ai1", type="AI", status=AgentStatus.READY),
            "ai2": AgentInfo(name="ai2", type="AI", status=AgentStatus.DISABLED),
            "search1": AgentInfo(name="search1", type="SEARCH", status=AgentStatus.READY),
            "scraping1": AgentInfo(name="scraping1", type="SCRAPING", status=AgentStatus.ERROR)
        }
        
        summary = dashboard.get_status_summary()
        
        # Prüfe Zusammenfassung
        assert summary["total_agents"] == 4
        assert summary["active_agents"] == 2
        assert summary["disabled_agents"] == 1
        assert summary["error_agents"] == 1
        
        # Prüfe Gruppierung nach Typ
        assert summary["agents_by_type"]["AI"]["total"] == 2
        assert summary["agents_by_type"]["AI"]["active"] == 1
        assert summary["agents_by_type"]["SEARCH"]["total"] == 1
        assert summary["agents_by_type"]["SEARCH"]["active"] == 1
    
    def test_get_health_report(self, dashboard):
        """Test System-Gesundheitsbericht"""
        # Setup problematische Konfiguration
        dashboard.agent_info = {
            "agent1": AgentInfo(
                name="agent1", type="AI", status=AgentStatus.ERROR,
                error_count=10, success_count=0
            ),
            "agent2": AgentInfo(
                name="agent2", type="SEARCH", status=AgentStatus.READY,
                error_count=2, success_count=100
            ),
            "scraper": AgentInfo(
                name="scraper", type="SCRAPING", status=AgentStatus.READY,
                error_count=0, success_count=50
            )
        }
        
        report = dashboard.get_health_report()
        
        # System sollte als degraded eingestuft werden
        assert report["system_health"] in ["degraded", "critical"]
        
        # Sollte Fehler und Warnungen enthalten
        assert len(report["errors"]) > 0
        assert any("agent1" in error for error in report["errors"])
        
        # Sollte Empfehlungen enthalten
        assert len(report["recommendations"]) > 0
    
    def test_cost_estimate(self, dashboard):
        """Test Kosten-Schätzung"""
        # Setup Agenten mit verschiedenen Kosten
        dashboard.agent_info = {
            "cheap": AgentInfo(
                name="cheap", status=AgentStatus.READY,
                cost_per_request=0.001
            ),
            "medium": AgentInfo(
                name="medium", status=AgentStatus.READY,
                cost_per_request=0.01
            ),
            "expensive": AgentInfo(
                name="expensive", status=AgentStatus.READY,
                cost_per_request=0.1
            ),
            "disabled": AgentInfo(
                name="disabled", status=AgentStatus.DISABLED,
                cost_per_request=1.0  # Sollte ignoriert werden
            )
        }
        
        # Test mit spezifischen Agenten
        cost = dashboard.get_cost_estimate(["cheap", "medium"])
        assert cost == 0.011
        
        # Test mit allen aktiven Agenten
        cost = dashboard.get_cost_estimate()
        assert cost == 0.111  # cheap + medium + expensive
        
        # Disabled Agent sollte nicht gezählt werden
        cost = dashboard.get_cost_estimate(["cheap", "disabled"])
        assert cost == 0.001
    
    @pytest.mark.asyncio
    async def test_test_single_agent(self, dashboard):
        """Test einzelne Agent-Validierung"""
        # Mock Agent
        mock_agent = AsyncMock()
        mock_agent.validate_credentials = AsyncMock(return_value=True)
        
        with patch('src.agents.factory.AgentFactory.create_agent', return_value=mock_agent):
            success, message = await dashboard.test_single_agent("test_agent")
            
            assert success is True
            assert "erfolgreich" in message.lower()
            mock_agent.validate_credentials.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_test_single_agent_failure(self, dashboard):
        """Test fehlgeschlagene Agent-Validierung"""
        # Mock Agent mit Fehler
        mock_agent = AsyncMock()
        mock_agent.validate_credentials = AsyncMock(side_effect=Exception("API Error"))
        
        with patch('src.agents.factory.AgentFactory.create_agent', return_value=mock_agent):
            success, message = await dashboard.test_single_agent("test_agent")
            
            assert success is False
            assert "API Error" in message
    
    @pytest.mark.asyncio
    async def test_test_all_agents(self, dashboard):
        """Test alle Agenten validieren"""
        # Setup Test-Agenten
        dashboard.agent_info = {
            "agent1": AgentInfo(name="agent1", status=AgentStatus.READY),
            "agent2": AgentInfo(name="agent2", status=AgentStatus.READY),
            "agent3": AgentInfo(name="agent3", status=AgentStatus.DISABLED)
        }
        
        # Mock test_single_agent
        async def mock_test(name):
            if name == "agent1":
                return True, "OK"
            elif name == "agent2":
                return False, "Error"
            else:
                return False, "Disabled"
        
        dashboard.test_single_agent = mock_test
        
        results = await dashboard.test_all_agents()
        
        # Prüfe Ergebnisse
        assert len(results) == 3
        assert results["agent1"] == (True, "OK")
        assert results["agent2"] == (False, "Error")
        # Agent3 sollte getestet werden, auch wenn disabled
    
    def test_agent_capability_mapping(self, dashboard):
        """Test korrekte Capability-Zuordnung"""
        # Prüfe dass alle definierten Agenten korrekte Capabilities haben
        for agent_name, definition in dashboard.AGENT_DEFINITIONS.items():
            capabilities = definition.get("capabilities", [])
            
            # Jeder Agent sollte mindestens eine Capability haben
            assert len(capabilities) > 0
            
            # Capabilities sollten vom richtigen Typ sein
            for cap in capabilities:
                assert isinstance(cap, AgentCapability)