"""
Compact Database Migrations
Kompakte Version der Database Migrations

Author: MineSearch Development Team
Date: 2025-01-11
"""

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
import logging
import re
from typing import Dict, Any, Optional, List
import os
import importlib

logger = logging.getLogger(__name__)


def _load_database_url_from_config() -> str:
    """Lädt die DATABASE_URL aus der Konfiguration"""
    try:
        config_module = importlib.import_module("minesearch.config.base")
        return config_module.DATABASE_URL
    except ImportError:
        return os.getenv("DATABASE_URL", "sqlite:///mines.db")


def create_database_engine(database_url: str = None):
    """Erstelle Database Engine"""
    if not database_url:
        database_url = _load_database_url_from_config()
    
    return create_engine(database_url, echo=False)


def get_session_factory(database_url: str = None):
    """Erstelle Session Factory"""
    engine = create_database_engine(database_url)
    return sessionmaker(bind=engine)


def run_migration_001_create_tables():
    """Migration 001: Erstelle Basis-Tabellen"""
    try:
        engine = create_database_engine()
        
        # Importiere Models
        from .models import Base
        
        # Erstelle alle Tabellen
        Base.metadata.create_all(engine)
        
        logger.info("✅ Migration 001: Basis-Tabellen erstellt")
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration 001 fehlgeschlagen: {e}")
        return False


def run_migration_002_add_indexes():
    """Migration 002: Füge Indizes hinzu"""
    try:
        engine = create_database_engine()
        
        with engine.connect() as conn:
            # Füge Indizes hinzu
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_source_url ON source(url)",
                "CREATE INDEX IF NOT EXISTS idx_source_domain ON source(domain)",
                "CREATE INDEX IF NOT EXISTS idx_field_search_result_mine_id ON field_search_result(mine_id)",
                "CREATE INDEX IF NOT EXISTS idx_sequential_search_result_mine_id ON sequential_search_result(mine_id)",
                "CREATE INDEX IF NOT EXISTS idx_model_source_contribution_model ON model_source_contribution(model_name)"
            ]
            
            for index_sql in indexes:
                conn.execute(text(index_sql))
            
            conn.commit()
        
        logger.info("✅ Migration 002: Indizes hinzugefügt")
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration 002 fehlgeschlagen: {e}")
        return False


def run_migration_003_add_constraints():
    """Migration 003: Füge Constraints hinzu"""
    try:
        engine = create_database_engine()
        
        with engine.connect() as conn:
            # Füge Constraints hinzu
            constraints = [
                "ALTER TABLE source ADD CONSTRAINT chk_source_url CHECK (url IS NOT NULL AND url != '')",
                "ALTER TABLE field_search_result ADD CONSTRAINT chk_field_search_result_mine_id CHECK (mine_id > 0)",
                "ALTER TABLE sequential_search_result ADD CONSTRAINT chk_sequential_search_result_mine_id CHECK (mine_id > 0)"
            ]
            
            for constraint_sql in constraints:
                try:
                    conn.execute(text(constraint_sql))
                except Exception as e:
                    logger.warning(f"Constraint bereits vorhanden oder Fehler: {e}")
            
            conn.commit()
        
        logger.info("✅ Migration 003: Constraints hinzugefügt")
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration 003 fehlgeschlagen: {e}")
        return False


def run_migration_004_add_views():
    """Migration 004: Füge Views hinzu"""
    try:
        engine = create_database_engine()
        
        with engine.connect() as conn:
            # Erstelle Views
            views = [
                """
                CREATE VIEW IF NOT EXISTS source_statistics AS
                SELECT 
                    domain,
                    COUNT(*) as source_count,
                    AVG(CASE WHEN content IS NOT NULL THEN 1 ELSE 0 END) as content_ratio
                FROM source
                GROUP BY domain
                """,
                """
                CREATE VIEW IF NOT EXISTS search_result_summary AS
                SELECT 
                    mine_id,
                    COUNT(*) as total_searches,
                    AVG(execution_time) as avg_execution_time,
                    MAX(created_at) as last_search
                FROM sequential_search_result
                GROUP BY mine_id
                """
            ]
            
            for view_sql in views:
                conn.execute(text(view_sql))
            
            conn.commit()
        
        logger.info("✅ Migration 004: Views hinzugefügt")
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration 004 fehlgeschlagen: {e}")
        return False


def run_migration_005_add_triggers():
    """Migration 005: Füge Trigger hinzu"""
    try:
        engine = create_database_engine()
        
        with engine.connect() as conn:
            # Erstelle Trigger
            triggers = [
                """
                CREATE TRIGGER IF NOT EXISTS update_source_updated_at
                AFTER UPDATE ON source
                BEGIN
                    UPDATE source SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
                END
                """,
                """
                CREATE TRIGGER IF NOT EXISTS update_field_search_result_updated_at
                AFTER UPDATE ON field_search_result
                BEGIN
                    UPDATE field_search_result SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
                END
                """
            ]
            
            for trigger_sql in triggers:
                conn.execute(text(trigger_sql))
            
            conn.commit()
        
        logger.info("✅ Migration 005: Trigger hinzugefügt")
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration 005 fehlgeschlagen: {e}")
        return False


