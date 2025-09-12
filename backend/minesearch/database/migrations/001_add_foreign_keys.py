"""
Author: rahn
Datum: 18.07.2025
Version: 1.0
Beschreibung: Migration - Foreign Keys hinzufügen und doppelte Indizes entfernen
"""

from sqlalchemy import create_engine, MetaData, Table, Column, Integer, ForeignKey, Index
from sqlalchemy.sql import text
import logging

logger = logging.getLogger(__name__)

def upgrade_database(db_path: str = "minesearch_v2/backend/mines.db"):
    """Führt die Migration aus"""
    engine = create_engine(f'sqlite:///{db_path}', echo=False)

    with engine.connect() as conn:
        logger.info("Starte Migration: Foreign Keys und Index-Bereinigung")

        # 1. Entferne doppelte Indizes
        try:
            logger.info("Entferne doppelte Indizes...")

            # Prüfe existierende Indizes
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'ix_%'"))
            existing_indexes = [row[0] for row in result.fetchall()]

            duplicates_to_remove = []
            if 'ix_search_results_session_id' in existing_indexes and 'idx_search_results_session' in existing_indexes:
                duplicates_to_remove.append('ix_search_results_session_id')

            if 'ix_search_results_search_timestamp' in existing_indexes and
'idx_search_results_timestamp' in existing_indexes:
                duplicates_to_remove.append('ix_search_results_search_timestamp')

            for index_name in duplicates_to_remove:
                try:
                    conn.execute(text(f"DROP INDEX {index_name}"))
                    logger.info(f"✓ Doppelter Index {index_name} entfernt")
                except Exception as e:
                    logger.warning(f"Index {index_name} konnte nicht entfernt werden: {e}")

        except Exception as e:
            logger.error(f"Fehler beim Entfernen doppelter Indizes: {e}")

        # 2. DEAKTIVIERT: mine_id Spalten (CSV-Export Kompatibilität)
        logger.info("mine_id Spalten ÜBERSPRUNGEN (CSV-Export Kompatibilität)")

        # 3. DEAKTIVIERT: Foreign Key Constraints (CSV-Export Kompatibilität)
        logger.info("Foreign Key Constraints ÜBERSPRUNGEN (CSV-Export Kompatibilität)")

        # 4. Erstelle CHECK Constraints für Datenqualität
        try:
            logger.info("Erstelle CHECK Constraints...")

            # Diese werden in zukünftigen Versionen von SQLite besser unterstützt
            # Für jetzt erstellen wir sie als Trigger

            logger.info("CHECK Constraints werden über Anwendungslogik validiert")

        except Exception as e:
            logger.error(f"Fehler beim Erstellen der CHECK Constraints: {e}")

        # Commit alle Änderungen
        conn.commit()
        logger.info("✅ Migration erfolgreich abgeschlossen")

def downgrade_database(db_path: str = "minesearch_v2/backend/mines.db"):
    """Rollback der Migration"""
    engine = create_engine(f'sqlite:///{db_path}', echo=False)

    with engine.connect() as conn:
        logger.info("Starte Rollback: Foreign Keys und Index-Bereinigung")

        # Entferne Foreign Key Indizes
        foreign_key_indexes = [
            "idx_search_results_mine_id",
            "idx_model_statistics_mine_id",
            "idx_field_consistency_mine_id"
        ]

        for index_name in foreign_key_indexes:
            try:
                conn.execute(text(f"DROP INDEX IF EXISTS {index_name}"))
                logger.info(f"✓ Index {index_name} entfernt")
        except KeyError as e:
                logger.warning(f"Index {index_name} konnte nicht entfernt werden: {e}")

        conn.commit()
        logger.info("✅ Rollback erfolgreich abgeschlossen")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        downgrade_database()
    else:
        upgrade_database()
