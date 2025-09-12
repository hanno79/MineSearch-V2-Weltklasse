"""
Author: rahn
Datum: 27.08.2025
Version: 1.0
Beschreibung: Database Migrations für Sequential Field Orchestrator
"""

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
import logging
import re
from typing import Dict, Any, Optional, List
import os
import importlib

from .models import Base, Source, SourceDiscoverySession, ModelSourceContribution,
FieldSearchResult, SequentialSearchResult, FieldSearchSourceUsage

logger = logging.getLogger(__name__)

def _load_database_url_from_config() -> str:
    """
    Lädt die DATABASE_URL aus der Konfiguration über einen sicheren Importpfad.
    Verwendet einen bewachten Lazy-Import, um ImportError klar zu behandeln.

    Fallback: falls die Konfiguration nicht importiert werden kann, wird
    die Umgebungsvariable "DATABASE_URL" genutzt, sofern vorhanden.
    """
    try:
        config_module = importlib.import_module("minesearch.config.base")
    except ImportError as ie:
        logger.error("Konfiguration kann nicht importiert werden (minesearch.config.base): %s", ie)
        env_url = os.environ.get("DATABASE_URL")
        if env_url:
            logger.info("Verwende Fallback aus Umgebungsvariable DATABASE_URL")
            return env_url
        raise

    try:
        Config = getattr(config_module, "Config")
    except AttributeError:
        logger.error("Config-Klasse nicht in minesearch.config.base gefunden")
        env_url = os.environ.get("DATABASE_URL")
        if env_url:
            logger.info("Verwende Fallback aus Umgebungsvariable DATABASE_URL")
            return env_url
        raise ImportError("'Config' nicht in minesearch.config.base vorhanden")

    config = Config()
    database_url = getattr(config, "DATABASE_URL", None)
    if not database_url:
        logger.error("DATABASE_URL fehlt oder ist leer in der Konfiguration")
        env_url = os.environ.get("DATABASE_URL")
        if env_url:
            logger.info("Verwende Fallback aus Umgebungsvariable DATABASE_URL")
            return env_url
        raise ValueError("DATABASE_URL ist nicht gesetzt")

    return database_url


