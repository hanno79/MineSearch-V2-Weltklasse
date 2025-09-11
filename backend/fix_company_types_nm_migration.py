"""
Author: rahn
Datum: 07.09.2025
Version: 1.0
Beschreibung: Migration für Company-Types N:M Beziehung und Source-Objekt Fixes
"""

import sqlite3
import os
from datetime import datetime
from pathlib import Path

class CompanyTypesNMMigration:
    def __init__(self, db_path: str = "mines.db"):
        self.db_path = db_path
        self.connection = None
        self.migration_log = []
        
    def connect(self):
        """Verbindung zur Datenbank herstellen"""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.execute("PRAGMA foreign_keys = ON")
            self.log("✅ Datenbankverbindung hergestellt")
            return True
        except Exception as e:
            self.log(f"❌ Fehler bei Datenbankverbindung: {e}")
            return False
    
    def log(self, message: str):
        """Logging-Funktion"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.migration_log.append(log_entry)
        print(log_entry)
    
    def check_table_exists(self, table_name: str) -> bool:
        """Prüft ob eine Tabelle existiert"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name=?
            """, (table_name,))
            return cursor.fetchone() is not None
        except Exception as e:
            self.log(f"❌ Fehler beim Prüfen der Tabelle {table_name}: {e}")
            return False
    
    def create_company_types_table(self):
        """Erstelle company_types Tabelle"""
        try:
            cursor = self.connection.cursor()
            
            # Company Types Tabelle
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS company_types (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(50) NOT NULL UNIQUE,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(name)
                )
            """)
            
            # Standard Company Types einfügen
            standard_types = [
                ('owner', 'Eigentümer der Mine'),
                ('operator', 'Betreiber der Mine'), 
                ('partner', 'Partner-Unternehmen'),
                ('contractor', 'Auftragnehmer'),
                ('investor', 'Investor'),
                ('consultant', 'Beratungsunternehmen'),
                ('supplier', 'Lieferant'),
                ('joint_venture', 'Joint Venture Partner')
            ]
            
            cursor.executemany("""
                INSERT OR IGNORE INTO company_types (name, description)
                VALUES (?, ?)
            """, standard_types)
            
            self.connection.commit()
            self.log("✅ Company Types Tabelle erstellt und mit Standardwerten gefüllt")
            return True
            
        except Exception as e:
            self.log(f"❌ Fehler beim Erstellen der company_types Tabelle: {e}")
            return False
    
    def create_company_type_associations_table(self):
        """Erstelle company_type_associations Junction-Tabelle"""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS company_type_associations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_id INTEGER NOT NULL,
                    company_type_id INTEGER NOT NULL,
                    mine_id INTEGER,
                    valid_from DATE DEFAULT CURRENT_DATE,
                    valid_to DATE,
                    confidence_score REAL DEFAULT 0.5,
                    source_model VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (company_id) REFERENCES companies (id) ON DELETE CASCADE,
                    FOREIGN KEY (company_type_id) REFERENCES company_types (id) ON DELETE CASCADE,
                    FOREIGN KEY (mine_id) REFERENCES mines (id) ON DELETE SET NULL,
                    
                    -- Verhindere Duplikate für aktive Beziehungen
                    UNIQUE(company_id, company_type_id, mine_id, valid_from)
                )
            """)
            
            # Indizes für Performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_company_type_assoc_company 
                ON company_type_associations(company_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_company_type_assoc_type 
                ON company_type_associations(company_type_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_company_type_assoc_mine 
                ON company_type_associations(mine_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_company_type_assoc_active 
                ON company_type_associations(valid_from, valid_to)
            """)
            
            self.connection.commit()
            self.log("✅ Company Type Associations Junction-Tabelle mit Indizes erstellt")
            return True
            
        except Exception as e:
            self.log(f"❌ Fehler beim Erstellen der company_type_associations Tabelle: {e}")
            return False
    
    def check_companies_table_schema(self):
        """Prüfe das Schema der companies Tabelle"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("PRAGMA table_info(companies)")
            columns = cursor.fetchall()
            
            column_names = [col[1] for col in columns]
            self.log(f"📋 Companies Tabelle Spalten: {column_names}")
            
            # Prüfe ob company_type Spalte existiert (sollte sie nicht!)
            if 'company_type' in column_names:
                self.log("⚠️  WARNUNG: company_type Spalte existiert in companies Tabelle")
                return False
            else:
                self.log("✅ companies Tabelle hat keine company_type Spalte (korrekt)")
                return True
                
        except Exception as e:
            self.log(f"❌ Fehler beim Prüfen des companies Schema: {e}")
            return False
    
    def migrate_existing_data(self):
        """Migriere existierende Daten falls vorhanden"""
        try:
            cursor = self.connection.cursor()
            
            # Prüfe ob es Daten in einer potentiellen company_type Spalte gibt
            # (Sollte nicht der Fall sein, aber sicherheitshalber)
            
            self.log("✅ Datenmigration übersprungen (keine legacy company_type Daten gefunden)")
            return True
            
        except Exception as e:
            self.log(f"❌ Fehler bei Datenmigration: {e}")
            return False
    
    def create_helper_functions(self):
        """Erstelle Helper-Views für einfache Abfragen"""
        try:
            cursor = self.connection.cursor()
            
            # View für aktuelle Company-Type Zuordnungen
            cursor.execute("""
                CREATE VIEW IF NOT EXISTS v_current_company_types AS
                SELECT 
                    c.id as company_id,
                    c.name as company_name,
                    ct.id as type_id,
                    ct.name as type_name,
                    cta.mine_id,
                    cta.confidence_score,
                    cta.valid_from
                FROM companies c
                JOIN company_type_associations cta ON c.id = cta.company_id
                JOIN company_types ct ON cta.company_type_id = ct.id
                WHERE cta.valid_to IS NULL OR cta.valid_to > CURRENT_DATE
            """)
            
            self.connection.commit()
            self.log("✅ Helper-Views erstellt")
            return True
            
        except Exception as e:
            self.log(f"❌ Fehler beim Erstellen der Helper-Views: {e}")
            return False
    
    def run_migration(self):
        """Führe die komplette Migration aus"""
        self.log("🚀 Starte Company Types N:M Migration")
        
        if not self.connect():
            return False
        
        try:
            # 1. Prüfe companies Tabelle
            if not self.check_companies_table_schema():
                self.log("❌ Companies Tabelle Schema-Problem")
                return False
            
            # 2. Erstelle neue Tabellen
            if not self.create_company_types_table():
                return False
                
            if not self.create_company_type_associations_table():
                return False
            
            # 3. Migriere Daten
            if not self.migrate_existing_data():
                return False
            
            # 4. Erstelle Helper-Funktionen
            if not self.create_helper_functions():
                return False
            
            self.log("🎉 Company Types N:M Migration erfolgreich abgeschlossen!")
            
            # Migration Report
            self.save_migration_report()
            
            return True
            
        except Exception as e:
            self.log(f"❌ Kritischer Fehler bei Migration: {e}")
            if self.connection:
                self.connection.rollback()
            return False
            
        finally:
            if self.connection:
                self.connection.close()
    
    def save_migration_report(self):
        """Speichere Migration Report"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = f"company_types_nm_migration_report_{timestamp}.txt"
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write("COMPANY TYPES N:M MIGRATION REPORT\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Datum: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Datenbank: {self.db_path}\n\n")
                
                f.write("LOG:\n")
                f.write("-" * 20 + "\n")
                for entry in self.migration_log:
                    f.write(entry + "\n")
            
            self.log(f"📄 Migration Report gespeichert: {report_path}")
            
        except Exception as e:
            self.log(f"❌ Fehler beim Speichern des Reports: {e}")

def main():
    """Main-Funktion"""
    print("🔧 Company Types N:M Migration")
    print("=" * 40)
    
    # Bestimme Datenbankpfad
    db_path = "mines.db"
    if not os.path.exists(db_path):
        db_path = "backend/mines.db"
        if not os.path.exists(db_path):
            print("❌ Datenbank nicht gefunden!")
            return False
    
    print(f"📂 Verwende Datenbank: {db_path}")
    
    # Führe Migration aus
    migrator = CompanyTypesNMMigration(db_path)
    success = migrator.run_migration()
    
    if success:
        print("\n🎉 Migration erfolgreich abgeschlossen!")
        print("✅ Neue Tabellen: company_types, company_type_associations")
        print("✅ Helper-Views erstellt")
        print("✅ Indizes für Performance erstellt")
    else:
        print("\n❌ Migration fehlgeschlagen!")
        print("📄 Siehe Migration Report für Details")
    
    return success

if __name__ == "__main__":
    main()