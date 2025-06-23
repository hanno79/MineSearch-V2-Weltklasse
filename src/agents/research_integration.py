"""
Author: rahn
Datum: 18.06.2025
Version: 1.0
Beschreibung: Integration der spezialisierten Research-APIs in das Mining Research System
"""

from typing import Dict, List, Optional
import os
from dotenv import load_dotenv

from .base_agent import BaseAgent
from .deepseek_research_agent import DeepSeekResearchAgent
from .perplexity_deep_agent import PerplexityDeepAgent
from .research_orchestrator import ResearchOrchestrator
from src.core.logger import get_logger

# Load environment variables
load_dotenv()

logger = get_logger(__name__)


class ResearchAgentFactory:
    """Factory für die Erstellung spezialisierter Research-Agenten"""
    
    @staticmethod
    def create_research_agents(existing_agents: Dict[str, BaseAgent]) -> Dict[str, BaseAgent]:
        """
        Erstellt und fügt spezialisierte Research-Agenten hinzu
        
        Args:
            existing_agents: Dictionary mit bereits vorhandenen Agenten
            
        Returns:
            Erweitertes Dictionary mit Research-Agenten
        """
        research_agents = {}
        
        # DeepSeek Research Agent
        deepseek_key = os.getenv("DEEPSEEK_API_KEY")
        if deepseek_key:
            try:
                # Erstelle beide Varianten - Chat und Reasoner
                deepseek_chat = DeepSeekResearchAgent(
                    api_key=deepseek_key,
                    model="chat"
                )
                research_agents["deepseek_research"] = deepseek_chat
                
                # Optional: Reasoner Model für komplexe Aufgaben
                deepseek_reasoner = DeepSeekResearchAgent(
                    api_key=deepseek_key,
                    model="reasoner"
                )
                research_agents["deepseek_reasoner"] = deepseek_reasoner
                
                logger.info("DeepSeek Research Agents created successfully")
            except Exception as e:
                logger.error(f"Failed to create DeepSeek agents: {str(e)}")
        else:
            logger.info("No DEEPSEEK_API_KEY found - using DeepSeek via OpenRouter")
        
        # Perplexity Deep Research Agent
        perplexity_key = os.getenv("PERPLEXITY_API_KEY")
        if perplexity_key and "perplexity" in existing_agents:
            try:
                # Erweitere bestehenden Perplexity Agent
                perplexity_deep = PerplexityDeepAgent(
                    api_key=perplexity_key,
                    use_deep_research=True
                )
                research_agents["perplexity_deep"] = perplexity_deep
                
                logger.info("Perplexity Deep Research Agent created")
            except Exception as e:
                logger.error(f"Failed to create Perplexity Deep agent: {str(e)}")
        
        # Weitere Research-Agenten können hier hinzugefügt werden:
        # - Gemini Deep Research Agent
        # - OpenAI o1 Agent
        # etc.
        
        # Kombiniere mit bestehenden Agenten
        all_agents = {**existing_agents, **research_agents}
        
        return all_agents


class ResearchModeSelector:
    """Wählt den optimalen Research-Modus basierend auf der Anfrage"""
    
    def __init__(self, agents: Dict[str, BaseAgent]):
        self.agents = agents
        self.logger = get_logger(__name__)
        
        # Definiere Research-Modi
        self.research_modes = {
            "standard": {
                "description": "Standard-Suche mit mehreren Agenten",
                "agents": ["tavily", "perplexity", "exa", "scraper"],
                "best_for": ["quick_search", "basic_info"]
            },
            "deep_research": {
                "description": "Tiefgreifende Research mit spezialisierten Agenten",
                "agents": ["deepseek_research", "perplexity_deep", "claude", "gpt4"],
                "best_for": ["comprehensive", "complex_analysis", "missing_data"]
            },
            "reasoning": {
                "description": "Komplexe Reasoning-Aufgaben",
                "agents": ["deepseek_reasoner", "claude", "gpt4"],
                "best_for": ["conflicting_data", "analysis", "synthesis"]
            },
            "discovery": {
                "description": "Quellenentdeckung und initiale Recherche",
                "agents": ["tavily", "perplexity", "gemini"],
                "best_for": ["new_region", "unknown_mine", "source_discovery"]
            }
        }
    
    def select_research_mode(
        self,
        mine_name: str,
        country: str,
        required_fields: List[str],
        context: Optional[Dict] = None
    ) -> str:
        """
        Wählt den optimalen Research-Modus
        
        Args:
            mine_name: Name der Mine
            country: Land
            required_fields: Benötigte Felder
            context: Zusätzlicher Kontext
            
        Returns:
            Name des gewählten Research-Modus
        """
        # Analysiere Anforderungen
        needs_financial = any(
            field in required_fields 
            for field in ["sanierungskosten", "rehabilitation_cost", "closure_bond"]
        )
        
        needs_technical = any(
            field in required_fields
            for field in ["production", "reserves", "mine_type"]
        )
        
        is_complex = len(required_fields) > 10
        is_unknown = context and context.get("previous_searches", 0) == 0
        
        # Wähle Modus basierend auf Analyse
        if is_complex or (needs_financial and needs_technical):
            mode = "deep_research"
        elif is_unknown:
            mode = "discovery"
        elif context and context.get("conflicting_results", False):
            mode = "reasoning"
        else:
            mode = "standard"
        
        self.logger.info(
            f"Selected research mode '{mode}' for {mine_name} in {country}"
        )
        
        return mode
    
    def get_agents_for_mode(self, mode: str) -> List[str]:
        """Gibt die Agenten für einen Research-Modus zurück"""
        if mode in self.research_modes:
            # Filtere nur verfügbare Agenten
            available_agents = [
                agent for agent in self.research_modes[mode]["agents"]
                if agent in self.agents
            ]
            return available_agents
        return []


