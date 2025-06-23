"""
Author: rahn
Datum: 23.06.2025
Version: 1.0
Beschreibung: Performance-Tests für Optimierungen
"""

import pytest
import asyncio
import time
from unittest.mock import MagicMock, AsyncMock

from src.core.performance_optimizer import (
    ConnectionPoolManager, ResultCache, AsyncBatchProcessor,
    PerformanceMonitor, SearchOptimizer
)
from src.core.search_executor_optimized import OptimizedSearchExecutor
from src.agents.base.http_client_optimized import OptimizedHTTPClient
from src.agents.base_agent import MineQuery, SearchResult


class TestPerformanceOptimization:
    """Tests für Performance-Optimierungen"""
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_connection_pool_performance(self):
        """Test Connection Pool Performance"""
        pool_manager = ConnectionPoolManager()
        
        # Test mehrere parallele Requests
        async def make_request(i):
            async with pool_manager.get_session() as session:
                # Simuliere Request
                await asyncio.sleep(0.01)
                return f"Result {i}"
        
        start_time = time.time()
        
        # 100 parallele Requests
        tasks = [make_request(i) for i in range(100)]
        results = await asyncio.gather(*tasks)
        
        duration = time.time() - start_time
        
        assert len(results) == 100
        assert duration < 1.0  # Sollte unter 1 Sekunde sein
        
        await pool_manager.close_all()
    
    def test_result_cache(self):
        """Test Result Cache Funktionalität"""
        cache = ResultCache(ttl_seconds=60)
        
        # Test Query
        query = MineQuery(
            mine_name="Test Mine",
            region="Test Region",
            country="Canada",
            languages=["en"],
            required_fields=["betreiber"]
        )
        
        # Test Results
        results = [
            SearchResult(
                field_name="betreiber",
                value="Test Corp",
                source="test_agent",
                confidence_score=0.9,
                metadata={}
            )
        ]
        
        # Cache Miss
        assert cache.get("test_agent", query) is None
        assert cache.get_stats()['hit_rate'] == 0
        
        # Cache Put
        cache.put("test_agent", query, results)
        
        # Cache Hit
        cached_results = cache.get("test_agent", query)
        assert cached_results == results
        assert cache.get_stats()['hit_rate'] > 0
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_batch_processor(self):
        """Test Batch Processing Performance"""
        processor = AsyncBatchProcessor(batch_size=10)
        
        # Erstelle 50 Mock-Tasks
        results_list = []
        
        async def mock_task(i):
            await asyncio.sleep(0.01)
            return f"Result {i}"
        
        tasks = [lambda i=i: mock_task(i) for i in range(50)]
        
        start_time = time.time()
        results = await processor.process_batch(tasks, max_concurrent=5)
        duration = time.time() - start_time
        
        assert len(results) == 50
        assert all(isinstance(r, str) for r in results)
        # Mit Batching sollte es effizienter sein
        assert duration < 2.0
    
    @pytest.mark.asyncio
    async def test_performance_monitor(self):
        """Test Performance Monitoring"""
        monitor = PerformanceMonitor()
        
        # Test Async Measurement
        async def slow_operation():
            await asyncio.sleep(0.1)
            return "done"
        
        result = await monitor.measure_async("test_op", slow_operation())
        assert result == "done"
        
        # Check Stats
        stats = monitor.get_stats("test_op")
        assert stats['count'] == 1
        assert 0.09 < stats['avg'] < 0.12  # ~0.1s
    
    @pytest.mark.asyncio
    async def test_search_optimizer_caching(self):
        """Test Search Optimizer mit Caching"""
        optimizer = SearchOptimizer()
        
        # Mock Agents
        mock_agents = []
        for i in range(3):
            agent = AsyncMock()
            agent.name = f"agent_{i}"
            agent.search = AsyncMock(return_value=[
                SearchResult(
                    field_name="betreiber",
                    value=f"Corp {i}",
                    source=f"agent_{i}",
                    confidence_score=0.8,
                    metadata={}
                )
            ])
            mock_agents.append(agent)
        
        query = MineQuery(
            mine_name="Test Mine",
            region="Ontario",
            country="Canada",
            languages=["en"],
            required_fields=["betreiber"]
        )
        
        # Erste Suche - keine Cache Hits
        start_time = time.time()
        results1 = await optimizer.optimize_agent_search(
            mock_agents, query, use_cache=True
        )
        first_duration = time.time() - start_time
        
        assert len(results1) == 3
        assert optimizer.result_cache.get_stats()['hits'] == 0
        
        # Zweite Suche - sollte aus Cache kommen
        start_time = time.time()
        results2 = await optimizer.optimize_agent_search(
            mock_agents, query, use_cache=True
        )
        cached_duration = time.time() - start_time
        
        assert len(results2) == 3
        assert optimizer.result_cache.get_stats()['hits'] == 3
        # Cache sollte deutlich schneller sein
        assert cached_duration < first_duration * 0.5
        
        await optimizer.cleanup()
    
    @pytest.mark.asyncio
    async def test_optimized_search_executor(self):
        """Test Optimized Search Executor"""
        executor = OptimizedSearchExecutor()
        
        # Mock Agents
        mock_agents = []
        for i in range(5):
            agent = AsyncMock()
            agent.name = f"agent_{i}"
            agent.search = AsyncMock(return_value=[
                SearchResult(
                    field_name="produktion",
                    value=f"{i * 1000} tons",
                    source=f"agent_{i}",
                    confidence_score=0.7 + i * 0.05,
                    metadata={}
                )
            ])
            mock_agents.append(agent)
        
        query = MineQuery(
            mine_name="Performance Test Mine",
            region="Quebec",
            country="Canada",
            languages=["en", "fr"],
            required_fields=["produktion"]
        )
        
        # Test normale Suche
        results = await executor.execute_search(
            agents=mock_agents,
            query=query,
            search_params={'max_concurrent': 3, 'show_stats': True}
        )
        
        assert len(results) == 5
        assert all(r.field_name == "produktion" for r in results)
        
        # Test Bulk Search
        queries = [
            MineQuery(
                mine_name=f"Mine {i}",
                region="Ontario",
                country="Canada",
                languages=["en"],
                required_fields=["betreiber"]
            )
            for i in range(3)
        ]
        
        bulk_results = await executor.execute_bulk_search(
            agents=mock_agents[:2],
            queries=queries,
            max_concurrent_queries=2
        )
        
        assert len(bulk_results) == 3
        assert all(mine_name in bulk_results for mine_name in ["Mine 0", "Mine 1", "Mine 2"])
        
        # Performance Report
        report = executor.get_performance_report()
        assert 'cache_performance' in report
        assert 'recommendations' in report
        
        await executor.cleanup()
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_http_client_optimization(self):
        """Test Optimized HTTP Client"""
        client = OptimizedHTTPClient(
            base_url="https://httpbin.org",
            pool_size=50,
            pool_connections_per_host=20
        )
        
        # Test Cache
        result1 = await client.get("/get", params={"test": "cache"})
        assert client.get_stats()['cache_size'] == 1
        
        # Zweiter Request sollte aus Cache kommen
        result2 = await client.get("/get", params={"test": "cache"})
        assert result1 == result2
        
        # Test Batch Requests
        batch_data = [{"item": i} for i in range(20)]
        
        start_time = time.time()
        batch_results = await client.post_batch(
            "/post",
            batch_data,
            batch_size=5
        )
        duration = time.time() - start_time
        
        assert len(batch_results) == 20
        # Batch sollte effizient sein
        assert duration < 5.0
        
        # Check Stats
        stats = client.get_stats()
        assert stats['total_requests'] > 20
        assert stats['success_rate'] > 0.8
        
        await client.close()


