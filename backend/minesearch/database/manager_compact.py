"""
Compact Database Manager
Kompakte Version des Database Managers

Author: MineSearch Development Team
Date: 2025-01-11
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from typing import Optional, Dict, List, Any
import sqlite3
import logging
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Verwaltung der Datenbankverbindung und -operationen"""

    def __init__(self, database_url: Optional[str] = None):
        """Initialisiere Database Manager"""
        try:
            from minesearch.config.base import config
            self.database_url = database_url or config.DATABASE_URL
        except ImportError:
            self.database_url = database_url or "sqlite:///mines.db"

        # Connection Pool für bessere Performance
        self.engine = create_engine(
            self.database_url,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            echo=False
        )
        
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # SQLite-spezifische Optimierungen
        if self.database_url.startswith("sqlite"):
            self._setup_sqlite_optimizations()

    def _setup_sqlite_optimizations(self):
        """Setup SQLite-spezifische Optimierungen"""
        @event.listens_for(self.engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA cache_size=10000")
            cursor.execute("PRAGMA temp_store=MEMORY")
            cursor.close()

    def get_session(self) -> Session:
        """Hole neue Datenbank-Session"""
        return self.SessionLocal()

    def close(self):
        """Schließe Datenbankverbindung"""
        if hasattr(self, 'engine'):
            self.engine.dispose()

    def create_tables(self):
        """Erstelle alle Tabellen"""
        try:
            from .models import Base
            Base.metadata.create_all(self.engine)
            logger.info("✅ Tabellen erfolgreich erstellt")
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen der Tabellen: {e}")
            raise

    def drop_tables(self):
        """Lösche alle Tabellen"""
        try:
            from .models import Base
            Base.metadata.drop_all(self.engine)
            logger.info("✅ Tabellen erfolgreich gelöscht")
        except Exception as e:
            logger.error(f"❌ Fehler beim Löschen der Tabellen: {e}")
            raise

    def backup_database(self, backup_path: str = None):
        """Erstelle Datenbank-Backup"""
        try:
            if not backup_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = f"mines_backup_{timestamp}.db"
            
            if self.database_url.startswith("sqlite:///"):
                db_path = self.database_url.replace("sqlite:///", "")
                import shutil
                shutil.copy2(db_path, backup_path)
                logger.info(f"✅ Backup erstellt: {backup_path}")
                return backup_path
            else:
                logger.warning("Backup für diese Datenbank-Art nicht implementiert")
                return None
                
        except Exception as e:
            logger.error(f"❌ Backup fehlgeschlagen: {e}")
            return None

    def restore_database(self, backup_path: str):
        """Stelle Datenbank aus Backup wieder her"""
        try:
            if self.database_url.startswith("sqlite:///"):
                db_path = self.database_url.replace("sqlite:///", "")
                import shutil
                shutil.copy2(backup_path, db_path)
                logger.info(f"✅ Datenbank aus Backup wiederhergestellt: {backup_path}")
                return True
            else:
                logger.warning("Restore für diese Datenbank-Art nicht implementiert")
                return False
                
        except Exception as e:
            logger.error(f"❌ Restore fehlgeschlagen: {e}")
            return False

    def get_database_stats(self) -> Dict[str, Any]:
        """Hole Datenbank-Statistiken"""
        try:
            stats = {}
            
            with self.get_session() as session:
                # Hole Tabellen-Info
                from .models import Source, SearchResult, ModelStatistics
                
                stats['sources'] = session.query(Source).count()
                stats['search_results'] = session.query(SearchResult).count()
                stats['model_statistics'] = session.query(ModelStatistics).count()
                
                # Hole Größe-Info
                if self.database_url.startswith("sqlite:///"):
                    db_path = self.database_url.replace("sqlite:///", "")
                    import os
                    stats['database_size_mb'] = os.path.getsize(db_path) / (1024 * 1024)
                
                stats['timestamp'] = datetime.now().isoformat()
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Abrufen der Statistiken: {e}")
            return {}

    def cleanup_old_data(self, days: int = 30):
        """Bereinige alte Daten"""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            with self.get_session() as session:
                from .models import Source, SearchResult
                
                # Lösche alte Quellen
                old_sources = session.query(Source).filter(
                    Source.created_at < cutoff_date
                ).count()
                
                session.query(Source).filter(
                    Source.created_at < cutoff_date
                ).delete()
                
                # Lösche alte Suchergebnisse
                old_results = session.query(SearchResult).filter(
                    SearchResult.created_at < cutoff_date
                ).count()
                
                session.query(SearchResult).filter(
                    SearchResult.created_at < cutoff_date
                ).delete()
                
                session.commit()
                
                logger.info(f"✅ Bereinigt: {old_sources} Quellen, {old_results} Suchergebnisse")
                return {'sources_deleted': old_sources, 'results_deleted': old_results}
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Bereinigen: {e}")
            return {}

    def optimize_database(self):
        """Optimiere Datenbank"""
        try:
            if self.database_url.startswith("sqlite:///"):
                with self.get_session() as session:
                    # VACUUM für SQLite
                    session.execute("VACUUM")
                    session.commit()
                    
                    # ANALYZE für bessere Query-Performance
                    session.execute("ANALYZE")
                    session.commit()
                    
                    logger.info("✅ Datenbank optimiert")
                    return True
            else:
                logger.warning("Optimierung für diese Datenbank-Art nicht implementiert")
                return False
                
        except Exception as e:
            logger.error(f"❌ Optimierung fehlgeschlagen: {e}")
            return False

    def get_connection_info(self) -> Dict[str, Any]:
        """Hole Verbindungsinformationen"""
        return {
            'database_url': self.database_url,
            'engine_info': str(self.engine),
            'pool_size': self.engine.pool.size(),
            'checked_out_connections': self.engine.pool.checkedout(),
            'overflow_connections': self.engine.pool.overflow(),
            'timestamp': datetime.now().isoformat()
        }

    def test_connection(self) -> bool:
        """Teste Datenbankverbindung"""
        try:
            with self.get_session() as session:
                session.execute("SELECT 1")
                logger.info("✅ Datenbankverbindung erfolgreich getestet")
                return True
        except Exception as e:
            logger.error(f"❌ Datenbankverbindung fehlgeschlagen: {e}")
            return False

    def get_table_info(self) -> Dict[str, Any]:
        """Hole Tabellen-Informationen"""
        try:
            from sqlalchemy import inspect
            
            inspector = inspect(self.engine)
            tables = inspector.get_table_names()
            
            table_info = {}
            for table in tables:
                columns = inspector.get_columns(table)
                indexes = inspector.get_indexes(table)
                
                table_info[table] = {
                    'columns': len(columns),
                    'indexes': len(indexes),
                    'column_names': [col['name'] for col in columns]
                }
            
            return {
                'tables': table_info,
                'total_tables': len(tables),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Abrufen der Tabellen-Info: {e}")
            return {}

    def execute_raw_sql(self, sql: str, params: Dict[str, Any] = None):
        """Führe rohe SQL-Abfrage aus"""
        try:
            with self.get_session() as session:
                result = session.execute(sql, params or {})
                session.commit()
                return result
        except Exception as e:
            logger.error(f"❌ SQL-Ausführung fehlgeschlagen: {e}")
            raise

    def get_health_status(self) -> Dict[str, Any]:
        """Hole Gesundheitsstatus der Datenbank"""
        try:
            health = {
                'status': 'healthy',
                'connection_test': self.test_connection(),
                'database_stats': self.get_database_stats(),
                'connection_info': self.get_connection_info(),
                'timestamp': datetime.now().isoformat()
            }
            
            # Prüfe auf Probleme
            if not health['connection_test']:
                health['status'] = 'unhealthy'
                health['issues'] = ['Connection test failed']
            
            return health
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Abrufen des Gesundheitsstatus: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }


# Globale Instanz für einfache Verwendung
_db_manager = None


def get_database_manager() -> DatabaseManager:
    """Hole globale Database Manager Instanz"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


def close_database_manager():
    """Schließe globale Database Manager Instanz"""
    global _db_manager
    if _db_manager:
        _db_manager.close()
        _db_manager = None


__all__ = [
    "DatabaseManager",
    "get_database_manager",
    "close_database_manager"
]