def integrate_research_orchestrator(
    agents: Dict[str, BaseAgent],
    enable_orchestration: bool = True
) -> Optional[ResearchOrchestrator]:
    """
    Integriert den Research Orchestrator
    
    Args:
        agents: Dictionary mit allen Agenten
        enable_orchestration: Ob Orchestrierung aktiviert werden soll
        
    Returns:
        ResearchOrchestrator Instanz oder None
    """
    if not enable_orchestration:
        return None
    
    try:
        orchestrator = ResearchOrchestrator(agents)
        logger.info(
            f"Research Orchestrator initialized with "
            f"{len(orchestrator.research_agents)} research agents"
        )
        return orchestrator
    except Exception as e:
        logger.error(f"Failed to initialize Research Orchestrator: {str(e)}")
        return None


# Beispiel-Integration in bestehenden Code:
def enhance_mining_search_with_research(
    original_search_function,
    agents: Dict[str, BaseAgent],
    use_research_mode: bool = True
):
    """
    Wrapper-Funktion die bestehende Suche mit Research-Funktionen erweitert
    
    Dies ist ein Beispiel wie die Research-Funktionen in bestehenden Code
    integriert werden können ohne große Änderungen.
    """
    
    # Erstelle Research-Agenten
    if use_research_mode:
        agents = ResearchAgentFactory.create_research_agents(agents)
    
    # Erstelle Mode Selector
    mode_selector = ResearchModeSelector(agents)
    
    # Optional: Research Orchestrator
    orchestrator = integrate_research_orchestrator(agents, use_research_mode)
    
    async def enhanced_search(query):
        """Enhanced search with research capabilities"""
        
        # Wähle Research-Modus
        mode = mode_selector.select_research_mode(
            query.mine_name,
            query.country,
            query.required_fields,
            {"previous_searches": 0}  # Context
        )
        
        # Wenn Deep Research Mode und Orchestrator verfügbar
        if mode == "deep_research" and orchestrator:
            logger.info("Using Research Orchestrator for deep research")
            result = await orchestrator.orchestrate_research(query)
            return result["results"]
        
        # Sonst nutze Standard-Suche mit ausgewählten Agenten
        selected_agents = mode_selector.get_agents_for_mode(mode)
        
        # Filtere Agenten für diese Suche
        filtered_agents = {
            name: agent for name, agent in agents.items()
            if name in selected_agents
        }
        
        # Führe Original-Suche mit gefilterten Agenten aus
        return await original_search_function(query, filtered_agents)
    
    return enhanced_search


# Konfigurationsbeispiel für Integration
RESEARCH_CONFIG = {
    "enable_deep_research": True,
    "enable_orchestration": True,
    "research_modes": {
        "auto": True,  # Automatische Modus-Auswahl
        "force_mode": None  # Oder "deep_research", "reasoning", etc.
    },
    "agent_priorities": {
        "deepseek_research": 1,
        "perplexity_deep": 2,
        "claude": 3,
        "gpt4": 4
    },
    "cost_optimization": {
        "prefer_free_agents": True,
        "max_premium_calls": 10
    }
}