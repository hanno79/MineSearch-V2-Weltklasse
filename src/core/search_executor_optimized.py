"""
Author: rahn
Datum: 23.06.2025
Version: 2.0
Beschreibung: Optimierter Search Executor mit Performance-Verbesserungen
"""

import asyncio
from typing import List, Dict, Optional, Any, Callable
from datetime import datetime
import time

from src.agents.base_agent import BaseAgent, MineQuery, SearchResult
from .cancellation import CancellationToken, CancellationException
from .logger import get_logger
from .performance_optimizer import SearchOptimizer, PerformanceMonitor


class OptimizedSearchExecutor:
    """Optimierter Search Executor mit Caching und Batching"""
    
    def __init__(self):
        self.logger = get_logger("search_executor_optimized")
        self.optimizer = SearchOptimizer()
        self.performance_monitor = PerformanceMonitor()
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
        Führt eine optimierte Suche mit den gegebenen Agenten aus
        
        Features:
        - Result Caching
        - Connection Pooling
        - Batch Processing
        - Performance Monitoring
        """
        if not agents:
            self.logger.warning("Keine Agenten für Suche verfügbar")
            return []
        
        search_params = search_params or {}
        use_cache = search_params.get('use_cache', True)
        max_concurrent = search_params.get('max_concurrent', 10)
        
        self._report_status(f"Starte optimierte Suche mit {len(agents)} Agenten", status_callback)
        
        try:
            # Nutze optimierte Suche
            results = await self.performance_monitor.measure_async(
                "total_search_time",
                self.optimizer.optimize_agent_search(
                    agents=agents,
                    query=query,
                    use_cache=use_cache,
                    max_concurrent=max_concurrent
                )
            )
            
            # Filtere und validiere Ergebnisse
            valid_results = self._validate_results(results)
            
            # Berichte Status
            self._report_status(
                f"Optimierte Suche abgeschlossen: {len(valid_results)} Ergebnisse gefunden",
                status_callback
            )
            
            # Zeige Performance-Stats
            if search_params.get('show_stats', False):
                stats = self.optimizer.get_performance_stats()
                self.logger.info(f"Performance Stats: {stats}")
            
            return valid_results
            
        except CancellationException:
            self.logger.info("Suche wurde abgebrochen")
            raise
        except Exception as e:
            self.logger.error(f"Fehler bei optimierter Suche: {e}")
            raise
    
    def _validate_results(self, results: List[Any]) -> List[SearchResult]:
        """Validiert und filtert Suchergebnisse"""
        valid_results = []
        
        for result in results:
            if isinstance(result, SearchResult):
                valid_results.append(result)
            elif isinstance(result, list):
                # Verschachtelte Listen auflösen
                for sub_result in result:
                    if isinstance(sub_result, SearchResult):
                        valid_results.append(sub_result)
        
        return valid_results
    
    async def execute_bulk_search(
        self,
        agents: List[BaseAgent],
        queries: List[MineQuery],
        max_concurrent_queries: int = 3,
        status_callback: Optional[Callable] = None
    ) -> Dict[str, List[SearchResult]]:
        """
        Führt mehrere Suchen gleichzeitig aus
        
        Returns:
            Dictionary mit mine_name als Key und Ergebnissen als Value
        """
        self.logger.info(f"Starte Bulk-Suche für {len(queries)} Minen")
        results = {}
        
        # Erstelle Tasks für alle Queries
        search_tasks = []
        for query in queries:
            async def search_single(q=query):
                try:
                    mine_results = await self.execute_search(
                        agents=agents,
                        query=q,
                        search_params={'use_cache': True, 'max_concurrent': 5}
                    )
                    return q.mine_name, mine_results
                except Exception as e:
                    self.logger.error(f"Fehler bei {q.mine_name}: {e}")
                    return q.mine_name, []
            
            search_tasks.append(search_single())
        
        # Führe mit Concurrency-Limit aus
        semaphore = asyncio.Semaphore(max_concurrent_queries)
        
        async def run_with_limit(task):
            async with semaphore:
                return await task
        
        # Sammle Ergebnisse
        task_results = await asyncio.gather(
            *[run_with_limit(task) for task in search_tasks],
            return_exceptions=True
        )
        
        # Verarbeite Ergebnisse
        for result in task_results:
            if isinstance(result, tuple) and len(result) == 2:
                mine_name, mine_results = result
                results[mine_name] = mine_results
        
        self.logger.info(f"Bulk-Suche abgeschlossen: {len(results)} Minen verarbeitet")
        return results
    
    async def warmup_cache(
        self,
        agents: List[BaseAgent],
        common_queries: List[MineQuery]
    ):
        """Wärmt den Cache mit häufigen Queries auf"""
        self.logger.info(f"Wärme Cache auf mit {len(common_queries)} Queries")
        
        for query in common_queries:
            try:
                await self.execute_search(
                    agents=agents,
                    query=query,
                    search_params={'use_cache': True, 'show_stats': False}
                )
            except Exception as e:
                self.logger.error(f"Cache-Warmup fehlgeschlagen für {query.mine_name}: {e}")
        
        cache_stats = self.optimizer.result_cache.get_stats()
        self.logger.info(f"Cache-Warmup abgeschlossen. Cache-Größe: {cache_stats['size']}")
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Erstellt einen detaillierten Performance-Report"""
        stats = self.optimizer.get_performance_stats()
        
        report = {
            'cache_performance': stats['cache'],
            'search_metrics': stats['metrics'],
            'recommendations': []
        }
        
        # Generiere Empfehlungen
        if stats['cache']['hit_rate'] < 0.3:
            report['recommendations'].append(
                "Cache-Hit-Rate niedrig. Erwäge längere TTL oder Pre-Warming."
            )
        
        # Analysiere langsame Agenten
        slow_agents = []
        for agent_metric, values in stats['metrics'].items():
            if 'search_' in agent_metric and values.get('avg', 0) > 10:
                slow_agents.append(agent_metric.replace('search_', ''))
        
        if slow_agents:
            report['recommendations'].append(
                f"Langsame Agenten gefunden: {', '.join(slow_agents)}. "
                f"Erwäge Timeout-Anpassung oder Parallelisierung."
            )
        
        return report
    
    async def cleanup(self):
        """Cleanup-Ressourcen"""
        await self.optimizer.cleanup()
    
    def _report_status(self, message: str, callback: Optional[Callable]):
        """Berichtet Status über Callback"""
        self.logger.info(message)
        if callback:
            try:
                callback(message)
            except Exception as e:
                self.logger.error(f"Error in status callback: {e}")