"""
Author: rahn
Datum: 19.06.2025
Version: 1.0
Beschreibung: Agent Status Dashboard und Management
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio

from .base_agent import BaseAgent, AgentStatus
from .factory import AgentFactory
from src.core.config import Config
from src.core.logger import get_logger


class AgentCapability(Enum):
    """Capabilities eines Agenten"""
    WEB_SEARCH = "web_search"
    WEB_SCRAPING = "web_scraping"
    AI_ANALYSIS = "ai_analysis"
    DEEP_RESEARCH = "deep_research"
    DOCUMENT_PARSING = "document_parsing"
    MULTI_LANGUAGE = "multi_language"
    GOVERNMENT_ACCESS = "government_access"
    PREMIUM_SOURCES = "premium_sources"


@dataclass
class AgentInfo:
    """Detaillierte Agent-Information"""
    name: str
    type: str
    status: AgentStatus
    capabilities: List[AgentCapability]
    api_required: bool
    api_key_present: bool
    error_message: Optional[str] = None
    last_used: Optional[datetime] = None
    requests_made: int = 0
    success_rate: float = 0.0
    average_response_time: float = 0.0
    cost_per_request: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class AgentStatusDashboard:
    """Zentrale Statusübersicht und Management für alle Agenten"""
    
    # Agent-Definitionen mit Capabilities
    AGENT_DEFINITIONS = {
        "claude": {
            "type": "AI",
            "capabilities": [AgentCapability.AI_ANALYSIS, AgentCapability.MULTI_LANGUAGE],
            "api_required": True,
            "api_key": "openrouter_key",
            "cost_per_request": 0.015
        },
        "gpt4": {
            "type": "AI",
            "capabilities": [AgentCapability.AI_ANALYSIS, AgentCapability.MULTI_LANGUAGE],
            "api_required": True,
            "api_key": "openrouter_key",
            "cost_per_request": 0.02
        },
        "perplexity": {
            "type": "Search",
            "capabilities": [AgentCapability.WEB_SEARCH, AgentCapability.DEEP_RESEARCH],
            "api_required": True,
            "api_key": "perplexity_key",
            "cost_per_request": 0.001
        },
        "perplexity_deep": {
            "type": "Search",
            "capabilities": [AgentCapability.WEB_SEARCH, AgentCapability.DEEP_RESEARCH, AgentCapability.PREMIUM_SOURCES],
            "api_required": True,
            "api_key": "perplexity_key",
            "cost_per_request": 0.005
        },
        "tavily": {
            "type": "Search",
            "capabilities": [AgentCapability.WEB_SEARCH, AgentCapability.DOCUMENT_PARSING],
            "api_required": True,
            "api_key": "tavily_key",
            "cost_per_request": 0.001
        },
        "exa": {
            "type": "Search",
            "capabilities": [AgentCapability.WEB_SEARCH],
            "api_required": True,
            "api_key": "exa_key",
            "cost_per_request": 0.001
        },
        "scraper": {
            "type": "Scraper",
            "capabilities": [AgentCapability.WEB_SCRAPING],
            "api_required": False,
            "api_key": None,
            "cost_per_request": 0.0
        },
        "apify": {
            "type": "Scraper",
            "capabilities": [AgentCapability.WEB_SCRAPING, AgentCapability.GOVERNMENT_ACCESS],
            "api_required": True,
            "api_key": "apify_key",
            "cost_per_request": 0.002
        },
        "scrapingbee": {
            "type": "Scraper",
            "capabilities": [AgentCapability.WEB_SCRAPING, AgentCapability.DOCUMENT_PARSING],
            "api_required": True,
            "api_key": "scrapingbee_key",
            "cost_per_request": 0.001
        },
        "firecrawl": {
            "type": "Scraper",
            "capabilities": [AgentCapability.WEB_SCRAPING, AgentCapability.DOCUMENT_PARSING],
            "api_required": True,
            "api_key": "firecrawl_key",
            "cost_per_request": 0.002
        },
        "brightdata": {
            "type": "Scraper",
            "capabilities": [AgentCapability.WEB_SCRAPING, AgentCapability.PREMIUM_SOURCES, AgentCapability.GOVERNMENT_ACCESS],
            "api_required": True,
            "api_key": "brightdata_key",
            "cost_per_request": 0.005
        },
        "deepseek": {
            "type": "AI",
            "capabilities": [AgentCapability.AI_ANALYSIS, AgentCapability.DEEP_RESEARCH],
            "api_required": True,
            "api_key": "openrouter_key",
            "cost_per_request": 0.001
        }
    }
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger(__name__)
        self.agent_instances: Dict[str, BaseAgent] = {}
        self.agent_info: Dict[str, AgentInfo] = {}
        self._initialized = False
        
    async def initialize(self) -> None:
        """Initialisiert alle verfügbaren Agenten"""
        if self._initialized:
            return
            
        self.logger.info("Initialisiere Agent Status Dashboard...")
        
        # Sammle alle verfügbaren Agenten
        available_agents = AgentFactory.get_available_agents(self.config)
        
        for agent_name, is_available in available_agents.items():
            # Skip Hilfsklassen
            if agent_name in ["deep_web_crawler", "premium_mining"]:
                continue
                
            definition = self.AGENT_DEFINITIONS.get(agent_name, {
                "type": "Unknown",
                "capabilities": [],
                "api_required": True,
                "api_key": None,
                "cost_per_request": 0.0
            })
            
            # Prüfe API-Key Status
            api_key_present = False
            if definition["api_key"]:
                api_key_present = bool(getattr(self.config.api, definition["api_key"], None))
            elif not definition["api_required"]:
                api_key_present = True
            
            # Erstelle AgentInfo
            info = AgentInfo(
                name=agent_name,
                type=definition["type"],
                status=AgentStatus.READY if is_available and api_key_present else AgentStatus.DISABLED,
                capabilities=definition["capabilities"],
                api_required=definition["api_required"],
                api_key_present=api_key_present,
                cost_per_request=definition["cost_per_request"],
                error_message="Kein API-Key konfiguriert" if not api_key_present and definition["api_required"] else None
            )
            
            self.agent_info[agent_name] = info
            
            # Versuche Agent zu initialisieren wenn verfügbar
            if is_available and api_key_present:
                try:
                    agent = AgentFactory.create_agent(agent_name, self.config)
                    if agent:
                        success = await agent.initialize()
                        if success:
                            self.agent_instances[agent_name] = agent
                            info.status = AgentStatus.READY
                        else:
                            info.status = AgentStatus.ERROR
                            info.error_message = "Initialisierung fehlgeschlagen"
                except Exception as e:
                    self.logger.error(f"Fehler bei Initialisierung von {agent_name}: {e}")
                    info.status = AgentStatus.ERROR
                    info.error_message = str(e)
        
        self._initialized = True
        self.logger.info(f"Dashboard initialisiert: {len(self.agent_instances)} aktive Agenten")
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Gibt eine Zusammenfassung aller Agent-Status zurück"""
        summary = {
            "total_agents": len(self.agent_info),
            "active_agents": sum(1 for info in self.agent_info.values() if info.status == AgentStatus.READY),
            "disabled_agents": sum(1 for info in self.agent_info.values() if info.status == AgentStatus.DISABLED),
            "error_agents": sum(1 for info in self.agent_info.values() if info.status == AgentStatus.ERROR),
            "agents_by_type": {},
            "agents_by_capability": {},
            "estimated_cost_per_search": 0.0,
            "details": {}
        }
        
        # Gruppiere nach Typ
        for info in self.agent_info.values():
            agent_type = info.type
            if agent_type not in summary["agents_by_type"]:
                summary["agents_by_type"][agent_type] = {"total": 0, "active": 0}
            summary["agents_by_type"][agent_type]["total"] += 1
            if info.status == AgentStatus.READY:
                summary["agents_by_type"][agent_type]["active"] += 1
                summary["estimated_cost_per_search"] += info.cost_per_request
        
        # Gruppiere nach Capabilities
        for capability in AgentCapability:
            agents_with_capability = [
                info.name for info in self.agent_info.values()
                if capability in info.capabilities and info.status == AgentStatus.READY
            ]
            if agents_with_capability:
                summary["agents_by_capability"][capability.value] = agents_with_capability
        
        # Detaillierte Informationen
        for name, info in self.agent_info.items():
            summary["details"][name] = {
                "type": info.type,
                "status": info.status.value,
                "capabilities": [cap.value for cap in info.capabilities],
                "api_required": info.api_required,
                "api_key_present": info.api_key_present,
                "error": info.error_message,
                "statistics": {
                    "requests": info.requests_made,
                    "success_rate": f"{info.success_rate:.1%}",
                    "avg_response_time": f"{info.average_response_time:.2f}s",
                    "cost_per_request": f"${info.cost_per_request:.3f}"
                }
            }
        
        return summary
    
    def get_agents_by_capability(self, capability: AgentCapability) -> List[str]:
        """Gibt alle aktiven Agenten mit einer bestimmten Capability zurück"""
        return [
            name for name, info in self.agent_info.items()
            if capability in info.capabilities and info.status == AgentStatus.READY
        ]
    
    def get_fallback_agents(self, primary_agent: str) -> List[str]:
        """Gibt Fallback-Agenten für einen primären Agenten zurück"""
        if primary_agent not in self.agent_info:
            return []
        
        primary_info = self.agent_info[primary_agent]
        fallback_agents = []
        
        # Suche Agenten mit ähnlichen Capabilities
        for name, info in self.agent_info.items():
            if name == primary_agent or info.status != AgentStatus.READY:
                continue
            
            # Prüfe Capability-Überlappung
            common_capabilities = set(primary_info.capabilities) & set(info.capabilities)
            if common_capabilities:
                # Priorität basierend auf Anzahl gemeinsamer Capabilities
                priority = len(common_capabilities)
                fallback_agents.append((priority, name))
        
        # Sortiere nach Priorität
        fallback_agents.sort(reverse=True)
        return [name for _, name in fallback_agents]
    
    def update_agent_stats(self, agent_name: str, success: bool, response_time: float) -> None:
        """Aktualisiert Statistiken eines Agenten"""
        if agent_name not in self.agent_info:
            return
        
        info = self.agent_info[agent_name]
        info.requests_made += 1
        info.last_used = datetime.now()
        
        # Aktualisiere Erfolgsrate (gleitender Durchschnitt)
        if info.requests_made == 1:
            info.success_rate = 1.0 if success else 0.0
        else:
            info.success_rate = ((info.success_rate * (info.requests_made - 1)) + 
                               (1.0 if success else 0.0)) / info.requests_made
        
        # Aktualisiere durchschnittliche Antwortzeit
        if success:
            if info.average_response_time == 0:
                info.average_response_time = response_time
            else:
                info.average_response_time = ((info.average_response_time * (info.requests_made - 1)) + 
                                            response_time) / info.requests_made
    
    def get_cost_estimate(self, agents_to_use: List[str]) -> float:
        """Schätzt die Kosten für eine Suche mit bestimmten Agenten"""
        total_cost = 0.0
        for agent_name in agents_to_use:
            if agent_name in self.agent_info:
                total_cost += self.agent_info[agent_name].cost_per_request
        return total_cost
    
    def get_health_report(self) -> Dict[str, Any]:
        """Gibt einen Gesundheitsbericht des Systems zurück"""
        report = {
            "system_health": "healthy",
            "warnings": [],
            "errors": [],
            "recommendations": []
        }
        
        # Prüfe kritische Bedingungen
        active_agents = sum(1 for info in self.agent_info.values() if info.status == AgentStatus.READY)
        
        if active_agents == 0:
            report["system_health"] = "critical"
            report["errors"].append("Keine aktiven Agenten verfügbar!")
        elif active_agents < 3:
            report["system_health"] = "degraded"
            report["warnings"].append(f"Nur {active_agents} aktive Agenten verfügbar")
        
        # Prüfe Capabilities
        for capability in AgentCapability:
            agents_with_cap = self.get_agents_by_capability(capability)
            if not agents_with_cap and capability in [
                AgentCapability.WEB_SEARCH,
                AgentCapability.WEB_SCRAPING
            ]:
                report["warnings"].append(f"Keine Agenten für {capability.value} verfügbar")
        
        # Empfehlungen
        if not any(info.api_key_present for info in self.agent_info.values() if info.api_required):
            report["recommendations"].append(
                "Konfigurieren Sie API-Keys in der .env Datei für erweiterte Funktionalität"
            )
        
        # Performance-Warnungen
        slow_agents = [
            name for name, info in self.agent_info.items()
            if info.average_response_time > 30.0 and info.requests_made > 10
        ]
        if slow_agents:
            report["warnings"].append(
                f"Langsame Agenten erkannt: {', '.join(slow_agents)}"
            )
        
        return report
    
    def format_status_table(self) -> str:
        """Formatiert Status als Tabelle für Console-Output"""
        lines = []
        lines.append("\n" + "="*80)
        lines.append("AGENT STATUS DASHBOARD")
        lines.append("="*80)
        lines.append(f"{'Agent':<15} {'Type':<10} {'Status':<10} {'API Key':<10} {'Success':<10} {'Avg Time':<10}")
        lines.append("-"*80)
        
        for name, info in sorted(self.agent_info.items()):
            status_symbol = {
                AgentStatus.READY: "✓",
                AgentStatus.DISABLED: "✗",
                AgentStatus.ERROR: "⚠",
                AgentStatus.RUNNING: "⟳",
                AgentStatus.RATE_LIMITED: "⏱"
            }.get(info.status, "?")
            
            api_status = "✓" if info.api_key_present else "✗" if info.api_required else "-"
            success_rate = f"{info.success_rate:.0%}" if info.requests_made > 0 else "-"
            avg_time = f"{info.average_response_time:.1f}s" if info.average_response_time > 0 else "-"
            
            lines.append(
                f"{name:<15} {info.type:<10} {status_symbol:<10} {api_status:<10} {success_rate:<10} {avg_time:<10}"
            )
        
        lines.append("-"*80)
        
        # Zusammenfassung
        summary = self.get_status_summary()
        lines.append(f"Gesamt: {summary['total_agents']} | "
                    f"Aktiv: {summary['active_agents']} | "
                    f"Deaktiviert: {summary['disabled_agents']} | "
                    f"Fehler: {summary['error_agents']}")
        lines.append(f"Geschätzte Kosten pro Suche: ${summary['estimated_cost_per_search']:.3f}")
        lines.append("="*80)
        
        return "\n".join(lines)
    
    async def test_agent(self, agent_name: str) -> Tuple[bool, str]:
        """Testet einen einzelnen Agenten"""
        if agent_name not in self.agent_instances:
            return False, f"Agent {agent_name} nicht initialisiert"
        
        try:
            agent = self.agent_instances[agent_name]
            # Einfacher Test mit validate_credentials
            result = await agent.validate_credentials()
            if result:
                return True, f"Agent {agent_name} funktioniert einwandfrei"
            else:
                return False, f"Agent {agent_name} Validierung fehlgeschlagen"
        except Exception as e:
            return False, f"Agent {agent_name} Test-Fehler: {str(e)}"
    
    async def test_all_agents(self) -> Dict[str, Tuple[bool, str]]:
        """Testet alle initialisierten Agenten"""
        results = {}
        for agent_name in self.agent_instances:
            results[agent_name] = await self.test_agent(agent_name)
        return results