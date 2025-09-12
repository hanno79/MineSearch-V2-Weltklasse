"""
Author: rahn
Datum: 03.09.2025
Version: 1.0
Beschreibung: Migration für missing Source-Spalten in normalisierte DB
"""

from sqlalchemy import text
from minesearch.database import db_manager
import logging

logger = logging.getLogger(__name__)

def add_missing_source_columns():
    """Fügt fehlende Spalten zur sources-Tabelle hinzu"""

    logger.info("🔧 [SOURCE-MIGRATION] Starte Migration für fehlende Source-Spalten")

    # Liste der fehlenden Spalten mit ihren Definitionen
    new_columns = [
        # Akkumulations-Tracking
        "discovery_count INTEGER NOT NULL DEFAULT 1",
        "first_discovered_by VARCHAR(100) NULL",
        "discovery_models JSON NULL",
        "last_discovery_session VARCHAR(100) NULL",

        # Qualitätsbewertung
        "cumulative_quality_score FLOAT NOT NULL DEFAULT 0.0",
        "field_specialization JSON NULL",
        "mine_specialization JSON NULL",

        # Sequential Search Statistiken
        "times_used_in_field_search INTEGER NOT NULL DEFAULT 0",
        "successful_field_extractions INTEGER NOT NULL DEFAULT 0",
        "field_extraction_success_rate FLOAT NOT NULL DEFAULT 0.0",

        # Metadaten
        "typical_content_types JSON NULL",
        "extra_metadata JSON NULL"
    ]

    try:
        with db_manager.get_session() as session:
            # Prüfe bestehende Spalten
            result = session.execute(text("PRAGMA table_info(sources)"))
            existing_columns = {row[1] for row in result.fetchall()}
            logger.info(f"✅ [SOURCE-MIGRATION] Bestehende Spalten: {len(existing_columns)}")

            # Füge fehlende Spalten hinzu
            added_count = 0
            for column_def in new_columns:
                column_name = column_def.split()[0]
                if column_name not in existing_columns:
                    try:
                        session.execute(text(f"ALTER TABLE sources ADD COLUMN {column_def}"))
                        added_count += 1
                        logger.info(f"✅ [SOURCE-MIGRATION] Spalte hinzugefügt: {column_name}")
                    except Exception as e:
                        logger.warning(f"⚠️ [SOURCE-MIGRATION] Konnte Spalte {column_name} nicht hinzufügen: {e}")
                else:
                    logger.info(f"⏭️ [SOURCE-MIGRATION] Spalte {column_name} existiert bereits")

            # Erstelle neue Indizes (falls nicht vorhanden)
            try:
                session.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_source_discovery_session
                    ON sources(last_discovery_session, discovery_count)
                """))
                session.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_source_quality_usage
                    ON sources(cumulative_quality_score, times_used_in_field_search)
                """))
                logger.info("✅ [SOURCE-MIGRATION] Neue Indizes erstellt")
            except Exception as e:
                logger.warning(f"⚠️ [SOURCE-MIGRATION] Index-Erstellung teilweise fehlgeschlagen: {e}")

            session.commit()
            logger.info(f"🎉 [SOURCE-MIGRATION] Migration abgeschlossen - {added_count} Spalten hinzugefügt")

            # Validierung: Prüfe finale Spaltenanzahl
            result = session.execute(text("PRAGMA table_info(sources)"))
            final_columns = result.fetchall()
            logger.info(f"✅ [SOURCE-MIGRATION] Finale Spaltenanzahl: {len(final_columns)}")

            return True

    except Exception as e:
        logger.error(f"❌ [SOURCE-MIGRATION] Migration fehlgeschlagen: {e}")
        return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    success = add_missing_source_columns()
    if success:
        print("🎉 SOURCE MIGRATION ERFOLGREICH")
    else:
        print("❌ SOURCE MIGRATION FEHLGESCHLAGEN")
