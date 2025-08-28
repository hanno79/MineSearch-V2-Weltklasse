"""
Author: rahn
Datum: 27.08.2025
Version: 1.0
Beschreibung: Database Migrations für Sequential Field Orchestrator
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging
from typing import Dict, Any, Optional, List

from .models import Base, Source, SourceDiscoverySession, ModelSourceContribution, FieldSearchResult, SequentialSearchResult

logger = logging.getLogger(__name__)


class SequentialMigrationManager:
    """
    ÄNDERUNG 27.08.2025: Migration Manager für Sequential Field Orchestrator
    Verwaltet Database Schema Updates für den neuen Workflow
    """
    
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
    
    def check_table_exists(self, table_name: str) -> bool:
        """
        Prüfe ob Tabelle existiert
        
        Args:
            table_name: Name der Tabelle
            
        Returns:
            True wenn Tabelle existiert
        """
        try:
            result = self.session.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name=:table_name"),
                {'table_name': table_name}
            ).fetchone()
            return result is not None
        except Exception as e:
            logger.error(f"[SequentialMigrationManager] Error checking table {table_name}: {e}")
            return False
    
    def get_table_columns(self, table_name: str) -> List[str]:
        """
        Ermittle existierende Spalten einer Tabelle
        
        Args:
            table_name: Name der Tabelle
            
        Returns:
            Liste der Spaltennamen
        """
        try:
            result = self.session.execute(text(f"PRAGMA table_info({table_name})"))
            columns = [row[1] for row in result.fetchall()]  # row[1] ist der column name
            return columns
        except Exception as e:
            logger.error(f"[SequentialMigrationManager] Error getting columns for {table_name}: {e}")
            return []
    
    def add_column_if_not_exists(self, table_name: str, column_name: str, column_definition: str) -> bool:
        """
        Füge Spalte hinzu falls sie nicht existiert
        
        Args:
            table_name: Name der Tabelle
            column_name: Name der Spalte
            column_definition: SQL Definition der Spalte
            
        Returns:
            True wenn erfolgreich
        """
        try:
            existing_columns = self.get_table_columns(table_name)
            if column_name not in existing_columns:
                self.session.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_definition}"))
                self.session.commit()
                logger.info(f"[SequentialMigrationManager] Added column {column_name} to {table_name}")
                return True
            else:
                logger.debug(f"[SequentialMigrationManager] Column {column_name} already exists in {table_name}")
                return True
        except Exception as e:
            logger.error(f"[SequentialMigrationManager] Error adding column {column_name} to {table_name}: {e}")
            self.session.rollback()
            return False
    
    def create_new_tables(self) -> bool:
        """
        Erstelle alle neuen Tabellen für Sequential Field Orchestrator
        
        Returns:
            True wenn erfolgreich
        """
        try:
            # Erstelle alle Tabellen die nicht existieren
            Base.metadata.create_all(self.engine, checkfirst=True)
            logger.info("[SequentialMigrationManager] Created all new tables")
            return True
        except Exception as e:
            logger.error(f"[SequentialMigrationManager] Error creating new tables: {e}")
            return False
    
    def migrate_sources_table(self) -> bool:
        """
        Migriere die Sources-Tabelle um neue Spalten für Sequential Orchestrator
        
        Returns:
            True wenn erfolgreich
        """
        logger.info("[SequentialMigrationManager] Starting sources table migration...")
        
        migrations = [
            ("discovery_count", "discovery_count INTEGER NOT NULL DEFAULT 1"),
            ("first_discovered_by", "first_discovered_by VARCHAR(100)"),
            ("discovery_models", "discovery_models JSON"),
            ("last_discovery_session", "last_discovery_session VARCHAR(100)"),
            ("cumulative_quality_score", "cumulative_quality_score FLOAT NOT NULL DEFAULT 0.0"),
            ("field_specialization", "field_specialization JSON"),
            ("mine_specialization", "mine_specialization JSON"),
            ("times_used_in_field_search", "times_used_in_field_search INTEGER NOT NULL DEFAULT 0"),
            ("successful_field_extractions", "successful_field_extractions INTEGER NOT NULL DEFAULT 0"),
            ("field_extraction_success_rate", "field_extraction_success_rate FLOAT NOT NULL DEFAULT 0.0")
        ]
        
        success = True
        for column_name, column_definition in migrations:
            if not self.add_column_if_not_exists("sources", column_name, column_definition):
                success = False
        
        if success:
            logger.info("[SequentialMigrationManager] Sources table migration completed successfully")
        else:
            logger.error("[SequentialMigrationManager] Sources table migration failed")
        
        return success
    
    def create_indexes(self) -> bool:
        """
        Erstelle zusätzliche Indizes für Performance
        
        Returns:
            True wenn erfolgreich
        """
        indexes = [
            ("idx_sources_discovery_session", "CREATE INDEX IF NOT EXISTS idx_sources_discovery_session ON sources(last_discovery_session, discovery_count)"),
            ("idx_sources_quality_usage", "CREATE INDEX IF NOT EXISTS idx_sources_quality_usage ON sources(cumulative_quality_score, times_used_in_field_search)"),
            ("idx_source_discovery_sessions_mine", "CREATE INDEX IF NOT EXISTS idx_source_discovery_sessions_mine ON source_discovery_sessions(mine_name, session_id)"),
            ("idx_source_discovery_sessions_phase", "CREATE INDEX IF NOT EXISTS idx_source_discovery_sessions_phase ON source_discovery_sessions(phase, started_at)"),
            ("idx_model_contributions_session_model", "CREATE INDEX IF NOT EXISTS idx_model_contributions_session_model ON model_source_contributions(session_id, model_id)"),
            ("idx_model_contributions_source", "CREATE INDEX IF NOT EXISTS idx_model_contributions_source ON model_source_contributions(source_id, discovered_at)"),
            ("idx_field_search_session_field", "CREATE INDEX IF NOT EXISTS idx_field_search_session_field ON field_search_results(session_id, field_name)"),
            ("idx_field_search_model_field", "CREATE INDEX IF NOT EXISTS idx_field_search_model_field ON field_search_results(model_id, field_name, searched_at)"),
            ("idx_sequential_results_mine", "CREATE INDEX IF NOT EXISTS idx_sequential_results_mine ON sequential_search_results(mine_name, created_at)"),
            ("idx_sequential_results_quality", "CREATE INDEX IF NOT EXISTS idx_sequential_results_quality ON sequential_search_results(overall_quality_score, completeness_percentage)")
        ]
        
        success = True
        for index_name, index_sql in indexes:
            try:
                self.session.execute(text(index_sql))
                self.session.commit()
                logger.debug(f"[SequentialMigrationManager] Created index: {index_name}")
            except Exception as e:
                logger.error(f"[SequentialMigrationManager] Error creating index {index_name}: {e}")
                success = False
                self.session.rollback()
        
        if success:
            logger.info("[SequentialMigrationManager] All indexes created successfully")
        
        return success
    
    def run_full_migration(self) -> bool:
        """
        Führe vollständige Migration durch
        
        Returns:
            True wenn erfolgreich
        """
        logger.info("[SequentialMigrationManager] Starting full migration for Sequential Field Orchestrator...")
        
        steps = [
            ("Create new tables", self.create_new_tables),
            ("Migrate sources table", self.migrate_sources_table),
            ("Create indexes", self.create_indexes)
        ]
        
        success = True
        for step_name, step_func in steps:
            logger.info(f"[SequentialMigrationManager] Running: {step_name}")
            if not step_func():
                logger.error(f"[SequentialMigrationManager] Failed: {step_name}")
                success = False
                break
            logger.info(f"[SequentialMigrationManager] Completed: {step_name}")
        
        if success:
            logger.info("[SequentialMigrationManager] Full migration completed successfully!")
        else:
            logger.error("[SequentialMigrationManager] Migration failed!")
        
        return success
    
    def verify_migration(self) -> Dict[str, Any]:
        """
        Verifiziere Migration
        
        Returns:
            Verification results
        """
        results = {
            'migration_successful': True,
            'tables_verified': {},
            'columns_verified': {},
            'indexes_verified': {}
        }
        
        # Prüfe neue Tabellen
        new_tables = [
            'source_discovery_sessions',
            'model_source_contributions', 
            'field_search_results',
            'sequential_search_results'
        ]
        
        for table in new_tables:
            exists = self.check_table_exists(table)
            results['tables_verified'][table] = exists
            if not exists:
                results['migration_successful'] = False
        
        # Prüfe neue Spalten in sources
        if self.check_table_exists('sources'):
            new_columns = [
                'discovery_count', 'first_discovered_by', 'discovery_models',
                'last_discovery_session', 'cumulative_quality_score',
                'field_specialization', 'mine_specialization',
                'times_used_in_field_search', 'successful_field_extractions',
                'field_extraction_success_rate'
            ]
            
            existing_columns = self.get_table_columns('sources')
            for column in new_columns:
                exists = column in existing_columns
                results['columns_verified'][f'sources.{column}'] = exists
                if not exists:
                    results['migration_successful'] = False
        
        # Prüfe Indizes (vereinfachte Prüfung)
        try:
            result = self.session.execute(text("SELECT name FROM sqlite_master WHERE type='index'"))
            existing_indexes = [row[0] for row in result.fetchall()]
            
            expected_indexes = [
                'idx_sources_discovery_session',
                'idx_sources_quality_usage', 
                'idx_source_discovery_sessions_mine',
                'idx_source_discovery_sessions_phase'
            ]
            
            for index in expected_indexes:
                exists = index in existing_indexes
                results['indexes_verified'][index] = exists
                if not exists:
                    results['migration_successful'] = False
                    
        except Exception as e:
            logger.error(f"[SequentialMigrationManager] Error verifying indexes: {e}")
            results['migration_successful'] = False
        
        return results
    
    def close(self):
        """Schließe Database Session"""
        self.session.close()


def run_sequential_migration(database_url: str) -> bool:
    """
    Convenience function to run migration
    
    Args:
        database_url: Database URL
        
    Returns:
        True wenn erfolgreich
    """
    migration_manager = SequentialMigrationManager(database_url)
    
    try:
        # Run migration
        success = migration_manager.run_full_migration()
        
        if success:
            # Verify migration
            verification = migration_manager.verify_migration()
            if verification['migration_successful']:
                logger.info("[SequentialMigration] Migration and verification successful!")
                return True
            else:
                logger.error(f"[SequentialMigration] Migration verification failed: {verification}")
                return False
        else:
            logger.error("[SequentialMigration] Migration failed!")
            return False
            
    finally:
        migration_manager.close()


if __name__ == "__main__":
    # Test migration with configured database
    from minesearch.config.base import Config
    config = Config()
    database_url = config.DATABASE_URL
    success = run_sequential_migration(database_url)
    
    if success:
        print("✅ Sequential Field Orchestrator Migration completed successfully!")
    else:
        print("❌ Migration failed!")