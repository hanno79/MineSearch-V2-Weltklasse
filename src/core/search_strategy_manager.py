"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Search Strategy Manager für verschiedene Such-Strategien
"""
from typing import List, Dict, Optional, Any, Protocol
from abc import abstractmethod
import asyncio

from src.agents.base_agent import BaseAgent, MineQuery, SearchResult
from src.agents.staged_search import StagedSearchStrategy
from src.agents.research_orchestrator import ResearchOrchestrator
from .cancellation import CancellationToken
from .logger import get_logger


class SearchStrategy(Protocol):
    """Protocol für Such-Strategien"""
    
    @abstractmethod
    async def execute(
        self,
        query: MineQuery,
        agents: List[BaseAgent],
        params: Dict[str, Any],
        status_callback=None,
        cancellation_token: Optional[CancellationToken] = None
    ) -> List[SearchResult]:
        """Führt Such-Strategie aus"""
        pass


class StandardSearchStrategy:
    """Standard Such-Strategie - einfache parallele Suche"""
    
    def __init__(self, search_executor):
        self.search_executor = search_executor
        self.logger = get_logger("standard_search")
        
    async def execute(
        self,
        query: MineQuery,
        agents: List[BaseAgent],
        params: Dict[str, Any],
        status_callback=None,
        cancellation_token: Optional[CancellationToken] = None
    ) -> List[SearchResult]:
        """Führt Standard-Suche aus"""
        self.logger.info(f"Starte Standard-Suche für {query.mine_name}")
        
        # Führe Suche mit allen Agenten aus
        results = await self.search_executor.execute_search(
            agents=agents,
            query=query,
            search_params=params,
            status_callback=status_callback,
            cancellation_token=cancellation_token
        )
        
        return results


class EnhancedStagedSearchStrategy:
    """Erweiterte Staged Search Strategie"""
    
    def __init__(self, staged_search: StagedSearchStrategy, source_discovery):
        self.staged_search = staged_search
        self.source_discovery = source_discovery
        self.logger = get_logger("staged_search")
        
    async def execute(
        self,
        query: MineQuery,
        agents: List[BaseAgent],
        params: Dict[str, Any],
        status_callback=None,
        cancellation_token: Optional[CancellationToken] = None
    ) -> List[SearchResult]:
        """Führt Staged Search mit Source Discovery aus"""
        self.logger.info(f"Starte Staged Search für {query.mine_name}")
        
        all_results = []
        
        # Phase 0: Source Discovery
        if params.get('enable_source_discovery', True):
            sources = await self.source_discovery.discover_sources(
                query=query,
                agents=agents,
                status_callback=status_callback,
                cancellation_token=cancellation_token
            )
            
            # Füge Quellen zu Params hinzu
            params['discovered_sources'] = sources
        
        # Führe Staged Search aus
        stage_results = await self.staged_search.execute_staged_search(
            query=query,
            agents=agents,
            discovered_sources=params.get('discovered_sources', []),
            cancellation_token=cancellation_token
        )
        
        all_results.extend(stage_results)
        
        return all_results


class DeepResearchStrategy:
    """Deep Research Strategie mit Research Orchestrator"""
    
    def __init__(self, research_orchestrator: Optional[ResearchOrchestrator] = None):
        self.research_orchestrator = research_orchestrator
        self.logger = get_logger("deep_research")
        
    async def execute(
        self,
        query: MineQuery,
        agents: List[BaseAgent],
        params: Dict[str, Any],
        status_callback=None,
        cancellation_token: Optional[CancellationToken] = None
    ) -> List[SearchResult]:
        """Führt Deep Research aus"""
        if not self.research_orchestrator:
            self.logger.warning("Research Orchestrator nicht verfügbar")
            return []
        
        self.logger.info(f"Starte Deep Research für {query.mine_name}")
        
        # Research Orchestrator verwenden
        if hasattr(self.research_orchestrator, 'research_mine'):
            results = await self.research_orchestrator.research_mine(query)
        else:
            # Fallback zu premium mining
            from src.agents.premium_mining_research import PremiumMiningResearch
            premium_agent = PremiumMiningResearch(agents=agents)
            results = await premium_agent.search(query)
        
        return results


class SearchStrategyManager:
    """Verwaltet und koordiniert verschiedene Such-Strategien"""
    
    def __init__(self, components: Dict[str, Any]):
        self.logger = get_logger("strategy_manager")
        
        # Initialisiere Strategien
        self.strategies = {
            'standard': StandardSearchStrategy(
                components['search_executor']
            ),
            'staged': EnhancedStagedSearchStrategy(
                components.get('staged_search', StagedSearchStrategy(None)),
                components['source_discovery']
            ),
            'deep_research': DeepResearchStrategy(
                components.get('research_orchestrator')
            )
        }
        
        self.default_strategy = 'staged'
        
    async def execute_search(
        self,
        strategy_name: str,
        query: MineQuery,
        agents: List[BaseAgent],
        params: Optional[Dict[str, Any]] = None,
        status_callback=None,
        cancellation_token: Optional[CancellationToken] = None
    ) -> List[SearchResult]:
        """
        Führt Suche mit der gewählten Strategie aus
        
        Args:
            strategy_name: Name der Strategie ('standard', 'staged', 'deep_research')
            query: Such-Query
            agents: Liste der Agenten
            params: Such-Parameter
            status_callback: Status Callback
            cancellation_token: Abbruch-Token
            
        Returns:
            Liste der Suchergebnisse
        """
        params = params or {}
        
        # Wähle Strategie
        strategy = self.strategies.get(strategy_name)
        if not strategy:
            self.logger.warning(
                f"Unbekannte Strategie '{strategy_name}', verwende '{self.default_strategy}'"
            )
            strategy = self.strategies[self.default_strategy]
        
        # Log Strategie
        self.logger.info(f"Verwende Such-Strategie: {strategy_name}")
        if status_callback:
            status_callback(f"🎯 Such-Strategie: {strategy_name.upper()}")
        
        try:
            # Führe Strategie aus
            results = await strategy.execute(
                query=query,
                agents=agents,
                params=params,
                status_callback=status_callback,
                cancellation_token=cancellation_token
            )
            
            return results
            
        except Exception as e:
            self.logger.error(f"Fehler in Strategie {strategy_name}: {e}")
            raise
    
    def get_available_strategies(self) -> List[str]:
        """Gibt verfügbare Strategien zurück"""
        return list(self.strategies.keys())
    
    def set_default_strategy(self, strategy_name: str):
        """Setzt die Standard-Strategie"""
        if strategy_name in self.strategies:
            self.default_strategy = strategy_name
            self.logger.info(f"Standard-Strategie gesetzt: {strategy_name}")
        else:
            self.logger.warning(f"Unbekannte Strategie: {strategy_name}")