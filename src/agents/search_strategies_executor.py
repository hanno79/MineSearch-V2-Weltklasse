"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Ausführung von Such-Strategien
"""

import asyncio
from typing import List, Dict, Any, Optional, Set, Callable
from datetime import datetime, timedelta
import logging

from .search_strategies_core import SearchStrategy, SearchScope, SearchDepth
from src.core.logger import get_logger


class StrategyExecutor:
    """Führt Such-Strategien aus"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or get_logger("strategy_executor")
        self.execution_history = []
        self.active_searches = {}
        self._search_semaphore = None
    
    async def execute_strategy(self,
                             strategy: SearchStrategy,
                             search_func: Callable,
                             mine_query: Any,
                             available_agents: List[str]) -> Dict[str, Any]:
        """
        Führt eine Such-Strategie aus
        
        Args:
            strategy: Die auszuführende Strategie
            search_func: Funktion zum Ausführen einzelner Suchen
            mine_query: Die Suchanfrage
            available_agents: Verfügbare Agenten
            
        Returns:
            Ausführungsergebnis mit Resultaten und Metriken
        """
        start_time = datetime.now()
        execution_id = f"{strategy.name}_{start_time.timestamp()}"
        
        self.logger.info(f"Starte Strategie-Ausführung: {strategy.name}")
        
        # Semaphore für parallele Suchen
        self._search_semaphore = asyncio.Semaphore(strategy.parallel_searches)
        
        try:
            # Agenten nach Präferenz filtern
            selected_agents = self._select_agents(
                strategy.agent_preferences,
                available_agents
            )
            
            if not selected_agents:
                self.logger.warning("Keine passenden Agenten verfügbar")
                return self._create_empty_result(strategy, "no_agents")
            
            # Timeouts berechnen
            timeout = strategy.time_budget
            agent_timeout = timeout // len(selected_agents) if selected_agents else 30
            
            # Parallele Ausführung mit Timeout
            results = await self._execute_parallel_searches(
                selected_agents,
                search_func,
                mine_query,
                agent_timeout,
                strategy.retry_strategy
            )
            
            # Ergebnisse aggregieren
            execution_time = (datetime.now() - start_time).total_seconds()
            
            execution_result = {
                "strategy": strategy.name,
                "execution_id": execution_id,
                "results": results,
                "metrics": {
                    "total_results": sum(len(r.get("results", [])) for r in results),
                    "successful_agents": len([r for r in results if r.get("success")]),
                    "failed_agents": len([r for r in results if not r.get("success")]),
                    "execution_time": execution_time,
                    "agents_used": selected_agents
                },
                "timestamp": datetime.now().isoformat()
            }
            
            # In History speichern
            self.execution_history.append(execution_result)
            
            return execution_result
            
        except asyncio.TimeoutError:
            self.logger.error(f"Strategie-Timeout nach {strategy.time_budget}s")
            return self._create_empty_result(strategy, "timeout")
            
        except Exception as e:
            self.logger.error(f"Strategie-Fehler: {e}")
            return self._create_empty_result(strategy, f"error: {str(e)}")
            
        finally:
            # Cleanup
            if execution_id in self.active_searches:
                del self.active_searches[execution_id]
    
    async def _execute_parallel_searches(self,
                                       agents: List[str],
                                       search_func: Callable,
                                       mine_query: Any,
                                       timeout: int,
                                       retry_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Führt parallele Suchen mit Retry-Logic aus"""
        tasks = []
        
        for agent in agents:
            task = self._execute_with_retry(
                agent,
                search_func,
                mine_query,
                timeout,
                retry_config
            )
            tasks.append(task)
        
        # Warte auf alle Tasks
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Exceptions zu Fehlern konvertieren
        processed_results = []
        for agent, result in zip(agents, results):
            if isinstance(result, Exception):
                processed_results.append({
                    "agent": agent,
                    "success": False,
                    "error": str(result),
                    "results": []
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def _execute_with_retry(self,
                                agent: str,
                                search_func: Callable,
                                mine_query: Any,
                                timeout: int,
                                retry_config: Dict[str, Any]) -> Dict[str, Any]:
        """Führt Suche mit Retry-Logic aus"""
        max_retries = retry_config.get("max_retries", 2)
        backoff = retry_config.get("backoff", 2)
        
        for attempt in range(max_retries + 1):
            try:
                # Rate limiting durch Semaphore
                async with self._search_semaphore:
                    self.logger.debug(f"Starte Suche mit {agent} (Versuch {attempt + 1})")
                    
                    # Suche mit Timeout ausführen
                    result = await asyncio.wait_for(
                        search_func(agent, mine_query),
                        timeout=timeout
                    )
                    
                    return {
                        "agent": agent,
                        "success": True,
                        "results": result,
                        "attempts": attempt + 1
                    }
                    
            except asyncio.TimeoutError:
                self.logger.warning(f"{agent} Timeout nach {timeout}s (Versuch {attempt + 1})")
                
            except Exception as e:
                self.logger.warning(f"{agent} Fehler: {e} (Versuch {attempt + 1})")
            
            # Exponential backoff vor Retry
            if attempt < max_retries:
                wait_time = backoff ** attempt
                await asyncio.sleep(wait_time)
        
        # Alle Versuche fehlgeschlagen
        return {
            "agent": agent,
            "success": False,
            "error": f"Failed after {max_retries + 1} attempts",
            "results": []
        }
    
    def _select_agents(self, 
                      preferences: List[str],
                      available: List[str]) -> List[str]:
        """Wählt Agenten basierend auf Präferenzen"""
        if "all" in preferences:
            return available
        
        selected = []
        for pref in preferences:
            # Exakte Übereinstimmung
            if pref in available:
                selected.append(pref)
            # Partial Match (z.B. "gpt" matches "gpt4")
            else:
                for agent in available:
                    if pref in agent or agent in pref:
                        if agent not in selected:
                            selected.append(agent)
        
        return selected
    
    def _create_empty_result(self, 
                           strategy: SearchStrategy,
                           reason: str) -> Dict[str, Any]:
        """Erstellt leeres Ergebnis"""
        return {
            "strategy": strategy.name,
            "execution_id": f"{strategy.name}_{datetime.now().timestamp()}",
            "results": [],
            "metrics": {
                "total_results": 0,
                "successful_agents": 0,
                "failed_agents": 0,
                "execution_time": 0,
                "agents_used": [],
                "failure_reason": reason
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Gibt Statistiken über Ausführungen zurück"""
        if not self.execution_history:
            return {"total_executions": 0}
        
        total_results = sum(
            e["metrics"]["total_results"] 
            for e in self.execution_history
        )
        
        avg_execution_time = sum(
            e["metrics"]["execution_time"] 
            for e in self.execution_history
        ) / len(self.execution_history)
        
        strategy_counts = {}
        for exec in self.execution_history:
            strategy = exec["strategy"]
            strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
        
        return {
            "total_executions": len(self.execution_history),
            "total_results_found": total_results,
            "average_execution_time": round(avg_execution_time, 2),
            "strategy_usage": strategy_counts,
            "last_execution": self.execution_history[-1]["timestamp"] if self.execution_history else None
        }
    
    async def cancel_active_searches(self):
        """Bricht aktive Suchen ab"""
        if self.active_searches:
            self.logger.info(f"Breche {len(self.active_searches)} aktive Suchen ab")
            
            for search_id, task in self.active_searches.items():
                if not task.done():
                    task.cancel()
            
            # Warte kurz auf Cleanup
            await asyncio.sleep(0.1)
            
            self.active_searches.clear()