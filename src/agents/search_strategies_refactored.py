"""
Author: rahn
Datum: 22.06.2025
Version: 2.0
Beschreibung: Refactored Search Strategies mit modularem Aufbau
"""

from typing import List, Dict, Optional, Any, Callable
import asyncio
import logging

from .search_strategies_core import (
    SearchStrategy, SearchContext, StrategyAnalysis,
    PREDEFINED_STRATEGIES
)
from .search_strategies_analyzer import StrategyAnalyzer
from .search_strategies_executor import StrategyExecutor
from src.core.logger import get_logger


class SearchStrategies:
    """
    Zentrale Verwaltung von Such-Strategien
    
    Refactored mit klarer Trennung von:
    - Core: Definitionen und Datenstrukturen
    - Analyzer: Kontext-Analyse und Strategie-Auswahl
    - Executor: Ausführung der Strategien
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or get_logger("search_strategies")
        self.analyzer = StrategyAnalyzer()
        self.executor = StrategyExecutor(self.logger)
        
        # State
        self.active_strategy: Optional[SearchStrategy] = None
        self.search_history = []
        
    def select_strategy(self, 
                       mine_name: str,
                       country: str,
                       region: str,
                       required_fields: List[str],
                       available_agents: List[str],
                       time_constraint: Optional[int] = None) -> SearchStrategy:
        """
        Wählt optimale Strategie basierend auf Kontext
        
        Delegiert an Analyzer für intelligente Auswahl
        """
        # Kontext erstellen
        context = SearchContext(
            mine_name=mine_name,
            country=country,
            region=region,
            required_fields=required_fields,
            available_agents=available_agents,
            time_constraint=time_constraint,
            previous_results=self._get_previous_results_count(mine_name),
            search_iteration=self._get_search_iteration(mine_name)
        )
        
        # Strategie auswählen
        strategy = self.analyzer.select_strategy(context)
        self.active_strategy = strategy
        
        self.logger.info(f"Strategie gewählt: {strategy.name}")
        
        return strategy
    
    async def execute_strategy(self,
                             strategy: SearchStrategy,
                             search_func: Callable,
                             mine_query: Any,
                             available_agents: List[str]) -> Dict[str, Any]:
        """
        Führt Such-Strategie aus
        
        Delegiert an Executor für robuste Ausführung
        """
        if not strategy:
            strategy = self.active_strategy
            
        if not strategy:
            raise ValueError("Keine Strategie ausgewählt")
        
        # Ausführung
        result = await self.executor.execute_strategy(
            strategy,
            search_func,
            mine_query,
            available_agents
        )
        
        # History aktualisieren
        self.search_history.append({
            "mine_name": mine_query.mine_name,
            "strategy": strategy.name,
            "timestamp": result["timestamp"],
            "results_count": result["metrics"]["total_results"]
        })
        
        return result
    
    def get_strategy_by_name(self, name: str) -> Optional[SearchStrategy]:
        """Holt Strategie nach Name"""
        return self.analyzer.strategies.get(name)
    
    def add_custom_strategy(self, name: str, strategy: SearchStrategy):
        """Fügt benutzerdefinierte Strategie hinzu"""
        self.analyzer.add_custom_strategy(name, strategy)
        self.logger.info(f"Custom Strategie hinzugefügt: {name}")
    
    def get_recommendation(self,
                          mine_name: str,
                          country: str,
                          region: str,
                          required_fields: List[str],
                          available_agents: List[str],
                          time_constraint: Optional[int] = None) -> Dict[str, Any]:
        """
        Gibt detaillierte Strategie-Empfehlung
        
        Nützlich für UI/Debugging
        """
        context = SearchContext(
            mine_name=mine_name,
            country=country,
            region=region,
            required_fields=required_fields,
            available_agents=available_agents,
            time_constraint=time_constraint
        )
        
        return self.analyzer.get_strategy_recommendation(context)
    
    def adapt_strategy(self, 
                      current_results: int,
                      time_remaining: Optional[int] = None) -> Optional[SearchStrategy]:
        """
        Passt Strategie basierend auf bisherigen Ergebnissen an
        
        Für iterative Verbesserung während der Suche
        """
        if not self.active_strategy:
            return None
        
        # Einfache Heuristik für Anpassung
        if current_results < 5 and self.active_strategy.depth.value < 3:
            # Upgrade zu tieferer Suche
            deeper_strategies = [
                s for s in self.analyzer.strategies.values()
                if s.depth.value > self.active_strategy.depth.value
            ]
            
            if deeper_strategies and (not time_remaining or time_remaining > 300):
                new_strategy = deeper_strategies[0]
                self.logger.info(f"Strategie-Upgrade: {self.active_strategy.name} -> {new_strategy.name}")
                self.active_strategy = new_strategy
                return new_strategy
        
        return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Gibt Statistiken zurück"""
        exec_stats = self.executor.get_execution_stats()
        
        # Strategie-Nutzung aus History
        strategy_usage = {}
        for entry in self.search_history:
            strategy = entry["strategy"]
            strategy_usage[strategy] = strategy_usage.get(strategy, 0) + 1
        
        return {
            "execution_stats": exec_stats,
            "strategy_usage": strategy_usage,
            "total_searches": len(self.search_history),
            "active_strategy": self.active_strategy.name if self.active_strategy else None
        }
    
    async def cancel_active_searches(self):
        """Bricht aktive Suchen ab"""
        await self.executor.cancel_active_searches()
    
    def _get_previous_results_count(self, mine_name: str) -> int:
        """Zählt vorherige Ergebnisse für Mine"""
        return sum(
            entry["results_count"] 
            for entry in self.search_history
            if entry["mine_name"] == mine_name
        )
    
    def _get_search_iteration(self, mine_name: str) -> int:
        """Zählt Suchiterationen für Mine"""
        return sum(
            1 for entry in self.search_history
            if entry["mine_name"] == mine_name
        ) + 1
    
    # Convenience Methods für häufige Strategien
    
    def quick_search_strategy(self) -> SearchStrategy:
        """Schnelle Suche für erste Ergebnisse"""
        return PREDEFINED_STRATEGIES["quick_scan"]
    
    def deep_research_strategy(self) -> SearchStrategy:
        """Tiefe Suche für umfassende Ergebnisse"""
        return PREDEFINED_STRATEGIES["deep_research"]
    
    def government_strategy(self) -> SearchStrategy:
        """Regierungs- und offizielle Quellen"""
        return PREDEFINED_STRATEGIES["government_focus"]