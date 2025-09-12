#!/usr/bin/env python3
"""
Compact Lookup Table Cleaner
Kompakte Version des Lookup Table Cleaners

Author: MineSearch Development Team
Date: 2025-01-11
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
    """Bereinigt falsche Einträge aus Lookup-Tabellen und merged Duplikate"""

    def __init__(self, db_path: str = 'mines.db'):
        """Initialisiere Lookup Table Cleaner"""
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.cleanup_stats = {
            'duplicates_removed': 0,
            'invalid_entries_removed': 0,
            'tables_cleaned': 0,
            'start_time': datetime.now()
        }

    def cleanup_all_tables(self):
        """Bereinige alle Lookup-Tabellen"""
        try:
            logger.info("🧹 Starte Bereinigung aller Lookup-Tabellen...")
            
            # Liste der zu bereinigenden Tabellen
            tables_to_clean = [
                'countries', 'regions', 'commodities', 'operational_statuses',
                'mining_companies', 'mining_methods', 'processing_methods'
            ]
            
            for table in tables_to_clean:
                try:
                    self._cleanup_table(table)
                    self.cleanup_stats['tables_cleaned'] += 1
                except Exception as e:
                    logger.warning(f"Fehler beim Bereinigen der Tabelle {table}: {e}")
            
            # Generiere Bericht
            self._generate_cleanup_report()
            
            logger.info("✅ Bereinigung aller Lookup-Tabellen abgeschlossen")
            
        except Exception as e:
            logger.error(f"Fehler bei der Bereinigung: {e}")

    def _cleanup_table(self, table_name: str):
        """Bereinige einzelne Tabelle"""
        try:
            logger.info(f"🧹 Bereinige Tabelle: {table_name}")
            
            # Prüfe ob Tabelle existiert
            if not self._table_exists(table_name):
                logger.warning(f"Tabelle {table_name} existiert nicht")
                return
            
            # Entferne Duplikate
            duplicates_removed = self._remove_duplicates(table_name)
            self.cleanup_stats['duplicates_removed'] += duplicates_removed
            
            # Entferne ungültige Einträge
            invalid_removed = self._remove_invalid_entries(table_name)
            self.cleanup_stats['invalid_entries_removed'] += invalid_removed
            
            # Optimiere Tabelle
            self._optimize_table(table_name)
            
            logger.info(f"✅ Tabelle {table_name} bereinigt: {duplicates_removed} Duplikate, {invalid_removed} ungültige Einträge entfernt")
            
        except Exception as e:
            logger.error(f"Fehler beim Bereinigen der Tabelle {table_name}: {e}")

    def _table_exists(self, table_name: str) -> bool:
        """Prüfe ob Tabelle existiert"""
        try:
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            return self.cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"Fehler beim Prüfen der Tabelle {table_name}: {e}")
            return False

    def _remove_duplicates(self, table_name: str) -> int:
        """Entferne Duplikate aus Tabelle"""
        try:
            # Hole Spalten der Tabelle
            columns = self._get_table_columns(table_name)
            if not columns:
                return 0
            
            # Erstelle temporäre Tabelle ohne Duplikate
            temp_table = f"{table_name}_temp"
            self.cursor.execute(f"CREATE TABLE {temp_table} AS SELECT DISTINCT * FROM {table_name}")
            
            # Zähle entfernte Duplikate
            self.cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            original_count = self.cursor.fetchone()[0]
            
            self.cursor.execute(f"SELECT COUNT(*) FROM {temp_table}")
            new_count = self.cursor.fetchone()[0]
            
            duplicates_removed = original_count - new_count
            
            # Ersetze ursprüngliche Tabelle
            self.cursor.execute(f"DROP TABLE {table_name}")
            self.cursor.execute(f"ALTER TABLE {temp_table} RENAME TO {table_name}")
            
            self.conn.commit()
            return duplicates_removed
            
        except Exception as e:
            logger.error(f"Fehler beim Entfernen von Duplikaten aus {table_name}: {e}")
            return 0

    def _remove_invalid_entries(self, table_name: str) -> int:
        """Entferne ungültige Einträge aus Tabelle"""
        try:
            # Hole Spalten der Tabelle
            columns = self._get_table_columns(table_name)
            if not columns:
                return 0
            
            # Entferne Einträge mit leeren oder ungültigen Werten
            invalid_conditions = []
            for column in columns:
                invalid_conditions.append(f"({column} IS NULL OR {column} = '' OR {column} = 'N/A' OR {column} = 'Unknown')")
            
            where_clause = " OR ".join(invalid_conditions)
            
            # Zähle ungültige Einträge
            self.cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {where_clause}")
            invalid_count = self.cursor.fetchone()[0]
            
            # Entferne ungültige Einträge
            if invalid_count > 0:
                self.cursor.execute(f"DELETE FROM {table_name} WHERE {where_clause}")
                self.conn.commit()
            
            return invalid_count
            
        except Exception as e:
            logger.error(f"Fehler beim Entfernen ungültiger Einträge aus {table_name}: {e}")
            return 0

    def _get_table_columns(self, table_name: str) -> List[str]:
        """Hole Spalten einer Tabelle"""
        try:
            self.cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [row[1] for row in self.cursor.fetchall()]
            return columns
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Spalten für {table_name}: {e}")
            return []

    def _optimize_table(self, table_name: str):
        """Optimiere Tabelle"""
        try:
            # VACUUM für SQLite
            self.cursor.execute(f"VACUUM {table_name}")
            
            # ANALYZE für bessere Query-Performance
            self.cursor.execute(f"ANALYZE {table_name}")
            
            self.conn.commit()
            
        except Exception as e:
            logger.error(f"Fehler beim Optimieren der Tabelle {table_name}: {e}")

    def _generate_cleanup_report(self):
        """Generiere Bereinigungsbericht"""
        try:
            end_time = datetime.now()
            duration = end_time - self.cleanup_stats['start_time']
            
            report = {
                'cleanup_summary': {
                    'tables_cleaned': self.cleanup_stats['tables_cleaned'],
                    'duplicates_removed': self.cleanup_stats['duplicates_removed'],
                    'invalid_entries_removed': self.cleanup_stats['invalid_entries_removed'],
                    'duration_seconds': duration.total_seconds(),
                    'start_time': self.cleanup_stats['start_time'].isoformat(),
                    'end_time': end_time.isoformat()
                },
                'database_info': {
                    'database_path': self.db_path,
                    'total_tables': self._get_total_table_count()
                }
            }
            
            # Speichere Bericht
            report_path = f"cleanup_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            logger.info(f"📊 Bereinigungsbericht generiert: {report_path}")
            logger.info(f"✅ {self.cleanup_stats['tables_cleaned']} Tabellen bereinigt")
            logger.info(f"✅ {self.cleanup_stats['duplicates_removed']} Duplikate entfernt")
            logger.info(f"✅ {self.cleanup_stats['invalid_entries_removed']} ungültige Einträge entfernt")
            
        except Exception as e:
            logger.error(f"Fehler beim Generieren des Bereinigungsberichts: {e}")

    def _get_total_table_count(self) -> int:
        """Hole Gesamtanzahl der Tabellen"""
        try:
            self.cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            return self.cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Tabellenanzahl: {e}")
            return 0

    def get_table_statistics(self, table_name: str) -> Dict[str, Any]:
        """Hole Tabellen-Statistiken"""
        try:
            if not self._table_exists(table_name):
                return {'error': f'Table {table_name} does not exist'}
            
            # Hole Spalten
            columns = self._get_table_columns(table_name)
            
            # Hole Anzahl der Einträge
            self.cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = self.cursor.fetchone()[0]
            
            # Hole Beispieldaten
            self.cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
            sample_data = self.cursor.fetchall()
            
            return {
                'table_name': table_name,
                'columns': columns,
                'row_count': row_count,
                'sample_data': sample_data,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Tabellen-Statistiken: {e}")
            return {'error': str(e)}

    def close(self):
        """Schließe Datenbankverbindung"""
        try:
            if self.conn:
                self.conn.close()
                logger.info("✅ Datenbankverbindung geschlossen")
        except Exception as e:
            logger.error(f"Fehler beim Schließen der Datenbankverbindung: {e}")


def main():
    """Hauptfunktion"""
    try:
        logger.info("🚀 Starte Lookup Table Cleaner...")
        
        # Erstelle Cleaner-Instanz
        cleaner = LookupTableCleaner()
        
        # Führe Bereinigung durch
        cleaner.cleanup_all_tables()
        
        # Schließe Verbindung
        cleaner.close()
        
        logger.info("🎉 Lookup Table Cleaner abgeschlossen!")
        
    except Exception as e:
        logger.error(f"❌ Fehler in main(): {e}")


if __name__ == "__main__":
    main()
