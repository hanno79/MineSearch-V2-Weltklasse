#!/usr/bin/env python3
"""
Compact Prevent Future Duplicates
Kompakte Version der Duplikat-Prävention

Author: MineSearch Development Team
Date: 2025-01-11
"""

import sqlite3
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import os
import shutil

logger = logging.getLogger(__name__)


class DuplicatePreventionManager:
    """Manager für permanente Duplikat-Prävention"""

    def __init__(self, db_path: str = "mines.db"):
        """Initialisiere Duplicate Prevention Manager"""
        self.db_path = db_path
        self.backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.logger = logger

    def create_unique_constraints(self) -> bool:
        """Erstelle UNIQUE-Constraints für kritische Felder"""
        try:
            self.logger.info("🛡️ Starte permanente Duplikat-Prävention...")
            
            # Erstelle Backup
            self._create_backup()
            
            # Erstelle neue Tabellen mit UNIQUE-Constraints
            self._create_normalized_tables()
            
            # Migriere Daten
            self._migrate_data()
            
            # Ersetze alte Tabellen
            self._replace_tables()
            
            self.logger.info("✅ UNIQUE-Constraints erfolgreich erstellt")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Fehler bei Duplikat-Prävention: {e}")
            self._restore_backup()
            return False

    def _create_backup(self):
        """Erstelle Backup der Datenbank"""
        try:
            shutil.copy2(self.db_path, self.backup_path)
            self.logger.info(f"📦 Backup erstellt: {self.backup_path}")
        except Exception as e:
            self.logger.error(f"Fehler beim Backup: {e}")
            raise

    def _create_normalized_tables(self):
        """Erstelle normalisierte Tabellen mit UNIQUE-Constraints"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Erstelle neue companies Tabelle mit UNIQUE-Constraint
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS companies_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    country TEXT,
                    industry TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Erstelle neue mines Tabelle mit UNIQUE-Constraint
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mines_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    company_id INTEGER,
                    country TEXT,
                    commodity TEXT,
                    operational_status TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (company_id) REFERENCES companies_new(id)
                )
            """)
            
            # Erstelle neue sources Tabelle mit UNIQUE-Constraint
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sources_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT UNIQUE NOT NULL,
                    title TEXT,
                    content TEXT,
                    source_type TEXT,
                    domain TEXT,
                    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_accessed TIMESTAMP,
                    access_count INTEGER DEFAULT 0,
                    reliability_score REAL DEFAULT 0.0
                )
            """)
            
            conn.commit()
            self.logger.info("📋 Neue Tabellen mit UNIQUE-Constraints erstellt")

    def _migrate_data(self):
        """Migriere Daten von alten zu neuen Tabellen"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Migriere companies (mit Duplikat-Behandlung)
            cursor.execute("SELECT DISTINCT name, country, industry FROM companies")
            companies = cursor.fetchall()
            
            for name, country, industry in companies:
                try:
                    cursor.execute("""
                        INSERT INTO companies_new (name, country, industry)
                        VALUES (?, ?, ?)
                    """, (name, country, industry))
                except sqlite3.IntegrityError:
                    self.logger.warning(f"Duplikat übersprungen: {name}")
            
            # Migriere mines (mit Duplikat-Behandlung)
            cursor.execute("SELECT DISTINCT name, company_id, country, commodity, operational_status FROM mines")
            mines = cursor.fetchall()
            
            for name, company_id, country, commodity, operational_status in mines:
                try:
                    cursor.execute("""
                        INSERT INTO mines_new (name, company_id, country, commodity, operational_status)
                        VALUES (?, ?, ?, ?, ?)
                    """, (name, company_id, country, commodity, operational_status))
                except sqlite3.IntegrityError:
                    self.logger.warning(f"Duplikat übersprungen: {name}")
            
            # Migriere sources (mit Duplikat-Behandlung)
            cursor.execute("SELECT DISTINCT url, title, content, source_type, domain FROM sources")
            sources = cursor.fetchall()
            
            for url, title, content, source_type, domain in sources:
                try:
                    cursor.execute("""
                        INSERT INTO sources_new (url, title, content, source_type, domain)
                        VALUES (?, ?, ?, ?, ?)
                    """, (url, title, content, source_type, domain))
                except sqlite3.IntegrityError:
                    self.logger.warning(f"Duplikat übersprungen: {url}")
            
            conn.commit()
            self.logger.info("🔄 Daten erfolgreich migriert")

    def _replace_tables(self):
        """Ersetze alte Tabellen durch neue"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Ersetze alte Tabellen
            cursor.execute("DROP TABLE IF EXISTS companies")
            cursor.execute("DROP TABLE IF EXISTS mines")
            cursor.execute("DROP TABLE IF EXISTS sources")
            
            # Benenne neue Tabellen um
            cursor.execute("ALTER TABLE companies_new RENAME TO companies")
            cursor.execute("ALTER TABLE mines_new RENAME TO mines")
            cursor.execute("ALTER TABLE sources_new RENAME TO sources")
            
            # Erstelle Indizes für Performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_companies_name ON companies(name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_mines_name ON mines(name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sources_url ON sources(url)")
            
            conn.commit()
            self.logger.info("🔄 Tabellen erfolgreich ersetzt")

    def _restore_backup(self):
        """Stelle Backup wieder her"""
        try:
            shutil.copy2(self.backup_path, self.db_path)
            self.logger.info("🔄 Backup wiederhergestellt")
        except Exception as e:
            self.logger.error(f"Fehler bei Backup-Wiederherstellung: {e}")

    def check_duplicates(self) -> Dict[str, int]:
        """Prüfe auf verbleibende Duplikate"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Prüfe companies
            cursor.execute("SELECT COUNT(*) FROM companies")
            total_companies = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT name) FROM companies")
            unique_companies = cursor.fetchone()[0]
            
            # Prüfe mines
            cursor.execute("SELECT COUNT(*) FROM mines")
            total_mines = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT name) FROM mines")
            unique_mines = cursor.fetchone()[0]
            
            # Prüfe sources
            cursor.execute("SELECT COUNT(*) FROM sources")
            total_sources = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT url) FROM sources")
            unique_sources = cursor.fetchone()[0]
            
            return {
                'companies': {'total': total_companies, 'unique': unique_companies},
                'mines': {'total': total_mines, 'unique': unique_mines},
                'sources': {'total': total_sources, 'unique': unique_sources}
            }

    def get_duplicate_statistics(self) -> Dict[str, Any]:
        """Hole Duplikat-Statistiken"""
        duplicates = self.check_duplicates()
        
        stats = {
            'timestamp': datetime.now().isoformat(),
            'duplicates_found': False,
            'details': {}
        }
        
        for table, counts in duplicates.items():
            total = counts['total']
            unique = counts['unique']
            duplicate_count = total - unique
            
            stats['details'][table] = {
                'total_records': total,
                'unique_records': unique,
                'duplicate_count': duplicate_count,
                'duplicate_percentage': (duplicate_count / total * 100) if total > 0 else 0
            }
            
            if duplicate_count > 0:
                stats['duplicates_found'] = True
        
        return stats

    def cleanup_backup(self):
        """Bereinige Backup-Datei"""
        try:
            if os.path.exists(self.backup_path):
                os.remove(self.backup_path)
                self.logger.info("🗑️ Backup-Datei bereinigt")
        except Exception as e:
            self.logger.error(f"Fehler bei Backup-Bereinigung: {e}")

    def health_check(self) -> Dict[str, Any]:
        """Prüfe System-Gesundheit"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Prüfe Tabellen-Existenz
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                required_tables = ['companies', 'mines', 'sources']
                missing_tables = [table for table in required_tables if table not in tables]
                
                return {
                    'status': 'healthy' if not missing_tables else 'unhealthy',
                    'tables_found': tables,
                    'missing_tables': missing_tables,
                    'duplicate_stats': self.get_duplicate_statistics(),
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }


def main():
    """Hauptfunktion für Duplikat-Prävention"""
    logger.info("🛡️ Starte permanente Duplikat-Prävention...")
    
    manager = DuplicatePreventionManager()
    
    # Führe Duplikat-Prävention durch
    success = manager.create_unique_constraints()
    
    if success:
        # Prüfe Ergebnisse
        stats = manager.get_duplicate_statistics()
        logger.info(f"📊 Duplikat-Statistiken: {stats}")
        
        # Bereinige Backup
        manager.cleanup_backup()
        
        logger.info("✅ Duplikat-Prävention erfolgreich abgeschlossen")
    else:
        logger.error("❌ Duplikat-Prävention fehlgeschlagen")


if __name__ == "__main__":
    main()


__all__ = ["DuplicatePreventionManager"]