class TestPerformanceComparison:
    """Vergleich zwischen optimiert und nicht-optimiert"""
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_search_performance_comparison(self):
        """Vergleicht Performance mit und ohne Optimierung"""
        # Mock viele Agents
        mock_agents = []
        for i in range(20):
            agent = AsyncMock()
            agent.name = f"agent_{i}"
            
            async def search_with_delay():
                await asyncio.sleep(0.1)  # Simuliere Netzwerk-Latenz
                return [SearchResult(
                    field_name="test",
                    value="value",
                    source="test",
                    confidence_score=0.8,
                    metadata={}
                )]
            
            agent.search = search_with_delay
            mock_agents.append(agent)
        
        query = MineQuery(
            mine_name="Benchmark Mine",
            region="Test",
            country="Test",
            languages=["en"],
            required_fields=["test"]
        )
        
        # Test ohne Optimierung (sequentiell)
        start = time.time()
        results_seq = []
        for agent in mock_agents:
            results_seq.extend(await agent.search())
        seq_duration = time.time() - start
        
        # Test mit Optimierung (parallel)
        optimizer = SearchOptimizer()
        start = time.time()
        results_opt = await optimizer.optimize_agent_search(
            mock_agents, query, use_cache=False, max_concurrent=10
        )
        opt_duration = time.time() - start
        
        print(f"\nPerformance Vergleich:")
        print(f"Sequentiell: {seq_duration:.2f}s")
        print(f"Optimiert: {opt_duration:.2f}s")
        print(f"Speedup: {seq_duration/opt_duration:.2f}x")
        
        # Optimiert sollte deutlich schneller sein
        assert opt_duration < seq_duration * 0.3
        assert len(results_opt) == len(results_seq)
        
        await optimizer.cleanup()