class SequentialMigrationManager:
    """
    ÄNDERUNG 27.08.2025: Migration Manager für Sequential Field Orchestrator
    Verwaltet Database Schema Updates für den neuen Workflow
    """

    def __init__(self, database_url: str):
    """__init__ - TODO: Dokumentation hinzufügen"""
        self.engine = create_engine(database_url)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def _validate_identifier(self, identifier: str) -> bool:
        """Whitelist-Validierung für SQL-Bezeichner (z. B. Tabellen-/Spaltennamen)."""
        return bool(re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', identifier))

    def _quote_identifier(self, identifier: str) -> str:
        """Dialect-spezifisches Quoten von SQL-Bezeichnern."""
        return self.engine.dialect.identifier_preparer.quote(identifier)

    def _sanitize_type_clause(self, clause: str) -> str:
        """Whitelist-Validierung des Typ-/Constraint-Teils für ALTER TABLE ... ADD COLUMN.
        Erlaubt sind Buchstaben/Ziffern/Unterstrich/Leerzeichen/Klammern/Komma/Punkt.
        Blockiert Steuerzeichen wie ;, --, /*, */.
        """
        if ";" in clause or "--" in clause or "/*" in clause or "*/" in clause:
            raise ValueError("Unsichere Zeichen in Typdefinition erkannt")
        if not re.match(r'^[A-Za-z0-9_(),.\s]+$', clause):
            raise ValueError("Unerlaubte Zeichen in Typdefinition")
        return clause.strip()

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
            if not self._validate_identifier(table_name):
                logger.error(f"[SequentialMigrationManager] Invalid table name: {table_name}")
                return []
            inspector = inspect(self.session.bind)
            columns_info = inspector.get_columns(table_name)
            columns = [col.get('name') for col in columns_info if col.get('name')]
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
            # Validierung der Bezeichner
            if not self._validate_identifier(table_name) or not self._validate_identifier(column_name):
                raise ValueError("Ungültiger Tabellen- oder Spaltenname")

            existing_columns = self.get_table_columns(table_name)
            if column_name not in existing_columns:
                # Unterstütze sowohl Definitionen mit als auch ohne Spaltennamen-Präfix
                definition = (column_definition or "").strip()
                if definition.lower().startswith(column_name.lower() + " "):
                    type_clause = definition[len(column_name):].strip()
                else:
                    type_clause = definition

                # Whitelist-basierte Validierung der Typ-/Constraint-Klausel
                type_clause = self._sanitize_type_clause(type_clause)

                quoted_table = self._quote_identifier(table_name)
                quoted_column = self._quote_identifier(column_name)
                sql = f"ALTER TABLE {quoted_table} ADD COLUMN {quoted_column} {type_clause}"
                self.session.execute(text(sql))
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

    def backfill_field_search_source_usage(self) -> bool:
        """
        Backfill: Überführe bestehende FieldSearchResult.sources_used_ids in
        die neue Assoziationstabelle field_search_source_usages.
        """
        logger.info("[SequentialMigrationManager] Starting backfill for field_search_source_usages...")
        try:
            # Prüfe, ob beide Tabellen existieren
            if not self.check_table_exists('field_search_results') or not
self.check_table_exists('field_search_source_usages'):
                logger.warning("[SequentialMigrationManager] Required tables for backfill do not
exist; skipping backfill")
                return True

            # Lade alle FieldSearchResults mit vorhandenen sources_used_ids
            results = self.session.query(FieldSearchResult).filter(
                FieldSearchResult.sources_used_ids.isnot(None)
            ).all()

            created = 0
            for fsr in results:
                try:
                    ids = fsr.sources_used_ids or []
                    # Normalisiere auf Integers
                    normalized_ids = []
                    for sid in ids:
                        try:
                            normalized_ids.append(int(sid))
                        except Exception:
                            # Überspringe nicht-konvertierbare Einträge
                            continue

                    # Erzeuge Assoziationen, vermeide Duplikate per UniqueConstraint
                    for sid in set(normalized_ids):
                        usage = FieldSearchSourceUsage(field_search_id=fsr.id, source_id=sid)
                        self.session.add(usage)
                        created += 1

                    # Optional: flush in Batches
                    if created % 500 == 0:
                        self.session.flush()

                except Exception as ie:
                    logger.error(f"[SequentialMigrationManager] Error backfilling FSR
id={getattr(fsr,'id',None)}: {ie}")
                    self.session.rollback()
            # Final commit
            self.session.commit()
            logger.info(f"[SequentialMigrationManager] Backfill completed, created ~{created} usage rows")
            return True
        except Exception as e:
            logger.error(f"[SequentialMigrationManager] Backfill failed: {e}")
            self.session.rollback()
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
            ("idx_sources_discovery_session", "CREATE INDEX IF NOT EXISTS
idx_sources_discovery_session ON sources(last_discovery_session, discovery_count)"),
            ("idx_sources_quality_usage", "CREATE INDEX IF NOT EXISTS idx_sources_quality_usage ON
sources(cumulative_quality_score, times_used_in_field_search)"),
            ("idx_source_discovery_sessions_mine", "CREATE INDEX IF NOT EXISTS
idx_source_discovery_sessions_mine ON source_discovery_sessions(mine_name, session_id)"),
            ("idx_source_discovery_sessions_phase", "CREATE INDEX IF NOT EXISTS
idx_source_discovery_sessions_phase ON source_discovery_sessions(phase, started_at)"),
            ("idx_model_contributions_session_model", "CREATE INDEX IF NOT EXISTS
idx_model_contributions_session_model ON model_source_contributions(session_id, model_id)"),
            ("idx_model_contributions_source", "CREATE INDEX IF NOT EXISTS
idx_model_contributions_source ON model_source_contributions(source_id, discovered_at)"),
            ("idx_field_search_session_field", "CREATE INDEX IF NOT EXISTS
idx_field_search_session_field ON field_search_results(session_id, field_name)"),
            ("idx_field_search_model_field", "CREATE INDEX IF NOT EXISTS
idx_field_search_model_field ON field_search_results(model_id, field_name, searched_at)"),
            ("idx_sequential_results_mine", "CREATE INDEX IF NOT EXISTS idx_sequential_results_mine
ON sequential_search_results(mine_name, created_at)"),
            ("idx_sequential_results_quality", "CREATE INDEX IF NOT EXISTS
idx_sequential_results_quality ON sequential_search_results(overall_quality_score,
completeness_percentage)")
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

    def ensure_mine_data_fields_on_update_cascade(self) -> bool:
        """
        Stellt sicher, dass der FK mine_data_fields.source_id → sources(id)
        die Klausel ON UPDATE CASCADE besitzt. Falls nicht, wird die Tabelle in SQLite
        per Rebuild (CREATE TABLE AS + COPY + RENAME) neu erstellt.
        """
        try:
            # Existiert Tabelle überhaupt?
            if not self.check_table_exists('mine_data_fields'):
                logging.info("[SequentialMigrationManager] 'mine_data_fields' nicht vorhanden – kein Rebuild nötig")
                return True

            # Prüfe aktuelle FK-Definition
            fk_rows = self.session.execute(text("PRAGMA foreign_key_list(mine_data_fields)"))
            rows = fk_rows.fetchall()
            on_update_ok = False
            for row in rows:
                # row Schema: (id, seq, table, from, to, on_update, on_delete, match)
                try:
                    ref_table = row[2]
                    from_col = row[3]
                    to_col = row[4]
                    on_update = (row[5] or '').upper()
                    if ref_table == 'sources' and from_col == 'source_id' and to_col == 'id':
                        if on_update == 'CASCADE':
                            on_update_ok = True
                            break
                except Exception:
                    continue

            if on_update_ok:
                logging.info("[SequentialMigrationManager] ON UPDATE CASCADE bereits aktiv für
mine_data_fields.source_id")
                return True

            logging.info("[SequentialMigrationManager] Rebuild von 'mine_data_fields' für ON UPDATE CASCADE gestartet…")

            # Temporär FK-Checks deaktivieren
            self.session.execute(text("PRAGMA foreign_keys=OFF"))

            # Temporäre Rebuild-Table bereinigen, falls von vorherigem Versuch vorhanden
            try:
                self.session.execute(text("DROP TABLE IF EXISTS mine_data_fields_new"))
            except Exception:
                pass

            # Neue Tabelle mit gewünschter Constraint anlegen
            create_new_sql = """
            CREATE TABLE IF NOT EXISTS mine_data_fields_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                search_result_id INTEGER NOT NULL,
                mine_id INTEGER NOT NULL,
                field_name VARCHAR(100) NOT NULL,
                raw_value TEXT,
                normalized_value TEXT,
                numeric_value DECIMAL(20,2),
                unit VARCHAR(50),
                confidence_score DECIMAL(3,2),
                is_template_value BOOLEAN DEFAULT FALSE,
                validation_status VARCHAR(20) DEFAULT 'valid' CHECK(validation_status IN ('valid',
'invalid', 'template', 'uncertain')),
                source_id INTEGER,
                source_name VARCHAR(500),
                model_used VARCHAR(100) NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (mine_id) REFERENCES mines_normalized(id) ON DELETE CASCADE,
                FOREIGN KEY (field_name) REFERENCES field_definitions(field_name) ON DELETE CASCADE,
                FOREIGN KEY (source_id) REFERENCES sources(id) ON DELETE SET NULL ON UPDATE CASCADE
            );
            """
            self.session.execute(text(create_new_sql))

            # Daten kopieren (inkl. id zur Beibehaltung der bestehenden IDs)
            copy_sql = text(
                """
                INSERT INTO mine_data_fields_new (
                    id, search_result_id, mine_id, field_name, raw_value, normalized_value,
                    numeric_value, unit, confidence_score, is_template_value, validation_status,
                    source_id, source_name, model_used, created_at, updated_at
                )
                SELECT
                    id, search_result_id, mine_id, field_name, raw_value, normalized_value,
                    numeric_value, unit, confidence_score, is_template_value, validation_status,
                    source_id, source_name, model_used, created_at, updated_at
                FROM mine_data_fields
                """
            )
            self.session.execute(copy_sql)

            # Abhängige Views, die mine_data_fields referenzieren, temporär droppen
            dependent_views = []
            try:
                view_rows = self.session.execute(text(
                    "SELECT name, sql FROM sqlite_master WHERE type='view' AND sql LIKE :pattern"
                ), {"pattern": "%mine_data_fields%"}).fetchall()
                for name, sql in view_rows:
                    if name and sql:
                        dependent_views.append((name, sql))
                # Drop all dependent views
                preparer = self.session.bind.dialect.identifier_preparer
                for name, _ in dependent_views:
                    quoted_name = preparer.quote(name)
                    self.session.execute(text(f"DROP VIEW IF EXISTS {quoted_name}"))
            except Exception as ve:
                logging.warning(f"[SequentialMigrationManager] Konnte Views nicht ermitteln/droppen: {ve}")

            # Alte Tabelle entfernen und neue umbenennen
            self.session.execute(text("DROP TABLE mine_data_fields"))
            self.session.execute(text("ALTER TABLE mine_data_fields_new RENAME TO mine_data_fields"))

            # Indizes neu erstellen
            index_sqls = [
                "CREATE INDEX IF NOT EXISTS idx_mine_fields_mine_id ON mine_data_fields(mine_id)",
                "CREATE INDEX IF NOT EXISTS idx_mine_fields_field_name ON mine_data_fields(field_name)",
                "CREATE INDEX IF NOT EXISTS idx_mine_fields_search_result ON mine_data_fields(search_result_id)",
                "CREATE INDEX IF NOT EXISTS idx_mine_fields_model ON mine_data_fields(model_used)",
                "CREATE INDEX IF NOT EXISTS idx_mine_fields_validation ON mine_data_fields(validation_status)",
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_mine_field_search ON
mine_data_fields(mine_id, field_name, search_result_id)"
            ]
            for sql in index_sqls:
                self.session.execute(text(sql))

            # Trigger neu erstellen
            trigger_sql = """
            CREATE TRIGGER IF NOT EXISTS update_mine_data_fields_timestamp
                AFTER UPDATE ON mine_data_fields
                WHEN NEW.updated_at IS OLD.updated_at
            BEGIN
                UPDATE mine_data_fields
                SET updated_at = CURRENT_TIMESTAMP
                WHERE id = NEW.id;
            END;
            """
            self.session.execute(text(trigger_sql))

            # Abhängige Views wiederherstellen
            for name, sql in dependent_views:
                try:
                    self.session.execute(text(sql))
                except Exception as re:
                    logging.error(f"[SequentialMigrationManager] Fehler beim Re-CREATE View {name}: {re}")
                    # Fail the migration if we cannot restore required view
                    raise

            # FK-Checks wieder aktivieren und committen
            self.session.execute(text("PRAGMA foreign_keys=ON"))
            self.session.commit()

            logging.info("[SequentialMigrationManager] Rebuild von 'mine_data_fields' abgeschlossen
– ON UPDATE CASCADE aktiv")
            return True

        except KeyError as e:
            logging.error(f"[SequentialMigrationManager] Fehler beim Rebuild von mine_data_fields: {e}")
            self.session.rollback()
            try:
                self.session.execute(text("PRAGMA foreign_keys=ON"))
            except Exception:
                pass
            return False

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
            ("Backfill field_search_source_usages", self.backfill_field_search_source_usage),
            ("Create indexes", self.create_indexes),
            ("Ensure mine_data_fields ON UPDATE CASCADE", self.ensure_mine_data_fields_on_update_cascade)
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
            'indexes_verified': {},
            'constraints_verified': {}
        }

        # Prüfe neue Tabellen
        new_tables = [
            'source_discovery_sessions',
            'model_source_contributions',
            'field_search_results',
            'field_search_source_usages',
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

        # Prüfe FK ON UPDATE CASCADE für mine_data_fields.source_id
        try:
            if self.check_table_exists('mine_data_fields'):
                fk_rows = self.session.execute(text("PRAGMA foreign_key_list(mine_data_fields)"))
                rows = fk_rows.fetchall()
                cascade_ok = False
                for row in rows:
                    try:
                        if row[2] == 'sources' and row[3] == 'source_id' and row[4] == 'id':
                            if (row[5] or '').upper() == 'CASCADE':
                                cascade_ok = True
                                break
                    except Exception:
                        continue
                results['constraints_verified']['mine_data_fields.source_id_on_update_cascade'] = cascade_ok
                if not cascade_ok:
                    results['migration_successful'] = False
        except Exception as e:
            logger.error(f"[SequentialMigrationManager] Error verifying mine_data_fields FK on_update: {e}")
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
    try:
        database_url = _load_database_url_from_config()
    except (ImportError, ValueError) as e:
        logger.error("[SequentialMigration] Konfiguration/Database URL konnte nicht geladen werden: %s", e)
        raise SystemExit(1)
    success = run_sequential_migration(database_url)

    if success:
        print("✅ Sequential Field Orchestrator Migration completed successfully!")
    else:
        print("❌ Migration failed!")
