#!/usr/bin/env python3
"""
Author: rahn
Datum: 07.09.2025
Version: 1.0
Beschreibung: Bereinigung falscher Einträge aus Lookup-Tabellen
"""

import sqlite3
import json
import re
from datetime import datetime
from typing import Dict, List, Set, Tuple
import logging

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LookupTableCleaner:
    """
    Bereinigt falsche Einträge aus Lookup-Tabellen und merged Duplikate
    """

    def __init__(self, db_path: str = 'mines.db'):
    """__init__ - TODO: Dokumentation hinzufügen"""
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()

        # Backup-Zeitstempel
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.cleanup_report = {
            'timestamp': self.timestamp,
            'tables_cleaned': {},
            'merged_duplicates': {},
            'deleted_entries': {},
            'backup_created': True
        }

    def create_backup(self):
        """Erstelle Backup vor Bereinigung"""
        try:
            backup_path = f'mines_backup_before_cleanup_{self.timestamp}.db'

            # SQLite Backup
            backup_conn = sqlite3.connect(backup_path)
            self.conn.backup(backup_conn)
            backup_conn.close()

            logger.info(f"✅ Backup erstellt: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"❌ Backup-Erstellung fehlgeschlagen: {e}")
            raise

    def is_problematic_entry(self, value: str, table_type: str) -> bool:
        """
        Prüft ob ein Eintrag problematisch ist und entfernt werden sollte
        """
        if not value or not isinstance(value, str):
            return True

        value = value.strip()
        if len(value) == 0:
            return True

        # Allgemeine problematische Patterns
        general_problematic = [
            r'ist\s+eine?\s+bedeutende?\s+.*mine',     # "Ist Eine Bedeutende Untertage-Goldmine"
            r'war\s+eine?\s+.*betrieb',                # "War Ein Kleiner Untertagebetrieb"
            r'für\s+.*\s+handelt',                     # "Für Kupfer Und Zink Handelt"
            r'spezifisch\s+als.*in.*berichten',       # "Spezifisch Als ... In Berichten"
            r'is\s+known\s+to\s+have\s+been',         # "Is known to have been operational"
            r'exact\s+production\s+figures',          # "exact production figures"
            r'dokumentiert\s+im\s+.*bergbau',         # "Dokumentiert Im Quebec Bergbauregister"
            r'mehrdeutige\s+eigentums',               # "Mehrdeutige Eigentumsverhältnisse"
            r'ohne\s+aktuelle\s+primärquellen',      # "Ohne Aktuelle Primärquellen"
            r'https?://',                              # URLs
            r'www\.',                                  # Web addresses
            r'\(\d+\.?\d*%\)',                        # Percentages in parentheses
            r'/\d{4}//',                               # "/1998//" patterns
            r'project.*auf\s+sedar',                  # "Project auf Sedar"
            r'von.*corporation.*betrieben',           # "von ... Corporation betrieben"
            r'nur\s+von\s+\d{4}-\d{4}\s+aktiv',     # "nur von 1972-1975 aktiv"
            r'bestätigt.*berichten',                   # "bestätigt ... Berichten"
        ]

        value_lower = value.lower()

        # Prüfe allgemeine Patterns
        for pattern in general_problematic:
            if re.search(pattern, value_lower):
                return True

        # Spezifische Prüfungen je Tabellentyp
        if table_type == 'commodities':
            return self._is_problematic_commodity(value, value_lower)
        elif table_type == 'companies':
            return self._is_problematic_company(value, value_lower)
        elif table_type == 'mine_types':
            return self._is_problematic_mine_type(value, value_lower)
        elif table_type == 'activity_statuses':
            return self._is_problematic_activity_status(value, value_lower)
        elif table_type == 'regions':
            return self._is_problematic_region(value, value_lower)

        return False

    def _is_problematic_commodity(self, value: str, value_lower: str) -> bool:
        """Spezifische Prüfung für Commodities"""
        # Zu lang für Rohstoff-Namen
        if len(value) > 80:
            return True

        # Enthält Beschreibungen statt Rohstoff-Namen
        commodity_bad_patterns = [
            'goldmine', 'kupfermine', 'eisenmine',
            'bedeutende', 'kleiner', 'untertagebetrieb',
            'production figures', 'operational for',
            'extraction, but exact', 'current owner'
        ]

        for pattern in commodity_bad_patterns:
            if pattern in value_lower:
                return True

        return False

    def _is_problematic_company(self, value: str, value_lower: str) -> bool:
        """Spezifische Prüfung für Companies"""
        # Definitiv keine Firmennamen
        company_bad_patterns = [
            'dokumentiert im', 'bergbauregister', 'unternehmensberichten',
            'mehrdeutige eigentumsverhältnisse', 'primärquellen',
            'quebec bergbau', 'government reports'
        ]

        for pattern in company_bad_patterns:
            if pattern in value_lower:
                return True

        # Komplexe Ownership-Listen mit Prozenten (zu komplex für einzelnen Firmennamen)
        if value.count('%') >= 2 and value.count(',') >= 2:
            return True

        return False

    def _is_problematic_mine_type(self, value: str, value_lower: str) -> bool:
        """Spezifische Prüfung für Mine Types"""
        # Enthält URLs oder komplexe Daten
        if any(x in value for x in ['http://', 'https://', 'mern.gouv', '//', '%C3%A9']):
            return True

        # Enthält Jahreszahlen, Tonnage, URLs (nicht atomare Minentyp-Werte)
        if re.search(r'/\d{4}/.*T/', value):
            return True

        # Zu komplexe Beschreibungen
        if len(value) > 60:
            return True

        return False

    def _is_problematic_activity_status(self, value: str, value_lower: str) -> bool:
        """Spezifische Prüfung für Activity Status"""
        # Sollte kurz und atomisch sein
        if len(value) > 50:
            return True

        # Beschreibungen statt Status
        if any(x in value_lower for x in ['mine is', 'since', 'operational for', 'figures']):
            return True

        return False

    def _is_problematic_region(self, value: str, value_lower: str) -> bool:
        """Spezifische Prüfung für Regions"""
        # URLs oder zu komplexe Beschreibungen
        if any(x in value for x in ['http://', 'https://', 'www.']):
            return True

        # Zu lang für Region
        if len(value) > 100:
            return True

        return False

    def clean_activity_statuses(self):
        """Bereinige Activity Statuses und merge Duplikate"""
        logger.info("🔍 Bereinige Activity Statuses...")

        # Hole alle Einträge
        self.cursor.execute("SELECT id, status FROM activity_statuses")
        entries = self.cursor.fetchall()

        deleted_count = 0
        merged_count = 0

        # Duplikat-Mappings (Explorationsphase → Exploration)
        duplicate_mappings = {
            'explorationsphase': 'exploration',
            'operating': 'aktiv',
            'operational': 'aktiv',
            'closed': 'geschlossen',
            'abandoned': 'geschlossen',
            'planned': 'geplant',
            'proposed': 'geplant'
        }

        for entry_id, status in entries:
            if self.is_problematic_entry(status, 'activity_statuses'):
                # Lösche problematischen Eintrag
                self.cursor.execute("DELETE FROM activity_statuses WHERE id = ?", (entry_id,))
                deleted_count += 1
                logger.info(f"❌ Gelöscht: Activity Status '{status[:60]}...'")
            else:
                # Prüfe auf Duplikate
                status_lower = status.lower().strip()
                if status_lower in duplicate_mappings:
                    target_status = duplicate_mappings[status_lower]

                    # Finde Target-ID
                    self.cursor.execute("SELECT id FROM activity_statuses WHERE LOWER(status) = ?", (target_status,))
                    target_result = self.cursor.fetchone()

                    if target_result:
                        target_id = target_result[0]

                        # Update alle mine_data_fields die diesen Status referenzieren
                        self.cursor.execute("""
                            UPDATE mine_data_fields
                            SET activity_status_id = ?
                            WHERE activity_status_id = ?
                        """, (target_id, entry_id))

                        # Lösche Duplikat
                        self.cursor.execute("DELETE FROM activity_statuses WHERE id = ?", (entry_id,))
                        merged_count += 1
                        logger.info(f"🔄 Merged: '{status}' → '{target_status}'")

        self.cleanup_report['tables_cleaned']['activity_statuses'] = {
            'deleted': deleted_count,
            'merged': merged_count,
            'total_processed': len(entries)
        }

        logger.info(f"✅ Activity Statuses: {deleted_count} gelöscht, {merged_count} gemerged")

    def clean_commodities(self):
        """Bereinige Commodities"""
        logger.info("🔍 Bereinige Commodities...")

        self.cursor.execute("SELECT id, name FROM commodities")
        entries = self.cursor.fetchall()

        deleted_count = 0

        for entry_id, name in entries:
            if self.is_problematic_entry(name, 'commodities'):
                # Update mine_data_fields zu NULL
                self.cursor.execute("""
                    UPDATE mine_data_fields
                    SET commodity_id = NULL
                    WHERE commodity_id = ?
                """, (entry_id,))

                # Lösche Eintrag
                self.cursor.execute("DELETE FROM commodities WHERE id = ?", (entry_id,))
                deleted_count += 1
                logger.info(f"❌ Gelöscht: Commodity '{name[:80]}...'")

        self.cleanup_report['tables_cleaned']['commodities'] = {
            'deleted': deleted_count,
            'total_processed': len(entries)
        }

        logger.info(f"✅ Commodities: {deleted_count} gelöscht")

    def clean_companies(self):
        """Bereinige Companies"""
        logger.info("🔍 Bereinige Companies...")

        self.cursor.execute("SELECT id, name FROM companies")
        entries = self.cursor.fetchall()

        deleted_count = 0

        for entry_id, name in entries:
            if self.is_problematic_entry(name, 'companies'):
                # Update mine_data_fields zu NULL
                self.cursor.execute("""
                    UPDATE mine_data_fields
                    SET company_id = NULL
                    WHERE company_id = ?
                """, (entry_id,))

                # Lösche Eintrag
                self.cursor.execute("DELETE FROM companies WHERE id = ?", (entry_id,))
                deleted_count += 1
                logger.info(f"❌ Gelöscht: Company '{name[:80]}...'")

        self.cleanup_report['tables_cleaned']['companies'] = {
            'deleted': deleted_count,
            'total_processed': len(entries)
        }

        logger.info(f"✅ Companies: {deleted_count} gelöscht")

    def clean_mine_types(self):
        """Bereinige Mine Types"""
        logger.info("🔍 Bereinige Mine Types...")

        self.cursor.execute("SELECT id, name FROM mine_types")
        entries = self.cursor.fetchall()

        deleted_count = 0
        merged_count = 0

        # Duplikat-Mappings
        duplicate_mappings = {
            'underground/souterrain': 'underground',
            'open-pit/à ciel ouvert': 'open-pit',
            'proposed open-pit/projet à ciel ouvert': 'open-pit',
            'exploration project/projet d\'exploration': 'exploration'
        }

        for entry_id, name in entries:
            if self.is_problematic_entry(name, 'mine_types'):
                # Update mine_data_fields zu NULL
                self.cursor.execute("""
                    UPDATE mine_data_fields
                    SET mine_type_id = NULL
                    WHERE mine_type_id = ?
                """, (entry_id,))

                # Lösche Eintrag
                self.cursor.execute("DELETE FROM mine_types WHERE id = ?", (entry_id,))
                deleted_count += 1
                logger.info(f"❌ Gelöscht: Mine Type '{name[:80]}...'")
            else:
                # Prüfe auf Duplikate
                name_lower = name.lower().strip()
                if name_lower in duplicate_mappings:
                    target_type = duplicate_mappings[name_lower]

                    # Finde Target-ID
                    self.cursor.execute("SELECT id FROM mine_types WHERE LOWER(name) = ?", (target_type,))
                    target_result = self.cursor.fetchone()

                    if target_result:
                        target_id = target_result[0]

                        # Update mine_data_fields
                        self.cursor.execute("""
                            UPDATE mine_data_fields
                            SET mine_type_id = ?
                            WHERE mine_type_id = ?
                        """, (target_id, entry_id))

                        # Lösche Duplikat
                        self.cursor.execute("DELETE FROM mine_types WHERE id = ?", (entry_id,))
                        merged_count += 1
                        logger.info(f"🔄 Merged: '{name}' → '{target_type}'")

        self.cleanup_report['tables_cleaned']['mine_types'] = {
            'deleted': deleted_count,
            'merged': merged_count,
            'total_processed': len(entries)
        }

        logger.info(f"✅ Mine Types: {deleted_count} gelöscht, {merged_count} gemerged")

    def clean_regions(self):
        """Bereinige Regions und merge Quebec-Duplikate"""
        logger.info("🔍 Bereinige Regions...")

        self.cursor.execute("SELECT id, name FROM regions")
        entries = self.cursor.fetchall()

        deleted_count = 0
        merged_count = 0

        # Quebec Duplikat-Mappings
        quebec_variants = ['québec', 'quebec', 'québec/nord-du-québec', 'nord-du-québec']
        target_quebec = 'quebec'  # Standard

        for entry_id, name in entries:
            if self.is_problematic_entry(name, 'regions'):
                # Update mine_data_fields zu NULL
                self.cursor.execute("""
                    UPDATE mine_data_fields
                    SET region_id = NULL
                    WHERE region_id = ?
                """, (entry_id,))

                # Lösche Eintrag
                self.cursor.execute("DELETE FROM regions WHERE id = ?", (entry_id,))
                deleted_count += 1
                logger.info(f"❌ Gelöscht: Region '{name[:80]}...'")
            else:
                # Prüfe Quebec-Duplikate
                name_lower = name.lower().strip()
                if name_lower in quebec_variants and name_lower != target_quebec:
                    # Finde Target Quebec
                    self.cursor.execute("SELECT id FROM regions WHERE LOWER(name) = ?", (target_quebec,))
                    target_result = self.cursor.fetchone()

                    if target_result:
                        target_id = target_result[0]

                        # Update mine_data_fields
                        self.cursor.execute("""
                            UPDATE mine_data_fields
                            SET region_id = ?
                            WHERE region_id = ?
                        """, (target_id, entry_id))

                        # Lösche Duplikat
                        self.cursor.execute("DELETE FROM regions WHERE id = ?", (entry_id,))
                        merged_count += 1
                        logger.info(f"🔄 Merged: '{name}' → 'Quebec'")

        self.cleanup_report['tables_cleaned']['regions'] = {
            'deleted': deleted_count,
            'merged': merged_count,
            'total_processed': len(entries)
        }

        logger.info(f"✅ Regions: {deleted_count} gelöscht, {merged_count} gemerged")

    def generate_report(self):
        """Erstelle Bereinigungsreport"""
        report_path = f'lookup_cleanup_report_{self.timestamp}.json'

        # Füge Statistiken hinzu
        total_deleted = sum(
            table_stats.get("deleted", 0)
            for table_stats in self.cleanup_report['tables_cleaned'].values()
        )
        total_merged = sum(
            table_stats.get("merged", 0)
            for table_stats in self.cleanup_report['tables_cleaned'].values()
        )

        self.cleanup_report['summary'] = {
            'total_deleted': total_deleted,
            'total_merged': total_merged,
            'tables_processed': len(self.cleanup_report['tables_cleaned'])
        }

        # Speichere Report
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.cleanup_report, f, indent=2, ensure_ascii=False)

        logger.info(f"📊 Report gespeichert: {report_path}")
        return report_path

    def run_full_cleanup(self):
        """Führe vollständige Bereinigung durch"""
        logger.info("🚀 STARTE VOLLSTÄNDIGE LOOKUP-TABELLEN BEREINIGUNG")
        logger.info("=" * 60)

        try:
            # Backup erstellen
            backup_path = self.create_backup()

            # Bereinige alle Tabellen
            self.clean_activity_statuses()
            self.clean_commodities()
            self.clean_companies()
            self.clean_mine_types()
            self.clean_regions()

            # Commit alle Änderungen
            self.conn.commit()

            # Report erstellen
            report_path = self.generate_report()

            logger.info("=" * 60)
            logger.info("✅ BEREINIGUNG ERFOLGREICH ABGESCHLOSSEN")
            logger.info(f"📁 Backup: {backup_path}")
            logger.info(f"📊 Report: {report_path}")

            # Zeige Zusammenfassung
            summary = self.cleanup_report['summary']
            logger.info(f"🗑️  Gesamt gelöscht: {summary['total_deleted']} Einträge")
            logger.info(f"🔄 Gesamt gemerged: {summary['total_merged']} Duplikate")
            logger.info(f"📋 Tabellen verarbeitet: {summary['tables_processed']}")

            return True

        except Exception as e:
            logger.error(f"❌ Bereinigung fehlgeschlagen: {e}")
            self.conn.rollback()
            return False
        finally:
            self.conn.close()


def main():
    """Hauptfunktion"""
    cleaner = LookupTableCleaner()
    success = cleaner.run_full_cleanup()

    if success:
        print("✅ LOOKUP-TABELLEN BEREINIGUNG ERFOLGREICH ABGESCHLOSSEN")
        print("Die Datenbank enthält jetzt nur noch saubere, atomare Werte.")
    else:
        print("❌ Bereinigung fehlgeschlagen - prüfe Logs für Details")


if __name__ == "__main__":
    main()
