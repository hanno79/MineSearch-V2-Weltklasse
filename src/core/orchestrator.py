"""
Author: rahn
Datum: 22.06.2025
Version: 2.0
Beschreibung: Refactored MineSearch Orchestrator - koordiniert alle Komponenten
"""
from typing import List, Dict, Any, Optional, Callable
import asyncio

from src.agents.base_agent import MineQuery, SearchResult
from src.data.aggregator import DataAggregator
from .config import Config
from .logger import get_logger
from .cancellation import CancellationToken, CancellationException

# Import refactored components
from .agent_manager import AgentManager
from .search_executor import SearchExecutor
from .source_discovery_service import SourceDiscoveryService
from .search_strategy_manager import SearchStrategyManager
from .source_manager import SourceManager


class MineSearchOrchestratorV2:
    """Refactored Orchestrator - koordiniert alle Such-Komponenten"""
    
    def __init__(self, config: Config, status_callback: Optional[Callable[[str], None]] = None):
        self.config = config
        self.logger = get_logger("orchestrator")
        self.status_callback = status_callback
        
        # Initialize components
        self.agent_manager = AgentManager(config)
        self.search_executor = SearchExecutor()
        self.source_manager = SourceManager()
        self.source_discovery = SourceDiscoveryService(self.source_manager)
        self.aggregator = DataAggregator()
        
        # Initialize strategy manager with components
        self.strategy_manager = SearchStrategyManager({
            'search_executor': self.search_executor,
            'source_discovery': self.source_discovery,
            'staged_search': self._get_staged_search(),
            'research_orchestrator': self._get_research_orchestrator()
        })
        
        self._initialized = False
        
        # Database manager
        from .database import get_db_manager
        self.db_manager = get_db_manager()
        
        # Kompatibilitäts-Attribute
        self.agents = {}  # Wird von agent_manager verwaltet
        self.active_agents = []  # Wird von agent_manager verwaltet
        self.coordinator = None  # Deprecated
        self.staged_search = self._get_staged_search()
        self.research_orchestrator = self._get_research_orchestrator()
    
    async def initialize(self) -> bool:
        """Initialisiert den Orchestrator und alle Agenten"""
        if self._initialized:
            return True
        
        self._report_status("🚀 Initialisiere MineSearch Orchestrator V2...")
        
        # Initialize agents
        success = await self.agent_manager.initialize_agents(self.status_callback)
        
        if success:
            self._initialized = True
            # Synchronisiere Agent-Referenzen für Kompatibilität
            self.agents = self.agent_manager.agents
            self.active_agents = self.agent_manager.active_agents
            self._report_status("✅ Orchestrator erfolgreich initialisiert")
        else:
            self._report_status("❌ Orchestrator-Initialisierung fehlgeschlagen")
        
        return success
    
    async def search_mine(
        self,
        query: MineQuery,
        search_params: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        Hauptmethode für Mine-Suche
        
        Args:
            query: Such-Query mit Mine-Informationen
            search_params: Zusätzliche Such-Parameter
            
        Returns:
            Liste der Suchergebnisse
        """
        if not self._initialized:
            await self.initialize()
        
        search_params = search_params or {}
        
        # Determine strategy
        strategy = search_params.get('strategy', 'staged')
        
        # Get active agents
        agent_types = search_params.get('agent_types', [])
        if agent_types:
            self.agent_manager.set_active_agents(agent_types)
        
        active_agents = self.agent_manager.get_active_agents()
        
        if not active_agents:
            self._report_status("❌ Keine aktiven Agenten verfügbar")
            return []
        
        # Get cancellation token
        cancellation_token = search_params.get('cancellation_token')
        
        try:
            # Execute search with chosen strategy
            results = await self.strategy_manager.execute_search(
                strategy_name=strategy,
                query=query,
                agents=active_agents,
                params=search_params,
                status_callback=self.status_callback,
                cancellation_token=cancellation_token
            )
            
            # Aggregate results
            aggregated_results = self.aggregator.aggregate_results(results)
            
            # Save to database if enabled
            if search_params.get('save_to_db', True):
                await self._save_results_to_db(query, aggregated_results)
            
            return aggregated_results
            
        except CancellationException:
            self._report_status("🛑 Suche abgebrochen")
            raise
        except Exception as e:
            self.logger.error(f"Fehler bei Suche: {e}")
            self._report_status(f"❌ Fehler: {str(e)}")
            raise
    
    async def search_mine_staged(
        self,
        query: MineQuery,
        search_params: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Kompatibilitäts-Methode für staged search"""
        search_params = search_params or {}
        search_params['strategy'] = 'staged'
        return await self.search_mine(query, search_params)
    
    async def search_mine_deep_research(
        self,
        query: MineQuery
    ) -> List[SearchResult]:
        """Kompatibilitäts-Methode für deep research"""
        return await self.search_mine(query, {'strategy': 'deep_research'})
    
    async def discover_sources(
        self,
        query: MineQuery,
        cancellation_token=None
    ) -> List:
        """Entdeckt Quellen für eine Mine"""
        agents = self.agent_manager.get_active_agents()
        
        sources = await self.source_discovery.discover_sources(
            query=query,
            agents=agents,
            status_callback=self.status_callback,
            cancellation_token=cancellation_token
        )
        
        return sources
    
    def set_active_agents(self, agent_types: List[str]):
        """Setzt aktive Agenten"""
        self.agent_manager.set_active_agents(agent_types)
    
    def get_agent_statistics(self) -> Dict[str, Dict[str, Any]]:
        """Gibt Agent-Statistiken zurück"""
        agent_stats = self.agent_manager.get_agent_statistics()
        search_stats = self.search_executor.get_statistics()
        
        # Kombiniere Statistiken
        combined_stats = {}
        for agent_type, stats in agent_stats.items():
            combined_stats[agent_type] = {
                **stats,
                'search_history': search_stats.get(stats.get('name', agent_type), [])
            }
        
        return combined_stats
    
    async def cleanup(self):
        """Räumt alle Ressourcen auf"""
        self._report_status("🧹 Räume Orchestrator auf...")
        await self.agent_manager.cleanup_agents()
        self._initialized = False
        self._report_status("✅ Orchestrator aufgeräumt")
    
    def _get_staged_search(self):
        """Holt Staged Search Strategie"""
        try:
            from src.agents.staged_search import StagedSearchStrategy
            return StagedSearchStrategy(self.config)
        except:
            return None
    
    def _get_research_orchestrator(self):
        """Holt Research Orchestrator"""
        try:
            from src.agents.research_orchestrator import ResearchOrchestrator
            return ResearchOrchestrator(self.config)
        except:
            return None
    
    async def _save_results_to_db(self, query: MineQuery, results: List[SearchResult]):
        """Speichert Ergebnisse in Datenbank"""
        try:
            # Implementation würde hier Ergebnisse in DB speichern
            pass
        except Exception as e:
            self.logger.error(f"Fehler beim Speichern in DB: {e}")
    
    def _report_status(self, message: str):
        """Berichtet Status über Callback"""
        self.logger.info(message)
        if self.status_callback:
            try:
                self.status_callback(message)
            except Exception as e:
                self.logger.error(f"Error in status callback: {e}")
    
    # Kompatibilitäts-Methoden (delegieren an neue Komponenten)
    
    async def _init_agent(self, agent_type: str, agent) -> bool:
        """Kompatibilität: Delegiert an AgentManager"""
        return await self.agent_manager._init_agent(agent_type, agent)
    
    async def _search_with_agent(self, agent, query, cancellation_token=None):
        """Kompatibilität: Delegiert an SearchExecutor"""
        return await self.search_executor._search_with_agent(agent, query, cancellation_token)
    
    async def _gather_search_tasks(self, tasks):
        """Kompatibilität: Delegiert an SearchExecutor"""
        return await self.search_executor._execute_parallel(tasks, None)
    
    def _determine_source_type(self, url: str, field_name: str = "") -> str:
        """Kompatibilität: Delegiert an SourceDiscoveryService"""
        return self.source_discovery._determine_source_type(url)


# Kompatibilitäts-Klasse
class MineSearchOrchestrator(MineSearchOrchestratorV2):
    """Alias für Kompatibilität"""
    pass