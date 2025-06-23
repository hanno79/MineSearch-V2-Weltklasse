"""
Author: rahn
Datum: 23.06.2025
Version: 1.0
Beschreibung: Performance-Optimierung für MineSearch
"""

import asyncio
import aiohttp
import time
from typing import List, Dict, Any, Optional, Callable, Set
from functools import lru_cache
from contextlib import asynccontextmanager
import json
import hashlib
from datetime import datetime, timedelta

from src.agents.base_agent import BaseAgent, MineQuery, SearchResult
from .logger import get_logger


class ConnectionPoolManager:
    """Verwaltet HTTP Connection Pools für bessere Performance"""
    
    def __init__(self):
        self.logger = get_logger("connection_pool")
        self._sessions: Dict[str, aiohttp.ClientSession] = {}
        self._connectors: Dict[str, aiohttp.TCPConnector] = {}
        
    @asynccontextmanager
    async def get_session(self, pool_name: str = "default", 
                         max_connections: int = 100,
                         max_per_host: int = 30) -> aiohttp.ClientSession:
        """Gibt eine Session aus dem Pool zurück"""
        if pool_name not in self._sessions:
            connector = aiohttp.TCPConnector(
                limit=max_connections,
                limit_per_host=max_per_host,
                ttl_dns_cache=300,
                enable_cleanup_closed=True
            )
            self._connectors[pool_name] = connector
            self._sessions[pool_name] = aiohttp.ClientSession(
                connector=connector,
                timeout=aiohttp.ClientTimeout(total=60)
            )
            self.logger.info(f"Created connection pool '{pool_name}' with {max_connections} connections")
        
        yield self._sessions[pool_name]
    
    async def close_all(self):
        """Schließt alle Connection Pools"""
        for name, session in self._sessions.items():
            await session.close()
            self.logger.info(f"Closed connection pool '{name}'")
        self._sessions.clear()
        self._connectors.clear()


class ResultCache:
    """Caching für API-Responses und Suchergebnisse"""
    
    def __init__(self, ttl_seconds: int = 3600):
        self.logger = get_logger("result_cache")
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._ttl = ttl_seconds
        self._hit_count = 0
        self._miss_count = 0
        
    def _generate_key(self, agent_name: str, query: MineQuery) -> str:
        """Generiert Cache-Key aus Agent und Query"""
        key_data = {
            'agent': agent_name,
            'mine': query.mine_name,
            'region': query.region,
            'country': query.country,
            'fields': sorted(query.required_fields),
            'languages': sorted(query.languages)
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, agent_name: str, query: MineQuery) -> Optional[List[SearchResult]]:
        """Holt Ergebnisse aus dem Cache"""
        key = self._generate_key(agent_name, query)
        
        if key in self._cache:
            entry = self._cache[key]
            if datetime.now() < entry['expires']:
                self._hit_count += 1
                self.logger.debug(f"Cache hit for {agent_name}: {query.mine_name}")
                return entry['results']
            else:
                # Abgelaufen
                del self._cache[key]
        
        self._miss_count += 1
        return None
    
    def put(self, agent_name: str, query: MineQuery, results: List[SearchResult]):
        """Speichert Ergebnisse im Cache"""
        key = self._generate_key(agent_name, query)
        self._cache[key] = {
            'results': results,
            'expires': datetime.now() + timedelta(seconds=self._ttl),
            'created': datetime.now()
        }
        self.logger.debug(f"Cached {len(results)} results for {agent_name}: {query.mine_name}")
    
    def clear_expired(self):
        """Entfernt abgelaufene Einträge"""
        now = datetime.now()
        expired_keys = [k for k, v in self._cache.items() if v['expires'] < now]
        for key in expired_keys:
            del self._cache[key]
        if expired_keys:
            self.logger.info(f"Cleared {len(expired_keys)} expired cache entries")
    
    def get_stats(self) -> Dict[str, Any]:
        """Gibt Cache-Statistiken zurück"""
        total = self._hit_count + self._miss_count
        hit_rate = self._hit_count / total if total > 0 else 0
        return {
            'size': len(self._cache),
            'hits': self._hit_count,
            'misses': self._miss_count,
            'hit_rate': hit_rate
        }


class AsyncBatchProcessor:
    """Verarbeitet Anfragen in Batches für bessere Performance"""
    
    def __init__(self, batch_size: int = 5, batch_timeout: float = 0.1):
        self.logger = get_logger("batch_processor")
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        
    async def process_batch(self, 
                          tasks: List[Callable],
                          max_concurrent: int = 10) -> List[Any]:
        """Verarbeitet Tasks in optimierten Batches"""
        results = []
        
        # Teile in Batches auf
        for i in range(0, len(tasks), self.batch_size):
            batch = tasks[i:i + self.batch_size]
            
            # Führe Batch aus mit Semaphore für Concurrency-Kontrolle
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def run_with_semaphore(task):
                async with semaphore:
                    return await task
            
            batch_results = await asyncio.gather(
                *[run_with_semaphore(task()) for task in batch],
                return_exceptions=True
            )
            
            results.extend(batch_results)
            
            # Kleine Pause zwischen Batches
            if i + self.batch_size < len(tasks):
                await asyncio.sleep(self.batch_timeout)
        
        return results


