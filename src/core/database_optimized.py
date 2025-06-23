"""
Author: rahn
Datum: 23.06.2025
Version: 2.0
Beschreibung: Optimierte Datenbank-Klasse mit Connection Pooling und Query-Optimierung
"""

import asyncio
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
from contextlib import asynccontextmanager
import aiomysql
import aiosqlite
from sqlalchemy import create_engine, text, Index
from sqlalchemy.pool import QueuePool
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from src.data.models import Base, Mine, SearchResultDB, Search, AgentStatistics
from .logger import get_logger
from .performance_optimizer import QueryOptimizer


class OptimizedDatabase:
    """Optimierte Datenbank mit Connection Pooling und Query-Optimierung"""
    
    def __init__(self, connection_string: str):
        self.logger = get_logger("database_optimized")
        self.connection_string = connection_string
        self.query_optimizer = QueryOptimizer()
        
        # Async Engine mit Connection Pool
        self.async_engine = create_async_engine(
            connection_string,
            pool_size=20,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=3600,
            pool_pre_ping=True,
            echo=False
        )
        
        # Async Session Factory
        self.async_session_factory = async_sessionmaker(
            self.async_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        # Sync Engine für Migrationen
        sync_conn_string = connection_string.replace('sqlite+aiosqlite', 'sqlite')
        self.sync_engine = create_engine(
            sync_conn_string,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=5
        )
        
        self._create_indexes()
    
    def _create_indexes(self):
        """Erstellt optimierte Indizes für häufige Queries"""
        with self.sync_engine.begin() as conn:
            # Index für Mine-Namen (häufigste Suche)
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_mines_name 
                ON mines(name)
            """))
            
            # Composite Index für Search Results
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_search_results_mine_field 
                ON search_results(mine_id, field_name)
            """))
            
            # Index für Confidence Score (für Sortierung)
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_search_results_confidence 
                ON search_results(confidence_score DESC)
            """))
            
            # Index für Agent Statistics
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_agent_stats_name 
                ON agent_statistics(agent_name)
            """))
            
            self.logger.info("Datenbank-Indizes erstellt/aktualisiert")
    
    @asynccontextmanager
    async def get_session(self) -> AsyncSession:
        """Gibt eine optimierte Async-Session zurück"""
        async with self.async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def bulk_insert_results(self, results: List[SearchResultDB]) -> int:
        """Fügt Ergebnisse mit Bulk-Insert ein"""
        if not results:
            return 0
        
        async with self.get_session() as session:
            # Nutze bulk_insert_mappings für bessere Performance
            mappings = []
            for result in results:
                mappings.append({
                    'mine_id': result.mine_id,
                    'field_name': result.field_name,
                    'value': result.value,
                    'source': result.source,
                    'source_url': result.source_url,
                    'source_date': result.source_date,
                    'confidence_score': result.confidence_score,
                    'agent_name': result.agent_name,
                    'timestamp': result.timestamp or datetime.utcnow(),
                    'extra_data': result.extra_data or {}
                })
            
            # Bulk Insert
            await session.run_sync(
                lambda sync_session: sync_session.bulk_insert_mappings(
                    SearchResultDB, mappings
                )
            )
            
            self.logger.info(f"Bulk-Insert von {len(results)} Ergebnissen erfolgreich")
            return len(results)
    
    async def get_mine_results_optimized(
        self,
        mine_name: str,
        fields: Optional[List[str]] = None,
        min_confidence: float = 0.0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Optimierte Abfrage für Mine-Ergebnisse"""
        async with self.get_session() as session:
            # Nutze optimierte Query
            query = """
                SELECT sr.*, m.name as mine_name, m.region, m.country
                FROM search_results sr
                INNER JOIN mines m ON sr.mine_id = m.id
                WHERE m.name = :mine_name
                AND sr.confidence_score >= :min_confidence
            """
            
            params = {
                'mine_name': mine_name,
                'min_confidence': min_confidence
            }
            
            if fields:
                field_placeholders = ', '.join([f':field_{i}' for i in range(len(fields))])
                query += f" AND sr.field_name IN ({field_placeholders})"
                for i, field in enumerate(fields):
                    params[f'field_{i}'] = field
            
            query += " ORDER BY sr.confidence_score DESC, sr.timestamp DESC"
            query += f" LIMIT {limit}"
            
            # Führe Query aus
            result = await session.execute(text(query), params)
            rows = result.fetchall()
            
            # Konvertiere zu Dict
            results = []
            for row in rows:
                results.append({
                    'id': row.id,
                    'mine_name': row.mine_name,
                    'region': row.region,
                    'country': row.country,
                    'field_name': row.field_name,
                    'value': row.value,
                    'source': row.source,
                    'confidence_score': row.confidence_score,
                    'agent_name': row.agent_name,
                    'timestamp': row.timestamp
                })
            
            return results
    
    async def update_agent_statistics_batch(
        self,
        stats_updates: Dict[str, Dict[str, Any]]
    ):
        """Batch-Update für Agent-Statistiken"""
        async with self.get_session() as session:
            for agent_name, stats in stats_updates.items():
                # Upsert Pattern für Statistiken
                await session.execute(
                    text("""
                        INSERT INTO agent_statistics 
                        (agent_name, total_requests, successful_requests, 
                         failed_requests, total_fields_found, average_confidence, last_used)
                        VALUES 
                        (:agent_name, :total, :success, :failed, :fields, :confidence, :last_used)
                        ON CONFLICT(agent_name) DO UPDATE SET
                            total_requests = total_requests + :total,
                            successful_requests = successful_requests + :success,
                            failed_requests = failed_requests + :failed,
                            total_fields_found = total_fields_found + :fields,
                            average_confidence = 
                                (average_confidence * total_requests + :confidence * :total) / 
                                (total_requests + :total),
                            last_used = :last_used,
                            updated_at = CURRENT_TIMESTAMP
                    """),
                    {
                        'agent_name': agent_name,
                        'total': stats.get('total_requests', 0),
                        'success': stats.get('successful_requests', 0),
                        'failed': stats.get('failed_requests', 0),
                        'fields': stats.get('fields_found', 0),
                        'confidence': stats.get('avg_confidence', 0.0),
                        'last_used': datetime.utcnow()
                    }
                )
    
    async def get_search_analytics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Gibt Such-Analytiken zurück"""
        async with self.get_session() as session:
            # Basis-Statistiken
            total_mines = await session.execute(
                text("SELECT COUNT(*) FROM mines")
            )
            total_results = await session.execute(
                text("SELECT COUNT(*) FROM search_results")
            )
            total_searches = await session.execute(
                text("SELECT COUNT(*) FROM searches")
            )
            
            # Top-Agenten nach Erfolg
            top_agents = await session.execute(
                text("""
                    SELECT agent_name, 
                           COUNT(*) as result_count,
                           AVG(confidence_score) as avg_confidence
                    FROM search_results
                    GROUP BY agent_name
                    ORDER BY result_count DESC
                    LIMIT 10
                """)
            )
            
            # Feldabdeckung
            field_coverage = await session.execute(
                text("""
                    SELECT field_name, 
                           COUNT(DISTINCT mine_id) as mines_with_field,
                           AVG(confidence_score) as avg_confidence
                    FROM search_results
                    GROUP BY field_name
                    ORDER BY mines_with_field DESC
                """)
            )
            
            return {
                'total_mines': total_mines.scalar(),
                'total_results': total_results.scalar(),
                'total_searches': total_searches.scalar(),
                'top_agents': [
                    {
                        'name': row.agent_name,
                        'results': row.result_count,
                        'avg_confidence': row.avg_confidence
                    }
                    for row in top_agents
                ],
                'field_coverage': [
                    {
                        'field': row.field_name,
                        'mines_count': row.mines_with_field,
                        'avg_confidence': row.avg_confidence
                    }
                    for row in field_coverage
                ]
            }
    
    async def cleanup_old_data(self, days_to_keep: int = 30):
        """Bereinigt alte Daten für bessere Performance"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        async with self.get_session() as session:
            # Lösche alte Such-Sessions
            deleted_searches = await session.execute(
                text("""
                    DELETE FROM searches 
                    WHERE completed_at < :cutoff 
                    AND status IN ('completed', 'failed')
                """),
                {'cutoff': cutoff_date}
            )
            
            self.logger.info(f"Gelöscht: {deleted_searches.rowcount} alte Such-Sessions")
    
    async def optimize_tables(self):
        """Optimiert Datenbank-Tabellen"""
        async with self.get_session() as session:
            # VACUUM für SQLite
            if 'sqlite' in self.connection_string:
                await session.execute(text("VACUUM"))
                self.logger.info("Datenbank optimiert (VACUUM)")
            
            # Analysiere Tabellen für bessere Query-Planung
            await session.execute(text("ANALYZE"))
            self.logger.info("Tabellen-Statistiken aktualisiert (ANALYZE)")
    
    async def close(self):
        """Schließt alle Datenbank-Verbindungen"""
        await self.async_engine.dispose()
        self.sync_engine.dispose()
        self.logger.info("Datenbank-Verbindungen geschlossen")