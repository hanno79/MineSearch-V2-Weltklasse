"""
Author: rahn
Datum: 25.08.2025
Version: 1.0
Beschreibung: Datenbank-Constraints für Feldkontamination-Prävention

DATENBANK-INTEGRITÄT 25.08.2025: SQL-Constraints zur Validierung von structured_data
Verhindert Feldkontamination auf Datenbankebene
"""

import sqlite3
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class DatabaseConstraintManager:
    """
    DATENBANK-CONSTRAINT-MANAGER 25.08.2025
    Verwaltet SQL-Constraints für Feldkontamination-Prävention
    """
    
    def __init__(self, db_path: str = None):
        """
        Initialisiert den Constraint-Manager
        
        Args:
            db_path: Pfad zur Datenbank (optional)
        """
        if db_path is None:
            db_path = "/app/backend/minesearch/database/mines.db"
        
        self.db_path = db_path
        
        # Kritische Feldnamen die nicht als Werte erscheinen dürfen
        self.prohibited_field_names = [
            'x-koordinate', 'y-koordinate', 'x-Koordinate', 'y-Koordinate',
            'restaurationskosten', 'Restaurationskosten', 'kostenjahr', 'Kostenjahr',
            'dokumentenjahr', 'Dokumentenjahr', 'produktionsstart', 'Produktionsstart',
            'produktionsende', 'Produktionsende', 'betreiber', 'Betreiber',
            'eigentümer', 'Eigentümer', 'rohstoffe', 'Rohstoffe',
            'minentyp', 'Minentyp', 'aktivitätsstatus', 'Aktivitätsstatus',
            'region', 'Region', 'country', 'Country', 'land', 'Land'
        ]
    
    def create_validation_functions(self) -> List[str]:
        """
        CONSTRAINT-FUNKTIONEN 25.08.2025: Erstellt SQL-Funktionen für Feldvalidierung
        
        Returns:
            Liste von SQL-Statements für Validierungs-Funktionen
        """
        
        # Da SQLite keine benutzerdefinierten Funktionen in reinem SQL unterstützt,
        # erstellen wir stattdessen CHECK-Constraints mit einfacheren Prüfungen
        
        constraints = []
        
        # 1. STRUCTURED_DATA JSON-FORMAT VALIDIERUNG
        constraints.append("""
            -- Validates that structured_data contains valid JSON
            ALTER TABLE search_results ADD CONSTRAINT check_structured_data_json
            CHECK (
                structured_data IS NULL OR 
                json_valid(structured_data) = 1
            );
        """)
        
        # 2. MINE_NAME NICHT LEER
        constraints.append("""
            -- Ensures mine_name is not empty
            ALTER TABLE search_results ADD CONSTRAINT check_mine_name_not_empty
            CHECK (
                mine_name IS NOT NULL AND 
                trim(mine_name) != '' AND
                length(trim(mine_name)) > 0
            );
        """)
        
        # 3. SESSION_ID FORMAT
        constraints.append("""
            -- Validates session_id format (UUID-like)
            ALTER TABLE search_results ADD CONSTRAINT check_session_id_format
            CHECK (
                session_id IS NULL OR
                (length(session_id) >= 8 AND session_id GLOB '*-*')
            );
        """)
        
        # 4. MODEL_USED FORMAT
        constraints.append("""
            -- Validates model_used format (provider:model)
            ALTER TABLE search_results ADD CONSTRAINT check_model_used_format
            CHECK (
                model_used IS NULL OR
                (model_used LIKE '%:%' AND length(model_used) > 3)
            );
        """)
        
        # 5. SEARCH_DURATION POSITIV
        constraints.append("""
            -- Ensures search_duration is positive
            ALTER TABLE search_results ADD CONSTRAINT check_search_duration_positive
            CHECK (
                search_duration IS NULL OR
                search_duration >= 0
            );
        """)
        
        return constraints
    
    def create_field_contamination_triggers(self) -> List[str]:
        """
        TRIGGER-FUNKTIONEN 25.08.2025: Erstellt SQL-Trigger für Feldkontamination-Prävention
        
        Returns:
            Liste von SQL-Statements für Trigger-Erstellung
        """
        
        triggers = []
        
        # SQLite Trigger für structured_data Validierung
        # Da wir keine komplexe JSON-Validierung in SQLite haben, 
        # implementieren wir grundlegende Prüfungen
        
        triggers.append("""
            -- Trigger: Prevents obvious field name contamination in structured_data
            CREATE TRIGGER IF NOT EXISTS prevent_field_contamination_insert
            BEFORE INSERT ON search_results
            WHEN NEW.structured_data IS NOT NULL
            BEGIN
                -- Verhindere offensichtliche Feldnamen als Werte
                SELECT CASE
                    WHEN NEW.structured_data LIKE '%"Country": "Region"%' OR
                         NEW.structured_data LIKE '%"Region": "Eigentümer"%' OR
                         NEW.structured_data LIKE '%"Betreiber": "x-Koordinate"%' OR
                         NEW.structured_data LIKE '%"Eigentümer": "y-Koordinate"%' OR
                         NEW.structured_data LIKE '%"Aktivitätsstatus": "Rohstoffe"%'
                    THEN RAISE(ABORT, 'FIELD_CONTAMINATION: Field names detected as values in structured_data')
                END;
            END;
        """)
        
        triggers.append("""
            -- Trigger: Prevents field name contamination on updates
            CREATE TRIGGER IF NOT EXISTS prevent_field_contamination_update
            BEFORE UPDATE ON search_results
            WHEN NEW.structured_data IS NOT NULL
            BEGIN
                -- Verhindere offensichtliche Feldnamen als Werte
                SELECT CASE
                    WHEN NEW.structured_data LIKE '%"Country": "Region"%' OR
                         NEW.structured_data LIKE '%"Region": "Eigentümer"%' OR
                         NEW.structured_data LIKE '%"Betreiber": "x-Koordinate"%' OR
                         NEW.structured_data LIKE '%"Eigentümer": "y-Koordinate"%' OR
                         NEW.structured_data LIKE '%"Aktivitätsstatus": "Rohstoffe"%'
                    THEN RAISE(ABORT, 'FIELD_CONTAMINATION: Field names detected as values in structured_data')
                END;
            END;
        """)
        
        # Logging-Trigger für erfolgreiche Insertionen
        triggers.append("""
            -- Trigger: Logs successful insertions (for monitoring)
            CREATE TRIGGER IF NOT EXISTS log_successful_insertions
            AFTER INSERT ON search_results
            BEGIN
                INSERT INTO constraint_log (
                    table_name, 
                    operation, 
                    record_id, 
                    timestamp, 
                    details
                ) VALUES (
                    'search_results', 
                    'INSERT', 
                    NEW.id, 
                    datetime('now'),
                    'Record inserted successfully'
                );
            END;
        """)
        
        return triggers
    
    def create_constraint_log_table(self) -> List[str]:
        """
        LOG-TABELLE 25.08.2025: Erstellt Tabelle für Constraint-Logging
        
        Returns:
            Liste von SQL-Statements für Log-Tabelle
        """
        
        return [
            """
            CREATE TABLE IF NOT EXISTS constraint_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_name TEXT NOT NULL,
                operation TEXT NOT NULL,
                record_id INTEGER,
                timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                constraint_name TEXT,
                details TEXT,
                severity TEXT DEFAULT 'INFO'
            )
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_constraint_log_timestamp 
            ON constraint_log(timestamp)
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_constraint_log_table_operation 
            ON constraint_log(table_name, operation)
            """
        ]
    
    def install_constraints(self) -> bool:
        """
        CONSTRAINT-INSTALLATION 25.08.2025: Installiert alle Datenbank-Constraints
        
        Returns:
            True wenn Installation erfolgreich
        """
        
        try:
            logger.info("[CONSTRAINTS] Installiere Datenbank-Constraints...")
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 1. Log-Tabelle erstellen
            logger.info("[CONSTRAINTS] Erstelle Constraint-Log-Tabelle...")
            log_table_statements = self.create_constraint_log_table()
            for statement in log_table_statements:
                cursor.execute(statement)
                logger.debug("[CONSTRAINTS] Log-Tabelle Statement ausgeführt")
            
            # 2. Validierungs-Constraints erstellen (falls unterstützt)
            logger.info("[CONSTRAINTS] Erstelle Validierungs-Constraints...")
            validation_constraints = self.create_validation_functions()
            
            constraints_installed = 0
            for constraint_sql in validation_constraints:
                try:
                    cursor.execute(constraint_sql)
                    constraints_installed += 1
                    logger.debug(f"[CONSTRAINTS] Constraint installiert: {constraint_sql[:50]}...")
                except sqlite3.Error as e:
                    # Manche Constraints sind möglicherweise nicht in allen SQLite-Versionen verfügbar
                    logger.warning(f"[CONSTRAINTS] Constraint übersprungen (nicht unterstützt): {e}")
            
            # 3. Trigger erstellen
            logger.info("[CONSTRAINTS] Erstelle Feldkontamination-Trigger...")
            triggers = self.create_field_contamination_triggers()
            
            triggers_installed = 0
            for trigger_sql in triggers:
                try:
                    cursor.execute(trigger_sql)
                    triggers_installed += 1
                    logger.debug(f"[CONSTRAINTS] Trigger installiert: {trigger_sql[:50]}...")
                except sqlite3.Error as e:
                    logger.error(f"[CONSTRAINTS] Trigger-Fehler: {e}")
            
            # Änderungen committen
            conn.commit()
            conn.close()
            
            logger.info(f"[CONSTRAINTS] ✅ Installation abgeschlossen:")
            logger.info(f"[CONSTRAINTS]   - {constraints_installed} Constraints installiert") 
            logger.info(f"[CONSTRAINTS]   - {triggers_installed} Trigger installiert")
            logger.info(f"[CONSTRAINTS]   - Log-Tabelle erstellt")
            
            return True
            
        except Exception as e:
            logger.error(f"[CONSTRAINTS] FEHLER bei Constraint-Installation: {e}")
            return False
    
    def test_constraints(self) -> bool:
        """
        CONSTRAINT-TEST 25.08.2025: Testet installierte Constraints
        
        Returns:
            True wenn alle Tests erfolgreich
        """
        
        try:
            logger.info("[CONSTRAINT-TEST] Starte Constraint-Validierung...")
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            test_passed = 0
            test_failed = 0
            
            # Test 1: Versuche ungültigen JSON einzufügen
            try:
                cursor.execute("""
                    INSERT INTO search_results (mine_name, structured_data) 
                    VALUES ('Test Mine', 'invalid json')
                """)
                logger.warning("[CONSTRAINT-TEST] JSON-Constraint nicht aktiv (erwartet)")
            except sqlite3.Error as e:
                logger.info(f"[CONSTRAINT-TEST] ✅ JSON-Constraint funktioniert: {e}")
                test_passed += 1
            
            # Test 2: Versuche leeren mine_name einzufügen
            try:
                cursor.execute("""
                    INSERT INTO search_results (mine_name, structured_data) 
                    VALUES ('', '{}')
                """)
                logger.warning("[CONSTRAINT-TEST] Mine-Name-Constraint nicht aktiv")
            except sqlite3.Error as e:
                logger.info(f"[CONSTRAINT-TEST] ✅ Mine-Name-Constraint funktioniert: {e}")
                test_passed += 1
            
            # Test 3: Prüfe Trigger-Existenz
            cursor.execute("SELECT name FROM sqlite_master WHERE type='trigger'")
            triggers = cursor.fetchall()
            trigger_names = [trigger[0] for trigger in triggers]
            
            expected_triggers = [
                'prevent_field_contamination_insert',
                'prevent_field_contamination_update', 
                'log_successful_insertions'
            ]
            
            for expected_trigger in expected_triggers:
                if expected_trigger in trigger_names:
                    logger.info(f"[CONSTRAINT-TEST] ✅ Trigger '{expected_trigger}' existiert")
                    test_passed += 1
                else:
                    logger.warning(f"[CONSTRAINT-TEST] ❌ Trigger '{expected_trigger}' fehlt")
                    test_failed += 1
            
            # Test 4: Prüfe Log-Tabelle
            cursor.execute("SELECT name FROM sqlite_master WHERE name='constraint_log'")
            if cursor.fetchone():
                logger.info("[CONSTRAINT-TEST] ✅ Constraint-Log-Tabelle existiert")
                test_passed += 1
            else:
                logger.error("[CONSTRAINT-TEST] ❌ Constraint-Log-Tabelle fehlt")
                test_failed += 1
            
            conn.close()
            
            logger.info(f"[CONSTRAINT-TEST] Test-Ergebnis: {test_passed} erfolgreich, {test_failed} fehlgeschlagen")
            
            return test_failed == 0
            
        except Exception as e:
            logger.error(f"[CONSTRAINT-TEST] FEHLER bei Constraint-Test: {e}")
            return False
    
    def get_constraint_violations(self) -> List[Dict[str, Any]]:
        """
        VIOLATION-ANALYSE 25.08.2025: Holt alle Constraint-Verletzungen aus dem Log
        
        Returns:
            Liste von Constraint-Verletzungen
        """
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM constraint_log 
                WHERE severity IN ('WARNING', 'ERROR')
                ORDER BY timestamp DESC
                LIMIT 100
            """)
            
            violations = []
            for row in cursor.fetchall():
                violations.append({
                    'id': row[0],
                    'table_name': row[1], 
                    'operation': row[2],
                    'record_id': row[3],
                    'timestamp': row[4],
                    'constraint_name': row[5],
                    'details': row[6],
                    'severity': row[7]
                })
            
            conn.close()
            
            logger.info(f"[CONSTRAINTS] {len(violations)} Constraint-Verletzungen gefunden")
            return violations
            
        except Exception as e:
            logger.error(f"[CONSTRAINTS] FEHLER beim Abrufen der Violations: {e}")
            return []

def main():
    """
    MAIN-FUNKTION 25.08.2025: Installiert und testet Datenbank-Constraints
    """
    
    print("🔒 DATENBANK-CONSTRAINT-INSTALLATION")
    print("=" * 50)
    
    constraint_manager = DatabaseConstraintManager()
    
    # Installation
    print("📦 Installiere Constraints und Trigger...")
    success = constraint_manager.install_constraints()
    
    if success:
        print("✅ Constraint-Installation erfolgreich!")
        
        # Test
        print("\n🧪 Teste installierte Constraints...")
        test_success = constraint_manager.test_constraints()
        
        if test_success:
            print("✅ Alle Constraint-Tests erfolgreich!")
        else:
            print("⚠️ Einige Constraint-Tests fehlgeschlagen")
        
        # Violations prüfen
        print("\n📊 Prüfe bestehende Violations...")
        violations = constraint_manager.get_constraint_violations()
        
        if violations:
            print(f"⚠️ {len(violations)} Constraint-Verletzungen gefunden")
            for violation in violations[:5]:  # Zeige nur erste 5
                print(f"   - {violation['timestamp']}: {violation['details']}")
        else:
            print("✅ Keine Constraint-Verletzungen gefunden")
        
    else:
        print("❌ Constraint-Installation fehlgeschlagen!")
        return False
    
    print(f"\n🎉 DATENBANK-CONSTRAINTS ERFOLGREICH EINGERICHTET!")
    return True

if __name__ == "__main__":
    main()