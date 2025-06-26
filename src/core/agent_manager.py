"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Agent Manager für MineSearch - verwaltet Agent-Initialisierung und -Status
# ÄNDERUNG 27.06.2025: SessionManager wird explizit übergeben
"""
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime

from src.agents.base_agent import BaseAgent, AgentStatus
from src.agents.factory import AgentFactory
from src.agents.openrouter.models import ModelRegistry
from src.agents.openrouter.utils import parse_model_id, extract_model_key_from_agent_type, find_model_by_key
from .config import Config
from .logger import get_logger


class AgentManager:
    """Verwaltet die Erstellung, Initialisierung und den Status von Agenten"""
    
    def __init__(self, config: Config, session_manager):
        self.config = config
        self.session_manager = session_manager
        self.agents: Dict[str, BaseAgent] = {}
        self.active_agents: List[str] = []
        self.logger = get_logger("agent_manager")
        self._initialized = False
        self._init_stats: Dict[str, Dict] = {}
        
    async def initialize_agents(self, status_callback=None) -> bool:
        """Initialisiert alle verfügbaren Agenten"""
        if self._initialized:
            return True
            
        self._report_status("Initialisiere Agent Manager...", status_callback)
        
        # Hole verfügbare Agenten
        available_agents = AgentFactory.get_available_agents(self.config)
        available_count = len([a for a, v in available_agents.items() if v])
        self._report_status(f"Gefunden: {available_count} verfügbare Agenten", status_callback)
        
        # Erstelle und initialisiere Agenten
        init_tasks = []
        for agent_type, is_available in available_agents.items():
            if is_available:
                agent = self._create_agent(agent_type)
                if agent:
                    self.agents[agent_type] = agent
                    # ÄNDERUNG 26.06.2025: Registriere Cancellation Cleanup
                    if hasattr(agent, 'set_cancellation_cleanup'):
                        async def cleanup_on_cancel(agent_id=agent_type):
                            await self.session_manager.cancel_agent_session(agent_id, "Search cancelled")
                        agent.set_cancellation_cleanup(cleanup_on_cancel)
                    init_tasks.append(self._init_agent(agent_type, agent))
        
        # Initialisiere alle Agenten parallel
        if init_tasks:
            init_results = await asyncio.gather(*init_tasks, return_exceptions=True)
            
            # Verarbeite Ergebnisse
            successful = 0
            for agent_type, result in zip(self.agents.keys(), init_results):
                if isinstance(result, Exception):
                    self.logger.error(f"Fehler bei {agent_type}: {result}")
                    self._init_stats[agent_type] = {
                        'status': 'failed',
                        'error': str(result),
                        'timestamp': datetime.now()
                    }
                elif result:
                    successful += 1
                    self.active_agents.append(agent_type)
                    self._init_stats[agent_type] = {
                        'status': 'success',
                        'timestamp': datetime.now()
                    }
            
            self._report_status(
                f"✅ {successful}/{len(init_tasks)} Agenten erfolgreich initialisiert",
                status_callback
            )
            
            # Log aktive Agenten
            if self.active_agents:
                self.logger.info(f"Aktive Agenten: {', '.join(self.active_agents)}")
            
            self._initialized = True
            return successful > 0
        
        return False
    
    def _create_agent(self, agent_type: str) -> Optional[BaseAgent]:
        """Erstellt einen einzelnen Agenten"""
        try:
            # Handle OpenRouter models
            if agent_type.startswith("openrouter_"):
                return self._create_openrouter_agent(agent_type)
            else:
                return AgentFactory.create_agent(agent_type, self.config, session_manager=self.session_manager)
        except Exception as e:
            self.logger.error(f"Fehler beim Erstellen von Agent {agent_type}: {e}")
            return None
    
    def _create_openrouter_agent(self, agent_type: str) -> Optional[BaseAgent]:
        """Spezielle Behandlung für OpenRouter Agenten"""
        from src.agents.openrouter_agent import OpenRouterAgent
        
        model_suffix = agent_type.replace("openrouter_", "")
        model_id = None
        
        # Search in both FREE_MODELS and PREMIUM_MODELS using robust parser
        all_models = {**ModelRegistry.get_free_models(), **ModelRegistry.get_premium_models()}
        model_id, _ = find_model_by_key(model_suffix, all_models)
        
        if model_id:
            return AgentFactory.create_agent(agent_type, self.config, session_manager=self.session_manager, model_id=model_id)
        else:
            self.logger.warning(f"Model ID not found for {agent_type}")
            return None
    
    async def _init_agent(self, agent_type: str, agent: BaseAgent) -> bool:
        """Initialisiert einen einzelnen Agenten"""
        try:
            self.logger.info(f"Initialisiere {agent_type}...")
            await agent.initialize()
            return True
        except Exception as e:
            self.logger.error(f"Initialisierung fehlgeschlagen für {agent_type}: {e}")
            return False
    
    def get_agent(self, agent_type: str) -> Optional[BaseAgent]:
        """Gibt einen spezifischen Agenten zurück"""
        return self.agents.get(agent_type)
    
    def get_active_agents(self) -> List[BaseAgent]:
        """Gibt alle aktiven Agenten zurück"""
        return [self.agents[agent_type] for agent_type in self.active_agents]
    
    def get_all_agents(self) -> List[BaseAgent]:
        """Gibt alle verfügbaren Agenten zurück (nicht nur die aktiven)"""
        return list(self.agents.values())
    
    def set_active_agents(self, agent_types: List[str]):
        """Setzt die Liste der aktiven Agenten"""
        self.active_agents = []
        for agent_type in agent_types:
            if agent_type in self.agents:
                self.active_agents.append(agent_type)
            else:
                self.logger.warning(f"Agent {agent_type} nicht verfügbar")
        
        self.logger.info(f"Aktive Agenten gesetzt: {self.active_agents}")
    
    def get_agent_statistics(self) -> Dict[str, Dict[str, Any]]:
        """Gibt Statistiken über alle Agenten zurück"""
        stats = {}
        for agent_type, agent in self.agents.items():
            stats[agent_type] = {
                "name": agent.name,
                "status": agent.status.value if hasattr(agent, 'status') else 'unknown',
                "active": agent_type in self.active_agents,
                "init_status": self._init_stats.get(agent_type, {})
            }
        return stats
    
    async def cleanup_agents(self):
        """Räumt alle Agenten auf"""
        self.logger.info("Räume Agenten auf...")
        
        cleanup_tasks = []
        for agent_type, agent in self.agents.items():
            if hasattr(agent, 'cleanup'):
                cleanup_tasks.append(agent.cleanup())
        
        if cleanup_tasks:
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)
        
        self.agents.clear()
        self.active_agents.clear()
        self._initialized = False
        self.logger.info("Alle Agenten aufgeräumt")
    
    def _report_status(self, message: str, callback=None):
        """Berichtet Status über Callback"""
        self.logger.info(message)
        if callback:
            try:
                callback(message)
            except Exception as e:
                self.logger.error(f"Error in status callback: {e}")