def run_all_migrations():
    """Führe alle Migrationen aus"""
    try:
        logger.info("🚀 Starte alle Migrationen...")
        
        migrations = [
            run_migration_001_create_tables,
            run_migration_002_add_indexes,
            run_migration_003_add_constraints,
            run_migration_004_add_views,
            run_migration_005_add_triggers
        ]
        
        success_count = 0
        for migration in migrations:
            if migration():
                success_count += 1
        
        logger.info(f"✅ {success_count}/{len(migrations)} Migrationen erfolgreich")
        return success_count == len(migrations)
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Ausführen der Migrationen: {e}")
        return False


def check_migration_status():
    """Prüfe Migrations-Status"""
    try:
        engine = create_database_engine()
        
        with engine.connect() as conn:
            # Prüfe ob Tabellen existieren
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            
            required_tables = [
                'source', 'source_discovery_session', 'model_source_contribution',
                'field_search_result', 'sequential_search_result', 'field_search_source_usage'
            ]
            
            missing_tables = [table for table in required_tables if table not in tables]
            
            if missing_tables:
                logger.warning(f"Fehlende Tabellen: {missing_tables}")
                return False
            
            # Prüfe Indizes
            indexes = []
            for table in required_tables:
                table_indexes = inspector.get_indexes(table)
                indexes.extend(table_indexes)
            
            logger.info(f"✅ {len(tables)} Tabellen, {len(indexes)} Indizes gefunden")
            return True
            
    except Exception as e:
        logger.error(f"❌ Fehler beim Prüfen des Migrations-Status: {e}")
        return False


def rollback_migration(migration_number: int):
    """Rollback einer Migration"""
    try:
        logger.info(f"🔄 Rollback Migration {migration_number}...")
        
        engine = create_database_engine()
        
        with engine.connect() as conn:
            if migration_number == 1:
                # Rollback: Lösche Tabellen
                conn.execute(text("DROP TABLE IF EXISTS field_search_source_usage"))
                conn.execute(text("DROP TABLE IF EXISTS sequential_search_result"))
                conn.execute(text("DROP TABLE IF EXISTS field_search_result"))
                conn.execute(text("DROP TABLE IF EXISTS model_source_contribution"))
                conn.execute(text("DROP TABLE IF EXISTS source_discovery_session"))
                conn.execute(text("DROP TABLE IF EXISTS source"))
                
            elif migration_number == 2:
                # Rollback: Lösche Indizes
                indexes_to_drop = [
                    "DROP INDEX IF EXISTS idx_source_url",
                    "DROP INDEX IF EXISTS idx_source_domain",
                    "DROP INDEX IF EXISTS idx_field_search_result_mine_id",
                    "DROP INDEX IF EXISTS idx_sequential_search_result_mine_id",
                    "DROP INDEX IF EXISTS idx_model_source_contribution_model"
                ]
                
                for index_sql in indexes_to_drop:
                    conn.execute(text(index_sql))
            
            conn.commit()
        
        logger.info(f"✅ Migration {migration_number} zurückgerollt")
        return True
        
    except Exception as e:
        logger.error(f"❌ Rollback fehlgeschlagen: {e}")
        return False


def backup_database():
    """Erstelle Datenbank-Backup"""
    try:
        database_url = _load_database_url_from_config()
        
        if database_url.startswith("sqlite:///"):
            # SQLite Backup
            db_path = database_url.replace("sqlite:///", "")
            backup_path = f"{db_path}.backup_{int(__import__('time').time())}"
            
            import shutil
            shutil.copy2(db_path, backup_path)
            
            logger.info(f"✅ SQLite Backup erstellt: {backup_path}")
            return backup_path
        
        else:
            # Andere Datenbanken
            logger.warning("Backup für diese Datenbank-Art nicht implementiert")
            return None
            
    except Exception as e:
        logger.error(f"❌ Backup fehlgeschlagen: {e}")
        return None


def restore_database(backup_path: str):
    """Stelle Datenbank aus Backup wieder her"""
    try:
        database_url = _load_database_url_from_config()
        
        if database_url.startswith("sqlite:///"):
            # SQLite Restore
            db_path = database_url.replace("sqlite:///", "")
            
            import shutil
            shutil.copy2(backup_path, db_path)
            
            logger.info(f"✅ Datenbank aus Backup wiederhergestellt: {backup_path}")
            return True
        
        else:
            # Andere Datenbanken
            logger.warning("Restore für diese Datenbank-Art nicht implementiert")
            return False
            
    except Exception as e:
        logger.error(f"❌ Restore fehlgeschlagen: {e}")
        return False


def get_database_info():
    """Hole Datenbank-Informationen"""
    try:
        engine = create_database_engine()
        
        with engine.connect() as conn:
            # Hole Tabellen-Info
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            
            # Hole Größe-Info
            size_info = {}
            for table in tables:
                try:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    size_info[table] = count
                except Exception:
                    size_info[table] = 0
            
            return {
                'database_url': _load_database_url_from_config(),
                'tables': tables,
                'table_sizes': size_info,
                'total_tables': len(tables),
                'total_records': sum(size_info.values())
            }
            
    except Exception as e:
        logger.error(f"❌ Fehler beim Abrufen der Datenbank-Info: {e}")
        return None


__all__ = [
    "create_database_engine",
    "get_session_factory",
    "run_all_migrations",
    "check_migration_status",
    "rollback_migration",
    "backup_database",
    "restore_database",
    "get_database_info"
]