class PerformanceMonitor:
    """Überwacht Performance-Metriken"""
    
    def __init__(self):
        self.logger = get_logger("performance_monitor")
        self._metrics: Dict[str, List[float]] = {}
        self._active_tasks: Set[str] = set()
        
    async def measure_async(self, name: str, coro):
        """Misst die Ausführungszeit einer Async-Operation"""
        self._active_tasks.add(name)
        start_time = time.perf_counter()
        
        try:
            result = await coro
            duration = time.perf_counter() - start_time
            self._record_metric(name, duration)
            return result
        finally:
            self._active_tasks.discard(name)
    
    def _record_metric(self, name: str, duration: float):
        """Zeichnet eine Metrik auf"""
        if name not in self._metrics:
            self._metrics[name] = []
        self._metrics[name].append(duration)
        
        # Behalte nur die letzten 100 Messungen
        if len(self._metrics[name]) > 100:
            self._metrics[name] = self._metrics[name][-100:]
    
    def get_stats(self, name: str) -> Dict[str, float]:
        """Gibt Statistiken für eine Metrik zurück"""
        if name not in self._metrics or not self._metrics[name]:
            return {}
        
        values = self._metrics[name]
        return {
            'count': len(values),
            'avg': sum(values) / len(values),
            'min': min(values),
            'max': max(values),
            'p50': sorted(values)[len(values) // 2],
            'p95': sorted(values)[int(len(values) * 0.95)]
        }
    
    def get_active_tasks(self) -> Set[str]:
        """Gibt aktuelle laufende Tasks zurück"""
        return self._active_tasks.copy()


class QueryOptimizer:
    """Optimiert Datenbank-Queries"""
    
    def __init__(self):
        self.logger = get_logger("query_optimizer")
        self._query_cache = {}
        
    @lru_cache(maxsize=128)
    def optimize_search_query(self, 
                            mine_name: str,
                            fields: tuple,
                            limit: int = 100) -> str:
        """Optimiert Such-Queries mit Caching"""
        # Nutze Index-optimierte Query
        base_query = """
        SELECT DISTINCT sr.* 
        FROM search_results sr
        INNER JOIN mines m ON sr.mine_id = m.id
        WHERE m.name = %s
        """
        
        if fields:
            field_conditions = " OR ".join([f"sr.field_name = %s" for _ in fields])
            base_query += f" AND ({field_conditions})"
        
        base_query += f"""
        ORDER BY sr.confidence_score DESC, sr.timestamp DESC
        LIMIT {limit}
        """
        
        return base_query
    
    def get_bulk_insert_query(self, table_name: str, columns: List[str], 
                            row_count: int) -> str:
        """Generiert optimierte Bulk-Insert Query"""
        placeholders = ", ".join(["%s"] * len(columns))
        values_template = f"({placeholders})"
        values_list = ", ".join([values_template] * row_count)
        
        return f"""
        INSERT INTO {table_name} ({', '.join(columns)})
        VALUES {values_list}
        ON CONFLICT DO NOTHING
        """


class SearchOptimizer:
    """Hauptklasse für Such-Optimierungen"""
    
    def __init__(self):
        self.logger = get_logger("search_optimizer")
        self.connection_pool = ConnectionPoolManager()
        self.result_cache = ResultCache()
        self.batch_processor = AsyncBatchProcessor()
        self.performance_monitor = PerformanceMonitor()
        self.query_optimizer = QueryOptimizer()
        
    async def optimize_agent_search(self,
                                  agents: List[BaseAgent],
                                  query: MineQuery,
                                  use_cache: bool = True,
                                  max_concurrent: int = 10) -> List[SearchResult]:
        """Optimierte Agent-Suche mit Caching und Batching"""
        results = []
        search_tasks = []
        
        for agent in agents:
            agent_name = getattr(agent, 'name', type(agent).__name__)
            
            # Check Cache
            if use_cache:
                cached_results = self.result_cache.get(agent_name, query)
                if cached_results is not None:
                    results.extend(cached_results)
                    self.logger.info(f"Using cached results for {agent_name}")
                    continue
            
            # Erstelle optimierte Such-Task
            async def create_search_task(agent=agent, name=agent_name):
                async def search():
                    try:
                        # Messe Performance
                        agent_results = await self.performance_monitor.measure_async(
                            f"search_{name}",
                            agent.search(query)
                        )
                        
                        # Cache Ergebnisse
                        if use_cache and agent_results:
                            self.result_cache.put(name, query, agent_results)
                        
                        return agent_results
                    except Exception as e:
                        self.logger.error(f"Error in {name}: {e}")
                        return []
                
                return search
            
            search_tasks.append(await create_search_task())
        
        # Führe Tasks optimiert aus
        if search_tasks:
            batch_results = await self.batch_processor.process_batch(
                search_tasks, 
                max_concurrent=max_concurrent
            )
            
            for result_list in batch_results:
                if isinstance(result_list, list):
                    results.extend(result_list)
        
        return results
    
    async def cleanup(self):
        """Cleanup-Ressourcen"""
        await self.connection_pool.close_all()
        self.result_cache.clear_expired()
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Gibt Performance-Statistiken zurück"""
        stats = {
            'cache': self.result_cache.get_stats(),
            'active_tasks': list(self.performance_monitor.get_active_tasks()),
            'metrics': {}
        }
        
        # Sammle Metriken für alle Agenten
        for key in self.performance_monitor._metrics:
            stats['metrics'][key] = self.performance_monitor.get_stats(key)
        
        return stats