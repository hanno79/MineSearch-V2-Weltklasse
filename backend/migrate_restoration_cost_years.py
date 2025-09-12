"""
Author: rahn
Datum: 11.09.2025
Version: 1.0
Beschreibung: Migration Script für Restaurationskosten Jahre

Dieses Script analysiert vorhandene Restaurationskosten und versucht
das entsprechende Jahr aus dem "Jahr der Erstellung des Dokumentes"
oder anderen verfügbaren Daten zu extrahieren.
"""

import sqlite3
import logging
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RestorationCostYearMigration:
    """Migration für Restaurationskosten Jahre"""

    def __init__(self, db_path: str = 'mines.db'):
    """__init__ - TODO: Dokumentation hinzufügen"""
        self.db_path = db_path
        self.migration_stats = {
            'total_restoration_costs': 0,
            'costs_with_existing_year': 0,
            'costs_migrated_from_document_year': 0,
            'costs_migrated_from_pattern': 0,
            'costs_without_year': 0,
            'errors': 0
        }

    def run_migration(self):
        """Führt die komplette Migration aus"""
        logger.info("🚀 Starting Restaurationskosten Jahr Migration...")

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 1. Analysiere aktuelle Situation
            self._analyze_current_data(cursor)

            # 2. Finde Restaurationskosten ohne Jahr
            restoration_costs_without_year = self._find_costs_without_year(cursor)

            # 3. Migriere Jahre
            for cost_data in restoration_costs_without_year:
                self._migrate_single_cost_year(cursor, cost_data)

            # 4. Commit Changes
            conn.commit()

            # 5. Zeige Statistiken
            self._show_migration_stats()

            conn.close()

        except Exception as e:
            logger.error(f"❌ Migration fehler: {e}")
            self.migration_stats['errors'] += 1

    def _analyze_current_data(self, cursor):
        """Analysiert die aktuelle Datenlage"""
        logger.info("📊 Analysiere aktuelle Restaurationskosten...")

        # Zähle Restaurationskosten
        cursor.execute('''
            SELECT COUNT(*) FROM mine_data_fields
            WHERE field_name = 'Restaurationskosten'
        ''')
        self.migration_stats['total_restoration_costs'] = cursor.fetchone()[0]

        # Zähle bereits vorhandene Jahre
        cursor.execute('''
            SELECT COUNT(DISTINCT mdf_cost.mine_id)
            FROM mine_data_fields mdf_cost
            WHERE mdf_cost.field_name = 'Restaurationskosten'
            AND EXISTS (
                SELECT 1 FROM mine_data_fields mdf_year
                WHERE mdf_year.mine_id = mdf_cost.mine_id
                AND mdf_year.field_name = 'Jahr der Aufnahme der Kosten'
                AND mdf_year.primitive_value IS NOT NULL
                AND mdf_year.primitive_value != ''
            )
        ''')
        self.migration_stats['costs_with_existing_year'] = cursor.fetchone()[0]

        logger.info(f"  Total Restaurationskosten: {self.migration_stats['total_restoration_costs']}")
        logger.info(f"  Bereits mit Jahr: {self.migration_stats['costs_with_existing_year']}")

    def _find_costs_without_year(self, cursor) -> List[Dict]:
        """Findet Restaurationskosten ohne Jahr"""
        logger.info("🔍 Suche Restaurationskosten ohne Jahr...")

        cursor.execute('''
            SELECT
                mdf_cost.id as cost_id,
                mdf_cost.mine_id,
                m.name as mine_name,
                mdf_cost.primitive_value as cost_value,
                mdf_cost.session_id,
                mdf_cost.created_at as cost_created_at
            FROM mine_data_fields mdf_cost
            JOIN mines m ON mdf_cost.mine_id = m.id
            WHERE mdf_cost.field_name = 'Restaurationskosten'
            AND NOT EXISTS (
                SELECT 1 FROM mine_data_fields mdf_year
                WHERE mdf_year.mine_id = mdf_cost.mine_id
                AND mdf_year.field_name = 'Jahr der Aufnahme der Kosten'
                AND mdf_year.primitive_value IS NOT NULL
                AND mdf_year.primitive_value != ''
            )
            ORDER BY mdf_cost.mine_id, mdf_cost.created_at
        ''')

        results = [{
                'cost_id': row[0],
                'mine_id': row[1],
                'mine_name': row[2],
                'cost_value': row[3],
                'session_id': row[4],
                'cost_created_at': row[5]
            } for row in cursor.fetchall()]

        logger.info(f"  Gefunden: {len(results)} Restaurationskosten ohne Jahr")
        return results

    def _migrate_single_cost_year(self, cursor, cost_data: Dict):
        """Migriert Jahr für einzelne Restaurationskosten"""
        mine_id = cost_data['mine_id']
        mine_name = cost_data['mine_name']
        cost_value = cost_data['cost_value']

        logger.debug(f"🔄 Migriere Jahr für Mine {mine_name} (ID: {mine_id})")

        # Strategie 1: Jahr aus Kostenwert extrahieren (z.B. "$25.8M (2023)")
        extracted_year = self._extract_year_from_cost_value(cost_value)
        if extracted_year:
            self._create_cost_year_entry(cursor, cost_data, extracted_year, 'pattern')
            self.migration_stats['costs_migrated_from_pattern'] += 1
            logger.info(f"  ✅ {mine_name}: Jahr {extracted_year} aus Kostenwert extrahiert")
            return

        # Strategie 2: Jahr aus "Jahr der Erstellung des Dokumentes" ableiten
        document_year = self._get_document_year_for_mine(cursor, mine_id, cost_data['session_id'])
        if document_year:
            self._create_cost_year_entry(cursor, cost_data, document_year, 'document')
            self.migration_stats['costs_migrated_from_document_year'] += 1
            logger.info(f"  ✅ {mine_name}: Jahr {document_year} aus Dokumentjahr übernommen")
            return

        # Keine Lösung gefunden
        self.migration_stats['costs_without_year'] += 1
        logger.debug(f"  ❌ {mine_name}: Kein Jahr gefunden")

    def _extract_year_from_cost_value(self, cost_value: str) -> Optional[str]:
        """Extrahiert Jahr aus Kostenwert"""
        if not cost_value:
            return None

        # Pattern für Jahr in Klammern: "$25.8M (2023)", "12.8 Millionen CAD (2021)"
        patterns = [
            r'\((\d{4})\)',  # (2023)
            r'\[(\d{4})\]',  # [2023]
            r'(\d{4})',      # 2023 irgendwo im Text
        ]

        for pattern in patterns:
            match = re.search(pattern, cost_value)
            if match:
                year = match.group(1)
                # Validiere Jahr (1990-2030)
                if 1990 <= int(year) <= 2030:
                    return year

        return None

    def _get_document_year_for_mine(self, cursor, mine_id: int, session_id: str = None) -> Optional[str]:
        """Holt Dokumentjahr für eine Mine"""
        # Zuerst versuchen: Gleiches Session-ID (gleicher Suchvorgang)
        if session_id:
            cursor.execute('''
                SELECT primitive_value
                FROM mine_data_fields
                WHERE mine_id = ?
                AND field_name = 'Jahr der Erstellung des Dokumentes'
                AND session_id = ?
                AND primitive_value IS NOT NULL
                AND primitive_value != ''
                ORDER BY created_at DESC
                LIMIT 1
            ''', (mine_id, session_id))
            result = cursor.fetchone()
            if result:
                year = result[0]
                if self._is_valid_year(year):
                    return year

        # Fallback: Beliebiges Dokumentjahr für diese Mine
        cursor.execute('''
            SELECT primitive_value
            FROM mine_data_fields
            WHERE mine_id = ?
            AND field_name = 'Jahr der Erstellung des Dokumentes'
            AND primitive_value IS NOT NULL
            AND primitive_value != ''
            ORDER BY created_at DESC
            LIMIT 1
        ''', (mine_id,))
        result = cursor.fetchone()
        if result:
            year = result[0]
            if self._is_valid_year(year):
                return year

        return None

    def _is_valid_year(self, year_str: str) -> bool:
        """Validiert Jahr"""
        try:
            year = int(year_str)
            return 1990 <= year <= 2030
        except:
            return False

    def _create_cost_year_entry(self, cursor, cost_data: Dict, year: str, source: str):
        """Erstellt neuen Eintrag für Jahr der Aufnahme der Kosten"""
        cursor.execute('''
            INSERT INTO mine_data_fields (
                search_result_id, mine_id, field_name, field_type,
                primitive_value, numeric_value,
                confidence_score, is_template_value, validation_status,
                source_name, model_used, session_id,
                extraction_timestamp, created_at, updated_at
            ) VALUES (
                ?, ?, 'Jahr der Aufnahme der Kosten', 'primitive',
                ?, ?,
                0.8, 0, 'valid',
                ?, 'migration_script', ?,
                datetime('now'), datetime('now'), datetime('now')
            )
        ''', (
            cost_data.get("search_result_id", cost_data['cost_id']),  # Fallback zu cost_id
            cost_data['mine_id'],
            year,
            int(year),
            f'Migrated from {source}',
            cost_data['session_id']
        ))

    def _show_migration_stats(self):
        """Zeigt Migration-Statistiken"""
        logger.info("\n" + "="*60)
        logger.info("📊 MIGRATION STATISTICS")
        logger.info("="*60)
        logger.info(f"Total Restaurationskosten:           {self.migration_stats['total_restoration_costs']}")
        logger.info(f"Bereits mit Jahr (vor Migration):    {self.migration_stats['costs_with_existing_year']}")
        logger.info(f"Migriert aus Kostenwert-Pattern:     {self.migration_stats['costs_migrated_from_pattern']}")
        logger.info(f"Migriert aus Dokumentjahr:           {self.migration_stats['costs_migrated_from_document_year']}")
        logger.info(f"Ohne Jahr (nicht migrierbar):        {self.migration_stats['costs_without_year']}")
        logger.info(f"Fehler:                               {self.migration_stats['errors']}")

        total_migrated = (self.migration_stats['costs_migrated_from_pattern'] +
                         self.migration_stats['costs_migrated_from_document_year'])
        logger.info(f"\n✅ TOTAL MIGRIERT: {total_migrated}")

        if self.migration_stats['errors'] == 0:
            logger.info("🎉 Migration erfolgreich abgeschlossen!")
        else:
            logger.warning("⚠️  Migration mit Fehlern abgeschlossen!")


if __name__ == "__main__":
    migration = RestorationCostYearMigration()
    migration.run_migration()
