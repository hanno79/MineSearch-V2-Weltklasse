"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Search Executor für MineSearch - führt Suchen mit Agenten aus
"""
import asyncio
from typing import List, Dict, Optional, Any, Callable
from datetime import datetime
import time

from src.agents.base_agent import BaseAgent, MineQuery, SearchResult
from .cancellation import CancellationToken, CancellationException
from .logger import get_logger


class SearchExecutor:
    """Führt Suchen mit verschiedenen Agenten aus"""
    
    def __init__(self):
        self.logger = get_logger("search_executor")
        self._search_stats = {}
        
    async def execute_search(
        self,
        agents: List[BaseAgent],
        query: MineQuery,
        search_params: Optional[Dict[str, Any]] = None,
        status_callback: Optional[Callable] = None,
        cancellation_token: Optional[CancellationToken] = None
    ) -> List[SearchResult]:
        """
        Führt eine Suche mit den gegebenen Agenten aus
        
        Args:
            agents: Liste der zu verwendenden Agenten
            query: Such-Query
            search_params: Zusätzliche Such-Parameter
            status_callback: Callback für Status-Updates
            cancellation_token: Token für Abbruch
            
        Returns:
            Liste der Suchergebnisse
        """
        if not agents:
            self.logger.warning("Keine Agenten für Suche verfügbar")
            return []
        
        search_params = search_params or {}
        self._report_status(f"Starte Suche mit {len(agents)} Agenten", status_callback)
        
        # Erstelle Such-Tasks
        search_tasks = []
        for agent in agents:
            if cancellation_token and cancellation_token.is_cancelled():
                break
                
            task = self._create_search_task(
                agent, query, cancellation_token, status_callback
            )
            search_tasks.append(task)
        
        # Führe Suchen aus
        if search_tasks:
            if search_params.get('parallel', True):
                results = await self._execute_parallel(search_tasks, cancellation_token)
            else:
                results = await self._execute_sequential(search_tasks, cancellation_token)
            
            # Sammle alle Ergebnisse
            all_results = []
            for result_list in results:
                if isinstance(result_list, list):
                    all_results.extend(result_list)
            
            self._report_status(
                f"Suche abgeschlossen: {len(all_results)} Ergebnisse gefunden",
                status_callback
            )
            
            return all_results
        
        return []
    
    async def _create_search_task(
        self,
        agent: BaseAgent,
        query: MineQuery,
        cancellation_token: Optional[CancellationToken],
        status_callback: Optional[Callable]
    ):
        """Erstellt einen Such-Task für einen Agenten"""
        agent_name = getattr(agent, 'name', type(agent).__name__)
        
        async def search_wrapper():
            start_time = time.time()
            try:
                self._report_status(f"🔍 {agent_name} startet Suche...", status_callback)
                
                results = await self._search_with_agent(
                    agent, query, cancellation_token
                )
                
                duration = time.time() - start_time
                self._record_stats(agent_name, len(results), duration, "success")
                
                if results:
                    self._report_status(
                        f"✅ {agent_name} fand {len(results)} Ergebnisse",
                        status_callback
                    )
                else:
                    self._report_status(
                        f"⚪ {agent_name} fand keine Ergebnisse",
                        status_callback
                    )
                
                return results
                
            except CancellationException:
                self._record_stats(agent_name, 0, time.time() - start_time, "cancelled")
                raise
            except Exception as e:
                duration = time.time() - start_time
                self._record_stats(agent_name, 0, duration, "error", str(e))
                self.logger.error(f"Fehler bei {agent_name}: {e}")
                self._report_status(f"❌ {agent_name} Fehler: {str(e)[:50]}...", status_callback)
                return []
        
        return search_wrapper()
    
    async def _search_with_agent(
        self,
        agent: BaseAgent,
        query: MineQuery,
        cancellation_token: Optional[CancellationToken]
    ) -> List[SearchResult]:
        """Führt Suche mit einem einzelnen Agenten aus"""
        try:
            # Check cancellation
            if cancellation_token and cancellation_token.is_cancelled():
                raise CancellationException("Search cancelled")
            
            # ÄNDERUNG 26.06.2025: Setze Cancellation Token im Agent
            if hasattr(agent, 'set_cancellation_token'):
                agent.set_cancellation_token(cancellation_token)
                self.logger.debug(f"Cancellation Token gesetzt für {agent.name}")
            
            # ÄNDERUNG 26.06.2025: Übergebe cancellation_token an Agent wenn unterstützt
            if hasattr(agent, 'search_mine_with_cancellation'):
                # Agent unterstützt direkte Cancellation
                search_task = asyncio.create_task(
                    agent.search_mine_with_cancellation(query, cancellation_token)
                )
            else:
                # Legacy: Verwende search_mine ohne direkte Cancellation
                # Der Agent sollte aber trotzdem den Token prüfen, wenn er gesetzt wurde
                search_task = asyncio.create_task(agent.search_mine(query))
            
            # Register task with global registry if available
            try:
                from src.core.global_cancellation_registry import get_global_cancellation_registry
                registry = get_global_cancellation_registry()
                search_id = getattr(cancellation_token, 'name', 'unknown')
                if search_id and search_id != 'unknown':
                    registry.register_task(search_id.replace('search_', ''), search_task)
            except:
                pass  # Registry nicht verfügbar
            
            # Wait with cancellation check
            while not search_task.done():
                if cancellation_token and cancellation_token.is_cancelled():
                    search_task.cancel()
                    # Give task time to cancel
                    try:
                        await asyncio.wait_for(search_task, timeout=0.1)
                    except (asyncio.TimeoutError, asyncio.CancelledError):
                        pass
                    raise CancellationException("Search cancelled")
                
                try:
                    await asyncio.wait_for(
                        asyncio.shield(search_task),
                        timeout=0.5  # Check every 500ms
                    )
                except asyncio.TimeoutError:
                    continue
            
            results = await search_task
            
            # Ensure results is a list
            if not isinstance(results, list):
                self.logger.warning(f"Agent returned non-list: {type(results)}")
                return []
            
            # Validate results
            valid_results = []
            for result in results:
                if isinstance(result, SearchResult):
                    valid_results.append(result)
                else:
                    self.logger.warning(f"Invalid result type: {type(result)}")
            
            return valid_results
            
        except CancellationException:
            raise
        except Exception as e:
            # ÄNDERUNG 23.06.2025: Erweiterte Fehlerdiagnose
            import traceback
            self.logger.error(f"Error in agent search: {e}")
            self.logger.error(f"Agent: {agent.name if hasattr(agent, 'name') else type(agent).__name__}")
            self.logger.error(f"Stack Trace:\n{traceback.format_exc()}")
            raise
    
    async def _execute_parallel(
        self,
        tasks: List,
        cancellation_token: Optional[CancellationToken]
    ) -> List:
        """Führt Tasks parallel aus"""
        # ÄNDERUNG 26.06.2025: Bei Cancellation alle Tasks abbrechen
        if cancellation_token:
            def cancel_all_tasks():
                for task in tasks:
                    if asyncio.iscoroutine(task):
                        # Task wurde noch nicht gestartet
                        pass
                    elif hasattr(task, 'cancel'):
                        task.cancel()
            
            cancellation_token.register_callback(cancel_all_tasks)
        
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _execute_sequential(
        self,
        tasks: List,
        cancellation_token: Optional[CancellationToken]
    ) -> List:
        """Führt Tasks sequentiell aus"""
        results = []
        for task in tasks:
            if cancellation_token and cancellation_token.is_cancelled():
                break
            try:
                result = await task
                results.append(result)
            except Exception as e:
                results.append(e)
        return results
    
    def _record_stats(
        self,
        agent_name: str,
        result_count: int,
        duration: float,
        status: str,
        error: Optional[str] = None
    ):
        """Zeichnet Such-Statistiken auf"""
        if agent_name not in self._search_stats:
            self._search_stats[agent_name] = []
        
        self._search_stats[agent_name].append({
            'timestamp': datetime.now(),
            'result_count': result_count,
            'duration': duration,
            'status': status,
            'error': error
        })
    
    def get_statistics(self) -> Dict[str, Any]:
        """Gibt Such-Statistiken zurück"""
        return self._search_stats.copy()
    
    def _report_status(self, message: str, callback: Optional[Callable]):
        """Berichtet Status über Callback"""
        self.logger.info(message)
        if callback:
            try:
                callback(message)
            except Exception as e:
                self.logger.error(f"Error in status callback: {e}")